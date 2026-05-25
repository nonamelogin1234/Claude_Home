param(
    [switch] $SelfTest,
    [datetime] $TestNow
)

$ErrorActionPreference = 'Stop'

$StartPoint = [datetime]'2026-05-18T09:00:00'
$FinishPoint = [datetime]'2026-05-29T17:00:00'
$WorkdayStartHour = 9
$WorkdayEndHour = 17
$TotalSeconds = 80 * 60 * 60

# Counts only portions of weekdays that fall inside the configured working window.
function Get-WorkedSeconds {
    param([datetime] $Now)

    if ($Now -le $StartPoint) {
        return 0
    }

    $effectiveNow = if ($Now -ge $FinishPoint) { $FinishPoint } else { $Now }
    $seconds = 0.0
    $date = $StartPoint.Date

    while ($date -le $FinishPoint.Date) {
        if ($date.DayOfWeek -ne [DayOfWeek]::Saturday -and
            $date.DayOfWeek -ne [DayOfWeek]::Sunday) {
            $windowStart = $date.AddHours($WorkdayStartHour)
            $windowEnd = $date.AddHours($WorkdayEndHour)
            $periodStart = if ($windowStart -lt $StartPoint) { $StartPoint } else { $windowStart }
            $periodEnd = if ($windowEnd -gt $FinishPoint) { $FinishPoint } else { $windowEnd }
            $countUntil = if ($effectiveNow -lt $periodEnd) { $effectiveNow } else { $periodEnd }

            if ($countUntil -gt $periodStart) {
                $seconds += ($countUntil - $periodStart).TotalSeconds
            }
        }

        $date = $date.AddDays(1)
    }

    return [Math]::Min($TotalSeconds, [Math]::Max(0, [int][Math]::Floor($seconds)))
}

function Format-WorkingTime {
    param([int] $Seconds)

    $hours = [Math]::Floor($Seconds / 3600)
    $minutes = [Math]::Floor(($Seconds % 3600) / 60)
    $remainingSeconds = $Seconds % 60
    return '{0:00}:{1:00}:{2:00}' -f $hours, $minutes, $remainingSeconds
}

function Get-CountdownState {
    param([datetime] $Now)

    $workedSeconds = Get-WorkedSeconds -Now $Now
    $remainingSeconds = $TotalSeconds - $workedSeconds
    $fraction = $workedSeconds / $TotalSeconds

    if ($Now -ge $FinishPoint) {
        $status = 'Отпуск начался'
    } elseif ($Now -lt $StartPoint) {
        $status = 'Ожидаем начала отсчёта'
    } elseif ($Now.DayOfWeek -eq [DayOfWeek]::Saturday -or
              $Now.DayOfWeek -eq [DayOfWeek]::Sunday) {
        $status = 'Выходные • отсчёт на паузе'
    } elseif ($Now.TimeOfDay -lt [TimeSpan]::FromHours($WorkdayStartHour)) {
        $status = 'До 09:00 • отсчёт на паузе'
    } elseif ($Now.TimeOfDay -ge [TimeSpan]::FromHours($WorkdayEndHour)) {
        $status = 'После 17:00 • отсчёт на паузе'
    } else {
        $status = 'Рабочее время • идёт отсчёт'
    }

    return [pscustomobject]@{
        WorkedSeconds = $workedSeconds
        RemainingSeconds = $remainingSeconds
        Worked = Format-WorkingTime -Seconds $workedSeconds
        Remaining = Format-WorkingTime -Seconds $remainingSeconds
        Percentage = [string]::Format([Globalization.CultureInfo]::InvariantCulture, '{0:0.0}%', ($fraction * 100))
        Fraction = $fraction
        Status = $status
    }
}

if ($SelfTest) {
    $clock = if ($PSBoundParameters.ContainsKey('TestNow')) { $TestNow } else { [datetime]::Now }
    Get-CountdownState -Now $clock | ConvertTo-Json -Compress
    exit 0
}

Add-Type -AssemblyName PresentationFramework, PresentationCore, WindowsBase

$createdNew = $false
$mutex = New-Object System.Threading.Mutex($true, 'VacationTimerWidget-2026', [ref] $createdNew)
if (-not $createdNew) {
    $mutex.Dispose()
    exit 0
}

