---
name: perfetto-triage-reasoner
description: Help Claude Code reason over perfetto-mcp results and choose the next investigative step during Perfetto trace analysis. Use after each tool result to extract direct evidence, update hypotheses, control token usage, and select the single best next SQL or native Perfetto metric.
---

# Perfetto Triage Reasoner

This skill is guidance only.
Do not call `Task Output`, `read_task`, or any task-result retrieval mechanism using `perfetto-triage-reasoner` as an ID.

## Goal

After every MCP result, extract evidence, update hypotheses, and choose the single best next query. Control the investigation loop until convergence or until the trace's observability ceiling is reached.

## When to use

- After every MCP tool result during a Perfetto trace investigation
- When deciding whether to continue drilling or declare convergence
- When the investigation is stuck and needs to re-evaluate hypotheses

---

# Part 1: Per-result reasoning

## Core reasoning loop

Use this skill after every MCP result. For each result, do this in order:

1. Extract direct evidence.
2. Distinguish direct evidence from inference.
3. Update the top hypotheses with confidence notes.
4. Identify the single most important unanswered question.
5. Choose the next tool call that best reduces that uncertainty.
6. Stop if the backend is unavailable or the next step would only repeat the same evidence.

## Investigation priorities

Start from broad structure and quickly narrow:

- schema and trace capability
- relevant process and thread identities
- one concrete hypothesis
- focused drill-down inside a justified time window

## Output format

After each MCP result, structure reasoning as:

- `current_hypothesis`: the leading explanation with confidence (low / medium / high)
- `competing_hypothesis`: strongest alternative, if any
- `direct_evidence`: facts directly observed from the query result
- `inferred`: conclusions drawn from evidence but not directly observed
- `unanswered_question`: the single most important gap
- `next_query`: the exact next MCP call
- `why_this_query`: why this call best reduces the unanswered question

After producing these sections, continue the investigation by actually executing the chosen next tool unless blocked.

---

# Part 2: Investigation playbooks

These are scenario-specific reasoning shortcuts. The detailed SQL templates live in the symptom skills (jank-frame-analysis, binder-latency, etc.). These playbooks provide the **reasoning engine's decision path** for common patterns.

## Playbook: Long slice on main thread

When investigating a long slice (>100ms) on the main thread or other critical threads:

### Step 1: Quantify thread_state distribution (MANDATORY - do this first)

```sql
SELECT
    ts.state,
    COUNT(*) as count,
    SUM(ts.dur)/1000000 as total_dur_ms
FROM thread_state ts
WHERE ts.utid = <main_thread_utid>
  AND ts.ts BETWEEN <slice_ts> AND <slice_ts + slice_dur>
GROUP BY ts.state
```

Calculate:
- D_state% = (D_total_dur / slice_dur) × 100
- Running% = (Running_total_dur / slice_dur) × 100

### Step 2a: If D state > 40% (IO wait suspected)

```sql
-- Check for frequent short D-states (database/file IO pattern)
SELECT
    ts.ts/1000000 as ts_ms,
    ts.dur/1000000 as dur_ms
FROM thread_state ts
WHERE ts.utid = <thread_utid>
  AND ts.state = 'D'
  AND ts.ts BETWEEN <slice_ts> AND <slice_ts + slice_dur>
ORDER BY ts.dur DESC
LIMIT 20
```

Look for:
- Many short D-states (0-5ms each, but sum is significant) → database或小文件 IO
- Few long D-states (>50ms each) → network or large file IO

### Step 2b: If Running > 50% (CPU work suspected)

```sql
-- Check child slices for what work is being done
SELECT
    s.name,
    s.dur/1000000 as dur_ms,
    s.ts
FROM slice s
WHERE s.track_id = <thread_track_id>
  AND s.ts BETWEEN <slice_ts> AND <slice_ts + slice_dur>
  AND s.dur > 1000000
ORDER BY s.dur DESC
LIMIT 20
```

### Step 3: Apply root cause classification

Use the state distribution to classify:
- D state > 50% → "IO, decode, or blocking resource load"
- D state 30-50% → Mixed, mark both as competing causes
- D state < 30% AND Running > 50% → "app main-thread work is too heavy"

Do not treat a single long slice or one slow transaction as convergence by default.

## Playbook: Janky frame

When a janky frame is identified from frame-timeline data:

1. **Identify the worst frame** — use `actual_frame_timeline_slice` WHERE `jank_type != 'None'`, sorted by dur DESC
2. **Determine which thread is late** — check whether the frame's delay is on UI thread, RenderThread, or SurfaceFlinger based on the frame window overlap
3. **Query thread_state for the late thread** inside the frame window — classify Running / D / R / S
4. **Branch by dominant state**:
   - Running high → app work or render work; drill into child slices
   - D-state high → IO blocking during frame; check IO-related slices
   - Runnable high → CPU scheduling delay; check competitors
   - RenderThread dominant → check GPU counters and composition fields

Detailed SQL templates are in `perfetto-jank-frame-analysis`.

## Playbook: High runnable delay

When a thread shows significant time in R / R+ state:

