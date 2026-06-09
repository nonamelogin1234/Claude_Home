param(
    [switch]$Apply,
    [switch]$NoSync,
    [int]$Limit = 0,
    [string]$ProgressPath = ""
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

function Invoke-BwEncode {
    param([Parameter(Mandatory = $true)][string]$Json)

    $oldSession = $env:BW_SESSION
    $env:BW_SESSION = $script:BwSession
    try {
        $encoded = $Json | & bw encode 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "bw encode failed."
        }
        return ($encoded -join "").Trim()
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

function Test-Blank {
    param($Value)
    return [string]::IsNullOrWhiteSpace([string]$Value)
}

function Get-NormalizedHost {
    param($Item)

    $uris = @()
    if ($Item.login -and $Item.login.uris) {
        $uris = @($Item.login.uris)
    }

    foreach ($entry in $uris) {
        $raw = [string]$entry.uri
        if (Test-Blank $raw) { continue }

        $candidate = $raw.Trim()
        if ($candidate -notmatch '^[a-zA-Z][a-zA-Z0-9+.-]*://') {
            $candidate = "https://$candidate"
        }

        try {
            $uriHost = ([Uri]$candidate).Host.ToLowerInvariant()
            if ($uriHost.StartsWith("www.")) {
                $uriHost = $uriHost.Substring(4)
            }
            if (-not (Test-Blank $uriHost)) {
                return $uriHost
            }
        }
        catch {
            continue
        }
    }

    return $null
}

function Get-MaskedLogin {
    param([string]$Login)

    if (Test-Blank $Login) { return "" }
    if ($Login -match '^(.).+(@.+)$') {
        return "$($Matches[1])***$($Matches[2])"
    }
    if ($Login.Length -le 3) {
        return "***"
    }
    return "$($Login.Substring(0, 2))***"
}

function Test-GeneratedImportName {
    param([string]$Name)

    if (Test-Blank $Name) { return $true }
    $trimmed = $Name.Trim()
    return $trimmed -match '^(--+|no title|untitled|bez nazvaniya|\(no title\)|imported item|login item)$'
}

function Get-ItemActionPlan {
    param(
        [array]$Items,
        [hashtable]$FolderNameById = @{}
    )

    $seenCredentialKeys = @{}
    $actions = @()

    foreach ($item in $Items) {
        $siteHost = Get-NormalizedHost $item
        $username = if ($item.login) { [string]$item.login.username } else { "" }
        $password = if ($item.login) { [string]$item.login.password } else { "" }
        $hasUri = -not (Test-Blank $siteHost)
        $hasUsername = -not (Test-Blank $username)
        $hasPassword = -not (Test-Blank $password)
        $hasNotes = -not (Test-Blank $item.notes)
        $hasFields = $item.fields -and @($item.fields).Count -gt 0
        $newName = $null
        $targetFolder = $null
        $reason = $null

        if ((Test-GeneratedImportName $item.name) -and $hasUri) {
            $newName = $siteHost
            $reason = "rename-from-uri"
        }

        $isEffectivelyEmpty = (-not $hasUri) -and (-not $hasUsername) -and (-not $hasPassword) -and (-not $hasNotes) -and (-not $hasFields)
        if ($isEffectivelyEmpty) {
            $targetFolder = "00-review-trash"
            $reason = "empty-item"
        }
        elseif ((-not $hasUri) -and ($hasUsername -or $hasPassword)) {
            $targetFolder = "00-review-no-site"
            if (-not $reason) { $reason = "credentials-without-site" }
        }
        elseif ($hasUri -and $hasUsername -and $hasPassword) {
            $key = "$siteHost|$username|$password"
            if ($seenCredentialKeys.ContainsKey($key)) {
                $targetFolder = "00-review-duplicates"
                if (-not $reason) { $reason = "exact-duplicate-credential" }
            }
            else {
                $seenCredentialKeys[$key] = $item.id
            }
        }

        if ($newName -and $newName -eq [string]$item.name) {
            $newName = $null
        }

        if ($targetFolder -and $item.folderId -and $FolderNameById.ContainsKey($item.folderId) -and $FolderNameById[$item.folderId] -eq $targetFolder) {
            $targetFolder = $null
            if (-not $newName) {
                $reason = $null
            }
        }

        if ($newName -or $targetFolder) {
            $actions += [pscustomobject]@{
                id = $item.id
                oldName = [string]$item.name
                newName = $newName
                host = $siteHost
                maskedLogin = Get-MaskedLogin $username
                targetFolder = $targetFolder
                reason = $reason
            }
        }
    }

    return $actions
}

function Ensure-Folder {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [array]$Folders
    )

    $existing = @($Folders | Where-Object { $_.name -eq $Name } | Select-Object -First 1)
    if ($existing.Count -gt 0) {
        return $existing[0].id
    }

    $folderJson = @{ name = $Name } | ConvertTo-Json -Compress
    $encoded = Invoke-BwEncode $folderJson
    $created = Invoke-Bw -Arguments @("create", "folder", $encoded) -Json
    return $created.id
}

function Update-Item {
    param(
        [Parameter(Mandatory = $true)]$Item,
        [string]$NewName,
        [string]$FolderId
    )

    $Item = Invoke-Bw -Arguments @("get", "item", $Item.id) -Json

    if ($NewName) {
        $Item.name = $NewName
    }
    if ($FolderId) {
        $Item.folderId = $FolderId
    }

    $json = $Item | ConvertTo-Json -Depth 100 -Compress
    $encoded = Invoke-BwEncode $json
    Invoke-Bw -Arguments @("edit", "item", $Item.id, $encoded) | Out-Null
}

function Write-CleanupProgress {
    param(
        [int]$Applied,
        [int]$Total,
        [string]$CurrentReason,
        [string]$CurrentHost
    )

    if (Test-Blank $ProgressPath) { return }

    [pscustomobject]@{
        updatedAt = (Get-Date).ToString("o")
        applied = $Applied
        total = $Total
        remaining = [Math]::Max(0, $Total - $Applied)
        currentReason = $CurrentReason
        currentHost = $CurrentHost
    } | ConvertTo-Json | Set-Content -LiteralPath $ProgressPath -Encoding UTF8
}

New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
$script:BwSession = Get-PlainTextFromDpapiFile $sessionPath

Invoke-Bw -Arguments @("status") -Json | Out-Null
if (-not $NoSync) {
    Invoke-Bw -Arguments @("sync") | Out-Null
}

$folders = ConvertTo-ItemArray (Invoke-Bw -Arguments @("list", "folders") -Json)
$items = ConvertTo-ItemArray (Invoke-Bw -Arguments @("list", "items") -Json)
$folderNameById = @{}
foreach ($folder in $folders) {
    if ($folder.id) {
        $folderNameById[$folder.id] = $folder.name
    }
}
$actions = @(Get-ItemActionPlan -Items $items -FolderNameById $folderNameById)

$folderIds = @{}
$appliedCount = 0
if ($Apply) {
    foreach ($folderName in @("00-review-trash", "00-review-duplicates", "00-review-no-site")) {
        if ($actions.targetFolder -contains $folderName) {
            $folderIds[$folderName] = Ensure-Folder -Name $folderName -Folders $folders
        }
    }

    $itemById = @{}
    foreach ($item in $items) {
        $itemById[$item.id] = $item
    }

    $actionsToApply = $actions
    if ($Limit -gt 0) {
        $actionsToApply = @($actions | Select-Object -First $Limit)
    }

    Write-CleanupProgress -Applied 0 -Total $actionsToApply.Count -CurrentReason "start" -CurrentHost ""
    foreach ($action in $actionsToApply) {
        $folderId = $null
        if ($action.targetFolder) {
            $folderId = $folderIds[$action.targetFolder]
        }
        Update-Item -Item $itemById[$action.id] -NewName $action.newName -FolderId $folderId
        $appliedCount += 1
        Write-CleanupProgress -Applied $appliedCount -Total $actionsToApply.Count -CurrentReason $action.reason -CurrentHost $action.host
    }

    Invoke-Bw -Arguments @("sync") | Out-Null
}

$summary = [pscustomobject]@{
    generatedAt = (Get-Date).ToString("o")
    mode = if ($Apply) { "apply" } else { "audit" }
    totalItems = $items.Count
    actionCount = $actions.Count
    renameCount = @($actions | Where-Object { $_.newName }).Count
    emptyItemCount = @($actions | Where-Object { $_.reason -eq "empty-item" }).Count
    duplicateCount = @($actions | Where-Object { $_.reason -eq "exact-duplicate-credential" }).Count
    noSiteCount = @($actions | Where-Object { $_.targetFolder -eq "00-review-no-site" }).Count
    appliedCount = $appliedCount
    limit = $Limit
}

$reportPath = Join-Path $outputDir "audit-$stamp.md"
$jsonPath = Join-Path $outputDir "audit-$stamp.json"

$actions | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $jsonPath -Encoding UTF8

$lines = @()
$lines += "# Vaultwarden cleanup report"
$lines += ""
$lines += "- Generated: $($summary.generatedAt)"
$lines += "- Mode: $($summary.mode)"
$lines += "- Total items: $($summary.totalItems)"
$lines += "- Planned/applied actions: $($summary.actionCount)"
$lines += "- Renames: $($summary.renameCount)"
$lines += "- Empty items -> 00-review-trash: $($summary.emptyItemCount)"
$lines += "- Exact duplicates -> 00-review-duplicates: $($summary.duplicateCount)"
$lines += "- Credentials without site -> 00-review-no-site: $($summary.noSiteCount)"
$lines += "- Applied in this run: $($summary.appliedCount)"
$lines += ""
$lines += "## Actions"
$lines += ""
foreach ($action in $actions) {
    $namePart = if ($action.newName) { "`"$($action.oldName)`" -> `"$($action.newName)`"" } else { "`"$($action.oldName)`"" }
    $folderPart = if ($action.targetFolder) { " folder=$($action.targetFolder)" } else { "" }
    $lines += "- $($action.reason): $namePart host=$($action.host) login=$($action.maskedLogin)$folderPart"
}

$lines | Set-Content -LiteralPath $reportPath -Encoding UTF8

[pscustomobject]@{
    report = $reportPath
    json = $jsonPath
    summary = $summary
} | ConvertTo-Json -Depth 10
