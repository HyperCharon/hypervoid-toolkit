"""
mod_productivity.py - Productivity tools module
Provides: snippet_mgr, task_mgr, notes, bookmarks, cmd_favorites
"""

import os, json, time, subprocess
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
    CYAN = 'bold bright_cyan'
    MAG = 'bold bright_magenta'
    YEL = 'bold bright_yellow'
    GRN = 'bold bright_green'
    RED = 'bold bright_red'
    WHT = 'bold bright_white'
    ACCENT = 'bold bright_magenta'
    DIM = 'dim bright_white'
    OK = 'bold bright_green'
    WARN = 'bold bright_yellow'
    ERR = 'bold bright_red'
    KEY = 'bold bright_yellow'
    LABEL = 'bold bright_white'
    DESC = 'dim bright_white'
    BOX = 'bright_cyan'


def read_key():
    ch = msvcrt.getch()
    if ch == b'\r':
        return ('enter', '')
    if ch == b'\x1b':
        return ('esc', '')
    if ch == b'\x03':
        raise KeyboardInterrupt
    if ch in (b'\x00', b'\xe0'):
        ch2 = msvcrt.getch()
        m = {b'H': 'up', b'P': 'down', b'K': 'left', b'M': 'right', b'I': 'pgup', b'Q': 'pgdn'}
        return ('nav', m.get(ch2, ''))
    return ('char', ch.decode('utf-8', errors='ignore').lower())


def clear():
    os.system('cls')


def wait_key():
    read_key()


DATA_DIR = Path.home() / '.claude-toolkit' / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_json(name, default=None):
    p = DATA_DIR / name
    if p.exists():
        try:
            return json.loads(p.read_text('utf-8'))
        except:
            pass
    return default if default is not None else []


def save_json(name, data):
    (DATA_DIR / name).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def gen_id():
    return f"{int(time.time()*1000)}"


def now_str():
    return datetime.now().strftime('%Y-%m-%d %H:%M')


# ─────────────────────────────────────────────
# 1. snippet_mgr - Code Snippet Manager
# ─────────────────────────────────────────────

