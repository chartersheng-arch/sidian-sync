---
name: perfetto-binder-latency
description: Investigate Binder transaction delays in Perfetto traces. Use when IPC waits, service congestion, or synchronous transaction latency is suspected.
---

# Perfetto Binder Latency

This skill is guidance only.
Do not call `Task Output`, `read_task`, or any task-result retrieval mechanism using `perfetto-binder-latency` as an ID.

## Goal

Identify the dominant cause of Binder transaction delay: is it service-side work, scheduler wait, thread pool exhaustion, or a chained downstream dependency?

## When to use

- A critical thread is blocked waiting on a synchronous Binder call
- Binder transaction slices appear on the critical path of a jank frame or slow startup
- The user suspects IPC congestion, service latency, or cross-process blocking

## Primary questions

1. Which Binder transactions are slowest?
2. Which caller → callee process/thread pairs dominate the delay?
3. Is the delay inside service execution, scheduler wait, thread pool exhaustion, or a downstream dependency?
4. Does the service itself block on further Binder calls or IO?

## Evidence checklist

- [ ] Binder-related slices on the caller side (name containing `binder transaction`, `binder reply`, etc.)
- [ ] Top-N slowest Binder slices with caller process/thread identity
- [ ] Service-side process/thread that handled the transaction
- [ ] Service-side `thread_state` distribution during the transaction window (Running / D / R / S)
- [ ] Service-side child slices inside the transaction window (what work the service did)
- [ ] Whether multiple Binder threads in the service are busy simultaneously (thread pool saturation)
- [ ] Whether the service itself issues chained Binder calls to another service (A → B → C)

## Reasoning pattern

1. **Identify** the slow Binder transaction or blocked caller thread
2. **Locate** both the caller-side waiting interval and the service-side handling interval
3. **Inspect** the service-side `thread_state` distribution to determine Running vs D-state vs Runnable
4. **Test** which delay category dominates:
   - service code is running (service work heavy)
   - service thread in D-state (service blocked on IO or resource)
   - service thread in Runnable (scheduler delay on service side)
   - no service-side slice found (thread pool exhaustion or dispatch delay)
   - service itself calls another Binder (chained dependency)
5. **Revise** the hypothesis after each query result

## SQL cookbook

### 1. Find slowest Binder slices on the caller side

```sql
SELECT
    s.id, s.ts, s.dur, s.dur/1e6 AS dur_ms, s.name,
    t.name AS thread_name, t.tid,
    p.name AS process_name, p.pid
FROM slice s
JOIN thread_track tt ON s.track_id = tt.id
JOIN thread t ON tt.utid = t.utid
JOIN process p ON t.upid = p.upid
WHERE s.name GLOB '*binder transaction*'
ORDER BY s.dur DESC
LIMIT 10
```

### 2. Service-side thread_state during a transaction window

```sql
SELECT
    ts.state,
    COUNT(*) AS count,
    SUM(ts.dur)/1e6 AS total_dur_ms
FROM thread_state ts
WHERE ts.utid = {{service_utid}}
  AND ts.ts BETWEEN {{txn_start}} AND {{txn_start}} + {{txn_dur}}
GROUP BY ts.state
ORDER BY total_dur_ms DESC
```

### 3. Service-side child slices during transaction window

```sql
SELECT
    s.name, s.ts, s.dur/1e6 AS dur_ms, s.parent_id
FROM slice s
JOIN thread_track tt ON s.track_id = tt.id
WHERE tt.utid = {{service_utid}}
  AND s.ts BETWEEN {{txn_start}} AND {{txn_start}} + {{txn_dur}}
  AND s.dur > 1000000
ORDER BY s.dur DESC
LIMIT 20
```

### 4. Check Binder thread pool saturation (concurrent busy threads)

```sql
SELECT
    t.name AS thread_name, t.tid,
    COUNT(*) AS busy_slices,
    SUM(s.dur)/1e6 AS total_busy_ms
FROM slice s
JOIN thread_track tt ON s.track_id = tt.id
JOIN thread t ON tt.utid = t.utid
WHERE t.upid = {{service_upid}}
  AND t.name GLOB '*Binder*'
  AND s.ts BETWEEN {{window_start}} AND {{window_end}}
  AND s.dur > 100000
GROUP BY t.utid
ORDER BY total_busy_ms DESC
```

## Classification / Decision tree

```
Binder transaction is slow
│
├─ Service-side slice found and is long
│  │
│  ├─ Running > 50% of txn duration
│  │  → Service work is heavy (CPU-bound service logic)
│  │  → Drill into child slices to find what dominates
│  │
│  ├─ D state > 40% of txn duration
│  │  → Service is blocked on IO or resource
│  │  → Check for file, database, or nested blocking evidence
│  │
│  ├─ Runnable (R) > 30% of txn duration
│  │  → Scheduler delay on service side
│  │  → Check CPU competitors in that window
│  │
│  └─ S (sleeping) dominant
│     → Service waiting on lock, condition, or downstream dependency
│     → Check for lock contention or nested Binder calls
│
├─ Service-side slice found but short, yet caller wait is long
│  → Dispatch delay or reply-return scheduling delay
│  → Check caller thread_state after service completes
│
├─ No service-side slice found in window
│  → Thread pool exhaustion or Binder driver dispatch delay
│  → Check how many Binder threads are concurrently busy
│
└─ Service itself issues another Binder call (chained)
   → A → B → C dependency chain
   → Follow the chain to the terminal service
```

## MCP usage guidance

Prefer thin tools:

- `describe_trace_schema` — check whether `binder_transaction` table exists; if not, fall back to `slice` name matching
- `list_processes_threads` — identify caller and service process/thread identities
- `run_trace_metric("overview")` or `run_trace_metric("trace_bounds")` when helpful
- `query_trace_sql(...)` — primary tool for all Binder evidence

Binder-specific guidance:

- First check schema for a dedicated `binder_transaction` table; if present, prefer it over `slice` name matching
- If no dedicated table, use `slice` WHERE name GLOB patterns for binder transaction / binder reply
- After finding the slow transaction, always locate the service-side thread before concluding
- Use `thread_state` on the service-side thread to disambiguate service work vs IO vs sched delay

Do not follow a fixed query sequence. Let each previous result decide the next query.

## Output format

After investigation, structure findings as:

- **Slowest transactions**: top 3-5 with caller → callee identity and duration
- **Dominant delay category**: service work / IO block / sched delay / thread pool exhaustion / chained dependency
- **Service-side breakdown**: Running% / D% / R% / S% during the transaction window
- **Blocking chain**: if chained calls exist, the full A → B → C path
- **Next investigation direction**: what remains uncertain

## Guardrails

- Do not claim Binder root cause until both the slow transaction window and the dominant blocking side are evidenced.
- Do not conclude based only on caller-side wait duration — always check the service side.
- Do not attribute Binder reply delay to slow service work when the real cause may be scheduler delay on reply return.
- Do not ignore chained Binder calls (A → B → C) — only looking at one hop may miss the real bottleneck.
- If service-side thread pool is saturated, the problem is concurrency/throughput, not a single slow transaction.
- If `thread_state` data is missing for the service thread, state that explicitly and reduce confidence.

## Escalation / Handoff

- If the delay is confirmed as Binder-dominant → feed the classification to `perfetto-root-cause-classifier` for formal bucketing
- If service-side shows CPU contention or scheduler delay → consider loading `perfetto-cpu-scheduler-stall`
- If service-side shows IO/D-state → the root cause may be IO rather than Binder itself; reflect this in classification
- If investigation converges → hand off to `perfetto-triage-reasoner` for convergence check and report flow