[xml] $xaml = @'
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="До отпуска"
        Width="215" Height="300"
        WindowStyle="None" AllowsTransparency="True" Background="Transparent"
        ResizeMode="NoResize" ShowInTaskbar="False" Topmost="True"
        UseLayoutRounding="True" SnapsToDevicePixels="True">
    <Window.Resources>
        <Color x:Key="TextPrimary">#FFF5F8FC</Color>
        <Color x:Key="TextMuted">#FF89A1BA</Color>
        <Color x:Key="Accent">#FF70E8D0</Color>
        <SolidColorBrush x:Key="PrimaryBrush" Color="{StaticResource TextPrimary}"/>
        <SolidColorBrush x:Key="MutedBrush" Color="{StaticResource TextMuted}"/>
        <SolidColorBrush x:Key="AccentBrush" Color="{StaticResource Accent}"/>
        <Style x:Key="ChromeButton" TargetType="Button">
            <Setter Property="Width" Value="35"/>
            <Setter Property="Height" Value="35"/>
            <Setter Property="Background" Value="Transparent"/>
            <Setter Property="Foreground" Value="#A7BCD0"/>
            <Setter Property="BorderThickness" Value="0"/>
            <Setter Property="Cursor" Value="Hand"/>
            <Setter Property="Template">
                <Setter.Value>
                    <ControlTemplate TargetType="Button">
                        <Border x:Name="Box" Background="{TemplateBinding Background}" CornerRadius="12">
                            <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                        </Border>
                        <ControlTemplate.Triggers>
                            <Trigger Property="IsMouseOver" Value="True">
                                <Setter TargetName="Box" Property="Background" Value="#18314945"/>
                                <Setter Property="Foreground" Value="#F5F8FC"/>
                            </Trigger>
                        </ControlTemplate.Triggers>
                    </ControlTemplate>
                </Setter.Value>
            </Setter>
        </Style>
    </Window.Resources>
    <Viewbox Stretch="Fill">
    <Grid Width="430" Height="600">
    <Grid Margin="14">
        <Border CornerRadius="30" BorderThickness="1.5" BorderBrush="#41597576">
            <Border.Effect>
                <DropShadowEffect Color="#081521" BlurRadius="38" ShadowDepth="18" Opacity="0.82"/>
            </Border.Effect>
            <Border.Background>
                <LinearGradientBrush StartPoint="0,0" EndPoint="1,1">
                    <GradientStop Color="#F1122032" Offset="0"/>
                    <GradientStop Color="#FA081728" Offset="0.52"/>
                    <GradientStop Color="#FA061322" Offset="1"/>
                </LinearGradientBrush>
            </Border.Background>
            <Grid>
                <Grid.RowDefinitions>
                    <RowDefinition Height="44"/>
                    <RowDefinition Height="336"/>
                    <RowDefinition Height="80"/>
                    <RowDefinition Height="58"/>
                    <RowDefinition Height="*"/>
                </Grid.RowDefinitions>

                <Grid x:Name="DragArea" Grid.Row="0" Margin="27,12,15,0" Background="Transparent">
                    <StackPanel Orientation="Horizontal" HorizontalAlignment="Right">
                        <Button x:Name="PinButton" Style="{StaticResource ChromeButton}" ToolTip="Поверх всех окон">
                            <Viewbox Width="18" Height="18">
                                <Path Data="M 12 2 L 22 12 L 18.3 13.4 L 15.2 16.5 L 13.7 22 L 11 14.9 L 3.7 11.8 L 9.3 10.3 L 12.4 7.2 Z M 11.3 14.5 L 4 22"
                                      Stroke="{Binding Foreground, RelativeSource={RelativeSource AncestorType=Button}}" StrokeThickness="1.6" Fill="Transparent"
                                      StrokeLineJoin="Round" StrokeStartLineCap="Round" StrokeEndLineCap="Round"/>
                            </Viewbox>
                        </Button>
                        <Button x:Name="CloseButton" Style="{StaticResource ChromeButton}" ToolTip="Закрыть">
                            <Viewbox Width="17" Height="17">
                                <Path Data="M 3 3 L 21 21 M 21 3 L 3 21" Stroke="{Binding Foreground, RelativeSource={RelativeSource AncestorType=Button}}" StrokeThickness="1.6"
                                      StrokeStartLineCap="Round"/>
                            </Viewbox>
                        </Button>
                    </StackPanel>
                </Grid>

                <Grid Grid.Row="1">
                    <Canvas Width="332" Height="332" HorizontalAlignment="Center" VerticalAlignment="Center">
                        <Ellipse Width="298" Height="298" Canvas.Left="17" Canvas.Top="17"
                                 Stroke="#233E5365" StrokeThickness="10"/>
                        <Path x:Name="ArcGlow" Stroke="#5570E8D0" StrokeThickness="19"
                              StrokeStartLineCap="Round" StrokeEndLineCap="Round">
                            <Path.Effect>
                                <BlurEffect Radius="16"/>
                            </Path.Effect>
                        </Path>
                        <Path x:Name="ArcProgress" StrokeThickness="11"
                              StrokeStartLineCap="Round" StrokeEndLineCap="Round">
                            <Path.Stroke>
                                <LinearGradientBrush StartPoint="0,0" EndPoint="1,1">
                                    <GradientStop Color="#38C7BE" Offset="0"/>
                                    <GradientStop Color="#83EFD5" Offset="1"/>
                                </LinearGradientBrush>
                            </Path.Stroke>
                        </Path>
                    </Canvas>
                    <StackPanel HorizontalAlignment="Center" VerticalAlignment="Center" Margin="0,8,0,0">
                        <TextBlock Text="До отпуска" FontFamily="Segoe UI" FontSize="24"
                                   Foreground="{StaticResource PrimaryBrush}" HorizontalAlignment="Center"/>
                        <TextBlock x:Name="RemainingText" Text="38:31:42" FontFamily="Segoe UI Semibold"
                                   FontSize="68" Foreground="{StaticResource PrimaryBrush}"
                                   HorizontalAlignment="Center" Margin="0,7,0,4"/>
                        <TextBlock Text="осталось рабочих часов" FontFamily="Segoe UI" FontSize="17"
                                   Foreground="{StaticResource MutedBrush}" HorizontalAlignment="Center"/>
                    </StackPanel>
                </Grid>

                <Grid Grid.Row="2" Margin="31,0,31,0">
                    <TextBlock HorizontalAlignment="Left" VerticalAlignment="Top" FontFamily="Segoe UI" FontSize="17">
                        <Run Text="Пройдено " Foreground="{StaticResource PrimaryBrush}"/>
                        <Run x:Name="WorkedText" Text="41:28:18" FontFamily="Segoe UI Semibold" Foreground="{StaticResource AccentBrush}"/>
                        <Run Text=" из 80:00:00" Foreground="{StaticResource MutedBrush}"/>
                    </TextBlock>
                    <Grid Margin="0,39,0,0">
                        <Grid.ColumnDefinitions>
                            <ColumnDefinition Width="*"/>
                            <ColumnDefinition Width="69"/>
                        </Grid.ColumnDefinitions>
                        <Border Height="10" Background="#1C314454" CornerRadius="5" Margin="0,5,12,0"
                                HorizontalAlignment="Stretch" VerticalAlignment="Top">
                            <Border x:Name="ProgressFill" HorizontalAlignment="Left" Width="0" Height="10" CornerRadius="5">
                                <Border.Background>
                                    <LinearGradientBrush StartPoint="0,0" EndPoint="1,0">
                                        <GradientStop Color="#31C3BF" Offset="0"/>
                                        <GradientStop Color="#73E8D2" Offset="1"/>
                                    </LinearGradientBrush>
                                </Border.Background>
                                <Border.Effect>
                                    <DropShadowEffect Color="#3DE7D3" BlurRadius="13" ShadowDepth="0" Opacity="0.7"/>
                                </Border.Effect>
                            </Border>
                        </Border>
                        <TextBlock x:Name="PercentageText" Grid.Column="1" Text="51.8%" FontFamily="Segoe UI Semibold"
                                   FontSize="21" Foreground="{StaticResource AccentBrush}" HorizontalAlignment="Right"/>
                    </Grid>
                </Grid>

                <Grid Grid.Row="3" Margin="30,0,30,0">
                    <Border Height="1" Background="#162D4050" VerticalAlignment="Top"/>
                    <TextBlock Text="Пн–Пт  •  09:00–17:00" FontFamily="Segoe UI" FontSize="16"
                               Foreground="{StaticResource PrimaryBrush}" VerticalAlignment="Center"/>
                    <TextBlock Text="29 мая  •  17:00" FontFamily="Segoe UI" FontSize="16"
                               Foreground="{StaticResource PrimaryBrush}" HorizontalAlignment="Right" VerticalAlignment="Center"/>
                </Grid>

                <Grid Grid.Row="4" Margin="30,0,30,0">
                    <Border Height="1" Background="#162D4050" VerticalAlignment="Top"/>
                    <StackPanel Orientation="Horizontal" HorizontalAlignment="Center" VerticalAlignment="Center">
                        <Ellipse Width="7" Height="7" Fill="{StaticResource AccentBrush}" Margin="0,1,10,0"/>
                        <TextBlock x:Name="StatusText" Text="Рабочее время • идёт отсчёт"
                                   FontFamily="Segoe UI" FontSize="16" Foreground="{StaticResource MutedBrush}"/>
                    </StackPanel>
                </Grid>
            </Grid>
        </Border>
    </Grid>
    </Grid>
    </Viewbox>
