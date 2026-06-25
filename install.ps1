# HYPERVOID Installer
$toolkitRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "  ╔═══════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "  ║  HYPERVOID Installer              ║" -ForegroundColor Magenta
Write-Host "  ╚═══════════════════════════════════╝" -ForegroundColor Magenta
Write-Host ""

# Desktop shortcut
$WshShell = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath("Desktop")
$lnk = $WshShell.CreateShortcut("$desktop\hypervoid.lnk")
$lnk.TargetPath = "python"
$lnk.Arguments = "$toolkitRoot\app.py"
$lnk.WorkingDirectory = $toolkitRoot
$lnk.Description = "HYPERVOID"
$lnk.Save()
Write-Host "  [OK] Desktop shortcut: hypervoid.lnk" -ForegroundColor Green

# PowerShell profile
$profilePath = $PROFILE.CurrentUserAllHosts
if (-not (Test-Path $profilePath)) {
    New-Item -ItemType File -Path $profilePath -Force | Out-Null
}

$existing = ""
if (Test-Path $profilePath) {
    $existing = Get-Content $profilePath -Raw -ErrorAction SilentlyContinue
}

# Remove old hv if present
if ($existing -and $existing -match "function hv ") {
    $lines = $existing -split "`n"
    $newLines = @()
    $skip = $false
    foreach ($line in $lines) {
        if ($line -match "^\s*# HYPERVOID\s*$") { $skip = $true; continue }
        if ($skip -and $line -match "^\s*function hv ") { $skip = $true; continue }
        if ($skip -and $line -match "^\s*\}\s*$") { $skip = $false; continue }
        if (-not $skip) { $newLines += $line }
    }
    $existing = $newLines -join "`n"
    Set-Content $profilePath $existing -Encoding utf8 -NoNewline
    Write-Host "  [OK] Removed old 'hv' command" -ForegroundColor Yellow
}

# Add hypervoid function
$func = "`n# HYPERVOID`nfunction hypervoid { Set-Location `"$toolkitRoot`"; python app.py }"

$current = ""
if (Test-Path $profilePath) {
    $current = Get-Content $profilePath -Raw -ErrorAction SilentlyContinue
}
if (-not $current -or $current -notmatch "function hypervoid") {
    Add-Content $profilePath $func -Encoding utf8
    Write-Host "  [OK] Command 'hypervoid' added" -ForegroundColor Green
} else {
    Write-Host "  [OK] Command 'hypervoid' exists" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "  Launch:" -ForegroundColor Cyan
Write-Host "    1. Double-click 'hypervoid' on Desktop" -ForegroundColor White
Write-Host "    2. Type: hypervoid" -ForegroundColor White
Write-Host "    3. python $toolkitRoot\app.py" -ForegroundColor White
Write-Host ""
