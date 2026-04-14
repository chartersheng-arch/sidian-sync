---
name: perfetto-cpu-scheduler-stall
description: Investigate CPU starvation and scheduler-driven stalls in Perfetto traces. Use when a thread is runnable but progress is delayed or system load appears to block execution.
---

# Perfetto CPU Scheduler Stall

This skill is guidance only.
Do not call `Task Output`, `read_task`, or any task-result retrieval mechanism using `perfetto-cpu-scheduler-stall` as an ID.

## Goal

Determine why a critical thread failed to get CPU time: is it global load, cpuset/affinity pressure, CPU frequency limits, a single dominant competitor, or high-frequency preemption?

## When to use

- A thread has high runnable (R / R+) time relative to its slice duration
- A jank frame or slow operation shows the critical thread waiting for CPU rather than doing work
- The user suspects system load, background interference, or scheduling unfairness

## Primary questions

1. Which threads experience the highest runnable delay?
2. Which threads or processes consume CPU in the same window?
3. Is the problem global load, affinity pressure, frequency limits, or one dominant competitor?
4. Is the runnable delay sustained or fragmented into many short bursts?

## Evidence checklist

- [ ] Target thread utid / tid identified
- [ ] `thread_state` distribution in the problem window (Running / R / R+ / D / S)
- [ ] Runnable (R / R+) cumulative time and percentage of total slice duration
- [ ] Top-N longest single runnable intervals
- [ ] Competing threads on the same CPU / same cpuset in the problem window
- [ ] CPU frequency values during the problem window
- [ ] Whether the target thread migrates across clusters repeatedly

## Reasoning pattern

1. **Identify** the blocked thread or process experiencing progress delay
2. **Locate** the interval where progress should have occurred but did not
3. **Quantify** the `thread_state` distribution inside that interval — especially Runnable vs Running vs D
4. **Test** which delay category dominates:
   - Runnable high + all CPUs busy → global load
   - Runnable high + only target cpuset busy → affinity/cpuset constraint
   - Running but slow progress → CPU frequency may be low
   - One thread dominates CPU in the window → single competitor
   - Many short Runnable bursts → high-frequency preemption / migration
5. **Revise** the hypothesis after each query

## SQL cookbook

### 1. Thread state distribution in the problem window

```sql
SELECT
    ts.state,
    COUNT(*) AS count,
    SUM(ts.dur)/1e6 AS total_dur_ms
FROM thread_state ts
WHERE ts.utid = {{target_utid}}
  AND ts.ts BETWEEN {{window_start}} AND {{window_end}}
GROUP BY ts.state
ORDER BY total_dur_ms DESC
```

### 2. Top-N longest runnable intervals

```sql
SELECT
    ts.ts, ts.dur/1e6 AS dur_ms, ts.state, ts.cpu
FROM thread_state ts
WHERE ts.utid = {{target_utid}}
  AND ts.state IN ('R', 'R+')
  AND ts.ts BETWEEN {{window_start}} AND {{window_end}}
ORDER BY ts.dur DESC
LIMIT 15
```

### 3. Competing threads on the same CPU during the window

```sql
SELECT
    t.name AS thread_name, t.tid,
    p.name AS process_name, p.pid,
    SUM(s.dur)/1e6 AS cpu_time_ms
FROM sched s
JOIN thread t ON s.utid = t.utid
JOIN process p ON t.upid = p.upid
WHERE s.cpu = {{target_cpu}}
  AND s.ts BETWEEN {{window_start}} AND {{window_end}}
GROUP BY s.utid
ORDER BY cpu_time_ms DESC
LIMIT 15
```

### 4. CPU frequency during the window

```sql
SELECT
    c.ts, c.value AS freq_khz
FROM counter c
JOIN cpu_counter_track ct ON c.track_id = ct.id
WHERE ct.name = 'cpufreq'
  AND ct.cpu = {{target_cpu}}
  AND c.ts BETWEEN {{window_start}} AND {{window_end}}
ORDER BY c.ts
```

## Classification / Decision tree

```
Thread has high runnable delay
│
├─ All CPUs in the cpuset are busy
│  │
│  ├─ System-wide utilization > 80%
│  │  → Global CPU load too high
│  │  → Check top CPU consumers across all processes
│  │
│  └─ Only target cpuset cores are saturated
│     → Affinity / cpuset constraint
│     → Check cpuset config; consider wider placement
│
├─ CPU has idle time but thread still waits
│  → Scheduling policy or priority issue
│  → Check if top-app boost / uclamp is effective
│
├─ Thread gets CPU but executes slowly
│  → CPU frequency may be throttled or ramping slowly
│  → Check cpufreq counter for low values or slow ramp
│
├─ One thread dominates > 50% CPU in the window
│  → Single competitor squeezing out the target
│  → Identify the competitor process/thread
│
└─ Many short Runnable bursts (< 1ms each but frequent)
   → High-frequency preemption or cross-cluster migration
   → Check migration pattern and wakeup frequency
```

## MCP usage guidance

Prefer thin tools:

- `describe_trace_schema` — verify `thread_state`, `sched`, `counter`, `cpu_counter_track` availability
- `list_processes_threads` — identify target thread and potential competitors
- `run_trace_metric("overview")` or `run_trace_metric("trace_bounds")` when helpful
- `query_trace_sql(...)` — primary tool for all scheduler evidence

Scheduler-specific guidance:

- Runnable delay analysis starts with `thread_state` WHERE state IN ('R', 'R+')
- Competitor identification uses `sched` table filtered by CPU and time window
- CPU frequency uses `counter` + `cpu_counter_track` WHERE name = 'cpufreq'
- Always quantify Runnable percentage before concluding scheduler stall

Do not follow a fixed query sequence. Let each previous result decide the next query.

## Output format

After investigation, structure findings as:

- **Target thread**: name, tid, utid
- **Runnable delay**: cumulative ms and percentage of problem window
- **Delay pattern**: sustained block vs fragmented short bursts
- **Dominant cause**: global load / cpuset constraint / frequency limit / single competitor / preemption churn
- **Top competitors**: process/thread names consuming CPU in the same window
- **CPU frequency**: observed range during the window
- **Next investigation direction**: what remains uncertain

## Guardrails

- Do not claim scheduler root cause until both the blocked victim and the competing or delaying factor are evidenced.
- Do not confuse D-state (IO wait / resource block) with Runnable (waiting for CPU) — they are fundamentally different causes.
- Do not look only at cumulative Runnable time — distinguish sustained long waits from many short ones; the mitigation differs.
- Do not ignore CPU frequency — a thread that gets CPU at a low frequency may appear "running" but still be slow.
- Do not attribute all Runnable delay to "system busy" without identifying the specific competing threads.
- Do not overlook cross-cluster migration overhead — frequent big-to-little or little-to-big transitions add latency.

## Escalation / Handoff

- If confirmed as scheduler delay → feed to `perfetto-root-cause-classifier` for formal mechanism bucketing
- If the Runnable delay is caused by a Binder transaction blocking the CPU path → consider loading `perfetto-binder-latency`
- If the competitor is a background process → mitigation direction is cpuset/cgroup protection for top-app
- If CPU frequency is the bottleneck → mitigation direction is frequency governor / uclamp tuning
- After convergence → hand off to `perfetto-triage-reasoner` for convergence check and report flow