def snippet_mgr():
    """Code snippet manager - store, search, and copy code snippets."""
    while True:
        snippets = load_json('snippets.json', [])
        clear()
        console.print(Align.center(Text("  ═══  代码片段管理  ═══  ", style=T.ACCENT)))
        console.print()

        if not snippets:
            console.print(f"  [{T.DIM}]暂无代码片段[/]")
        else:
            tbl = Table(box=box.SIMPLE, show_header=True, header_style=T.CYAN, padding=(0, 1))
            tbl.add_column('#', style=T.DIM, width=4)
            tbl.add_column('名称', style=T.LABEL)
            tbl.add_column('语言', style=T.MAG)
            tbl.add_column('标签', style=T.YEL)
            tbl.add_column('创建时间', style=T.DIM)
            for i, s in enumerate(snippets, 1):
                tags = ', '.join(s.get('tags', [])) if s.get('tags') else '-'
                tbl.add_row(str(i), s['name'], s.get('language', '-'), tags, s.get('created', '-'))
            console.print(tbl)

        console.print(f"\n  [{T.DIM}]操作: [A]dd [V]iew [C]opy [D]elete [S]earch [Esc]返回[/]")
        console.print(f"  [{T.DIM}]选择序号: 1-{len(snippets)} 直接查看[/]" if snippets else "")

        key, ch = read_key()

        if key == 'esc':
            return

        if ch == 'a':
            # Add snippet
            clear()
            console.print(Align.center(Text("  ═══  添加代码片段  ═══  ", style=T.ACCENT)))
            console.print()
            console.print(f"  [{T.LABEL}]名称:[/] ", end='')
            name = input().strip()
            if not name:
                continue
            console.print(f"  [{T.LABEL}]语言:[/] ", end='')
            lang = input().strip()
            console.print(f"  [{T.LABEL}]标签 (逗号分隔):[/] ", end='')
            tags_raw = input().strip()
            tags = [t.strip() for t in tags_raw.split(',') if t.strip()] if tags_raw else []
            console.print(f"  [{T.LABEL}]输入代码 (输入 END 结束):[/]")
            lines = []
            while True:
                line = input()
                if line.strip() == 'END':
                    break
                lines.append(line)
            code = '\n'.join(lines)
            snippet = {
                'id': gen_id(),
                'name': name,
                'language': lang,
                'code': code,
                'tags': tags,
                'created': now_str()
            }
            snippets.append(snippet)
            save_json('snippets.json', snippets)
            console.print(f"  [{T.OK}]已添加: {name}[/]")
            time.sleep(1)

        elif ch == 's':
            # Search
            clear()
            console.print(Align.center(Text("  ═══  搜索代码片段  ═══  ", style=T.ACCENT)))
            console.print()
            console.print(f"  [{T.LABEL}]搜索关键词 (名称/标签):[/] ", end='')
            kw = input().strip().lower()
            if not kw:
                continue
            results = [s for s in snippets if kw in s['name'].lower() or kw in ' '.join(s.get('tags', [])).lower()]
            clear()
            console.print(Align.center(Text("  ═══  搜索结果  ═══  ", style=T.ACCENT)))
            console.print()
            if not results:
                console.print(f"  [{T.DIM}]未找到匹配的片段[/]")
            else:
                for i, s in enumerate(results, 1):
                    console.print(f"  [{T.KEY}]{i}.[/] [{T.LABEL}]{s['name']}[/] [{T.DIM}]({s.get('language', '-')})[/]")
            console.print()
            console.print(f"  [{T.DIM}]按任意键返回[/]")
            wait_key()

        elif ch == 'v' or (key == 'char' and ch.isdigit()):
            # View snippet
            idx = 0
            if ch == 'v':
                clear()
                console.print(Align.center(Text("  ═══  查看代码片段  ═══  ", style=T.ACCENT)))
                console.print()
                console.print(f"  [{T.LABEL}]输入序号:[/] ", end='')
                try:
                    idx = int(input().strip()) - 1
                except:
                    continue
            else:
                idx = int(ch) - 1
            if 0 <= idx < len(snippets):
                s = snippets[idx]
                clear()
                console.print(Align.center(Text("  ═══  片段详情  ═══  ", style=T.ACCENT)))
                console.print()
                console.print(f"  [{T.LABEL}]名称:[/] {s['name']}")
                console.print(f"  [{T.LABEL}]语言:[/] {s.get('language', '-')}")
                tags = ', '.join(s.get('tags', [])) if s.get('tags') else '-'
                console.print(f"  [{T.LABEL}]标签:[/] {tags}")
                console.print(f"  [{T.LABEL}]创建:[/] {s.get('created', '-')}")
                console.print()
                console.print(Panel(s.get('code', ''), title='代码', border_style=T.BOX, box=box.ROUNDED))
                console.print()
                console.print(f"  [{T.DIM}]按任意键返回[/]")
                wait_key()

        elif ch == 'c':
            # Copy to clipboard
            if not snippets:
                continue
            clear()
            console.print(Align.center(Text("  ═══  复制代码片段  ═══  ", style=T.ACCENT)))
            console.print()
            for i, s in enumerate(snippets, 1):
                console.print(f"  [{T.KEY}]{i}.[/] [{T.LABEL}]{s['name']}[/]")
            console.print()
            console.print(f"  [{T.LABEL}]输入序号:[/] ", end='')
            try:
                idx = int(input().strip()) - 1
            except:
                continue
            if 0 <= idx < len(snippets):
                code = snippets[idx].get('code', '')
                try:
                    subprocess.run(['clip'], input=code.encode('utf-16le'), check=True)
                    console.print(f"  [{T.OK}]已复制到剪贴板[/]")
                except Exception as e:
                    console.print(f"  [{T.ERR}]复制失败: {e}[/]")
                time.sleep(1)

        elif ch == 'd':
            # Delete snippet
            if not snippets:
                continue
            clear()
            console.print(Align.center(Text("  ═══  删除代码片段  ═══  ", style=T.ACCENT)))
            console.print()
            for i, s in enumerate(snippets, 1):
                console.print(f"  [{T.KEY}]{i}.[/] [{T.LABEL}]{s['name']}[/]")
            console.print()
            console.print(f"  [{T.LABEL}]输入序号:[/] ", end='')
            try:
                idx = int(input().strip()) - 1
            except:
                continue
            if 0 <= idx < len(snippets):
                removed = snippets.pop(idx)
                save_json('snippets.json', snippets)
                console.print(f"  [{T.OK}]已删除: {removed['name']}[/]")
                time.sleep(1)


