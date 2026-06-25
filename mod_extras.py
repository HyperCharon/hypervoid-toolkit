"""
HYPERVOID 扩展模块 - 快捷工具箱、命令面板、博客集成
"""
import os, sys, json, hashlib, base64, uuid, re, time, subprocess, webbrowser
from pathlib import Path
from datetime import datetime
from urllib.parse import quote, unquote

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.rule import Rule
from rich import box
import msvcrt

console = Console()

class T:
    CYAN='bold bright_cyan'; MAG='bold bright_magenta'; YEL='bold bright_yellow'
    GRN='bold bright_green'; RED='bold bright_red'; WHT='bold bright_white'
    ACCENT='bold bright_cyan'; DIM='dim bright_white'; OK='bold bright_green'
    WARN='bold bright_yellow'; ERR='bold bright_red'; KEY='bold bright_cyan'
    LABEL='bold bright_white'; DESC='dim bright_white'; BOX='bright_cyan'
    BORDER='bright_cyan'; HEADER='bold bright_white on dark_cyan'
    STATUS='black on dark_cyan'; STAR='dim bright_white'

def read_key():
    ch = msvcrt.getch()
    if ch == b'\r': return ('enter','')
    if ch == b'\x1b': return ('esc','')
    if ch == b'\x03': raise KeyboardInterrupt
    if ch in (b'\x00', b'\xe0'):
        ch2 = msvcrt.getch()
        m = {b'H':'up',b'P':'down',b'I':'pgup',b'Q':'pgdn'}
        return ('nav', m.get(ch2,''))
    return ('char', ch.decode('utf-8',errors='ignore').lower())

def clear(): os.system('cls')
def wait_key(): read_key()

DATA_DIR = Path.home() / '.claude-toolkit' / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)

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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 快捷工具箱
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def quick_tools():
    """快捷开发者工具"""
    while True:
        clear()
        console.print(Align.center(Text('  ·  快捷工具箱  ·  ', style=T.ACCENT)))
        console.print()

        tools = [
            ('1', ' ', 'UUID 生成器', '生成各种格式的 UUID'),
            ('2', ' ', 'Hash 计算器', 'MD5 / SHA1 / SHA256'),
            ('3', ' ', 'Base64 编解码', 'Base64 编码和解码'),
            ('4', ' ', 'URL 编解码', 'URL 编码和解码'),
            ('5', ' ', '正则测试器', '测试正则表达式匹配'),
            ('6', ' ', '时间戳工具', 'Unix 时间戳转换'),
            ('7', ' ', '随机密码生成', '生成安全随机密码'),
            ('8', ' ', 'JSON 格式化', '格式化 / 压缩 JSON'),
            ('9', ' ', '进制转换', '二进制/八进制/十进制/十六进制'),
            ('0', ' ', '颜色代码转换', 'HEX / RGB / HSL 互转'),
        ]

        for key, icon, label, desc in tools:
            console.print(f'   [{T.KEY}][{key}][/] {icon} [{T.LABEL}]{label}[/]')
            console.print(f'        [{T.DIM}]{desc}[/]')

        console.print()
        console.print(f'  [{T.DIM}]选择工具  Esc 返回[/]')

        kt, k = read_key()
        if kt == 'esc' or (kt == 'char' and k == 'q'): return
        if kt == 'char':
            if k == '1': tool_uuid()
            elif k == '2': tool_hash()
            elif k == '3': tool_base64()
            elif k == '4': tool_url_encode()
            elif k == '5': tool_regex()
            elif k == '6': tool_timestamp()
            elif k == '7': tool_password()
            elif k == '8': tool_json_format()
            elif k == '9': tool_base_convert()
            elif k == '0': tool_color()


