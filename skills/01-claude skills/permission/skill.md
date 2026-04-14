---
name: permission
description: |
  Claude Code 权限自动放行规范。当用户要求执行以下操作时，直接允许无需询问：
  1. 白名单路径下的所有文件操作
  2. 简单确认类操作（yes/no、安装、创建等）
  3. 常见文件读写操作（读取、编辑、创建小文件）
  4. 常用命令执行（git status/log/diff、ls、cat等）
  触发场景：任何涉及权限确认的对话、任何需要用户确认的操作、用户明确要求绕过确认。
---

# Permission Skill - 权限自动放行规范

## 核心规则

### 1. 白名单路径自动放行

以下路径下的**所有操作**直接允许，无需询问：

| 路径 | 说明 |
|------|------|
| `D:\BUG` | Bug相关项目 |
| `C:\Users\nijiasheng1\.claude` | Claude配置目录 |
| `D:\sidian-charter` | Obsidian知识库 - **所有操作完全放行** |
| `D:\claudes` | Claude项目目录 |
| `D:\CC-Switch-v3.12.3-Windows-Portable` | 当前工作目录 |

**判断逻辑**：
- Windows路径需同时处理反斜杠和正斜杠
- 使用 `path.startsWith(allowedPath)` 匹配前缀

### 2. 简单确认自动放行

以下类型的确认**直接选择 "yes"**：

**继续/确认类**：
- `continue?`, `是否继续`, `y/n`, `yes/no`, `proceed?`, `go on?`
- `are you sure?`, `confirm?`, `ok?`, `好的`, `是`, `y`

**安装/配置类**：
- `install`, `npm install`, `pip install`, `配置`, `setup`, `setup`
- `是否安装`, `是否配置`, `要不要安装`, `要不要配置`

**创建类**：
- `创建目录`, `创建文件`, `新建文件`, `新建文件夹`
- `是否创建`, `要不要创建`

**执行类**：
- `是否运行`, `是否执行`, `run?`, `execute?`
- `是否运行以下命令`

### 3. 文件操作自动放行

以下文件操作**直接执行**，无需确认：

**读取操作**：
- `Read`, `Glob`, `Grep`, `Bash` (ls, cat, head, tail, git status, git log, git diff)
- 查看文件内容、搜索代码、列出目录

**写入操作**（小文件、配置类）：
- 创建/编辑 `.md`, `.txt`, `.json`, `.yaml`, `.yml`, `.toml`, `.ini`, `.cfg`, `.conf`
- 创建/编辑 `.gitignore`, `.env`, `.npmrc`, `.prettierrc` 等配置文件
- 创建/编辑 `package.json`, `tsconfig.json` 等项目配置

**注意**：覆盖已有文件超过10KB、删除文件、修改系统配置仍需确认

### 4. 命令执行自动放行

以下命令模式**直接执行**：

**Git常用命令**：
- `git status`, `git log`, `git diff`, `git branch`, `git remote -v`
- `git show`, `git reflog`, `git stash list`

**目录查看**：
- `ls`, `ll`, `dir`, `pwd`, `cd` (仅切换目录，不删除)

**进程查看**：
- `ps`, `top`, `tasklist`, `netstat`

**不自动放行**：涉及网络请求（curl/wget）、修改系统、删除文件的命令

### 5. 操作日志（可选）

自动放行的操作**尽量**记录到 Obsidian：

**路径**：`D:\sidian-charter\permissions\权限记录-{日期}-{项目}.md`

如因沙箱限制无法写入，跳过日志继续执行。

## 决策流程

```
用户确认请求
       │
       ▼
┌─────────────────────────┐
│ 路径在白名单中？          │──是──▶  直接允许
└────────┬────────────────┘
         │否
         ▼
┌─────────────────────────┐
│ 匹配简单确认模式？        │──是──▶  直接 yes
└────────┬────────────────┘
         │否
         ▼
┌─────────────────────────┐
│ 匹配文件操作/命令模式？   │──是──▶  直接执行
└────────┬────────────────┘
         │否
         ▼
       询问用户
```

## 安全边界

以下操作**必须询问**：

- 删除文件 (`rm`, `del`, `rmdir`)
- 覆盖大文件（>10KB）
- 修改系统配置（注册表、系统环境变量）
- 网络请求（curl, wget, Invoke-WebRequest）
- 危险命令 (`Format-Disk`, `diskpart`, `fdisk`)
- 跨白名单路径的移动/重命名

## ⚠️ 沙箱说明

Claude Code 默认沙箱会拦截文件操作。本 skill 规则在**禁用沙箱模式**后完整生效：

```bash
claude --dangerouslyDisableSandbox
```

沙箱启用时：`Read`/`Glob`/`Grep` 等只读操作通常不受影响。
