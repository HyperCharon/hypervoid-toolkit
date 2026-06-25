# Command Reference Module - TUI Version

$script:CmdCategories = @(
    @{ Name='CLI Launch Commands'; Items=@(
        @{ C='claude';            D='Start interactive session';  E='claude' }
        @{ C='claude "prompt"';   D='Send one-shot prompt';       E='claude "explain this code"' }
        @{ C='claude -p "prompt"';D='Non-interactive mode';       E='claude -p "review this file"' }
        @{ C='claude -c';         D='Continue recent conversation';E='claude -c' }
        @{ C='claude -r';         D='Resume a past session';      E='claude -r' }
        @{ C='claude commit';     D='Generate commit message';    E='claude commit' }
        @{ C='claude config';     D='Manage configuration';       E='claude config set model sonnet' }
    )}
    @{ Name='Slash Commands'; Items=@(
        @{ C='/help';       D='List all commands';           E='/help' }
        @{ C='/clear';      D='Clear conversation';          E='/clear' }
        @{ C='/compact';    D='Compress context (save tokens)';E='/compact' }
        @{ C='/config';     D='View/modify config';          E='/config' }
        @{ C='/cost';       D='Show token usage and cost';   E='/cost' }
        @{ C='/doctor';     D='Check installation health';   E='/doctor' }
        @{ C='/init';       D='Initialize CLAUDE.md';        E='/init' }
        @{ C='/login';      D='Login to Anthropic';          E='/login' }
        @{ C='/logout';     D='Logout';                      E='/logout' }
        @{ C='/memory';     D='Edit CLAUDE.md memory';       E='/memory' }
        @{ C='/model';      D='Switch model';                E='/model opus' }
        @{ C='/permissions';D='Manage tool permissions';     E='/permissions' }
        @{ C='/review';     D='Structured code review';      E='/review' }
        @{ C='/vim';        D='Toggle vim keybindings';      E='/vim' }
        @{ C='/fast';       D='Toggle fast mode';            E='/fast' }
    )}
    @{ Name='Keyboard Shortcuts'; Items=@(
        @{ C='Shift+Tab';  D='Switch permission mode';  E='auto/suggest/plan' }
        @{ C='Ctrl+C';     D='Cancel current operation'; E='' }
        @{ C='Ctrl+D';     D='Exit session';             E='' }
    )}
    @{ Name='Pipes & Combos'; Items=@(
        @{ C='git diff | claude';   D='Pipe diff for review'; E='git diff | claude "review"' }
        @{ C='cat file | claude';   D='Pipe file content';    E='cat error.log | claude "diagnose"' }
        @{ C='claude -p --json';    D='JSON output mode';     E='claude -p "review" --output-format json' }
    )}
    @{ Name='Config Files'; Items=@(
        @{ C='CLAUDE.md';               D='Project memory file';   E='Place in project root' }
        @{ C='.claude/settings.json';   D='Project-level config';  E='permissions, hooks, MCP' }
        @{ C='~/.claude/settings.json'; D='Global user config';    E='Cross-project shared' }
        @{ C='.claude/commands/*.md';   D='Project custom cmds';   E='/project:review' }
        @{ C='~/.claude/commands/*.md'; D='User custom cmds';      E='/user:explain' }
    )}
)

function Invoke-CmdRef {
    $T = $script:Theme
    $catIdx = 0
    $scrollY = 0

    while ($true) {
        Clear-Screen
        $w = $script:Screen.Width
        $h = $script:Screen.Height

        # Header
        Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
        Write-Centered 1 '[*] COMMAND REFERENCE' 'White' $T.HeaderBG

        # Category tabs
        $tabY = 3
        Fill-Rect 0 $tabY $w 1 ' ' $T.FG 'DarkGray'
        $tx = 2
        for ($i = 0; $i -lt $script:CmdCategories.Count; $i++) {
            $cat = $script:CmdCategories[$i]
            $isSelected = ($i -eq $catIdx)
            $fg = if ($isSelected) { 'Yellow' } else { 'DarkGray' }
            $bg = 'DarkGray'
            $prefix = if ($isSelected) { '>' } else { ' ' }
            $label = "$prefix$($i+1):$($cat.Name) "
            Write-Text $tx $tabY $label $fg $bg
            $tx += $label.Length
        }

        # Content
        $contentY = 5
        $contentH = $h - 7
        $cat = $script:CmdCategories[$catIdx]

        Write-Text 3 $contentY $cat.Name $T.Accent
        Draw-HLine 2 ($contentY+1) ($w-4) 'DarkGray'

        $itemY = $contentY + 2
        $line = 0
        for ($idx = $scrollY; $idx -lt $cat.Items.Count; $idx++) {
            $item = $cat.Items[$idx]
            $iy = $itemY + $line
            if ($iy -ge $h - 3) { break }
            Write-Text 4 $iy $item.C.PadRight(35) $T.Success
            Write-Text 40 $iy $item.D $T.FG
            $line++
            if ($item.E -and ($iy+1) -lt ($h-3)) {
                Write-Text 40 ($iy+1) "Example: $($item.E)" $T.Dim
                $line++
            }
        }

        # Status
        $total = ($cat.Items | ForEach-Object { 1 + $(if ($_.E) {1} else {0}) }) | Measure-Object -Sum
        $scrollInfo = if ($scrollY -gt 0) { " Scroll:$scrollY" } else { '' }
        Draw-Status " [1-5] Category " "[Up/Down] Scroll$scrollInfo" "[Esc/Q] Back" 'Black' $T.StatusBG

        Flush-Screen

        $key = Read-Key
        if (Is-EscKey $key -or (Is-CharKey $key 'q')) { return }
        if (Is-UpKey $key) { if ($scrollY -gt 0) { $scrollY-- } }
        if (Is-DownKey $key) { $scrollY++ }
        if (Is-LeftKey $key) { $catIdx = ($catIdx - 1 + $script:CmdCategories.Count) % $script:CmdCategories.Count; $scrollY = 0 }
        if (Is-RightKey $key) { $catIdx = ($catIdx + 1) % $script:CmdCategories.Count; $scrollY = 0 }
        if ($key.Character -match '[1-5]') { $catIdx = [int]$key.Character.ToString() - 1; $scrollY = 0 }
    }
}
