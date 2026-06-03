param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('On', 'Off')]
    [string]$Mode
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$SonyHfpMediaDevice = 'BTHHFENUM\BTHHFPAUDIO\9&155B9701&0&97'
$SonyStereoRenderId = '{0.0.0.00000000}.{2a373126-53df-4c77-b49b-25c72ed0cab5}'
$SonyHandsFreeRenderId = '{0.0.0.00000000}.{a699f755-4a2f-4d6a-8586-b7f4178ca13e}'
$SonyMicCaptureId = '{0.0.1.00000000}.{c5a5f9a7-bf2f-422f-80a7-b22b3083c2ce}'
$NvidiaBroadcastCaptureId = '{0.0.1.00000000}.{30cde97a-34db-4d85-8b8d-4a0c412a9d91}'
$LaptopMicCaptureId = '{0.0.1.00000000}.{a6d9fb97-b06d-4c8a-ae50-ea20125a9b0c}'

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Restart-AsAdministrator {
    $arguments = @(
        '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-File', "`"$PSCommandPath`"",
        '-Mode', $Mode
    )
    Start-Process -FilePath 'powershell.exe' -ArgumentList $arguments -Verb RunAs | Out-Null
}

function Add-AudioPolicyType {
    if ([type]::GetType('AudioPolicySwitcher', $false)) {
        return
    }

    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;

public enum AudioRole { Console = 0, Multimedia = 1, Communications = 2 }

[ComImport, Guid("f8679f50-850a-41cf-9c72-430f290290c8"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IPolicyConfig
{
    int GetMixFormat();
    int GetDeviceFormat();
    int ResetDeviceFormat();
    int SetDeviceFormat();
    int GetProcessingPeriod();
    int SetProcessingPeriod();
    int GetShareMode();
    int SetShareMode();
    int GetPropertyValue();
    int SetPropertyValue();
    [PreserveSig] int SetDefaultEndpoint([MarshalAs(UnmanagedType.LPWStr)] string deviceId, AudioRole role);
    [PreserveSig] int SetEndpointVisibility([MarshalAs(UnmanagedType.LPWStr)] string deviceId, bool visible);
}

[ComImport, Guid("870af99c-171d-4f9e-af0d-e63df40c2bc9")]
class PolicyConfigClient { }

public static class AudioPolicySwitcher
{
    public static void SetDefault(string deviceId)
    {
        IPolicyConfig policy = (IPolicyConfig)new PolicyConfigClient();
        policy.SetEndpointVisibility(deviceId, true);

        foreach (AudioRole role in Enum.GetValues(typeof(AudioRole)))
        {
            int hr = policy.SetDefaultEndpoint(deviceId, role);
            if (hr != 0)
            {
                Marshal.ThrowExceptionForHR(hr);
            }
        }
    }

    public static void SetVisible(string deviceId, bool visible)
    {
        IPolicyConfig policy = (IPolicyConfig)new PolicyConfigClient();
        int hr = policy.SetEndpointVisibility(deviceId, visible);
        if (hr != 0)
        {
            Marshal.ThrowExceptionForHR(hr);
        }
    }
}
'@
}

function Test-EndpointActive {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet('Capture', 'Render')]
        [string]$Kind,

        [Parameter(Mandatory = $true)]
        [string]$EndpointId
    )

    $guid = ($EndpointId -replace '^\{0\.0\.[01]\.00000000\}\.', '').ToLowerInvariant()
    $path = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\$Kind\$guid"
    if (-not (Test-Path $path)) {
        return $false
    }

    $state = (Get-ItemProperty -Path $path -Name DeviceState -ErrorAction SilentlyContinue).DeviceState
    return $state -eq 1
}

function Invoke-PnpUtil {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    $output = & pnputil.exe @Arguments 2>&1
    return ($output -join [Environment]::NewLine)
}

if (-not (Test-IsAdministrator)) {
    Restart-AsAdministrator
    exit
}

Add-AudioPolicyType

if ($Mode -eq 'On') {
    Invoke-PnpUtil -Arguments @('/enable-device', $SonyHfpMediaDevice) | Out-Null
    Start-Sleep -Seconds 2
    Invoke-PnpUtil -Arguments @('/restart-device', $SonyHfpMediaDevice) | Out-Null
    Start-Sleep -Seconds 4

    [AudioPolicySwitcher]::SetVisible($SonyMicCaptureId, $true)
    [AudioPolicySwitcher]::SetVisible($SonyHandsFreeRenderId, $true)
    [AudioPolicySwitcher]::SetDefault($SonyStereoRenderId)
    [AudioPolicySwitcher]::SetDefault($SonyMicCaptureId)

    Write-Host 'Sony WH-1000XM4 microphone is ON.'
    exit
}

$fallbackCaptureId = $NvidiaBroadcastCaptureId
if (-not (Test-EndpointActive -Kind Capture -EndpointId $fallbackCaptureId)) {
    $fallbackCaptureId = $LaptopMicCaptureId
}

[AudioPolicySwitcher]::SetDefault($SonyStereoRenderId)
[AudioPolicySwitcher]::SetDefault($fallbackCaptureId)
[AudioPolicySwitcher]::SetVisible($SonyMicCaptureId, $false)
[AudioPolicySwitcher]::SetVisible($SonyHandsFreeRenderId, $false)
Invoke-PnpUtil -Arguments @('/disable-device', $SonyHfpMediaDevice) | Out-Null
Start-Sleep -Seconds 2
[AudioPolicySwitcher]::SetDefault($SonyStereoRenderId)
[AudioPolicySwitcher]::SetDefault($fallbackCaptureId)

Write-Host 'Sony WH-1000XM4 microphone is OFF; stereo headphones remain ON.'