# ─────────────────────────────────────────────
# 2. task_mgr - Task Manager
# ─────────────────────────────────────────────

def task_mgr():
    """Task manager - track tasks with priorities and completion status."""
    while True:
        tasks = load_json('tasks.json', [])
        clear()
        console.print(Align.center(Text("  ═══  任务管理  ═══  ", style=T.ACCENT)))
        console.print()

        total = len(tasks)
        done = sum(1 for t in tasks if t.get('done'))
        pending = total - done
        console.print(f"  [{T.DIM}]总计: {total}  已完成: {done}  待办: {pending}[/]")
        console.print()

        if not tasks:
            console.print(f"  [{T.DIM}]暂无任务[/]")
        else:
            tbl = Table(box=box.SIMPLE, show_header=True, header_style=T.CYAN, padding=(0, 1))
            tbl.add_column('#', style=T.DIM, width=4)
            tbl.add_column('状态', width=4)
            tbl.add_column('任务', style=T.LABEL)
            tbl.add_column('优先级', width=8)
            tbl.add_column('创建时间', style=T.DIM)
            for i, t in enumerate(tasks, 1):
                status = Text('✔', style=T.OK) if t.get('done') else Text('✖', style=T.ERR)
                pri = t.get('priority', 'med')
                if pri == 'high':
                    pri_text = Text('高', style=T.RED)
                elif pri == 'low':
                    pri_text = Text('低', style=T.DIM)
                else:
                    pri_text = Text('中', style=T.YEL)
                tbl.add_row(str(i), status, t['text'], pri_text, t.get('created', '-'))
            console.print(tbl)

        console.print(f"\n  [{T.DIM}]操作: [A]dd [T]oggle [D]elete [S]tats [Esc]返回[/]")

        key, ch = read_key()

        if key == 'esc':
            return

        if ch == 'a':
            # Add task
            clear()
            console.print(Align.center(Text("  ═══  添加任务  ═══  ", style=T.ACCENT)))
            console.print()
            console.print(f"  [{T.LABEL}]任务内容:[/] ", end='')
            text = input().strip()
            if not text:
                continue
            console.print(f"  [{T.LABEL}]优先级 ([H]高 / [M]中 / [L]低):[/] ", end='')
            pri_input = input().strip().lower()
            if pri_input in ('h', 'high'):
                pri = 'high'
            elif pri_input in ('l', 'low'):
                pri = 'low'
            else:
                pri = 'med'
            task = {
                'id': gen_id(),
                'text': text,
                'done': False,
                'priority': pri,
                'created': now_str()
            }
            tasks.append(task)
            save_json('tasks.json', tasks)
            console.print(f"  [{T.OK}]已添加任务[/]")
            time.sleep(1)

        elif ch == 't':
            # Toggle done/undone
            if not tasks:
                continue
            clear()
            console.print(Align.center(Text("  ═══  切换任务状态  ═══  ", style=T.ACCENT)))
            console.print()
            for i, t in enumerate(tasks, 1):
                status = '✔' if t.get('done') else '✖'
                console.print(f"  [{T.KEY}]{i}.[/] {status} [{T.LABEL}]{t['text']}[/]")
            console.print()
            console.print(f"  [{T.LABEL}]输入序号:[/] ", end='')
            try:
                idx = int(input().strip()) - 1
            except:
                continue
            if 0 <= idx < len(tasks):
                tasks[idx]['done'] = not tasks[idx].get('done', False)
                save_json('tasks.json', tasks)
                state = '已完成' if tasks[idx]['done'] else '未完成'
                console.print(f"  [{T.OK}]已标记为: {state}[/]")
                time.sleep(1)

        elif ch == 'd':
            # Delete task
            if not tasks:
                continue
            clear()
            console.print(Align.center(Text("  ═══  删除任务  ═══  ", style=T.ACCENT)))
            console.print()
            for i, t in enumerate(tasks, 1):
                status = '✔' if t.get('done') else '✖'
                console.print(f"  [{T.KEY}]{i}.[/] {status} [{T.LABEL}]{t['text']}[/]")
            console.print()
            console.print(f"  [{T.LABEL}]输入序号:[/] ", end='')
            try:
                idx = int(input().strip()) - 1
            except:
                continue
            if 0 <= idx < len(tasks):
                removed = tasks.pop(idx)
                save_json('tasks.json', tasks)
                console.print(f"  [{T.OK}]已删除: {removed['text']}[/]")
                time.sleep(1)

        elif ch == 's':
            # Stats
            clear()
            console.print(Align.center(Text("  ═══  任务统计  ═══  ", style=T.ACCENT)))
            console.print()
            high = sum(1 for t in tasks if t.get('priority') == 'high' and not t.get('done'))
            med = sum(1 for t in tasks if t.get('priority') == 'med' and not t.get('done'))
            low = sum(1 for t in tasks if t.get('priority') == 'low' and not t.get('done'))
            console.print(f"  [{T.LABEL}]总任务:[/] {total}")
            console.print(f"  [{T.OK}]已完成:[/] {done}")
            console.print(f"  [{T.WARN}]待处理:[/] {pending}")
            console.print()
            console.print(f"  [{T.DIM}]待办优先级分布:[/]")
            console.print(f"    [{T.RED}]高优先级:[/] {high}")
            console.print(f"    [{T.YEL}]中优先级:[/] {med}")
            console.print(f"    [{T.DIM}]低优先级:[/] {low}")
            if total > 0:
                pct = int(done / total * 100)
                console.print()
                console.print(f"  [{T.LABEL}]完成率:[/] {pct}%")
                bar_len = 30
                filled = int(bar_len * done / total)
                bar = '█' * filled + '░' * (bar_len - filled)
                console.print(f"  [{T.OK}]{bar}[/]")
            console.print()
            console.print(f"  [{T.DIM}]按任意键返回[/]")
            wait_key()


