<#
.SYNOPSIS
    Prompt Template Library - TUI Version
    Browse and use curated prompt templates from prompts.json
#>

function Invoke-Prompts {
    $T = $script:Theme

    $promptPath = Join-Path $script:ROOT 'data\prompts.json'
    $promptData = $null
    if (Test-Path $promptPath) {
        try {
            $raw = Get-Content $promptPath -Raw -ErrorAction Stop
            $promptData = $raw | ConvertFrom-Json
        } catch {
            $promptData = $null
        }
    }

    if (-not $promptData) {
        Show-PromptError 'Could not load prompts.json'
        return
    }

    $categories = $promptData.categories
    $sel = 0
    $items = @(
        @{ Label='Browse Categories';  Desc='View prompts organized by category' }
        @{ Label='View Detail';        Desc='See full prompt text for a template' }
        @{ Label='Copy to Clipboard';  Desc='Copy a prompt template to clipboard' }
        @{ Label='Search Prompts';     Desc='Search across all prompt templates' }
    )

    while ($true) {
        Clear-Screen
        $w = $script:Screen.Width; $h = $script:Screen.Height

        Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
        Write-Centered 1 '[=] Prompt Template Library' 'White' $T.HeaderBG

        Draw-Box 3 4 ($w-6) ($h-8) $T.Border $T.BG $T.Title ' ACTIONS '

        $totalPrompts = 0
        foreach ($cat in $categories) { $totalPrompts += $cat.prompts.Count }

        Write-Text 7 6 "$($categories.Count) categories, $totalPrompts prompts available" $T.Accent

        for ($i = 0; $i -lt $items.Count; $i++) {
            $iy = 8 + $i * 2
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
                0 { Browse-Categories $categories }
                1 { View-Detail $categories }
                2 { Copy-Prompt $categories }
                3 { Search-Prompts $categories }
            }
        }
    }
}

function Browse-Categories {
    param($categories)
    $T = $script:Theme
    $sel = 0

    while ($true) {
        Clear-Screen
        $w = $script:Screen.Width; $h = $script:Screen.Height

        Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
        Write-Centered 1 '[=] Prompt Categories' 'White' $T.HeaderBG

        Draw-Box 3 4 ($w-6) ($h-8) $T.Border $T.BG $T.Title ' CATEGORIES '

        for ($i = 0; $i -lt $categories.Count; $i++) {
            $iy = 6 + $i * 2
            $isSel = ($i -eq $sel)
            $count = $categories[$i].prompts.Count
            $label = "$($categories[$i].name) ($count prompts)"
            if ($isSel) {
                Fill-Rect 5 $iy ($w-12) 1 ' ' $T.Selection $T.SelBG
                Write-Text 7 $iy $label $T.Selection $T.SelBG
                Write-Text 7 ($iy+1) "  $($categories[$i].icon)" $T.Accent
            } else {
                Write-Text 7 $iy $label $T.MenuLabel
                Write-Text 7 ($iy+1) "  $($categories[$i].icon)" $T.Dim
            }
        }

        Draw-Status ' [Up/Down] Navigate ' '[Enter] Browse' '[Esc] Back' 'Black' $T.StatusBG
        Flush-Screen

        $key = Read-Key
        if (Is-EscKey $key -or (Is-CharKey $key 'q')) { return }
        if (Is-UpKey $key) { $sel = ($sel - 1 + $categories.Count) % $categories.Count }
        if (Is-DownKey $key) { $sel = ($sel + 1) % $categories.Count }
        if (Is-EnterKey $key) { Browse-CategoryPrompts $categories[$sel] }
    }
}