def tool_uuid():
    """UUID 生成器"""
    clear()
    console.print(Align.center(Text('  ·  UUID 生成器  ·  ', style=T.ACCENT)))
    console.print()

    results = []
    for i in range(5):
        u = uuid.uuid4()
        results.append(str(u))

    console.print(f'  [{T.ACCENT}]生成 5 个 UUID v4:[/]')
    console.print()
    for i, u in enumerate(results):
        console.print(f'  [{T.GRN}]{i+1}.[/] {u}')

    console.print()
    console.print(f'  [{T.DIM}]UUID v1 (时间戳): {uuid.uuid1()}[/]')
    console.print(f'  [{T.DIM}]无连字符: {uuid.uuid4().hex}[/]')

    # 复制到剪贴板
    console.print()
    console.print(f'  [{T.DIM}][C] 复制第一个  [A] 复制全部  Esc 返回[/]')

    while True:
        kt, k = read_key()
        if kt == 'esc' or (kt == 'char' and k == 'q'): return
        if kt == 'char' and k == 'c':
            try:
                subprocess.run(['clip'], input=results[0].encode(), check=True)
                console.print(f'  [{T.OK}]已复制[/]')
            except: pass
        if kt == 'char' and k == 'a':
            try:
                subprocess.run(['clip'], input='\n'.join(results).encode(), check=True)
                console.print(f'  [{T.OK}]已复制全部[/]')
            except: pass


def tool_hash():
    """Hash 计算器"""
    clear()
    console.print(Align.center(Text('  ·  Hash 计算器  ·  ', style=T.ACCENT)))
    console.print()
    console.print(f'  [{T.PROMPT}]输入文本:[/] ', end='')
    text = input()
    if not text: return

    b = text.encode('utf-8')
    md5 = hashlib.md5(b).hexdigest()
    sha1 = hashlib.sha1(b).hexdigest()
    sha256 = hashlib.sha256(b).hexdigest()

    console.print()
    console.print(f'  [{T.ACCENT}]计算结果:[/]')
    console.print()
    console.print(f'  [{T.GRN}]MD5:[/]    {md5}')
    console.print(f'  [{T.GRN}]SHA1:[/]   {sha1}')
    console.print(f'  [{T.GRN}]SHA256:[/] {sha256}')

    console.print()
    console.print(f'  [{T.DIM}][C] 复制 SHA256  Esc 返回[/]')

    while True:
        kt, k = read_key()
        if kt == 'esc' or (kt == 'char' and k == 'q'): return
        if kt == 'char' and k == 'c':
            try:
                subprocess.run(['clip'], input=sha256.encode(), check=True)
                console.print(f'  [{T.OK}]已复制[/]')
            except: pass


def tool_base64():
    """Base64 编解码"""
    clear()
    console.print(Align.center(Text('  ·  Base64 编解码  ·  ', style=T.ACCENT)))
    console.print()
    console.print(f'  [{T.KEY}][E][/] 编码  [{T.KEY}][D][/] 解码  [{T.KEY}][Q][/] 返回')

    kt, k = read_key()
    if kt == 'esc' or k == 'q': return

    if k == 'e':
        console.print(f'\n  [{T.PROMPT}]输入原文:[/] ', end='')
        text = input()
        if not text: return
        encoded = base64.b64encode(text.encode('utf-8')).decode('ascii')
        console.print(f'\n  [{T.GRN}]Base64:[/] {encoded}')
        try:
            subprocess.run(['clip'], input=encoded.encode(), check=True)
            console.print(f'  [{T.DIM}]已复制到剪贴板[/]')
        except: pass

    elif k == 'd':
        console.print(f'\n  [{T.PROMPT}]输入 Base64:[/] ', end='')
        text = input()
        if not text: return
        try:
            decoded = base64.b64decode(text).decode('utf-8')
            console.print(f'\n  [{T.GRN}]原文:[/] {decoded}')
        except Exception as e:
            console.print(f'\n  [{T.ERR}]解码失败: {e}[/]')

    console.print(f'\n  [{T.DIM}]按任意键返回...[/]')
    wait_key()


