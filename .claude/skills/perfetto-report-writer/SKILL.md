---
name: perfetto-report-writer
description: Write a professional Chinese report for Perfetto trace analysis after the investigation converges. Use when Claude Code has collected the key evidence, dominant hypothesis, uncertainty bounds, and recommended next actions.
---

# Perfetto Report Writer

This skill is guidance only.
Do not call `Task Output`, `read_task`, or any task-result retrieval mechanism using `perfetto-report-writer` as an ID.
After loading this skill, write the report directly in the assistant response.

## Goal

Write a professional, traceable final report **in Chinese** that converts the entire investigation — evidence, reasoning, classification, and mitigations — into a single deliverable for Android device-side teams.

## When to use

Load this skill only when ALL of these are true:

- The main trace analysis has converged (dominant mechanism identified or explicitly marked unclassified)
- `perfetto-root-cause-classifier` has been executed
- `perfetto-trace-observability-auditor` has been executed
- `perfetto-system-mitigation-advisor` has been loaded (required before writing recommendations)
- The user confirms they are ready for the final report

## Report template and output

The report must follow the strict template in [perfetto-report-template.md](docs/perfetto-report-template.md).
Do not reorder sections. Do not collapse the reasoning process into a short summary.
Save the report under `reports/` using this required filename template:
`应用名_场景_问题类型_主机制_YYYYMMDD_HHMM_trace-会话ID.md`

Filename field guidance:
- `应用名`: stable product name such as `抖音` or `高德地图`
- `场景`: concise user-visible scenario such as `首页滑动` or `启动`
- `问题类型`: symptom label such as `卡顿` or `启动慢`
- `主机制`: dominant mechanism such as `GPU合成慢`、`Binder延迟`、`CPU争抢`、`RenderThread阻塞`、`IO等待`、`未分类`
- `YYYYMMDD_HHMM`: report generation time in local time
- `会话ID`: current trace session ID

## Required sections

1. 执行摘要
2. 输入信息
3. 会话模式与工具约束
4. 调查范围与证据边界
5. 推理过程记录
6. 关键证据
7. 根因判断
8. 置信度与局限性
9. 优化建议
10. 后续建议
11. 历史相似案例参考（可选）
12. 关键查询附录

If no strong root cause is proven, say that plainly and explain what evidence is still missing.

---

## Writing rules

### Evidence & reasoning rules

- Separate direct trace evidence from inference
- Use time windows, thread names, and process names when helpful
- Record the reasoning chain step by step
- Include the actual MCP query intent for each investigation step
- Explain why the next query was chosen at each step
- Make the final report traceable from conclusion back to evidence
- When nested slices or parent-child evidence exist, include an explicit call chain or blocking chain in the report

### Structure & format rules

- Write like an engineer's incident analysis, not like a chatbot answer
- Keep the report professional and concise
- Keep evidence, reasoning, assessment, and limitations clearly separated
- Keep the narrative scoped to the user's problem statement; do not include unrelated mechanism pages or generic textbook sections
- Remove redundant repetitions of the same evidence across sections; if repeated, add only new decision value

### Classification reflection rules

- Reflect the root-cause classification explicitly in the root-cause section (from `perfetto-root-cause-classifier`)
- Reflect the observability ceiling explicitly in the confidence and limitations section (from `perfetto-trace-observability-auditor`)
- If confidence is bounded by missing data sources, say so explicitly
- If historical matches were searched, include them as supporting references in the dedicated optional section

---

## Mandatory relevance and anti-redundancy constraints

- Every section must trace back to the target symptom, target process, or target window.
- If a paragraph does not change diagnosis, confidence, or action priority, omit it.
- Do not copy broad taxonomy content into case reports.

## Mandatory GC evidence gate

Do not write "confirmed GC/memory-pressure cause" unless all checks pass:

1. process-scoped evidence on the target app/process
2. measurable overlap with bad-frame or bad-slice windows
3. blocking-path evidence on critical threads (for example main, RenderThread, or equivalent)

If any check is missing, report GC/memory only as a competing hypothesis or secondary signal.

## Mandatory process-record format

In the `推理过程记录` section, each step must include:

- 当时已掌握的证据
- 当时的假设 / 未决问题
- 指令
- 结果摘要
- 结果分析
- 下一步要查什么
- 为什么选择这个查询
- 这一步如何改变了判断

Do not skip the failed or corrected queries if they materially affected the reasoning path.
The reader should be able to follow the path from the initial symptom to the final root-cause judgment.

