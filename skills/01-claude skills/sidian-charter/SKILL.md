---
name: sidian-charter
description: Obsidian仓库同步管理技能。管理E:\AIopen\sidian-charter仓库，当用户需要同步、保存文档时读取写入仓库；将全局skills内容备份到仓库skills目录下并生成目录索引；当用户修改、新建、删除skill时自动同步；当用户请求同步时执行同步操作。
metadata:
  version: 1.0.0
  vault_path: E:\AIopen\sidian-charter
---

# Sidian-Charter: Obsidian仓库同步管理

本skill管理Obsidian仓库 `E:\AIopen\sidian-charter`，负责skill内容的持久化备份、目录索引生成及双向同步。

## 仓库信息

- **仓库路径**: `E:\AIopen\sidian-charter`
- **Skills目录**: `E:\AIopen\sidian-charter\skills`

## 何时激活

- 用户说"同步"、"保存skill"、"备份skill"
- 用户修改、新建、删除skill内容
- 用户请求查看skills目录或索引
- 用户提到"sidian-charter"或"obsidian仓库"

## 核心功能

### 1. 同步所有Skills到仓库

将全局skills目录 `C:\Users\Administrator\.claude\skills` 下的所有内容同步到Obsidian仓库的 `skills` 目录下。

**同步内容**：
- 每个skill的完整内容（SKILL.md等）
- 符号链接指向的实际内容
- 目录结构保持一致

**操作步骤**：
1. 扫描全局skills目录
2. 解析符号链接获取实际路径
3. 复制所有skill文件夹到仓库skills目录
4. 更新或创建首页索引文件

### 2. 生成Skills目录索引

在仓库根目录创建或更新 `Skills目录.md` 文件，包含：

- 按分类组织的skills列表
- 每个skill的名称和功能简述
- 分类结构：
  - **开发工具类**: code-reviewer, debugger, security-auditor等
  - **中文处理类**: context-ZH, translation
  - **Perfetto分析类**: perfetto-* 系列（约14个）
  - **系统集成类**: skill-router, find-skills, skill-creator等
  - **其他工具类**: report-generator, translation等

### 3. 双向同步

当检测到skill变化时：
- **新建skill**: 同步到仓库
- **修改skill**: 更新仓库中的内容
- **删除skill**: 从仓库中移除

### 4. 按需同步

用户可通过以下指令触发同步：
- "同步skills"
- "保存到obsidian"
- "备份skills"
- "同步sidian-charter"

## 分类索引模板

```markdown
# Skills 目录索引

## 开发工具类

| Skill名称 | 功能简述 |
|-----------|----------|
| code-reviewer | 代码审查，质量检查 |
| debugger | 调试诊断，错误定位 |
| security-auditor | 安全审计，漏洞扫描 |
| ... | ... |

## 中文处理类

| Skill名称 | 功能简述 |
|-----------|----------|
| context-ZH | 中文语境增强 |
| translation | 翻译优化 |

## Perfetto性能分析类

| Skill名称 | 功能简述 |
|-----------|----------|
| perfetto-audio | 音频问题分析 |
| perfetto-binder-latency | Binder延迟分析 |
| ... | ... |

## 系统集成类

| Skill名称 | 功能简述 |
|-----------|----------|
| skill-router | 技能路由 |
| find-skills | 技能查找 |
| skill-creator | 技能创建 |
| ... | ... |
```

## 同步流程

### 全量同步流程

```
1. 扫描 C:\Users\Administrator\.claude\skills\
2. 对每个skill文件夹：
   a. 如果是符号链接，解析实际路径
   b. 复制文件夹到 E:\AIopen\sidian-charter\skills\
3. 更新 E:\AIopen\sidian-charter\Skills目录.md
4. 报告同步结果
```

### 增量同步流程

```
1. 获取变化的skill名称
2. 根据变化类型执行：
   - 新增：复制到仓库
   - 修改：更新仓库内容
   - 删除：从仓库移除
3. 更新索引文件
```

## 操作命令

### 同步所有Skills

当用户请求同步时，执行：
```bash
# 1. 确保仓库skills目录存在
mkdir -p "E:/AIopen/sidian-charter/skills"

# 2. 同步每个skill
# 遍历全局skills目录，复制内容到仓库

# 3. 生成/更新索引
# 写入Skills目录.md到仓库根目录
```

### 读取仓库内容

当用户需要查看仓库内容时：
- 读取 `E:\AIopen\sidian-charter\skills\{skill-name}\SKILL.md`
- 读取 `E:\AIopen\sidian-charter\Skills目录.md`

### 写入仓库内容

当用户保存内容到仓库时：
- 写入 `E:\AIopen\sidian-charter\{filename}.md`

## 分类定义

### 开发工具类 (Development Tools)
- code-reviewer: 代码审查和质量检查
- debugger: 调试和错误诊断
- security-auditor: 安全漏洞审计
- report-generator: 数据报告生成

### 中文处理类 (Chinese Language)
- context-ZH: 中文语境增强，自动使用简体中文输出
- translation: 翻译优化，语义提升

### Perfetto性能分析类 (Perfetto Analysis)
- perfetto-audio: 音频问题分析
- perfetto-binder-latency: Binder延迟分析
- perfetto-command-playbook: 命令手册
- perfetto-cpu-scheduler-stall: CPU调度分析
- perfetto-history-issue-matcher: 历史问题匹配
- perfetto-jank-frame-analysis: 帧率抖动分析
- perfetto-priority: 线程优先级分析
- perfetto-report-writer: 报告撰写
- perfetto-root-cause-classifier: 根因分类
- perfetto-stack-evidence-hunter: 栈追踪
- perfetto-startup-latency: 启动延迟分析
- perfetto-system-mitigation-advisor: 系统缓解建议
- perfetto-trace-intake: trace摄入
- perfetto-trace-observability-auditor: 可观测性审计
- perfetto-triage-reasoner: 分诊推理

### 系统集成类 (System Integration)
- skill-router: 技能路由，智能推荐
- find-skills: 技能查找
- skill-creator: 技能创建
- auto-trigger: 自动触发
- using-superpowers: 能力使用
- update-config: 配置更新

### 其他工具类 (Other Tools)
- simplify: 代码简化
- loop: 循环任务
- claude-api: Claude API使用
- vercel-react-native-skills: React Native

## 质量检查

同步完成后验证：
- [ ] 所有skill文件夹已复制到仓库
- [ ] 符号链接已解析为实际内容
- [ ] Skills目录.md已更新
- [ ] 内容完整性检查

## 错误处理

- **仓库不存在**: 提示用户创建或检查路径
- **复制失败**: 报告具体失败原因
- **索引生成失败**: 保留已复制的skill，单独报告索引错误
