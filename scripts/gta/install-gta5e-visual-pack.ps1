param(
    [string]$GameDir = "C:\Download\Grand.Theft.Auto.V.Enhanced-InsaneRamZes",
    [string]$SourceDir = "C:\Download\GTA5E_codex_modding_BACKUP_20260619\content-visual-20260614",
    [switch]$SkipV4EverDownload,
    [switch]$LaunchReShadeSetup,
    [switch]$InstallDownloadedMapSubstitutes
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Assert-Path {
    param([string]$Path, [string]$Label)
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "$Label not found: $Path"
    }
}

function Copy-IfExists {
    param([string]$Path, [string]$Destination)
    if (Test-Path -LiteralPath $Path) {
        Copy-Item -LiteralPath $Path -Destination $Destination -Force
    }
}

function Get-GoogleDriveFile {
    param(
        [string]$FileId,
        [string]$OutFile
    )

    $directUrl = "https://drive.usercontent.google.com/download?id=$FileId&export=download&confirm=t"
    Write-Host "Downloading Google Drive payload..."
    Invoke-WebRequest -Uri $directUrl -OutFile $OutFile -UseBasicParsing

    $item = Get-Item -LiteralPath $OutFile
    if ($item.Length -lt 50MB) {
        $head = Get-Content -LiteralPath $OutFile -Raw -ErrorAction SilentlyContinue
        if ($head -match "<html|Google Drive|virus scan|quota|sign in") {
            throw "Google Drive did not return the real V4EVER archive. Download it manually from https://drive.google.com/file/d/$FileId/view?usp=sharing and put it next to this script/source folder, then rerun."
        }
    }
}

function New-LiteReShadePreset {
    param([string]$PresetPath)

    @"
PreprocessorDefinitions=
Techniques=CAS,Curves,Vibrance,Tonemap
TechniqueSorting=CAS,Curves,Vibrance,Tonemap

[CAS.fx]
Contrast=0.000000
Sharpening=0.420000

[Curves.fx]
Contrast=0.180000
Formula=4
Mode=0

[Vibrance.fx]
Vibrance=0.110000
VibranceRGBBalance=1.000000,1.000000,1.000000

[Tonemap.fx]
Bleach=0.000000
Defog=0.000000
Exposure=0.000000
FogColor=0.000000,0.000000,1.000000
Gamma=1.000000
Saturation=0.030000
"@ | Set-Content -LiteralPath $PresetPath -Encoding ASCII
}

function New-RollbackScript {
    param(
        [string]$RollbackPath,
        [string]$BackupDir,
        [string]$GameDir
    )

    $text = @"
@echo off
setlocal
set "GAME=$GameDir"
set "BACKUP=$BackupDir"
echo Restoring Codex visual pack backup...
if exist "%BACKUP%\update.rpf" copy /Y "%BACKUP%\update.rpf" "%GAME%\mods\update\update.rpf"
if exist "%BACKUP%\Outfit" (
  rmdir /S /Q "%GAME%\menyooStuff\Outfit"
  xcopy /E /I /Y "%BACKUP%\Outfit" "%GAME%\menyooStuff\Outfit"
)
if exist "%GAME%\mods\update\x64\dlcpacks\v4evermod" rmdir /S /Q "%GAME%\mods\update\x64\dlcpacks\v4evermod"
if exist "%BACKUP%\custom_maps" (
  rmdir /S /Q "%GAME%\mods\update\x64\dlcpacks\custom_maps"
  xcopy /E /I /Y "%BACKUP%\custom_maps" "%GAME%\mods\update\x64\dlcpacks\custom_maps"
) else (
  if exist "%GAME%\mods\update\x64\dlcpacks\custom_maps" rmdir /S /Q "%GAME%\mods\update\x64\dlcpacks\custom_maps"
)
del /F /Q "%GAME%\CodexLite_NoRT.ini" 2>nul
del /F /Q "%GAME%\ReShade.ini" 2>nul
del /F /Q "%GAME%\dxgi.ini" 2>nul
del /F /Q "%GAME%\dxgi.dll" 2>nul
if exist "%GAME%\reshade-shaders" rmdir /S /Q "%GAME%\reshade-shaders"
echo Done. If ReShade was installed through its setup, uninstall/disable it there too if needed.
pause
"@
    $text | Set-Content -LiteralPath $RollbackPath -Encoding ASCII
}

