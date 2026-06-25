# CLAUDE.md Generator - TUI Version

$script:Templates = @(
    @{ N='TypeScript / Node.js'; L='TypeScript'; F='Node.js / Express'; P='pnpm'; T='Vitest'; X='ESLint+Prettier' }
    @{ N='Python';               L='Python 3.11+'; F='FastAPI / Django'; P='pip'; T='pytest'; X='ruff' }
    @{ N='Go';                   L='Go 1.21+'; F='Gin / Echo'; P='go mod'; T='go test'; X='golangci-lint' }
    @{ N='Rust';                 L='Rust'; F='Axum / Actix'; P='cargo'; T='cargo test'; X='clippy' }
    @{ N='React / Vue';         L='TypeScript'; F='React / Vue / Svelte'; P='pnpm'; T='Vitest'; X='ESLint' }
    @{ N='Java / Spring';       L='Java 17+'; F='Spring Boot'; P='maven'; T='JUnit 5'; X='Spotless' }
    @{ N='Custom';               L=''; F=''; P=''; T=''; X='' }
)

function Invoke-InitClaude {
    $T = $script:Theme
    $sel = 0

    while ($true) {
        Clear-Screen
        $w = $script:Screen.Width; $h = $script:Screen.Height

        Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
        Write-Centered 1 '[+] CLAUDE.MD GENERATOR' 'White' $T.HeaderBG

        Draw-Box 3 4 ($w-6) ($h-8) $T.Border $T.BG $T.Title ' SELECT TEMPLATE '

        for ($i = 0; $i -lt $script:Templates.Count; $i++) {
            $t = $script:Templates[$i]
            $iy = 6 + $i * 2
            $isSel = ($i -eq $sel)
            if ($isSel) {
                Fill-Rect 5 $iy ($w-12) 1 ' ' $T.Selection $T.SelBG
                Write-Text 7 $iy "[$($i+1)] $($t.N)" $T.Selection $T.SelBG
                Write-Text 7 ($iy+1) "  L:$($t.L) F:$($t.F) P:$($t.P)" $T.Accent
            } else {
                Write-Text 7 $iy "[$($i+1)] $($t.N)" $T.MenuLabel
                Write-Text 7 ($iy+1) "  L:$($t.L) F:$($t.F) P:$($t.P)" $T.Dim
            }
        }

        Draw-Status ' [Up/Down] Navigate ' '[Enter] Select' '[Esc] Back' 'Black' $T.StatusBG
        Flush-Screen

        $key = Read-Key
        if (Is-EscKey $key -or (Is-CharKey $key 'q')) { return }
        if (Is-UpKey $key) { $sel = ($sel - 1 + $script:Templates.Count) % $script:Templates.Count }
        if (Is-DownKey $key) { $sel = ($sel + 1) % $script:Templates.Count }
        if (Is-EnterKey $key) { Generate-ClaudeMd $script:Templates[$sel]; return }
        if ($key.Character -match '[1-7]') { $sel = [int]$key.Character.ToString() - 1; Generate-ClaudeMd $script:Templates[$sel]; return }
    }
}

