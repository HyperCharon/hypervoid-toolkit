<#
.SYNOPSIS
    Config Manager - TUI Version
    Manages Claude Code settings, permissions, and diagnostics
#>

function Invoke-Config {
    $T = $script:Theme
    $sel = 0
    $items = @(
        @{ Label='View Configuration';   Desc='Display current settings.json contents' }
        @{ Label='Permissions';           Desc='Manage allowlist and denylist rules' }
        @{ Label='Environment Variables'; Desc='View and check Claude-related env vars' }
        @{ Label='Init Project Config';   Desc='Create .claude/settings.json for project' }
        @{ Label='Diagnostics';           Desc='Run configuration health checks' }
    )

    while ($true) {
        Clear-Screen
        $w = $script:Screen.Width; $h = $script:Screen.Height

        Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
        Write-Centered 1 '[@] Config Manager' 'White' $T.HeaderBG

        Draw-Box 3 4 ($w-6) ($h-8) $T.Border $T.BG $T.Title ' ACTIONS '

        for ($i = 0; $i -lt $items.Count; $i++) {
            $iy = 6 + $i * 2
            $isSel = ($i -eq $sel)
            if ($isSel) {
                Fill-Rect 5 $iy ($w-12) 1 ' ' $T.Selection $T.SelBG
                Write-Text 7 $iy "[$($i+1)] $($items[$i].Label)" $T.Selection $T.SelBG
                Write-Text 7 ($iy+1) "  $($items[$i].Desc)" $T.Accent
            } else {
                Write-Text 7 $iy "[$($i+1)] $($items[$i].Label)" $T.MenuLabel
                Write-Text 7 ($iy+1) "  $($items[$i].Desc)" $T.Dim
            }
        }

        Draw-Status ' [Up/Down] Navigate ' '[Enter] Select' '[Esc] Back' 'Black' $T.StatusBG
        Flush-Screen

        $key = Read-Key
        if (Is-EscKey $key -or (Is-CharKey $key 'q')) { return }
        if (Is-UpKey $key) { $sel = ($sel - 1 + $items.Count) % $items.Count }
        if (Is-DownKey $key) { $sel = ($sel + 1) % $items.Count }
        if (Is-EnterKey $key) {
            switch ($sel) {
                0 { Show-CurrentConfig }
                1 { Show-Permissions }
                2 { Show-EnvVars }
                3 { Init-ProjectConfig }
                4 { Run-Diagnostics }
            }
        }
    }
}

function Show-CurrentConfig {
    $T = $script:Theme
    Clear-Screen
    $w = $script:Screen.Width; $h = $script:Screen.Height

    Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
    Write-Centered 1 '[@] Current Configuration' 'White' $T.HeaderBG

    Draw-Box 3 4 ($w-6) ($h-8) $T.Border $T.BG $T.Title ' settings.json '

    $settingsPath = Join-Path (Get-Location) '.claude\settings.json'
    if (Test-Path $settingsPath) {
        try {
            $raw = Get-Content $settingsPath -Raw -ErrorAction Stop
            $parsed = $raw | ConvertFrom-Json -AsHashtable
            $json = $parsed | ConvertTo-Json -Depth 10
            $lines = $json -split "`n"

            $lineY = 6
            $maxLines = $h - 12
            for ($i = 0; $i -lt [Math]::Min($lines.Count, $maxLines); $i++) {
                $displayLine = $lines[$i]
                if ($displayLine.Length -gt ($w - 14)) {
                    $displayLine = $displayLine.Substring(0, ($w - 17)) + '...'
                }
                Write-Text 5 $lineY $displayLine $T.FG
                $lineY++
            }
            if ($lines.Count -gt $maxLines) {
                Write-Text 5 ($lineY + 1) "... ($($lines.Count - $maxLines) more lines)" $T.Dim
            }
        } catch {
            Write-Text 7 7 'Error reading settings.json' $T.Error
            Write-Text 7 9 $_.Exception.Message $T.Dim
        }
    } else {
        Write-Text 7 7 'No .claude/settings.json found.' $T.Dim
        Write-Text 7 9 'Use "Init Project Config" to create one.' $T.Dim
    }

    Draw-Status ' Configuration ' '' '[Esc] Back' 'Black' $T.StatusBG
    Flush-Screen

    do { $key = Read-Key } until ((Is-EscKey $key) -or (Is-EnterKey $key))
}

