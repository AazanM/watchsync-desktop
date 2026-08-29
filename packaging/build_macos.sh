#!/bin/sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$project_dir"

python_bin=${PYTHON_BIN:-python3}
wheel_dir="$project_dir/build/universal-wheels"

python_arches=$(file "$("$python_bin" -c 'import os, sys; print(os.path.realpath(getattr(sys, "_base_executable", sys.executable)))')")
case "$python_arches" in
  *x86_64*arm64*|*arm64*x86_64*) ;;
  *)
    echo "A universal2 Python interpreter is required (arm64 + x86_64)." >&2
    echo "$python_arches" >&2
    exit 1
    ;;
esac

rm -rf "$project_dir/build" "$project_dir/dist/WatchSync Desktop.app"
"$python_bin" -m pip install --upgrade pip wheel setuptools py2app
"$python_bin" -m pip uninstall -y PySide6 PySide6_Addons
"$python_bin" -m pip install -r requirements.txt -r requirements_gui.txt

# PyPI does not publish universal2 wheels for every native dependency. Rebuild
# the small C extensions locally, and explicitly select universal2 Rust wheels.
"$python_bin" -m pip uninstall -y zope.interface cffi cryptography charset-normalizer
CFLAGS="-arch x86_64 -arch arm64" ARCHFLAGS="-arch x86_64 -arch arm64" \
  "$python_bin" -m pip install --no-binary :all: zope.interface cffi
mkdir -p "$wheel_dir"
"$python_bin" -m pip download \
  --platform macosx_10_10_universal2 \
  --only-binary :all: \
  --no-deps \
  --dest "$wheel_dir" \
  'cryptography>=46,<48' charset-normalizer
"$python_bin" -m pip install \
  --no-deps \
  --no-index \
  --find-links "$wheel_dir" \
  'cryptography>=46,<48' charset-normalizer

# PySide6 6.11 ships as a namespace package (no __init__.py), which
# modulegraph's legacy imp.find_module cannot resolve, so py2app's "packages"
# option rejects it. py2app's own pyside6 recipe means to request the same
# thing but misspells the key as "packagse", so PySide6 is swept into the
# zipped site-packages where its dylibs cannot be dlopen'd. Materialising an
# empty __init__.py makes it a regular package for the duration of the build.
"$python_bin" - <<'PY'
import os
import PySide6

for package in (PySide6,):
    root = list(package.__path__)[0]
    init = os.path.join(root, "__init__.py")
    if not os.path.exists(init):
        with open(init, "w") as handle:
            handle.write("")
        print("created", init)
PY

"$python_bin" buildPy2app.py py2app

codesign --force --deep --sign - "dist/WatchSync Desktop.app"
lipo -archs "dist/WatchSync Desktop.app/Contents/MacOS/WatchSync Desktop" | grep -q arm64
lipo -archs "dist/WatchSync Desktop.app/Contents/MacOS/WatchSync Desktop" | grep -q x86_64
lipo -archs "dist/WatchSync Desktop.app/Contents/MacOS/syncplayServer" | grep -q arm64
lipo -archs "dist/WatchSync Desktop.app/Contents/MacOS/syncplayServer" | grep -q x86_64
echo "App bundle: $project_dir/dist/WatchSync Desktop.app"
