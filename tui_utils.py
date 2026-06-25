"""
HYPERVOID 共享工具模块 - 跨平台 TUI 组件
所有模块导入此模块获取通用功能
"""
import os, sys, json, platform
from pathlib import Path
from datetime import datetime

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.rule import Rule
from rich.live import Live
from rich import box

# ── 平台检测 ──────────────────────────────────────────────
IS_WINDOWS = platform.system() == 'Windows'

if IS_WINDOWS:
    import msvcrt
else:
    import tty, termios

# ── 控制台 ────────────────────────────────────────────────
console = Console()

# ── 数据目录 ──────────────────────────────────────────────
DATA_DIR = Path.home() / '.hypervoid' / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 主题色彩  ·  宇宙星空
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class T:
    """统一主题色常量 - 宇宙星空配色"""
    # 主色调
    CYAN    = 'bold bright_cyan'
    MAG     = 'bold bright_magenta'
    YEL     = 'bold bright_yellow'
    GRN     = 'bold bright_green'
    RED     = 'bold bright_red'
    BLU     = 'bold bright_blue'
    WHT     = 'bold bright_white'

    # 语义色
    ACCENT  = 'bold bright_cyan'
    DIM     = 'dim bright_white'
    OK      = 'bold bright_green'
    WARN    = 'bold bright_yellow'
    ERR     = 'bold bright_red'

    # UI 组件色
    KEY     = 'bold bright_cyan'
    LABEL   = 'bold bright_white'
    DESC    = 'dim bright_white'
    BORDER  = 'dim bright_white'
    BOX     = 'bright_cyan'
    SEL_BG  = 'black on dark_blue'

    # 头尾栏 - 无背景，仅用线条分隔
    HEADER  = 'dim bright_white'
    STATUS  = 'dim bright_white'

    # Logo
    LOGO1   = 'bold bright_cyan'
    LOGO2   = 'bold bright_white'

    # 装饰
    STAR    = 'dim bright_cyan'
    PROMPT  = 'bold bright_cyan'

    # 选中项
    SEL_KEY   = 'bold bright_cyan'
    SEL_LABEL = 'bold bright_white'
    SEL_DESC  = 'bright_cyan'
    SEL_BAR   = 'bright_cyan'


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 跨平台键盘输入
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def read_key():
    """跨平台单按键输入"""
    if IS_WINDOWS:
        return _read_key_windows()
    return _read_key_unix()


def _read_key_windows():
    ch = msvcrt.getch()
    if ch == b'\r': return ('enter', '')
    if ch == b'\x1b': return ('esc', '')
    if ch == b'\x03': raise KeyboardInterrupt
    if ch in (b'\x00', b'\xe0'):
        ch2 = msvcrt.getch()
        m = {b'H':'up',b'P':'down',b'K':'left',b'M':'right',
             b'S':'del',b'G':'home',b'O':'end',b'I':'pgup',b'Q':'pgdn'}
        return ('nav', m.get(ch2, ''))
    return ('char', ch.decode('utf-8', errors='ignore').lower())


def _read_key_unix():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch in ('\r', '\n'): return ('enter', '')
        if ch == '\x1b':
            ch2 = sys.stdin.read(1)
            if ch2 == '[':
                ch3 = sys.stdin.read(1)
                m = {'A':'up','B':'down','C':'right','D':'left',
                     '5':'pgup','6':'pgdn','H':'home','F':'end'}
                if ch3 in m: return ('nav', m[ch3])
                if ch3 == '3': sys.stdin.read(1); return ('nav', 'del')
            return ('esc', '')
        if ch == '\x03': raise KeyboardInterrupt
        return ('char', ch.lower())
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def wait_key():
    read_key()


def clear():
    os.system('cls' if IS_WINDOWS else 'clear')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 数据管理
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def load_json(name, default=None):
    p = DATA_DIR / name
    if p.exists():
        try: return json.loads(p.read_text('utf-8'))
        except: pass
    return default if default is not None else {}


def save_json(name, data):
    (DATA_DIR / name).write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def now_str():
    return datetime.now().strftime('%Y-%m-%d %H:%M')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 项目信息
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def get_project_info():
    import subprocess
    cwd = Path.cwd()
    info = {'dir': cwd.name, 'path': str(cwd)}
    try:
        info['git'] = subprocess.check_output(
            ['git', 'branch', '--show-current'],
            stderr=subprocess.DEVNULL, text=True).strip()
    except: info['git'] = ''
    info['claude_md'] = (cwd / 'CLAUDE.md').exists()
    info['settings'] = (cwd / '.claude' / 'settings.json').exists()
    cmd_dir = cwd / '.claude' / 'commands'
    info['commands'] = len(list(cmd_dir.glob('*.md'))) if cmd_dir.exists() else 0
    info['api_key'] = bool(os.environ.get('ANTHROPIC_API_KEY'))
    return info


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 绘制组件
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def draw_header():
    w = console.width
    now = datetime.now().strftime('%H:%M')
    # 宇宙风格头栏 - 星星点缀 + 渐变
    # ◆ ━━━ ✦ ━━━ HYPERVOID ━━━━━━━━━ hypervoid.top  20:30 ━━━ ✦ ━━━ ◆
    left = f'◆ ━━━ ✦ ━━━ HYPERVOID ━━━'
    right = f'━━━ hypervoid.top  {now} ━━━ ✦ ━━━ ◆'
    mid_fill = '━' * max(1, w - len(left) - len(right) - 2)
    console.print(f'[bright_cyan]{left}[dim]{mid_fill}[/dim][bright_cyan]{right}[bright_cyan]')