$sevenZip = "C:\Program Files\7-Zip\7z.exe"
$oivHelper = "C:\Download\GTA5E_codex_modding_BACKUP_20260619\tools\OivDirectHelper\bin\Debug\net8.0-windows\OivDirectHelper.exe"
$addonHelper = "C:\Download\GTA5E_codex_modding_BACKUP_20260619\tools\AddonEnableHelper\bin\Debug\net8.0-windows\AddonEnableHelper.exe"
$ultimateArchive = Join-Path $SourceDir "b54e86-UltimateOutfitPackv3.rar"
$v4everInstructionArchive = Join-Path $SourceDir "ca8bdc-GTA5 V4EVERMOD 1.1 Enhanced.rar"
$mirrorParkArchive = Join-Path $SourceDir "acaa81-v4ever Mirror Park Update.rar"
$reshadeSetupLocal = Join-Path $SourceDir "ReShade_Setup_6.7.3.exe"
$v4everFileId = "1gP1UXnGlWBXUnLCpx80CXQOAZxcPLhdg"

Write-Step "Preflight"
Assert-Path $GameDir "GTA V Enhanced folder"
Assert-Path (Join-Path $GameDir "GTA5_Enhanced.exe") "GTA5_Enhanced.exe"
Assert-Path $SourceDir "Source folder"
Assert-Path $sevenZip "7-Zip"
Assert-Path $ultimateArchive "Ultimate Outfit Pack archive"
Assert-Path $addonHelper "AddonEnableHelper"

$running = Get-Process -Name "GTA5_Enhanced","PlayGTAV" -ErrorAction SilentlyContinue
if ($running) {
    throw "GTA is running. Exit the game before installing."
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$workDir = Join-Path $GameDir "_codex_modding\visual_pack_$stamp"
$backupDir = Join-Path $GameDir "_codex_backup_visual_pack_$stamp"
$downloadDir = Join-Path $workDir "downloads"
$extractDir = Join-Path $workDir "extract"

New-Item -ItemType Directory -Force -Path $workDir, $backupDir, $downloadDir, $extractDir | Out-Null

Write-Step "Backup"
Copy-IfExists -Path (Join-Path $GameDir "mods\update\update.rpf") -Destination (Join-Path $backupDir "update.rpf")
if (Test-Path -LiteralPath (Join-Path $GameDir "menyooStuff\Outfit")) {
    Copy-Item -LiteralPath (Join-Path $GameDir "menyooStuff\Outfit") -Destination (Join-Path $backupDir "Outfit") -Recurse -Force
}
Copy-IfExists -Path (Join-Path $GameDir "CodexLite_NoRT.ini") -Destination (Join-Path $backupDir "CodexLite_NoRT.ini.bak")
Copy-IfExists -Path (Join-Path $GameDir "ReShade.ini") -Destination (Join-Path $backupDir "ReShade.ini.bak")
Copy-IfExists -Path (Join-Path $GameDir "dxgi.ini") -Destination (Join-Path $backupDir "dxgi.ini.bak")
Copy-IfExists -Path (Join-Path $GameDir "dxgi.dll") -Destination (Join-Path $backupDir "dxgi.dll.bak")
if (Test-Path -LiteralPath (Join-Path $GameDir "mods\update\x64\dlcpacks\custom_maps")) {
    Copy-Item -LiteralPath (Join-Path $GameDir "mods\update\x64\dlcpacks\custom_maps") -Destination (Join-Path $backupDir "custom_maps") -Recurse -Force
}
if (Test-Path -LiteralPath (Join-Path $GameDir "reshade-shaders")) {
    Copy-Item -LiteralPath (Join-Path $GameDir "reshade-shaders") -Destination (Join-Path $backupDir "reshade-shaders") -Recurse -Force
}

$rollbackPath = Join-Path $GameDir "_codex_rollback_visual_pack_$stamp.cmd"
New-RollbackScript -RollbackPath $rollbackPath -BackupDir $backupDir -GameDir $GameDir
Write-Host "Rollback script: $rollbackPath"

Write-Step "Install Ultimate Outfit Pack for Menyoo"
$outfitExtract = Join-Path $extractDir "UltimateOutfitPack"
New-Item -ItemType Directory -Force -Path $outfitExtract | Out-Null
& $sevenZip x $ultimateArchive "-o$outfitExtract" -y | Out-Host
$srcOutfit = Join-Path $outfitExtract "Outfit"
Assert-Path $srcOutfit "Extracted Outfit folder"
$dstOutfit = Join-Path $GameDir "menyooStuff\Outfit"
New-Item -ItemType Directory -Force -Path $dstOutfit | Out-Null
robocopy $srcOutfit $dstOutfit /E /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -gt 7) { throw "Robocopy failed while installing outfits. Code: $LASTEXITCODE" }

