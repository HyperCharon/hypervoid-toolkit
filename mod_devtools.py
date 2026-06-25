# -*- coding: utf-8 -*-
"""Developer Tools Module - Self-contained TUI developer utilities using rich."""

import os, json, shutil, subprocess, time, platform, socket
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.rule import Rule
from rich import box
import msvcrt

console = Console()


class T:
    CYAN = 'bold bright_cyan'; MAG = 'bold bright_magenta'; YEL = 'bold bright_yellow'
    GRN = 'bold bright_green'; RED = 'bold bright_red'; WHT = 'bold bright_white'
    ACCENT = 'bold bright_magenta'; DIM = 'dim bright_white'; OK = 'bold bright_green'
    WARN = 'bold bright_yellow'; ERR = 'bold bright_red'; KEY = 'bold bright_yellow'
    LABEL = 'bold bright_white'; DESC = 'dim bright_white'; BORDER = 'bright_magenta'
    BOX = 'bright_magenta'; SEL_BG = 'on dark_cyan'


def read_key():
    ch = msvcrt.getch()
    if ch == b'\r': return ('enter', '')
    if ch == b'\x1b': return ('esc', '')
    if ch == b'\x03': raise KeyboardInterrupt
    if ch in (b'\x00', b'\xe0'):
        ch2 = msvcrt.getch()
        m = {b'H': 'up', b'P': 'down', b'K': 'left', b'M': 'right', b'I': 'pgup', b'Q': 'pgdn'}
        return ('nav', m.get(ch2, ''))
    return ('char', ch.decode('utf-8', errors='ignore').lower())


def clear(): os.system('cls')


def wait_key(): read_key()


# ---------------------------------------------------------------------------
# Scrollable view helper
# ---------------------------------------------------------------------------

def scroll_view(title, lines, colorize_fn=None):
    """Display lines in a scrollable view with arrow keys and PgUp/PgDn."""
    offset = 0
    page_size = 20

    while True:
        clear()
        console.print(Align.center(Text(f"  ═══  {title}  ═══  ", style=T.ACCENT)))
        console.print()

        visible = lines[offset:offset + page_size]
        for line in visible:
            if colorize_fn:
                console.print(f"  {colorize_fn(line)}")
            else:
                console.print(f"  {line}")

        total = len(lines)
        if total == 0:
            console.print(f"  [{T.DIM}]（空）[/]")
        console.print()
        console.print(
            f"  [{T.DIM}]行 {offset + 1}-{min(offset + page_size, total)} / {total}"
            f"  |  ↑↓/PgUp/PgDn 翻页  |  Esc 返回[/]"
        )

        key, val = read_key()
        if key == 'esc':
            return
        elif key == 'nav':
            if val == 'up':
                offset = max(0, offset - 1)
            elif val == 'down':
                offset = min(max(0, total - page_size), offset + 1)
            elif val == 'pgup':
                offset = max(0, offset - page_size)
            elif val == 'pgdn':
                offset = min(max(0, total - page_size), offset + page_size)


def draw_header(title):
    console.print(Align.center(Text(f"  ═══  {title}  ═══  ", style=T.ACCENT)))
    console.print()


# ---------------------------------------------------------------------------
# 1. git_tools() - Git 可视化工具
# ---------------------------------------------------------------------------

def _run_git(args):
    """Run a git command and return output lines."""
    try:
        result = subprocess.run(
            ['git'] + args,
            capture_output=True, text=True, timeout=15,
            encoding='utf-8', errors='replace'
        )
        output = result.stdout.strip()
        if result.returncode != 0 and result.stderr.strip():
            output = result.stderr.strip()
        return output.splitlines() if output else ['（无输出）']
    except FileNotFoundError:
        return ['[错误] 未找到 git，请确认已安装 Git']
    except subprocess.TimeoutExpired:
        return ['[错误] 命令超时']
    except Exception as e:
        return [f'[错误] {e}']


def _git_log_colorize(line):
    """Colorize git log --oneline output: hash green, rest yellow."""
    parts = line.split(' ', 1)
    if len(parts) == 2:
        return f"[{T.GRN}]{parts[0]}[/] [{T.YEL}]{parts[1]}[/]"
    return f"[{T.GRN}]{line}[/]"


