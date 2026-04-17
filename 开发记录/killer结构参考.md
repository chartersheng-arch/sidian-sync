# 独立 AI 工具项目结构参考标准

> 基于 `perfetto-trace-killer` 架构提炼，作为后续 AI 工具项目的设计基准。

---

## 一、核心设计理念

**Agent-First**：以 AI Agent（Claude Code）为核心编排层，而非简单 CLI 工具。AI 负责推理、决策、迭代；工具层负责执行与数据提供。

**Skill 驱动**：将方法论封装为可组合的 Skill，AI 在不同阶段调用不同 Skill，避免硬编码流程。

**三层分离**：

```
┌──────────────────────────────────────┐
│  AI Agent（推理 & 编排层）            │
│  Claude Code / Codex / Copilot       │
├──────────────────────────────────────┤
│  Skill 层（方法论 & 决策逻辑）         │
│  .claude/skills/                     │
├──────────────────────────────────────┤
│  工具层（执行 & 数据提供）              │
│  MCP Server / CLI / SDK              │
└──────────────────────────────────────┘
```

---

## 二、必选目录结构

```
项目根目录/
├── .claude/
│   └── skills/              # 【必须】AI 技能方法论（至少覆盖入口→执行→输出全流程）
├── docs/                   # 【必须】参考文档：模板、配方、契约、术语表
├── 项目核心工具或服务/      # 【必须】实际执行层（MCP Server / CLI / 脚本）
├── reports/                # 【建议】输出报告目录
├── CLAUDE.md               # 【必须】AI 编排规则（强制检查点、Iron Rules）
├── README.md               # 【必须】项目说明
└── SETUP.md               # 【建议】安装配置指南
```

### 目录详解

| 目录/文件 | 必须 | 用途 |
|-----------|------|------|
| `.claude/skills/` | ✅ | 核心方法论 Skill 集合 |
| `docs/` | ✅ | 模板、SQL cookbook、协议契约等参考文档 |
| `CLAUDE.md` | ✅ | AI 编排规则，强制检查点必须在此明文规定 |
| `README.md` | ✅ | 项目定位、能力、架构、使用说明 |
| `SETUP.md` | ⚙️ | 安装配置步骤（建议独立，避免 README 臃肿） |
| `reports/` | ⚙️ | 分析报告输出目录 |
| `项目核心工具/` | ✅ | 实际执行层（如 MCP server、CLI 工具、Python 包等） |

---

## 三、Skill 架构设计标准

### 3.1 Skill 命名规范

格式：`领域-具体能力`（全小写，横杠分隔）

✅ 正确：`perfetto-trace-intake`、`audio-debug`、`api-documenter`
❌ 错误：`IntakeSkill`、`trace_intake`、`TraceIntake`

### 3.2 Skill 必须文件

每个 Skill 目录下必须包含：

```
.claude/skills/<skill-name>/
├── SKILL.md        # 【必须】核心定义：触发条件、职责、输出、调用时机
├── README.md       # 【建议】使用者文档：何时用、如何用、示例
└── references/     # 【可选】子技能依赖的模式/清单/模板
    ├── patterns.md
    ├── checklist.md
    └── examples/
```

### 3.3 SKILL.md 标准结构

```markdown
# <skill-name>

## 触发条件
- 用户明确要求时调用
- 特定场景出现时自动触发

## 职责
<清晰描述该 Skill 在整体流程中的角色>

## 输入
<AI 调用该 Skill 时需要提供的信息>

## 输出
<Skill 执行后的产出物>

## 调用时机
<流程中的位置：入口/核心循环/收敛/输出>

## 强制检查点（如适用）
<必须执行的关键动作，不得跳过>

## 与其他 Skill 的关系
<依赖哪些 Skill、被哪些 Skill 依赖>
```

### 3.4 Skill 分类原则

| 类型 | 说明 | 示例 |
|------|------|------|
| **入口类** | 验证输入、分类问题、路由到正确流程 | `perfetto-trace-intake` |
| **执行类** | 执行具体查询/操作 | `perfetto-command-playbook` |
| **推理类** | 基于结果推理、更新假设、选择下一步 | `perfetto-triage-reasoner` |
| **收敛类** | 分类根因、确认证据深度、审计能力边界 | `perfetto-root-cause-classifier`、`perfetto-stack-evidence-hunter` |
| **输出类** | 生成报告、发布文档 | `perfetto-report-writer` |
| **辅助类** | 历史匹配、建议生成 | `perfetto-history-issue-matcher`、`perfetto-system-mitigation-advisor` |

### 3.5 最小 Skill 数量

**至少 3 个**，覆盖：
1. **入口验证** — 接收任务、验证输入、分类问题
2. **执行/推理循环** — 执行操作、迭代推理
3. **输出报告** — 生成最终交付物

> 实际建议：**5-13 个**，按职责细分（参考 perfetto-trace-killer 的 13 个 Skill）

---

## 四、CLAUDE.md 编排规则标准

### 4.1 必须包含章节