Write-Step "Prepare lightweight ReShade preset"
$presetPath = Join-Path $GameDir "CodexLite_NoRT.ini"
New-LiteReShadePreset -PresetPath $presetPath
$reshadeSetup = Join-Path $downloadDir "ReShade_Setup_6.7.3.exe"
if (Test-Path -LiteralPath $reshadeSetupLocal) {
    Copy-Item -LiteralPath $reshadeSetupLocal -Destination $reshadeSetup -Force
} else {
    try {
        Invoke-WebRequest -Uri "https://reshade.me/downloads/ReShade_Setup_6.7.3.exe" -OutFile $reshadeSetup -UseBasicParsing
        Write-Host "Downloaded official ReShade setup: $reshadeSetup"
    } catch {
        Write-Warning "Could not download ReShade setup automatically: $($_.Exception.Message)"
    }
}

if (Test-Path -LiteralPath $reshadeSetup) {
    $reshadeExtract = Join-Path $extractDir "ReShadeSetup"
    New-Item -ItemType Directory -Force -Path $reshadeExtract | Out-Null
    & $sevenZip x $reshadeSetup "-o$reshadeExtract" "ReShade64.dll" -y | Out-Host
    $reshadeDll = Join-Path $reshadeExtract "ReShade64.dll"
    if (Test-Path -LiteralPath $reshadeDll) {
        Copy-Item -LiteralPath $reshadeDll -Destination (Join-Path $GameDir "dxgi.dll") -Force
    }
}

