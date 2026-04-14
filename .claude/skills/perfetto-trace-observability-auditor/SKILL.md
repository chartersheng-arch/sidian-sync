---
name: perfetto-trace-observability-auditor
description: Audit what the current Perfetto trace can and cannot prove, and plan the deepest still-justified next drill-down. Use when Claude Code needs to bound confidence, explain missing stack evidence, decide whether the trace has enough data to support a thread-level, mechanism-level, or method-level conclusion, or determine whether deeper investigation is still possible.
---

# Perfetto Trace Observability Auditor

This skill is guidance only.
Do not call `Task Output`, `read_task`, or any task-result retrieval mechanism using `perfetto-trace-observability-auditor` as an ID.

## Goal

Determine the observability ceiling of the current trace: what it can prove directly, what it can only suggest, what is impossible to confirm, and whether one more focused query can still deepen the conclusion.

## When to use

- When the investigation is nearing conclusion and confidence needs bounding
- When the triage-reasoner's pre-stop review triggers the observability check
- When the model is unsure whether deeper investigation is still justified
- When the user asks for the exact method or call stack
- When the report needs a confidence and limitation section
- When the investigation suspects deadlock or lock contention but evidence is uncertain

## Audit checklist

Check whether the trace appears to support each capability, using the suggested verification:

| Capability | How to verify |
|-----------|---------------|
| Process and thread identity | `list_processes_threads` or `thread`/`process` tables |
| Frame-timeline analysis | `actual_frame_timeline_slice` exists in schema |
| Nested slice analysis | `parent_id` non-null in `slice` for target thread |
| Scheduler analysis | `thread_state` and `sched` tables have data for target window |
| Binder or IPC analysis | Binder-named slices exist in `slice` table |
| Lock-contention or wait-state analysis | Monitor/mutex/futex/contention slices exist |
| Stack-like or method-level attribution | Profile/stack/sample/callsite tables in schema |
| Memory or GC analysis | GC-named slices scoped to target process exist |

## Key decision questions

After the checklist, explicitly answer these three questions:

1. **Data vs query gap**: Is the current conclusion limited by missing trace data, or only by missing queries that could still be run?
2. **Disambiguation potential**: Is there one more query that could distinguish competing mechanisms?
3. **Ceiling reached**: Has the model stopped because the trace ceiling is truly reached, or has it stopped too early?

## SQL cookbook

### 1. Quick schema capability check (key tables existence)

```sql
SELECT name FROM sqlite_master
WHERE type IN ('table', 'view')
  AND (name IN ('actual_frame_timeline_slice', 'expected_frame_timeline_slice',
                 'thread_state', 'sched', 'counter', 'cpu_counter_track')
    OR name GLOB '*profile*' OR name GLOB '*stack*'
    OR name GLOB '*sample*' OR name GLOB '*callsite*')
ORDER BY name
```

### 2. Check nested slice depth for target thread

```sql
SELECT
    MAX(s.depth) AS max_depth,
    COUNT(CASE WHEN s.parent_id IS NOT NULL THEN 1 END) AS nested_count,
    COUNT(*) AS total_slices
FROM slice s
JOIN thread_track tt ON s.track_id = tt.id
WHERE tt.utid = {{target_utid}}
  AND s.ts BETWEEN {{window_start}} AND {{window_end}}
```

### 3. Check thread_state data coverage for target thread

```sql
SELECT
    COUNT(*) AS state_count,
    MIN(ts.ts) AS earliest,
    MAX(ts.ts + ts.dur) AS latest,
    SUM(ts.dur)/1e6 AS total_covered_ms
FROM thread_state ts
WHERE ts.utid = {{target_utid}}
  AND ts.ts BETWEEN {{window_start}} AND {{window_end}}
```

## Output format

Always report in this shape:

- `supported_depth`: what evidence tiers the trace supports (method / call-chain / blocking-chain / frame / thread+slice / thread-only)
- `unsupported_depth`: what evidence tiers are absent
- `current_limit`: what is limiting the current conclusion
- `can_drill_deeper`: yes or no
- `next_depth_target`: what deeper tier could be reached
- `best_next_query`: the single best query to go deeper (if can_drill_deeper = yes)
- `why_that_query`: why this specific query most reduces uncertainty
- `reporting_ceiling`: whether the final report should stay at module level, thread level, or method level

## Deepening guidance

If the trace still supports deeper work, recommend **one** concrete next move. Prefer the single query that most reduces uncertainty:

- `thread_state` inside the bad window → separate CPU work from blocking wait
- `parent_id` queries → extract a dominant call chain under a long parent slice
- `actual_frame_timeline_slice` → lock onto the worst frames
- Binder, lock, futex, or wait-like slices inside the critical window
- GC or memory-pressure events aligned against the bad frame window

When recommending deeper work, prefer the single query that most reduces uncertainty rather than a broad search.

When `can_drill_deeper = no`, recommend what additional trace categories (e.g., method profiling, GPU counters, memory events) would improve the diagnosis in a future trace collection.

## Guardrails

- Do not claim stack traces or call stacks exist unless they were actually observed.
- Do not overstate certainty when the trace lacks the needed categories.
- If a report is forced to stay at "thread + slice" level, say that explicitly.
- Do not use this skill as an excuse to stop early if a deeper query is still available.
- If a competing mechanism can still be falsified with one more focused query, recommend that query instead of declaring the trace insufficient.

## Handoff

- If `can_drill_deeper = yes` → return the `best_next_query` to `perfetto-triage-reasoner` for execution; do not declare convergence
- If `can_drill_deeper = no` → confirm the observability ceiling to `perfetto-triage-reasoner`; convergence may proceed
- The `reporting_ceiling` value should be carried forward to `perfetto-report-writer` for the confidence and limitations section
