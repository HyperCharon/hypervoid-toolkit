<#
.SYNOPSIS
    Slash Command Factory - TUI Version
    Manages custom slash command templates for Claude Code
#>

function Invoke-Commands {
    $T = $script:Theme
    $sel = 0
    $items = @(
        @{ Label='Browse Templates';      Desc='View available slash command templates' }
        @{ Label='Install Command';       Desc='Install a template to .claude/commands/' }
        @{ Label='View Installed';        Desc='See currently installed commands' }
        @{ Label='Create Custom';         Desc='Create a new custom slash command' }
    )

    $templates = @(
        @{ Name='review.md';      Title='Code Review';     Desc='Review code for bugs, security, and best practices';
           Content='Review the following code for bugs, security vulnerabilities, performance issues, and best practices. Provide specific suggestions for improvement with line references.' }
        @{ Name='test.md';        Title='Generate Tests';  Desc='Create unit/integration tests for given code';
           Content='Write comprehensive tests for the following code. Include happy path, edge cases, error handling, and boundary conditions. Aim for high coverage.' }
        @{ Name='refactor.md';    Title='Refactor Code';   Desc='Refactor for readability and SOLID principles';
           Content='Refactor the following code to improve readability, apply SOLID principles, remove duplication, and improve naming. Preserve all existing behavior.' }
        @{ Name='deploy-check.md';Title='Deploy Check';    Desc='Pre-deployment checklist and validation';
           Content='Perform a pre-deployment review. Check for hardcoded secrets, debug code left in, missing error handling, logging adequacy, and rollback strategy.' }
        @{ Name='explain.md';     Title='Explain Code';    Desc='Get detailed explanation of complex code';
           Content='Explain the following code in detail. Cover the purpose, how it works step by step, any design patterns used, potential gotchas, and suggest improvements.' }
        @{ Name='debug.md';       Title='Debug Issue';     Desc='Systematic debugging approach for issues';
           Content='Debug the following issue systematically. Identify the root cause, explain why it happens, provide a fix, and suggest how to prevent similar issues.' }
        @{ Name='optimize.md';    Title='Optimize';        Desc='Performance optimization suggestions';
           Content='Analyze the following code for performance. Identify bottlenecks, suggest algorithmic improvements, caching opportunities, and async/parallel execution options.' }
    )

    while ($true) {
        Clear-Screen
        $w = $script:Screen.Width; $h = $script:Screen.Height

        Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
        Write-Centered 1 '[!] Slash Command Factory' 'White' $T.HeaderBG

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
                0 { Show-Templates $templates }
                1 { Install-Template $templates }
                2 { Show-Installed }
                3 { Create-Custom }
            }
        }
    }
}

function Show-Templates {
    param($templates)
    $T = $script:Theme
    $sel = 0
    $offset = 0

    while ($true) {
        Clear-Screen
        $w = $script:Screen.Width; $h = $script:Screen.Height

        Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
        Write-Centered 1 '[!] Available Templates' 'White' $T.HeaderBG

        $boxH = $h - 8
        Draw-Box 3 4 ($w-6) $boxH $T.Border $T.BG $T.Title ' TEMPLATES '

        $visible = [Math]::Max(1, [Math]::Floor(($boxH - 4) / 2))
        if ($sel -lt $offset) { $offset = $sel }
        if ($sel -ge $offset + $visible) { $offset = $sel - $visible + 1 }

        for ($i = 0; $i -lt $visible; $i++) {
            $idx = $i + $offset
            if ($idx -ge $templates.Count) { break }
            $iy = 6 + $i * 2
            $isSel = ($idx -eq $sel)
            if ($isSel) {
                Fill-Rect 5 $iy ($w-12) 1 ' ' $T.Selection $T.SelBG
                Write-Text 7 $iy "$($templates[$idx].Name) - $($templates[$idx].Title)" $T.Selection $T.SelBG
                Write-Text 7 ($iy+1) "  $($templates[$idx].Desc)" $T.Accent
            } else {
                Write-Text 7 $iy "$($templates[$idx].Name) - $($templates[$idx].Title)" $T.MenuLabel
                Write-Text 7 ($iy+1) "  $($templates[$idx].Desc)" $T.Dim
            }
        }

        $scrollInfo = "[$($sel+1)/$($templates.Count)]"
        Draw-Status ' [Up/Down] Navigate ' $scrollInfo '[Esc] Back' 'Black' $T.StatusBG
        Flush-Screen

        $key = Read-Key
        if (Is-EscKey $key -or (Is-CharKey $key 'q')) { return }
        if (Is-UpKey $key) { $sel = ($sel - 1 + $templates.Count) % $templates.Count }
        if (Is-DownKey $key) { $sel = ($sel + 1) % $templates.Count }
        if (Is-EnterKey $key) { Show-TemplateDetail $templates[$sel] }
    }
}

function Show-TemplateDetail {
    param($template)
    $T = $script:Theme
    Clear-Screen
    $w = $script:Screen.Width; $h = $script:Screen.Height

    Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
    Write-Centered 1 "[!] $($template.Name)" 'White' $T.HeaderBG

    Draw-Box 3 4 ($w-6) ($h-8) $T.Border $T.BG $T.Title " $($template.Title) "

    Write-Text 5 6 "File: $($template.Name)" $T.Accent
    Write-Text 5 7 "Description: $($template.Desc)" $T.FG

    Draw-HLine 5 9 ($w-12) $T.Dim

    $lines = $template.Content -split "`n"
    $lineY = 11
    foreach ($line in $lines) {
        if ($lineY -lt $h - 5) {
            $displayLine = $line
            if ($displayLine.Length -gt ($w - 14)) {
                $displayLine = $displayLine.Substring(0, ($w - 17)) + '...'
            }
            Write-Text 7 $lineY $displayLine $T.FG
            $lineY++
        }
    }

    Draw-Status ' Template Detail ' '' '[Esc] Back' 'Black' $T.StatusBG
    Flush-Screen

    do { $key = Read-Key } until ((Is-EscKey $key) -or (Is-EnterKey $key))
}

