param()

$ErrorActionPreference = "Stop"

$secretDir = Join-Path $env:USERPROFILE ".codex-secrets"
$sessionPath = Join-Path $secretDir "bw-session.dpapi"
$metaPath = Join-Path $secretDir "bw-session.meta.json"

New-Item -ItemType Directory -Force -Path $secretDir | Out-Null

Write-Host ""
Write-Host "Bitwarden CLI unlock"
Write-Host "Type the master password in this window. It will not be shown to Codex."
Write-Host "Only the temporary BW_SESSION token is stored locally via Windows DPAPI."
Write-Host ""

$session = & bw unlock --raw
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($session)) {
    throw "Bitwarden unlock failed."
}

$secureSession = ConvertTo-SecureString $session.Trim() -AsPlainText -Force
$secureSession | ConvertFrom-SecureString | Set-Content -LiteralPath $sessionPath -Encoding ASCII

[pscustomobject]@{
    createdAt = (Get-Date).ToString("o")
    user = $env:USERNAME
    host = $env:COMPUTERNAME
    purpose = "Temporary Bitwarden CLI session for Codex Vaultwarden cleanup"
} | ConvertTo-Json | Set-Content -LiteralPath $metaPath -Encoding UTF8

Write-Host ""
Write-Host "Done. Temporary session saved:"
Write-Host $sessionPath
Write-Host "You can close this window."
