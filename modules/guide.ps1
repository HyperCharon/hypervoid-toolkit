<#
.SYNOPSIS
    Best Practices Guide - TUI Version
    Scrollable reference guide for Claude Code best practices
#>

function Invoke-Guide {
    $T = $script:Theme
    $sel = 0
    $items = @(
        @{ Label='CLAUDE.md Tips';        Desc='Project configuration best practices' }
        @{ Label='Prompt Engineering';     Desc='Write effective prompts for Claude' }
        @{ Label='Workflows';             Desc='Optimize your development workflow' }
        @{ Label='Permissions';           Desc='Configure security and access rules' }
        @{ Label='Hooks';                 Desc='Automate with pre/post hooks' }
        @{ Label='MCP Integration';       Desc='Connect external tools via MCP' }
    )

    while ($true) {
        Clear-Screen
        $w = $script:Screen.Width; $h = $script:Screen.Height

        Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
        Write-Centered 1 '[^] Best Practices Guide' 'White' $T.HeaderBG

        Draw-Box 3 4 ($w-6) ($h-8) $T.Border $T.BG $T.Title ' SECTIONS '

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
                0 { Show-GuideSection 'CLAUDE.md Tips' (Get-ClaudeMdTips) }
                1 { Show-GuideSection 'Prompt Engineering' (Get-PromptEngineering) }
                2 { Show-GuideSection 'Workflows' (Get-Workflows) }
                3 { Show-GuideSection 'Permissions' (Get-PermissionsGuide) }
                4 { Show-GuideSection 'Hooks' (Get-HooksGuide) }
                5 { Show-GuideSection 'MCP Integration' (Get-McpGuide) }
            }
        }
    }
}

function Show-GuideSection {
    param([string]$Title, $lines)
    $T = $script:Theme
    $offset = 0

    while ($true) {
        Clear-Screen
        $w = $script:Screen.Width; $h = $script:Screen.Height

        Fill-Rect 0 0 $w 3 ' ' 'White' $T.HeaderBG
        Write-Centered 1 "[^] $Title" 'White' $T.HeaderBG

        $boxH = $h - 8
        Draw-Box 3 4 ($w-6) $boxH $T.Border $T.BG $T.Title " $Title "

        $visibleLines = $boxH - 4
        if ($offset -gt ($lines.Count - $visibleLines)) {
            $offset = [Math]::Max(0, $lines.Count - $visibleLines)
        }
        if ($offset -lt 0) { $offset = 0 }

        $lineY = 6
        for ($i = 0; $i -lt $visibleLines; $i++) {
            $idx = $i + $offset
            if ($idx -ge $lines.Count) { break }
            $displayLine = $lines[$idx]
            if ($displayLine.Length -gt ($w - 14)) {
                $displayLine = $displayLine.Substring(0, ($w - 17)) + '...'
            }

            $lineColor = $T.FG
            if ($displayLine.StartsWith('  *') -or $displayLine.StartsWith('  -')) {
                $lineColor = $T.Accent
            } elseif ($displayLine.StartsWith('  ') -and $displayLine.Trim().Length -gt 0) {
                $lineColor = $T.MenuLabel
            } elseif ($displayLine.Trim().EndsWith(':')) {
                $lineColor = $T.Warning
            }

            Write-Text 5 $lineY $displayLine $lineColor
            $lineY++
        }

        $scrollPos = ''
        if ($lines.Count -gt $visibleLines) {
            $pct = [Math]::Floor(($offset / ($lines.Count - $visibleLines)) * 100)
            $scrollPos = "$pct%"
        }
        $lineInfo = "Line $($offset+1)-$([Math]::Min($offset+$visibleLines,$lines.Count)) of $($lines.Count)"

        Draw-Status ' [Up/Down] Scroll ' $lineInfo '[Esc] Back' 'Black' $T.StatusBG
        Flush-Screen

        $key = Read-Key
        if (Is-EscKey $key -or (Is-CharKey $key 'q')) { return }
        if (Is-UpKey $key) { $offset = [Math]::Max(0, $offset - 1) }
        if (Is-DownKey $key) { $offset = [Math]::Min([Math]::Max(0, $lines.Count - $visibleLines), $offset + 1) }
    }
}