</Window>
'@

$reader = New-Object System.Xml.XmlNodeReader $xaml
$window = [Windows.Markup.XamlReader]::Load($reader)
$remainingText = $window.FindName('RemainingText')
$workedText = $window.FindName('WorkedText')
$percentageText = $window.FindName('PercentageText')
$progressFill = $window.FindName('ProgressFill')
$statusText = $window.FindName('StatusText')
$arcGlow = $window.FindName('ArcGlow')
$arcProgress = $window.FindName('ArcProgress')
$dragArea = $window.FindName('DragArea')
$pinButton = $window.FindName('PinButton')
$closeButton = $window.FindName('CloseButton')

# Produces the live circular progress segment used by both the sharp and glow strokes.
function New-ProgressArc {
    param([double] $Fraction)

    $center = 166.0
    $radius = 149.0
    $fractionSafe = [Math]::Min(0.9999, [Math]::Max(0.0001, $Fraction))
    $angle = $fractionSafe * 360.0
    $endAngle = ($angle - 90.0) * [Math]::PI / 180.0
    $start = New-Object Windows.Point -ArgumentList $center, ($center - $radius)
    $end = New-Object Windows.Point -ArgumentList ($center + $radius * [Math]::Cos($endAngle)), ($center + $radius * [Math]::Sin($endAngle))
    $size = New-Object Windows.Size -ArgumentList $radius, $radius
    $segment = New-Object Windows.Media.ArcSegment -ArgumentList $end, $size, 0, ($angle -gt 180), ([Windows.Media.SweepDirection]::Clockwise), $true
    $figure = New-Object Windows.Media.PathFigure
    $figure.StartPoint = $start
    $figure.Segments.Add($segment)
    $geometry = New-Object Windows.Media.PathGeometry
    $geometry.Figures.Add($figure)
    return $geometry
}