# ─────────────────────────────────────────────
# 3. notes - Notebook
# ─────────────────────────────────────────────

def notes():
    """Notebook - create, view, edit, and manage notes."""
    while True:
        note_list = load_json('notes.json', [])
        clear()
        console.print(Align.center(Text("  ═══  笔记本  ═══  ", style=T.ACCENT)))
        console.print()

        if not note_list:
            console.print(f"  [{T.DIM}]暂无笔记[/]")
        else:
            tbl = Table(box=box.SIMPLE, show_header=True, header_style=T.CYAN, padding=(0, 1))
            tbl.add_column('#', style=T.DIM, width=4)
            tbl.add_column('标题', style=T.LABEL)
            tbl.add_column('内容预览', style=T.DESC, max_width=40)
            tbl.add_column('创建时间', style=T.DIM)
            tbl.add_column('更新时间', style=T.DIM)
            for i, n in enumerate(note_list, 1):
                preview = n.get('content', '')[:40]
                if len(n.get('content', '')) > 40:
                    preview += '...'
                tbl.add_row(str(i), n['title'], preview, n.get('created', '-'), n.get('updated', '-'))
            console.print(tbl)

        console.print(f"\n  [{T.DIM}]操作: [A]dd [V]iew [E]dit [D]elete [Esc]返回[/]")

        key, ch = read_key()

        if key == 'esc':
            return

        if ch == 'a':
            # Add note
            clear()
            console.print(Align.center(Text("  ═══  添加笔记  ═══  ", style=T.ACCENT)))
            console.print()
            console.print(f"  [{T.LABEL}]标题:[/] ", end='')
            title = input().strip()
            if not title:
                continue
            console.print(f"  [{T.LABEL}]内容 (输入 END 结束):[/]")
            lines = []
            while True:
                line = input()
                if line.strip() == 'END':
                    break
                lines.append(line)
            content = '\n'.join(lines)
            note = {
                'id': gen_id(),
                'title': title,
                'content': content,
                'created': now_str(),
                'updated': now_str()
            }
            note_list.append(note)
            save_json('notes.json', note_list)
            console.print(f"  [{T.OK}]已添加笔记: {title}[/]")
            time.sleep(1)

        elif ch == 'v':
            # View note
            if not note_list:
                continue
            clear()
            console.print(Align.center(Text("  ═══  查看笔记  ═══  ", style=T.ACCENT)))
            console.print()
            for i, n in enumerate(note_list, 1):
                console.print(f"  [{T.KEY}]{i}.[/] [{T.LABEL}]{n['title']}[/]")
            console.print()
            console.print(f"  [{T.LABEL}]输入序号:[/] ", end='')
            try:
                idx = int(input().strip()) - 1
            except:
                continue
            if 0 <= idx < len(note_list):
                n = note_list[idx]
                clear()
                console.print(Align.center(Text("  ═══  笔记详情  ═══  ", style=T.ACCENT)))
                console.print()
                console.print(f"  [{T.LABEL}]标题:[/] {n['title']}")
                console.print(f"  [{T.LABEL}]创建:[/] {n.get('created', '-')}")
                console.print(f"  [{T.LABEL}]更新:[/] {n.get('updated', '-')}")
                console.print()
                console.print(Panel(n.get('content', '(空)'), title='内容', border_style=T.BOX, box=box.ROUNDED))
                console.print()
                console.print(f"  [{T.DIM}]按任意键返回[/]")
                wait_key()

        elif ch == 'e':
            # Edit note
            if not note_list:
                continue
            clear()
            console.print(Align.center(Text("  ═══  编辑笔记  ═══  ", style=T.ACCENT)))
            console.print()
            for i, n in enumerate(note_list, 1):
                console.print(f"  [{T.KEY}]{i}.[/] [{T.LABEL}]{n['title']}[/]")
            console.print()
            console.print(f"  [{T.LABEL}]输入序号:[/] ", end='')
            try:
                idx = int(input().strip()) - 1
            except:
                continue
            if 0 <= idx < len(note_list):
                console.print(f"  [{T.LABEL}]编辑方式 ([R]替换 / [A]追加):[/] ", end='')
                mode = input().strip().lower()
                console.print(f"  [{T.LABEL}]输入内容 (输入 END 结束):[/]")
                lines = []
                while True:
                    line = input()
                    if line.strip() == 'END':
                        break
                    lines.append(line)
                new_content = '\n'.join(lines)
                if mode == 'a':
                    old = note_list[idx].get('content', '')
                    note_list[idx]['content'] = old + '\n' + new_content if old else new_content
                else:
                    note_list[idx]['content'] = new_content
                note_list[idx]['updated'] = now_str()
                save_json('notes.json', note_list)
                console.print(f"  [{T.OK}]已更新笔记[/]")
                time.sleep(1)

        elif ch == 'd':
            # Delete note
            if not note_list:
                continue
            clear()
            console.print(Align.center(Text("  ═══  删除笔记  ═══  ", style=T.ACCENT)))
            console.print()
            for i, n in enumerate(note_list, 1):
                console.print(f"  [{T.KEY}]{i}.[/] [{T.LABEL}]{n['title']}[/]")
            console.print()
            console.print(f"  [{T.LABEL}]输入序号:[/] ", end='')
            try:
                idx = int(input().strip()) - 1
            except:
                continue
            if 0 <= idx < len(note_list):
                removed = note_list.pop(idx)
                save_json('notes.json', note_list)
                console.print(f"  [{T.OK}]已删除: {removed['title']}[/]")
                time.sleep(1)