def git_tools():
    """Git visualization tools sub-menu."""
    options = [
        ('1', 'git status', ['status']),
        ('2', 'git log (--oneline -20)', ['log', '--oneline', '-20']),
        ('3', 'git diff', ['diff']),
        ('4', 'git diff --staged', ['diff', '--staged']),
        ('5', 'git branch (-a)', ['branch', '-a']),
        ('6', 'git stash list', ['stash', 'list']),
        ('7', 'git remote -v', ['remote', '-v']),
        ('8', 'git tag', ['tag']),
    ]
    sel = 0

    while True:
        clear()
        draw_header("Git 可视化工具")
        console.print()

        for i, (key, label, _) in enumerate(options):
            marker = '▸' if i == sel else ' '
            style = T.SEL_BG + ' ' + T.WHT if i == sel else T.DIM
            console.print(f"  {marker} [{style}]{key}. {label}[/]")

        console.print()
        console.print(f"  [{T.DIM}]↑↓ 选择  |  Enter 执行  |  Esc 返回[/]")

        key, val = read_key()
        if key == 'esc':
            return
        elif key == 'nav':
            if val == 'up':
                sel = (sel - 1) % len(options)
            elif val == 'down':
                sel = (sel + 1) % len(options)
        elif key == 'enter':
            _, label, args = options[sel]
            lines = _run_git(args)
            colorize = _git_log_colorize if args == ['log', '--oneline', '-20'] else None
            scroll_view(label, lines, colorize_fn=colorize)


# ---------------------------------------------------------------------------
# 2. file_browser() - 文件浏览器
# ---------------------------------------------------------------------------

def _human_size(size_bytes):
    """Convert bytes to human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}" if unit != 'B' else f"{size_bytes} B"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def _get_dir_entries(path):
    """Get directory entries sorted: dirs first, then files."""
    entries = []
    try:
        for item in sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            try:
                stat = item.stat()
                entries.append({
                    'name': item.name,
                    'path': item,
                    'is_dir': item.is_dir(),
                    'size': stat.st_size if not item.is_dir() else 0,
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
                })
            except (PermissionError, OSError):
                entries.append({
                    'name': item.name,
                    'path': item,
                    'is_dir': item.is_dir(),
                    'size': 0,
                    'modified': '无法访问',
                })
    except PermissionError:
        pass
    return entries


def _preview_file(filepath, max_lines=20):
    """Preview first N lines of a text file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = []
            for i, line in enumerate(f):
                if i >= max_lines:
                    lines.append(f"  ... (超过 {max_lines} 行，已截断)")
                    break
                lines.append(line.rstrip('\n\r'))
            return lines if lines else ['（空文件）']
    except Exception as e:
        return [f'[错误] 无法读取: {e}']


