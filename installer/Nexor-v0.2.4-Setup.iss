#define MyAppName "Nexor"
#define MyAppVersion "0.2.4"
#define MyAppPublisher "Nexor"
#define MyAppExeName "Nexor-v0.2.4.exe"
#define SourceDir "..\dist\0.2.4\installable"
[Setup]
AppId={{D6B7A497-68B0-48BC-B6E0-44FA95497BAD}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Nexor
DefaultGroupName=Nexor
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist\0.2.4\installer
OutputBaseFilename=Nexor-Setup-v0.2.4
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoProductName={#MyAppName}
[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
[Tasks]
Name: "desktopicon"; Description: "Criar um atalho na área de trabalho"; GroupDescription: "Atalhos adicionais:"
[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{autoprograms}\Nexor"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Nexor"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Executar Nexor"; Flags: nowait postinstall skipifsilent