function Get-ClaudeMdTips {
    return @(
        'CLAUDE.md Project Configuration'
        ''
        'The CLAUDE.md file is your project memory. It tells Claude about'
        'your project structure, conventions, and preferences.'
        ''
        'Key sections to include:'
        ''
        '  * Project Overview'
        '    - What the project does'
        '    - Tech stack and frameworks'
        '    - Repository structure'
        ''
        '  * Coding Conventions'
        '    - Naming conventions (camelCase, snake_case, etc.)'
        '    - Import style and module organization'
        '    - Error handling patterns'
        '    - Testing requirements'
        ''
        '  * Build and Run'
        '    - How to install dependencies'
        '    - How to build the project'
        '    - How to run tests'
        '    - How to start the dev server'
        ''
        '  * Important Files'
        '    - Entry points and main modules'
        '    - Configuration files'
        '    - Shared utilities and helpers'
        ''
        'Tips:'
        ''
        '  - Keep it concise. Claude reads it every conversation.'
        '  - Use bullet points, not paragraphs.'
        '  - Include actual commands, not descriptions.'
        '  - Update it as your project evolves.'
        '  - Place it in the project root directory.'
        ''
        'Example structure:'
        ''
        '  # Project Name'
        '  Brief description of what this project does.'
        ''
        '  ## Tech Stack'
        '  - Language: TypeScript 5.x'
        '  - Framework: Next.js 14'
        '  - Database: PostgreSQL'
        ''
        '  ## Commands'
        '  - Install: npm install'
        '  - Build: npm run build'
        '  - Test: npm test'
        '  - Lint: npm run lint'
        ''
        '  ## Conventions'
        '  - Use functional components'
        '  - Prefer named exports'
        '  - All tests use Jest + Testing Library'
    )
}

function Get-PromptEngineering {
    return @(
        'Prompt Engineering for Claude Code'
        ''
        'Writing effective prompts gets better results from Claude.'
        ''
        'Principles:'
        ''
        '  * Be Specific'
        '    - Bad: "Fix the bug"'
        '    - Good: "Fix the null pointer in UserService.getProfile() when userId is undefined"'
        ''
        '  * Provide Context'
        '    - Mention the file, function, or module'
        '    - Reference related code or documentation'
        '    - Explain the expected behavior'
        ''
        '  * Use Step-by-Step Instructions'
        '    - Break complex tasks into numbered steps'
        '    - Specify the order of operations'
        '    - Define success criteria'
        ''
        '  * Include Examples'
        '    - Show expected input/output'
        '    - Reference similar patterns in the codebase'
        '    - Provide test cases'
        ''
        '  * Set Constraints'
        '    - Specify language/framework versions'
        '    - Mention performance requirements'
        '    - Define error handling expectations'
        ''
        'Effective Patterns:'
        ''
        '  - "Review this code for X, Y, Z issues"'
        '  - "Refactor this function to follow SOLID principles"'
        '  - "Write tests that cover edge cases A, B, C"'
        '  - "Explain how X works and suggest improvements"'
        ''
        'Using Slash Commands:'
        ''
        '  - /review for code reviews'
        '  - /test for test generation'
        '  - /refactor for code improvement'
        '  - /explain for documentation'
        ''
        'Tips for Complex Tasks:'
        ''
        '  1. Start with a high-level request'
        '  2. Review the initial response'
        '  3. Ask for refinements with specifics'
        '  4. Iterate until satisfied'
    )
}

function Get-Workflows {
    return @(
        'Development Workflows with Claude Code'
        ''
        'Optimize your workflow with these patterns.'
        ''
        'Code Review Workflow:'
        ''
        '  1. Write or modify code'
        '  2. Run /review to check for issues'
        '  3. Address findings'
        '  4. Run /test to generate tests'
        '  5. Verify tests pass'
        '  6. Commit with descriptive message'
        ''
        'Feature Development:'
        ''
        '  1. Describe the feature to Claude'
        '  2. Review the proposed implementation'
        '  3. Ask Claude to implement step by step'
        '  4. Test each component as built'
        '  5. Run /refactor for cleanup'
        '  6. Update documentation'
        ''
        'Debugging Workflow:'
        ''
        '  1. Share the error message or behavior'
        '  2. Ask Claude to analyze the root cause'
        '  3. Review the suggested fix'
        '  4. Apply and test the fix'
        '  5. Ask for prevention strategies'
        ''
        'Documentation Workflow:'
        ''
        '  1. Run /explain on complex modules'
        '  2. Review generated documentation'
        '  3. Add to README or docs folder'
        '  4. Update CLAUDE.md if needed'
        ''
        'Best Practices:'
        ''
        '  - Use CLAUDE.md to maintain context'
        '  - Commit frequently with good messages'
        '  - Use hooks for automated checks'
        '  - Keep prompts focused and specific'
        '  - Review all generated code before committing'
    )
}