def file_browser():
    """File browser with navigation and preview."""
    current = Path.cwd()

    while True:
        clear()
        draw_header("文件浏览器")
        console.print(f"  [{T.LABEL}]路径:[/] [{T.CYAN}]{current}[/]")
        console.print()

        entries = [{'name': '..', 'path': current.parent, 'is_dir': True, 'size': 0, 'modified': ''}]
        entries.extend(_get_dir_entries(current))

        sel = 0
        scroll_offset = 0
        page_size = 20

        while True:
            clear()
            draw_header("文件浏览器")
            console.print(f"  [{T.LABEL}]路径:[/] [{T.CYAN}]{current}[/]")
            console.print()

            # Adjust scroll to keep selection visible
            if sel < scroll_offset:
                scroll_offset = sel
            if sel >= scroll_offset + page_size:
                scroll_offset = sel - page_size + 1

            visible = entries[scroll_offset:scroll_offset + page_size]

            table = Table(box=box.SIMPLE, show_header=True, header_style=T.YEL, border_style=T.BOX)
            table.add_column("", width=3)
            table.add_column("名称", min_width=30)
            table.add_column("类型", width=8)
            table.add_column("大小", width=12, justify="right")
            table.add_column("修改时间", width=18)

            for i, entry in enumerate(visible):
                idx = scroll_offset + i
                marker = '▸' if idx == sel else ' '
                name_style = T.SEL_BG if idx == sel else ''

                if entry['name'] == '..':
                    typ = '[目录]'
                    name_str = f"[{T.CYAN}]..[/]"
                elif entry['is_dir']:
                    typ = '[目录]'
                    name_str = f"[{T.CYAN}]{entry['name']}[/]"
                else:
                    typ = '[文件]'
                    name_str = entry['name']

                size_str = _human_size(entry['size']) if not entry['is_dir'] else '-'
                table.add_row(marker, name_str, typ, size_str, entry['modified'])

            console.print(table)
            console.print()
            console.print(
                f"  [{T.DIM}]共 {len(entries)} 项"
                f"  |  ↑↓ 导航  |  Enter 打开/预览  |  Esc 返回[/]"
            )

            key, val = read_key()
            if key == 'esc':
                return
            elif key == 'nav':
                if val == 'up':
                    sel = max(0, sel - 1)
                elif val == 'down':
                    sel = min(len(entries) - 1, sel + 1)
                elif val == 'pgup':
                    sel = max(0, sel - page_size)
                elif val == 'pgdn':
                    sel = min(len(entries) - 1, sel + page_size)
            elif key == 'enter':
                entry = entries[sel]
                if entry['is_dir']:
                    try:
                        current = entry['path'].resolve()
                        sel = 0
                        scroll_offset = 0
                        break  # re-list directory
                    except (PermissionError, OSError):
                        pass
                else:
                    # Preview file
                    lines = _preview_file(entry['path'])
                    scroll_view(f"预览: {entry['name']}", lines)


# ---------------------------------------------------------------------------
# 3. env_vars() - 环境变量管理
# ---------------------------------------------------------------------------

def env_vars():
    """Environment variable viewer and manager."""
    important_vars = [
        'ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'GITHUB_TOKEN',
        'GITHUB_PAT', 'PATH', 'HOME', 'USERPROFILE',
        'APPDATA', 'LOCALAPPDATA', 'TEMP', 'TMP',
        'PYTHONPATH', 'NODE_ENV', 'COMPUTERNAME', 'USERNAME',
        'SHELL', 'TERM', 'LANG',
    ]

    while True:
        clear()
        draw_header("环境变量管理")
        console.print()

        table = Table(box=box.ROUNDED, show_header=True, header_style=T.YEL, border_style=T.BOX)
        table.add_column("变量名", min_width=25, style=T.LABEL)
        table.add_column("状态", width=10, justify="center")
        table.add_column("值（截断）", min_width=40, style=T.DIM)

        for var in important_vars:
            val = os.environ.get(var, '')
            if val:
                # Mask sensitive keys
                display = val
                if 'KEY' in var or 'TOKEN' in var or 'PAT' in var:
                    if len(val) > 8:
                        display = val[:4] + '*' * (len(val) - 8) + val[-4:]
                    else:
                        display = '****'
                elif len(display) > 60:
                    display = display[:57] + '...'
                status = f"[{T.OK}]已设置[/]"
            else:
                display = '-'
                status = f"[{T.DIM}]未设置[/]"
            table.add_row(var, status, display)

        console.print(table)
        console.print()

        # Options
        console.print(f"  [{T.KEY}]1[/]  设置 ANTHROPIC_API_KEY")
        console.print(f"  [{T.KEY}]2[/]  设置 GITHUB_TOKEN")
        console.print(f"  [{T.KEY}]3[/]  搜索环境变量")
        console.print()
        console.print(f"  [{T.DIM}]输入数字选择  |  Esc 返回[/]")

        key, val = read_key()
        if key == 'esc':
            return
        elif key == 'char':
            if val == '1':
                _set_env_var('ANTHROPIC_API_KEY')
            elif val == '2':
                _set_env_var('GITHUB_TOKEN')
            elif val == '3':
                _search_env_vars()