```markdown
# CLAUDE.md

## Repository Overview
<30 秒内让 AI 理解项目是做什么的>

## Core Workflow
<主流程控制循环，3-10 步描述>

## <工具/服务名> Server（如果存在）
<可用工具列表及说明>

## Skills Architecture
<表格：Phase | Skill | Role>

## Recommended Skill Order
<编号列表，与上述架构对应>

## ⚠️ CRITICAL: 强制检查点
<明确哪些步骤禁止跳过，以及后果>

## Iron Rules
<绝对规则，违反即错误>
```

### 4.2 强制检查点设计

每个流程必须定义**不可跳过的检查点**：

| 阶段 | 必须检查 | 跳过后果 |
|------|----------|----------|
| 收敛前 | `root-cause-classifier` | 停留在表层归因 |
| 写报告前 | `evidence-hunter` | 缺少调用链证据 |
| 写报告前 | `observability-auditor` | 过度推断，证据边界不清 |
| 写建议前 | `mitigation-advisor` | 建议不具体、不可执行 |

### 4.3 深度追问链

对于诊断类工具，必须定义**强制追问链条**，防止 AI 停在表层现象：

```
发现慢操作
  → 问：为什么慢？
     → 如果是 GPU 相关 → 查 GPU counter、频率、completion
     → 如果是 IPC → 查服务侧进程、线程池状态
     → 如果是 IO → 查 D-state 占比、具体 IO 操作
     → 如果是 CPU → 查 child slices、具体方法调用
```

---

## 五、工具层（执行层）设计标准

### 5.1 推荐技术选型

| 场景 | 推荐方案 |
|------|----------|
| 为 Claude Code 提供工具调用 | MCP Server（Python/Node） |
| 轻量 CLI 工具 | Python 脚本 + argparse |
| 复杂数据分析 | Python 包 + trace_processor |
| Web 服务封装 | FastAPI / Flask |

### 5.2 MCP Server 标准结构

```
perfetto-mcp/                  # 或其他项目名-mcp/
├── README.md                  # MCP Server 说明
├── pyproject.toml             # Python 包配置
├── src/
│   └── perfetto_mcp/
│       ├── __init__.py
│       ├── server.py         # MCP 入口
│       ├── tools.py           # 工具函数定义
│       └── utils.py          # 辅助函数
└── tests/
```

### 5.3 工具接口规范

每个工具必须明确：
- **输入**：参数名、类型、必填/可选、默认值
- **输出**：返回格式（JSON schema）
- **错误处理**：常见错误及返回

---

## 六、文档体系标准

### 6.1 必须文档

| 文档 | 位置 | 用途 |
|------|------|------|
| README.md | 根目录 | 项目概述、架构图、快速开始 |
| CLAUDE.md | 根目录 | AI 编排规则、强制检查点 |
| SETUP.md | 根目录 | 安装配置步骤 |
| SKILL.md | 每个 Skill 目录 | 技能定义 |
| 模板 | docs/ | 输入/输出模板 |

### 6.2 建议文档

| 文档 | 位置 | 用途 |
|------|------|------|
| SQL Cookbook | docs/ | 可复用查询模式 |
| Table Relationships | docs/ | 表关联路径（用于 trace 类） |
| Problem Taxonomy | docs/ | 问题分类参考 |
| MCP JSON Contract | docs/ | 工具输入输出 schema |
| Investigation Template | docs/ | AI 调查对话模板 |

### 6.3 文档风格

- **README**：面向人类使用者，图文并茂，架构图优先
- **CLAUDE.md**：面向 AI，规则清晰，无歧义，禁止模糊表述
- **SKILL.md**：面向 AI 和开发者，触发条件明确，职责边界清晰

---

## 七、输出物规范

### 7.1 报告输出

- 路径：`reports/`
- 命名：`{应用名}_{场景}_{问题类型}_{主机制}_{日期}_{时间}_trace-{会话ID}.md`
- 语言：中文（面向团队）
- 必须包含：推理链、证据、结论、建议

### 7.2 建议质量标准

每条优化建议必须包含：
1. **具体实现细节**（代码/配置片段）
2. **可执行命令**
3. **量化收益**（预期改善幅度）
4. **难度/风险评估**
5. **前提条件**

---

## 八、权限与安全

- 代码**禁止上传公共 GitHub**（如为内部工具）
- 敏感配置（API Key、Token）不得硬编码
- 使用 `.gitignore` 排除敏感文件

---

## 九、架构检查清单

新项目设计完成后，对照以下清单验证：

```
□ 三层架构清晰（AI 编排 / Skill 方法论 / 工具执行）
□ .claude/skills/ 存在，至少 3 个 Skill
□ CLAUDE.md 存在，包含强制检查点和 Iron Rules
□ README.md 存在，架构图清晰
□ 工具层可独立运行（不依赖 AI 层）
□ Skill 有明确触发条件和职责定义
□ 文档体系覆盖使用者（README）和 AI（CLAUDE.md）
□ 输出报告格式有模板或规范
□ 强制追问链已定义（诊断类工具）
□ 禁止上传公共仓库的警示已添加
```

---

## 十、参考项目

- **perfetto-trace-killer**：Agent-First Perfetto trace 分析工具（13 Skills，MCP Server，完整文档体系）
