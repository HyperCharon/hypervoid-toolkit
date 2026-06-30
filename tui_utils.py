"""
HYPERVOID 共享 TUI 模块 - 跨平台终端组件

风格定位：深空科技工作站（v2 留白版）
  · 学习 mimo 的"选中行整块高亮"与"紧凑信息密度"
  · 不照搬 mimo 的输入框/子智能体等不存在功能
  · 配色：冷青 + 星云紫 + 星尘灰 + 暗金橙，低饱和、高留白
  · 布局突出"个人开发工作站"：项目状态 badge、功能热键、严格对齐菜单
  · 星空背景稀疏克制，中央大面积留白
"""
import os, sys, json, platform, re, random
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
from rich.cells import cell_len

IS_WINDOWS = platform.system() == 'Windows'

if IS_WINDOWS:
    import msvcrt
else:
    import tty, termios


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HYPERVOID 主题色：v2 低饱和深空科技风
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 256 色 palette，终端兼容性好；减少颜色数量，统一语义
CYAN        = 'color(80)'      # 冷青：主边框、标题、主强调
CYAN_DIM    = 'color(73)'      # 深青：次级边框/分隔线
CYAN_BRIGHT = 'color(87)'      # 亮青：高亮提示
ORANGE      = 'color(179)'     # 暗金橙：热键、重要提示、强调
ORANGE_BRIGHT = 'color(208)'   # 太阳橙：选中态背景、强强调
AMBER       = 'color(180)'     # 暖琥珀：计数、次要强调
PURPLE      = 'color(147)'     # 星云紫：分组、装饰
PURPLE_BRIGHT = 'color(141)'   # 亮紫：选中态背景（高对比）
GREY        = 'color(245)'     # 星尘灰：正文
DIM_GREY    = 'color(243)'     # 暗灰：次要/禁用信息
DARK        = 'color(234)'     # 深空面板背景
DARKER      = 'color(233)'     # 更黑背景
WHITE       = 'white'

# ANSI 备用（历史代码/外部模块可能直接引用）
RESET       = '\x1b[0m'
DIM         = '\x1b[2m'
GREEN       = '\x1b[32m'
YELLOW      = '\x1b[33m'
RED         = '\x1b[31m'
BLUE        = '\x1b[34m'
MAGENTA     = '\x1b[35m'
BOLD        = '\x1b[1m'
REVERSE     = '\x1b[7m'
BRIGHT_GREEN = '\x1b[92m'
BRIGHT_RED   = '\x1b[91m'
BRIGHT_CYAN  = '\x1b[96m'
BRIGHT_YELLOW = '\x1b[93m'


class T:
    """兼容历史导入的主题色别名（已映射到 HYPERVOID v2 风格）"""
    RESET = RESET; DIM = DIM; CYAN = CYAN; GREEN = GREEN; YELLOW = YELLOW
    RED = RED; BLUE = BLUE; MAGENTA = MAGENTA; BOLD = BOLD; REVERSE = REVERSE
    BRIGHT_GREEN = BRIGHT_GREEN; BRIGHT_RED = BRIGHT_RED; BRIGHT_CYAN = BRIGHT_CYAN
    BRIGHT_YELLOW = BRIGHT_YELLOW
    BORDER = CYAN; ACCENT = CYAN; KEY = ORANGE; LABEL = 'bold'
    DESC = DIM_GREY; OK = GREEN; WARN = YELLOW; ERR = RED; BOX = CYAN
    STAR = DIM_GREY; HEADER = CYAN; STATUS = DIM_GREY; PROMPT = ORANGE
    LOGO1 = CYAN; LOGO2 = GREY
    SEL_BG = 'color(141)'
    SEL_KEY = 'bold white on ' + SEL_BG
    SEL_LABEL = 'bold white on ' + SEL_BG
    SEL_DESC = 'white on ' + SEL_BG


# 控制台：256 色 + 禁用旧版 Windows 转义兼容，由 Rich 自行处理
console = Console(color_system='256', legacy_windows=False)

DATA_DIR = Path.home() / '.hypervoid' / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 宽度与 ANSI 辅助
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _strip_ansi(s):
    return re.sub(r'\x1b\[[0-9;]*m', '', s)


def _char_width(ch):
    cp = ord(ch)
    if 0x1100 <= cp <= 0x115f or cp in (0x2329, 0x232a) or \
       (0x2e80 <= cp <= 0xa4cf and cp != 0x303f) or \
       (0xac00 <= cp <= 0xd7a3) or \
       (0xf900 <= cp <= 0xfaff) or \
       (0xfe10 <= cp <= 0xfe19) or \
       (0xfe30 <= cp <= 0xfe6f) or \
       (0xff00 <= cp <= 0xff60) or \
       (0xffe0 <= cp <= 0xffe6) or \
       (0x1f300 <= cp <= 0x1faf6) or \
       (0x20000 <= cp <= 0x3fffd):
        return 2
    return 1


