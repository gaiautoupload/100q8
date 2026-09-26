$ErrorActionPreference='Stop'
$repo=Split-Path $PSScriptRoot -Parent
$private=Join-Path $repo '.local'
New-Item -ItemType Directory -Path $private -Force | Out-Null
if(-not $env:Q8_PASSWORDS){throw 'Provide Q8_PASSWORDS during installation'}
$secure=ConvertTo-SecureString -String $env:Q8_PASSWORDS -AsPlainText -Force
$credential=New-Object System.Management.Automation.PSCredential('100q8-publish',$secure)
$credential | Export-Clixml -LiteralPath (Join-Path $private 'publish-secret.xml')
$userId=[System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$action=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "'+(Join-Path $PSScriptRoot 'daily_update.ps1')+'"') -WorkingDirectory $repo
$trigger=New-ScheduledTaskTrigger -Daily -At '19:15'
$settings=New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable -MultipleInstances IgnoreNew -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 30) -ExecutionTimeLimit (New-TimeSpan -Hours 2)
$principal=New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName '100Q8 Champion Daily' -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description 'Replay P19 support30 from official local data, export encrypted dashboard and push GitHub Pages at 19:15. Requires signed-in user and upstream stock1 data.' -Force | Select-Object TaskName,State
