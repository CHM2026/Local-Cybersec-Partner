; Installateur Windows de CyberSec Dashboard (Inno Setup 6).
;
; Compilation locale, depuis la racine du dépôt :
;   iscc /DAppVersion=1.0.0 installer\CyberSecDashboard.iss
;
; Le dossier build\win\dist\CyberSecDashboard doit exister : il est produit par
;   py -3.15 tools/build_windows.py --keep-work
; Le marqueur portable.txt est volontairement exclu : l'installation utilise le
; registre système, pas un settings.ini local.

#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

[Setup]
AppId={{A3C88A48-5F6A-4F5D-9EEC-7FD431389DBF}
AppName=CyberSec Dashboard
AppVersion={#AppVersion}
AppPublisher=CHM2026
AppPublisherURL=https://github.com/CHM2026/Local-Cybersec-Partner
AppSupportURL=https://github.com/CHM2026/Local-Cybersec-Partner/issues
AppUpdatesURL=https://github.com/CHM2026/Local-Cybersec-Partner/releases
DefaultDirName={autopf}\CyberSec Dashboard
DefaultGroupName=CyberSec Dashboard
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
OutputDir=..\dist
OutputBaseFilename=CyberSecDashboard-{#AppVersion}-setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\CyberSecDashboard.exe
UninstallDisplayName=CyberSec Dashboard {#AppVersion}
CloseApplications=yes
CloseApplicationsFilter=CyberSecDashboard.exe
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\build\win\dist\CyberSecDashboard\*"; Excludes: "portable.txt,settings.ini"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\CyberSec Dashboard"; Filename: "{app}\CyberSecDashboard.exe"
Name: "{autodesktop}\CyberSec Dashboard"; Filename: "{app}\CyberSecDashboard.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\CyberSecDashboard.exe"; Description: "{cm:LaunchProgram,CyberSec Dashboard}"; Flags: nowait postinstall skipifsilent