function Get-PermissionsGuide {
    return @(
        'Permissions Configuration Guide'
        ''
        'Control what Claude can and cannot do in your project.'
        ''
        'Configuration File:'
        ''
        '  Location: .claude/settings.json'
        '  Format: JSON with permissions.allow and permissions.deny'
        ''
        'Allow Rules:'
        ''
        '  Grant Claude access to specific tools.'
        ''
        '  Common allow rules:'
        '    "Read(.*)"        - Read any file'
        '    "Glob(.*)"        - Search for files'
        '    "Grep(.*)"        - Search file contents'
        '    "Edit(.*)"        - Edit files'
        '    "Write(.*)"       - Create/overwrite files'
        '    "Bash(npm *)"     - Run npm commands'
        '    "Bash(git *)"     - Run git commands'
        ''
        'Deny Rules:'
        ''
        '  Block access to sensitive paths or commands.'
        ''
        '  Common deny rules:'
        '    "Read(.env)"      - Block .env files'
        '    "Read(*.key)"     - Block key files'
        '    "Bash(rm *)"      - Block delete commands'
        '    "Write(node_modules/**)" - Block node_modules'
        ''
        'Pattern Matching:'
        ''
        '  *  matches any characters'
        '  ?  matches single character'
        '  ** matches path separators'
        ''
        'Examples:'
        ''
        '  Allow reading src directory:'
        '    "Read(src/**)"'
        ''
        '  Allow running tests:'
        '    "Bash(npm test*)"'
        ''
        '  Deny accessing secrets:'
        '    "Read(**/*secret*)'
        '    "Read(**/*credential*)"'
        ''
        'Security Tips:'
        ''
        '  - Always deny access to .env and secret files'
        '  - Limit bash commands to known safe operations'
        '  - Use specific patterns, not broad wildcards'
        '  - Review permissions after project changes'
    )
}

function Get-HooksGuide {
    return @(
        'Hooks Configuration Guide'
        ''
        'Hooks let you run custom scripts at specific points.'
        ''
        'Hook Types:'
        ''
        '  * PreToolUse  - Runs before a tool executes'
        '  * PostToolUse - Runs after a tool executes'
        '  * Notification - Runs when Claude sends a notification'
        ''
        'Configuration:'
        ''
        '  In .claude/settings.json:'
        ''
        '  {'
        '    "hooks": {'
        '      "PreToolUse": ['
        '        {'
        '          "matcher": "Write",'
        '          "command": "lint-staged"'
        '        }'
        '      ]'
        '    }'
        '  }'
        ''
        'Common Use Cases:'
        ''
        '  * Auto-lint after file writes'
        '    matcher: "Write"'
        '    command: "npx eslint --fix $FILE"'
        ''
        '  * Run tests before commits'
        '    matcher: "Bash(git commit*)"'
        '    command: "npm test"'
        ''
        '  * Format code after edits'
        '    matcher: "Edit"'
        '    command: "npx prettier --write $FILE"'
        ''
        'Environment Variables:'
        ''
        '  $FILE   - Path to the file being operated on'
        '  $TOOL   - Name of the tool being used'
        '  $ARGS   - Arguments passed to the tool'
        ''
        'Tips:'
        ''
        '  - Keep hooks fast to avoid slowing Claude'
        '  - Use matchers to target specific tools'
        '  - Handle errors gracefully in hook scripts'
        '  - Test hooks before deploying'
        '  - Use hooks for linting, formatting, and validation'
    )
}

function Get-McpGuide {
    return @(
        'MCP Integration Guide'
        ''
        'Model Context Protocol connects Claude to external tools.'
        ''
        'What is MCP?'
        ''
        '  MCP is a protocol that lets Claude access external'
        '  data sources and tools through standardized servers.'
        ''
        'Available Servers:'
        ''
        '  * GitHub - Access repos, issues, PRs'
        '  * Filesystem - Read/write local files'
        '  * Brave Search - Web search'
        '  * Puppeteer - Browser automation'
        '  * PostgreSQL - Database queries'
        '  * SQLite - Local database'
        '  * Slack - Team messaging'
        '  * Memory - Knowledge graph'
        '  * Fetch - HTTP requests'
        ''
        'Setup:'
        ''
        '  1. Install the server package via npm'
        '  2. Add configuration to .claude/settings.json'
        '  3. Set required environment variables'
        '  4. Restart Claude to load the server'
        ''
        'Configuration Format:'
        ''
        '  {'
        '    "mcpServers": {'
        '      "server-name": {'
        '        "command": "npx",'
        '        "args": ["@modelcontextprotocol/server-name"]'
        '      }'
        '    }'
        '  }'
        ''
        'With Environment Variables:'
        ''
        '  {'
        '    "mcpServers": {'
        '      "github": {'
        '        "command": "npx",'
        '        "args": ['
        '          "@modelcontextprotocol/server-github",'
        '          "--env",'
        '          "GITHUB_PERSONAL_ACCESS_TOKEN=..."'
        '        ]'
        '      }'
        '    }'
        '  }'
        ''
        'Tips:'
        ''
        '  - Start with one server at a time'
        '  - Check server documentation for required args'
        '  - Use environment variables for secrets'
        '  - Servers run as separate processes'
        '  - Monitor server logs for debugging'
    )
}
