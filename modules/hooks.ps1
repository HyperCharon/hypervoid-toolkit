# Hook Manager - TUI Version

$script:HookList = @(
    @{ N='Auto Format';  D='Prettier/Black after edits';  E='PostToolUse'; M='Write|Edit'; H='npx prettier --write $CLAUDE_FILE_PATH' }
    @{ N='Auto Lint';    D='ESLint after edits';           E='PostToolUse'; M='Write|Edit'; H='npx eslint $CLAUDE_FILE_PATH --fix' }
    @{ N='Audit Log';    D='Log all tool usage';           E='PreToolUse';  M='.*';         H='echo "$(date): $CLAUDE_TOOL_NAME" >> .claude/audit.log' }
    @{ N='Safety Guard'; D='Block dangerous commands';     E='PreToolUse';  M='Bash';       H='if ($input -match "rm -rf") { exit 1 }' }
    @{ N='Auto Test';    D='Run tests after changes';      E='PostToolUse'; M='Write|Edit'; H='npm test 2>&1 | Select-Object -Last 20' }
    @{ N='Notification'; D='System notification';           E='Notification';M='';           H='msg * /TIME:5 "Claude needs attention"' }
)

function Invoke-Hooks {
    $T = $script:Theme
    $sel = 0

    while ($true) {
        Clear-Screen
        $w = $script:Screen.Width; $h = $script:Screen.Height

        Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
        Write-Centered 1 '[#] HOOK MANAGER' 'White' $T.HeaderBG

        Draw-Box 3 4 ($w-6) ($h-8) $T.Border $T.BG $T.Title ' HOOK TEMPLATES '

        for ($i = 0; $i -lt $script:HookList.Count; $i++) {
            $hk = $script:HookList[$i]
            $iy = 6 + $i * 2
            $isSel = ($i -eq $sel)
            if ($isSel) {
                Fill-Rect 5 $iy ($w-12) 1 ' ' $T.Selection $T.SelBG
                Write-Text 7 $iy "[$($i+1)] $($hk.N)" $T.Selection $T.SelBG
                Write-Text 7 ($iy+1) "  $($hk.D) | $($hk.E)" $T.Accent
            } else {
                Write-Text 7 $iy "[$($i+1)] $($hk.N)" $T.MenuLabel
                Write-Text 7 ($iy+1) "  $($hk.D)" $T.Dim
            }
        }

        Draw-Status ' [1-6] Select Hook ' '[Enter] Install' '[Esc] Back' 'Black' $T.StatusBG
        Flush-Screen

        $key = Read-Key
        if (Is-EscKey $key -or (Is-CharKey $key 'q')) { return }
        if (Is-UpKey $key) { $sel = ($sel - 1 + $script:HookList.Count) % $script:HookList.Count }
        if (Is-DownKey $key) { $sel = ($sel + 1) % $script:HookList.Count }
        if (Is-EnterKey $key) { Install-HookTui $script:HookList[$sel] }
        if ($key.Character -match '[1-6]') { $sel = [int]$key.Character.ToString() - 1; Install-HookTui $script:HookList[$sel] }
    }
}

function Install-HookTui {
    param($Hook)
    $T = $script:Theme
    Clear-Screen
    $w = $script:Screen.Width; $h = $script:Screen.Height

    Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
    Write-Centered 1 '[#] INSTALL HOOK' 'White' $T.HeaderBG

    Draw-Box 3 4 ($w-6) 8 $T.Border $T.BG $T.Title ' SELECT SCOPE '
    Write-Text 7 6 '[1] Project  (.claude/settings.json)' $T.MenuLabel
    Write-Text 7 7 '[2] Global   (~/.claude/settings.json)' $T.MenuLabel
    Flush-Screen

    $key = Read-Key
    if (Is-EscKey $key -or (Is-CharKey $key 'q')) { return }

    $scope = $key.Character.ToString()
    $settingsPath = switch ($scope) {
        '1' { Join-Path (Get-Location) '.claude\settings.json' }
        '2' { Join-Path $env:USERPROFILE '.claude\settings.json' }
        default { return }
    }

    $dir = Split-Path -Parent $settingsPath
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }

    $settings = @{}
    if (Test-Path $settingsPath) { try { $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json } catch {} }
    if (-not $settings.hooks) { $settings | Add-Member -NotePropertyName 'hooks' -NotePropertyValue @{} -Force }

    $hookObj = @{ matcher=$Hook.M; hooks=@($Hook.H) }
    if (-not $settings.hooks.($Hook.E)) {
        $settings.hooks | Add-Member -NotePropertyName $Hook.E -NotePropertyValue @() -Force
    }
    $settings.hooks.($Hook.E) += $hookObj

    try {
        $settings | ConvertTo-Json -Depth 10 | Out-File $settingsPath -Encoding utf8 -Force
        Clear-Screen
        Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
        Write-Centered 1 '[#] HOOK INSTALLED' 'White' $T.HeaderBG
        Draw-Box 3 4 ($w-6) ($h-8) 'Green' $T.BG $T.Title ' SUCCESS '
        Write-Text 6 6 "Installed: $($Hook.N)" 'Green'
        Write-Text 6 8 "Event: $($Hook.E)" $T.FG
        Write-Text 6 9 "Config: $settingsPath" $T.Dim
        Draw-Status ' Claude Toolkit ' ' Hook Installed ' '[Esc] Back' 'Black' $T.StatusBG
        Flush-Screen
        do { $key = Read-Key } until (Is-EscKey $key -or (Is-CharKey $key 'q'))
    } catch {
        Write-Text 6 6 "Error: $_" 'Red'
        Flush-Screen
        Start-Sleep -Seconds 2
    }
}
