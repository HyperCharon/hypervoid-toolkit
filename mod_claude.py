"""
mod_claude.py - Claude Code CLI features module
Provides: command reference, CLAUDE.md generator/editor, project scanner,
          session manager, and cost tracker.
"""

import os
import re
import shutil
import subprocess
from pathlib import Path

from rich.align import Align
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from rich import box

from tui_base import (
    console, T, read_key, wait_key, clear,
    menu, scroll_view, show_table, show_ok, show_err,
    draw_header, draw_logo, draw_divider,
    draw_status_bar, draw_project_info,
    load_json, save_json, DATA_DIR,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Data: Command Reference
# ═══════════════════════════════════════════════════════════════════════════════

CMD_CATEGORIES = [
    {
        "name": "CLI 命令",
        "icon": ">_",
        "items": [
            ("claude", "启动交互式 REPL 会话"),
            ("claude \"prompt\"", "直接发送提示词 (非交互模式)"),
            ("claude -p \"prompt\"", "管道模式: 从 stdin 读取, 输出到 stdout"),
            ("claude --resume", "恢复之前的会话"),
            ("claude --continue", "继续最近一次会话"),
            ("claude --model <model>", "指定使用的模型"),
            ("claude --max-turns <n>", "限制最大对话轮次"),
            ("claude --allowedTools <tools>", "限制可用工具 (逗号分隔)"),
            ("claude --disallowedTools <tools>", "禁用指定工具"),
            ("claude --output-format json", "JSON 格式输出"),
            ("claude --output-format stream-json", "流式 JSON 输出"),
            ("claude --system-prompt <prompt>", "自定义系统提示词"),
            ("claude --append-system-prompt <prompt>", "追加系统提示词"),
            ("claude -v / --version", "显示版本信息"),
            ("claude -h / --help", "显示帮助信息"),
            ("claude config <key> <value>", "设置配置项"),
            ("claude update", "更新 Claude Code"),
            ("claude mcp <subcommand>", "管理 MCP 服务器"),
            ("claude doctor", "诊断环境和配置问题"),
        ],
    },
    {
        "name": "斜杠命令",
        "icon": "/",
        "items": [
            ("/help", "显示帮助信息"),
            ("/compact", "压缩对话上下文 (可指定重点)"),
            ("/clear", "清空当前对话历史"),
            ("/config", "查看/修改配置"),
            ("/cost", "显示当前会话的 token 用量和费用"),
            ("/init", "在当前目录初始化 CLAUDE.md"),
            ("/login", "登录/切换账号"),
            ("/logout", "登出当前账号"),
            ("/model <model>", "切换模型"),
            ("/permissions", "查看/修改权限设置"),
            ("/pr-review", "创建 Pull Request 审查"),
            ("/review", "请求代码审查"),
            ("/status", "显示当前会话状态"),
            ("/terminal-setup", "配置终端集成"),
            ("/vim", "切换 Vim 模式"),
            ("/mcp", "查看 MCP 服务器状态"),
            ("/memory", "打开记忆文件进行编辑"),
            ("/bug <description>", "提交 Bug 报告"),
            ("/doctor", "检查环境和配置健康状况"),
        ],
    },
    {
        "name": "快捷键",
        "icon": "⌨",
        "items": [
            ("Ctrl+C", "取消当前输入 / 中断生成"),
            ("Ctrl+D", "退出会话 (EOF)"),
            ("Ctrl+L", "清屏"),
            ("Ctrl+R", "反向搜索历史命令"),
            ("Escape", "取消当前输入行"),
            ("Tab", "自动补全"),
            ("↑ / ↓", "浏览输入历史"),
            ("Enter", "发送消息"),
            ("Shift+Enter", "换行 (多行输入)"),
            ("Ctrl+Shift+Backspace", "删除最后一个工具调用"),
        ],
    },
    {
        "name": "管道与输入",
        "icon": "|",
        "items": [
            ("echo \"prompt\" | claude", "通过管道传入提示词"),
            ("cat file.py | claude \"review\"", "将文件内容管道传入"),
            ("claude -p \"summarize\" < doc.txt", "从文件重定向输入"),
            ("claude -p \"prompt\" --output-format json", "管道 + JSON 输出"),
            ("git diff | claude \"explain\"", "传入 git diff 进行解释"),
            ("git log | claude \"summarize\"", "传入 git 日志进行总结"),
            ("docker logs app | claude \"debug\"", "传入容器日志进行调试"),
            ("cat error.log | claude \"fix\"", "传入错误日志请求修复"),
        ],
    },
    {
        "name": "配置文件",
        "icon": "⚙",
        "items": [
            ("~/.claude/settings.json", "全局用户设置"),
            (".claude/settings.json", "项目级设置 (Git 提交共享)"),
            (".claude/settings.local.json", "项目级本地设置 (不提交)"),
            ("CLAUDE.md", "项目根目录的指令文件"),
            ("CLAUDE.local.md", "本地指令文件 (不提交)"),
            ("~/.claude/CLAUDE.md", "全局指令文件"),
            (".claude/commands/", "自定义斜杠命令目录"),
            (".mcp.json", "MCP 服务器配置"),
            ("~/.claude.json", "认证和账户信息"),
            ("~/.claude/statsig/", "特性标志和实验缓存"),
        ],
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# Data: CLAUDE.md Templates
# ═══════════════════════════════════════════════════════════════════════════════

CLAUDE_TEMPLATES = {
    "typescript": {
        "name": "TypeScript",
        "lang": "TypeScript",
        "framework": "Node.js",
        "pkg": "npm",
        "test": "jest",
        "lint": "eslint + prettier",
        "ext": ".ts",
    },
    "python": {
        "name": "Python",
        "lang": "Python",
        "framework": "Standard",
        "pkg": "pip",
        "test": "pytest",
        "lint": "ruff",
        "ext": ".py",
    },
    "go": {
        "name": "Go",
        "lang": "Go",
        "framework": "Standard",
        "pkg": "go",
        "test": "go test",
        "lint": "golangci-lint",
        "ext": ".go",
    },
    "rust": {
        "name": "Rust",
        "lang": "Rust",
        "framework": "Standard",
        "pkg": "cargo",
        "test": "cargo test",
        "lint": "clippy",
        "ext": ".rs",
    },
    "react_vue": {
        "name": "React / Vue",
        "lang": "TypeScript",
        "framework": "React / Vue",
        "pkg": "npm",
        "test": "vitest",
        "lint": "eslint + prettier",
        "ext": ".tsx",
    },
    "java": {
        "name": "Java",
        "lang": "Java",
        "framework": "Spring Boot",
        "pkg": "maven",
        "test": "JUnit 5",
        "lint": "checkstyle",
        "ext": ".java",
    },
    "custom": {
        "name": "自定义",
        "lang": "",
        "framework": "",
        "pkg": "",
        "test": "",
        "lint": "",
        "ext": "",
    },
}

# Commands generated per package manager
PKG_COMMANDS = {
    "npm": {
        "install": "npm install",
        "dev":     "npm run dev",
        "build":   "npm run build",
        "test":    "npm test",
        "lint":    "npm run lint",
    },
    "pnpm": {
        "install": "pnpm install",
        "dev":     "pnpm dev",
        "build":   "pnpm build",
        "test":    "pnpm test",
        "lint":    "pnpm lint",
    },
    "yarn": {
        "install": "yarn install",
        "dev":     "yarn dev",
        "build":   "yarn build",
        "test":    "yarn test",
        "lint":    "yarn lint",
    },
    "pip": {
        "install": "pip install -r requirements.txt",
        "dev":     "python -m app",
        "build":   "python -m build",
        "test":    "pytest",
        "lint":    "ruff check .",
    },
    "poetry": {
        "install": "poetry install",
        "dev":     "poetry run python -m app",
        "build":   "poetry build",
        "test":    "poetry run pytest",
        "lint":    "poetry run ruff check .",
    },
    "go": {
        "install": "go mod download",
        "dev":     "go run .",
        "build":   "go build ./...",
        "test":    "go test ./...",
        "lint":    "golangci-lint run",
    },
    "cargo": {
        "install": "cargo fetch",
        "dev":     "cargo run",
        "build":   "cargo build --release",
        "test":    "cargo test",
        "lint":    "cargo clippy -- -D warnings",
    },
    "maven": {
        "install": "mvn install -DskipTests",
        "dev":     "mvn spring-boot:run",
        "build":   "mvn package",
        "test":    "mvn test",
        "lint":    "mvn checkstyle:check",
    },
    "gradle": {
        "install": "./gradlew build -x test",
        "dev":     "./gradlew bootRun",
        "build":   "./gradlew build",
        "test":    "./gradlew test",
        "lint":    "./gradlew checkstyleMain",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# 1. cmd_ref() - Command Reference Browser
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_ref() -> None:
    """Interactive command reference browser with tabbed categories."""
    cat_idx = 0
    scroll_offset = 0
    page_size = max(console.height - 14, 6)

    while True:
        clear()
        draw_header("命令参考", "Claude Code CLI 命令速查手册")

        # ── Category tabs ─────────────────────────────────────────────────────
        num_cats = len(CMD_CATEGORIES)
        tab_line = Text()
        tab_line.append("    ")  # left margin
        for i, cat in enumerate(CMD_CATEGORIES):
            label = f" {cat['icon']} {cat['name']} "
            if i == cat_idx:
                tab_line.append(label, style=f"bold {T.TITLE} on {T.PRIMARY}")
            else:
                tab_line.append(label, style=f"{T.MUTED} on {T.HEADER_BG}")
            tab_line.append(" ")
        console.print(tab_line)

        # ── Content area ──────────────────────────────────────────────────────
        cat = CMD_CATEGORIES[cat_idx]
        items = cat["items"]
        total = len(items)

        # build header row
        tbl = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style=f"bold {T.PRIMARY}",
                     expand=True, padding=(0, 1))
        tbl.add_column("#", width=4, justify="right")
        tbl.add_column("命令", min_width=30)
        tbl.add_column("说明", ratio=1)

        visible = items[scroll_offset:scroll_offset + page_size]
        for j, (cmd, desc) in enumerate(visible):
            row_num = scroll_offset + j + 1
            tbl.add_row(
                Text(str(row_num), style=T.DIM),
                Text(cmd, style=T.SECONDARY),
                Text(desc),
            )
        console.print(tbl)

        # ── Status bar ────────────────────────────────────────────────────────
        console.print()
        left_info = f"Tab {cat_idx + 1}/{num_cats} | 条目 {scroll_offset + 1}-{min(scroll_offset + page_size, total)}/{total}"
        right_info = "←→ 切换分类 | ↑↓ 滚动 | 数字跳转 | Esc 返回"
        draw_status_bar(left_info, right_info)

        # ── Input handling ────────────────────────────────────────────────────
        key = read_key()
        if key == "esc":
            return
        elif key == "left":
            cat_idx = (cat_idx - 1) % num_cats
            scroll_offset = 0
        elif key == "right":
            cat_idx = (cat_idx + 1) % num_cats
            scroll_offset = 0
        elif key == "up":
            scroll_offset = max(0, scroll_offset - 1)
        elif key == "down":
            scroll_offset = min(max(0, total - page_size), scroll_offset + 1)
        elif key == "pgup":
            scroll_offset = max(0, scroll_offset - page_size)
        elif key == "pgdn":
            scroll_offset = min(max(0, total - page_size), scroll_offset + page_size)
        elif key == "home":
            scroll_offset = 0
        elif key == "end":
            scroll_offset = max(0, total - page_size)
        elif key.isdigit():
            n = int(key)
            if 1 <= n <= total:
                scroll_offset = min(n - 1, max(0, total - page_size))


# ═══════════════════════════════════════════════════════════════════════════════
# 2. gen_claudemd() - CLAUDE.md Generator
# ═══════════════════════════════════════════════════════════════════════════════

def _build_claudemd_content(template: dict, project_name: str) -> str:
    """Build CLAUDE.md content from a template dict."""
    lang = template["lang"]
    framework = template["framework"]
    pkg = template["pkg"]
    test = template["test"]
    lint = template["lint"]

    # Lookup commands
    cmds = PKG_COMMANDS.get(pkg, {})
    install_cmd = cmds.get("install", f"# TODO: install command for {pkg}")
    dev_cmd     = cmds.get("dev", f"# TODO: dev command for {pkg}")
    build_cmd   = cmds.get("build", f"# TODO: build command for {pkg}")
    test_cmd    = cmds.get("test", f"# TODO: test command for {pkg}")
    lint_cmd    = cmds.get("lint", f"# TODO: lint command for {pkg}")

    content = f"""# CLAUDE.md - {project_name}

This file provides instructions for Claude Code when working in this repository.

## Project Overview

- **Language**: {lang}
- **Framework**: {framework}
- **Package Manager**: {pkg}

## Common Commands

```bash
# Install dependencies
{install_cmd}

# Start development server
{dev_cmd}

# Build for production
{build_cmd}

# Run tests
{test_cmd}

# Lint code
{lint_cmd}
```

## Code Style

- **Testing**: {test}
- **Linting**: {lint}
- Write clean, well-documented code
- Follow existing project conventions
- Use meaningful variable and function names

## Guidelines

- Always run tests before committing
- Keep changes focused and minimal
- Write descriptive commit messages
- Prefer composition over inheritance
- Handle errors explicitly; avoid silent failures
"""
    return content


def gen_claudemd() -> None:
    """Interactive CLAUDE.md generator with template selection."""
    draw_header("CLAUDE.md 生成器", "选择项目模板，自动生成 CLAUDE.md 指令文件")

    # Template selection
    template_keys = list(CLAUDE_TEMPLATES.keys())
    template_names = [CLAUDE_TEMPLATES[k]["name"] for k in template_keys]

    idx = menu("选择项目模板", template_names, allow_esc=True)
    if idx < 0:
        return

    template = CLAUDE_TEMPLATES[template_keys[idx]]
    project_name = Path.cwd().name

    # For custom template, prompt for values
    if template_keys[idx] == "custom":
        console.print()
        console.print(f"  [{T.INFO}]自定义模板配置[/]")
        console.print(f"  [{T.MUTED}]直接回车使用默认值[/]")
        console.print()

        lang = console.input(f"  {T.PROMPT}语言 [{T.MUTED}]Custom[/]: ").strip() or "Custom"
        framework = console.input(f"  {T.PROMPT}框架 [{T.MUTED}]None[/]: ").strip() or "None"
        pkg = console.input(f"  {T.PROMPT}包管理器 [{T.MUTED}]npm[/]: ").strip() or "npm"
        test = console.input(f"  {T.PROMPT}测试工具 [{T.MUTED}]jest[/]: ").strip() or "jest"
        lint = console.input(f"  {T.PROMPT}Lint 工具 [{T.MUTED}]eslint[/]: ").strip() or "eslint"

        template = {
            "name": "自定义",
            "lang": lang,
            "framework": framework,
            "pkg": pkg,
            "test": test,
            "lint": lint,
            "ext": "",
        }

    # Generate content
    content = _build_claudemd_content(template, project_name)

    # Preview
    clear()
    draw_header("预览 CLAUDE.md", f"模板: {template['name']}")
    preview_lines = content.split("\n")
    for line in preview_lines[:30]:
        console.print(f"  {line}", highlight=False)
    if len(preview_lines) > 30:
        console.print(f"  [{T.MUTED}]... ({len(preview_lines)} 行)[/]")
    console.print()

    choice = menu("操作", ["写入 CLAUDE.md", "取消"], allow_esc=True)
    if choice != 0:
        return

    # Write file
    target = Path.cwd() / "CLAUDE.md"
    try:
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        show_ok(f"已写入 {target}")
    except OSError as e:
        show_err(f"写入失败: {e}")

    wait_key()


# ═══════════════════════════════════════════════════════════════════════════════
# 3. edit_claudemd() - CLAUDE.md Editor
# ═══════════════════════════════════════════════════════════════════════════════

def edit_claudemd() -> None:
    """View, edit, or regenerate CLAUDE.md."""
    target = Path.cwd() / "CLAUDE.md"

    if not target.exists():
        console.print()
        show_err("当前目录没有 CLAUDE.md 文件")
        console.print()
        choice = menu("操作", ["生成 CLAUDE.md", "返回"], allow_esc=True)
        if choice == 0:
            gen_claudemd()
        return

    # File exists - show content
    content = target.read_text(encoding="utf-8")
    lines = content.split("\n")

    while True:
        clear()
        draw_header("CLAUDE.md 编辑器", str(target.resolve()))

        # Show file info
        stat = target.stat()
        size_kb = stat.st_size / 1024
        line_count = len(lines)
        console.print(f"  [{T.MUTED}]大小: {size_kb:.1f} KB | 行数: {line_count}[/]")
        console.print()

        # Show first 5 lines as preview
        for line in lines[:5]:
            console.print(f"  {line}", highlight=False)
        if line_count > 5:
            console.print(f"  [{T.MUTED}]...[/]")
        console.print()

        draw_divider()
        choice = menu("操作", [
            "查看完整内容",
            "用系统编辑器打开",
            "重新生成",
            "返回",
        ], allow_esc=True)

        if choice == 0:
            # Scroll view
            scroll_view("CLAUDE.md", lines, line_numbers=True)
        elif choice == 1:
            # Open in default editor
            try:
                os.startfile(str(target))
                show_ok("已在默认编辑器中打开")
            except OSError as e:
                # Fallback: try common editors
                for editor in ["code", "notepad"]:
                    try:
                        subprocess.Popen([editor, str(target)])
                        show_ok(f"已用 {editor} 打开")
                        break
                    except FileNotFoundError:
                        continue
                else:
                    show_err(f"无法打开编辑器: {e}")
            wait_key()
        elif choice == 2:
            gen_claudemd()
            # Reload after regeneration
            if target.exists():
                content = target.read_text(encoding="utf-8")
                lines = content.split("\n")
        elif choice == 3 or choice == -1:
            return


# ═══════════════════════════════════════════════════════════════════════════════
# 4. scan_project() - Project Scanner
# ═══════════════════════════════════════════════════════════════════════════════

# Project detection signatures
PROJECT_SIGNATURES = [
    {
        "marker": "package.json",
        "lang": "TypeScript/JavaScript",
        "framework_hint": "Node.js",
        "pkg": "npm",
        "parser": "_parse_package_json",
    },
    {
        "marker": "tsconfig.json",
        "lang": "TypeScript",
        "framework_hint": "Node.js",
        "pkg": "npm",
        "parser": None,
    },
    {
        "marker": "requirements.txt",
        "lang": "Python",
        "framework_hint": "Python",
        "pkg": "pip",
        "parser": "_parse_requirements_txt",
    },
    {
        "marker": "pyproject.toml",
        "lang": "Python",
        "framework_hint": "Python",
        "pkg": "pip",
        "parser": "_parse_pyproject_toml",
    },
    {
        "marker": "go.mod",
        "lang": "Go",
        "framework_hint": "Go",
        "pkg": "go",
        "parser": "_parse_go_mod",
    },
    {
        "marker": "Cargo.toml",
        "lang": "Rust",
        "framework_hint": "Rust",
        "pkg": "cargo",
        "parser": "_parse_cargo_toml",
    },
    {
        "marker": "pom.xml",
        "lang": "Java",
        "framework_hint": "Maven/Spring Boot",
        "pkg": "maven",
        "parser": None,
    },
    {
        "marker": "build.gradle",
        "lang": "Java",
        "framework_hint": "Gradle/Spring Boot",
        "pkg": "gradle",
        "parser": None,
    },
    {
        "marker": "Gemfile",
        "lang": "Ruby",
        "framework_hint": "Ruby",
        "pkg": "gem",
        "parser": None,
    },
    {
        "marker": "composer.json",
        "lang": "PHP",
        "framework_hint": "PHP/Laravel",
        "pkg": "composer",
        "parser": None,
    },
    {
        "marker": "CMakeLists.txt",
        "lang": "C/C++",
        "framework_hint": "CMake",
        "pkg": "cmake",
        "parser": None,
    },
]


def _parse_package_json(directory: Path) -> dict:
    """Parse package.json to extract project info."""
    info = {"deps": [], "dev_deps": [], "scripts": [], "framework": "Node.js"}
    try:
        data = load_json(directory / "package.json", {})
        info["name"] = data.get("name", "")
        info["deps"] = list(data.get("dependencies", {}).keys())
        info["dev_deps"] = list(data.get("devDependencies", {}).keys())
        info["scripts"] = list(data.get("scripts", {}).keys())

        # Detect framework
        all_deps = info["deps"] + info["dev_deps"]
        if "react" in all_deps or "react-dom" in all_deps:
            info["framework"] = "React"
        elif "vue" in all_deps:
            info["framework"] = "Vue"
        elif "next" in all_deps:
            info["framework"] = "Next.js"
        elif "nuxt" in all_deps:
            info["framework"] = "Nuxt"
        elif "express" in all_deps:
            info["framework"] = "Express"
        elif "fastify" in all_deps:
            info["framework"] = "Fastify"
        elif "angular" in all_deps or "@angular/core" in all_deps:
            info["framework"] = "Angular"
        elif "svelte" in all_deps:
            info["framework"] = "Svelte"

        # Detect package manager
        if (directory / "pnpm-lock.yaml").exists():
            info["pkg"] = "pnpm"
        elif (directory / "yarn.lock").exists():
            info["pkg"] = "yarn"
        else:
            info["pkg"] = "npm"
    except Exception:
        pass
    return info


def _parse_requirements_txt(directory: Path) -> dict:
    """Parse requirements.txt."""
    info = {"deps": [], "framework": "Python"}
    try:
        content = (directory / "requirements.txt").read_text(encoding="utf-8")
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("-"):
                # Extract package name
                pkg = re.split(r"[>=<!~\[;]", line)[0].strip()
                if pkg:
                    info["deps"].append(pkg)

        # Detect framework
        dep_lower = [d.lower() for d in info["deps"]]
        if "django" in dep_lower:
            info["framework"] = "Django"
        elif "flask" in dep_lower:
            info["framework"] = "Flask"
        elif "fastapi" in dep_lower:
            info["framework"] = "FastAPI"
        elif "tornado" in dep_lower:
            info["framework"] = "Tornado"
    except Exception:
        pass
    return info


def _parse_pyproject_toml(directory: Path) -> dict:
    """Parse pyproject.toml (basic text-based parsing)."""
    info = {"deps": [], "framework": "Python"}
    try:
        content = (directory / "pyproject.toml").read_text(encoding="utf-8")
        # Simple extraction - look for dependencies section
        in_deps = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped in ("dependencies = [", "[tool.poetry.dependencies]"):
                in_deps = True
                continue
            if in_deps:
                if stripped.startswith("]") or (stripped.startswith("[") and "=" not in stripped):
                    in_deps = False
                    continue
                # Extract package name from quoted strings
                match = re.search(r'"([^"><=!~]+)', stripped)
                if match:
                    pkg = match.group(1).strip()
                    if pkg and pkg != "python":
                        info["deps"].append(pkg)

        dep_lower = [d.lower() for d in info["deps"]]
        if "django" in dep_lower:
            info["framework"] = "Django"
        elif "flask" in dep_lower:
            info["framework"] = "Flask"
        elif "fastapi" in dep_lower:
            info["framework"] = "FastAPI"
    except Exception:
        pass
    return info


def _parse_go_mod(directory: Path) -> dict:
    """Parse go.mod."""
    info = {"deps": [], "framework": "Go"}
    try:
        content = (directory / "go.mod").read_text(encoding="utf-8")
        in_require = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("require ("):
                in_require = True
                continue
            if in_require:
                if stripped == ")":
                    in_require = False
                    continue
                parts = stripped.split()
                if parts:
                    info["deps"].append(parts[0])
            elif stripped.startswith("require "):
                parts = stripped.split()
                if len(parts) >= 2:
                    info["deps"].append(parts[1])

        dep_str = " ".join(info["deps"])
        if "gin-gonic" in dep_str:
            info["framework"] = "Gin"
        elif "echo" in dep_str:
            info["framework"] = "Echo"
        elif "fiber" in dep_str:
            info["framework"] = "Fiber"
    except Exception:
        pass
    return info


def _parse_cargo_toml(directory: Path) -> dict:
    """Parse Cargo.toml (basic text-based)."""
    info = {"deps": [], "framework": "Rust"}
    try:
        content = (directory / "Cargo.toml").read_text(encoding="utf-8")
        in_deps = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped in ("[dependencies]", "[dev-dependencies]"):
                in_deps = True
                continue
            if in_deps:
                if stripped.startswith("["):
                    in_deps = False
                    continue
                if "=" in stripped:
                    pkg = stripped.split("=")[0].strip()
                    if pkg:
                        info["deps"].append(pkg)

        dep_str = " ".join(info["deps"])
        if "actix-web" in dep_str:
            info["framework"] = "Actix Web"
        elif "axum" in dep_str:
            info["framework"] = "Axum"
        elif "rocket" in dep_str:
            info["framework"] = "Rocket"
        elif "tokio" in dep_str:
            info["framework"] = "Tokio (async)"
    except Exception:
        pass
    return info


_PARSERS = {
    "_parse_package_json":     _parse_package_json,
    "_parse_requirements_txt": _parse_requirements_txt,
    "_parse_pyproject_toml":   _parse_pyproject_toml,
    "_parse_go_mod":           _parse_go_mod,
    "_parse_cargo_toml":       _parse_cargo_toml,
}


def _generate_claudemd_from_scan(project_name: str, lang: str, framework: str,
                                  pkg: str, deps: list[str], scripts: list[str]) -> str:
    """Generate CLAUDE.md content from scan results."""
    cmds = PKG_COMMANDS.get(pkg, {})
    install_cmd = cmds.get("install", f"# TODO: install for {pkg}")
    dev_cmd     = cmds.get("dev", f"# TODO: dev for {pkg}")
    build_cmd   = cmds.get("build", f"# TODO: build for {pkg}")
    test_cmd    = cmds.get("test", f"# TODO: test for {pkg}")

    deps_section = ""
    if deps:
        dep_list = ", ".join(deps[:20])
        if len(deps) > 20:
            dep_list += f" (+{len(deps) - 20} more)"
        deps_section = f"\n## Key Dependencies\n\n{dep_list}\n"

    scripts_section = ""
    if scripts:
        script_lines = "\n".join(f"- `{s}`" for s in scripts[:15])
        scripts_section = f"\n## Available Scripts\n\n{script_lines}\n"

    return f"""# CLAUDE.md - {project_name}

Auto-generated by claude-toolkit project scanner.

## Project Overview

- **Language**: {lang}
- **Framework**: {framework}
- **Package Manager**: {pkg}
{deps_section}
## Common Commands

```bash
# Install dependencies
{install_cmd}

# Start development
{dev_cmd}

# Build
{build_cmd}

# Run tests
{test_cmd}
```
{scripts_section}
## Guidelines

- Follow existing project conventions
- Write tests for new features
- Keep changes focused and minimal
"""


def scan_project() -> None:
    """Scan current directory for project files and auto-generate CLAUDE.md."""
    directory = Path.cwd()
    project_name = directory.name

    clear()
    draw_header("项目扫描器", f"扫描目录: {directory}")
    console.print()

    # Scan for markers
    found = []
    for sig in PROJECT_SIGNATURES:
        marker_path = directory / sig["marker"]
        if marker_path.exists():
            found.append(sig)
            console.print(f"  {T.OK} 发现 [bold]{sig['marker']}[/] -> {sig['lang']}")
        else:
            console.print(f"  [{T.DIM}]  {sig['marker']} (未找到)[/]")

    console.print()

    if not found:
        show_err("未找到任何已知项目文件")
        wait_key()
        return

    # Parse the first (primary) match
    primary = found[0]
    info = {"deps": [], "scripts": [], "framework": primary["framework_hint"], "pkg": primary["pkg"]}

    if primary["parser"] and primary["parser"] in _PARSERS:
        info = _PARSERS[primary["parser"]](directory)

    lang = primary["lang"]
    framework = info.get("framework", primary["framework_hint"])
    pkg = info.get("pkg", primary["pkg"])
    deps = info.get("deps", [])
    scripts = info.get("scripts", [])

    # Display findings
    draw_divider("扫描结果")
    console.print()
    tbl = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    tbl.add_column("属性", style=f"bold {T.PRIMARY}")
    tbl.add_column("值")
    tbl.add_row("项目名称", project_name)
    tbl.add_row("语言", lang)
    tbl.add_row("框架", framework)
    tbl.add_row("包管理器", pkg)
    tbl.add_row("依赖数量", str(len(deps)))
    tbl.add_row("脚本数量", str(len(scripts)))
    console.print(tbl)
    console.print()

    if deps:
        console.print(f"  [{T.INFO}]主要依赖:[/] {', '.join(deps[:15])}")
        console.print()

    # Offer to generate
    choice = menu("操作", [
        "生成 CLAUDE.md",
        "返回",
    ], allow_esc=True)

    if choice != 0:
        return

    content = _generate_claudemd_from_scan(project_name, lang, framework, pkg, deps, scripts)
    target = directory / "CLAUDE.md"

    # Check if file exists
    if target.exists():
        console.print()
        show_err("CLAUDE.md 已存在")
        overwrite = menu("操作", ["覆盖", "取消"], allow_esc=True)
        if overwrite != 0:
            return

    try:
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        console.print()
        show_ok(f"已生成 CLAUDE.md ({len(content.splitlines())} 行)")
    except OSError as e:
        show_err(f"写入失败: {e}")

    wait_key()


# ═══════════════════════════════════════════════════════════════════════════════
# 5. session_mgr() - Session Manager
# ═══════════════════════════════════════════════════════════════════════════════

def session_mgr() -> None:
    """Manage Claude Code sessions: list, resume, copy IDs."""
    clear()
    draw_header("会话管理器", "查看和恢复历史会话")
    console.print()

    # Check if claude is available
    if not shutil.which("claude"):
        show_err("未找到 claude 命令，请确保已安装 Claude Code")
        wait_key()
        return

    console.print(f"  [{T.INFO}]正在获取会话列表...[/]")
    console.print()

    # Run claude --resume to get session list
    try:
        result = subprocess.run(
            ["claude", "--resume"],
            capture_output=True,
            text=True,
            timeout=15,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.TimeoutExpired:
        show_err("获取会话列表超时")
        wait_key()
        return
    except FileNotFoundError:
        show_err("无法执行 claude 命令")
        wait_key()
        return

    output = result.stdout.strip()
    if not output:
        # Try stderr in case the output goes there
        output = result.stderr.strip()

    if not output:
        show_err("没有找到历史会话")
        wait_key()
        return

    # Parse session lines
    sessions = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        sessions.append(line)

    if not sessions:
        show_err("会话列表为空")
        wait_key()
        return

    # Interactive session browser
    idx = 0
    page_size = max(console.height - 10, 5)

    while True:
        clear()
        draw_header("会话管理器", f"共 {len(sessions)} 个会话")
        console.print()

        # Show sessions
        visible = sessions[idx:idx + page_size]
        for j, sess in enumerate(visible):
            row_idx = idx + j
            marker = f"[bold {T.MENU_SEL}]❯[/]" if row_idx == idx else " "
            # Truncate long lines
            display = sess if len(sess) <= console.width - 10 else sess[:console.width - 13] + "..."
            console.print(f"  {marker} [{T.SECONDARY}]{row_idx + 1:>3}.[/] {display}")

        console.print()
        console.print(f"  [{T.DIM}]会话 {idx + 1}-{min(idx + page_size, len(sessions))}/{len(sessions)}[/]")
        draw_status_bar("↑↓ 滚动 | R 恢复选中会话 | C 复制 ID", "Esc 返回")

        key = read_key()
        if key == "esc":
            return
        elif key == "up":
            idx = max(0, idx - 1)
        elif key == "down":
            idx = min(max(0, len(sessions) - page_size), idx + 1)
        elif key == "pgup":
            idx = max(0, idx - page_size)
        elif key == "pgdn":
            idx = min(max(0, len(sessions) - page_size), idx + page_size)
        elif key in ("r", "R"):
            # Resume selected session
            selected = sessions[idx]
            # Try to extract session ID (usually a UUID)
            id_match = re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", selected)
            if id_match:
                session_id = id_match.group()
            else:
                session_id = selected.strip()

            clear()
            console.print(f"  [{T.INFO}]正在恢复会话: {session_id}[/]")
            console.print(f"  [{T.MUTED}]Ctrl+C 可中断[/]")
            console.print()
            try:
                subprocess.run(["claude", "--resume", session_id])
            except KeyboardInterrupt:
                console.print(f"\n  [{T.WARNING}]已中断[/]")
            wait_key()
        elif key in ("c", "C"):
            # Copy session ID to clipboard
            selected = sessions[idx]
            id_match = re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", selected)
            if id_match:
                session_id = id_match.group()
            else:
                session_id = selected.strip()

            try:
                # Try Windows clipboard
                subprocess.run(["clip"], input=session_id.encode(), check=True, timeout=5)
                show_ok(f"已复制到剪贴板: {session_id}")
            except Exception:
                # Fallback: just show it
                console.print(f"  [{T.INFO}]会话 ID: {session_id}[/]")
            wait_key()
        elif key.isdigit():
            n = int(key)
            if 1 <= n <= len(sessions):
                idx = min(n - 1, max(0, len(sessions) - page_size))


# ═══════════════════════════════════════════════════════════════════════════════
# 6. cost_tracker() - Cost Tracker
# ═══════════════════════════════════════════════════════════════════════════════

def cost_tracker() -> None:
    """Show token usage and cost information for the current session."""
    clear()
    draw_header("费用追踪器", "查看当前会话的 Token 用量和费用")
    console.print()

    # Check if claude is available
    if not shutil.which("claude"):
        show_err("未找到 claude 命令，请确保已安装 Claude Code")
        wait_key()
        return

    console.print(f"  [{T.INFO}]正在查询费用信息...[/]")
    console.print()

    # Method 1: Try running claude with /cost as input
    try:
        result = subprocess.run(
            ["claude", "-p", "/cost"],
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
            errors="replace",
        )
        output = result.stdout.strip()
        if result.stderr.strip():
            output = output + "\n" + result.stderr.strip() if output else result.stderr.strip()
    except subprocess.TimeoutExpired:
        show_err("查询超时")
        wait_key()
        return
    except FileNotFoundError:
        show_err("无法执行 claude 命令")
        wait_key()
        return

    if not output:
        # Fallback: show usage instructions
        console.print(Panel(
            f"""[{T.MUTED}]无法自动获取费用信息。

费用追踪有以下几种方式:

1. 在 Claude Code 交互会话中输入:
   [bold]/cost[/]

2. 使用 API 直接查看:
   访问 https://console.anthropic.com/settings/usage

3. 查看本地日志:
   日志位于 ~/.claude/ 目录下[/]""",
            title="费用查询方式",
            border_style=T.BORDER,
            padding=(1, 2),
        ))
        wait_key()
        return

    # Display output
    lines = output.split("\n")
    console.print(Panel(
        "\n".join(lines),
        title="Token 用量与费用",
        border_style=T.BORDER,
        padding=(1, 2),
    ))

    console.print()
    # Try to parse key metrics from output
    for line in lines:
        line_lower = line.lower()
        if "input" in line_lower and "token" in line_lower:
            console.print(f"  {T.ARROW} {line.strip()}")
        elif "output" in line_lower and "token" in line_lower:
            console.print(f"  {T.ARROW} {line.strip()}")
        elif "cost" in line_lower or "费" in line:
            console.print(f"  {T.ARROW} {line.strip()}")
        elif "total" in line_lower:
            console.print(f"  {T.ARROW} {line.strip()}")

    console.print()
    wait_key()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Hook 管理器
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HOOKS = [
    {'n':'自动格式化', 'd':'编辑后运行 Prettier/Black', 'e':'PostToolUse', 'm':'Write|Edit', 'h':'npx prettier --write $CLAUDE_FILE_PATH'},
    {'n':'自动 Lint',  'd':'编辑后运行 ESLint',         'e':'PostToolUse', 'm':'Write|Edit', 'h':'npx eslint $CLAUDE_FILE_PATH --fix'},
    {'n':'审计日志',   'd':'记录所有工具操作',           'e':'PreToolUse',  'm':'.*',         'h':'echo "$(date): $CLAUDE_TOOL_NAME" >> .claude/audit.log'},
    {'n':'安全守护',   'd':'阻止危险命令',               'e':'PreToolUse',  'm':'Bash',       'h':'if echo "$CLAUDE_TOOL_INPUT" | grep -q "rm -rf"; then exit 1; fi'},
    {'n':'自动测试',   'd':'代码变更后运行测试',         'e':'PostToolUse', 'm':'Write|Edit', 'h':'npm test 2>&1 | tail -20'},
    {'n':'系统通知',   'd':'需要关注时弹出通知',         'e':'Notification','m':'',           'h':'msg * /TIME:5 "Claude Code 需要关注"'},
]

def hook_mgr():
    items = [{'key':str(i+1),'icon':'🪝','label':h['n'],'desc':f"{h['d']}  |  {h['e']}"} for i,h in enumerate(HOOKS)]
    sel = menu(items, '🪝 Hook 管理器')
    if sel < 0: return
    hook = HOOKS[sel]
    scope_items = [{'key':'1','icon':'📁','label':'项目级','desc':'.claude/settings.json'},{'key':'2','icon':'🌐','label':'全局级','desc':'~/.claude/settings.json'}]
    scope = menu(scope_items, f'安装: {hook["n"]}')
    if scope < 0: return
    sp = Path.cwd()/'.claude'/'settings.json' if scope==0 else Path.home()/'.claude'/'settings.json'
    sp.parent.mkdir(parents=True, exist_ok=True)
    cfg = {}
    if sp.exists():
        try: cfg = json.loads(sp.read_text('utf-8'))
        except: pass
    if 'hooks' not in cfg: cfg['hooks'] = {}
    if hook['e'] not in cfg['hooks']: cfg['hooks'][hook['e']] = []
    cfg['hooks'][hook['e']].append({'matcher':hook['m'],'hooks':[hook['h']]})
    sp.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding='utf-8')
    show_ok('安装成功', f'Hook "{hook["n"]}" 已安装', str(sp))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 斜杠命令工厂
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CMD_TPL = [
    {'n':'代码审查','f':'review.md','d':'全面审查代码质量'},
    {'n':'测试生成','f':'test.md','d':'生成测试用例'},
    {'n':'代码重构','f':'refactor.md','d':'优化代码结构'},
    {'n':'部署检查','f':'deploy-check.md','d':'部署前检查清单'},
    {'n':'代码解释','f':'explain.md','d':'解释代码逻辑'},
    {'n':'错误调试','f':'debug.md','d':'诊断和修复错误'},
    {'n':'性能优化','f':'optimize.md','d':'性能分析优化'},
]

def cmd_factory():
    while True:
        items = [
            {'key':'1','icon':'📋','label':'浏览模板','desc':'查看可用的命令模板'},
            {'key':'2','icon':'📦','label':'一键安装','desc':'安装全部模板到 .claude/commands/'},
            {'key':'3','icon':'👀','label':'已安装','desc':'查看已安装的自定义命令'},
        ]
        sel = menu(items, '⚡ 斜杠命令工厂')
        if sel < 0: return
        if sel == 0:
            browse = [{'key':str(i+1),'icon':'📄','label':t['n'],'desc':t['d']} for i,t in enumerate(CMD_TPL)]
            menu(browse, '📋 命令模板')
        elif sel == 1:
            target = Path.cwd()/'.claude'/'commands'
            target.mkdir(parents=True, exist_ok=True)
            n = 0
            for t in CMD_TPL:
                src = ROOT/'templates'/'commands'/t['f']
                if src.exists(): shutil.copy2(src, target/t['f']); n += 1
            show_ok('安装完成', f'{n} 个命令已安装', str(target))
        elif sel == 2:
            lines = []
            for label,path in [('项目级',Path.cwd()/'.claude'/'commands'),('用户级',Path.home()/'.claude'/'commands')]:
                lines.append(Text(f"\n  [{label}] {path}", style=T.ACCENT))
                if path.exists():
                    for f in path.glob('*.md'):
                        first = f.read_text('utf-8').split('\n')[0][:50]
                        lines.append(Text(f"    /project:{f.stem}  {first}", style=T.DIM))
                else:
                    lines.append(Text("    (无)", style=T.DIM))
            scroll_view('已安装的命令', lines)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MCP 服务器管理
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MCP = [
    {'n':'GitHub','p':'@modelcontextprotocol/server-github','d':'仓库、Issue、PR','e':{'GITHUB_TOKEN':'<token>'}},
    {'n':'Filesystem','p':'@modelcontextprotocol/server-filesystem','d':'安全的文件读写','e':{}},
    {'n':'Brave Search','p':'@modelcontextprotocol/server-brave-search','d':'网络搜索','e':{'BRAVE_API_KEY':'<key>'}},
    {'n':'Puppeteer','p':'@modelcontextprotocol/server-puppeteer','d':'浏览器自动化','e':{}},
    {'n':'PostgreSQL','p':'@modelcontextprotocol/server-postgres','d':'数据库查询','e':{'POSTGRES_URL':'postgresql://...'}},
    {'n':'SQLite','p':'@modelcontextprotocol/server-sqlite','d':'SQLite 访问','e':{}},
    {'n':'Slack','p':'@modelcontextprotocol/server-slack','d':'Slack 集成','e':{'SLACK_BOT_TOKEN':'<token>'}},
    {'n':'Memory','p':'@modelcontextprotocol/server-memory','d':'持久化知识图谱','e':{}},
    {'n':'Fetch','p':'@modelcontextprotocol/server-fetch','d':'HTTP 请求','e':{}},
]

def mcp_mgr():
    while True:
        items = [
            {'key':'1','icon':'📋','label':'浏览服务器','desc':'查看可用的 MCP 服务器'},
            {'key':'2','icon':'📥','label':'安装服务器','desc':'配置到 settings.json'},
            {'key':'3','icon':'👀','label':'已配置','desc':'查看当前 MCP 配置'},
        ]
        sel = menu(items, '🔌 MCP 服务器管理')
        if sel < 0: return
        if sel == 0:
            browse = [{'key':str(i+1),'icon':'🔌','label':s['n'],'desc':f"{s['d']}  |  {s['p']}"} for i,s in enumerate(MCP)]
            menu(browse, '📋 MCP 服务器')
        elif sel == 1:
            srv_items = [{'key':str(i+1),'icon':'🔌','label':s['n'],'desc':s['d']} for i,s in enumerate(MCP)]
            si = menu(srv_items, '📥 选择服务器')
            if si < 0: continue
            srv = MCP[si]
            scope_items = [{'key':'1','icon':'📁','label':'项目级','desc':'.claude/settings.json'},{'key':'2','icon':'🌐','label':'全局级','desc':'~/.claude/settings.json'}]
            sc = menu(scope_items, f'安装: {srv["n"]}')
            if sc < 0: continue
            sp = Path.cwd()/'.claude'/'settings.json' if sc==0 else Path.home()/'.claude'/'settings.json'
            sp.parent.mkdir(parents=True, exist_ok=True)
            cfg = {}
            if sp.exists():
                try: cfg = json.loads(sp.read_text('utf-8'))
                except: pass
            if 'mcpServers' not in cfg: cfg['mcpServers'] = {}
            key = srv['n'].lower().replace(' ','-')
            cfg['mcpServers'][key] = {'command':'npx','args':['-y',srv['p']]}
            if srv['e']: cfg['mcpServers'][key]['env'] = dict(srv['e'])
            sp.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding='utf-8')
            show_ok('安装成功', f'MCP 服务器 "{srv["n"]}" 已配置', str(sp))
        elif sel == 2:
            lines = []
            for label,path in [('项目级',Path.cwd()/'.claude'/'settings.json'),('全局级',Path.home()/'.claude'/'settings.json')]:
                lines.append(Text(f"\n  [{label}] {path}", style=T.ACCENT))
                if path.exists():
                    try:
                        cfg = json.loads(path.read_text('utf-8'))
                        srvs = cfg.get('mcpServers', {})
                        if srvs:
                            for name,s in srvs.items():
                                lines.append(Text(f"    {name}: {s.get('command','?')} {' '.join(s.get('args',[]))}", style=T.LABEL))
                        else: lines.append(Text("    (无)", style=T.DIM))
                    except: lines.append(Text("    (解析错误)", style=T.ERR))
                else: lines.append(Text("    (文件不存在)", style=T.DIM))
            scroll_view('已配置的 MCP 服务器', lines)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 配置管理器
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def config_mgr():
    while True:
        items = [
            {'key':'1','icon':'👀','label':'查看配置','desc':'显示当前 settings.json'},
            {'key':'2','icon':'🆕','label':'初始化配置','desc':'创建项目 .claude/settings.json'},
            {'key':'3','icon':'🩺','label':'配置诊断','desc':'检查配置健康状态'},
        ]
        sel = menu(items, '⚙️ 配置管理器')
        if sel < 0: return
        if sel == 0:
            lines = []
            for label,path in [('项目级',Path.cwd()/'.claude'/'settings.json'),('全局级',Path.home()/'.claude'/'settings.json')]:
                lines.append(Text(f"\n  [{label}] {path}", style=T.ACCENT))
                if path.exists():
                    try:
                        cfg = json.loads(path.read_text('utf-8'))
                        for line in json.dumps(cfg, indent=2, ensure_ascii=False).split('\n'):
                            lines.append(Text(f"  {line}", style=T.DIM))
                    except: lines.append(Text("  (解析错误)", style=T.ERR))
                else: lines.append(Text("  (文件不存在)", style=T.DIM))
            scroll_view('当前配置', lines)
        elif sel == 1:
            sp = Path.cwd()/'.claude'/'settings.json'
            sp.parent.mkdir(parents=True, exist_ok=True)
            default = {'permissions':{'allow':['Read'],'deny':[]},'hooks':{'PostToolUse':[{'matcher':'Write|Edit','hooks':['npx prettier --write $CLAUDE_FILE_PATH 2>/dev/null']}]}}
            sp.write_text(json.dumps(default, indent=2), encoding='utf-8')
            show_ok('初始化成功', '配置已创建', str(sp))
        elif sel == 2:
            checks = [
                ('Claude Code CLI', shutil.which('claude') is not None),
                ('Node.js / npx', shutil.which('npx') is not None),
                ('Git', shutil.which('git') is not None),
                ('ANTHROPIC_API_KEY', bool(os.environ.get('ANTHROPIC_API_KEY'))),
                ('项目 .claude 目录', (Path.cwd()/'.claude').exists()),
                ('项目 settings.json', (Path.cwd()/'.claude'/'settings.json').exists()),
                ('项目 CLAUDE.md', (Path.cwd()/'CLAUDE.md').exists()),
                ('全局 settings.json', (Path.home()/'.claude'/'settings.json').exists()),
            ]
            rows = [(n, Text('✔ 通过',style=T.OK) if ok else Text('✖ 未通过',style=T.ERR)) for n,ok in checks]
            show_table('🩺 配置诊断', ['检查项','状态'], rows)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Prompt 模板库
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def prompt_lib():
    pp = ROOT/'data'/'prompts.json'
    if not pp.exists():
        show_err('prompts.json 未找到'); return
    data = json.loads(pp.read_text('utf-8'))
    cats = data.get('categories', [])
    while True:
        items = [{'key':str(i+1),'icon':'📚','label':c['name'],'desc':f"{len(c['prompts'])} 个模板"} for i,c in enumerate(cats)]
        items.append({'key':'s','icon':'🔍','label':'搜索模板','desc':'在所有模板中搜索'})
        sel = menu(items, '📚 Prompt 模板库')
        if sel < 0: return
        if sel == len(cats):
            clear()
            draw_header()
            console.print()
            console.print(f"  [{T.PROMPT}]输入关键词:[/] ", end='')
            kw = input().strip().lower()
            if not kw: continue
            results = []
            for cat in cats:
                for p in cat['prompts']:
                    if kw in p['title'].lower() or kw in p['prompt'].lower():
                        results.append(Text(f"  [{cat['name']}] {p['title']}", style=T.LABEL))
                        results.append(Text(f"    {p['prompt'].split(chr(10))[0][:70]}...", style=T.DIM))
            if results: scroll_view(f'搜索结果: {kw}', results)
            else: show_err(f'未找到匹配 "{kw}" 的模板')
            continue
        cat = cats[sel]
        pi = [{'key':str(i+1),'icon':'📝','label':p['title'],'desc':p['prompt'].split('\n')[0][:50]} for i,p in enumerate(cat['prompts'])]
        ps = menu(pi, f'📚 {cat["name"]}')
        if ps < 0: continue
        prompt = cat['prompts'][ps]
        lines = prompt['prompt'].split('\n')
        while True:
            clear()
            draw_header()
            console.print()
            console.print(Align.center(Text(f"  ═══  {prompt['title']}  ═══  ", style=T.ACCENT)))
            console.print()
            for i,line in enumerate(lines):
                console.print(f"  [{T.DIM}]{i+1:>3}[/] │ {line}")
            console.print()
            draw_status_bar(prompt['title'], '[C] 复制  Esc 返回', f'{len(lines)} 行')
            kt,k = read_key()
            if kt=='esc' or (kt=='char' and k=='q'): break
            if kt=='char' and k=='c':
                try:
                    subprocess.run(['clip'], input=prompt['prompt'].encode('utf-8'), check=True)
                    show_ok('已复制', '提示词已复制到剪贴板')
                except: show_err('复制失败')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 最佳实践指南
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GUIDE = [
    ('📝 CLAUDE.md 最佳实践', [
        'CLAUDE.md 是项目记忆文件，每次会话开始时自动读取。',
        '','[bold bright_cyan]核心原则:[/]','  1. 简洁 - Claude 每次都读，冗长浪费 Token',
        '  2. 使用祈使句 - "始终做 X"、"永远不要做 Y"','  3. 分层管理 - 根目录放全局规则，子目录放模块规则',
        '  4. 持续更新 - 当作活文档维护',
        '','[bold bright_cyan]推荐结构:[/]','  - 项目概述(一句话)',
        '  - 技术栈(语言/框架/包管理/测试/Lint)','  - 代码规范(命名/格式/风格)',
        '  - 构建命令(install/dev/build/test/lint)','  - 架构说明(目录结构/关键文件)',
        '  - 常见陷阱(容易踩的坑)',
    ]),
    ('💡 提示词工程技巧', [
        '[bold bright_cyan]写出更好的 Claude Code 指令:[/]','',
        '1. 具体明确','  ✗ "修复这个 bug"','  ✔ "在 src/auth.ts 的 login 函数中，密码为空时应返回 400"',
        '','2. 指向文件和行号','  ✔ "修改 src/components/Form.tsx 第 45 行的验证逻辑"',
        '','3. 描述结果而非步骤','  ✔ "创建一个支持搜索、分页、排序的 React 组件"',
        '','4. 拆分复杂任务 - 分多轮对话，每次专注一个方面',
        '5. 用 CLAUDE.md 存放常驻指令',
        '6. 善用管道: git diff | claude "review"','7. 适时使用 /compact 压缩上下文',
        '8. 复杂任务用计划模式(Shift+Tab)',
    ]),
    ('🔄 常用工作流', [
        '[bold bright_cyan]日常开发:[/]','  1. cd 到项目根目录  2. claude 启动会话',
        '  3. /init 初始化 CLAUDE.md  4. 自然语言描述任务','  5. /compact 压缩上下文  6. /review 审查变更',
        '  7. claude commit 生成提交信息',
        '','[bold bright_cyan]代码审查:[/]  git diff | claude "review these changes"',
        '[bold bright_cyan]CI/CD:[/]  claude -p "review" --output-format json',
        '[bold bright_cyan]调试:[/]  cat error.log | claude "diagnose"',
        '[bold bright_cyan]重构:[/]  Shift+Tab -> 描述目标 -> 确认 -> 执行',
    ]),
    ('🔐 权限模式详解', [
        '[bold bright_green]建议模式(最安全):[/] Claude 提出修改，你确认后才执行',
        '[bold bright_yellow]自动模式:[/] Claude 自动执行常用操作，危险操作仍需确认',
        '[bold bright_blue]计划模式:[/] Claude 先展示计划，确认后执行',
        '','切换: Shift+Tab',
    ]),
    ('🪝 Hook 实用场景', [
        '自动格式化: PostToolUse -> npx prettier --write $FILE',
        '自动 Lint:   PostToolUse -> npx eslint $FILE --fix',
        '审计日志:     PreToolUse  -> echo "$(date): $TOOL" >> log',
        '安全守护:     PreToolUse  -> 阻止 rm -rf、force push',
        '系统通知:     Notification -> msg * "需要关注"',
    ]),
    ('🔌 MCP 服务器指南', [
        'MCP 是 Anthropic 的开放协议，让 Claude 连接外部工具。',
        '','[bold bright_cyan]热门服务器:[/]',
        '  - GitHub (仓库/Issue/PR)  - Filesystem (文件操作)',
        '  - Brave Search (搜索)  - Puppeteer (浏览器)',
        '  - PostgreSQL/SQLite (数据库)  - Slack/Discord (协作)',
        '','配置: .claude/settings.json -> mcpServers',
    ]),
    ('🚀 CI/CD 最佳实践', [
        '[bold bright_cyan]GitHub Actions 示例:[/]',
        '  name: CI Pipeline',
        '  on: [push, pull_request]',
        '  jobs:',
        '    build:',
        '      runs-on: ubuntu-latest',
        '      steps:',
        '        - uses: actions/checkout@v4',
        '        - uses: actions/setup-node@v4',
        '          with: { node-version: 20 }',
        '        - run: npm ci',
        '        - run: npm test',
        '        - run: npm run build',
        '',
        '[bold bright_cyan]GitLab CI 示例:[/]',
        '  stages: [build, test, deploy]',
        '  build:',
        '    stage: build',
        '    image: node:20-alpine',
        '    script:',
        '      - npm ci',
        '      - npm run build',
        '    artifacts:',
        '      paths: [dist/]',
        '  test:',
        '    stage: test',
        '    script: [npm test]',
        '  deploy:',
        '    stage: deploy',
        '    only: [main]',
        '    script: [npm run deploy]',
        '',
        '[bold bright_cyan]关键实践:[/]',
        '  1. 缓存 node_modules / pip cache 加速构建',
        '  2. 并行运行测试和 Lint',
        '  3. 使用 matrix 策略测试多版本',
        '  4. 部署前自动运行安全扫描',
        '  5. 保护 main 分支，要求 PR 审批',
        '  6. 自动生成 changelog 和版本号',
        '  7. 使用 secrets 管理敏感信息',
    ]),
    ('🔒 安全编码指南', [
        '[bold bright_cyan]OWASP Top 10 关键项:[/]',
        '  1. 注入 (SQL/NoSQL/OS) - 始终使用参数化查询',
        '  2. 失效的认证 - 实施 MFA、会话管理',
        '  3. 敏感数据暴露 - 加密传输和存储',
        '  4. XML 外部实体 (XXE) - 禁用外部实体解析',
        '  5. 失效的访问控制 - 最小权限原则',
        '  6. 安全配置错误 - 定期审计配置',
        '  7. XSS - 对输出进行编码和转义',
        '  8. 不安全的反序列化 - 避免不可信数据反序列化',
        '  9. 使用含漏洞的组件 - 定期更新依赖',
        '  10. 日志和监控不足 - 记录安全事件',
        '',
        '[bold bright_cyan]输入验证:[/]',
        '  - 白名单验证优于黑名单',
        '  - 在服务端验证所有输入',
        '  - 使用类型约束和长度限制',
        '  - 对文件上传进行类型和大小检查',
        '',
        '[bold bright_cyan]Secrets 管理:[/]',
        '  - 永远不要硬编码密码/密钥',
        '  - 使用环境变量或 Vault/AWS Secrets Manager',
        '  - .env 文件加入 .gitignore',
        '  - 定期轮换 API 密钥',
        '  - 使用 pre-commit hook 检测泄露',
    ]),
    ('📊 性能优化技巧', [
        '[bold bright_cyan]Profiling 工具:[/]',
        '  - Node.js: clinic.js / 0x / Chrome DevTools',
        '  - Python: cProfile / py-spy / line_profiler',
        '  - Go: pprof / go tool trace',
        '  - Rust: cargo-flamegraph / perf',
        '',
        '[bold bright_cyan]缓存策略:[/]',
        '  1. 浏览器缓存 - Cache-Control / ETag',
        '  2. CDN 缓存 - 静态资源分发',
        '  3. 应用缓存 - Redis / Memcached',
        '  4. 数据库查询缓存 - 结果集缓存',
        '  5. 计算缓存 - memoize / lru_cache',
        '',
        '[bold bright_cyan]数据库优化:[/]',
        '  - 为高频查询字段添加索引',
        '  - 避免 N+1 查询，使用 JOIN 或预加载',
        '  - 分页查询避免 OFFSET，改用游标',
        '  - 使用 EXPLAIN ANALYZE 分析慢查询',
        '  - 读写分离、连接池复用',
        '  - 批量操作替代逐条处理',
        '',
        '[bold bright_cyan]通用技巧:[/]',
        '  - 懒加载和代码分割',
        '  - 图片压缩和 WebP 格式',
        '  - Gzip/Brotli 压缩响应',
        '  - 异步处理耗时任务',
    ]),
    ('🌐 更多资源', [
        f'[bold bright_magenta]访问 HYPERVOID 博客获取更多内容:[/]',
        '  [bold]https://hypervoid.top[/]',
        '',
        '  - 最新 AI 编程工具评测',
        '  - Claude Code 深度使用技巧',
        '  - 开发者效率提升指南',
        '  - 技术教程和最佳实践',
    ]),
]

def guide():
    while True:
        items = [{'key':str(i+1),'icon':'📖','label':t,'desc':f"{len(l)} 行"} for i,(t,l) in enumerate(GUIDE)]
        sel = menu(items, '🎓 最佳实践指南')
        if sel < 0: return
        title,lines = GUIDE[sel]
        styled = []
        for line in lines:
            if isinstance(line,str) and '[' in line:
                styled.append(Text.from_markup(f"  {line}"))
            else:
                styled.append(Text(f"  {line}"))
        scroll_view(title, styled)