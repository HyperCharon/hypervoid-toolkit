<#
.SYNOPSIS
    TUI Engine - Full-screen terminal UI framework for PowerShell 5.1
#>

# ── Screen Buffer ──────────────────────────────────────────
$script:Screen = @{
    Width  = 0
    Height = 0
    Buffer = $null
    FG     = $null
    BG     = $null
}

function Initialize-Screen {
    $raw = $Host.UI.RawUI
    $script:Screen.Width  = $raw.WindowSize.X
    $script:Screen.Height = $raw.WindowSize.Y
    $size = $script:Screen.Width * $script:Screen.Height
    $script:Screen.Buffer = [char[]]::new($size)
    $script:Screen.FG     = [System.ConsoleColor[]]::new($size)
    $script:Screen.BG     = [System.ConsoleColor[]]::new($size)
    Clear-Screen
}

function Clear-Screen {
    $w = $script:Screen.Width
    $h = $script:Screen.Height
    $size = $w * $h
    for ($i = 0; $i -lt $size; $i++) {
        $script:Screen.Buffer[$i] = ' '
        $script:Screen.FG[$i] = [ConsoleColor]::White
        $script:Screen.BG[$i] = [ConsoleColor]::Black
    }
}

function Flush-Screen {
    $w = $script:Screen.Width
    $h = $script:Screen.Height
    [Console]::CursorVisible = $false
    [Console]::SetCursorPosition(0, 0)
    $sb = New-Object System.Text.StringBuilder ($w * $h * 20)
    $lastFG = [ConsoleColor]::Black
    $lastBG = [ConsoleColor]::Black
    for ($y = 0; $y -lt $h; $y++) {
        for ($x = 0; $x -lt $w; $x++) {
            $idx = $y * $w + $x
            $fg = $script:Screen.FG[$idx]
            $bg = $script:Screen.BG[$idx]
            if ($fg -ne $lastFG -or $bg -ne $lastBG) {
                $fgCode = Get-FGCode $fg
                $bgCode = Get-BGCode $bg
                [void]$sb.Append("$fgCode$bgCode")
                $lastFG = $fg
                $lastBG = $bg
            }
            [void]$sb.Append($script:Screen.Buffer[$idx])
        }
        if ($y -lt $h - 1) { [void]$sb.AppendLine() }
    }
    [void]$sb.Append("$([char]27)[0m")
    Write-Host $sb.ToString() -NoNewline
}

function Get-FGCode {
    param([ConsoleColor]$Color)
    $codes = @{
        Black=30; DarkBlue=34; DarkGreen=32; DarkCyan=36; DarkRed=31
        DarkMagenta=35; DarkYellow=33; Gray=37; DarkGray=90; Blue=94
        Green=92; Cyan=96; Red=91; Magenta=95; Yellow=93; White=97
    }
    "$([char]27)[$($codes[$Color])m"
}

function Get-BGCode {
    param([ConsoleColor]$Color)
    $codes = @{
        Black=40; DarkBlue=44; DarkGreen=42; DarkCyan=46; DarkRed=41
        DarkMagenta=45; DarkYellow=43; Gray=47; DarkGray=100; Blue=104
        Green=102; Cyan=106; Red=101; Magenta=105; Yellow=103; White=107
    }
    "$([char]27)[$($codes[$Color])m"
}

# ── Drawing Primitives ────────────────────────────────────
function Set-Cell {
    param([int]$X, [int]$Y, [string]$Char, [ConsoleColor]$FG = 'White', [ConsoleColor]$BG = 'Black')
    if ($X -lt 0 -or $Y -lt 0 -or $X -ge $script:Screen.Width -or $Y -ge $script:Screen.Height) { return }
    $idx = $Y * $script:Screen.Width + $X
    $script:Screen.Buffer[$idx] = $Char[0]
    $script:Screen.FG[$idx] = $FG
    $script:Screen.BG[$idx] = $BG
}

function Write-Text {
    param([int]$X, [int]$Y, [string]$Text, [ConsoleColor]$FG = 'White', [ConsoleColor]$BG = 'Black')
    for ($i = 0; $i -lt $Text.Length; $i++) {
        Set-Cell ($X + $i) $Y $Text[$i] $FG $BG
    }
}

function Write-Centered {
    param([int]$Y, [string]$Text, [ConsoleColor]$FG = 'White', [ConsoleColor]$BG = 'Black')
    $x = [Math]::Floor(($script:Screen.Width - $Text.Length) / 2)
    Write-Text $x $Y $Text $FG $BG
}

function Fill-Rect {
    param([int]$X, [int]$Y, [int]$W, [int]$H, [string]$Char = ' ', [ConsoleColor]$FG = 'White', [ConsoleColor]$BG = 'Black')
    for ($dy = 0; $dy -lt $H; $dy++) {
        for ($dx = 0; $dx -lt $W; $dx++) {
            Set-Cell ($X + $dx) ($Y + $dy) $Char $FG $BG
        }
    }
}