function Update-Widget {
    $state = Get-CountdownState -Now ([datetime]::Now)
    $remainingText.Text = $state.Remaining
    $workedText.Text = $state.Worked
    $percentageText.Text = $state.Percentage
    $statusText.Text = $state.Status
    $progressFill.Width = 276 * $state.Fraction
    $geometry = New-ProgressArc -Fraction $state.Fraction
    $arcGlow.Data = $geometry
    $arcProgress.Data = $geometry
}

# Lets the user move the widget from any non-button area of its surface.
$window.Add_MouseLeftButtonDown({
    if ($_.ChangedButton -ne [Windows.Input.MouseButton]::Left) {
        return
    }

    $element = $_.OriginalSource
    while ($null -ne $element -and $element -ne $window) {
        if ($element -is [Windows.Controls.Button]) {
            return
        }
        $element = [Windows.Media.VisualTreeHelper]::GetParent($element)
    }

    $window.DragMove()
})
$closeButton.Add_Click({ $window.Close() })
$pinButton.Add_Click({
    $window.Topmost = -not $window.Topmost
    $pinButton.Opacity = if ($window.Topmost) { 1.0 } else { 0.48 }
})

$workArea = [System.Windows.SystemParameters]::WorkArea
$window.Left = $workArea.Right - $window.Width - 28
$window.Top = $workArea.Bottom - $window.Height - 28

$timer = New-Object Windows.Threading.DispatcherTimer
$timer.Interval = [TimeSpan]::FromMilliseconds(250)
$timer.Add_Tick({ Update-Widget })
Update-Widget
$timer.Start()

try {
    [void] $window.ShowDialog()
} finally {
    $timer.Stop()
    $mutex.ReleaseMutex()
    $mutex.Dispose()
}