function Show-Permissions {
    $T = $script:Theme
    Clear-Screen
    $w = $script:Screen.Width; $h = $script:Screen.Height

    Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
    Write-Centered 1 '[@] Permissions' 'White' $T.HeaderBG

    Draw-Box 3 4 ($w-6) ($h-8) $T.Border $T.BG $T.Title ' ALLOW/DENY RULES '

    $settingsPath = Join-Path (Get-Location) '.claude\settings.json'
    $allowRules = @()
    $denyRules = @()

    if (Test-Path $settingsPath) {
        try {
            $raw = Get-Content $settingsPath -Raw -ErrorAction Stop
            $settings = $raw | ConvertFrom-Json -AsHashtable
            if ($settings.ContainsKey('permissions')) {
                if ($settings['permissions'].ContainsKey('allow')) {
                    $allowRules = @($settings['permissions']['allow'])
                }
                if ($settings['permissions'].ContainsKey('deny')) {
                    $denyRules = @($settings['permissions']['deny'])
                }
            }
        } catch {}
    }

    $lineY = 6
    Write-Text 5 $lineY 'Allow Rules:' $T.Success
    $lineY += 2
    if ($allowRules.Count -eq 0) {
        Write-Text 7 $lineY '  (none)' $T.Dim
        $lineY += 1
    } else {
        foreach ($rule in $allowRules) {
            if ($lineY -lt $h - 6) {
                $displayRule = [string]$rule
                if ($displayRule.Length -gt ($w - 16)) {
                    $displayRule = $displayRule.Substring(0, ($w - 19)) + '...'
                }
                Write-Text 7 $lineY "+ $displayRule" $T.Success
                $lineY++
            }
        }
    }

    $lineY++
    Draw-HLine 5 $lineY ($w-12) $T.Dim
    $lineY += 2

    Write-Text 5 $lineY 'Deny Rules:' $T.Error
    $lineY += 2
    if ($denyRules.Count -eq 0) {
        Write-Text 7 $lineY '  (none)' $T.Dim
    } else {
        foreach ($rule in $denyRules) {
            if ($lineY -lt $h - 5) {
                $displayRule = [string]$rule
                if ($displayRule.Length -gt ($w - 16)) {
                    $displayRule = $displayRule.Substring(0, ($w - 19)) + '...'
                }
                Write-Text 7 $lineY "- $displayRule" $T.Error
                $lineY++
            }
        }
    }

    Draw-Status ' Permissions ' '' '[Esc] Back' 'Black' $T.StatusBG
    Flush-Screen

    do { $key = Read-Key } until ((Is-EscKey $key) -or (Is-EnterKey $key))
}

function Show-EnvVars {
    $T = $script:Theme
    Clear-Screen
    $w = $script:Screen.Width; $h = $script:Screen.Height

    Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
    Write-Centered 1 '[@] Environment Variables' 'White' $T.HeaderBG

    Draw-Box 3 4 ($w-6) ($h-8) $T.Border $T.BG $T.Title ' CLAUDE ENV '

    $envVars = @(
        @{ Name='ANTHROPIC_API_KEY'; Desc='API authentication key' }
        @{ Name='CLAUDE_API_KEY';    Desc='Alternative API key variable' }
        @{ Name='GITHUB_TOKEN';      Desc='GitHub personal access token' }
        @{ Name='BRAVE_API_KEY';     Desc='Brave Search API key' }
        @{ Name='SLACK_BOT_TOKEN';   Desc='Slack bot OAuth token' }
        @{ Name='NODE_PATH';         Desc='Node.js module resolution path' }
        @{ Name='HOME';              Desc='User home directory' }
        @{ Name='PATH';              Desc='System executable search path' }
    )

    $lineY = 6
    foreach ($ev in $envVars) {
        if ($lineY -lt $h - 5) {
            $val = [Environment]::GetEnvironmentVariable($ev.Name)
            $status = ''
            $statusColor = $T.Dim
            if ($val) {
                $status = 'SET'
                $statusColor = $T.Success
                $displayVal = $val
                if ($displayVal.Length -gt 30) {
                    $displayVal = $displayVal.Substring(0, 27) + '...'
                }
            } else {
                $status = 'NOT SET'
                $statusColor = $T.Dim
                $displayVal = '(not configured)'
            }

            Write-Text 5 $lineY $ev.Name $T.MenuLabel
            Write-Text 35 $lineY $status $statusColor
            Write-Text 5 ($lineY + 1) "  $displayVal" $T.Dim
            $lineY += 2
        }
    }

    Draw-Status ' Environment ' '' '[Esc] Back' 'Black' $T.StatusBG
    Flush-Screen

    do { $key = Read-Key } until ((Is-EscKey $key) -or (Is-EnterKey $key))
}

