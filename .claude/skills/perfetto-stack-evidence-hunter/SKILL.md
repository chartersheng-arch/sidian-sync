---
name: perfetto-stack-evidence-hunter
description: Hunt for the deepest available execution evidence in the current trace, including nested slices, parent-child relationships, frame-specific work, Binder chains, and any method-level or stack-like signals. Use when Claude Code needs to know whether it can move from thread-level diagnosis to call-chain-level diagnosis.
---

# Perfetto Stack Evidence Hunter

This skill is guidance only.
Do not call `Task Output`, `read_task`, or any task-result retrieval mechanism using `perfetto-stack-evidence-hunter` as an ID.

## Goal

Determine the deepest level of execution evidence this trace can actually support, and extract the best available call chain or blocking chain for the report.

## When to use

- Before convergence, to check whether deeper evidence is still reachable
- When the investigation needs a concrete call chain or blocking chain for the report
- When the triage-reasoner's pre-stop review triggers the depth check

## Core question

Ask:

"What is the deepest level of execution evidence this trace can actually support?"

## Evidence depth ladder

Check for evidence in this order (deepest first):

1. Profile, sample, or stack-related tables if present → **method-level**
2. Nested slices with `parent_id` relationships → **call-chain level**
3. Binder-adjacent or lock-adjacent slices → **blocking-chain level**
4. Frame-timeline or specialized Android views → **frame-level**
5. Thread-associated slices through `thread_track` → **thread + slice level**
6. Only thread-level timing evidence (thread_state / sched) → **thread-level only**

## Evidence checklist

- [ ] `parent_id` in `slice` — do target slices have nested children?
- [ ] Nested operations under one long parent slice — how many levels deep?
- [ ] Frame-timeline tables (`actual_frame_timeline_slice`, `expected_frame_timeline_slice`)
- [ ] Binder-related slices (binder transaction, binder reply)
- [ ] Lock, contention, monitor, mutex, futex, wait-like slices
- [ ] Profile/sample/stack-oriented tables visible in schema
- [ ] `depth` field in slice table (if available)

## Depth assessment flow

```
Assessing evidence depth for the current trace
│
├─ Schema contains profile / stack / sample tables?
│  → Method-level evidence may be reachable
│  → Query those tables for the target window
│
├─ Target long slice has parent_id AND children with multiple nesting levels?
│  → Call-chain level evidence
│  → Extract the dominant parent → child → grandchild chain
│
├─ Target window contains Binder / lock / wait slices?
│  → Blocking-chain level evidence
│  → Reconstruct caller → service or holder → waiter chain
│
├─ Thread_track-associated slices exist for target thread?
│  → Thread + slice level evidence
│  → Can attribute time to named operations but not deeper
│
└─ Only thread_state / sched data available?
   → Thread-level timing only
   → Report can show Running/D/R distribution but not what code ran
```

## SQL cookbook

### 1. Check if a long slice has child slices

```sql
SELECT
    s.name, s.ts, s.dur/1e6 AS dur_ms, s.depth, s.parent_id
FROM slice s
WHERE s.parent_id = {{target_slice_id}}
ORDER BY s.dur DESC
LIMIT 20
```

### 2. Find nesting depth under a parent slice

```sql
SELECT
    s.name, s.ts, s.dur/1e6 AS dur_ms, s.depth, s.id, s.parent_id
FROM slice s
JOIN thread_track tt ON s.track_id = tt.id
WHERE tt.utid = {{target_utid}}
  AND s.ts BETWEEN {{parent_ts}} AND {{parent_ts}} + {{parent_dur}}
ORDER BY s.depth DESC, s.dur DESC
LIMIT 30
```

### 3. Check for profile/stack/sample tables in schema

```sql
SELECT name FROM sqlite_master
WHERE type IN ('table', 'view')
  AND name GLOB '*profile*' OR name GLOB '*stack*' OR name GLOB '*sample*' OR name GLOB '*callsite*'
```

### 4. Find blocking-chain evidence (Binder / lock / wait slices in window)

```sql
SELECT
    s.name, s.ts, s.dur/1e6 AS dur_ms, t.name AS thread_name, p.name AS process_name
FROM slice s
JOIN thread_track tt ON s.track_id = tt.id
JOIN thread t ON tt.utid = t.utid
JOIN process p ON t.upid = p.upid
WHERE s.ts BETWEEN {{window_start}} AND {{window_end}}
  AND (s.name GLOB '*binder*' OR s.name GLOB '*lock*' OR s.name GLOB '*contention*'
       OR s.name GLOB '*monitor*' OR s.name GLOB '*mutex*' OR s.name GLOB '*futex*')
ORDER BY s.dur DESC
LIMIT 20
```

## Output format

Always summarize in this shape:

- `current_depth`: the deepest evidence tier reached (method / call-chain / blocking-chain / frame / thread+slice / thread-only)
- `supporting_tables`: tables or fields that support that depth
- `can_conclude_at_this_depth`: what can be concluded
- `cannot_conclude_at_this_depth`: what cannot be concluded
- `deeper_query`: the next best query to go one level deeper, if possible
- `recommendation`: if depth is insufficient, recommend a stronger trace collection strategy

## Guardrails

- Do not promise method-level attribution unless the trace actually contains method-level or equivalent nested evidence.
- If the trace only supports thread-level timing, say that clearly.
- If stack-level evidence is absent, recommend a stronger trace collection strategy rather than pretending certainty.
- Do not assume `parent_id` chains exist without querying — many traces only have flat slices.

## Handoff

- After depth assessment → `perfetto-trace-observability-auditor` to check whether the ceiling has been reached or further drilling is justified
- Then → back to `perfetto-triage-reasoner` for convergence decision
- If call-chain or blocking-chain evidence was found → it should be included in the final report via `perfetto-report-writer`
