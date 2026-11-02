; Novaboard - Windows Kurulum Betiği (Inno Setup 6)
; Geliştirici: Efe Saçlı

#define MyAppName "Novaboard"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Efe Saçlı"
#define MyAppExeName "Novaboard.exe"

[Setup]
AppId={{D37F8A21-7890-4B12-9C44-885E220199AA}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL=https://github.com/efesacli/sorufelek
AppSupportURL=https://github.com/efesacli/sorufelek
AppUpdatesURL=https://github.com/efesacli/sorufelek
VersionInfoCompany=Efe Saçlı
VersionInfoCopyright=Copyright (C) 2026 Efe Saçlı
VersionInfoDescription=Novaboard Kurulum (Geliştirici: Efe Saçlı)
VersionInfoProductName=Novaboard
VersionInfoProductVersion=1.0.0.0
VersionInfoVersion=1.0.0.0
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=.
OutputBaseFilename=Novaboard_Kurulum
SetupIconFile=icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UsedUserAreasWarning=no
UninstallDisplayIcon={app}\{#MyAppExeName}
CloseApplications=yes

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "taskbaricon"; Description: "Görev çubuğuna sabitle"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
Source: "Novaboard.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "KULLANIM_REHBERI.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\Kullanım Rehberi"; Filename: "{app}\KULLANIM_REHBERI.txt"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: taskbaricon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent runasoriginaluser

[Messages]
turkish.FinishedHeadingLabel=Novaboard Kurulumu Tamamlandı
turkish.FinishedLabel=Novaboard başarıyla bilgisayarınıza kuruldu.%n%nSeçilen kısayollar masaüstünüze ve görev çubuğunuza eklenmiştir.