function Init-ProjectConfig {
    $T = $script:Theme
    Clear-Screen
    $w = $script:Screen.Width; $h = $script:Screen.Height

    Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
    Write-Centered 1 '[@] Init Project Config' 'White' $T.HeaderBG

    Draw-Box 3 4 ($w-6) ($h-8) $T.Border $T.BG $T.Title ' CREATE CONFIG '

    Write-Text 5 6 'This will create .claude/settings.json with defaults.' $T.FG

    Draw-HLine 5 8 ($w-12) $T.Dim

    $defaultConfig = @{
        permissions = @{
            allow = @(
                'Read(.*)'
                'Glob(.*)'
                'Grep(.*)'
            )
            deny = @()
        }
        mcpServers = @{}
    }

    Write-Text 5 10 'Default permissions:' $T.Accent
    Write-Text 7 12 '+ Read(*)' $T.Success
    Write-Text 7 13 '+ Glob(*)' $T.Success
    Write-Text 7 14 '+ Grep(*)' $T.Success

    Draw-HLine 5 16 ($w-12) $T.Dim
    Write-Text 5 18 'Press Enter to create, Esc to cancel.' $T.Warning

    Draw-Status ' Init Config ' '[Enter] Create' '[Esc] Cancel' 'Black' $T.StatusBG
    Flush-Screen

    $key = Read-Key
    if (Is-EnterKey $key) {
        $settingsPath = Join-Path (Get-Location) '.claude\settings.json'
        $claudeDir = Join-Path (Get-Location) '.claude'

        if (-not (Test-Path $claudeDir)) {
            New-Item -ItemType Directory -Path $claudeDir -Force | Out-Null
        }

        $json = $defaultConfig | ConvertTo-Json -Depth 10
        Set-Content -Path $settingsPath -Value $json -Encoding UTF8
        Show-ConfigSuccess 'Created .claude/settings.json with default config'
    }
}

function Run-Diagnostics {
    $T = $script:Theme
    Clear-Screen
    $w = $script:Screen.Width; $h = $script:Screen.Height

    Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
    Write-Centered 1 '[@] Diagnostics' 'White' $T.HeaderBG

    Draw-Box 3 4 ($w-6) ($h-8) $T.Border $T.BG $T.Title ' HEALTH CHECK '

    $checks = @()
    $lineY = 6

    # Check settings.json
    $settingsPath = Join-Path (Get-Location) '.claude\settings.json'
    $hasSettings = Test-Path $settingsPath
    $checks += @{ Name='settings.json exists'; Status=$hasSettings }

    # Check .claude directory
    $claudeDir = Join-Path (Get-Location) '.claude'
    $hasDir = Test-Path $claudeDir
    $checks += @{ Name='.claude directory exists'; Status=$hasDir }

    # Check CLAUDE.md
    $claudeMd = Join-Path (Get-Location) 'CLAUDE.md'
    $hasMd = Test-Path $claudeMd
    $checks += @{ Name='CLAUDE.md exists'; Status=$hasMd }

    # Check API key
    $apiKey = [Environment]::GetEnvironmentVariable('ANTHROPIC_API_KEY')
    $hasKey = [bool]$apiKey
    $checks += @{ Name='ANTHROPIC_API_KEY set'; Status=$hasKey }

    # Check Node.js
    $hasNode = $false
    try { $null = & node --version 2>&1; $hasNode = $true } catch {}
    $checks += @{ Name='Node.js available'; Status=$hasNode }

    # Check npm
    $hasNpm = $false
    try { $null = & npm --version 2>&1; $hasNpm = $true } catch {}
    $checks += @{ Name='npm available'; Status=$hasNpm }

    # Check commands dir
    $cmdDir = Join-Path (Get-Location) '.claude\commands'
    $hasCmdDir = Test-Path $cmdDir
    $checks += @{ Name='.claude/commands/ exists'; Status=$hasCmdDir }

    $passCount = 0
    foreach ($check in $checks) {
        if ($lineY -lt $h - 5) {
            $icon = '[X]'
            $color = $T.Error
            if ($check.Status) {
                $icon = '[OK]'
                $color = $T.Success
                $passCount++
            }
            Write-Text 5 $lineY "$icon  $($check.Name)" $color
            $lineY += 2
        }
    }

    $lineY++
    Draw-HLine 5 $lineY ($w-12) $T.Dim
    $lineY += 2
    $summary = "$passCount / $($checks.Count) checks passed"
    $summaryColor = $T.Success
    if ($passCount -lt $checks.Count) { $summaryColor = $T.Warning }
    Write-Text 5 $lineY $summary $summaryColor

    Draw-Status ' Diagnostics ' '' '[Esc] Back' 'Black' $T.StatusBG
    Flush-Screen

    do { $key = Read-Key } until ((Is-EscKey $key) -or (Is-EnterKey $key))
}

function Show-ConfigSuccess {
    param([string]$Message)
    $T = $script:Theme
    Clear-Screen
    $w = $script:Screen.Width; $h = $script:Screen.Height

    $boxW = [Math]::Min(50, $w - 6)
    $boxH = 8
    $boxX = [Math]::Floor(($w - $boxW) / 2)
    $boxY = [Math]::Floor(($h - $boxH) / 2)

    Draw-Box $boxX $boxY $boxW $boxH $T.Success $T.BG $T.Success ' SUCCESS '

    Write-Centered ($boxY + 3) $Message $T.FG

    Draw-Status ' Success ' '' '[Esc] Back' 'Black' $T.StatusBG
    Flush-Screen

    do { $key = Read-Key } until ((Is-EscKey $key) -or (Is-EnterKey $key))
}
