param(
    [string[]]$FolderNames = @("00-review-trash", "00-review-duplicates", "00-review-no-site"),
    [switch]$Permanent
)

$ErrorActionPreference = "Stop"

$secretDir = Join-Path $env:USERPROFILE ".codex-secrets"
$sessionPath = Join-Path $secretDir "bw-session.dpapi"
$outputDir = Join-Path (Get-Location) "outputs\vaultwarden-cleanup"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"

function Get-PlainTextFromDpapiFile {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Missing DPAPI session file: $Path"
    }

    $secure = Get-Content -LiteralPath $Path | ConvertTo-SecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    }
}

function Invoke-Bw {
    param(
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [switch]$Json
    )

    $oldSession = $env:BW_SESSION
    $env:BW_SESSION = $script:BwSession
    try {
        $output = & bw @Arguments 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "bw $($Arguments -join ' ') failed: $($output -join ' ')"
        }
        if ($Json) {
            return ($output -join "`n") | ConvertFrom-Json
        }
        return $output
    }
    finally {
        $env:BW_SESSION = $oldSession
    }
}

function ConvertTo-ItemArray {
    param($Value)

    if ($null -eq $Value) {
        return @()
    }

    if (($Value -is [array]) -and ($Value.Count -eq 1) -and ($Value[0] -is [array])) {
        return @($Value[0])
    }

    return @($Value)
}

New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
$script:BwSession = Get-PlainTextFromDpapiFile $sessionPath

Invoke-Bw -Arguments @("sync") | Out-Null
$folders = ConvertTo-ItemArray (Invoke-Bw -Arguments @("list", "folders") -Json)
$items = ConvertTo-ItemArray (Invoke-Bw -Arguments @("list", "items") -Json)

$targets = @()
foreach ($folderName in $FolderNames) {
    $folder = @($folders | Where-Object { $_.name -eq $folderName } | Select-Object -First 1)
    if ($folder.Count -eq 0) {
        continue
    }

    $folderItems = @($items | Where-Object { $_.folderId -eq $folder[0].id })
    foreach ($item in $folderItems) {
        $targets += [pscustomobject]@{
            id = $item.id
            folder = $folderName
        }
    }
}

$deleted = @()
foreach ($target in $targets) {
    $args = @("delete", "item", $target.id)
    if ($Permanent) {
        $args += "--permanent"
    }
    Invoke-Bw -Arguments $args | Out-Null
    $deleted += $target
}

Invoke-Bw -Arguments @("sync") | Out-Null

$report = [pscustomobject]@{
    generatedAt = (Get-Date).ToString("o")
    mode = if ($Permanent) { "permanent-delete" } else { "soft-delete" }
    folderNames = $FolderNames
    deletedCount = $deleted.Count
    byFolder = @($deleted | Group-Object folder | ForEach-Object {
        [pscustomobject]@{
            folder = $_.Name
            count = $_.Count
        }
    })
}

$reportPath = Join-Path $outputDir "archive-review-$stamp.json"
$report | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $reportPath -Encoding UTF8

[pscustomobject]@{
    report = $reportPath
    summary = $report
} | ConvertTo-Json -Depth 10
