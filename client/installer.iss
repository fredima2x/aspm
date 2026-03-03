[Setup]
AppName=ASPM
AppVersion=1.0.0
AppPublisher=fredima
AppPublisherURL=https://fredima.de
AppSupportURL=https://fredima.de
DefaultDirName={autopf}\ASPM
DefaultGroupName=ASPM
AllowNoIcons=yes
OutputDir=installer_output
OutputBaseFilename=aspm-Setup-1.0.0
SetupIconFile=assets\logo.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardResizable=no
MinVersion=10.0

[Languages]
Name: "german";  MessagesFile: "compiler:Languages\German.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Desktop-Verknüpfung erstellen"; GroupDescription: "Symbole:"

[Files]
Source: "dist\aspm\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\ASPM";           Filename: "{app}\aspm.exe"
Name: "{group}\Deinstallieren"; Filename: "{uninstallexe}"
Name: "{commondesktop}\ASPM";   Filename: "{app}\aspm.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\aspm.exe"; Description: "ASPM starten"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"