def draw_logo():
    console.print()
    console.print()  # 与头栏拉开距离
    w = console.width

    # ── Hero 区域 - Impossible 风格实心 Logo ──
    art = [
        '██  ██ ██╗   ██╗██████╗ ███████╗██████╗ ██╗   ██╗ ██████╗ ██╗██████╗',
        '██████ ╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗██║   ██║██╔═══██╗██║██╔══██╗',
        '██  ██  ╚████╔╝ ██████╔╝█████╗  ██████╔╝██║   ██║██║   ██║██║██║  ██║',
        '██████   ╚██╔╝  ██╔═══╝ ██╔══╝  ██╔══██╗╚██╗ ██╔╝██║   ██║██║██║  ██║',
        '██  ██    ██║   ██║     ███████╗██║  ██║ ╚████╔╝ ╚██████╔╝██║██████╔╝',
        '╚╝  ╚╝    ╚═╝   ╚═╝     ╚══════╝╚═╝  ╚═╝  ╚═══╝   ╚═════╝ ╚═╝╚═════╝',
    ]

    # 渐变色: HYPER=青, VOID=白
    # R 结束位置约在第 40 字符处，V 从第 41 开始
    split_pos = 40

    for line in art:
        t = Text()
        t.append(line[:split_pos], style='bold bright_cyan')
        t.append(line[split_pos:], style='bold bright_white')
        console.print(Align.center(t))

    # 副标题
    console.print()
    console.print(Align.center(Text('·  个人开发工作站  ·  hypervoid.top  ·', style=T.DIM)))
    console.print()


def draw_stars():
    import random
    w = console.width
    patterns = [
        '✦ · • ✧ . ·  ✦  . • ✧ · .  ✦ · • ✧ . ·',
        '· ✦  .  • ✧ ·  .  ✦  · • ✧  .  ✦ · • ✧',
        '✧ · ✦  •  . ✧ · ✦  •  . ✧ · ✦  •  . ✧',
    ]
    stars = random.choice(patterns)
    offset = random.randint(0, 8)
    line = (' ' * offset + stars)[:w]
    console.print(f'[{T.STAR}]{line}[/]')


def draw_divider(char='─', style='dim'):
    console.print(Rule(characters=char, style=style))


def draw_status_bar(left='', center='', right=''):
    w = console.width
    # 宇宙风格底栏
    left_s = left[:20] if left else ''
    right_s = right[:20] if right else ''
    if left_s and right_s:
        left_part = f'◆ ━━━ ✦ ━━━ {left_s} ━━━'
        right_part = f'━━━ {right_s} ━━━ ✦ ━━━ ◆'
        mid_fill = '━' * max(1, w - len(left_part) - len(right_part) - 2)
        console.print(f'[bright_cyan]{left_part}[dim]{mid_fill}[/dim][bright_cyan]{right_part}[/bright_cyan]')
    elif left_s:
        left_part = f'◆ ━━━ ✦ ━━━ {left_s} ━━━'
        right_part = '━━━ ✦ ━━━ ◆'
        mid_fill = '━' * max(1, w - len(left_part) - len(right_part) - 2)
        console.print(f'[bright_cyan]{left_part}[dim]{mid_fill}[/dim][bright_cyan]{right_part}[/bright_cyan]')
    else:
        console.print(f'[dim]{"━" * w}[/dim]')