function Generate-ClaudeMd {
    param($T)
    $TH = $script:Theme
    Clear-Screen
    $w = $script:Screen.Width; $h = $script:Screen.Height

    Fill-Rect 0 0 $w 3 ' ' 'White' $TH.HeaderBG
    Write-Centered 1 '[+] GENERATE CLAUDE.MD' 'White' $TH.HeaderBG

    $fields = @(
        @{ L='Project Name';  D=(Split-Path -Leaf (Get-Location)) }
        @{ L='Description';   D="$($T.N) project" }
        @{ L='Language';      D=$T.L }
        @{ L='Framework';     D=$T.F }
        @{ L='Package Mgr';   D=$T.P }
        @{ L='Test Framework';D=$T.T }
        @{ L='Lint Tool';     D=$T.X }
    )

    Draw-Box 3 4 ($w-6) ($h-8) $TH.Border $TH.BG $TH.Title ' PROJECT INFO '

    for ($i = 0; $i -lt $fields.Count; $i++) {
        $f = $fields[$i]
        $iy = 6 + $i * 2
        Write-Text 6 $iy "$($f.L):" $TH.Accent
        Write-Text 22 $iy $f.D $TH.Dim
    }

    Write-Text 6 ($h-4) '[Enter] Generate   [Esc] Cancel' $TH.Dim
    Flush-Screen

    $key = Read-Key
    if (Is-EscKey $key -or (Is-CharKey $key 'q')) { return }

    $name = $fields[0].D; $desc = $fields[1].D
    $lang = $fields[2].D; $fw = $fields[3].D; $pm = $fields[4].D
    $test = $fields[5].D; $lint = $fields[6].D

    $install = switch -Wildcard ($pm) {
        'pnpm'{'pnpm install'} 'npm'{'npm install'} 'yarn'{'yarn install'}
        'pip*'{'pip install -r requirements.txt'} 'poetry'{'poetry install'}
        'cargo'{'cargo build'} 'go*'{'go mod download'}
        'maven'{'mvn install'} 'gradle'{'gradle build'} default{'# TODO'}
    }
    $dev = switch -Wildcard ($pm) {
        'pnpm'{'pnpm dev'} 'npm'{'npm run dev'} 'yarn'{'yarn dev'}
        'cargo'{'cargo run'} 'go*'{'go run .'} default{'# TODO'}
    }
    $build = switch -Wildcard ($pm) {
        'pnpm'{'pnpm build'} 'npm'{'npm run build'} 'yarn'{'yarn build'}
        'cargo'{'cargo build --release'} 'go*'{'go build -o app .'} default{'# TODO'}
    }
    $tst = switch -Wildcard ($test) {
        'vitest'{'pnpm test'} 'jest'{'npm test'} 'pytest'{'pytest'}
        'go*'{'go test ./...'} 'cargo*'{'cargo test'} default{'# TODO'}
    }

    $content = @"
# $name

> $desc

## Tech Stack
- Language: $lang
- Framework: $fw
- Package Manager: $pm
- Testing: $test
- Linting: $lint

## Build & Run
``````bash
$install    # Install
$dev        # Dev
$build      # Build
$tst        # Test
``````

## Code Conventions
- Use descriptive names
- Handle errors explicitly
- Write tests for new features

## Important Files
- CLAUDE.md - Project instructions
- .claude/settings.json - Claude config
- .claude/commands/ - Custom commands
"@

    $outPath = 'CLAUDE.md'
    try {
        $content | Out-File $outPath -Encoding utf8 -Force
        Clear-Screen
        Fill-Rect 0 0 $w 3 ' ' 'White' $TH.HeaderBG
        Write-Centered 1 '[+] CLAUDE.MD GENERATED' 'White' $TH.HeaderBG
        Draw-Box 3 4 ($w-6) ($h-8) 'Green' $TH.BG $TH.Title ' SUCCESS '
        Write-Text 6 6 "Generated: $outPath" 'Green'
        Write-Text 6 8 'Preview:' $TH.Accent
        $lines = $content -split "`n" | Select-Object -First 15
        for ($i = 0; $i -lt $lines.Count; $i++) {
            if ((10+$i) -lt ($h-4)) { Write-Text 6 (10+$i) $lines[$i] $TH.FG }
        }
        Draw-Status ' Claude Toolkit ' ' Generated! ' '[Esc] Back' 'Black' $TH.StatusBG
        Flush-Screen
        do { $key = Read-Key } until (Is-EscKey $key -or (Is-CharKey $key 'q'))
    } catch {
        Write-Text 6 6 "Error: $_" 'Red'
        Flush-Screen
        Start-Sleep -Seconds 2
    }
}