def _set_env_var(var_name):
    """Prompt user to set an environment variable (current session only)."""
    clear()
    draw_header(f"设置 {var_name}")
    console.print(f"  [{T.DIM}]输入值（将仅对当前会话生效）:[/]")
    console.print()

    # Simple line input
    import sys
    console.print(f"  {var_name} = ", end='')
    sys.stdout.flush()
    value = input()
    if value:
        os.environ[var_name] = value
        console.print(f"\n  [{T.OK}]已设置 {var_name}[/]")
    else:
        console.print(f"\n  [{T.WARN}]已取消[/]")
    time.sleep(1)


def _search_env_vars():
    """Search and display all environment variables."""
    clear()
    draw_header("所有环境变量")

    lines = []
    for key in sorted(os.environ.keys()):
        val = os.environ[key]
        if len(val) > 80:
            val = val[:77] + '...'
        lines.append(f"{key} = {val}")

    scroll_view("所有环境变量", lines)


# ---------------------------------------------------------------------------
# 4. port_checker() - 端口检查器
# ---------------------------------------------------------------------------

def port_checker():
    """Check listening ports using netstat."""
    sel = 0
    filter_port = ''
    ports_data = []

    while True:
        clear()
        draw_header("端口检查器")

        if not ports_data:
            console.print(f"  [{T.DIM}]正在扫描端口...[/]")
            ports_data = _get_listening_ports()

        # Filter
        if filter_port:
            filtered = [p for p in ports_data if filter_port in str(p['port'])]
        else:
            filtered = ports_data

        if not filtered:
            console.print(f"  [{T.DIM}]无匹配结果[/]")
        else:
            table = Table(box=box.ROUNDED, show_header=True, header_style=T.YEL, border_style=T.BOX)
            table.add_column("", width=3)
            table.add_column("协议", width=6)
            table.add_column("本地地址", min_width=25)
            table.add_column("端口", width=8, style=T.GRN)
            table.add_column("状态", width=12)
            table.add_column("PID", width=8, style=T.YEL)
            table.add_column("进程", min_width=15)

            for i, p in enumerate(filtered):
                marker = '▸' if i == sel else ' '
                table.add_row(
                    marker, p['proto'], p['local_addr'],
                    str(p['port']), p['state'], str(p['pid']), p['process']
                )

            console.print(table)

        console.print()
        console.print(
            f"  [{T.KEY}]f[/] 筛选端口  [{T.KEY}]r[/] 刷新  [{T.DIM}]|  Esc 返回[/]"
        )
        if filter_port:
            console.print(f"  [{T.DIM}]当前筛选: {filter_port}  (按 c 清除)[/]")

        key, val = read_key()
        if key == 'esc':
            return
        elif key == 'char':
            if val == 'f':
                filter_port = _simple_input("输入端口号筛选: ")
                sel = 0
            elif val == 'r':
                ports_data = []
                sel = 0
            elif val == 'c':
                filter_port = ''
                sel = 0
        elif key == 'nav':
            if val == 'up':
                sel = max(0, sel - 1)
            elif val == 'down':
                sel = min(len(filtered) - 1, sel + 1)


def _simple_input(prompt):
    """Simple single-line input."""
    import sys
    console.print(f"  {prompt}", end='')
    sys.stdout.flush()
    return input().strip()


