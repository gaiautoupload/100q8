$ErrorActionPreference='Stop'
$repo=Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $repo
$private=Join-Path $repo '.local'
New-Item -ItemType Directory -Path $private -Force | Out-Null
Start-Transcript -Path (Join-Path $private ('daily-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.log')) | Out-Null
try {
    $lab=Join-Path (Split-Path $repo -Parent) 'race-five-stock-lab'
    $python='C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe'
    $node='C:\Users\user\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
    & $python (Join-Path $lab 'update_champion.py')
    if($LASTEXITCODE -ne 0){throw 'Strategy replay failed'}
    & $python scripts/export_dashboard.py --lab $lab
    if($LASTEXITCODE -ne 0){throw 'Export failed'}
    $credential=Import-Clixml -LiteralPath (Join-Path $private 'publish-secret.xml')
    $env:Q8_PASSWORDS=$credential.GetNetworkCredential().Password
    & $node scripts/encrypt_dashboard.mjs
    if($LASTEXITCODE -ne 0){throw 'Encryption failed'}
    Remove-Item Env:\Q8_PASSWORDS
    & git -c "safe.directory=$repo" diff --cached --quiet
    if($LASTEXITCODE -ne 0){throw 'Existing staged changes; publish stopped'}
    & git -c "safe.directory=$repo" diff --quiet -- data/dashboard.secure.json
    if($LASTEXITCODE -eq 0){
        & git -c "safe.directory=$repo" push origin main
        if($LASTEXITCODE -ne 0){throw 'Git retry push failed'}
        exit 0
    }
    & git -c "safe.directory=$repo" add -- data/dashboard.secure.json
    if($LASTEXITCODE -ne 0){throw 'Git stage failed'}
    & git -c "safe.directory=$repo" commit -m 'Update champion daily model and orders'
    if($LASTEXITCODE -ne 0){throw 'Git commit failed'}
    & git -c "safe.directory=$repo" push origin main
    if($LASTEXITCODE -ne 0){throw 'Git push failed; local commit retained for retry'}
} finally {
    Remove-Item Env:\Q8_PASSWORDS -ErrorAction SilentlyContinue
    Stop-Transcript | Out-Null
}