function Browse-CategoryPrompts {
    param($category)
    $T = $script:Theme
    $sel = 0
    $prompts = $category.prompts

    while ($true) {
        Clear-Screen
        $w = $script:Screen.Width; $h = $script:Screen.Height

        Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
        Write-Centered 1 "[=] $($category.name)" 'White' $T.HeaderBG

        Draw-Box 3 4 ($w-6) ($h-8) $T.Border $T.BG $T.Title " $($category.icon) PROMPTS "

        for ($i = 0; $i -lt $prompts.Count; $i++) {
            $iy = 6 + $i * 2
            $isSel = ($i -eq $sel)
            if ($isSel) {
                Fill-Rect 5 $iy ($w-12) 1 ' ' $T.Selection $T.SelBG
                Write-Text 7 $iy "[$($i+1)] $($prompts[$i].title)" $T.Selection $T.SelBG
                $preview = $prompts[$i].prompt
                if ($preview.Length -gt ($w - 16)) {
                    $preview = $preview.Substring(0, ($w - 19)) + '...'
                }
                Write-Text 7 ($iy+1) "  $preview" $T.Accent
            } else {
                Write-Text 7 $iy "[$($i+1)] $($prompts[$i].title)" $T.MenuLabel
                Write-Text 7 ($iy+1) '  (Enter to view)' $T.Dim
            }
        }

        Draw-Status ' [Up/Down] Navigate ' '[Enter] View' '[Esc] Back' 'Black' $T.StatusBG
        Flush-Screen

        $key = Read-Key
        if (Is-EscKey $key -or (Is-CharKey $key 'q')) { return }
        if (Is-UpKey $key) { $sel = ($sel - 1 + $prompts.Count) % $prompts.Count }
        if (Is-DownKey $key) { $sel = ($sel + 1) % $prompts.Count }
        if (Is-EnterKey $key) { Show-PromptDetail $prompts[$sel] }
    }
}

function Show-PromptDetail {
    param($prompt)
    $T = $script:Theme
    Clear-Screen
    $w = $script:Screen.Width; $h = $script:Screen.Height

    Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
    Write-Centered 1 "[=] $($prompt.title)" 'White' $T.HeaderBG

    Draw-Box 3 4 ($w-6) ($h-8) $T.Border $T.BG $T.Title ' PROMPT DETAIL '

    $lines = $prompt.prompt -split "`n"
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

    Draw-Status ' Prompt Detail ' '[Esc] Back' '' 'Black' $T.StatusBG
    Flush-Screen

    do { $key = Read-Key } until ((Is-EscKey $key) -or (Is-EnterKey $key))
}

function View-Detail {
    param($categories)
    $T = $script:Theme
    $allPrompts = @()
    foreach ($cat in $categories) {
        foreach ($p in $cat.prompts) {
            $allPrompts += @{ Category=$cat.name; Title=$p.title; Prompt=$p.prompt }
        }
    }

    $sel = 0
    $offset = 0

    while ($true) {
        Clear-Screen
        $w = $script:Screen.Width; $h = $script:Screen.Height

        Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
        Write-Centered 1 '[=] Select Prompt to View' 'White' $T.HeaderBG

        $boxH = $h - 8
        Draw-Box 3 4 ($w-6) $boxH $T.Border $T.BG $T.Title ' ALL PROMPTS '

        $visible = [Math]::Max(1, [Math]::Floor(($boxH - 4) / 2))
        if ($sel -lt $offset) { $offset = $sel }
        if ($sel -ge $offset + $visible) { $offset = $sel - $visible + 1 }

        for ($i = 0; $i -lt $visible; $i++) {
            $idx = $i + $offset
            if ($idx -ge $allPrompts.Count) { break }
            $iy = 6 + $i * 2
            $isSel = ($idx -eq $sel)
            if ($isSel) {
                Fill-Rect 5 $iy ($w-12) 1 ' ' $T.Selection $T.SelBG
                Write-Text 7 $iy "$($allPrompts[$idx].Title)" $T.Selection $T.SelBG
                Write-Text 7 ($iy+1) "  [$($allPrompts[$idx].Category)]" $T.Accent
            } else {
                Write-Text 7 $iy "$($allPrompts[$idx].Title)" $T.MenuLabel
                Write-Text 7 ($iy+1) "  [$($allPrompts[$idx].Category)]" $T.Dim
            }
        }

        $scrollInfo = "[$($sel+1)/$($allPrompts.Count)]"
        Draw-Status ' [Up/Down] Navigate ' $scrollInfo '[Esc] Back' 'Black' $T.StatusBG
        Flush-Screen

        $key = Read-Key
        if (Is-EscKey $key -or (Is-CharKey $key 'q')) { return }
        if (Is-UpKey $key) { $sel = ($sel - 1 + $allPrompts.Count) % $allPrompts.Count }
        if (Is-DownKey $key) { $sel = ($sel + 1) % $allPrompts.Count }
        if (Is-EnterKey $key) { Show-PromptDetail $allPrompts[$sel] }
    }
}

