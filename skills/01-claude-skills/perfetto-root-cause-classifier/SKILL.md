---
name: perfetto-root-cause-classifier
description: Classify the dominant mechanism behind a performance problem using evidence already collected from perfetto-mcp. Use when Claude Code has identified a slow frame, long slice, or suspicious window and needs to decide whether the main cause is app work, render path, CPU contention, Binder delay, lock contention, GC, IO, or something else.
---

# Perfetto Root Cause Classifier

This skill is guidance only.
Do not call `Task Output`, `read_task`, or any task-result retrieval mechanism using `perfetto-root-cause-classifier` as an ID.

## Goal

Decide which causal mechanism the current evidence most strongly supports, and determine whether the classification is ready for convergence or still needs disambiguation.

## When to use

- After enough investigative evidence has been collected (at least thread_state distribution and top slices identified)
- Before declaring convergence in `perfetto-triage-reasoner`
- When a report is about to say vague things like "the app is slow" or "the frame is long" — push one step further

---

# Core classification logic

## Candidate root-cause buckets

Classify the current case into one primary bucket when possible:

- app main-thread work is too heavy
- render or GPU path is dominant
- CPU contention or scheduler delay
- Binder or IPC blocking
- lock contention or deadlock-like waiting
- GC or memory pressure
- IO, decode, or blocking resource load
- evidence insufficient

## Required reasoning steps

1. List the strongest direct evidence collected so far.
2. Map each evidence item to one or more candidate buckets.
3. Identify the current leading bucket.
4. Identify the strongest competing bucket.
5. State what one missing piece of evidence would disambiguate them.
6. If the competing bucket is still plausible, do not declare convergence yet.

## Output format

Always structure the classification like this:

- `dominant_bucket`: the primary mechanism
- `confidence`: low / medium / high
- `why`: why this bucket currently fits best
- `competing_bucket`: strongest alternative
- `supporting_evidence`: evidence supporting the dominant bucket
- `missing_evidence`: evidence needed before final confirmation
- `next_mcp_call`: to confirm or falsify the classification
- `mitigation_directions`: likely system-side mitigation directions if this bucket is confirmed

---

# Mandatory disambiguation checks

These checks must pass before confirming specific buckets. They are **not optional guardrails** — they are required classification gates.

## Mandatory IO vs CPU work disambiguation

Before classifying a long slice as "app main-thread work is too heavy":

1. **Check thread_state time distribution inside the slice window**:
   - Query `thread_state` for the specific thread during the slice time range
   - Calculate the percentage of time in `D` (IO wait) vs `Running` vs `R` (runnable)
   - If `D` state > 40% of slice duration, IO wait is a competing or dominant cause

2. **Do not prematurely conclude "app workload"** if:
   - D-state exists but was not quantified
   - The slice has no child slices explaining the work
   - The trace lacks thread_state data entirely (say so explicitly)

3. **Frequent short D-states still count as IO wait**:
   - Many short D-states (e.g., 77 × 0-5ms) can sum to significant IO wait time
   - Do not dismiss IO because "each D-state is short" — look at cumulative D duration
   - Pattern: 50%+ D-state = IO-dominant; 30-50% = mixed; <30% = app-work dominant

4. **Required evidence before confirming "app workload"**:
   - Running state should dominate (>50% of slice time)
   - Child slices or nested evidence should show concrete CPU work (not just waiting)
   - D-state cumulative time should be <20% of slice duration

### IO vs CPU work decision tree

```
Is there a long slice (>100ms) on main thread?
│
├─ Yes → Check thread_state during slice window
│        │
│        ├─ D state > 50% of slice duration → IO wait dominant
│        │   → Next: Check for database/file/network hints
│        │   → Mitigation: IO scheduler, file cache, read-ahead
│        │
│        ├─ D state 30-50% → Mixed IO + CPU
│        │   → Next: Check what IO operations (if trace available)
│        │   → Mitigation: Both IO tuning and workload optimization
│        │
│        ├─ D state < 30% and Running > 50% → CPU work dominant
│        │   → Next: Check child slices for what work is being done
│        │   → Mitigation: Workload optimization, async, scheduling
│        │
│        └─ thread_state data missing → Cannot disambiguate
│            → Say so explicitly, mark confidence as medium
│
└─ No → Look for other causes (scheduler, GC, Binder, etc.)
```

