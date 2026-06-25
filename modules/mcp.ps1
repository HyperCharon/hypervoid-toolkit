<#
.SYNOPSIS
    MCP Server Manager - TUI Version
    Manages Model Context Protocol server configurations
#>

function Invoke-Mcp {
    $T = $script:Theme
    $sel = 0
    $items = @(
        @{ Label='Browse Servers';    Desc='View available MCP servers' }
        @{ Label='Install Server';    Desc='Add a server to settings.json' }
        @{ Label='View Configured';   Desc='See currently configured servers' }
        @{ Label='Remove Server';     Desc='Remove a server from settings.json' }
    )

    $servers = @(
        @{ Name='GitHub';        Package='@modelcontextprotocol/server-github';       Desc='Access GitHub repos, issues, and PRs';
           Args='--env GITHUB_PERSONAL_ACCESS_TOKEN=$GITHUB_TOKEN' }
        @{ Name='Filesystem';    Package='@modelcontextprotocol/server-filesystem';   Desc='Read and write local files securely';
           Args='/allowed/directory' }
        @{ Name='Brave Search';  Package='@modelcontextprotocol/server-brave-search'; Desc='Web search via Brave Search API';
           Args='--env BRAVE_API_KEY=$BRAVE_API_KEY' }
        @{ Name='Puppeteer';     Package='@modelcontextprotocol/server-puppeteer';    Desc='Browser automation and web scraping';
           Args='' }
        @{ Name='PostgreSQL';    Package='@modelcontextprotocol/server-postgres';     Desc='Query PostgreSQL databases';
           Args='postgresql://localhost:5432/mydb' }
        @{ Name='SQLite';        Package='@modelcontextprotocol/server-sqlite';       Desc='SQLite database operations';
           Args='--db-path /path/to/database.db' }
        @{ Name='Slack';         Package='@modelcontextprotocol/server-slack';        Desc='Read and send Slack messages';
           Args='--env SLACK_BOT_TOKEN=$SLACK_TOKEN' }
        @{ Name='Memory';        Package='@modelcontextprotocol/server-memory';       Desc='Persistent knowledge graph memory';
           Args='' }
        @{ Name='Fetch';         Package='@modelcontextprotocol/server-fetch';        Desc='Fetch web pages and APIs';
           Args='' }
    )

    while ($true) {
        Clear-Screen
        $w = $script:Screen.Width; $h = $script:Screen.Height

        Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
        Write-Centered 1 '[~] MCP Server Manager' 'White' $T.HeaderBG

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
                0 { Show-Servers $servers }
                1 { Install-Server $servers }
                2 { Show-Configured }
                3 { Remove-Server $servers }
            }
        }
    }
}

function Show-Servers {
    param($servers)
    $T = $script:Theme
    $sel = 0
    $offset = 0

    while ($true) {
        Clear-Screen
        $w = $script:Screen.Width; $h = $script:Screen.Height

        Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
        Write-Centered 1 '[~] Available MCP Servers' 'White' $T.HeaderBG

        $boxH = $h - 8
        Draw-Box 3 4 ($w-6) $boxH $T.Border $T.BG $T.Title ' SERVERS '

        $visible = [Math]::Max(1, [Math]::Floor(($boxH - 4) / 2))
        if ($sel -lt $offset) { $offset = $sel }
        if ($sel -ge $offset + $visible) { $offset = $sel - $visible + 1 }

        for ($i = 0; $i -lt $visible; $i++) {
            $idx = $i + $offset
            if ($idx -ge $servers.Count) { break }
            $iy = 6 + $i * 2
            $isSel = ($idx -eq $sel)
            if ($isSel) {
                Fill-Rect 5 $iy ($w-12) 1 ' ' $T.Selection $T.SelBG
                Write-Text 7 $iy "$($servers[$idx].Name)" $T.Selection $T.SelBG
                Write-Text 7 ($iy+1) "  $($servers[$idx].Desc)" $T.Accent
            } else {
                Write-Text 7 $iy "$($servers[$idx].Name)" $T.MenuLabel
                Write-Text 7 ($iy+1) "  $($servers[$idx].Desc)" $T.Dim
            }
        }

        $scrollInfo = "[$($sel+1)/$($servers.Count)]"
        Draw-Status ' [Up/Down] Navigate ' $scrollInfo '[Esc] Back' 'Black' $T.StatusBG
        Flush-Screen

        $key = Read-Key
        if (Is-EscKey $key -or (Is-CharKey $key 'q')) { return }
        if (Is-UpKey $key) { $sel = ($sel - 1 + $servers.Count) % $servers.Count }
        if (Is-DownKey $key) { $sel = ($sel + 1) % $servers.Count }
        if (Is-EnterKey $key) { Show-ServerDetail $servers[$sel] }
    }
}

