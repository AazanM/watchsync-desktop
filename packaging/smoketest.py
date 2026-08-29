"""Console smoke test for the frozen Windows build.

PyInstaller's static analysis cannot see syncplay's dynamically imported Qt
binding, so a bundle can be produced that only fails once a user launches the
GUI. This exercises the vendored shim and the pieces the client touches during
startup inside the real frozen environment, and is run by CI against the built
executable.
"""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def main():
    from syncplay.vendor.Qt import QtCore, QtGui, QtWidgets
    from syncplay.vendor import Qt as QtShim

    print("binding:", QtShim.__binding__, QtShim.__binding_version__)
    print("qt:", QtShim.__qt_version__)

    for name, submodule in (
        ("QtCore", QtCore), ("QtGui", QtGui), ("QtWidgets", QtWidgets)
    ):
        for member in ("QObject", "QIcon", "QApplication"):
            if hasattr(submodule, member):
                print("%s.%s ok" % (name, member))
                break
        else:
            raise SystemExit("%s exposed no expected member" % name)

    app = QtWidgets.QApplication(sys.argv[:1])
    QtWidgets.QWidget().setWindowTitle("smoke")
    app.processEvents()
    print("QApplication ok")

    from syncplay import product
    from syncplay.chat import ChatStore
    print("product:", product.PRODUCT_NAME)

    store = ChatStore()
    print("chat store ok:", store is not None)

    import syncplay.ui.gui  # noqa: F401
    import syncplay.ui.chat_overlay  # noqa: F401
    import syncplay.private_server  # noqa: F401
    print("syncplay ui modules ok")

    print("SMOKE TEST PASSED")


if __name__ == "__main__":
    main()
