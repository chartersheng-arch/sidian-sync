---
name: perfetto-jank-frame-analysis
description: Investigate jank, frame misses, and rendering stalls in Perfetto traces. Use when the user reports stutter, missed deadlines, or rendering instability.
---

# Perfetto Jank Frame Analysis

This skill is guidance only.
Do not call `Task Output`, `read_task`, or any task-result retrieval mechanism using `perfetto-jank-frame-analysis` as an ID.

## Goal

Identify which frames missed their deadlines and determine the dominant cause: UI thread work, RenderThread/GPU, SurfaceFlinger, Binder, CPU scheduling, or IO.

## When to use

- The user reports stutter, jank, or dropped frames during scrolling, animation, or interaction
- Frame timeline data shows missed deadlines
- The investigation needs to anchor on specific bad frames and trace back to the blocking work

## Primary questions

1. Which frames missed their deadlines?
2. Which thread or dependency dominated the worst frame windows?
3. Is the root cause on UI, RenderThread, SurfaceFlinger, Binder, or CPU scheduling?

## Evidence checklist

- [ ] Dedicated frame-timeline tables exist (`actual_frame_timeline_slice`, `expected_frame_timeline_slice`)
- [ ] Janky frames identified with `jank_type`, duration, and layer
- [ ] Worst frame windows isolated (ts, dur, frame_number)
- [ ] UI thread slices inside the worst frame window (doFrame, input, traversal, measure, layout, draw)
- [ ] RenderThread slices inside the worst frame window (syncAndDrawFrame, dequeueBuffer, eglSwapBuffers)
- [ ] Main-thread `thread_state` distribution inside the worst frame window
- [ ] SurfaceFlinger or composition evidence if available
- [ ] Binder calls overlapping the frame window
- [ ] GPU-related counters or composition fields (`gpu_composition`, `on_time_finish`)

## Reasoning pattern

1. Check whether dedicated frame-timeline tables exist before doing broad keyword search on `slice`
2. Identify janky frames and their `jank_type`, duration, and layer first
3. Anchor the investigation on one bad frame window
4. Isolate one suspicious frame window using real evidence
5. Inspect the dominant work on UI thread, RenderThread, SurfaceFlinger, or related dependencies
6. Test whether the bottleneck is app work, Binder wait, GPU/render dependency, or scheduler delay
7. Revise the hypothesis after each query

## SQL cookbook

### 1. Jank frame statistics by jank_type

```sql
SELECT
    jank_type,
    COUNT(*) AS frame_count,
    AVG(dur)/1e6 AS avg_dur_ms,
    MAX(dur)/1e6 AS max_dur_ms
FROM actual_frame_timeline_slice
WHERE jank_type != 'None'
GROUP BY jank_type
ORDER BY frame_count DESC
```

### 2. Worst janky frames for target layer (TOP-N)

```sql
SELECT
    ts, dur/1e6 AS dur_ms, jank_type,
    layer_name, display_frame_token, surface_frame_token,
    on_time_finish, gpu_composition
FROM actual_frame_timeline_slice
WHERE jank_type != 'None'
  AND layer_name GLOB '*{{target_package}}*'
ORDER BY dur DESC
LIMIT 10
```

### 3. UI thread top slices inside a frame window

```sql
SELECT
    s.name, s.ts, s.dur/1e6 AS dur_ms, s.id, s.parent_id
FROM slice s
JOIN thread_track tt ON s.track_id = tt.id
WHERE tt.utid = {{main_thread_utid}}
  AND s.ts BETWEEN {{frame_ts}} AND {{frame_ts}} + {{frame_dur}}
  AND s.dur > 500000
ORDER BY s.dur DESC
LIMIT 20
```

### 4. RenderThread slices inside a frame window

```sql
SELECT
    s.name, s.ts, s.dur/1e6 AS dur_ms, s.id, s.parent_id
FROM slice s
JOIN thread_track tt ON s.track_id = tt.id
WHERE tt.utid = {{render_thread_utid}}
  AND s.ts BETWEEN {{frame_ts}} AND {{frame_ts}} + {{frame_dur}}
  AND s.dur > 500000
ORDER BY s.dur DESC
LIMIT 20
```

### 5. Main-thread thread_state during a frame window

```sql
SELECT
    ts.state,
    COUNT(*) AS count,
    SUM(ts.dur)/1e6 AS total_dur_ms
FROM thread_state ts
WHERE ts.utid = {{main_thread_utid}}
  AND ts.ts BETWEEN {{frame_ts}} AND {{frame_ts}} + {{frame_dur}}
GROUP BY ts.state
ORDER BY total_dur_ms DESC
```

## Classification / Decision tree