## Mandatory GC / memory-pressure disambiguation

Before confirming "GC or memory pressure" as a root-cause bucket, all checks below must pass:

1. Process scope check
  - GC or memory events must be constrained to the target process or target app UID.
  - Do not use global keyword-only GC queries as confirmation evidence.
  - Explicitly exclude cross-process contamination such as system_server LowMemThread unless it directly blocks the target process.

2. Time-window overlap check
  - GC or memory events must overlap the bad-frame or bad-slice windows with measurable overlap ratio.
  - If only whole-trace correlation is available, classify as competing bucket, not confirmed.

3. Blocking-path check
  - Show a concrete blocking path that links the target thread delay to GC or memory reclaim effects.
  - If no blocking path is visible, keep GC/memory as unresolved.

4. STW caution
  - Do not treat all GC-named slices as stop-the-world pauses.
  - Distinguish concurrent GC activity from pause-like blocking on critical threads.

---

# Supporting guidance

## Escalation guidance

Use this skill especially when a report is about to say:

- "the app is slow"
- "the frame is long"
- "RecyclerView is expensive"

Those statements are not enough on their own.
Push one step further and ask what mechanism made the app expensive.

## Disambiguation examples

- If the thread is running most of the time and nested slices show concrete app work, that supports app-self workload.
- If the thread spends meaningful time in blocked or D-like states, ask what it is waiting on before closing the case.
- If Binder slices, lock contention slices, GC slices, or sched delay overlap the bad window, they must be checked before final confirmation.

## Mitigation mapping hints

If the bucket is confirmed, carry forward system-side mitigation directions for the final report:

- app main-thread work is too heavy
  - prefer top-app scheduling protection, reclaim-pressure reduction, cache preservation, and background interference reduction
- render or GPU path is dominant
  - prefer RenderThread / SurfaceFlinger / composition / display-pipeline tuning directions
- CPU contention or scheduler delay
  - prefer cpuset, uclamp, frequency, top-app placement, or scheduler-protection directions
- Binder or IPC blocking
  - prefer binder threadpool sizing, service-side scheduling, dependency isolation, or congestion reduction directions
- lock contention or deadlock-like waiting
  - prefer contention-point isolation, lock scope reduction, or worker split directions
- GC or memory pressure
  - prefer reclaim tuning, watermark tuning, LMKD policy, zram or swappiness adjustment, and cache-retention directions
- IO, decode, or blocking resource load
  - prefer reclaim-pressure reduction, file-cache preservation, watermark tuning, swappiness or zram policy adjustment, read-ahead, and storage-path tuning directions

Each recommendation must:
- Be mechanism-specific and evidence-linked
- Include concrete implementation details (commands, config changes)
- Prioritize system-side mitigations over APK-side rewrites

## Guardrails

- Do not claim a bucket is confirmed if the evidence only shows correlation.
- Do not confuse a long slice with the mechanism that caused it.
- Distinguish between:
  - app work consuming CPU
  - app waiting on Binder or locks
  - app being delayed by scheduler contention
- If the evidence is only at thread level, say so explicitly.
- If the evidence suggests IO, lock contention, Binder, or GC but does not identify the waited resource or blocking dependency, classify that bucket as unresolved rather than confirmed.
- A D-state or blocked-looking thread is not enough to conclude IO by itself.
- If "app workload" and "IO / blocking wait" are both plausible, explicitly mark IO as a competing bucket and recommend one more disambiguating query.

## Handoff

- After classification → `perfetto-stack-evidence-hunter` to check evidence depth
- Then → `perfetto-trace-observability-auditor` to check whether deeper drilling is possible
- Then → back to `perfetto-triage-reasoner` to decide convergence or continue
- If convergence confirmed → post-convergence workflow in triage-reasoner proceeds to report