Unicode true
RequestExecutionLevel user
SetCompressor /SOLID lzma

!define PRODUCT "WatchSync Desktop"
!define VERSION "1.7.6"
!define PROJECT_ROOT "${__FILEDIR__}\.."

Name "${PRODUCT} ${VERSION}"
OutFile "${PROJECT_ROOT}\dist\WatchSync-Desktop-${VERSION}-Setup.exe"
InstallDir "$LOCALAPPDATA\Programs\${PRODUCT}"
Icon "${PROJECT_ROOT}\syncplay\resources\icon.ico"

Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

Section "Install"
  SetOutPath "$INSTDIR"
  File /r "${PROJECT_ROOT}\dist\${PRODUCT}\*"
  CreateDirectory "$SMPROGRAMS\${PRODUCT}"
  CreateShortcut "$SMPROGRAMS\${PRODUCT}\${PRODUCT}.lnk" "$INSTDIR\${PRODUCT}.exe"
  CreateShortcut "$DESKTOP\${PRODUCT}.lnk" "$INSTDIR\${PRODUCT}.exe"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\${PRODUCT}.lnk"
  RMDir /r "$SMPROGRAMS\${PRODUCT}"
  RMDir /r "$INSTDIR"
SectionEnd