```
Frame missed deadline
│
├─ UI thread doFrame / traversal is long
│  │
│  ├─ Running > 50% of frame duration
│  │  → App work dominates (measure / layout / draw / onBindViewHolder)
│  │  → Drill into child slices for the heaviest component
│  │
│  ├─ D-state > 40%
│  │  → IO blocking during frame (database / file read / decode)
│  │  → Check for IO-related child slices
│  │
│  └─ Runnable (R/R+) > 30%
│     → CPU scheduling delay during frame
│     → Load perfetto-cpu-scheduler-stall
│
├─ RenderThread is the bottleneck (UI thread finishes early)
│  │
│  ├─ syncAndDrawFrame / drawFrame long
│  │  → GPU rendering load heavy
│  │  → Check gpu_composition, gpufreq counter, PrevGpuFrameMissed
│  │
│  └─ dequeueBuffer / queueBuffer long
│     → Buffer queue contention or GPU completion wait
│     → Check buffer queue depth and GPU counters
│
├─ SurfaceFlinger side delay
│  → Composition path or display pipeline issue
│  → Check SF layer composition and HWC evidence
│
├─ Binder call overlaps frame window
│  → Cross-process IPC during frame execution
│  → Load perfetto-binder-latency
│
└─ Frame interval uneven but individual frames are not long
   → Vsync scheduling anomaly or Choreographer callback delay
   → Check doFrame callback timestamps and vsync pattern
```

## High-value entry points

When available, prefer this order of evidence:

1. `actual_frame_timeline_slice`
2. `expected_frame_timeline_slice`
3. `thread`, `process`, `thread_track`
4. `slice`
5. `sched`

Do not start with broad keyword search on the entire `slice` table unless dedicated frame-timeline data is absent.

## Query correction rules

- If a SQL query fails because of an unknown column, inspect table structure before retrying.
- For `slice` to thread mapping, prefer `slice.track_id -> thread_track.id -> thread_track.utid -> thread.utid`.
- For `sched`, prefer `sched.utid -> thread.utid`.
- Do not guess `slice.tid`, `slice.thread_id`, or `sched.thread_id` without confirming schema.

## MCP usage guidance

Prefer thin tools:

- `describe_trace_schema` — verify frame-timeline tables exist before querying them
- `list_processes_threads` — identify target app process, main thread, and RenderThread
- `run_trace_metric("overview")` or `run_trace_metric("trace_bounds")` when helpful
- `query_trace_sql(...)` — primary tool for all frame and slice evidence

Jank-specific guidance:

- Always check whether `actual_frame_timeline_slice` and `expected_frame_timeline_slice` exist first
- When frame-timeline tables exist, use `jank_type != 'None'` to quickly locate janky frames
- Filter by `layer_name` to scope to the target app's frames
- After finding the worst frame, use its ts/dur as the window for main-thread and RenderThread slice queries
- Check `gpu_composition` and `on_time_finish` fields when suspecting render-path issues

Do not follow a fixed query sequence. Let each previous result decide the next query.

## Output format

After investigation, structure findings as:

- **Jank summary**: total janky frames, dominant jank_type, worst frame duration
- **Worst frame window**: ts → ts+dur, duration ms
- **Dominant thread**: UI / RenderThread / SurfaceFlinger
- **Delay breakdown**: Running% / D% / R% for the critical thread in the worst frame
- **Top blocking slices**: name + duration for the 3-5 heaviest
- **GPU/render evidence**: gpu_composition, on_time_finish stats if available
- **Root cause category**: app work / IO / sched delay / render-GPU / Binder / composition
- **Next investigation direction**: what remains uncertain

## Stop conditions for jank

Stop deep drilling when all of the following are true:

- at least one janky frame is identified
- the dominant bad frame window is identified
- the dominant blocking thread or dependency is identified
- additional queries would only add detail, not change the conclusion

## Guardrails

- Do not claim jank root cause until at least one frame-adjacent window and one dominant thread or dependency are both evidenced.
- Do not start with broad `slice` name LIKE searches when frame-timeline tables are available — use the dedicated tables first.
- Do not attribute all jank to "app work heavy" without checking `thread_state` — the main thread may be in D-state (IO) or R-state (sched delay).
- Do not ignore RenderThread — if UI thread finishes within budget but the frame is still late, RenderThread or GPU is the bottleneck.
- Do not conflate `queueBuffer` latency with "app is slow" — it may be GPU completion wait, not app CPU work (check `gpu_composition` field).
- Do not treat frame interval irregularity as the same problem as long individual frames — they have different mechanisms.

## Escalation / Handoff

- If jank is dominated by app CPU work → proceed to `perfetto-root-cause-classifier` for formal bucketing
- If jank is caused by Binder calls during frame → load `perfetto-binder-latency`
- If jank is caused by CPU scheduling delay → load `perfetto-cpu-scheduler-stall`
- If GPU / render path is dominant → check GPU counters and composition evidence, then classify
- After convergence → hand off to `perfetto-triage-reasoner` for convergence check and report flow