def _string_width(s):
    return sum(_char_width(c) for c in _strip_ansi(s))


def _text_width(t):
    return cell_len(t.plain)


def _truncate(s, width):
    if width <= 0: return ''
    if _string_width(s) <= width: return s
    if width <= 3: return s[:width]
    target = width - 3
    cur = ''
    used = 0
    for ch in s:
        cw = _char_width(ch)
        if used + cw > target: break
        cur += ch
        used += cw
    return cur + '...'


def _pad(s, width):
    vis = _string_width(s)
    return s if vis >= width else s + ' ' * (width - vis)


def _ljust(s, width):
    vis = _string_width(s)
    return s if vis >= width else s + ' ' * (width - vis)


def _rjust(s, width):
    vis = _string_width(s)
    return s if vis >= width else ' ' * (width - vis) + s


def _center(s, width):
    vis = _string_width(s)
    if vis >= width: return s
    left = (width - vis) // 2
    right = width - vis - left
    return ' ' * left + s + ' ' * right


def _as_text(obj, style=None):
    if isinstance(obj, Text): return obj
    return Text(str(obj), style=style)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HYPERVOID 基础装饰
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _starfield(width, height, seed=42):
    """层次星空：星点只分布在四角边缘，偶有亮星和流星，中央大面积留白。"""
    rng = random.Random(seed)
    dim_stars = ['·', '∙']
    mid_stars = ['•', '✦']
    bright_stars = ['✧', '✶']
    lines = [' ' * width for _ in range(height)]

    def place(x, y, ch):
        if 0 <= x < width and 0 <= y < height and lines[y][x] == ' ':
            row = list(lines[y])
            row[x] = ch
            lines[y] = ''.join(row)

    # 基础密度：很低
    count = max(5, (width * height) // 180)
    for _ in range(count):
        # 75% 概率出现在边缘四角
        if rng.random() < 0.75:
            if rng.random() < 0.5:
                x = rng.choice([rng.randint(0, max(1, width // 7)),
                                rng.randint(width * 6 // 7, width - 1)])
                y = rng.randint(0, height - 1)
            else:
                x = rng.randint(0, width - 1)
                y = rng.choice([rng.randint(0, max(1, height // 5)),
                                rng.randint(height * 4 // 5, height - 1)])
        else:
            x = rng.randint(0, width - 1)
            y = rng.randint(0, height - 1)
        r = rng.random()
        ch = dim_stars[0] if r < 0.6 else (mid_stars[0] if r < 0.9 else bright_stars[0])
        place(x, y, ch)

    # 几颗亮星（四角）
    for _ in range(2):
        x = rng.choice([rng.randint(2, max(3, width // 8)),
                        rng.randint(width * 7 // 8, width - 3)])
        y = rng.randint(2, max(3, height // 5))
        place(x, y, rng.choice(bright_stars))

    # 一两条流星尾迹，斜向划过边缘
    for _ in range(rng.randint(1, 2)):
        sx = rng.randint(width * 3 // 5, width - 4)
        sy = rng.randint(0, max(1, height // 6))
        length = rng.randint(7, 14)
        for i in range(length):
            x = sx - i
            y = sy + i // 2
            if 0 <= x < width and 0 <= y < height and lines[y][x] == ' ':
                row = list(lines[y])
                row[x] = '·'
                lines[y] = ''.join(row)

    # 为不同字符准备样式映射
    styled = []
    for line in lines:
        t = Text(line)
        for i, ch in enumerate(line):
            if ch in dim_stars:
                t.stylize(DIM_GREY, i, i + 1)
            elif ch in mid_stars:
                t.stylize(CYAN_DIM, i, i + 1)
            elif ch in bright_stars:
                t.stylize(CYAN, i, i + 1)
        styled.append(t)
    return styled


def _badge(label, value, color=CYAN):
    """紧凑 badge：[label] value，label 着色，value 高对比。"""
    t = Text()
    t.append('[', style=DIM_GREY)
    t.append(label, style=color)
    t.append('] ', style=DIM_GREY)
    t.append(str(value), style=GREY if value not in ('✖', '—', '') else DIM_GREY)
    return t


def _join_badges(badges, max_width=None):
    """用两个空格连接 badge，超出宽度时截断。"""
    t = Text()
    used = 0
    for i, b in enumerate(badges):
        if i > 0:
            t.append('  ', style=DIM_GREY)
            used += 2
        bw = _text_width(b)
        if max_width and used + bw > max_width:
            remain = max(0, max_width - used - 3)
            if remain > 0:
                t.append(_truncate(b.plain, remain), style=DIM_GREY)
            break
        t.append(b)
        used += bw
    return t


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HYPERVOID 大 ASCII Logo（6 行，HYPER 青色 + VOID 灰色）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HYPER_LOGO = [
    '██  ██   ██  ██   █████    ██████   █████  ',
    '██  ██   ██  ██   ██  ██   ██       ██  ██ ',
    '██████    ████    █████    ██████   █████  ',
    '██  ██     ██     ██       ██       ██ ██  ',
    '██  ██     ██     ██       ██████   ██  ██ ',
    '██  ██     ██     ██       ██       ██  ██ ',
]
VOID_LOGO = [
    '  ██  ██    ████    ██████   ██████ ',
    '  ██  ██   ██  ██     ██     ██   ██',
    '  ██  ██   ██  ██     ██     ██   ██',
    '  ██  ██   ██  ██     ██     ██   ██',
    '   ████     ████      ██     ███████',
    '    ██       ██     ██████   ███████',
]


def _render_big_logo(width):
    """渲染 6 行大 ASCII Logo，HYPER 冷青，VOID 星尘灰，整体居中。"""
    rows = []
    sample_total = _string_width(HYPER_LOGO[0]) + 3 + _string_width(VOID_LOGO[0])
    pad = max(0, (width - sample_total) // 2)
    for h, v in zip(HYPER_LOGO, VOID_LOGO):
        t = Text(style='on ' + DARKER)
        t.append(' ' * pad, style='on ' + DARKER)
        t.append(h, style='bold ' + CYAN)
        t.append('   ', style='on ' + DARKER)
        t.append(v, style='bold ' + GREY)
        rows.append(_pad_visual(t, width))
    return rows


def _render_tagline(width):
    """Logo 下方小字：带装饰线的副标题，居中。"""
    text = ' 个人开发工作站 · hypervoid.top · ' + datetime.now().strftime('%H:%M') + ' '
    text_w = _string_width(text)
    if text_w >= width - 4:
        text = ' ' + _truncate(text.strip(), width - 4) + ' '
        text_w = _string_width(text)
    # 装饰线：─ 个人开发工作站 · hypervoid.top · 18:24 ─
    side = max(1, (width - text_w) // 2)
    left_line = '─' * side
    right_line = '─' * (width - text_w - side)
    t = Text(style='on ' + DARKER)
    t.append(left_line, style=CYAN_DIM)
    # 文本内部分段着色
    t.append(' 个人开发工作站', style=DIM_GREY)
    t.append(' · ', style=CYAN_DIM)
    t.append('hypervoid.top', style=CYAN)
    t.append(' · ', style=CYAN_DIM)
    t.append(datetime.now().strftime('%H:%M'), style=GREY)
    t.append(' ', style=DIM_GREY)
    t.append(right_line, style=CYAN_DIM)
    return t


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HYPERVOID 顶部栏 / 状态栏
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _pad_visual(text_obj, width):
    """按显示宽度在 Text 右侧填充空格，使其显示宽度达到 width。"""
    vis = _text_width(text_obj)
    if vis < width:
        text_obj.append(' ' * (width - vis), style='on ' + DARKER)
    return text_obj


def _center_visual(text_obj, width):
    """按显示宽度把 Text 居中。"""
    vis = _text_width(text_obj)
    if vis >= width:
        return text_obj
    left = (width - vis) // 2
    right = width - vis - left
    t = Text(style='on ' + DARKER)
    t.append(' ' * left, style='on ' + DARKER)
    t.append(text_obj)
    t.append(' ' * right, style='on ' + DARKER)
    return t


def _render_logo_line(width):
    """单行 Logo：◈ HYPER·VOID 个人开发工作站，强制补齐显示宽度。"""
    t = Text(style='on ' + DARKER)
    t.append('◈ ', style=DIM_GREY)
    t.append('HYPER', style='bold ' + CYAN)
    t.append('·', style=DIM_GREY)
    t.append('VOID', style='bold ' + GREY)
    t.append('   个人开发工作站 · hypervoid.top', style=DIM_GREY)
    right = Text(datetime.now().strftime('%H:%M'), style=GREY)
    used = _text_width(t) + _text_width(right)
    gap = max(1, width - used)
    t.append(' ' * gap, style='on ' + DARKER)
    t.append(right)
    return _pad_visual(t, width)


def _render_status_line(width):
    """项目状态栏：badge 用 │ 分隔，居中，强制补齐显示宽度。"""
    info = get_project_info()
    segments = [
        ('dir', info['dir'][:14], CYAN),
        ('git', info['git'][:10] if info['git'] else '—', PURPLE),
        ('claude', '✔' if info['claude_md'] else '✖', ORANGE if info['claude_md'] else DIM_GREY),
        ('settings', '✔' if info['settings'] else '✖', ORANGE if info['settings'] else DIM_GREY),
        ('cmds', str(info['commands']), AMBER),
        ('api', '✔' if info['api_key'] else '✖', ORANGE if info['api_key'] else DIM_GREY),
    ]
    t = Text(style='on ' + DARKER)
    for i, (label, value, color) in enumerate(segments):
        if i > 0:
            t.append(' │ ', style=DIM_GREY)
        t.append('[', style=DIM_GREY)
        t.append(label, style=color)
        t.append('] ', style=DIM_GREY)
        t.append(str(value), style=GREY if value not in ('✖', '—', '') else DIM_GREY)
    # 居中并补齐
    vis = _text_width(t)
    if vis < width:
        left = (width - vis) // 2
        right = width - vis - left
        result = Text(style='on ' + DARKER)
        result.append(' ' * left, style='on ' + DARKER)
        result.append(t)
        result.append(' ' * right, style='on ' + DARKER)
        return result
    return t


def _render_banner(width, title=None, subtitle=None):
    """顶部双行 banner：紧凑 Logo 行 + 居中状态行。"""
    lines = [Text(' ' * width, style='on ' + DARKER) for _ in range(2)]
    lines[0] = _render_logo_line(width)
    lines[1] = _render_status_line(width)
    return Group(*lines)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HYPERVOID 菜单面板（严格对齐，v2 留白版）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _menu_columns(width):
    """返回菜单各列宽度（基于手工面板 content_w = width - 4）。"""
    content_w = max(40, width - 4)   # 左右边框 2 + 两侧各 1 空格内边距
    key_w = 4
    label_w = 18
    gaps = 4                         # 两处 "  "
    desc_w = max(10, content_w - key_w - label_w - gaps)
    return content_w, key_w, label_w, desc_w


def _menu_row(item, key_w, label_w, desc_w, selected=False):
    """生成一行严格对齐的菜单项（三列：KEY / 功能 / 说明）。"""
    key = str(item.get('key', ''))
    label = str(item.get('label', ''))
    desc = str(item.get('desc', ''))

    key_part = _rjust(key, key_w)   # 右对齐，更像菜单热键
    label_part = _ljust(_truncate(label, label_w), label_w)
    desc_part = _ljust(_truncate(desc, desc_w), desc_w)

    plain = f'{key_part}  {label_part}  {desc_part}'
    text = Text(plain)

    p0 = 0
    p1 = key_w
    p2 = p1 + 2
    p3 = p2 + label_w

    if selected:
        text.stylize('white on ' + PURPLE_BRIGHT, 0, len(plain))
        text.stylize('bold white on ' + PURPLE_BRIGHT, p0, p1)
        text.stylize('bold white on ' + PURPLE_BRIGHT, p2, p3)
    else:
        # 整行深空背景，KEY 用亮橙、功能用粗体白、说明用暗灰
        text.stylize('on ' + DARK, 0, len(plain))
        text.stylize(DIM_GREY, 0, len(plain))
        text.stylize('bold ' + ORANGE_BRIGHT, p0, p1)
        text.stylize('bold ' + WHITE, p2, p3)
    return text


def _render_menu_panel(width, items, selected, title, footer):
    """手工绘制圆角面板，内部菜单列严格对齐，显示宽度精确等于 width，增加留白。"""
    inner = max(40, width - 2)          # 左右 │ 之间的显示宽度
    content_w = max(36, inner - 2)      # 内容实际可用显示宽度（去掉两侧 1 空格内边距）

    # 顶边框：分段着色，标题居中偏左，footer 居右
    title_full = f'◈ {title}'
    title_text = _truncate(title_full, max(4, content_w // 2 - 4))
    footer_text = _truncate(str(footer), 16)
    title_w = _string_width(title_text)
    footer_w = _string_width(footer_text)
    # 布局：╭── title ───────────── footer ─╮ 各部分宽度需按实际字符数
    left_decor_w = 3   # ╭──
    right_decor_w = 3  #  ─╮
    mid = max(1, width - left_decor_w - title_w - 1 - footer_w - 1 - right_decor_w)
    top = Text('╭──', style=CYAN + ' on ' + DARK)
    top.append(title_text, style='bold ' + WHITE + ' on ' + DARK)
    top.append(' ', style=CYAN + ' on ' + DARK)
    top.append('─' * mid, style=CYAN_DIM + ' on ' + DARK)
    top.append(' ', style=CYAN + ' on ' + DARK)
    top.append(footer_text, style=DIM_GREY + ' on ' + DARK)
    top.append(' ─╮', style=CYAN + ' on ' + DARK)

    rows = [top]
    # 上空行
    rows.append(Text(f'│{" " * inner}│', style=CYAN + ' on ' + DARK))

    # 表头
    key_w, label_w, desc_w = _menu_columns(width)[1:]
    header_plain = (
        _rjust('KEY', key_w) + '  ' +
        _ljust('功能', label_w) + '  ' +
        _ljust('说明', desc_w)
    )
    header = Text(header_plain, style='bold ' + CYAN + ' on ' + DARK)
    header = _panel_content_line(header, content_w)
    rows.append(header)

    # 分隔线：使用更细的双线或渐变效果，保持简洁
    sep = Text('─' * content_w, style=CYAN_DIM + ' on ' + DARK)
    sep = _panel_content_line(sep, content_w)
    rows.append(sep)

    # 菜单项
    for i, it in enumerate(items):
        rows.append(_panel_content_line(_menu_row(it, key_w, label_w, desc_w, selected=(i == selected)), content_w))

    # 底边框（紧凑：不再加下空行，让面板更利落）
    bot_plain = f'╰{"─" * (width - 2)}╯'
    rows.append(Text(bot_plain, style=CYAN + ' on ' + DARK))
    return rows


def _panel_content_line(content, content_w):
    """把内容行包装成 │ content │，按显示宽度对齐，边框和内容自带深色背景。"""
    plain = content.plain
    if _string_width(plain) > content_w:
        plain = _truncate(plain, content_w)
        content = Text(plain)
        content.stylize(DIM_GREY, 0, len(plain))
    pad = max(0, content_w - _string_width(plain))
    border_style = CYAN + ' on ' + DARK
    line = Text('│ ', style=border_style)
    line.append(content)
    if pad > 0:
        line.append(' ' * pad, style='on ' + DARK)
    line.append(' │', style=border_style)
    return line


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HYPERVOID 底部栏（合并为一行）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _render_bottom_bar(width, left_hint, right_hint=''):
    """底部栏：左侧操作提示（热键橙色高亮），右侧装饰 + 描述，单行，严格补齐宽度。"""
    t = Text(style='on ' + DARKER)
    # 左侧提示分段着色：↑↓ / Enter / Esc 等着色
    segments = [
        (' ', DIM_GREY),
        ('↑↓', ORANGE_BRIGHT), (' 导航 ', DIM_GREY),
        ('Enter', ORANGE_BRIGHT), (' 选择  ', DIM_GREY),
        ('数字热键', ORANGE_BRIGHT), ('  ', DIM_GREY),
        ('Esc', ORANGE_BRIGHT), (' 返回', DIM_GREY),
    ]
    for seg, style in segments:
        t.append(seg, style=style)

    # 右侧：◇ + 描述
    left_w = _text_width(t)
    right_avail = max(0, width - left_w - 3)
    right_full = _truncate(str(right_hint), right_avail)
    right_w = _string_width(right_full)
    pad = max(1, width - left_w - 3 - right_w)
    t.append(' ' * pad, style='on ' + DARKER)
    t.append('◇ ', style=CYAN_DIM)
    t.append(right_full, style=GREY)

    # 最终补齐显示宽度
    final_pad = width - _text_width(t)
    if final_pad > 0:
        t.append(' ' * final_pad, style='on ' + DARKER)
    return t


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HYPERVOID 完整帧组装
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _overlay_on_starfield(width, height, overlays):
    """在星空背景上叠加若干行；overlays 是 (y, renderable) 列表。"""
    bg = _starfield(width, height)
    for y, obj in overlays:
        if 0 <= y < height:
            bg[y] = _overlay_text(bg[y], obj, width)
    return Group(*bg)


def _overlay_text(bg_line, fg_line, width):
    """把 fg_line 居中叠加到 bg_line 上，保留样式。"""
    if hasattr(fg_line, 'plain'):
        fg = fg_line
    else:
        fg = Text(str(fg_line))
    fg_plain = fg.plain
    fg_w = _string_width(fg_plain)
    pad = max(0, (width - fg_w) // 2)
    bg_plain = bg_line.plain
    new_plain = bg_plain[:pad] + fg_plain + bg_plain[pad + len(fg_plain):]
    if len(new_plain) > width:
        new_plain = new_plain[:width]
    result = Text(new_plain)
    result.stylize(DIM_GREY, 0, len(new_plain))
    for start, end, style in fg.spans:
        result.stylize(style, pad + start, pad + end)
    return result


def _render_frame(items, selected, title, footer, width=None, height=None):
    """组装完整主菜单帧：星空背景 + 大 Logo/紧凑 banner + 状态行 + 菜单面板 + 底部栏。"""
    w = width or max(70, console.width)
    h = height or max(24, console.height)

    bg = _starfield(w, h)

    # 顶部区域：主菜单用大 Logo + 副标题 + 状态行；子菜单或项目过多用紧凑 banner
    use_big_logo = (title == '主菜单' and len(items) <= 8 and h >= 24)
    if use_big_logo:
        # 大 Logo 顶部留白：2 行深色空行，让标题呼吸
        logo_top = 2
        for i in range(logo_top):
            if i < h:
                bg[i] = Text(' ' * w, style='on ' + DARKER)
        # 大 Logo（6 行）
        logo_rows = _render_big_logo(w)
        for i, row in enumerate(logo_rows[:6]):
            if logo_top + i < h:
                bg[logo_top + i] = row
        # Logo 下方：1 行纯深色空行 + tagline
        y = logo_top + 6
        if y < h:
            bg[y] = Text(' ' * w, style='on ' + DARKER)
        y = logo_top + 6 + 1
        if y < h:
            bg[y] = _render_tagline(w)
        # tagline 下方直接接状态行，紧凑且连贯
        y = logo_top + 6 + 2
        if y < h:
            bg[y] = _render_status_line(w)
        # 状态行下方：1 行纯深色空行，分隔面板
        y = logo_top + 6 + 3
        if y < h:
            bg[y] = Text(' ' * w, style='on ' + DARKER)
        # 面板从此处开始
        header_rows = logo_top + 6 + 4
    else:
        banner = _render_banner(w)
        for i in range(min(2, h)):
            bg[i] = banner.renderables[i]
        header_rows = 2

    # 菜单面板：在顶部区域下方可用空间内垂直居中，预留底部栏 1 行 + 1 行空行
    panel_rows = _render_menu_panel(w, items, selected, title, footer)
    panel_h = len(panel_rows)
    bottom_reserved = 2  # 底部栏 1 行 + 上方 1 行空行
    available_top = h - header_rows - bottom_reserved
    if panel_h + 2 <= available_top:
        # 在可用空间内居中，与顶部区域之间至少有 1 行空行
        start_y = header_rows + 1 + (available_top - panel_h) // 2
    else:
        # 空间不足：贴紧顶部区域，但不超过屏幕
        start_y = header_rows
    start_y = min(start_y, h - panel_h - bottom_reserved)
    start_y = max(start_y, header_rows)  # 确保不覆盖顶部 Logo/状态区域
    for i, row in enumerate(panel_rows):
        if start_y + i < h:
            bg[start_y + i] = row

    # 底部栏：单行，合并帮助和提示
    bottom_y = h - 1
    selected_desc = items[selected].get('desc', '') if 0 <= selected < len(items) else ''
    bg[bottom_y] = _render_bottom_bar(w, '↑↓ 导航  Enter 选择  数字热键  Esc 返回', selected_desc or 'HYPERVOID 工作站')

    return Group(*bg)


def _panel_to_lines(panel, width):
    """把 Rich Panel 渲染成多行 Text，用于叠加到星空背景。"""
    import io
    tmp_console = Console(file=io.StringIO(), width=width, color_system='256', legacy_windows=False, markup=False)
    tmp_console.print(panel)
    output = tmp_console.file.getvalue()
    lines = output.split('\n')
    result = []
    for line in lines:
        if not line:
            continue
        result.append(Text.from_ansi(line))
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 键盘输入 / 数据管理
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def read_key():
    if IS_WINDOWS:
        ch = msvcrt.getch()
        if ch == b'\r': return ('enter', '')
        if ch == b'\x1b': return ('esc', '')
        if ch == b'\x03': raise KeyboardInterrupt
        if ch in (b'\x00', b'\xe0'):
            ch2 = msvcrt.getch()
            m = {b'H':'up',b'P':'down',b'K':'left',b'M':'right',b'S':'del',b'G':'home',b'O':'end',b'I':'pgup',b'Q':'pgdn'}
            return ('nav', m.get(ch2, ''))
        return ('char', ch.decode('utf-8', errors='ignore').lower())
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
                m = {'A':'up','B':'down','C':'right','D':'left','5':'pgup','6':'pgdn','H':'home','F':'end'}
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


def load_json(name, default=None):
    p = DATA_DIR / name
    if p.exists():
        try: return json.loads(p.read_text('utf-8'))
        except: pass
    return default if default is not None else {}


def save_json(name, data):
    (DATA_DIR / name).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def now_str():
    return datetime.now().strftime('%Y-%m-%d %H:%M')


def get_project_info():
    import subprocess
    cwd = Path.cwd()
    info = {'dir': cwd.name, 'path': str(cwd)}
    try:
        info['git'] = subprocess.check_output(['git','branch','--show-current'], stderr=subprocess.DEVNULL, text=True).strip()
    except: info['git'] = ''
    info['claude_md'] = (cwd / 'CLAUDE.md').exists()
    info['settings'] = (cwd / '.claude' / 'settings.json').exists()
    cmd_dir = cwd / '.claude' / 'commands'
    info['commands'] = len(list(cmd_dir.glob('*.md'))) if cmd_dir.exists() else 0
    info['api_key'] = bool(os.environ.get('ANTHROPIC_API_KEY'))
    return info


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 兼容层绘制函数（映射到 HYPERVOID 风格）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def draw_header(title=None, subtitle=None):
    """HYPERVOID 风格顶部横幅：Logo + 状态 + 可选标题。"""
    w = max(70, console.width)
    clear()
    banner = _render_banner(w)
    if title:
        t = Text()
        t.append('◈ ', style=DIM_GREY)
        t.append(title, style='bold ' + CYAN)
        if subtitle:
            t.append(' · ', style=DIM_GREY)
            t.append(subtitle, style=GREY)
        console.print(Align.center(t, width=w))
    console.print(banner)


def draw_logo():
    """HYPERVOID 风格：绘制完整主界面框架（无交互）。"""
    w = max(70, console.width)
    h = max(24, console.height)
    clear()
    console.print(_render_frame([], 0, '主菜单', '按 Enter 开始', width=w, height=h))


def draw_stars():
    """HYPERVOID 风格：打印一行稀疏星点分隔。"""
    console.print(Text('  ·  ✦  ·  ', style=DIM_GREY))


def draw_status_bar(*args):
    """HYPERVOID 风格：项目状态 badge 行 + 帮助提示。"""
    w = max(70, console.width)
    console.print(_render_status_line(w))
    hint = ' '.join(str(a) for a in args) if args else 'HYPERVOID · 个人开发工作站'
    console.print(_render_bottom_bar(w, '按任意键继续...', hint))


def draw_project_info():
    """打印 HYPERVOID 风格项目状态行。"""
    w = max(70, console.width)
    console.print(_render_status_line(w))


def draw_divider(char='─', style='dim'):
    """HYPERVOID 风格分隔线。"""
    if len(str(char)) > 1:
        console.print(Rule(title=str(char), style=style))
    else:
        console.print(Rule(characters=char, style=style))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 菜单（HYPERVOID 严格对齐面板）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def menu(items, title='菜单', footer='↑↓ 导航  Enter 选择  Esc 返回', **kwargs):
    """
    HYPERVOID 风格菜单：
      · 深黑稀疏星空背景，四角星点，中央留白
      · 顶部大 Logo + 副标题 + 居中项目状态 badge
      · 中央圆角面板，菜单列严格对齐（KEY / 功能 / 说明），上下留白
      · 选中行整块星云紫高亮
      · 底部单行栏：左侧操作提示，右侧当前项说明或站点标识
    兼容旧调用：menu(title, items_list) 自动交换；字符串列表自动转 dict。
    """
    # 兼容旧顺序 menu(title, items_list)
    if isinstance(items, str) and isinstance(title, (list, tuple)):
        items, title = title, items
    # 兼容字符串列表
    if items and isinstance(items[0], str):
        items = [{'key': str(i + 1), 'label': s, 'desc': '', 'icon': ' '} for i, s in enumerate(items)]
    # 保证每项有基础字段
    for i, it in enumerate(items):
        if 'key' not in it: it['key'] = str(i + 1)
        if 'label' not in it: it['label'] = ''
        if 'desc' not in it: it['desc'] = ''
        if 'icon' not in it: it['icon'] = ' '

    sel = 0
    w = max(70, console.width)
    h = max(24, console.height)
    frame = _render_frame(items, sel, title, footer, width=w, height=h)
    with Live(frame, console=console, refresh_per_second=30, screen=True) as live:
        while True:
            kt, k = read_key()
            if kt == 'esc' or (kt == 'char' and k == 'q'):
                return -1
            if kt == 'enter':
                return sel
            if kt == 'nav':
                if k == 'up': sel = (sel - 1) % len(items)
                if k == 'down': sel = (sel + 1) % len(items)
            if kt == 'char' and k in [str(i + 1) for i in range(len(items))]:
                return int(k) - 1
            live.update(_render_frame(items, sel, title, footer, width=w, height=h))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 滚动视图 / 表格 / 提示框（统一成 HYPERVOID 面板）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _scroll_frame(title, lines, pos, page, line_numbers=False):
    w = max(70, console.width)
    h = max(24, console.height)
    total = len(lines)
    visible = lines[pos:pos + page]

    body_rows = []
    for i, line in enumerate(visible):
        prefix = f'{pos + i + 1:>4}  ' if line_numbers else ''
        txt = _as_text(line)
        plain = prefix + txt.plain
        row = Text(plain, style=GREY)
        body_rows.append(row)
    while len(body_rows) < page:
        body_rows.append(Text(''))

    body = Group(*body_rows)
    panel = Panel(
        body,
        title=f'◈ {title}',
        title_align='left',
        subtitle=f'{min(pos + page, total)}/{total}',
        subtitle_align='right',
        border_style=CYAN,
        style='on ' + DARK,
        box=box.ROUNDED,
        padding=(1, 2),
    )

    bg = _starfield(w, h)
    panel_lines = _panel_to_lines(panel, w)
    start_y = max(3, (h - len(panel_lines)) // 2)
    for i, row in enumerate(panel_lines):
        if start_y + i < h:
            bg[start_y + i] = row

    bg[h - 1] = _render_bottom_bar(w, '↑↓ 滚动  PgUp/PgDn 翻页  Esc 返回', 'HYPERVOID · 阅读模式')
    return Group(*bg)


def scroll_view(title, lines, footer='↑↓ 滚动  PgUp/PgDn 翻页  Esc 返回', line_numbers=False, **kwargs):
    pos = 0
    page = max(console.height - 8, 10)
    total = len(lines)
    frame = _scroll_frame(title, lines, pos, page, line_numbers)
    with Live(frame, console=console, refresh_per_second=30, screen=True) as live:
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
                    live.update(_scroll_frame(title, lines, pos, page, line_numbers))


def show_table(title, headers, rows, footer='按任意键返回', **kwargs):
    clear()
    w = max(70, console.width)
    h = max(24, console.height)
    bg = _starfield(w, h)

    table = Table(
        box=box.ROUNDED,
        border_style=CYAN,
        show_lines=False,
        pad_edge=True,
        padding=(0, 1),
        style='on ' + DARK,
    )
    for h_text in headers:
        table.add_column(h_text, style='bold ' + WHITE)
    for row in rows:
        table.add_row(*[str(c) for c in row])

    panel = Panel(table, title=f'◈ {title}', title_align='left', border_style=CYAN, style='on ' + DARK)
    panel_lines = _panel_to_lines(Align.center(panel, width=w), w)
    start_y = max(3, (h - len(panel_lines)) // 2)
    for i, row in enumerate(panel_lines):
        if start_y + i < h:
            bg[start_y + i] = row

    bg[h - 1] = _render_bottom_bar(w, '按任意键返回', footer)

    console.print(Group(*bg))
    wait_key()


def show_ok(a, b='', c='', **kwargs):
    """
    成功提示：HYPERVOID 风格面板
    兼容：show_ok(msg) / show_ok(title, msg, detail)
    """
    if not b and not c:
        msg, title, detail = a, '完成', ''
    else:
        title, msg, detail = a, b, c
    clear()
    w = max(70, console.width)
    h = max(24, console.height)
    bg = _starfield(w, h)

    body_lines = [Text('')]
    t = Text('✔ ', style=ORANGE)
    t.append(msg, style='bold ' + WHITE)
    body_lines.append(t)
    if detail:
        body_lines.append(Text(''))
        body_lines.append(Text(detail, style=DIM_GREY))
    body_lines.append(Text(''))

    panel = _render_left_bar_panel(w, body_lines, title=title, right='ok')
    start_y = max(3, (h - len(panel)) // 2)
    for i, row in enumerate(panel):
        if start_y + i < h:
            bg[start_y + i] = row

    bg[h - 1] = _render_bottom_bar(w, '按任意键继续...', 'HYPERVOID')

    console.print(Group(*bg))
    wait_key()


def show_err(msg, **kwargs):
    """错误提示：HYPERVOID 风格面板。"""
    clear()
    w = max(70, console.width)
    h = max(24, console.height)
    bg = _starfield(w, h)

    body_lines = [Text('')]
    t = Text('✖ ', style=ORANGE)
    t.append(msg, style='bold ' + WHITE)
    body_lines.append(t)
    body_lines.append(Text(''))

    panel = _render_left_bar_panel(w, body_lines, title='错误', right='err')
    start_y = max(3, (h - len(panel)) // 2)
    for i, row in enumerate(panel):
        if start_y + i < h:
            bg[start_y + i] = row

    bg[h - 1] = _render_bottom_bar(w, '按任意键继续...', '请检查输入或环境后重试')

    console.print(Group(*bg))
    wait_key()


# 保留旧内部辅助函数名，避免外部代码引用时缺失
def _render_left_bar_panel(width, body_lines, title='命令', right='esc'):
    """HYPERVOID v2 风格左竖线面板（用于 show_ok/show_err 等提示框）：深青竖线。"""
    inner = max(0, width - 6)  # 左右 ▌▐ 各 1，padding 左右各 2
    bg = 'on ' + DARK
    rows = []

    top = Text('', style=bg)
    top.append(' ▌', style=CYAN + ' ' + bg)
    title_t = _as_text(title, style='bold ' + WHITE + ' ' + bg)
    right_t = _as_text(right, style=DIM_GREY + ' ' + bg)
    gap = max(0, inner - _text_width(title_t) - _text_width(right_t))
    top.append(title_t)
    top.append(' ' * gap, style=bg)
    top.append(right_t)
    top.append('▐', style=CYAN + ' ' + bg)
    rows.append(top)

    rows.append(Text(' ▌' + ' ' * inner + '▐', style=CYAN + ' ' + bg))

    for line in body_lines:
        lt = _as_text(line)
        plain = lt.plain
        if _string_width(plain) > inner:
            plain = _truncate(plain, inner)
            lt = Text(plain)
        pad = max(0, inner - _string_width(plain))
        row = Text('', style=bg)
        row.append(' ▌', style=CYAN + ' ' + bg)
        row.append(lt)
        row.append(' ' * pad, style=bg)
        row.append('▐', style=CYAN + ' ' + bg)
        rows.append(row)

    while len(rows) < 6:
        rows.append(Text(' ▌' + ' ' * inner + '▐', style=CYAN + ' ' + bg))
    return rows
