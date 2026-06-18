#Requires -RunAsAdministrator
# Claude VPN Killswitch — включить
# Блокирует Claude на всех адаптерах кроме AmneziaVPN

$ErrorActionPreference = 'Stop'

$vpnAdapter = 'AmneziaVPN'
$vpnIpv4    = '10.8.1.2'
$vpnIpv6    = 'fd58:baa6:dead::1'

# Все EXE которые нужно ограничить
$claudioExes = @(
    # Ищем динамически — path меняется при обновлениях
    (Get-ChildItem 'C:\Program Files\WindowsApps' -Filter 'claude.exe' -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -match 'Claude_' } | Select-Object -First 1 -ExpandProperty FullName),
    (Get-ChildItem "$env:LOCALAPPDATA\Packages\Claude_pzs8sxrjxfjjc" -Filter 'claude.exe' -Recurse -ErrorAction SilentlyContinue |
        Select-Object -First 1 -ExpandProperty FullName)
) | Where-Object { $_ -and (Test-Path $_) }

if (-not $claudioExes) {
    Write-Error "Claude exe не найден. Проверь пути вручную."
    exit 1
}

# Адаптеры для блокировки — все кроме VPN
$blockAdapters = (Get-NetAdapter | Where-Object { $_.Name -ne $vpnAdapter } | Select-Object -ExpandProperty Name)

Write-Host "Claude exes:"
$claudioExes | ForEach-Object { Write-Host "  $_" }
Write-Host "Block adapters:"
$blockAdapters | ForEach-Object { Write-Host "  $_" }

$i = 0
foreach ($exe in $claudioExes) {
    $tag = "Claude-KS-$i"

    # Удалить старые правила с этим тегом если есть
    Get-NetFirewallRule -DisplayName "$tag*" -ErrorAction SilentlyContinue | Remove-NetFirewallRule

    # Блок на не-VPN интерфейсах (IPv4 и IPv6)
    New-NetFirewallRule `
        -Name          "$tag-Block-NoVPN" `
        -DisplayName   "$tag-Block-NoVPN" `
        -Description   "Claude KS: блокировать на не-VPN адаптерах" `
        -Direction     Outbound `
        -Action        Block `
        -Program       $exe `
        -InterfaceAlias $blockAdapters `
        -Profile       Any `
        -Enabled       True | Out-Null

    # Дополнительно: блок IPv6 link-local (fe80::) который может вытечь мимо VPN
    New-NetFirewallRule `
        -Name          "$tag-Block-IPv6-Linklocal" `
        -DisplayName   "$tag-Block-IPv6-Linklocal" `
        -Description   "Claude KS: блокировать IPv6 link-local" `
        -Direction     Outbound `
        -Action        Block `
        -Program       $exe `
        -RemoteAddress "fe80::/10" `
        -Profile       Any `
        -Enabled       True | Out-Null

    Write-Host "[$i] Правила созданы для: $(Split-Path $exe -Leaf) ($exe)"
    $i++
}

Write-Host ""
Write-Host "Killswitch ВКЛЮЧЁН. Claude работает только через AmneziaVPN ($vpnIpv4)."
