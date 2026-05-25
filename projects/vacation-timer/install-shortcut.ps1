$ErrorActionPreference = 'Stop'

$projectDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$launcherPath = Join-Path $projectDirectory 'launch-vacation-timer.vbs'
$desktopPath = [Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktopPath 'До отпуска.lnk'

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = Join-Path $env:WINDIR 'System32\wscript.exe'
$shortcut.Arguments = '"' + $launcherPath + '"'
$shortcut.WorkingDirectory = $projectDirectory
$shortcut.Description = 'Таймер рабочих часов до отпуска'
$shortcut.IconLocation = (Join-Path $env:WINDIR 'System32\shell32.dll') + ',266'
$shortcut.Save()

Write-Output $shortcutPath