def _get_listening_ports():
    """Parse netstat output to get listening ports."""
    try:
        result = subprocess.run(
            ['netstat', '-ano'],
            capture_output=True, text=True, timeout=10,
            encoding='utf-8', errors='replace'
        )
        lines = result.stdout.splitlines()
    except Exception as e:
        return [{'proto': '-', 'local_addr': str(e), 'port': 0, 'state': '-', 'pid': 0, 'process': '-'}]

    ports = []
    for line in lines:
        parts = line.split()
        if len(parts) >= 5 and parts[0] in ('TCP', 'UDP') and parts[3] == 'LISTENING':
            proto = parts[0]
            local = parts[1]
            pid = parts[4]
            # Parse address and port
            if ':' in local:
                addr, port_str = local.rsplit(':', 1)
                try:
                    port_num = int(port_str)
                except ValueError:
                    continue
            else:
                continue
            # Get process name
            process_name = _get_process_name(pid)
            ports.append({
                'proto': proto,
                'local_addr': addr,
                'port': port_num,
                'state': parts[3],
                'pid': pid,
                'process': process_name,
            })
        elif len(parts) >= 4 and parts[0] == 'UDP':
            proto = parts[0]
            local = parts[1]
            pid = parts[3] if len(parts) > 3 else '-'
            if ':' in local:
                addr, port_str = local.rsplit(':', 1)
                try:
                    port_num = int(port_str)
                except ValueError:
                    continue
            else:
                continue
            process_name = _get_process_name(pid)
            ports.append({
                'proto': proto,
                'local_addr': addr,
                'port': port_num,
                'state': '-',
                'pid': pid,
                'process': process_name,
            })

    return sorted(ports, key=lambda p: p['port'])


def _get_process_name(pid):
    """Get process name from PID."""
    try:
        result = subprocess.run(
            ['tasklist', '/FI', f'PID eq {pid}', '/FO', 'CSV', '/NH'],
            capture_output=True, text=True, timeout=5,
            encoding='utf-8', errors='replace'
        )
        line = result.stdout.strip()
        if line and ',' in line:
            return line.split(',')[0].strip('"')
    except Exception:
        pass
    return '-'


# ---------------------------------------------------------------------------
# 5. docker_mgr() - Docker 管理
# ---------------------------------------------------------------------------