function Show-ServerDetail {
    param($server)
    $T = $script:Theme
    Clear-Screen
    $w = $script:Screen.Width; $h = $script:Screen.Height

    Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
    Write-Centered 1 "[~] $($server.Name)" 'White' $T.HeaderBG

    Draw-Box 3 4 ($w-6) ($h-8) $T.Border $T.BG $T.Title ' SERVER DETAILS '

    Write-Text 5 6 "Name: $($server.Name)" $T.Accent
    Write-Text 5 7 "Package: $($server.Package)" $T.FG
    Write-Text 5 8 "Description: $($server.Desc)" $T.FG

    Draw-HLine 5 10 ($w-12) $T.Dim

    Write-Text 5 12 'Installation command:' $T.Accent
    $npxCmd = "npx $($server.Package)"
    if ($server.Args) {
        $npxCmd += " $($server.Args)"
    }
    Write-Text 5 13 $npxCmd $T.Warning

    Draw-HLine 5 15 ($w-12) $T.Dim

    Write-Text 5 17 'Add to .claude/settings.json under mcpServers:' $T.Accent
    $jsonExample = "{`"$($server.Name.ToLower().Replace(' ','-'))`": {`"command`": `"npx`", `"args`": [`"$($server.Package)`"]}}"
    if ($jsonExample.Length -gt ($w - 14)) {
        $jsonExample = $jsonExample.Substring(0, ($w - 17)) + '...'
    }
    Write-Text 5 18 $jsonExample $T.Dim

    Draw-Status ' Server Detail ' '' '[Esc] Back' 'Black' $T.StatusBG
    Flush-Screen

    do { $key = Read-Key } until ((Is-EscKey $key) -or (Is-EnterKey $key))
}

function Install-Server {
    param($servers)
    $T = $script:Theme
    $sel = 0

    while ($true) {
        Clear-Screen
        $w = $script:Screen.Width; $h = $script:Screen.Height

        Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
        Write-Centered 1 '[~] Install MCP Server' 'White' $T.HeaderBG

        Draw-Box 3 4 ($w-6) ($h-8) $T.Border $T.BG $T.Title ' SELECT SERVER '

        $offset = 0
        $boxH = $h - 8
        $visible = [Math]::Max(1, [Math]::Floor(($boxH - 4) / 2))
        if ($sel -lt $offset) { $offset = $sel }
        if ($sel -ge $offset + $visible) { $offset = $sel - $visible + 1 }

        for ($i = 0; $i -lt $visible; $i++) {
            $idx = $i + $offset
            if ($idx -ge $servers.Count) { break }
            $iy = 6 + $i * 2
            $isSel = ($idx -eq $sel)
            if ($isSel) {
                Fill-Rect 5 $iy ($w-12) 1 ' ' $T.Selection $T.SelBG
                Write-Text 7 $iy "$($servers[$idx].Name) - $($servers[$idx].Package)" $T.Selection $T.SelBG
                Write-Text 7 ($iy+1) "  $($servers[$idx].Desc)" $T.Accent
            } else {
                Write-Text 7 $iy "$($servers[$idx].Name) - $($servers[$idx].Package)" $T.MenuLabel
                Write-Text 7 ($iy+1) "  $($servers[$idx].Desc)" $T.Dim
            }
        }

        Draw-Status ' [Up/Down] Select ' '[Enter] Install' '[Esc] Back' 'Black' $T.StatusBG
        Flush-Screen

        $key = Read-Key
        if (Is-EscKey $key -or (Is-CharKey $key 'q')) { return }
        if (Is-UpKey $key) { $sel = ($sel - 1 + $servers.Count) % $servers.Count }
        if (Is-DownKey $key) { $sel = ($sel + 1) % $servers.Count }
        if (Is-EnterKey $key) {
            $server = $servers[$sel]
            $settingsPath = Join-Path (Get-Location) '.claude\settings.json'
            $settings = @{}

            if (Test-Path $settingsPath) {
                try {
                    $raw = Get-Content $settingsPath -Raw -ErrorAction Stop
                    $settings = $raw | ConvertFrom-Json -AsHashtable
                } catch {
                    $settings = @{}
                }
            }

            if (-not $settings.ContainsKey('mcpServers')) {
                $settings['mcpServers'] = @{}
            }

            $serverKey = $server.Name.ToLower().Replace(' ', '-')
            $argsList = @($server.Package)
            if ($server.Args -and $server.Args.StartsWith('--')) {
                $argsList = @($server.Package) + ($server.Args -split ' ')
            }

            $settings['mcpServers'][$serverKey] = @{
                command = 'npx'
                args = $argsList
            }

            $json = $settings | ConvertTo-Json -Depth 10
            Set-Content -Path $settingsPath -Value $json -Encoding UTF8

            Show-McpSuccess "Added $($server.Name) to settings.json"
            return
        }
    }
}

