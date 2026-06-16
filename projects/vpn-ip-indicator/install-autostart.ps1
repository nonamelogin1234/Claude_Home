$ErrorActionPreference = 'Stop'

$projectDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$launcherPath = Join-Path $projectDirectory 'launch-vpn-ip-indicator.vbs'
$startupFolder = [Environment]::GetFolderPath('Startup')
$shortcutPath = Join-Path $startupFolder 'VPN IP Indicator.lnk'

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = Join-Path $env:WINDIR 'System32\wscript.exe'
$shortcut.Arguments = '"' + $launcherPath + '"'
$shortcut.WorkingDirectory = $projectDirectory
$shortcut.Description = 'Индикатор VPN IP в трее: зелёный = VPN включён, красный = другой IP'
$shortcut.IconLocation = (Join-Path $env:WINDIR 'System32\shell32.dll') + ',13'
$shortcut.Save()

Write-Output "Ярлык добавлен в автозагрузку: $shortcutPath"
