; KEYGEN installer — no license page.
; Compile from repo root:  ISCC.exe packaging\keygen.iss
; Output: dist\keygen-setup.exe

#define MyAppName "KEYGEN"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "KEYGEN"
#define MyAppExeName "KEYGEN.exe"

[Setup]
AppId={{8F3C1A2B-6D4E-4A91-9B70-KEYGEN000001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\KEYGEN
DefaultGroupName=KEYGEN
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=keygen-setup
SetupIconFile=app.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#MyAppExeName}
DisableWelcomePage=no
DisableDirPage=no
AllowNoIcons=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\KEYGEN\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\KEYGEN"; Filename: "{app}\{#MyAppExeName}"
Name: "{userdesktop}\KEYGEN"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch KEYGEN"; Flags: nowait postinstall skipifsilent
