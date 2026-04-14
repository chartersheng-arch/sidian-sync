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

当用户说"同步skill到obsidian"、"同步skills"、"更新skills索引"或类似语义时，执行以下流程：

### 同步流程

1. **比较差异**：对比本地 `C:\Users\nijiasheng1\.claude\skills\` 与 Obsidian `D:\sidian-charter\claude skills\` 中的 skills 文件
2. **复制最新内容**：将本地最新的 skill 内容同步到 Obsidian
3. **更新索引**：更新 `D:\sidian-charter\claude skills\00 - Skills Index.md`

### 操作步骤

```
1. 获取本地所有 skills 列表：
   - 使用 Glob 工具搜索 C:\Users\nijiasheng1\.claude\skills\ 下的所有 .md 文件
   - 获取每个 skill 的名称、描述和最后修改时间

2. 获取 Obsidian 中的 skills 列表：
   - 使用 Glob 工具搜索 D:\sidian-charter\claude skills\ 下的所有 .md 文件

3. 比较两者差异：
   - 识别新增的 skills（存在于本地但不在 Obsidian）
   - 识别更新的 skills（本地版本比 Obsidian 版本更新）
   - 识别 Obsidian 独有的 skills（仅供参考，不删除）

4. 同步操作：
   - 对于新增和更新的 skills，读取本地文件内容
   - 写入或覆盖到 D:\sidian-charter\claude skills\{skill-name}.md

5. 更新 Skills Index：
   - 读取现有的 00 - Skills Index.md
   - 根据最新的 skills 列表重新生成索引表格
   - 索引格式：| 序号 | 技能名称 | 分类 | 功能简述 |
```

### 同步触发条件

当出现以下任何情况时，必须执行同步：
- 用户明确提到"同步skill到obsidian"
- 用户要求"同步skills"或"更新skills索引"
- 用户提到"同步到sidian"或类似表达
- 用户修改了本地 skills 并希望同步到 Obsidian

### 注意事项

- 所有文件路径必须以 D:\\sidian-charter 开头
- 在写入文件前，确保内容格式符合 Markdown 规范
- 对重要文件进行修改前，建议先读取原内容
- 保持文件路径使用双反斜杠(\\)或正斜杠(/)以确保跨平台兼容性
- 同步只从本地到 Obsidian 单向进行，不删除 Obsidian 中独有的内容