---
name: perfetto-command-playbook
description: Guide first-pass tool selection for perfetto-mcp. Use when Claude Code needs to choose the first summary, metric, or SQL query for a Perfetto trace without wasting context on oversized or redundant results.
---

# Perfetto Command Playbook

This skill is guidance only.
Do not call `Task Output`, `read_task`, or any task-result retrieval mechanism using `perfetto-command-playbook` as an ID.

## Goal

Pick a small, high-value first-pass tool set after opening a trace session, then branch intelligently based on results. Avoid wasting context on oversized or redundant queries.

## When to use

- Immediately after `open_trace_session` succeeds and before deep investigative SQL
- When switching to a new trace file and needing to establish baseline context
- When the investigation is stuck and needs to reset to a broader view

## First-pass defaults

Start with:

1. `open_trace_session`
2. One lightweight baseline such as `run_trace_metric("overview")`, `run_trace_metric("trace_bounds")`, `describe_trace_schema`, or `list_processes_threads`
3. One hypothesis-driven `query_trace_sql` once the target entity or question is clearer

Do not start with broad SQL against large tables unless the user already gave a precise target window and entity.
Do not create custom shell clients for MCP when direct MCP tools are available.

## Symptom-aware first move

When the intake phase has already identified a symptom category, prefer a differentiated first step:

| Symptom category | Recommended baseline | Recommended first SQL direction |
|-----------------|---------------------|-------------------------------|
| Jank / frame miss | `list_processes_threads` | `actual_frame_timeline_slice` jank stats |
| Startup latency | `list_processes_threads` | Launch-related slices (e.g. `activityStart`, `bindApplication`) |
| Binder latency | `describe_trace_schema` | Check for `binder_transaction` table; if absent, `slice` name matching |
| CPU stall | `list_processes_threads` | `thread_state` distribution for target thread |
| Memory / GC | `run_trace_metric("overview")` | GC-named slices scoped to target process |
| Unknown | `run_trace_metric("overview")` | Follow the overview to pick direction |

When the symptom is unknown, start with `overview` and let the result guide the branch.

## Query strategy

- Let the previous result decide the next branch.
- Prefer SQL that tests one question at a time.
- Use native Perfetto metrics only when they map directly to the question you are asking.
- Avoid embedding scenario conclusions into the tool selection itself.
- For jank investigations, prefer dedicated frame-timeline tables over broad `slice name LIKE '%frame%'` searches when such tables exist.
- Prefer narrower follow-ups over re-running broad summaries.

## Error recovery

- After a SQL column error, inspect table structure with `describe_trace_schema` or a targeted `PRAGMA table_info(...)` before issuing a corrected query.
- Stop and fix the backend first if a tool reports `status=stub`, `status=blocked`, or backend failure.
- If a query returns empty results, verify the table exists and the WHERE conditions are correct before concluding the data is absent.

## First-pass output template

After choosing the first-pass set, frame it like this:

- `baseline_choice`: which MCP call and why it is sufficient
- `known_facts`: what is already known from intake or user context
- `unknown_gaps`: what remains unknown
- `first_hypothesis`: the first hypothesis to test
- `next_mcp_call`: the exact next MCP call
- `why_this_call`: why this call best reduces uncertainty

## Token & cost control

- Do not repeat the same overview query unless the scope changed.
- If a query produces too much output, use `get_query_result` to paginate, or reduce the time window before continuing.
- Avoid `SELECT *` on large tables; always specify columns and add WHERE + LIMIT.
- Prefer one precise query over several speculative ones.
- Do not issue multiple parallel MCP calls in the first pass — sequential evaluation reduces wasted context.

## Anti-patterns

Avoid these common mistakes:

- `SELECT * FROM slice` or `SELECT * FROM sched` without WHERE — result explosion
- `COUNT(*) GROUP BY` on large tables without time-window filter — slow and noisy
- `LIKE '%keyword%'` full-table scan before checking schema for dedicated tables
- Running `overview` + `schema` + `processes` + `trace_bounds` all at once — pick the single most useful one first
- Guessing column names without checking schema — leads to repeated error-retry cycles

## Guardrails

- Do not start investigative SQL before `open_trace_session` succeeds.
- Do not create custom shell/Python/Node clients for MCP when direct MCP tools are available.
- Do not treat broad summaries as conclusions — they are starting points for hypothesis formation.

## Handoff

After the first-pass baseline is complete:

1. Based on the result, load the appropriate symptom-focused skill:
   - Jank → `perfetto-jank-frame-analysis`
   - Startup → `perfetto-startup-latency`
   - Binder → `perfetto-binder-latency`
   - CPU stall → `perfetto-cpu-scheduler-stall`
2. Enter the `perfetto-triage-reasoner` loop for iterative investigation
3. The playbook's role ends once the first hypothesis and target entity are established