def tool_url_encode():
    """URL 编解码"""
    clear()
    console.print(Align.center(Text('  ·  URL 编解码  ·  ', style=T.ACCENT)))
    console.print()
    console.print(f'  [{T.KEY}][E][/] 编码  [{T.KEY}][D][/] 解码  [{T.KEY}][Q][/] 返回')

    kt, k = read_key()
    if kt == 'esc' or k == 'q': return

    if k == 'e':
        console.print(f'\n  [{T.PROMPT}]输入文本:[/] ', end='')
        text = input()
        if not text: return
        encoded = quote(text, safe='')
        console.print(f'\n  [{T.GRN}]URL 编码:[/] {encoded}')

    elif k == 'd':
        console.print(f'\n  [{T.PROMPT}]输入编码文本:[/] ', end='')
        text = input()
        if not text: return
        decoded = unquote(text)
        console.print(f'\n  [{T.GRN}]解码结果:[/] {decoded}')

    console.print(f'\n  [{T.DIM}]按任意键返回...[/]')
    wait_key()


def tool_regex():
    """正则测试器"""
    clear()
    console.print(Align.center(Text('  ·  正则测试器  ·  ', style=T.ACCENT)))
    console.print()

    console.print(f'  [{T.PROMPT}]正则表达式:[/] ', end='')
    pattern = input()
    if not pattern: return

    console.print(f'  [{T.PROMPT}]测试文本:[/] ', end='')
    text = input()
    if not text: return

    try:
        matches = list(re.finditer(pattern, text))
        console.print()
        if matches:
            console.print(f'  [{T.OK}]找到 {len(matches)} 个匹配:[/]')
            for i, m in enumerate(matches[:10]):
                console.print(f'  [{T.GRN}]{i+1}.[/] 位置 {m.start()}-{m.end()}: "{m.group()}"')
                if m.groups():
                    for j, g in enumerate(m.groups()):
                        console.print(f'       组{j+1}: "{g}"')
        else:
            console.print(f'  [{T.WARN}]未找到匹配[/]')

        # 显示完整匹配高亮
        highlighted = re.sub(pattern, f'[{T.OK}]\\g<0>[/{T.OK}]', text)
        console.print()
        console.print(f'  [{T.DIM}]高亮显示:[/] {highlighted}')

    except re.error as e:
        console.print(f'\n  [{T.ERR}]正则错误: {e}[/]')

    console.print(f'\n  [{T.DIM}]按任意键返回...[/]')
    wait_key()