function Show-Configured {
    $T = $script:Theme
    $settingsPath = Join-Path (Get-Location) '.claude\settings.json'
    $configured = @()

    if (Test-Path $settingsPath) {
        try {
            $raw = Get-Content $settingsPath -Raw -ErrorAction Stop
            $settings = $raw | ConvertFrom-Json -AsHashtable
            if ($settings.ContainsKey('mcpServers')) {
                $configured = $settings['mcpServers'].Keys
            }
        } catch {
            $configured = @()
        }
    }

    Clear-Screen
    $w = $script:Screen.Width; $h = $script:Screen.Height

    Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
    Write-Centered 1 '[~] Configured MCP Servers' 'White' $T.HeaderBG

    Draw-Box 3 4 ($w-6) ($h-8) $T.Border $T.BG $T.Title ' settings.json '

    if ($configured.Count -eq 0) {
        Write-Text 7 7 'No MCP servers configured.' $T.Dim
        Write-Text 7 9 'Use "Install Server" to add one.' $T.Dim
    } else {
        $lineY = 6
        foreach ($name in $configured) {
            if ($lineY -lt $h - 5) {
                Write-Text 7 $lineY "* $name" $T.MenuLabel
                $lineY += 2
            }
        }
    }

    Draw-Status ' Configured Servers ' "$($configured.Count) found" '[Esc] Back' 'Black' $T.StatusBG
    Flush-Screen

    do { $key = Read-Key } until ((Is-EscKey $key) -or (Is-EnterKey $key))
}

function Remove-Server {
    param($servers)
    $T = $script:Theme

    $settingsPath = Join-Path (Get-Location) '.claude\settings.json'
    $configured = @()
    $settings = @{}

    if (Test-Path $settingsPath) {
        try {
            $raw = Get-Content $settingsPath -Raw -ErrorAction Stop
            $settings = $raw | ConvertFrom-Json -AsHashtable
            if ($settings.ContainsKey('mcpServers')) {
                $configured = @($settings['mcpServers'].Keys)
            }
        } catch {
            $configured = @()
        }
    }

    if ($configured.Count -eq 0) {
        Show-McpSuccess 'No servers to remove.'
        return
    }

    $sel = 0

    while ($true) {
        Clear-Screen
        $w = $script:Screen.Width; $h = $script:Screen.Height

        Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
        Write-Centered 1 '[~] Remove MCP Server' 'White' $T.HeaderBG

        Draw-Box 3 4 ($w-6) ($h-8) $T.Border $T.BG $T.Title ' SELECT SERVER '

        for ($i = 0; $i -lt $configured.Count; $i++) {
            $iy = 6 + $i * 2
            $isSel = ($i -eq $sel)
            if ($isSel) {
                Fill-Rect 5 $iy ($w-12) 1 ' ' $T.Selection $T.SelBG
                Write-Text 7 $iy "$($configured[$i])" $T.Selection $T.SelBG
                Write-Text 7 ($iy+1) '  Press Enter to remove' $T.Error
            } else {
                Write-Text 7 $iy "$($configured[$i])" $T.MenuLabel
                Write-Text 7 ($iy+1) '  Configured' $T.Dim
            }
        }

        Draw-Status ' [Up/Down] Select ' '[Enter] Remove' '[Esc] Back' 'Black' $T.StatusBG
        Flush-Screen

        $key = Read-Key
        if (Is-EscKey $key -or (Is-CharKey $key 'q')) { return }
        if (Is-UpKey $key) { $sel = ($sel - 1 + $configured.Count) % $configured.Count }
        if (Is-DownKey $key) { $sel = ($sel + 1) % $configured.Count }
        if (Is-EnterKey $key) {
            $toRemove = $configured[$sel]
            $settings['mcpServers'].Remove($toRemove)
            $json = $settings | ConvertTo-Json -Depth 10
            Set-Content -Path $settingsPath -Value $json -Encoding UTF8
            Show-McpSuccess "Removed $toRemove from settings.json"
            return
        }
    }
}

function Show-McpSuccess {
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
