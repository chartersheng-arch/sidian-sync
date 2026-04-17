# Perfetto Audio 性能分析流程（融合版）

## 1. 入口：perfetto-trace-intake

用户输入 trace 文件 + 分析目标（如"音频卡顿"、"underrun"）

**Intake 做两件事：**
- 确认 trace 路径、分析目标、关注进程/时间窗口
- **症状分类** — 识别为 `audio glitch / underrun / stutter`

**路由到：** `perfetto-audio` + `perfetto-command-playbook`
**扩展：** `perfetto-priority`  `perfetto-compare`

---

## 2. 推理阶段：perfetto-audio

`perfetto-audio` 作为 reasoning-lens skill，指导全路径调查：

```
音频问题
  ├─ APP 层 — 回调线程 thread_state + top slices
  ├─ Framework 层 — AudioFlinger mixer slices + thread_state
  ├─ HAL 层 — stream_out / write / DRAIN 耗时
  └─ 跨层 Binder — 若怀疑 APP→AF 通信延迟
```

**每个发现都会触发 perfetto-triage-reasoner 的迭代推理**

---

## 3. 收敛检查

在 `perfetto-triage-reasoner` 判断收敛后：

| 下一步 | 做什么 |
|--------|--------|
| `perfetto-root-cause-classifier` | 根因分类（8 buckets） |
| `perfetto-stack-evidence-hunter` | 深挖调用链/阻塞链证据 |
| `perfetto-trace-observability-auditor` | 审计 trace 证据边界 |
| `perfetto-system-mitigation-advisor` | 系统侧 mitigation 建议 |

---

## 4. 报告输出：perfetto-report-writer

生成中文报告，第 7b 节填入对比机信息（如果有对比机）

## 关键差异（旧流程 vs 新增后）

| | 旧流程 | 新增后 |
|---|---|---|
| audio 入口 | 无专门分类，笼统走 `unknown` | `perfetto-trace-intake` 直接路由到 `perfetto-audio` |
| audio 调查 | 依赖通用 SQL 无特定 guidance | `perfetto-audio` 提供三层 SQL cookbook + decision tree |
| 对比机 | 无 | `perfetto-compare` + 报告模板第 7b 节 |

**核心变化：** `perfetto-audio` 把原来分散的 audio 分析经验固化成了结构化的 skill，使每一次调查都遵循同样的深度追问链条（APP → Framework → HAL → cross-layer）。

---

## 5. perfetto-trace-killer 整体架构

**项目定位**: Agent-first Perfetto trace 分析工具，基于 Claude Code 和 `perfetto-mcp` 驱动。

### 核心架构图

```
┌─────────────────────────────────────────────────┐
│  Claude Code (推理 & 编排层)                      │
│                                                 │
│  ┌──────────────┐     ┌──────────────────────┐  │
│  │ .claude/     │     │ perfetto-mcp/        │  │
│  │  skills/ (16)│────▶│  trace_processor     │  │
│  │  分析方法论  │     │  SQL & metrics       │  │
│  └──────────────┘     └──────────────────────┘  │
└─────────────────────────────────────────────────┘
```

### 三层职责

| 层级 | 组件 | 职责 |
|------|------|------|
| **编排层** | Claude Code | 读取技能、调用 MCP 工具、更新假设、生成报告 |
| **方法论层** | `.claude/skills/` (16个技能) | 可复用的调查方法论：intake、triage、classification、auditing、mitigation、reporting |
| **执行层** | `perfetto-mcp/` (git submodule) | MCP server，封装 `trace_processor`，提供 open_trace_session、query_trace_sql 等工具 |

### 技能列表 (16个)

| 阶段 | 技能 | 作用 |
|------|------|------|
| 入口 | `perfetto-trace-intake` | 验证输入、分类症状 |
| 首轮查询 | `perfetto-command-playbook` | 根据症状选择第一个 MCP 调用 |
| 症状透镜 | `perfetto-jank-frame-analysis` | 卡顿、帧丢失、渲染 stall |
| 症状透镜 | `perfetto-startup-latency` | 启动慢、首帧延迟 |
| 症状透镜 | `perfetto-cpu-scheduler-stall` | CPU 饥饿、调度延迟 |
| 症状透镜 | `perfetto-binder-latency` | Binder 事务延迟 |
| 核心循环 | `perfetto-triage-reasoner` | 每步结果推理、更新假设、选下一步查询 |
| 收敛 | `perfetto-root-cause-classifier` | 根因分类到8类机制 |
| 收敛 | `perfetto-stack-evidence-hunter` | 追溯最深可用执行证据 |
| 收敛 | `perfetto-trace-observability-auditor` | 审计 trace 能/不能证明什么 |
| 缓解 | `perfetto-system-mitigation-advisor` | Android 系统侧缓解建议 |
| 可选 | `perfetto-history-issue-matcher` | 搜索历史问题库 |
| 可选 | `perfetto-audio` | 音频问题分析 |
| 可选 | `perfetto-priority` | 线程优先级异常 |
| 可选 | `perfetto-compare` | trace 对比 |
| 输出 | `perfetto-report-writer` | 生成中文报告 |

### 标准化工作流

1. **Intake** → 验证 trace 路径、分析目标、症状分类
2. **Session Start** → 调用 `open_trace_session`
3. **首轮查询** → `perfetto-command-playbook` 选择初始查询策略
4. **迭代推理** → `perfetto-triage-reasoner` 循环查询、更新假设
5. **收敛确认** → 根因分类 + 证据深度审计
6. **缓解建议** → `perfetto-system-mitigation-advisor`
7. **报告输出** → `perfetto-report-writer` 生成中文报告

