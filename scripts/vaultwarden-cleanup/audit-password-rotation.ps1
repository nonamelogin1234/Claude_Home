param()

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

function Test-Blank {
    param($Value)
    return [string]::IsNullOrWhiteSpace([string]$Value)
}

function Get-NormalizedHost {
    param($Item)

    if (-not ($Item.login -and $Item.login.uris)) {
        return $null
    }

    foreach ($entry in @($Item.login.uris)) {
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

function Get-Sha256 {
    param([string]$Value)

    $bytes = [Text.Encoding]::UTF8.GetBytes($Value)
    $hash = [Security.Cryptography.SHA256]::Create().ComputeHash($bytes)
    return ([BitConverter]::ToString($hash)).Replace("-", "").ToLowerInvariant()
}

function Test-WeakPassword {
    param([string]$Password)

    if (Test-Blank $Password) { return $false }
    if ($Password.Length -lt 12) { return $true }
    if ($Password -match '^(.)\1+$') { return $true }
    if ($Password -match '^(123|qwerty|password|пароль|admin|111|000|йцукен)') { return $true }
    if ($Password -match '^[0-9]{1,10}$') { return $true }
    if ($Password -match '^[a-zA-Z]{1,10}$') { return $true }
    return $false
}

function Get-ServiceCategory {
    param(
        [string]$Name,
        [string]$HostName,
        [string]$Login
    )

    $text = "$Name $HostName".ToLowerInvariant()

    if ($text -match 'vault|bitwarden|vaultwarden|password') { return "password-manager" }
    if ($text -match "google|gmail|yandex|mail\.ru|live\.com|outlook|hotmail|email") { return "mail-identity" }
    if ($text -match "github|gitlab|notion|openai|grok|huggingface|supabase|api|token|oauth|timeweb|cloudflare|n8n|ssh|root|vps|server|myserver-ai|nextcloud|immich|homepage|monitor|rss|auth\.") { return "dev-infra" }
    if ($text -match "gosuslugi|sber|sbrf|bank|okx|crypto|wallet|qiwi|tele2|pay|payecom|budgetbakers") { return "finance-government" }
    if ($text -match "discord|telegram|facebook|twitter|x\.com|vk|twitch|snapchat|spotify|evernote") { return "personal-social" }
    if ($text -match "steam|ea|origin|xbox|playstation|epic|gog|poker|xbet|fon\.bet|parimatch|1xbet|pokerdom|888poker|amediateka|okko|kinopoisk|amazon|aliexpress") { return "commercial-entertainment" }
    return "low-priority"
}

function Get-ServiceImportance {
    param([string]$Category)

    switch ($Category) {
        "password-manager" { return "important" }
        "mail-identity" { return "important" }
        "dev-infra" { return "important" }
        "finance-government" { return "important" }
        "personal-social" { return "important" }
        default { return "low" }
    }
}

New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
$script:BwSession = Get-PlainTextFromDpapiFile $sessionPath

Invoke-Bw -Arguments @("sync") | Out-Null
$items = ConvertTo-ItemArray (Invoke-Bw -Arguments @("list", "items") -Json)

$passwordGroups = @{}
$records = @()

foreach ($item in $items) {
    if (-not $item.login) { continue }
    $password = [string]$item.login.password
    if (Test-Blank $password) { continue }

    $hash = Get-Sha256 $password
    if (-not $passwordGroups.ContainsKey($hash)) {
        $passwordGroups[$hash] = @()
    }
    $passwordGroups[$hash] += $item.id
}

foreach ($item in $items) {
    if (-not $item.login) { continue }
    $password = [string]$item.login.password
    if (Test-Blank $password) { continue }

    $hash = Get-Sha256 $password
    $reuseCount = @($passwordGroups[$hash]).Count
    $name = [string]$item.name
    $hostName = Get-NormalizedHost $item
    $login = [string]$item.login.username
    $category = Get-ServiceCategory -Name $name -HostName $hostName -Login $login
    $importance = Get-ServiceImportance -Category $category

    $reasons = @()
    if (Test-WeakPassword $password) { $reasons += "weak-or-short" }
    if ($reuseCount -gt 1) { $reasons += "reused-$reuseCount" }

    if ($reasons.Count -eq 0) { continue }

    $records += [pscustomobject]@{
        name = $name
        host = $hostName
        maskedLogin = Get-MaskedLogin $login
        category = $category
        importance = $importance
        passwordLength = $password.Length
        reuseCount = $reuseCount
        reasons = $reasons
    }
}

$important = @($records | Where-Object { $_.importance -eq "important" } | Sort-Object category, name, host, maskedLogin)
$low = @($records | Where-Object { $_.importance -eq "low" } | Sort-Object category, name, host, maskedLogin)

$report = [pscustomobject]@{
    generatedAt = (Get-Date).ToString("o")
    totalItems = $items.Count
    rotationCandidates = $records.Count
    importantCount = $important.Count
    lowPriorityCount = $low.Count
    important = $important
    lowPriority = $low
}

$jsonPath = Join-Path $outputDir "password-rotation-audit-$stamp.json"
$mdPath = Join-Path $outputDir "password-rotation-audit-$stamp.md"
$report | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $jsonPath -Encoding UTF8

$lines = @()
$lines += "# Vaultwarden password rotation audit"
$lines += ""
$lines += "- Generated: $($report.generatedAt)"
$lines += "- Total active items: $($report.totalItems)"
$lines += "- Rotation candidates: $($report.rotationCandidates)"
$lines += "- Important: $($report.importantCount)"
$lines += "- Low priority: $($report.lowPriorityCount)"
$lines += ""
$lines += "## Important"
$lines += ""
foreach ($entry in $important) {
    $lines += "- $($entry.name) | host=$($entry.host) | login=$($entry.maskedLogin) | category=$($entry.category) | reasons=$($entry.reasons -join ',')"
}
$lines += ""
$lines += "## Low priority"
$lines += ""
foreach ($entry in $low) {
    $lines += "- $($entry.name) | host=$($entry.host) | login=$($entry.maskedLogin) | category=$($entry.category) | reasons=$($entry.reasons -join ',')"
}

$lines | Set-Content -LiteralPath $mdPath -Encoding UTF8

[pscustomobject]@{
    json = $jsonPath
    markdown = $mdPath
    summary = [pscustomobject]@{
        totalItems = $report.totalItems
        rotationCandidates = $report.rotationCandidates
        importantCount = $report.importantCount
        lowPriorityCount = $report.lowPriorityCount
    }
} | ConvertTo-Json -Depth 10
