"""
HYPERVOID - 个人开发工作站
打造极致开发体验 · hypervoid.top
跨平台支持: Windows / Linux / macOS
"""
import sys
from pathlib import Path

# ── 路径设置 ──────────────────────────────────────────────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# ── 导入共享 TUI 组件 ────────────────────────────────────
from tui_utils import (
    console, T, IS_WINDOWS,
    read_key, wait_key, clear,
    load_json, save_json, now_str,
    draw_header, draw_logo, draw_stars, draw_status_bar, draw_project_info,
    menu, scroll_view, show_table, show_ok, show_err,
    Group, Panel, Table, Text, Align, box,
)

# ── 导入功能模块 ──────────────────────────────────────────
from mod_claude import (
    cmd_ref, gen_claudemd, edit_claudemd, scan_project, session_mgr, cost_tracker,
    hook_mgr, cmd_factory, mcp_mgr, config_mgr, prompt_lib, guide
)
from mod_devtools import git_tools, file_browser, env_vars, port_checker, docker_mgr, json_editor, sys_info
from mod_productivity import snippet_mgr, task_mgr, notes, bookmarks, cmd_favorites
from mod_cheatsheet import cheatsheet_menu
from mod_extras import quick_tools, command_palette, blog_hub, hypervoid_shortcuts, show_recent, record_usage


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 分类菜单
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def menu_claude():
    while True:
        items = [
            {'key':'1','icon':' ','label':'命令速查手册','desc':'所有 Claude Code 命令一览'},
            {'key':'2','icon':' ','label':'CLAUDE.md 生成器','desc':'交互式生成项目配置文件'},
            {'key':'3','icon':' ','label':'CLAUDE.md 编辑器','desc':'查看 / 编辑 / 重新生成'},
            {'key':'4','icon':' ','label':'项目扫描器','desc':'自动检测技术栈并生成配置'},
            {'key':'5','icon':' ','label':'Hook 管理器','desc':'创建和管理自动化钩子'},
            {'key':'6','icon':' ','label':'斜杠命令工厂','desc':'自定义命令模板'},
            {'key':'7','icon':' ','label':'MCP 服务器管理','desc':'连接外部工具和数据源'},
            {'key':'8','icon':' ','label':'配置管理器','desc':'管理 settings.json 和权限'},
            {'key':'9','icon':' ','label':'Prompt 模板库','desc':'精选提示词模板'},
            {'key':'0','icon':' ','label':'最佳实践指南','desc':'学习 Claude Code 技巧'},
            {'key':'s','icon':' ','label':'会话管理','desc':'查看和恢复历史会话'},
            {'key':'c','icon':' ','label':'费用追踪','desc':'查看 Token 用量和费用'},
        ]
        sel = menu(items, 'Claude Code 工具', '↑↓ 导航  Enter 选择  Esc 返回')
        if sel < 0: return
        k = items[sel]['key']
        if   k=='1': cmd_ref()
        elif k=='2': gen_claudemd()
        elif k=='3': edit_claudemd()
        elif k=='4': scan_project()
        elif k=='5': hook_mgr()
        elif k=='6': cmd_factory()
        elif k=='7': mcp_mgr()
        elif k=='8': config_mgr()
        elif k=='9': prompt_lib()
        elif k=='0': guide()
        elif k=='s': session_mgr()
        elif k=='c': cost_tracker()


def menu_devtools():
    while True:
        items = [
            {'key':'1','icon':' ','label':'Git 工具','desc':'status / log / diff / branch 可视化'},
            {'key':'2','icon':' ','label':'文件浏览器','desc':'目录导航和文件预览'},
            {'key':'3','icon':' ','label':'环境变量','desc':'查看和管理系统环境变量'},
            {'key':'4','icon':' ','label':'端口检查器','desc':'查看占用端口的进程'},
            {'key':'5','icon':' ','label':'Docker 管理','desc':'容器 / 镜像 / 数据卷管理'},
            {'key':'6','icon':' ','label':'JSON 编辑器','desc':'格式化 / 验证 / 编辑 JSON'},
            {'key':'7','icon':' ','label':'系统信息','desc':'OS / CPU / 内存 / 磁盘信息'},
        ]
        sel = menu(items, '开发者工具箱', '↑↓ 导航  Enter 选择  Esc 返回')
        if sel < 0: return
        k = items[sel]['key']
        if   k=='1': git_tools()
        elif k=='2': file_browser()
        elif k=='3': env_vars()
        elif k=='4': port_checker()
        elif k=='5': docker_mgr()
        elif k=='6': json_editor()
        elif k=='7': sys_info()


