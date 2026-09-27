#define MyAppName "Kittelligence"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Jayden"
#define MyAppExeName "Kiteelegence.exe"

[Setup]
AppId={{A8C6E8B5-4F3D-4E7B-9F21-KITELLIGENCE}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={autopf}\Kittelligence
DefaultGroupName=Kittelligence

OutputDir=installer
OutputBaseFilename=KiteelegenceSetup

Compression=lzma
SolidCompression=yes
WizardStyle=modern

Uninstallable=yes

[Files]
Source: "dist\Kiteelegence\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Kittelligence"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Kittelligence"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Kittelligence"; Flags: nowait postinstall skipifsilent