def draw_project_info():
    info = get_project_info()
    proj = f'📁 {info["dir"]}'
    if info.get('git'):
        proj += f' ({info["git"]})'
    md = '✔ CLAUDE.md' if info['claude_md'] else '✖ CLAUDE.md'
    md_s = T.OK if info['claude_md'] else T.ERR
    st = '✔ settings' if info['settings'] else '✖ settings'
    st_s = T.OK if info['settings'] else T.ERR
    api = 'API ✔' if info['api_key'] else 'API ✖'
    api_s = T.OK if info['api_key'] else T.ERR

    line = Text()
    line.append(f'  {proj}', style=T.WHT)
    line.append(f'  │  ', style=T.DIM)
    line.append(md, style=md_s)
    line.append(f'  ', style=T.DIM)
    line.append(st, style=st_s)
    line.append(f'  │  ', style=T.DIM)
    line.append(api, style=api_s)
    console.print(line)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 交互菜单  ·  Live 显示
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _build_menu_content(items, sel, title, footer):
    parts = []
    w = console.width
    now = datetime.now().strftime('%H:%M')

    # ── 宇宙风格头栏 ──
    left = f'◆ ━━━ ✦ ━━━ HYPERVOID ━━━'
    right = f'━━━ hypervoid.top  {now} ━━━ ✦ ━━━ ◆'
    mid_fill = '━' * max(1, w - len(left) - len(right) - 2)
    parts.append(Text(f'{left}{mid_fill} {right}', style='bright_cyan'))

    # ── Hero 区域 - Impossible 风格实心 Logo ──
    art = [
        '██  ██ ██╗   ██╗██████╗ ███████╗██████╗ ██╗   ██╗ ██████╗ ██╗██████╗',
        '██████ ╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗██║   ██║██╔═══██╗██║██╔══██╗',
        '██  ██  ╚████╔╝ ██████╔╝█████╗  ██████╔╝██║   ██║██║   ██║██║██║  ██║',
        '██████   ╚██╔╝  ██╔═══╝ ██╔══╝  ██╔══██╗╚██╗ ██╔╝██║   ██║██║██║  ██║',
        '██  ██    ██║   ██║     ███████╗██║  ██║ ╚████╔╝ ╚██████╔╝██║██████╔╝',
        '╚╝  ╚╝    ╚═╝   ╚═╝     ╚══════╝╚═╝  ╚═╝  ╚═══╝   ╚═════╝ ╚═╝╚═════╝',
    ]

    split_pos = 40
    parts.append(Text(''))  # 与头栏拉开距离
    for line in art:
        t = Text()
        t.append(line[:split_pos], style='bold bright_cyan')
        t.append(line[split_pos:], style='bold bright_white')
        parts.append(Align.center(t))

    parts.append(Text(''))
    parts.append(Align.center(Text('·  个人开发工作站  ·  hypervoid.top  ·', style=T.DIM)))
    parts.append(Text(''))

    # ── 项目信息 - 单行紧凑 ──
    info = get_project_info()
    proj = f'📁 {info["dir"]}'
    if info.get('git'):
        proj += f' ({info["git"]})'
    md = '✔ CLAUDE.md' if info['claude_md'] else '✖ CLAUDE.md'
    md_s = T.OK if info['claude_md'] else T.ERR
    st = '✔ settings' if info['settings'] else '✖ settings'
    st_s = T.OK if info['settings'] else T.ERR
    api = 'API ✔' if info['api_key'] else 'API ✖'
    api_s = T.OK if info['api_key'] else T.ERR

    info_line = Text()
    info_line.append(f'  {proj}', style=T.WHT)
    info_line.append(f'  │  ', style=T.DIM)
    info_line.append(md, style=md_s)
    info_line.append(f'  ', style=T.DIM)
    info_line.append(st, style=st_s)
    info_line.append(f'  │  ', style=T.DIM)
    info_line.append(api, style=api_s)
    parts.append(info_line)

    # ── 菜单标题 - 带装饰 ──
    parts.append(Text(''))
    parts.append(Text(f'  ── {title} ──', style=T.ACCENT))
    parts.append(Text(''))

    # ── 菜单项 ──
    for i, item in enumerate(items):
        is_sel = (i == sel)
        icon = item.get('icon', '')
        key = item['key']
        label = item['label']
        desc = item.get('desc', '')

        if is_sel:
            # 选中项 - 高亮显示，带装饰
            sel_line = Text()
            sel_line.append(f'  ▸ [{key}]  ', style='bold bright_cyan')
            sel_line.append(f'{icon} {label}', style='bold bright_white')
            sel_line.append(f'  {desc}', style='bright_cyan')
            parts.append(sel_line)
        else:
            # 未选中项 - 简洁显示
            line = Text()
            line.append(f'    [{key}]  ', style='dim bright_white')
            line.append(f'{icon} {label}', style='bright_white')
            line.append(f'  {desc}', style='dim bright_white')
            parts.append(line)

    # ── 宇宙风格底栏 ──
    parts.append(Text(''))
    left = '◆ ━━━ ✦ ━━━ HYPERVOID ━━━'
    right = '━━━ hypervoid.top ━━━ ✦ ━━━ ◆'
    mid_fill = '━' * max(1, w - len(left) - len(right) - 2)
    parts.append(Text(f'{left}{mid_fill} {right}', style='bright_cyan'))

    return Group(*parts)