function Install-Template {
    param($templates)
    $T = $script:Theme
    $sel = 0

    while ($true) {
        Clear-Screen
        $w = $script:Screen.Width; $h = $script:Screen.Height

        Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
        Write-Centered 1 '[!] Install Template' 'White' $T.HeaderBG

        Draw-Box 3 4 ($w-6) ($h-8) $T.Border $T.BG $T.Title ' SELECT TEMPLATE '

        for ($i = 0; $i -lt $templates.Count; $i++) {
            $iy = 6 + $i * 2
            $isSel = ($i -eq $sel)
            if ($isSel) {
                Fill-Rect 5 $iy ($w-12) 1 ' ' $T.Selection $T.SelBG
                Write-Text 7 $iy "$($templates[$i].Name)" $T.Selection $T.SelBG
                Write-Text 7 ($iy+1) "  $($templates[$i].Title)" $T.Accent
            } else {
                Write-Text 7 $iy "$($templates[$i].Name)" $T.MenuLabel
                Write-Text 7 ($iy+1) "  $($templates[$i].Title)" $T.Dim
            }
        }

        Draw-Status ' [Up/Down] Select ' '[Enter] Install' '[Esc] Back' 'Black' $T.StatusBG
        Flush-Screen

        $key = Read-Key
        if (Is-EscKey $key -or (Is-CharKey $key 'q')) { return }
        if (Is-UpKey $key) { $sel = ($sel - 1 + $templates.Count) % $templates.Count }
        if (Is-DownKey $key) { $sel = ($sel + 1) % $templates.Count }
        if (Is-EnterKey $key) {
            $template = $templates[$sel]
            $cmdDir = Join-Path (Get-Location) '.claude\commands'
            if (-not (Test-Path $cmdDir)) {
                New-Item -ItemType Directory -Path $cmdDir -Force | Out-Null
            }
            $destPath = Join-Path $cmdDir $template.Name
            Set-Content -Path $destPath -Value $template.Content -Encoding UTF8
            Show-Success "Installed $($template.Name) to .claude/commands/"
            return
        }
    }
}

function Show-Installed {
    $T = $script:Theme
    $cmdDir = Join-Path (Get-Location) '.claude\commands'
    $installed = @()
    if (Test-Path $cmdDir) {
        $installed = Get-ChildItem -Path $cmdDir -Filter '*.md' -ErrorAction SilentlyContinue
    }

    Clear-Screen
    $w = $script:Screen.Width; $h = $script:Screen.Height

    Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
    Write-Centered 1 '[!] Installed Commands' 'White' $T.HeaderBG

    Draw-Box 3 4 ($w-6) ($h-8) $T.Border $T.BG $T.Title ' .claude/commands/ '

    if ($installed.Count -eq 0) {
        Write-Text 7 7 'No commands installed yet.' $T.Dim
        Write-Text 7 9 'Use "Install Template" to add slash commands.' $T.Dim
    } else {
        $lineY = 6
        foreach ($file in $installed) {
            if ($lineY -lt $h - 5) {
                Write-Text 7 $lineY "/$($file.Name)" $T.MenuLabel
                $size = "$($file.Length) bytes"
                Write-Text 35 $lineY $size $T.Dim
                $lineY += 2
            }
        }
    }

    Draw-Status ' Installed Commands ' "$($installed.Count) found" '[Esc] Back' 'Black' $T.StatusBG
    Flush-Screen

    do { $key = Read-Key } until ((Is-EscKey $key) -or (Is-EnterKey $key))
}

function Create-Custom {
    $T = $script:Theme
    Clear-Screen
    $w = $script:Screen.Width; $h = $script:Screen.Height

    Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
    Write-Centered 1 '[!] Create Custom Command' 'White' $T.HeaderBG

    Draw-Box 3 4 ($w-6) ($h-8) $T.Border $T.BG $T.Title ' NEW COMMAND '

    Write-Text 5 6 'This will create a template file in .claude/commands/' $T.FG
    Write-Text 5 8 'Suggested structure:' $T.Accent
    Write-Text 5 10 '  1. Describe the task clearly' $T.Dim
    Write-Text 5 11 '  2. Include specific instructions' $T.Dim
    Write-Text 5 12 '  3. Reference $ARGUMENTS for dynamic input' $T.Dim
    Write-Text 5 13 '  4. Define output format expectations' $T.Dim

    Draw-HLine 5 15 ($w-12) $T.Dim

    Write-Text 5 17 'A sample template will be created as example.md' $T.FG
    Write-Text 5 18 'Edit it with your preferred text editor.' $T.FG

    $sampleContent = @'
Describe your task here.

Instructions:
- Step 1: Analyze $ARGUMENTS
- Step 2: Provide detailed output
- Step 3: Include examples

Format your response with clear sections.
'@

    $cmdDir = Join-Path (Get-Location) '.claude\commands'

    Draw-Status ' Create Custom ' '[Enter] Create' '[Esc] Cancel' 'Black' $T.StatusBG
    Flush-Screen

    $key = Read-Key
    if (Is-EnterKey $key) {
        if (-not (Test-Path $cmdDir)) {
            New-Item -ItemType Directory -Path $cmdDir -Force | Out-Null
        }
        $destPath = Join-Path $cmdDir 'example.md'
        Set-Content -Path $destPath -Value $sampleContent -Encoding UTF8
        Show-Success 'Created example.md in .claude/commands/'
    }
}

function Show-Success {
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
