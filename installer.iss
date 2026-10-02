#define MyAppName "Kittelligence"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Jayden"
#define MyAppExeName "Kittelligence.exe"

#define ProjectRoot SourcePath
#define DistDir ProjectRoot + "\dist"
#define InstallerDir ProjectRoot + "\installer"

[Setup]

AppId={{8B3D7C1E-9A8D-4E5A-B7A3-91D7F2C8E441}

AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={autopf}\Kittelligence
DefaultGroupName=Kittelligence

OutputDir={#InstallerDir}
OutputBaseFilename=KittelligenceSetup-{#MyAppVersion}

Compression=lzma2
SolidCompression=yes
WizardStyle=modern

PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

DisableProgramGroupPage=yes
DisableWelcomePage=no

CloseApplications=yes
RestartApplications=no

Uninstallable=yes
CreateUninstallRegKey=yes

SetupLogging=yes

UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]

Source: "{#DistDir}\Kittelligence.exe"; \
    DestDir: "{app}"; \
    Flags: ignoreversion restartreplace

[Icons]

Name: "{autoprograms}\Kittelligence"; \
    Filename: "{app}\{#MyAppExeName}"; \
    WorkingDir: "{app}"

Name: "{autodesktop}\Kittelligence"; \
    Filename: "{app}\{#MyAppExeName}"; \
    WorkingDir: "{app}"

[Run]

Filename: "{app}\{#MyAppExeName}"; \
    Description: "Launch Kittelligence"; \
    WorkingDir: "{app}"; \
    Flags: nowait postinstall skipifsilent

[UninstallDelete]

Type: filesandordirs; \
    Name: "{app}"