# ─────────────────────────────────────────────
# 4. bookmarks - Bookmark Manager
# ─────────────────────────────────────────────

_DEFAULT_BOOKMARKS = [
    {"name": "hypervoid.top", "url": "https://hypervoid.top", "category": "Blog", "desc": "个人博客"},
    {"name": "Claude Code Docs", "url": "https://docs.anthropic.com/en/docs/claude-code", "category": "AI", "desc": "Claude Code 官方文档"},
    {"name": "MCP Servers", "url": "https://github.com/modelcontextprotocol/servers", "category": "AI", "desc": "MCP 服务器仓库"},
    {"name": "Rich Docs", "url": "https://rich.readthedocs.io", "category": "Python", "desc": "Rich 库文档"},
    {"name": "GitHub", "url": "https://github.com", "category": "Dev", "desc": "代码托管平台"},
]


def bookmarks():
    """Bookmark manager - organize and open URLs by category."""
    import webbrowser
    while True:
        bm_list = load_json('bookmarks.json', None)
        # Pre-populate defaults on first run (empty / missing file)
        if bm_list is None or (isinstance(bm_list, list) and len(bm_list) == 0):
            bm_list = [dict(bm, id=gen_id(), created=now_str()) for bm in _DEFAULT_BOOKMARKS]
            save_json('bookmarks.json', bm_list)
        clear()
        console.print(Align.center(Text("  ═══  书签管理  ═══  ", style=T.ACCENT)))
        console.print()

        if not bm_list:
            console.print(f"  [{T.DIM}]暂无书签[/]")
        else:
            # Group by category
            categories = {}
            for bm in bm_list:
                cat = bm.get('category', '未分类')
                categories.setdefault(cat, []).append(bm)

            for cat, items in categories.items():
                console.print(f"  [{T.MAG}]── {cat} ──[/]")
                tbl = Table(box=box.SIMPLE, show_header=True, header_style=T.CYAN, padding=(0, 1))
                tbl.add_column('#', style=T.DIM, width=4)
                tbl.add_column('名称', style=T.LABEL)
                tbl.add_column('URL', style=T.DIM, max_width=50)
                tbl.add_column('说明', style=T.DESC, max_width=30)
                for bm in items:
                    global_idx = bm_list.index(bm) + 1
                    tbl.add_row(str(global_idx), bm['name'], bm.get('url', '-'), bm.get('desc', '-'))
                console.print(tbl)
                console.print()

        console.print(f"  [{T.DIM}]操作: [A]dd [O]pen [D]elete [S]earch [Esc]返回[/]")

        key, ch = read_key()

        if key == 'esc':
            return

        if ch == 'a':
            # Add bookmark
            clear()
            console.print(Align.center(Text("  ═══  添加书签  ═══  ", style=T.ACCENT)))
            console.print()
            console.print(f"  [{T.LABEL}]名称:[/] ", end='')
            name = input().strip()
            if not name:
                continue
            console.print(f"  [{T.LABEL}]URL:[/] ", end='')
            url = input().strip()
            console.print(f"  [{T.LABEL}]分类:[/] ", end='')
            category = input().strip() or '未分类'
            console.print(f"  [{T.LABEL}]说明:[/] ", end='')
            desc = input().strip()
            bm = {
                'id': gen_id(),
                'name': name,
                'url': url,
                'category': category,
                'desc': desc,
                'created': now_str()
            }
            bm_list.append(bm)
            save_json('bookmarks.json', bm_list)
            console.print(f"  [{T.OK}]已添加书签: {name}[/]")
            time.sleep(1)

        elif ch == 'o':
            # Open in browser
            if not bm_list:
                continue
            clear()
            console.print(Align.center(Text("  ═══  打开书签  ═══  ", style=T.ACCENT)))
            console.print()
            for i, bm in enumerate(bm_list, 1):
                console.print(f"  [{T.KEY}]{i}.[/] [{T.LABEL}]{bm['name']}[/] [{T.DIM}]{bm.get('url', '')}[/]")
            console.print()
            console.print(f"  [{T.LABEL}]输入序号:[/] ", end='')
            try:
                idx = int(input().strip()) - 1
            except:
                continue
            if 0 <= idx < len(bm_list):
                url = bm_list[idx].get('url', '')
                if url:
                    try:
                        webbrowser.open(url)
                        console.print(f"  [{T.OK}]已打开: {url}[/]")
                    except Exception as e:
                        console.print(f"  [{T.ERR}]打开失败: {e}[/]")
                else:
                    console.print(f"  [{T.WARN}]该书签没有URL[/]")
                time.sleep(1)

        elif ch == 'd':
            # Delete bookmark
            if not bm_list:
                continue
            clear()
            console.print(Align.center(Text("  ═══  删除书签  ═══  ", style=T.ACCENT)))
            console.print()
            for i, bm in enumerate(bm_list, 1):
                console.print(f"  [{T.KEY}]{i}.[/] [{T.LABEL}]{bm['name']}[/] [{T.DIM}]{bm.get('url', '')}[/]")
            console.print()
            console.print(f"  [{T.LABEL}]输入序号:[/] ", end='')
            try:
                idx = int(input().strip()) - 1
            except:
                continue
            if 0 <= idx < len(bm_list):
                removed = bm_list.pop(idx)
                save_json('bookmarks.json', bm_list)
                console.print(f"  [{T.OK}]已删除: {removed['name']}[/]")
                time.sleep(1)

        elif ch == 's':
            # Search
            clear()
            console.print(Align.center(Text("  ═══  搜索书签  ═══  ", style=T.ACCENT)))
            console.print()
            console.print(f"  [{T.LABEL}]搜索关键词 (名称/URL):[/] ", end='')
            kw = input().strip().lower()
            if not kw:
                continue
            results = [bm for bm in bm_list if kw in bm['name'].lower() or kw in bm.get('url', '').lower()]
            clear()
            console.print(Align.center(Text("  ═══  搜索结果  ═══  ", style=T.ACCENT)))
            console.print()
            if not results:
                console.print(f"  [{T.DIM}]未找到匹配的书签[/]")
            else:
                for i, bm in enumerate(results, 1):
                    console.print(f"  [{T.KEY}]{i}.[/] [{T.LABEL}]{bm['name']}[/] [{T.DIM}]{bm.get('url', '')}[/]")
                    if bm.get('desc'):
                        console.print(f"     [{T.DESC}]{bm['desc']}[/]")
            console.print()
            console.print(f"  [{T.DIM}]按任意键返回[/]")
            wait_key()