## Call-chain requirement

If the trace contains nested slices, parent-child relationships, or a clear blocking chain, the final report must include at least one explicit chain in a readable indented format such as:

```text
Choreographer#doFrame
└── input
    └── dispatchInputEvent
        └── View#onTouchEvent
            └── RV Scroll
                └── RV OnBindView
                    └── Constructing StaticLayout
```

Do not reduce this to a single-sentence summary when the chain can be reconstructed from the evidence.

---

## Section-level guidance

- **执行摘要**: State the dominant hypothesis first.
- **关键证据**: Prefer 3-5 high-value facts over long query dumps. Include a dedicated `关键调用链 / 阻塞链` item when the trace supports it.
- **根因判断**: Separate confirmed cause, contributing factors, and open uncertainty. State the dominant mechanism bucket (app-self workload / render path / CPU contention / binder-IPC / lock contention / GC-memory pressure / IO-decode / unclassified). Restate the dominant parent-child chain that best explains why the frame or stall became late.
- **置信度与局限性**: Say plainly what is proven, inferred, still missing, and what the current trace can or cannot directly prove.
- **历史相似案例参考**: Include only strong matches from the user-provided history path; clearly separate them from direct trace evidence.
- **关键查询附录**: Keep only the most decision-relevant commands.

---

## Recommendation rules

All recommendation-related constraints are collected here. **Before writing this section, ALWAYS load `perfetto-system-mitigation-advisor` skill first.**

### Audience and priority

- Default to **system-side practical mitigation** first, because this project is used by Android device-side teams.
- If the root cause appears to be APK behavior, still provide system-side mitigations that a device or platform team can actually try.
- If application behavior is the dominant cause, explicitly separate:
  - "APK-side ideal fix" — only to explain the ideal upstream fix
  - "system-side practical mitigation" — the main recommendation set
- Only include APK-side fixes when they help explain context; do not make them the main recommendation set.

### Mechanism-specific mapping

Every recommendation must be mechanism-specific and evidence-linked. Avoid generic advice.

- **IO or blocking resource load**: reclaim pressure reduction, watermark tuning, swappiness adjustment, read-ahead, storage scheduler, cache retention strategy
- **CPU contention**: scheduler, cpuset, uclamp, frequency, top-app placement
- **Binder congestion**: binder threadpool, service scheduling, dependency isolation
- **Lock contention**: contention-point reduction, lock scope isolation, worker offloading
- **Memory pressure / GC**: reclaim, LMKD, watermark, file-cache preservation, swap/zram, compaction tuning
- **Render-path issues**: RenderThread, SurfaceFlinger, composition, buffer queue, display-pipeline mitigations

### Mandatory detail per recommendation

**Every optimization recommendation MUST include:**

| Field | Requirement | BAD example | GOOD example |
|-------|-------------|-------------|--------------|
| Implementation detail | Specific config files, parameter names, values | "调整 ART 锁策略" | "在 build.prop 中添加 `dalvik.vm.intern-table-buckets=4096`" |
| Command / config snippet | Actual shell commands, kernel config, XML | "优化 Binder 线程池" | "修改 /system/etc/init/servicemanager.rc，添加 `write /dev/binderfs/binder-control/new 16`" |
| Expected benefit | Percentage or absolute improvement | "减少延迟" | "预期延迟降低 20-30%" |
| Difficulty & risk | low / medium / high | _(missing)_ | "难度 medium，风险 low" |
| Preconditions | Kernel version, hardware, etc. | _(missing)_ | "需要 kernel 5.10+ 且 CONFIG_UCLAMP_TASK=y" |

**Violations of this rule invalidate the recommendation.** If you cannot provide this level of detail, explicitly state what additional information is needed.

### Anti-generic guardrails

- Do not write generic advice such as "optimize performance", "reduce workload", or "use async" without tying it to a specific bottleneck and execution side.
- For each recommendation, label it as `system-side practical mitigation` or `APK-side ideal fix`.
- If no credible system-side mitigation exists, say so plainly instead of inventing one.

---

## Footer

Append this block at the end of the report:

```text
报告生成日期： {{date}}
会话 ID： {{session ID}}
分析师： perfetto-trace-killer by iliuqi
作者主页：https://www.iliuqi.com
```

## Handoff

- After saving the report to `reports/` → tell the user the file path
- Ask whether the user has additional questions about this trace
- If no further questions → call `close_trace_session` to release resources
- If the user wants to investigate another trace → start a new intake cycle
