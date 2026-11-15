; Inno Setup 6 script for Kittelligence 2.2
#define AppName "Kittelligence"
#define AppVersion "2.2.0"
#define AppPublisher "anyonomous studios"

[Setup]
AppId={{A92A71C8-3B42-4B70-AB44-9D1B2D2E2100}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\Kittelligence
DefaultGroupName={#AppName}
OutputDir=dist
OutputBaseFilename=Kittelligence-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\Kittelligence.exe

[Files]
Source: "dist\Kittelligence\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Kittelligence"; Filename: "{app}\Kittelligence.exe"
Name: "{autodesktop}\Kittelligence"; Filename: "{app}\Kittelligence.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
Filename: "{app}\Kittelligence.exe"; Description: "Launch Kittelligence"; Flags: postinstall nowait skipifsilent
