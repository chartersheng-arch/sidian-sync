---
name: perfetto-history-issue-matcher
description: Optionally search a user-provided history issue library after the dominant root cause is identified and before final report writing. Use to find similar prior cases, compare mechanisms, and append reference links into the final report.
---

# Perfetto History Issue Matcher

This skill is guidance only.
Do not call `Task Output`, `read_task`, or any task-result retrieval mechanism using `perfetto-history-issue-matcher` as an ID.

## Goal

Search a user-provided historical issue library for similar prior cases, then carry the most relevant references into the final report as supporting context. Historical references must never replace direct trace evidence.

## When to use

This skill is **optional**. Only invoke when ALL of these are true:

- The dominant root-cause mechanism is already identified or strongly bounded
- The key evidence and call chain are already collected
- The user is willing to search a history issue library
- The user provides a local path to search

If the user does not want historical matching or does not provide a path, skip this skill entirely.

## Interaction protocol

1. **Before searching**: Ask one short question (only if needed) — whether the user wants history search and the local path. Do not ask if the user has already provided the path.
2. **After searching**: Pause and ask two follow-ups:
   - Whether the user has any additional questions
   - If not, whether the final report should be generated now

## Search scope

Search only under the user-provided path.

Prefer text-like files:
- `.md`, `.txt`, `.rst`, `.log`

Ignore obviously irrelevant binary files unless the user explicitly asks otherwise.

Use `grep_search` or `semantic_search` for keyword retrieval within the provided path.

## Similarity signals

Rank similar cases by these signals, from highest to lowest priority:

| Priority | Signal | Examples |
|----------|--------|----------|
| 1 (highest) | Same dominant mechanism | app-self workload, render path, CPU contention, binder/IPC, lock contention, GC/memory, IO/decode |
| 2 | Same symptom class | jank, startup latency, binder stall, scheduler stall |
| 3 | Same or similar call-chain tokens | `Choreographer#doFrame`, `RV OnBindView`, `StaticLayout`, `binder`, `sched`, `lock contention` |
| 4 | Same process/thread/module/component keywords | Package names, thread names, view class names |
| 5 (lowest) | Similar optimization direction | precompute layout, reduce main-thread bind, improve reuse, reduce binder wait |

## Search workflow

1. **Summarize** the current case in 3-6 retrieval terms (symptom, dominant mechanism, key call chain tokens, bottleneck keywords)
2. **Search** the provided path for those terms using grep or semantic search
3. **Read** only the most promising few files (do not read all matches)
4. **Select** up to 3 historical references: most similar, informative, and non-redundant
5. **Summarize** each selected reference:
   - Why it is similar
   - Where it differs
   - Whether it increases confidence in the current conclusion

## Output format

Before switching to `perfetto-report-writer`, summarize matches as:

- `history_path_searched`: the user-provided path
- `retrieval_terms`: the 3-6 terms used for search
- `matched_references`: up to 3 selected references with file paths
- `similarity_reason`: why each match is similar
- `key_differences`: how each differs from the current case
- `confidence_impact`: whether the references strengthen, weaken, or do not change confidence

## Guardrails

- Do not search the history library before the main trace evidence has converged.
- Do not present historical cases as direct evidence for the current trace.
- Do not add weakly related references just to fill the report.
- If no strong match is found, say so plainly and skip the historical-reference section in the report — do not force weak matches.

## Handoff

- After summarizing matches → ask user for additional questions
- If user has no questions and confirms → load `perfetto-report-writer`
- Before loading report-writer → also load `perfetto-system-mitigation-advisor` if not yet loaded
- The matched references go into the report's optional `历史相似案例参考` section, clearly separated from direct trace evidence
