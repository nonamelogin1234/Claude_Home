#Requires -RunAsAdministrator
# Claude VPN Killswitch — выключить (временно, для диагностики)

$ErrorActionPreference = 'Stop'

$rules = Get-NetFirewallRule -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -match '^Claude-KS-' }

if (-not $rules) {
    Write-Host "Правила killswitch не найдены (уже выключен или не был настроен)."
    exit 0
}

$rules | Remove-NetFirewallRule
Write-Host "Killswitch ВЫКЛЮЧЕН. Удалено правил: $($rules.Count)"
Write-Host "ВНИМАНИЕ: Claude теперь ходит в сеть напрямую без VPN!"