function Copy-Prompt {
    param($categories)
    $T = $script:Theme
    $allPrompts = @()
    foreach ($cat in $categories) {
        foreach ($p in $cat.prompts) {
            $allPrompts += @{ Category=$cat.name; Title=$p.title; Prompt=$p.prompt }
        }
    }

    $sel = 0
    $offset = 0

    while ($true) {
        Clear-Screen
        $w = $script:Screen.Width; $h = $script:Screen.Height

        Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
        Write-Centered 1 '[=] Copy Prompt to Clipboard' 'White' $T.HeaderBG

        $boxH = $h - 8
        Draw-Box 3 4 ($w-6) $boxH $T.Border $T.BG $T.Title ' SELECT PROMPT '

        $visible = [Math]::Max(1, [Math]::Floor(($boxH - 4) / 2))
        if ($sel -lt $offset) { $offset = $sel }
        if ($sel -ge $offset + $visible) { $offset = $sel - $visible + 1 }

        for ($i = 0; $i -lt $visible; $i++) {
            $idx = $i + $offset
            if ($idx -ge $allPrompts.Count) { break }
            $iy = 6 + $i * 2
            $isSel = ($idx -eq $sel)
            if ($isSel) {
                Fill-Rect 5 $iy ($w-12) 1 ' ' $T.Selection $T.SelBG
                Write-Text 7 $iy "$($allPrompts[$idx].Title)" $T.Selection $T.SelBG
                Write-Text 7 ($iy+1) "  [$($allPrompts[$idx].Category)]" $T.Accent
            } else {
                Write-Text 7 $iy "$($allPrompts[$idx].Title)" $T.MenuLabel
                Write-Text 7 ($iy+1) "  [$($allPrompts[$idx].Category)]" $T.Dim
            }
        }

        $scrollInfo = "[$($sel+1)/$($allPrompts.Count)]"
        Draw-Status ' [Up/Down] Select ' $scrollInfo '[Esc] Back' 'Black' $T.StatusBG
        Flush-Screen

        $key = Read-Key
        if (Is-EscKey $key -or (Is-CharKey $key 'q')) { return }
        if (Is-UpKey $key) { $sel = ($sel - 1 + $allPrompts.Count) % $allPrompts.Count }
        if (Is-DownKey $key) { $sel = ($sel + 1) % $allPrompts.Count }
        if (Is-EnterKey $key) {
            try {
                $allPrompts[$idx].Prompt | Set-Clipboard
                Show-PromptSuccess "Copied '$($allPrompts[$idx].Title)' to clipboard"
            } catch {
                Show-PromptError 'Failed to copy to clipboard'
            }
            return
        }
    }
}

function Search-Prompts {
    param($categories)
    $T = $script:Theme

    $allPrompts = @()
    foreach ($cat in $categories) {
        foreach ($p in $cat.prompts) {
            $allPrompts += @{ Category=$cat.name; Title=$p.title; Prompt=$p.prompt }
        }
    }

    # Show a simple search with predefined keywords
    $keywords = @('review', 'test', 'security', 'performance', 'API', 'error', 'refactor', 'Docker', 'CI')
    $sel = 0

    while ($true) {
        Clear-Screen
        $w = $script:Screen.Width; $h = $script:Screen.Height

        Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
        Write-Centered 1 '[=] Search Prompts' 'White' $T.HeaderBG

        Draw-Box 3 4 ($w-6) ($h-8) $T.Border $T.BG $T.Title ' KEYWORD SEARCH '

        Write-Text 5 6 'Select a keyword to search all prompts:' $T.FG

        for ($i = 0; $i -lt $keywords.Count; $i++) {
            $iy = 8 + $i
            $isSel = ($i -eq $sel)
            if ($isSel) {
                Fill-Rect 5 $iy ($w-12) 1 ' ' $T.Selection $T.SelBG
                Write-Text 7 $iy $keywords[$i] $T.Selection $T.SelBG
            } else {
                Write-Text 7 $iy $keywords[$i] $T.MenuLabel
            }
        }

        Draw-Status ' [Up/Down] Select ' '[Enter] Search' '[Esc] Back' 'Black' $T.StatusBG
        Flush-Screen

        $key = Read-Key
        if (Is-EscKey $key -or (Is-CharKey $key 'q')) { return }
        if (Is-UpKey $key) { $sel = ($sel - 1 + $keywords.Count) % $keywords.Count }
        if (Is-DownKey $key) { $sel = ($sel + 1) % $keywords.Count }
        if (Is-EnterKey $key) {
            $keyword = $keywords[$sel].ToLower()
            $results = @()
            foreach ($p in $allPrompts) {
                if ($p.Title.ToLower().Contains($keyword) -or $p.Prompt.ToLower().Contains($keyword)) {
                    $results += $p
                }
            }
            Show-SearchResults $keyword $results
        }
    }
}

