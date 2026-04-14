---
name: perfetto-trace-intake
description: Validate Perfetto trace investigation inputs before calling perfetto-mcp. Use when the user provides a trace file and an analysis goal, and Claude Code must confirm the trace path, focus scope, expected symptom, and any initial constraints that should guide the first hypothesis. Supports optional comparison with a baseline (healthy) trace from a reference device.
---

# Perfetto Trace Intake

This skill is guidance only.
Do not call `Task Output`, `read_task`, or any task-result retrieval mechanism using `perfetto-trace-intake` as an ID.

## Goal

Gate every new Perfetto trace analysis by validating and confirming the trace path, analysis goal, focus scope, expected symptom, and initial constraints before any MCP call. When the user provides a second trace from a reference device under normal / healthy conditions, record it and ensure subsequent analysis includes a comparison between the two traces.

## When to use

Load this skill as the **first step** of every new trace investigation, before calling `open_trace_session`. Repeat it when the user switches to a different trace file within the same conversation.

## Inputs to confirm

Confirm these inputs before opening a session:

1. trace path (problematic trace)
2. analysis goal
3. focus process or package when known
4. focus time window when known
5. expected symptom category
6. *(optional)* reference trace path – a trace from a comparable device / scenario that exhibits **normal** (non‑problematic) behavior
7. *(optional)* description of normal behavior in the reference trace

## Input validation rules

- If the trace path is missing or does not exist, stop and report it.
- If the analysis goal is vague, ask a short clarifying question before proceeding.
- If the user already knows the target app, process, or thread, carry that forward into the session metadata.
- If the user knows a suspicious time window, record it and prefer queries inside that window.
- Do not bypass MCP by writing ad hoc Bash, Node, or Python clients to call the same tools.
- Do not start investigative SQL before `open_trace_session` succeeds.
- **Reference trace validation**: If a reference trace path is provided, verify the file exists. If it does not, ask the user to provide a valid path or skip the comparison. The reference trace is expected to be from the same or equivalent device model and OS version, running the same workload under healthy conditions.

## Symptom categories

Classify the case into one primary category when possible, but treat it as a hint for reasoning rather than a fixed investigation branch:

| Symptom category | Reasoning‑lens skill to consider |
|-----------------|----------------------------------|
| startup latency | `perfetto-startup-latency` |
| jank or frame misses | `perfetto-jank-frame-analysis` |
| CPU scheduler stall | `perfetto-cpu-scheduler-stall` |
| Binder latency | `perfetto-binder-latency` |
| memory pressure | _(no dedicated lens; use triage-reasoner)_ |
| IO wait (frequent D-state, blocking resource load) | _(no dedicated lens; use triage-reasoner)_ |
| **priority anomaly** (explicit mention, or suspected scheduler priority misconfiguration) | `perfetto-priority` |
| **audio glitch** (stutter, pop, crackle, underrun, or glitch during playback/recording) | `perfetto-audio` |
| unknown | _(decide after first-pass data)_ |

> **When to choose “priority anomaly”**: user directly mentions thread priority, nice value, scheduling policy, or describes symptoms like “background thread preempts UI thread”, “important thread runs at low priority”, or “priority seems wrong”. Also consider this category when the reference trace shows different priority values for the same threads under normal behavior.

## IO wait hint detection

If the user mentions any of these hints, pre-mark IO wait as a hypothesis to check:

- "卡顿" (stutter) during scrolling or page transitions
- "滑动慢" (slow scroll)
- "页面切换卡" (page switch lag)
- "加载慢" (slow load) — could be IO or network
- "数据库慢" (database slow)
- "文件读写" (file read/write)

## Audio glitch hint detection

If the user mentions any of these hints, pre-mark audio glitch as the symptom category and load `perfetto-audio`:

- "音频卡顿" (audio stutter)
- "pop音" (pop sound)
- "杂音" (noise)
- "破音" (distortion)
- "音频断续" (audio intermittent)
- "underrun" (audio buffer underrun)
- "音频延迟" (audio delay)
- "声音卡" (sound stutter)
- "爆音" (clipping/popping)
- "audio glitch"
- "audio stutter"
- "audio pop"

## Output format

Before the first MCP call, summarize intake as:

- `trace_path`: confirmed file path (problematic trace)
- `analysis_goal`: what the user wants to understand
- `focus_process`: target process/package, or "unknown"
- `focus_window`: suspicious time range, or "unknown"
- `symptom_category`: one of the categories above
- `assumptions_and_uncertainties`: any open questions or constraints stated by the user
- `first_investigation_hint`: initial direction for the first query
- `reference_trace_path`: file path to a normal / baseline trace, or "none"
- `reference_behavior`: description of what "normal" looks like in the reference trace, or "none"

Confirm all fields are filled (or explicitly marked unknown/none) before proceeding.

## Handoff

- After output format is confirmed → call `open_trace_session` with the problematic trace path
- If a reference trace path is provided, also call `open_trace_session` for the reference trace (store both sessions separately)
- **Determine which reasoning‑lens skills to load**:
  - If `symptom_category` maps to a specific skill in the table above, load that skill alongside `perfetto-command-playbook`.
  - If `symptom_category` is “priority anomaly” → load `perfetto-priority` (and `perfetto-command-playbook`).
  - If `symptom_category` is “CPU scheduler stall” → load both `perfetto-cpu-scheduler-stall` and `perfetto-priority` (since priority misconfiguration is a common root cause of scheduler stalls).
  - If `symptom_category` is “audio glitch” → load `perfetto-audio` (and `perfetto-command-playbook`).
  - If the user explicitly asks about thread priority, nice values, or scheduling policies → load `perfetto-priority` regardless of the primary category.
  - If `symptom_category` is unknown or does not map → load only `perfetto-command-playbook`.
- **When a reference trace is available**, the analysis must include a comparison between the problematic trace and the baseline trace. For priority analysis specifically, the reference trace provides the authoritative “normal” priority values for the same threads; highlight any differences.
- The final report should highlight:
  - Metrics that differ significantly between the two traces (e.g., frame duration, CPU load, binder transactions, IO latency)
  - Any anomalous patterns present only in the problematic trace
  - For priority‑related investigations: explicit comparison of `nice`, `policy`, and `rt_priority` for the suspect threads
  - Confirmation that the reference trace exhibits expected healthy behavior for the same workload and device class
- Do **not** start `open_trace_session` until the trace path and user goal are clear
