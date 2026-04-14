---
name: perfetto-startup-latency
description: Investigate slow startup, delayed first frame, and launch-phase stalls in Perfetto traces. Use when the main question is why an app launch is slow or visibly blocked before becoming interactive.
---

# Perfetto Startup Latency

This skill is guidance only.
Do not call `Task Output`, `read_task`, or any task-result retrieval mechanism using `perfetto-startup-latency` as an ID.

## Goal

Identify the critical path of app launch and determine what dominates the delay: app code execution, IO/class loading, Binder calls, CPU scheduling, or first-frame rendering.

## When to use

- The user reports slow app launch or delayed first frame
- A startup-related trace shows long time between activity start and first draw
- The investigation needs to locate the launch window and its dominant blocker

## Primary questions

1. When does the launch window begin and end?
2. Which thread owns the critical path?
3. Is the delay dominated by app work, Binder waits, CPU starvation, IO, or rendering?
4. Are there hidden blockers before `Application.onCreate` (e.g., ContentProvider initialization)?

## Evidence checklist

- [ ] Target app process and main thread identified (upid, utid)
- [ ] Launch window boundaries estimated (start marker → first frame or `reportFullyDrawn`)
- [ ] Main-thread `thread_state` distribution inside launch window (Running / D / R / S)
- [ ] Top-N longest slices on main thread inside launch window
- [ ] Binder calls during launch window (caller-side slices on main thread)
- [ ] RenderThread activity and first-frame timing
- [ ] ContentProvider.onCreate or early initialization slices (before Application.onCreate)
- [ ] Whether `android_startup` metric or `reportFullyDrawn` slice exists in the trace

## Reasoning pattern

1. **Identify** the target app process and main thread
2. **Locate** the launch window using evidence from slices (`activityStart`, `bindApplication`, `activityResume`), frames, or app lifecycle tracks
3. **Quantify** the main-thread `thread_state` distribution inside the launch window to separate CPU work from IO wait from scheduling delay
4. **Inspect** the longest slices inside the launch window and their child slices
5. **Check** dependencies that block the critical path: Binder calls, ContentProvider init, class loading, resource loading
6. **Verify** whether first-frame rendering (RenderThread) adds significant delay after main-thread work completes
7. **Revise** the launch hypothesis after each result

## SQL cookbook

### 1. Find launch-related slices for the target process

```sql
SELECT
    s.name, s.ts, s.dur/1e6 AS dur_ms, s.track_id, s.id, s.parent_id
FROM slice s
JOIN thread_track tt ON s.track_id = tt.id
JOIN thread t ON tt.utid = t.utid
WHERE t.upid = {{target_upid}}
  AND (s.name GLOB '*activityStart*'
    OR s.name GLOB '*bindApplication*'
    OR s.name GLOB '*activityResume*'
    OR s.name GLOB '*reportFullyDrawn*'
    OR s.name GLOB '*inflate*'
    OR s.name GLOB '*ContentProvider*'
    OR s.name GLOB '*Application.onCreate*')
ORDER BY s.ts
```

### 2. Top-N longest slices on main thread during launch window

```sql
SELECT
    s.name, s.ts, s.dur/1e6 AS dur_ms, s.id, s.parent_id
FROM slice s
JOIN thread_track tt ON s.track_id = tt.id
WHERE tt.utid = {{main_thread_utid}}
  AND s.ts BETWEEN {{launch_start}} AND {{launch_end}}
  AND s.dur > 1000000
ORDER BY s.dur DESC
LIMIT 20
```

### 3. Main-thread thread_state distribution during launch window

```sql
SELECT
    ts.state,
    COUNT(*) AS count,
    SUM(ts.dur)/1e6 AS total_dur_ms
FROM thread_state ts
WHERE ts.utid = {{main_thread_utid}}
  AND ts.ts BETWEEN {{launch_start}} AND {{launch_end}}
GROUP BY ts.state
ORDER BY total_dur_ms DESC
```