function Show-SearchResults {
    param([string]$keyword, $results)
    $T = $script:Theme
    $sel = 0
    $offset = 0

    while ($true) {
        Clear-Screen
        $w = $script:Screen.Width; $h = $script:Screen.Height

        Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
        Write-Centered 1 "[=] Search: $keyword" 'White' $T.HeaderBG

        $boxH = $h - 8
        Draw-Box 3 4 ($w-6) $boxH $T.Border $T.BG $T.Title " RESULTS ($($results.Count)) "

        if ($results.Count -eq 0) {
            Write-Text 7 7 'No prompts match this keyword.' $T.Dim
            Write-Text 7 9 'Try a different search term.' $T.Dim
        } else {
            $visible = [Math]::Max(1, [Math]::Floor(($boxH - 4) / 2))
            if ($sel -lt $offset) { $offset = $sel }
            if ($sel -ge $offset + $visible) { $offset = $sel - $visible + 1 }

            for ($i = 0; $i -lt $visible; $i++) {
                $idx = $i + $offset
                if ($idx -ge $results.Count) { break }
                $iy = 6 + $i * 2
                $isSel = ($idx -eq $sel)
                if ($isSel) {
                    Fill-Rect 5 $iy ($w-12) 1 ' ' $T.Selection $T.SelBG
                    Write-Text 7 $iy "$($results[$idx].Title)" $T.Selection $T.SelBG
                    Write-Text 7 ($iy+1) "  [$($results[$idx].Category)]" $T.Accent
                } else {
                    Write-Text 7 $iy "$($results[$idx].Title)" $T.MenuLabel
                    Write-Text 7 ($iy+1) "  [$($results[$idx].Category)]" $T.Dim
                }
            }
        }

        Draw-Status ' [Up/Down] Navigate ' '[Enter] View' '[Esc] Back' 'Black' $T.StatusBG
        Flush-Screen

        $key = Read-Key
        if (Is-EscKey $key -or (Is-CharKey $key 'q')) { return }
        if ($results.Count -gt 0) {
            if (Is-UpKey $key) { $sel = ($sel - 1 + $results.Count) % $results.Count }
            if (Is-DownKey $key) { $sel = ($sel + 1) % $results.Count }
            if (Is-EnterKey $key) { Show-PromptDetail $results[$sel] }
        }
    }
}

function Show-PromptSuccess {
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

function Show-PromptError {
    param([string]$Message)
    $T = $script:Theme
    Clear-Screen
    $w = $script:Screen.Width; $h = $script:Screen.Height

    $boxW = [Math]::Min(50, $w - 6)
    $boxH = 8
    $boxX = [Math]::Floor(($w - $boxW) / 2)
    $boxY = [Math]::Floor(($h - $boxH) / 2)

    Draw-Box $boxX $boxY $boxW $boxH $T.Error $T.BG $T.Error ' ERROR '

    Write-Centered ($boxY + 3) $Message $T.FG

    Draw-Status ' Error ' '' '[Esc] Back' 'Black' $T.StatusBG
    Flush-Screen

    do { $key = Read-Key } until ((Is-EscKey $key) -or (Is-EnterKey $key))
}
