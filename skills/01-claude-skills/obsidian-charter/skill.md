---
name: obsidian-charter
description: 连接并操作 D:\sidian-charter 目录下的 Obsidian 仓库。当用户提到保存、更新、读取或写入 obsidian-charter 时，以及用户提到"同步skill到obsidian"或类似语义时必须使用此技能。确保在处理 Obsidian 笔记时使用此技能，即使用户没有明确提到'保存到obsidian-charter'但上下文涉及笔记管理。
---

# Obsidian 仓库连接技能

本技能用于连接和操作位于 D:\sidian-charter 的 Obsidian 仓库，实现文件的读取、写入和管理功能。

## 功能

- 读取 Obsidian 仓库中的文件
- 在 Obsidian 仓库中创建新文件
- 更新现有文件内容
- 搜索仓库中的文件

## 触发条件

当出现以下任何情况时，必须使用此技能：
- 用户明确提到"保存到obsidian-charter"
- 用户要求读取或写入 Obsidian 笔记
- 用户提到"sidian-charter"或"obsidian"
- 上下文涉及笔记管理、知识库操作或文档存储
- 用户创建、修改或删除本地 skill 文件（自动同步到 Obsidian）

## 使用方法

### 读取文件
使用 Read 工具读取指定路径的文件：
```json
{"name": "Read", "arguments": {"file_path": "D:\\sidian-charter\\filename.md"}}
```

### 写入文件
使用 Write 工具创建或覆盖文件：
```json
{"name": "Write", "arguments": {"file_path": "D:\\sidian-charter\\filename.md", "content": "文件内容"}}
```

### 编辑文件
使用 Edit 工具修改现有文件：
```json
{"name": "Edit", "arguments": {"file_path": "D:\\sidian-charter\\filename.md", "old_string": "旧内容", "new_string": "新内容"}}
```

### 搜索文件
使用 Glob 工具查找文件：
```json
{"name": "Glob", "arguments": {"pattern": "**/*.md", "path": "D:\\sidian-charter"}}
```

## 同步 Skills 到 Obsidian

当用户说"同步skill"、"同步skills"或类似语义时，执行以下流程：

### ⚠️ 同步原则（必须严格遵守）

1. **必须完整复制**：使用 `cp -r` 命令直接复制整个 skill 目录
2. **禁止手写简化版**：不得用 Write/Edit 工具手写简化版内容，必须完整复制
3. **保持目录结构**：skill 的 references/、mcp_server/ 等子目录必须完整复制
4. **文件名与索引一致**：Obsidian索引 `D:\sidian-charter\skills\00-Skill Index.md` 中的链接格式是 `SKILL.md`（大写），必须确保复制后文件名匹配

### 同步路径

| 用途 | 路径 |
|------|------|
| 本地skills | `C:\Users\nijiasheng1\.claude\skills\` |
| Obsidian同步目标 | `D:\sidian-charter\skills\01-claude skills\` |
| Skills索引 | `D:\sidian-charter\skills\00-Skill Index.md` |

### 同步流程

```
1. 同步目录（排除 .git 和符号链接）
   for dir in "C:/Users/nijiasheng1/.claude/skills/"*/; do
     skill_name=$(basename "$dir")
     # 跳过隐藏目录
     [[ "$skill_name" == .* ]] && continue
     cp -r "$dir" "D:/sidian-charter/skills/01-claude skills/" 2>/dev/null
   done

2. 验证同步完整性
   # 检查源目录 skill 数量
   SRC_COUNT=$(ls -1 "C:/Users/nijiasheng1/.claude/skills/" | wc -l)
   # 检查目标目录 skill 数量
   DST_COUNT=$(ls -1 "D:/sidian-charter/skills/01-claude skills/" | wc -l)
   echo "Source: $SRC_COUNT, Dest: $DST_COUNT"

   # 验证每个 skill 都有 SKILL.md
   for skill in "D:/sidian-charter/skills/01-claude skills"/*/; do
     name=$(basename "$skill")
     if [ ! -f "$skill/SKILL.md" ]; then
       echo "MISSING: $name/SKILL.md"
     fi
   done

3. 自动更新索引
   bash "D:/sidian-charter/scripts/update-skill-index.sh"

4. 验证索引链接
   # 检查新增的 skill 是否已加入索引，日期是否为今天
```

### 同步检查清单

| 检查项 | 命令/方法 |
|-------|---------|
| 源目录 skill 数量 | `ls -1 "C:/Users/nijiasheng1/.claude/skills/" \| wc -l` |
| 目标目录 skill 数量 | `ls -1 "D:/sidian-charter/skills/01-claude skills/" \| wc -l` |
| 所有 skill 都有 SKILL.md | `for d in "D:/sidian-charter/skills/01-claude skills"/*/; do [ ! -f "$d/SKILL.md" ] && echo "MISSING: $(basename $d)"; done` |
| 索引已更新 | 检查 `00-Skill Index.md` 日期是否为今天 |

### 常见错误及规避

| 错误做法 | 正确做法 |
|---------|---------|
| 用 Write 工具手写简化版 | 必须用 `cp -r` 命令完整复制 |
| 只复制主文件，忽略 references/ | 必须复制整个目录 `cp -r dir/` |
| 文件名与索引不一致 | 重命名为 `SKILL.md`（大写）确保链接生效 |
| 修改 Obsidian 独有的内容 | 同步只从本地到 Obsidian 单向进行 |

### 注意事项

- 同步只从本地到 Obsidian 单向进行，不删除 Obsidian 中独有的内容
- 保持文件路径使用正斜杠(/)以确保跨平台兼容性
- 同步完成后验证：执行 `ls` 确认文件存在和目录结构完整

## Skill 变更自动同步

当检测到用户创建、修改或删除 skill 文件时，必须自动执行同步。

### 自动同步触发场景

| 操作类型 | 触发条件 | 同步动作 |
|---------|---------|---------|
| 创建新 skill | 在 `C:\Users\nijiasheng1\.claude\skills\` 下新增 skill 目录 | 用 `cp -r` 完整复制整个目录到 Obsidian |
| 修改 skill | 已有 skill 文件内容发生变更 | 用 `cp -r` 完整复制覆盖 Obsidian 版本 |
| 删除 skill | skill 文件被删除 | **不执行删除**，保持 Obsidian 中历史版本 |

### 自动同步流程

```
1. 检测变更：
   - 监听用户对 C:\Users\nijiasheng1\.claude\skills\ 下 .md 文件的操作
   - 识别发生变更的 skill 名称和操作类型

2. 执行同步（必须用 cp 命令完整复制）：
   - 创建/修改：
     ```bash
     # 完整复制整个 skill 目录
     cp -r "C:/Users/nijiasheng1/.claude/skills/{skill-name}/" "D:/sidian-charter/claude skills/{skill-name}/"
     ```
   - 删除：仅记录变更，不删除 Obsidian 内容

3. 更新索引：
   bash "D:/sidian-charter/scripts/update-skill-index.sh"

4. 确认完成：
   - 向用户确认同步结果
   - 报告新增/更新/未删除（保留）的 skill 数量
   - 验证同步：ls -la 确认文件大小
```

### 同步规则

- **创建**：新增文件立即同步
- **修改**：检测到文件变更时同步
- **删除**：**不删除** Obsidian 中的对应文件，仅记录变更
- **索引**：每次同步后自动更新索引文件
- **复制方式**：**必须用 `cp -r` 完整复制**，禁止手写简化版