if ($LaunchReShadeSetup -and (Test-Path -LiteralPath $reshadeSetup)) {
    Write-Host "Launching ReShade setup. Choose GTA5_Enhanced.exe, DirectX 10/11/12, and preset CodexLite_NoRT.ini."
    Start-Process -FilePath $reshadeSetup -ArgumentList "`"$GameDir\GTA5_Enhanced.exe`""
}

$shaderRoot = Join-Path $GameDir "reshade-shaders"
$shaderDir = Join-Path $shaderRoot "Shaders"
$textureDir = Join-Path $shaderRoot "Textures"
New-Item -ItemType Directory -Force -Path $shaderDir, $textureDir | Out-Null
$shaderUrls = @{
    "CAS.fx" = "https://raw.githubusercontent.com/crosire/reshade-shaders/slim/Shaders/CAS.fx"
    "Curves.fx" = "https://raw.githubusercontent.com/crosire/reshade-shaders/slim/Shaders/Curves.fx"
    "Vibrance.fx" = "https://raw.githubusercontent.com/crosire/reshade-shaders/slim/Shaders/Vibrance.fx"
    "Tonemap.fx" = "https://raw.githubusercontent.com/crosire/reshade-shaders/slim/Shaders/Tonemap.fx"
}
foreach ($pair in $shaderUrls.GetEnumerator()) {
    $target = Join-Path $shaderDir $pair.Key
    try {
        Invoke-WebRequest -Uri $pair.Value -OutFile $target -UseBasicParsing
    } catch {
        Write-Warning "Could not download shader $($pair.Key): $($_.Exception.Message)"
    }
}

$reshadeIni = @"
[GENERAL]
CurrentPresetPath=$presetPath
EffectSearchPaths=$shaderDir
TextureSearchPaths=$textureDir
PerformanceMode=1
ShowFPS=0
TutorialProgress=4

[INPUT]
KeyEffects=118,0,0,0
KeyMenu=36,0,1,0
KeyReload=119,0,0,0
"@
$reshadeIni | Set-Content -LiteralPath (Join-Path $GameDir "ReShade.ini") -Encoding ASCII
$reshadeIni | Set-Content -LiteralPath (Join-Path $GameDir "dxgi.ini") -Encoding ASCII

if ($InstallDownloadedMapSubstitutes) {
    Write-Step "Install downloaded V4EVER map substitute: Mirror Park"
    Assert-Path $mirrorParkArchive "Mirror Park archive"
    $mirrorExtract = Join-Path $extractDir "MirrorPark"
    New-Item -ItemType Directory -Force -Path $mirrorExtract | Out-Null
    & $sevenZip x $mirrorParkArchive "-o$mirrorExtract" -y | Out-Host
    $customMapsSource = Get-ChildItem -LiteralPath $mirrorExtract -Recurse -Directory -Force |
        Where-Object { $_.Name -ieq "custom_maps" } |
        Select-Object -First 1
    Assert-Path $customMapsSource.FullName "Mirror Park custom_maps folder"
    $customMapsTarget = Join-Path $GameDir "mods\update\x64\dlcpacks\custom_maps"
    New-Item -ItemType Directory -Force -Path (Split-Path $customMapsTarget -Parent) | Out-Null
    if (Test-Path -LiteralPath $customMapsTarget) {
        Remove-Item -LiteralPath $customMapsTarget -Recurse -Force
    }
    Copy-Item -LiteralPath $customMapsSource.FullName -Destination $customMapsTarget -Recurse -Force
    & $addonHelper $GameDir "custom_maps" | Out-Host
}

Write-Step "Install V4EVER Mega Mod"
$v4everArchive = Get-ChildItem -LiteralPath $SourceDir -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match "V4EVER" -and $_.Length -gt 50MB } |
    Sort-Object Length -Descending |
    Select-Object -First 1

if (-not $v4everArchive) {
    $candidate = Join-Path $downloadDir "GTA5_V4EVERMOD_1.1_Enhanced.rar"
    if ($SkipV4EverDownload) {
        Write-Warning "V4EVER real archive is missing. The local 616-byte archive only contains Google Drive instructions."
    } else {
        Get-GoogleDriveFile -FileId $v4everFileId -OutFile $candidate
        $v4everArchive = Get-Item -LiteralPath $candidate
    }
}

if ($v4everArchive) {
    $v4extract = Join-Path $extractDir "V4EVER"
    New-Item -ItemType Directory -Force -Path $v4extract | Out-Null
    & $sevenZip x $v4everArchive.FullName "-o$v4extract" -y | Out-Host

    $oiv = Get-ChildItem -LiteralPath $v4extract -Recurse -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -ieq ".oiv" } |
        Select-Object -First 1
    $dlcFolder = Get-ChildItem -LiteralPath $v4extract -Recurse -Directory -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ieq "v4evermod" } |
        Select-Object -First 1

    if ($dlcFolder) {
        $targetDlc = Join-Path $GameDir "mods\update\x64\dlcpacks\v4evermod"
        New-Item -ItemType Directory -Force -Path (Split-Path $targetDlc -Parent) | Out-Null
        if (Test-Path -LiteralPath $targetDlc) {
            Remove-Item -LiteralPath $targetDlc -Recurse -Force
        }
        Copy-Item -LiteralPath $dlcFolder.FullName -Destination $targetDlc -Recurse -Force
        & $addonHelper $GameDir "v4evermod" | Out-Host
    } elseif ($oiv -and (Test-Path -LiteralPath $oivHelper)) {
        Write-Warning "No v4evermod folder found; installing OIV package with CodeWalker helper."
        & $oivHelper $GameDir $oiv.FullName | Out-Host
        & $addonHelper $GameDir "v4evermod" | Out-Host
    } else {
        throw "V4EVER archive extracted, but no v4evermod folder or OIV package was found."
    }
} else {
    Write-Warning "V4EVER was not installed because the real archive is missing."
    if (Test-Path -LiteralPath $v4everInstructionArchive) {
        Write-Host "Instruction archive exists here: $v4everInstructionArchive"
        Write-Host "Download real payload from: https://drive.google.com/file/d/$v4everFileId/view?usp=sharing"
    }
}

Write-Step "Verification"
$checks = [ordered]@{
    "Ultimate outfits target" = (Join-Path $GameDir "menyooStuff\Outfit")
    "ReShade preset" = (Join-Path $GameDir "CodexLite_NoRT.ini")
    "ReShade dxgi.dll" = (Join-Path $GameDir "dxgi.dll")
    "Mirror Park custom_maps" = (Join-Path $GameDir "mods\update\x64\dlcpacks\custom_maps")
    "V4EVER dlcpack" = (Join-Path $GameDir "mods\update\x64\dlcpacks\v4evermod")
    "Rollback script" = $rollbackPath
}

foreach ($item in $checks.GetEnumerator()) {
    $ok = Test-Path -LiteralPath $item.Value
    Write-Host ("{0}: {1}" -f $item.Key, $(if ($ok) { "OK" } else { "MISSING" }))
}

Write-Host ""
Write-Host "Done. ReShade preset is CodexLite_NoRT.ini. In Menyoo: Player Options -> Wardrobe -> Outfits."
Write-Host "If the game fails to start, run rollback: $rollbackPath"