def _docker_available():
    """Check if Docker is available."""
    try:
        result = subprocess.run(
            ['docker', 'info'],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _run_docker(args):
    """Run a docker command and return output lines."""
    try:
        result = subprocess.run(
            ['docker'] + args,
            capture_output=True, text=True, timeout=30,
            encoding='utf-8', errors='replace'
        )
        output = result.stdout.strip()
        if result.returncode != 0 and result.stderr.strip():
            output = result.stderr.strip()
        return output.splitlines() if output else ['（无输出）']
    except FileNotFoundError:
        return ['[错误] 未找到 docker']
    except subprocess.TimeoutExpired:
        return ['[错误] 命令超时']
    except Exception as e:
        return [f'[错误] {e}']


def docker_mgr():
    """Docker management sub-menu."""
    if not _docker_available():
        clear()
        draw_header("Docker 管理")
        console.print(f"  [{T.ERR}]Docker 未运行或未安装[/]")
        console.print(f"\n  [{T.DIM}]按任意键返回...[/]")
        read_key()
        return

    options = [
        ('1', '容器列表 (docker ps -a)', ['ps', '-a']),
        ('2', '镜像列表 (docker images)', ['images']),
        ('3', '数据卷列表 (docker volume ls)', ['volume', 'ls']),
        ('4', 'Docker 信息 (docker info)', ['info']),
    ]
    sel = 0

    while True:
        clear()
        draw_header("Docker 管理")
        console.print(f"  [{T.OK}]Docker 已就绪[/]")
        console.print()

        for i, (key, label, _) in enumerate(options):
            marker = '▸' if i == sel else ' '
            style = T.SEL_BG + ' ' + T.WHT if i == sel else T.DIM
            console.print(f"  {marker} [{style}]{key}. {label}[/]")

        console.print()
        console.print(f"  [{T.DIM}]↑↓ 选择  |  Enter 执行  |  Esc 返回[/]")

        key, val = read_key()
        if key == 'esc':
            return
        elif key == 'nav':
            if val == 'up':
                sel = (sel - 1) % len(options)
            elif val == 'down':
                sel = (sel + 1) % len(options)
        elif key == 'enter':
            _, label, args = options[sel]
            clear()
            draw_header(label.split('(')[0].strip())
            console.print(f"  [{T.DIM}]正在执行...[/]")
            lines = _run_docker(args)
            scroll_view(label, lines)


# ---------------------------------------------------------------------------
# 6. json_editor() - JSON 编辑器
# ---------------------------------------------------------------------------

def json_editor():
    """JSON file editor with validation and formatting."""
    while True:
        clear()
        draw_header("JSON 编辑器")
        console.print()

        console.print(f"  [{T.KEY}]1[/]  打开 JSON 文件")
        console.print(f"  [{T.KEY}]2[/]  从剪贴板粘贴 JSON")
        console.print(f"  [{T.KEY}]3[/]  验证 JSON 字符串")
        console.print()
        console.print(f"  [{T.DIM}]输入数字选择  |  Esc 返回[/]")

        key, val = read_key()
        if key == 'esc':
            return
        elif key == 'char':
            if val == '1':
                _json_open_file()
            elif val == '2':
                _json_from_input()
            elif val == '3':
                _json_validate_input()


def _json_open_file():
    """Open and display a JSON file."""
    clear()
    draw_header("打开 JSON 文件")
    filepath = _simple_input("输入文件路径: ")
    if not filepath:
        return

    path = Path(filepath)
    if not path.exists():
        console.print(f"\n  [{T.ERR}]文件不存在: {filepath}[/]")
        time.sleep(1.5)
        return

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        console.print(f"\n  [{T.ERR}]JSON 解析错误: {e}[/]")
        time.sleep(2)
        return
    except Exception as e:
        console.print(f"\n  [{T.ERR}]读取错误: {e}[/]")
        time.sleep(1.5)
        return

    formatted = json.dumps(data, indent=2, ensure_ascii=False)
    lines = formatted.splitlines()

    while True:
        clear()
        draw_header(f"JSON: {path.name}")
        console.print(f"  [{T.DIM}]有效 JSON  |  {len(lines)} 行[/]")
        console.print()

        # Show first 30 lines as preview
        preview = lines[:30]
        for line in preview:
            console.print(f"  {line}")
        if len(lines) > 30:
            console.print(f"\n  [{T.DIM}]... 共 {len(lines)} 行 ...[/]")

        console.print()
        console.print(f"  [{T.KEY}]1[/]  格式化并保存  [{T.KEY}]2[/]  完整滚动查看  [{T.KEY}]3[/]  压缩并保存")
        console.print(f"  [{T.DIM}]输入数字选择  |  Esc 返回[/]")

        key, val = read_key()
        if key == 'esc':
            return
        elif key == 'char':
            if val == '1':
                try:
                    with open(path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    console.print(f"\n  [{T.OK}]已格式化并保存[/]")
                    time.sleep(1)
                except Exception as e:
                    console.print(f"\n  [{T.ERR}]保存失败: {e}[/]")
                    time.sleep(1.5)
            elif val == '2':
                scroll_view(f"JSON: {path.name}", lines)
            elif val == '3':
                try:
                    compressed = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(compressed)
                    console.print(f"\n  [{T.OK}]已压缩并保存[/]")
                    time.sleep(1)
                except Exception as e:
                    console.print(f"\n  [{T.ERR}]保存失败: {e}[/]")
                    time.sleep(1.5)


def _json_from_input():
    """Parse JSON from user input."""
    clear()
    draw_header("输入 JSON")
    console.print(f"  [{T.DIM}]输入 JSON 字符串（单行）:[/]")
    json_str = _simple_input(">>> ")
    if not json_str:
        return

    try:
        data = json.loads(json_str)
        formatted = json.dumps(data, indent=2, ensure_ascii=False)
        lines = formatted.splitlines()
        scroll_view("解析结果", lines)
    except json.JSONDecodeError as e:
        console.print(f"\n  [{T.ERR}]JSON 解析错误: {e}[/]")
        time.sleep(2)


def _json_validate_input():
    """Validate a JSON string."""
    clear()
    draw_header("验证 JSON")
    console.print(f"  [{T.DIM}]输入 JSON 字符串:[/]")
    json_str = _simple_input(">>> ")
    if not json_str:
        return

    try:
        json.loads(json_str)
        console.print(f"\n  [{T.OK}]✓ 有效的 JSON[/]")
    except json.JSONDecodeError as e:
        console.print(f"\n  [{T.ERR}]✗ 无效的 JSON: {e}[/]")

    console.print(f"\n  [{T.DIM}]按任意键返回...[/]")
    read_key()


# ---------------------------------------------------------------------------
# 7. sys_info() - 系统信息
# ---------------------------------------------------------------------------

def sys_info():
    """Display system information."""
    while True:
        clear()
        draw_header("系统信息")
        console.print()

        # OS Info
        table = Table(box=box.ROUNDED, show_header=False, border_style=T.BOX, padding=(0, 2))
        table.add_column("属性", style=T.LABEL, min_width=18)
        table.add_column("值", style=T.DIM, min_width=50)

        table.add_row("操作系统", f"{platform.system()} {platform.release()} {platform.version()}")
        table.add_row("架构", f"{platform.machine()} ({platform.architecture()[0]})")
        table.add_row("计算机名", platform.node())
        table.add_row("用户名", os.environ.get('USERNAME', os.environ.get('USER', '-')))
        table.add_row("处理器", platform.processor() or '-')
        table.add_row("CPU 核心数", str(os.cpu_count() or '-'))
        table.add_row("Python", platform.python_version())

        # Pip version
        try:
            pip_result = subprocess.run(
                ['pip', '--version'], capture_output=True, text=True, timeout=5,
                encoding='utf-8', errors='replace'
            )
            pip_ver = pip_result.stdout.strip().split()[1] if pip_result.returncode == 0 else '-'
        except Exception:
            pip_ver = '-'
        table.add_row("Pip", pip_ver)

        # Network hostname
        try:
            hostname = socket.gethostname()
        except Exception:
            hostname = '-'
        table.add_row("网络主机名", hostname)

        # Current user
        try:
            import getpass
            current_user = getpass.getuser()
        except Exception:
            current_user = os.environ.get('USERNAME', os.environ.get('USER', '-'))
        table.add_row("当前用户", current_user)

        table.add_row("工作目录", str(Path.cwd()))

        # Uptime / boot time
        try:
            import ctypes
            tick = ctypes.windll.kernel32.GetTickCount64()
            uptime_sec = tick // 1000
            days = uptime_sec // 86400
            hours = (uptime_sec % 86400) // 3600
            mins = (uptime_sec % 3600) // 60
            table.add_row("系统运行时间", f"{days} 天 {hours} 小时 {mins} 分钟")
        except Exception:
            pass

        console.print(table)
        console.print()

        # Disk usage
        console.print(f"  [{T.YEL}]磁盘使用情况:[/]")
        disk_table = Table(box=box.SIMPLE, show_header=True, header_style=T.YEL, border_style=T.BOX)
        disk_table.add_column("驱动器", width=10)
        disk_table.add_column("总容量", width=15, justify="right")
        disk_table.add_column("已用", width=15, justify="right")
        disk_table.add_column("可用", width=15, justify="right")
        disk_table.add_column("使用率", width=10, justify="right")

        for drive in 'CDEFGH':
            drive_path = f"{drive}:\\"
            try:
                usage = shutil.disk_usage(drive_path)
                total = _human_size(usage.total)
                used = _human_size(usage.used)
                free = _human_size(usage.free)
                pct = f"{usage.used / usage.total * 100:.1f}%"
                disk_table.add_row(drive_path, total, used, free, pct)
            except OSError:
                pass

        console.print(disk_table)
        console.print()

        # Memory info via systeminfo (cached for performance)
        console.print(f"  [{T.KEY}]m[/]  查看内存详情  [{T.KEY}]e[/]  导出系统信息")
        console.print(f"  [{T.DIM}]按 Esc 返回[/]")

        key, val = read_key()
        if key == 'esc':
            return
        elif key == 'char':
            if val == 'm':
                _show_memory_info()
            elif val == 'e':
                _export_sys_info()


def _show_memory_info():
    """Show detailed memory information."""
    clear()
    draw_header("内存详情")
    try:
        result = subprocess.run(
            ['systeminfo'],
            capture_output=True, text=True, timeout=15,
            encoding='utf-8', errors='replace'
        )
        lines = result.stdout.splitlines()
        mem_lines = [l for l in lines if '内存' in l or 'Memory' in l.lower() or '物理' in l]
        if mem_lines:
            for line in mem_lines:
                console.print(f"  {line.strip()}")
        else:
            # Fallback
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ('dwLength', ctypes.c_ulong),
                    ('dwMemoryLoad', ctypes.c_ulong),
                    ('ullTotalPhys', ctypes.c_ulonglong),
                    ('ullAvailPhys', ctypes.c_ulonglong),
                    ('ullTotalPageFile', ctypes.c_ulonglong),
                    ('ullAvailPageFile', ctypes.c_ulonglong),
                    ('ullTotalVirtual', ctypes.c_ulonglong),
                    ('ullAvailVirtual', ctypes.c_ulonglong),
                    ('ullAvailExtendedVirtual', ctypes.c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(stat)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            console.print(f"  内存使用率: {stat.dwMemoryLoad}%")
            console.print(f"  总物理内存: {_human_size(stat.ullTotalPhys)}")
            console.print(f"  可用物理内存: {_human_size(stat.ullAvailPhys)}")
            console.print(f"  总虚拟内存: {_human_size(stat.ullTotalPageFile)}")
            console.print(f"  可用虚拟内存: {_human_size(stat.ullAvailPageFile)}")
    except Exception as e:
        console.print(f"  [{T.ERR}]获取内存信息失败: {e}[/]")

    console.print(f"\n  [{T.DIM}]按任意键返回...[/]")
    read_key()


def _export_sys_info():
    """Export system info to a JSON file."""
    info = {
        'timestamp': datetime.now().isoformat(),
        'os': platform.system(),
        'os_release': platform.release(),
        'os_version': platform.version(),
        'architecture': platform.machine(),
        'processor': platform.processor(),
        'hostname': platform.node(),
        'username': os.environ.get('USERNAME', ''),
        'python_version': platform.python_version(),
        'cwd': str(Path.cwd()),
        'disk_usage': {},
    }

    for drive in 'CDEFGH':
        try:
            usage = shutil.disk_usage(f"{drive}:\\")
            info['disk_usage'][f'{drive}:'] = {
                'total': usage.total,
                'used': usage.used,
                'free': usage.free,
            }
        except OSError:
            pass

    filename = f"sys_info_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=2, ensure_ascii=False)
        console.print(f"\n  [{T.OK}]已导出到: {filename}[/]")
    except Exception as e:
        console.print(f"\n  [{T.ERR}]导出失败: {e}[/]")

    time.sleep(1.5)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main_menu():
    """Developer tools main menu."""
    options = [
        ('1', 'Git 可视化工具', git_tools),
        ('2', '文件浏览器', file_browser),
        ('3', '环境变量管理', env_vars),
        ('4', '端口检查器', port_checker),
        ('5', 'Docker 管理', docker_mgr),
        ('6', 'JSON 编辑器', json_editor),
        ('7', '系统信息', sys_info),
    ]
    sel = 0

    while True:
        clear()
        draw_header("HYPERVOID 开发者工具")
        console.print()

        for i, (key, label, _) in enumerate(options):
            marker = '▸' if i == sel else ' '
            style = T.SEL_BG + ' ' + T.WHT if i == sel else T.DIM
            console.print(f"  {marker} [{style}]{key}. {label}[/]")

        console.print()
        console.print(f"  [{T.DIM}]↑↓ 选择  |  Enter 打开  |  Esc 退出[/]")

        key, val = read_key()
        if key == 'esc':
            return
        elif key == 'nav':
            if val == 'up':
                sel = (sel - 1) % len(options)
            elif val == 'down':
                sel = (sel + 1) % len(options)
        elif key == 'enter':
            _, _, func = options[sel]
            try:
                func()
            except KeyboardInterrupt:
                pass
            except Exception as e:
                clear()
                console.print(f"\n  [{T.ERR}]错误: {e}[/]")
                console.print(f"\n  [{T.DIM}]按任意键返回...[/]")
                read_key()


if __name__ == '__main__':
    try:
        main_menu()
    except KeyboardInterrupt:
        clear()
        console.print(f"\n  [{T.DIM}]已退出[/]\n")
