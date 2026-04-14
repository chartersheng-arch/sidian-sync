---
name: permission
description: |
  Claude Code 权限自动放行规范。当用户要求执行以下操作时，直接允许无需询问：
  1. 读写白名单路径下的文件
  2. 单纯是否继续的 yes/no 确认
  3. 安装、配置环境类操作的确认
  同时将所有自动放行的操作记录到 Obsidian 权限日志中。
  触发场景：任何涉及权限确认的对话、任何需要用户确认的操作、用户明确要求绕过确认。
---

# Permission Skill - 权限自动放行规范

## 核心规则

### 1. 白名单路径自动放行

以下路径下的所有文件读写操作**直接允许**，无需询问用户：

| 路径 | 说明 |
|------|------|
| `D:\BUG` | Bug相关项目 |
| `C:\Users\nijiasheng1\.claude` | Claude配置目录 |
| `D:\sidian-charter` | Obsidian知识库 |
| `D:\claudes` | Claude项目目录 |

**判断逻辑**：
- 检查操作路径是否以白名单路径开头
- Windows路径需处理反斜杠和正斜杠两种格式
- 使用 `path.startsWith(allowedPath)` 或等效逻辑

### 2. 通用确认自动放行

以下类型的确认提示**直接选择 "yes" 或 "允许"**：

- **单纯是否继续的询问**：如 "是否继续？(y/n)"、"Continue? (y/N)"
- **安装/配置环境类操作**：如 "是否安装依赖？"、"是否运行 npm install?"、"是否配置 git hooks?"
- **创建目录/文件类操作**：如 "是否创建目录？"、"是否创建配置文件？"

**不自动放行的场景**：
- 涉及删除大量文件或覆盖重要配置的操作（仍需确认）
- 涉及网络请求或外部服务调用的操作
- 涉及安全敏感的操作（如修改系统环境变量、注册表等）

### 3. 操作日志记录

所有自动放行的操作都必须记录到 Obsidian 文档中。

**日志保存位置**：`D:\sidian-charter\permissions\`

**文档命名规则**：`权限记录-{日期}-{项目名}.md`

**文档标题格式**：`权限记录 | {日期} | {项目名}`

**记录格式**（详细格式）：

```markdown
---
title: 权限记录 | {日期} | {项目名}
created: {ISO格式时间戳}
tags: [权限记录, claude-code]
---

# {项目名} 权限操作记录

## 操作日志

| 时间 | 操作类型 | 具体路径/操作 | 原因/上下文 |
|------|----------|--------------|------------|
| {HH:mm:ss} | {read/write/confirm/env_install} | {具体路径或命令} | {为什么会触发这个操作} |
```

**操作类型枚举**：
- `read` - 读取文件/目录
- `write` - 写入文件/创建目录
- `confirm` - yes/no 确认
- `env_install` - 环境安装/配置

**项目名自动识别逻辑**：
1. 如果有明确的项目路径，使用路径最后一层目录名
2. 如果是纯命令执行，使用 "通用操作"
3. 日期格式：`YYYY-MM-DD`

### 4. 实现伪代码

```python
# 判断是否在白名单路径内
def is_whitelisted(path):
    whitelist = [
        r"D:\BUG",
        r"C:\Users\nijiasheng1\.claude",
        r"D:\sidian-charter",
        r"D:\claudes"
    ]
    normalized = path.replace("/", "\\")
    return any(normalized.startswith(p) for p in whitelist)

# 判断是否是简单确认
def is_simple_confirm(question):
    simple_patterns = [
        "continue?", "是否继续", "y/n", "yes/no",
        "install", "配置", "setup", "是否安装",
        "创建目录", "创建文件"
    ]
    return any(p in question.lower() for p in simple_patterns)

# 记录到Obsidian
def log_permission(action_type, detail, context):
    # 生成文档名和路径
    date = datetime.now().strftime("%Y-%m-%d")
    project = extract_project_name(detail)
    filename = f"权限记录-{date}-{project}.md"
    filepath = Path("D:/sidian-charter/permissions") / filename
    
    # 写入日志条目
    entry = f"| {time} | {action_type} | {detail} | {context} |"
    # 追加到文档
```

## 决策流程

```
用户操作/确认请求
       │
       ▼
┌─────────────────┐
│ 检查路径是否在   │──否──▶  正常询问用户
│ 白名单中？        │
└────────┬────────┘
         │是
         ▼
┌─────────────────┐
│ 检查是否简单确认 │──是──▶  直接允许 + 记录日志
│ (安装/继续/创建) │
└────────┬────────┘
         │否
         ▼
┌─────────────────┐
│ 检查是否安全敏感 │──是──▶  正常询问用户
│ (删除/覆盖/系统) │
└────────┬────────┘
         │否
         ▼
   直接允许 + 记录日志
```

## 注意事项

1. **安全边界**：如果操作涉及 `rm -rf`、`del /f /s` 等高危命令，即使在白名单路径内也要询问
2. **Token消耗**：日志记录应简洁，不要记录大文件内容
3. **上下文记录**：记录"为什么"比记录"是什么"更重要
4. **跨平台**：代码需处理 Windows 路径格式

## 与 Obsidian 的配合

本 skill 与 `obsidian-charter` skill 配合使用：
- 权限日志使用 `obsidian-charter` skill 的基础路径 `D:\sidian-charter`
- 权限日志存放在 `permissions/` 子目录下
- 如果 `obsidian-charter` skill 可用，可调用其方法简化文件操作
