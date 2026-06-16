Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$ErrorActionPreference = 'Stop'

$expectedIp = '186.246.22.35'
$checkUrl = 'https://api.ipify.org'
$intervalMs = 30000

function New-DotIcon([string]$color) {
    $bitmap = New-Object System.Drawing.Bitmap 16, 16
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.Clear([System.Drawing.Color]::Transparent)
    $brush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromName($color))
    $graphics.FillEllipse($brush, 1, 1, 13, 13)
    $graphics.Dispose()
    $iconHandle = $bitmap.GetHicon()
    return [System.Drawing.Icon]::FromHandle($iconHandle)
}

$greenIcon = New-DotIcon 'Lime'
$redIcon = New-DotIcon 'Red'
$grayIcon = New-DotIcon 'Gray'

$notifyIcon = New-Object System.Windows.Forms.NotifyIcon
$notifyIcon.Icon = $grayIcon
$notifyIcon.Visible = $true
$notifyIcon.Text = 'VPN IP: проверка...'

$menu = New-Object System.Windows.Forms.ContextMenuStrip
$refreshItem = $menu.Items.Add('Проверить сейчас')
$exitItem = $menu.Items.Add('Выход')
$notifyIcon.ContextMenuStrip = $menu

function Update-Status {
    try {
        $currentIp = (Invoke-RestMethod -Uri $checkUrl -TimeoutSec 8).Trim()
        if ($currentIp -eq $expectedIp) {
            $notifyIcon.Icon = $greenIcon
            $notifyIcon.Text = "VPN активен`nIP: $currentIp"
        } else {
            $notifyIcon.Icon = $redIcon
            $notifyIcon.Text = "VPN ВЫКЛЮЧЕН`nТекущий IP: $currentIp`nОжидался: $expectedIp"
        }
    } catch {
        $notifyIcon.Icon = $redIcon
        $notifyIcon.Text = "Нет ответа от $checkUrl`nПроверь интернет/VPN"
    }
}

$refreshItem.add_Click({ Update-Status })
$exitItem.add_Click({
    $notifyIcon.Visible = $false
    $timer.Stop()
    [System.Windows.Forms.Application]::Exit()
})

$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = $intervalMs
$timer.add_Tick({ Update-Status })
$timer.Start()

Update-Status

[System.Windows.Forms.Application]::Run()