### 4. Binder calls on main thread during launch window

```sql
SELECT
    s.name, s.ts, s.dur/1e6 AS dur_ms
FROM slice s
JOIN thread_track tt ON s.track_id = tt.id
WHERE tt.utid = {{main_thread_utid}}
  AND s.ts BETWEEN {{launch_start}} AND {{launch_end}}
  AND s.name GLOB '*binder*'
ORDER BY s.dur DESC
LIMIT 15
```

## Classification / Decision tree

```
App launch is slow
│
├─ Main thread Running > 50% of launch window
│  → App code execution dominates (bindApplication / onCreate / layout / inflate)
│  → Drill into child slices to find the heaviest work
│
├─ Main thread D-state > 40% of launch window
│  → IO blocking dominates (class loading / dex / file reads / database)
│  → Check for specific IO-related slices or frequent short D-states
│
├─ Main thread Runnable (R/R+) > 30% of launch window
│  → CPU scheduling delay during launch
│  → Load perfetto-cpu-scheduler-stall for deeper analysis
│
├─ Binder slices occupy significant portion of launch window
│  → Cross-process IPC blocking during startup
│  → Load perfetto-binder-latency for service-side investigation
│
├─ Main thread work finishes quickly but first frame is late
│  → RenderThread or first-frame rendering is the bottleneck
│  → Check RenderThread slices and GPU evidence
│
└─ Large slices before Application.onCreate
   → ContentProvider initialization or early framework work
   → Check ContentProvider.onCreate and provider-related slices
```

## MCP usage guidance

Prefer thin tools:

- `describe_trace_schema` — check for `android_startup` metric availability and launch-related tables
- `list_processes_threads` — identify target app process and main thread
- `run_trace_metric("android_startup")` — use if available; gives structured startup breakdown
- `run_trace_metric("overview")` or `run_trace_metric("trace_bounds")` when helpful
- `query_trace_sql(...)` — primary tool for all startup evidence

Startup-specific guidance:

- First check whether `android_startup` metric exists — it provides pre-computed launch breakdown
- Search `slice` for startup markers: `activityStart`, `bindApplication`, `activityResume`, `reportFullyDrawn`
- After finding the launch window, immediately query `thread_state` to classify Running vs D vs R
- Verify RenderThread activity to check whether first-frame rendering adds delay after main-thread work

Do not follow a fixed query sequence. Let each previous result decide the next query.

## Output format

After investigation, structure findings as:

- **Launch window**: start_ts → end_ts, total duration ms
- **Critical path owner**: which thread dominates (main / RenderThread / Binder)
- **Delay breakdown**: Running% / D% / R% / Binder% of the launch window
- **Top blocking slices**: name + duration for the 3-5 heaviest
- **Hidden blockers**: ContentProvider or pre-onCreate work if found
- **Dominant cause**: app work / IO / Binder / sched delay / render
- **Next investigation direction**: what remains uncertain

## Guardrails

- Do not claim startup root cause until the launch window and the blocking critical-path work are both evidenced.
- Do not treat the entire trace duration as the launch window — find precise start/end markers from lifecycle slices or frame evidence.
- Do not ignore ContentProvider.onCreate — it executes before Application.onCreate and can be a hidden blocker, especially with multiple providers.
- Do not look only at the main thread — RenderThread (first-frame render) and Binder threads (cross-process calls) are also on the launch critical path.
- Do not conclude "app work is heavy" without checking `thread_state` — the main thread may be blocked on IO or Binder rather than executing code.

## Escalation / Handoff

- If the dominant delay is Binder calls during launch → load `perfetto-binder-latency`
- If the dominant delay is CPU scheduling → load `perfetto-cpu-scheduler-stall`
- If the dominant delay is app code execution → proceed to `perfetto-root-cause-classifier` to formally classify
- If IO/class loading dominates → classify as IO mechanism and carry forward to mitigation
- After convergence → hand off to `perfetto-triage-reasoner` for convergence check and report flow
