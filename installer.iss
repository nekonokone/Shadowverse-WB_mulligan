#define AppName "シャドウバース WB マリガントラッカー"
#define AppVersion "0.3.1"
#define AppPublisher "Personal Project"
#define AppExeName "MulliganTracker.exe"

[Setup]
AppId={{8BE36191-1644-4C91-A240-04DF2A1D3A68}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\MulliganTracker
DefaultGroupName={#AppName}
OutputDir=installer-output
OutputBaseFilename=Shadowverse-WB-Mulligan-Tracker-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=mulligan_tracker.ico
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#AppExeName}
CloseApplications=yes

[Languages]
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"

[Tasks]
Name: "desktopicon"; Description: "デスクトップにショートカットを作成する"; GroupDescription: "追加のショートカット:"; Flags: unchecked

[Files]
Source: "dist\MulliganTracker\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "mulligan_tracker.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\mulligan_tracker.ico"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\mulligan_tracker.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "アプリを起動"; Flags: postinstall nowait skipifsilent