# ─────────────────────────────────────────────
# 5. cmd_favorites - Command Favorites
# ─────────────────────────────────────────────

_DEFAULT_CMD_FAVORITES = [
    {"command": "claude", "desc": "启动 Claude Code", "category": "AI", "used_count": 0},
    {"command": "git status", "desc": "查看 git 状态", "category": "Git", "used_count": 0},
    {"command": "npm run dev", "desc": "启动开发服务器", "category": "Node", "used_count": 0},
    {"command": "docker ps", "desc": "查看运行中的容器", "category": "Docker", "used_count": 0},
]


def cmd_favorites():
    """Command favorites - save, organize, and quickly copy frequently used commands."""
    while True:
        cmds = load_json('cmd_favorites.json', None)
        # Pre-populate defaults on first run (empty / missing file)
        if cmds is None or (isinstance(cmds, list) and len(cmds) == 0):
            cmds = [dict(c, id=gen_id()) for c in _DEFAULT_CMD_FAVORITES]
            save_json('cmd_favorites.json', cmds)
        clear()
        console.print(Align.center(Text("  ═══  命令收藏夹  ═══  ", style=T.ACCENT)))
        console.print()

        if not cmds:
            console.print(f"  [{T.DIM}]暂无收藏命令[/]")
        else:
            tbl = Table(box=box.SIMPLE, show_header=True, header_style=T.CYAN, padding=(0, 1))
            tbl.add_column('#', style=T.DIM, width=4)
            tbl.add_column('命令', style=T.LABEL, max_width=50)
            tbl.add_column('说明', style=T.DESC)
            tbl.add_column('分类', style=T.MAG)
            tbl.add_column('使用次数', style=T.YEL, width=8)
            for i, c in enumerate(cmds, 1):
                tbl.add_row(str(i), c['command'], c.get('desc', '-'), c.get('category', '-'), str(c.get('used_count', 0)))
            console.print(tbl)

        console.print(f"\n  [{T.DIM}]操作: [A]dd [C]opy [D]elete [Esc]返回[/]")

        key, ch = read_key()

        if key == 'esc':
            return

        if ch == 'a':
            # Add command
            clear()
            console.print(Align.center(Text("  ═══  添加命令  ═══  ", style=T.ACCENT)))
            console.print()
            console.print(f"  [{T.LABEL}]命令:[/] ", end='')
            command = input().strip()
            if not command:
                continue
            console.print(f"  [{T.LABEL}]说明:[/] ", end='')
            desc = input().strip()
            console.print(f"  [{T.LABEL}]分类:[/] ", end='')
            category = input().strip() or '通用'
            cmd = {
                'id': gen_id(),
                'command': command,
                'desc': desc,
                'category': category,
                'used_count': 0
            }
            cmds.append(cmd)
            save_json('cmd_favorites.json', cmds)
            console.print(f"  [{T.OK}]已添加命令[/]")
            time.sleep(1)

        elif ch == 'c':
            # Copy command to clipboard
            if not cmds:
                continue
            clear()
            console.print(Align.center(Text("  ═══  复制命令  ═══  ", style=T.ACCENT)))
            console.print()
            for i, c in enumerate(cmds, 1):
                console.print(f"  [{T.KEY}]{i}.[/] [{T.LABEL}]{c['command']}[/] [{T.DIM}]({c.get('desc', '')})[/]")
            console.print()
            console.print(f"  [{T.LABEL}]输入序号:[/] ", end='')
            try:
                idx = int(input().strip()) - 1
            except:
                continue
            if 0 <= idx < len(cmds):
                command = cmds[idx]['command']
                try:
                    subprocess.run(['clip'], input=command.encode('utf-16le'), check=True)
                    cmds[idx]['used_count'] = cmds[idx].get('used_count', 0) + 1
                    save_json('cmd_favorites.json', cmds)
                    console.print(f"  [{T.OK}]已复制到剪贴板 (使用次数: {cmds[idx]['used_count']})[/]")
                except Exception as e:
                    console.print(f"  [{T.ERR}]复制失败: {e}[/]")
                time.sleep(1)

        elif ch == 'd':
            # Delete command
            if not cmds:
                continue
            clear()
            console.print(Align.center(Text("  ═══  删除命令  ═══  ", style=T.ACCENT)))
            console.print()
            for i, c in enumerate(cmds, 1):
                console.print(f"  [{T.KEY}]{i}.[/] [{T.LABEL}]{c['command']}[/] [{T.DIM}]({c.get('desc', '')})[/]")
            console.print()
            console.print(f"  [{T.LABEL}]输入序号:[/] ", end='')
            try:
                idx = int(input().strip()) - 1
            except:
                continue
            if 0 <= idx < len(cmds):
                removed = cmds.pop(idx)
                save_json('cmd_favorites.json', cmds)
                console.print(f"  [{T.OK}]已删除: {removed['command']}[/]")
                time.sleep(1)


# ─────────────────────────────────────────────
# Main entry point for standalone testing
# ─────────────────────────────────────────────

def main():
    """Interactive menu to launch productivity tools."""
    tools = [
        ('1', 'snippet_mgr', '代码片段管理', snippet_mgr),
        ('2', 'task_mgr', '任务管理', task_mgr),
        ('3', 'notes', '笔记本', notes),
        ('4', 'bookmarks', '书签管理', bookmarks),
        ('5', 'cmd_favorites', '命令收藏夹', cmd_favorites),
    ]
    while True:
        clear()
        console.print(Align.center(Text("  ═══  HYPERVOID 生产力工具箱  ═══  ", style=T.ACCENT)))
        console.print()
        for num, _, desc, _ in tools:
            console.print(f"  [{T.KEY}]{num}.[/] [{T.LABEL}]{desc}[/]")
        console.print()
        console.print(f"  [{T.DIM}]选择工具 (1-5) 或 [Esc] 退出[/]")

        key, ch = read_key()
        if key == 'esc':
            return
        if key == 'char' and ch.isdigit():
            for num, _, _, func in tools:
                if ch == num:
                    func()
                    break


if __name__ == '__main__':
    main()