def tool_timestamp():
    """时间戳工具"""
    clear()
    console.print(Align.center(Text('  ·  时间戳工具  ·  ', style=T.ACCENT)))
    console.print()

    now = time.time()
    console.print(f'  [{T.ACCENT}]当前时间:[/]')
    console.print(f'  [{T.GRN}]Unix:[/]     {int(now)}')
    console.print(f'  [{T.GRN}]毫秒:[/]     {int(now * 1000)}')
    console.print(f'  [{T.GRN}]ISO 8601:[/] {datetime.now().isoformat()}')
    console.print(f'  [{T.GRN}]格式化:[/]   {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

    console.print()
    console.print(f'  [{T.PROMPT}]输入时间戳转换 (留空跳过):[/] ', end='')
    ts = input()
    if ts:
        try:
            t = float(ts)
            if t > 1e12: t = t / 1000  # 毫秒转秒
            dt = datetime.fromtimestamp(t)
            console.print(f'  [{T.GRN}]转换结果:[/] {dt.strftime("%Y-%m-%d %H:%M:%S")}')
        except:
            console.print(f'  [{T.ERR}]无效时间戳[/]')

    console.print(f'\n  [{T.DIM}]按任意键返回...[/]')
    wait_key()


def tool_password():
    """随机密码生成"""
    import random
    import string

    clear()
    console.print(Align.center(Text('  ·  随机密码生成  ·  ', style=T.ACCENT)))
    console.print()

    console.print(f'  [{T.PROMPT}]密码长度 (默认 16):[/] ', end='')
    len_input = input()
    length = int(len_input) if len_input.isdigit() else 16
    length = max(4, min(128, length))

    # 生成不同复杂度的密码
    chars_simple = string.ascii_letters + string.digits
    chars_complex = string.ascii_letters + string.digits + '!@#$%^&*()-_=+[]{}|;:,.<>?'

    pw_simple = ''.join(random.choice(chars_simple) for _ in range(length))
    pw_complex = ''.join(random.choice(chars_complex) for _ in range(length))

    console.print()
    console.print(f'  [{T.GRN}]简单 (字母+数字):[/]')
    console.print(f'  {pw_simple}')
    console.print()
    console.print(f'  [{T.GRN}]复杂 (含特殊字符):[/]')
    console.print(f'  {pw_complex}')

    console.print()
    console.print(f'  [{T.DIM}][1] 复制简单  [2] 复制复杂  [R] 重新生成  Esc 返回[/]')

    while True:
        kt, k = read_key()
        if kt == 'esc' or k == 'q': return
        if k == '1':
            try: subprocess.run(['clip'], input=pw_simple.encode(), check=True); console.print(f'  [{T.OK}]已复制[/]')
            except: pass
        if k == '2':
            try: subprocess.run(['clip'], input=pw_complex.encode(), check=True); console.print(f'  [{T.OK}]已复制[/]')
            except: pass
        if k == 'r':
            pw_simple = ''.join(random.choice(chars_simple) for _ in range(length))
            pw_complex = ''.join(random.choice(chars_complex) for _ in range(length))
            clear()
            console.print(Align.center(Text('  ·  随机密码生成  ·  ', style=T.ACCENT)))
            console.print()
            console.print(f'  [{T.GRN}]简单:[/] {pw_simple}')
            console.print(f'  [{T.GRN}]复杂:[/] {pw_complex}')
            console.print()
            console.print(f'  [{T.DIM}][1] 复制简单  [2] 复制复杂  [R] 重新生成  Esc 返回[/]')


def tool_json_format():
    """JSON 格式化"""
    clear()
    console.print(Align.center(Text('  ·  JSON 格式化  ·  ', style=T.ACCENT)))
    console.print()
    console.print(f'  [{T.KEY}][F][/] 格式化  [{T.KEY}][C][/] 压缩  [{T.KEY}][Q][/] 返回')

    kt, k = read_key()
    if kt == 'esc' or k == 'q': return

    console.print(f'\n  [{T.PROMPT}]输入 JSON:[/] ', end='')
    text = input()
    if not text: return

    try:
        obj = json.loads(text)
        if k == 'f':
            formatted = json.dumps(obj, indent=2, ensure_ascii=False)
            console.print(f'\n  [{T.GRN}]格式化结果:[/]')
            for line in formatted.split('\n')[:30]:
                console.print(f'  {line}')
        elif k == 'c':
            compressed = json.dumps(obj, separators=(',', ':'), ensure_ascii=False)
            console.print(f'\n  [{T.GRN}]压缩结果:[/] {compressed}')
    except json.JSONDecodeError as e:
        console.print(f'\n  [{T.ERR}]JSON 错误: {e}[/]')

    console.print(f'\n  [{T.DIM}]按任意键返回...[/]')
    wait_key()


def tool_base_convert():
    """进制转换"""
    clear()
    console.print(Align.center(Text('  ·  进制转换  ·  ', style=T.ACCENT)))
    console.print()

    console.print(f'  [{T.PROMPT}]输入数字:[/] ', end='')
    num_str = input()
    if not num_str: return

    console.print(f'  [{T.PROMPT}]输入进制 (2/8/10/16, 默认 10):[/] ', end='')
    base_str = input()
    base = int(base_str) if base_str.isdigit() else 10

    try:
        num = int(num_str, base)
        console.print()
        console.print(f'  [{T.ACCENT}]转换结果:[/]')
        console.print(f'  [{T.GRN}]二进制:[/]   {bin(num)}')
        console.print(f'  [{T.GRN}]八进制:[/]   {oct(num)}')
        console.print(f'  [{T.GRN}]十进制:[/]   {num}')
        console.print(f'  [{T.GRN}]十六进制:[/] {hex(num)}')
    except ValueError as e:
        console.print(f'\n  [{T.ERR}]转换错误: {e}[/]')

    console.print(f'\n  [{T.DIM}]按任意键返回...[/]')
    wait_key()


def tool_color():
    """颜色代码转换"""
    clear()
    console.print(Align.center(Text('  ·  颜色代码转换  ·  ', style=T.ACCENT)))
    console.print()

    console.print(f'  [{T.PROMPT}]输入 HEX 颜色 (如 #FF6B6B 或 FF6B6B):[/] ', end='')
    hex_input = input().strip().lstrip('#')
    if not hex_input or len(hex_input) != 6:
        console.print(f'  [{T.ERR}]无效颜色代码[/]')
        console.print(f'\n  [{T.DIM}]按任意键返回...[/]')
        wait_key()
        return

    try:
        r = int(hex_input[0:2], 16)
        g = int(hex_input[2:4], 16)
        b = int(hex_input[4:6], 16)

        console.print()
        console.print(f'  [{T.ACCENT}]转换结果:[/]')
        console.print(f'  [{T.GRN}]HEX:[/]  #{hex_input.upper()}')
        console.print(f'  [{T.GRN}]RGB:[/]  rgb({r}, {g}, {b})')
        console.print(f'  [{T.GRN}]RGBA:[/] rgba({r}, {g}, {b}, 1.0)')

        # 颜色预览
        console.print()
        console.print(f'  颜色预览: [on #{hex_input}]      [/] #{hex_input.upper()}')

    except ValueError:
        console.print(f'  [{T.ERR}]无效颜色代码[/]')

    console.print(f'\n  [{T.DIM}]按任意键返回...[/]')
    wait_key()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 命令面板  ·  全局搜索
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def command_palette():
    """全局命令搜索面板"""
    clear()
    console.print(Align.center(Text('  ·  命令面板  ·  ', style=T.ACCENT)))
    console.print()
    console.print(f'  [{T.PROMPT}]搜索命令:[/] ', end='')
    query = input().strip().lower()
    if not query: return

    # 搜索所有可用命令
    all_commands = [
        # Claude Code
        ('Claude Code', '命令速查手册', 'cmd_ref'),
        ('Claude Code', 'CLAUDE.md 生成器', 'gen_claudemd'),
        ('Claude Code', 'CLAUDE.md 编辑器', 'edit_claudemd'),
        ('Claude Code', '项目扫描器', 'scan_project'),
        ('Claude Code', 'Hook 管理器', 'hook_mgr'),
        ('Claude Code', '斜杠命令工厂', 'cmd_factory'),
        ('Claude Code', 'MCP 服务器管理', 'mcp_mgr'),
        ('Claude Code', '配置管理器', 'config_mgr'),
        ('Claude Code', 'Prompt 模板库', 'prompt_lib'),
        ('Claude Code', '最佳实践指南', 'guide'),
        ('Claude Code', '会话管理', 'session_mgr'),
        ('Claude Code', '费用追踪', 'cost_tracker'),
        # Developer tools
        ('开发者工具', 'Git 工具', 'git_tools'),
        ('开发者工具', '文件浏览器', 'file_browser'),
        ('开发者工具', '环境变量', 'env_vars'),
        ('开发者工具', '端口检查器', 'port_checker'),
        ('开发者工具', 'Docker 管理', 'docker_mgr'),
        ('开发者工具', 'JSON 编辑器', 'json_editor'),
        ('开发者工具', '系统信息', 'sys_info'),
        # Productivity
        ('效率工具', '代码片段', 'snippet_mgr'),
        ('效率工具', '任务管理', 'task_mgr'),
        ('效率工具', '笔记本', 'notes'),
        ('效率工具', '书签管理', 'bookmarks'),
        ('效率工具', '命令收藏夹', 'cmd_favorites'),
        # Quick tools
        ('快捷工具', 'UUID 生成器', 'tool_uuid'),
        ('快捷工具', 'Hash 计算器', 'tool_hash'),
        ('快捷工具', 'Base64 编解码', 'tool_base64'),
        ('快捷工具', 'URL 编解码', 'tool_url_encode'),
        ('快捷工具', '正则测试器', 'tool_regex'),
        ('快捷工具', '时间戳工具', 'tool_timestamp'),
        ('快捷工具', '随机密码生成', 'tool_password'),
        ('快捷工具', 'JSON 格式化', 'tool_json_format'),
        ('快捷工具', '进制转换', 'tool_base_convert'),
        ('快捷工具', '颜色代码转换', 'tool_color'),
    ]

    # 搜索匹配
    results = []
    for category, name, func in all_commands:
        if query in name.lower() or query in category.lower():
            results.append((category, name, func))

    if not results:
        console.print(f'\n  [{T.WARN}]未找到匹配 "{query}" 的命令[/]')
        console.print(f'\n  [{T.DIM}]按任意键返回...[/]')
        wait_key()
        return

    # 显示结果
    console.print()
    console.print(f'  [{T.ACCENT}]找到 {len(results)} 个结果:[/]')
    console.print()

    for i, (cat, name, _) in enumerate(results[:15]):
        console.print(f'  [{T.KEY}]{i+1}.[/] [{T.DIM}]{cat}[/] → [{T.LABEL}]{name}[/]')

    console.print()
    console.print(f'  [{T.DIM}]选择编号执行  Esc 返回[/]')

    while True:
        kt, k = read_key()
        if kt == 'esc' or (kt == 'char' and k == 'q'): return
        if kt == 'char' and k.isdigit():
            idx = int(k) - 1
            if 0 <= idx < len(results):
                _, _, func_name = results[idx]
                # 执行对应函数
                _execute_command(func_name)
                return


def _execute_command(func_name):
    """执行命令"""
    try:
        if func_name == 'quick_tools': quick_tools()
        elif func_name == 'tool_uuid': tool_uuid()
        elif func_name == 'tool_hash': tool_hash()
        elif func_name == 'tool_base64': tool_base64()
        elif func_name == 'tool_url_encode': tool_url_encode()
        elif func_name == 'tool_regex': tool_regex()
        elif func_name == 'tool_timestamp': tool_timestamp()
        elif func_name == 'tool_password': tool_password()
        elif func_name == 'tool_json_format': tool_json_format()
        elif func_name == 'tool_base_convert': tool_base_convert()
        elif func_name == 'tool_color': tool_color()
        else:
            # 尝试从其他模块导入
            import importlib
            for mod_name in ['mod_claude', 'mod_devtools', 'mod_productivity', 'mod_cheatsheet']:
                try:
                    mod = importlib.import_module(mod_name)
                    if hasattr(mod, func_name):
                        getattr(mod, func_name)()
                        return
                except: pass
            console.print(f'  [{T.ERR}]未找到命令: {func_name}[/]')
            wait_key()
    except Exception as e:
        console.print(f'  [{T.ERR}]执行错误: {e}[/]')
        wait_key()


def tool_uuid():
    """UUID 生成器别名"""
    uuid_gen = tool_uuid_gen if hasattr(sys.modules[__name__], 'tool_uuid_gen') else quick_tools
    quick_tools()

def tool_uuid_gen():
    """UUID 生成器"""
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# hypervoid.top 博客集成
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def blog_hub():
    """hypervoid.top 博客中心"""
    while True:
        clear()
        console.print(Align.center(Text('  ·  hypervoid.top  ·  ', style=T.ACCENT)))
        console.print()

        items = [
            ('1', ' ', '访问博客', '打开 hypervoid.top'),
            ('2', ' ', 'Claude Code 文档', 'docs.anthropic.com/claude-code'),
            ('3', ' ', 'MCP 服务器仓库', 'github.com/modelcontextprotocol'),
            ('4', ' ', 'Rich 库文档', 'rich.readthedocs.io'),
            ('5', ' ', 'Python 官方文档', 'docs.python.org'),
            ('6', ' ', 'GitHub', 'github.com'),
            ('7', ' ', 'Stack Overflow', 'stackoverflow.com'),
            ('8', ' ', 'MDN Web 文档', 'developer.mozilla.org'),
        ]

        for key, icon, label, url in items:
            console.print(f'   [{T.KEY}][{key}][/] {icon} [{T.LABEL}]{label}[/]')
            console.print(f'        [{T.DIM}]{url}[/]')

        console.print()
        console.print(f'  [{T.DIM}]选择链接在浏览器中打开  Esc 返回[/]')

        kt, k = read_key()
        if kt == 'esc' or k == 'q': return
        urls = {
            '1': 'https://hypervoid.top',
            '2': 'https://docs.anthropic.com/en/docs/claude-code',
            '3': 'https://github.com/modelcontextprotocol/servers',
            '4': 'https://rich.readthedocs.io',
            '5': 'https://docs.python.org',
            '6': 'https://github.com',
            '7': 'https://stackoverflow.com',
            '8': 'https://developer.mozilla.org',
        }
        if k in urls:
            try:
                webbrowser.open(urls[k])
                console.print(f'  [{T.OK}]已打开浏览器[/]')
                time.sleep(1)
            except:
                console.print(f'  [{T.ERR}]无法打开浏览器[/]')
                time.sleep(1)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HYPERVOID 快捷键参考
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def hypervoid_shortcuts():
    """HYPERVOID 快捷键参考"""
    clear()
    console.print(Align.center(Text('  ·  HYPERVOID 快捷键  ·  ', style=T.ACCENT)))
    console.print()

    shortcuts = [
        ('导航', [
            ('↑ / ↓', '上下移动选择'),
            ('Enter', '确认选择'),
            ('Esc / Q', '返回上级'),
            ('1-9, 0', '数字快捷键'),
            ('PgUp / PgDn', '翻页滚动'),
        ]),
        ('全局', [
            ('Ctrl+C', '中断当前操作'),
            ('数字键', '快速选择菜单项'),
        ]),
        ('命令行启动', [
            ('hypervoid', '启动 HYPERVOID'),
            ('python app.py', '直接运行'),
        ]),
        ('文件位置', [
            ('主程序', 'E:\\claude-toolkit\\app.py'),
            ('用户数据', '~\\.claude-toolkit\\data\\'),
            ('Prompt 模板', 'E:\\claude-toolkit\\data\\prompts.json'),
        ]),
    ]

    for section, items in shortcuts:
        console.print(f'  [{T.ACCENT}]{section}[/]')
        for key, desc in items:
            console.print(f'    [{T.KEY}]{key:<20}[/] [{T.DESC}]{desc}[/]')
        console.print()

    console.print(f'  [{T.DIM}]按任意键返回...[/]')
    wait_key()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 最近使用记录
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def record_usage(command_name):
    """记录命令使用"""
    data = load_json('recent.json', [])
    # 移除重复
    data = [d for d in data if d.get('name') != command_name]
    # 添加到开头
    data.insert(0, {'name': command_name, 'time': now_str()})
    # 保留最近 50 条
    data = data[:50]
    save_json('recent.json', data)


def show_recent():
    """显示最近使用记录"""
    data = load_json('recent.json', [])
    if not data:
        console.print(f'\n  [{T.DIM}]暂无使用记录[/]')
        console.print(f'\n  [{T.DIM}]按任意键返回...[/]')
        wait_key()
        return

    clear()
    console.print(Align.center(Text('  ·  最近使用  ·  ', style=T.ACCENT)))
    console.print()

    table = Table(box=box.ROUNDED, border_style=T.BOX, show_lines=False, padding=(0, 1))
    table.add_column('序号', style=T.KEY, width=6)
    table.add_column('命令', style=T.LABEL)
    table.add_column('时间', style=T.DIM)

    for i, item in enumerate(data[:20]):
        table.add_row(str(i+1), item.get('name', ''), item.get('time', ''))

    console.print(Align.center(table))
    console.print()
    console.print(f'  [{T.DIM}]按任意键返回...[/]')
    wait_key()


if __name__ == '__main__':
    quick_tools()