1. **Quantify runnable time** — `thread_state` WHERE state IN ('R', 'R+'), sum dur
2. **Find the top runnable intervals** — sorted by dur DESC
3. **Identify CPU competitors** — `sched` table for the same CPU in the same window
4. **Check CPU frequency** — `counter` + `cpu_counter_track` WHERE name = 'cpufreq'

Detailed SQL templates are in `perfetto-cpu-scheduler-stall`.

## Token control

- Avoid carrying large row sets forward when a short evidence summary is enough
- Paginate large results with `get_query_result` instead of rerunning the same query
- Prefer smaller time windows to broader SQL
- Avoid `SELECT *` unless the result is guaranteed to be tiny
- Prefer one precise query over several speculative ones

---

# Part 3: Convergence control

## Stop conditions

Stop active drilling when one of these is true:

- the best hypothesis has direct supporting evidence at the mechanism level
- the remaining uncertainty comes from missing trace data
- the next query would only restate the same conclusion

Do not treat the investigation as converged if the current evidence still leaves a plausible competing mechanism unresolved.

## Mandatory pre-stop review

Before declaring convergence, explicitly check these three questions **in this order**:

### 1. Mechanism check → load `perfetto-root-cause-classifier`

- Has it reduced the problem to one dominant mechanism, or does it still show a strong competing bucket?
- If IO, CPU contention, Binder, lock contention, GC, render-path delay, or app-self workload still compete, do not stop.

### 2. Depth check → load `perfetto-stack-evidence-hunter`

- Has it already exhausted the deepest available nested-slice or blocking-chain evidence?
- If it identifies a deeper reachable evidence tier, do not stop yet.

### 3. Observability check → load `perfetto-trace-observability-auditor`

- Has it concluded that the current reporting ceiling has truly been reached?
- If it says `can_drill_deeper = yes`, do not stop yet.
- If it recommends a `best_next_query`, that query should normally be executed before convergence.

You may declare convergence only when:

- the dominant mechanism is sufficiently supported
- no strong competing mechanism remains
- the observability ceiling has been reached or the remaining deeper queries are genuinely low value
- there is no still-reachable deeper evidence tier that would materially change the conclusion

Examples of unresolved competing mechanisms:

- a long main-thread slice could still be IO wait rather than pure app CPU work
- a D-state thread could still be lock contention or blocking resource wait
- a slow frame could still be driven by Binder, GC, or scheduler delay unless those are checked or explicitly bounded

### Mandatory checkpoint: IO vs CPU disambiguation

When a long slice (>100ms) is identified on a critical thread:

**Before concluding "app workload" or classifying the root cause:**

1. Query thread_state distribution during the slice window (see Investigation playbook above)
2. Calculate D state % and Running state % relative to slice duration
3. Apply the following decision rule:
   - **D state > 50%** → IO wait is dominant, continue drilling into IO sources
   - **D state 30-50%** → Mixed IO + CPU, both are competing causes
   - **D state < 30% AND Running > 50%** → CPU work is dominant, safe to classify as app workload
   - **thread_state missing** → Cannot disambiguate, mark confidence as medium

**Do not stop investigation** until this checkpoint is completed.

## Non-convergence triggers

Keep drilling when any of these is true:

- the dominant mechanism is still described with words like "suspect", "maybe", "possibly", or "looks like"
- the root-cause classifier still has a strong competing bucket
- the observability auditor still says deeper drilling is possible
- the observability auditor still recommends a high-value next query
- the stack evidence hunter still indicates a deeper reachable evidence tier
- the current conclusion is only "a long slice exists" but not "why that slice became long"
- the evidence shows waiting states, but the waited resource is still unclear
- the report would have to say "likely IO" or "possibly lock contention" without a confirming or falsifying query

Non-convergence triggers are **signals to continue investigating**. Guardrails below are **red-line constraints on behavior**.

## Post-convergence workflow

When a stop condition is met:

1. Stop issuing further investigative SQL by default
2. Summarize why the investigation is considered converged
3. Explicitly state why no higher-value disambiguation query remains
4. Ask the user whether they want to search a history issue library
5. If the user says yes and provides a path, load `perfetto-history-issue-matcher`
6. After history matching, ask whether the user has any additional questions
7. If the user has no further questions, ask whether to generate the final report now
8. Before final report writing, load `perfetto-system-mitigation-advisor` when the report needs Android device-side or platform-side mitigations
9. Only after user confirmation, load `perfetto-report-writer` and generate the final report

Do not keep querying just to add marginal evidence after convergence. Pause for user confirmation before optional history search and final report generation.

## Guardrails

- Do not present inference as direct trace evidence.
- Do not keep querying after `status=blocked` or backend failure.
- Do not issue multiple broad SQL queries when one narrower query can answer the next question.
- Do not stop at symptom-level localization when mechanism-level disambiguation is still possible.
- If IO, lock contention, Binder, GC, or scheduler delay remains plausible, ask for one more query that distinguishes them.

## Handoff

- During active investigation → each MCP result triggers this skill's reasoning loop
- At convergence → invoke pre-stop review skills in order: root-cause-classifier → stack-evidence-hunter → observability-auditor
- After convergence → post-convergence workflow leads to history-matcher (optional) → system-mitigation-advisor → report-writer
- If a specific mechanism dominates → the corresponding symptom skill may be re-loaded for deeper targeted queries
