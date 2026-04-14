---
name: perfetto-system-mitigation-advisor
description: Generate Android system-side mitigation guidance after the dominant performance mechanism is identified. Use when the trace analysis is converged enough to name a mechanism such as app-self workload, IO, memory pressure, Binder, scheduler delay, render path, or lock contention, and the report must provide device-side or platform-side actions instead of generic APK-side advice.
---

# Perfetto System Mitigation Advisor

This skill is guidance only.
Do not call `Task Output`, `read_task`, or any task-result retrieval mechanism using `perfetto-system-mitigation-advisor` as an ID.

## Goal

Turn a confirmed root-cause mechanism into targeted, system-side mitigation options for an Android phone-side or platform-side team. Default to mitigations that can be tried without changing application code.

## When to use

- After the dominant mechanism is identified or strongly bounded (from `perfetto-root-cause-classifier`)
- After the strongest competing mechanism is either ruled out or explicitly bounded
- Before writing the final report's recommendations section

## Input requirements

Before invoking this skill, the following must already be established:

- `dominant_mechanism`: the confirmed root-cause bucket (from root-cause-classifier)
- `supporting_evidence`: key evidence items that support this mechanism
- `competing_mechanism_status`: either ruled out or bounded with explicit reasoning

If any of these is missing, go back to `perfetto-root-cause-classifier` or `perfetto-triage-reasoner` first.

## Core rule

Always distinguish:

- **APK-side ideal fix** — what the app team should ideally change
- **System-side practical mitigation** — what the device/platform team can do without APK changes

If the root cause is dominated by APK behavior, keep APK-side changes as secondary context only.
Lead with system-side actions that can reduce impact or improve tolerance.

## Recommendation template

Every recommendation must follow this structure:

| Field | Required | Description |
|-------|----------|-------------|
| `mitigation_direction` | ✅ | What to do (one sentence) |
| `mechanism_match` | ✅ | Why it matches the confirmed mechanism |
| `evidence_link` | ✅ | Which direct evidence supports it |
| `implementation_details` | ✅ | Specific config files, parameter names, values, commands |
| `expected_benefit` | ✅ | Quantified improvement estimate (percentage or absolute) |
| `difficulty_and_risk` | ✅ | Implementation difficulty (low/medium/high) + rollback risk |
| `preconditions` | ✅ | What must be true (kernel version, hardware, etc.) |
| `side_effects` | optional | Known side effects or trade-offs |
| `category` | ✅ | system-side practical mitigation OR APK-side ideal fix |

**BAD examples** (violate this template):
- "调整 ART 锁策略" — no config path, no parameter, no expected benefit
- "优化 Binder 线程池" — no specific command, no quantified benefit
- "减少延迟" — not a mitigation, just restating the symptom

**GOOD examples**:
- "在 build.prop 中添加 `dalvik.vm.intern-table-buckets=4096`，预期 ART intern 锁竞争降低 20-30%"
- "修改 /system/etc/init/servicemanager.rc，添加 `write /dev/binderfs/binder-control/new 16`，将 Binder 线程池从默认 8 扩展到 16"

If you cannot provide this level of detail, explicitly state what additional information is needed.

## Recommendation constraints

- Do not propose generic ideas such as "optimize performance" or "reduce workload".
- Do not repeat the symptom as if it were a mitigation.
- Do not recommend system knobs unless they are plausibly connected to the confirmed mechanism.
- If no credible system-side mitigation exists, say so plainly.
- Prefer 2 to 5 high-value mitigations over a long undifferentiated list.

---

## Mechanism-to-mitigation mapping

### 1. App main-thread work is too heavy

Prefer:

- reduce reclaim pressure on top-app
- preserve file cache for hot resources
- reduce background interference from non-top-app cgroups
- protect top-app scheduling capacity
- raise top-app CPU/uclamp protection when justified
- reduce memory-pressure-induced jitter around the top-app

Good triggers:

- long nested app slices while the thread is actually running
- clear main-thread call chain such as `doFrame -> input -> RV Scroll -> OnBindView`

Avoid:

- pretending the system can fully fix a pathological UI pipeline

### 2. IO, decode, or blocking resource load

Prefer:

- reduce file-cache reclamation
- adjust reclaim aggressiveness
- lower inappropriate watermark pressure when justified
- tune `swappiness` / zram policy when reclaim is harming hot-page retention
- tune read-ahead when sequential read patterns exist
- review storage scheduler or queueing path
- protect critical storage or filesystem worker paths

Good triggers:

- blocked or D-like waits that align with file, decode, storage, or page-cache symptoms
- resource-load slices, decode slices, or storage pressure evidence

### 3. GC or memory pressure

Prefer:

- tune reclaim aggressiveness
- review LMKD thresholds or kill policy
- tune `watermark_scale_factor` or related watermark behavior when justified
- preserve hot file cache where reclaim churn is the problem
- tune zram size or swappiness policy
- reduce unnecessary compaction pressure

Good triggers:

- GC slices overlapping the bad window
- direct memory pressure symptoms
- reclaim or cache churn likely contributing to latency

### 4. CPU contention or scheduler delay

Prefer:

- top-app cpuset placement review
- uclamp tuning
- frequency response tuning
- scheduler protection for top-app
- reduce cross-cluster migration or interference when justified

Good triggers:

- runnable delay
- long time in runnable state without CPU
- competing heavy threads or cores under pressure

### 5. Binder or IPC blocking

Prefer:

- binder threadpool sizing review
- service-side worker isolation
- reduce synchronous dependency chains
- prioritize or isolate critical services
- reduce service congestion in the hot path

Good triggers:

- binder slices or transactions overlapping the bad window
- service wait chains clearly on the critical path

### 6. Lock contention or deadlock-like waiting

Prefer:

- isolate the contended resource path
- reduce shared critical-section exposure
- move non-critical work off the blocked path
- reduce work under contested locks
- review worker split or queue design on the system side

Good triggers:

- monitor contention, lock slices, or a clear blocking dependency chain

### 7. Render or GPU path is dominant

Prefer:

- RenderThread / SurfaceFlinger priority review
- composition-path tuning
- buffer queue depth review
- display pipeline or HWUI pressure mitigation
- reduce producer-consumer mismatch in the render path

Good triggers:

- RenderThread or SurfaceFlinger dominates the critical window
- app thread is not the main bottleneck

---

## Prioritization rule

When multiple mitigations are plausible, rank them by:

1. strongest evidence alignment
2. feasibility for a phone-side team
3. lowest rollback risk
4. highest expected impact on the critical path

## Final reporting rule

When this skill is used together with `perfetto-report-writer`:

- recommendations should be grouped by priority
- each recommendation should clearly state whether it is:
  - system-side practical mitigation
  - APK-side ideal fix
- system-side items must come first

## Handoff

- After generating mitigations → pass the prioritized recommendation list to `perfetto-report-writer` for the 优化建议 section
- If historical issues were searched → `perfetto-history-issue-matcher` results may supplement but never replace mechanism-specific mitigations
- If no credible system-side mitigation exists → say so plainly in the report rather than inventing weak suggestions
