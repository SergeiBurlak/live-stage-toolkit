[Setup]
AppName=Live Stage Toolkit
AppVersion=1.0.0
AppPublisher=Queen Anne Project
DefaultDirName={autopf}\LiveStageToolkit
DefaultGroupName=Live Stage Toolkit
OutputDir=Output
OutputBaseFilename=LiveStageToolkit-Setup
SetupIconFile=..\assets\icon.ico
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes

[Files]
Source: "..\dist\LiveStageToolkit\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Live Stage Toolkit"; Filename: "{app}\LiveStageToolkit.exe"
Name: "{autodesktop}\Live Stage Toolkit"; Filename: "{app}\LiveStageToolkit.exe"

[Run]
Filename: "{app}\LiveStageToolkit.exe"; Description: "Launch Live Stage Toolkit"; Flags: postinstall nowait skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
