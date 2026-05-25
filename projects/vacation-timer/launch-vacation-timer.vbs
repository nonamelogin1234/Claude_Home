Option Explicit

Dim shell, files, folder, scriptPath, command
Set shell = CreateObject("WScript.Shell")
Set files = CreateObject("Scripting.FileSystemObject")
folder = files.GetParentFolderName(WScript.ScriptFullName)
scriptPath = files.BuildPath(folder, "vacation-timer.ps1")
command = "powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -WindowStyle Hidden -File """ & scriptPath & """"
shell.Run command, 0, False
