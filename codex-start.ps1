$ErrorActionPreference = "Stop"

$root = "C:\Users\no-na\Desktop\2027\Codex_Home"
Set-Location -LiteralPath $root

if (-not (Test-Path -LiteralPath ".git")) {
    Write-Host "No Git repository is cloned in $root yet."
    Write-Host "Clone one with: git clone <repo-url> ."
    exit 0
}

Write-Host "Repository:" (git remote get-url origin)
Write-Host "Branch:" (git branch --show-current)

git pull --ff-only

$contextFiles = @(
    "README.md",
    "CLAUDE.md",
    "AGENTS.md",
    "CONTRIBUTING.md",
    ".github\pull_request_template.md",
    ".github\copilot-instructions.md"
)

Write-Host ""
Write-Host "Context files found:"

foreach ($file in $contextFiles) {
    if (Test-Path -LiteralPath $file) {
        Write-Host "- $file"
    }
}

if (Test-Path -LiteralPath "docs") {
    Get-ChildItem -LiteralPath "docs" -Filter "*.md" -File -ErrorAction SilentlyContinue |
        ForEach-Object { Write-Host "- $($_.FullName.Substring($root.Length + 1))" }
}
