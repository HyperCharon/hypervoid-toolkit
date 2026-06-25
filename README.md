# HYPERVOID

> 个人开发工作站 · hypervoid.top

一个基于 Python + Rich 的精美终端 TUI 工具，为 Claude Code CLI 用户打造。

## ✨ 特性

- 🎨 **宇宙星空主题** - 深蓝配色 + 渐变 Logo
- ⚡ **无闪烁刷新** - Rich Live 显示技术
- 🖥️ **跨平台支持** - Windows / Linux / macOS
- 📦 **模块化设计** - 8 个独立功能模块，123 个函数

## 🚀 快速开始

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/hypervoid.git
cd hypervoid

# 安装依赖
pip install rich

# 运行
python app.py
```

### Windows 快捷安装

```powershell
# 运行安装脚本（创建桌面快捷方式 + PowerShell 命令）
.\install.ps1

# 之后可以直接使用
hypervoid
```

## 📦 功能模块

### 1. Claude Code 工具 (34 函数)
- 命令速查手册
- CLAUDE.md 生成器 / 编辑器
- 项目扫描器
- Hook 管理器
- 斜杠命令工厂
- MCP 服务器管理
- 配置管理器
- Prompt 模板库
- 最佳实践指南
- 会话管理 / 费用追踪

### 2. 开发者工具箱 (22 函数)
- Git 可视化工具
- 文件浏览器
- 环境变量管理
- 端口检查器
- Docker 管理
- JSON 编辑器
- 系统信息

### 3. 效率工具 (22 函数)
- 代码片段管理
- 任务管理 (Todo)
- 笔记本
- 书签管理
- 命令收藏夹

### 4. 速查表 (10 大类)
- Git / Docker / NPM / Regex
- Python / VS Code / Markdown / Linux
- Kubernetes / PowerShell

### 5. 扩展功能 (35 函数)
- 快捷工具箱 (UUID/Hash/Base64/URL/正则/密码/进制/颜色)
- 命令面板 (全局搜索)
- hypervoid.top 博客集成
- 最近使用记录
- 快捷键参考

## 🎨 界面预览

```
◆ ━━━ ✦ ━━━ HYPERVOID ━━━━━━━━━━━━━━━━━ hypervoid.top  20:30 ━━━ ✦ ━━━ ◆

██  ██ ██╗   ██╗██████╗ ███████╗██████╗ ██╗   ██╗ ██████╗ ██╗██████╗
██████ ╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗██║   ██║██╔═══██╗██║██╔══██╗
██  ██  ╚████╔╝ ██████╔╝█████╗  ██████╔╝██║   ██║██║   ██║██║██║  ██║
██████   ╚██╔╝  ██╔═══╝ ██╔══╝  ██╔══██╗╚██╗ ██╔╝██║   ██║██║██║  ██║
██  ██    ██║   ██║     ███████╗██║  ██║ ╚████╔╝ ╚██████╔╝██║██████╔╝
╚╝  ╚╝    ╚═╝   ╚═╝     ╚══════╝╚═╝  ╚═╝  ╚═══╝   ╚═════╝ ╚═╝╚═════╝

            ·  个人开发工作站  ·  hypervoid.top  ·

  📁 my-project (main)  │  ✔ CLAUDE.md  ✔ settings  │  API ✔

  ◆ 主菜单

  ▸ [1]   Claude Code  命令速查 · CLAUDE.md · Hook · MCP · Prompt
    [2]   开发者工具  Git 可视化 · 文件浏览 · Docker · 系统信息
    [3]   效率工具  代码片段 · 任务 · 笔记 · 书签 · 命令收藏
    [4]   速查表  Git · Docker · NPM · Regex · Python · Linux
    [5]   扩展功能  快捷工具 · 命令面板 · 博客 · 最近使用

◆ ━━━ ✦ ━━━ HYPERVOID ━━━━━━━━━━━━━━━━━━━━━ hypervoid.top ━━━ ✦ ━━━ ◆
```

## 🎯 操作方式

| 按键 | 功能 |
|------|------|
| ↑ ↓ | 上下移动选择 |
| Enter | 确认选择 |
| Esc / Q | 返回上级 |
| 1-9, 0 | 数字快捷键 |
| PgUp / PgDn | 翻页滚动 |

## 📁 项目结构

```
hypervoid/
├── app.py              # 主程序入口
├── tui_utils.py        # TUI 核心框架 (跨平台)
├── tui_base.py         # 兼容层
├── mod_claude.py       # Claude Code 工具
├── mod_devtools.py     # 开发者工具
├── mod_productivity.py # 效率工具
├── mod_cheatsheet.py   # 速查表
├── mod_extras.py       # 扩展功能
├── data/
│   └── prompts.json    # Prompt 模板数据
├── templates/          # 命令和 Hook 模板
├── modules/            # PowerShell 模块 (旧版兼容)
├── install.ps1         # Windows 安装脚本
└── .gitignore
```

## 🔧 依赖

- Python 3.8+
- rich

```bash
pip install rich
```

## 🔒 安全性

- ✅ 无硬编码密钥或令牌
- ✅ 用户数据存储在 `~/.hypervoid/data/` (不在项目目录)
- ✅ `.gitignore` 排除敏感文件
- ✅ 跨平台键盘输入 (msvcrt / termios)

## 📄 License

MIT

## 🔗 链接

- 🌐 [hypervoid.top](https://hypervoid.top)
- 📖 [Claude Code 文档](https://docs.anthropic.com/en/docs/claude-code)
- 🔌 [MCP 服务器](https://github.com/modelcontextprotocol/servers)
- 📚 [Rich 库](https://rich.readthedocs.io)