function Draw-Box {
    param([int]$X, [int]$Y, [int]$W, [int]$H, [ConsoleColor]$BorderFG = 'Cyan', [ConsoleColor]$BG = 'Black', [ConsoleColor]$TitleFG = 'White', [string]$Title = '')
    # Corners
    Set-Cell $X $Y ([char]0x250C) $BorderFG $BG
    Set-Cell ($X+$W-1) $Y ([char]0x2510) $BorderFG $BG
    Set-Cell $X ($Y+$H-1) ([char]0x2514) $BorderFG $BG
    Set-Cell ($X+$W-1) ($Y+$H-1) ([char]0x2518) $BorderFG $BG
    # Top/Bottom edges
    for ($i = 1; $i -lt ($W-1); $i++) {
        Set-Cell ($X+$i) $Y ([char]0x2500) $BorderFG $BG
        Set-Cell ($X+$i) ($Y+$H-1) ([char]0x2500) $BorderFG $BG
    }
    # Left/Right edges
    for ($i = 1; $i -lt ($H-1); $i++) {
        Set-Cell $X ($Y+$i) ([char]0x2502) $BorderFG $BG
        Set-Cell ($X+$W-1) ($Y+$i) ([char]0x2502) $BorderFG $BG
    }
    # Fill interior
    Fill-Rect ($X+1) ($Y+1) ($W-2) ($H-2) ' ' 'White' $BG
    # Title
    if ($Title) {
        $titleStr = " $Title "
        $tx = $X + [Math]::Floor(($W - $titleStr.Length) / 2)
        Write-Text ($X+2) $Y $titleStr $TitleFG $BG
    }
}

function Draw-HLine {
    param([int]$X, [int]$Y, [int]$W, [ConsoleColor]$FG = 'DarkGray', [ConsoleColor]$BG = 'Black')
    Set-Cell $X $Y ([char]0x251C) $FG $BG
    for ($i = 1; $i -lt ($W-1); $i++) { Set-Cell ($X+$i) $Y ([char]0x2500) $FG $BG }
    Set-Cell ($X+$W-1) $Y ([char]0x2524) $FG $BG
}

function Draw-Status {
    param([string]$Left, [string]$Center = '', [string]$Right = '', [ConsoleColor]$FG = 'Black', [ConsoleColor]$BG = 'DarkCyan')
    $w = $script:Screen.Width
    $y = $script:Screen.Height - 1
    Fill-Rect 0 $y $w 1 ' ' $FG $BG
    Write-Text 1 $y $Left $FG $BG
    if ($Center) {
        $cx = [Math]::Floor(($w - $Center.Length) / 2)
        Write-Text $cx $y $Center $FG $BG
    }
    if ($Right) {
        Write-Text ($w - $Right.Length - 1) $y $Right $FG $BG
    }
}

# ── Input Handling ─────────────────────────────────────────
function Read-Key {
    $key = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
    return $key
}

function Is-UpKey    { param($Key); return $Key.VirtualKeyCode -eq 38 }
function Is-DownKey  { param($Key); return $Key.VirtualKeyCode -eq 40 }
function Is-LeftKey  { param($Key); return $Key.VirtualKeyCode -eq 37 }
function Is-RightKey { param($Key); return $Key.VirtualKeyCode -eq 39 }
function Is-EnterKey { param($Key); return $Key.VirtualKeyCode -eq 13 }
function Is-EscKey   { param($Key); return $Key.VirtualKeyCode -eq 27 }
function Is-CharKey  { param($Key, $Char); return $Key.Character.ToString().ToLower() -eq $Char.ToLower() }

# ── Animation Helpers ─────────────────────────────────────
$script:Spinners = @('|','/','-','\')
$script:SpinIdx = 0

function Get-Spinner {
    $ch = $script:Spinners[$script:SpinIdx % 4]
    $script:SpinIdx++
    return $ch
}

function Animate-Text {
    param([int]$X, [int]$Y, [string]$Text, [ConsoleColor]$FG = 'Cyan', [int]$DelayMs = 30)
    for ($i = 0; $i -lt $Text.Length; $i++) {
        Set-Cell ($X + $i) $Y $Text[$i] $FG
        if ($i % 3 -eq 0) { Flush-Screen; Start-Sleep -Milliseconds $DelayMs }
    }
}

# ── Theme ─────────────────────────────────────────────────
$script:Theme = @{
    BG         = [ConsoleColor]::Black
    FG         = [ConsoleColor]::White
    Accent     = [ConsoleColor]::Cyan
    Accent2    = [ConsoleColor]::Magenta
    Dim        = [ConsoleColor]::DarkGray
    Success    = [ConsoleColor]::Green
    Warning    = [ConsoleColor]::Yellow
    Error      = [ConsoleColor]::Red
    Border     = [ConsoleColor]::DarkCyan
    Title      = [ConsoleColor]::Cyan
    Selection  = [ConsoleColor]::Black
    SelBG      = [ConsoleColor]::DarkCyan
    HeaderBG   = [ConsoleColor]::DarkBlue
    StatusBG   = [ConsoleColor]::DarkCyan
    MenuKey    = [ConsoleColor]::Yellow
    MenuLabel  = [ConsoleColor]::White
    MenuDesc   = [ConsoleColor]::DarkGray
}
