# deploy.ps1 — сборка и деплой RuRevitCommandSet
# Запускать из папки revit-mcp\
# Работает на любом ПК (путь берётся из $env:APPDATA)

$plugin = "$env:APPDATA\Autodesk\Revit\Addins\2024\revit_mcp_plugin"
$registryFile = "$plugin\commandRegistry.json"
$dotnet = "C:\Program Files\dotnet\dotnet.exe"

Write-Host "=== Сборка ===" -ForegroundColor Cyan
& $dotnet build src\RuRevitCommandSet.csproj
if ($LASTEXITCODE -ne 0) { Write-Host "ОШИБКА сборки" -ForegroundColor Red; exit 1 }

Write-Host "=== Обновление commandRegistry.json ===" -ForegroundColor Cyan

$entry = @{
    commandName            = "create_grid_ru"
    assemblyPath           = "RuRevitCommandSet\2024\RuRevitCommandSet.dll"
    enabled                = $true
    supportedRevitVersions = @("2024")
    developer              = @{ name = "Sergei"; organization = "RuRevitMCP" }
    description            = "Создать сетку осей с произвольными пролётами (мм)"
}

$reg = Get-Content $registryFile -Raw | ConvertFrom-Json
$exists = $reg.commands | Where-Object { $_.commandName -eq "create_grid_ru" }
if (-not $exists) {
    $reg.commands += $entry
    $reg | ConvertTo-Json -Depth 10 | Set-Content $registryFile -Encoding UTF8
    Write-Host "Команда добавлена в реестр" -ForegroundColor Green
} else {
    Write-Host "Команда уже в реестре, пропускаем" -ForegroundColor Yellow
}

Write-Host "=== Готово. Перезапусти Revit. ===" -ForegroundColor Green