def menu_productivity():
    while True:
        items = [
            {'key':'1','icon':' ','label':'代码片段','desc':'保存和管理常用代码片段'},
            {'key':'2','icon':' ','label':'任务管理','desc':'Todo 列表与进度追踪'},
            {'key':'3','icon':' ','label':'笔记本','desc':'快速记录和检索笔记'},
            {'key':'4','icon':' ','label':'书签管理','desc':'保存常用 URL 和文档'},
            {'key':'5','icon':' ','label':'命令收藏夹','desc':'收藏和复用常用命令'},
        ]
        sel = menu(items, '效率工具', '↑↓ 导航  Enter 选择  Esc 返回')
        if sel < 0: return
        k = items[sel]['key']
        if   k=='1': snippet_mgr()
        elif k=='2': task_mgr()
        elif k=='3': notes()
        elif k=='4': bookmarks()
        elif k=='5': cmd_favorites()


def menu_extras():
    while True:
        items = [
            {'key':'1','icon':' ','label':'快捷工具箱','desc':'UUID · Hash · Base64 · URL · 正则 · 密码 · 进制 · 颜色'},
            {'key':'2','icon':' ','label':'命令面板','desc':'全局搜索所有功能'},
            {'key':'3','icon':' ','label':'hypervoid.top','desc':'博客 · 文档 · 资源链接'},
            {'key':'4','icon':' ','label':'最近使用','desc':'查看最近使用过的功能'},
            {'key':'5','icon':' ','label':'快捷键参考','desc':'HYPERVOID 操作指南'},
        ]
        sel = menu(items, '扩展功能', '↑↓ 导航  Enter 选择  Esc 返回')
        if sel < 0: return
        k = items[sel]['key']
        if   k=='1': quick_tools()
        elif k=='2': command_palette()
        elif k=='3': blog_hub()
        elif k=='4': show_recent()
        elif k=='5': hypervoid_shortcuts()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 主菜单
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MAIN = [
    {'key':'1','icon':' ','label':'Claude Code','desc':'命令速查 · CLAUDE.md · Hook · MCP · 配置 · Prompt 模板', 'fn': menu_claude},
    {'key':'2','icon':' ','label':'开发者工具','desc':'Git 可视化 · 文件浏览 · 环境变量 · Docker · 系统信息', 'fn': menu_devtools},
    {'key':'3','icon':' ','label':'效率工具','desc':'代码片段 · 任务管理 · 笔记本 · 书签 · 命令收藏', 'fn': menu_productivity},
    {'key':'4','icon':' ','label':'速查表','desc':'Git · Docker · NPM · Regex · Python · VSCode · Linux · K8S · PowerShell', 'fn': cheatsheet_menu},
    {'key':'5','icon':' ','label':'扩展功能','desc':'快捷工具 · 命令面板 · 博客 · 最近使用 · 快捷键', 'fn': menu_extras},
]


def main():
    try:
        while True:
            sel = menu(MAIN, '主菜单', '↑↓ 导航  Enter 选择  Q 退出')
            if sel < 0: break
            try: record_usage(MAIN[sel]['label'])
            except: pass
            MAIN[sel]['fn']()
        clear()
        console.print()
        console.print(Align.center(Text('  ·  HYPERVOID  ·', style=T.ACCENT)))
        console.print()
        console.print(Align.center(Text('感谢使用  ·  hypervoid.top', style=T.DIM)))
        console.print()
    except KeyboardInterrupt:
        clear()
        console.print("\n  再见！")


if __name__ == '__main__':
    main()