def menu(items, title='菜单', footer='↑↓ Enter 选择  Q 退出'):
    """交互式菜单  ·  Live 显示消除闪烁"""
    sel = 0
    content = _build_menu_content(items, sel, title, footer)
    with Live(content, console=console, refresh_per_second=30, screen=True) as live:
        while True:
            kt, k = read_key()
            if kt == 'esc' or (kt == 'char' and k == 'q'):
                return -1
            if kt == 'enter':
                return sel
            if kt == 'nav':
                if k == 'up': sel = (sel - 1) % len(items)
                if k == 'down': sel = (sel + 1) % len(items)
            if kt == 'char' and k in [str(i+1) for i in range(len(items))]:
                return int(k) - 1
            live.update(_build_menu_content(items, sel, title, footer))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 滚动视图  ·  Live 显示
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _build_scroll_content(title, lines, pos, page, footer):
    parts = []
    w = console.width
    now = datetime.now().strftime('%H:%M')

    # 宇宙风格头栏
    left = f'◆ ━━━ ✦ ━━━ HYPERVOID ━━━'
    right = f'━━━ hypervoid.top  {now} ━━━ ✦ ━━━ ◆'
    mid_fill = '━' * max(1, w - len(left) - len(right) - 2)
    parts.append(Text(f'{left}{mid_fill} {right}', style='bright_cyan'))

    # 标题
    parts.append(Text(f'  ◆ {title}', style=T.ACCENT))
    parts.append(Text(''))

    # 内容
    visible = lines[pos:pos + page]
    for line in visible:
        if isinstance(line, Text):
            parts.append(Text('  ') + line)
        else:
            parts.append(Text(f'  {line}'))

    # 进度条
    total = len(lines)
    if total > page:
        pct = int(pos / max(1, total - page) * 100)
        bar_len = 40
        filled = int(bar_len * pos / max(1, total - page))
        bar = '█' * filled + '░' * (bar_len - filled)
        info = f'{pos+1}-{min(pos+page, total)}/{total}'
        parts.append(Text(''))
        parts.append(Align.center(Text(f'  {bar}  {pct}%  {info}', style=T.DIM)))

    parts.append(Text(''))

    # 宇宙风格底栏
    left = f'◆ ━━━ ✦ ━━━ {title[:20]} ━━━'
    right = '━━━ hypervoid.top ━━━ ✦ ━━━ ◆'
    mid_fill = '━' * max(1, w - len(left) - len(right) - 2)
    parts.append(Text(f'{left}{mid_fill} {right}', style='bright_cyan'))
    return Group(*parts)


def scroll_view(title, lines, footer='↑↓ 滚动  PgUp/PgDn 翻页  Esc 返回'):
    """可滚动文本视图  ·  Live 显示"""
    pos = 0
    page = max(console.height - 12, 8)
    total = len(lines)
    content = _build_scroll_content(title, lines, pos, page, footer)
    with Live(content, console=console, refresh_per_second=30, screen=True) as live:
        while True:
            kt, k = read_key()
            if kt == 'esc' or (kt == 'char' and k == 'q'): return
            if kt == 'nav':
                new_pos = pos
                if k == 'up' and pos > 0: new_pos = pos - 1
                if k == 'down' and pos < max(0, total - page): new_pos = pos + 1
                if k == 'pgup': new_pos = max(0, pos - page)
                if k == 'pgdn': new_pos = min(max(0, total - page), pos + page)
                if new_pos != pos:
                    pos = new_pos
                    live.update(_build_scroll_content(title, lines, pos, page, footer))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 表格 / 提示框
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def show_table(title, headers, rows, footer='按任意键返回'):
    clear()
    draw_header()
    console.print(Align.center(Text(f"  ·  {title}  ·  ", style=T.ACCENT)))
    console.print()
    table = Table(box=box.ROUNDED, border_style=T.BOX, show_lines=False, pad_edge=True, padding=(0, 1))
    for h in headers:
        table.add_column(h, style=T.LABEL)
    for row in rows:
        table.add_row(*row)
    console.print(Align.center(table))
    console.print()
    draw_status_bar(title, footer, '')
    wait_key()


def show_ok(title, msg, detail=''):
    clear()
    console.print()
    content = Text(f'\n  ✔  {msg}\n', style=T.OK)
    if detail:
        content.append(f'\n  {detail}\n', style=T.DIM)
    console.print(Align.center(
        Panel(content, title=f'[bold bright_green]{title}[/]',
              border_style='bright_green', width=min(66, console.width - 4),
              padding=(1, 2), box=box.DOUBLE)))
    console.print()
    draw_status_bar(title, '按任意键继续...', '')
    wait_key()


def show_err(msg):
    console.print(f"\n  [{T.ERR}]✖  {msg}[/]")
    console.print(f"  [{T.DIM}]按任意键继续...[/]")
    wait_key()
