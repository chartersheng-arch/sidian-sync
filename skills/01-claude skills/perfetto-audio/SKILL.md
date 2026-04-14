---
name: perfetto-audio
description: Investigate audio glitches, underruns, and sound stuttering in Perfetto traces. Use when the user reports audio problems, sound interruptions, or suspects audio thread scheduling delays, HAL blocking, or third-party audio effect latency.
---

# Perfetto Audio

This skill is guidance only.
Do not call `Task Output`, `read_task`, or any task-result retrieval mechanism using `perfetto-audio` as an ID.

## Goal

Identify the root cause of audio glitches (underrun/overrun, audible pops, sound stuttering) by analyzing audio thread behavior, scheduling delays, CPU contention, HAL blocking, and third-party audio effect processing. When possible, use user-provided logcat timestamps to pinpoint exact glitch moments in the trace.

## When to use

- User reports "音频卡顿", "声音断续", "audio glitch", "pop/click", "underrun", "声音卡"
- Trace shows audio-related threads or underrun events
- Jank or binder analysis hints at audio path delays

## Primary questions

1. When does the audio glitch occur? Which audio thread (`AudioOut_D`, `AudioIn`, `AudioFlinger`, `EffectWorker`) is involved?
2. What is the immediate cause of the glitch?
   - Audio thread scheduler delay (high Runnable time)
   - Audio thread preempted by other heavy threads (CPU contention)
   - App not writing data in time (mixer thread waits for data)
   - HAL write() blocking (driver or DSP issue)
   - Audio effect processing taking too long
3. Is a third-party audio effect process present? If internal behavior is invisible in the trace, what information should be requested from the user?

## Time window localization: ask user first

**Before querying the trace**, ask the user for precise timing information if available:

> To narrow down the analysis, please provide:
> 1. The **approximate time** (in seconds from start, or wall-clock time) when audio glitches occurred.
> 2. If you have **logcat logs** containing audio-related warnings/errors (e.g., `underrun`, `AudioTrack`, `AudioFlinger`), please share the timestamps.
> 3. Any **user action** that triggered the glitch (e.g., "after switching to song B", "during incoming call").

**If the user provides logcat timestamps**, convert them to trace time by subtracting trace start time (obtain via `run_trace_metric("trace_bounds")`). Then use that narrowed window for all subsequent queries.

**If the user does not provide timing**, proceed with full-trace search for underrun events or rely on the worst glitch window identified from audio thread anomalies.

## Evidence checklist

- [ ] User-provided glitch timestamps (if any) converted to trace time range
- [ ] Audio thread names and utids (`AudioOut_D`, `AudioFlinger`, `AudioIn`, `EffectWorker`, etc.)
- [ ] Underrun/overrun events (slices named `underrun`, `audio track underrun`, or periodic wakeup pattern broken)
- [ ] `thread_state` distribution for audio thread during glitch window (Running / R / D / S)
- [ ] Competing threads/processes consuming CPU in the same window
- [ ] Wakeup interval analysis to detect broken periodicity (normal: 10-20ms)
- [ ] Third-party audio effect processes (e.g., `dolby`, `misound`, `dirac`, `audio_effect`, `vivo.effect`, `miui.audioeffect`) and their observability

## Reasoning pattern

1. **Ask for timestamps** (if not already provided) — prioritize user-provided logcat time points.
2. **Convert wall-clock to trace time** — use `trace_bounds` to map logcat timestamps to trace nanoseconds.
3. **Identify** audio threads using `list_processes_threads` or SQL pattern matching.
4. **Locate** glitch windows:
   - If user provided timestamps → use that exact window (±50ms)
   - Else → find underrun slices or abnormal gaps in audio thread activity
5. **Quantify** audio thread `thread_state` inside each glitch window.
6. **Test** which delay category dominates (see decision tree).
7. **If third-party effect process exists but lacks internal slices** → ask user for implementation details.

## Converting logcat timestamps to trace time

```sql
-- First, get trace start time in nanoseconds since boot
SELECT ts FROM trace_bounds LIMIT 1;  -- returns start_ts_ns

-- Then convert user-provided wall-clock time:
-- trace_time_ns = (logcat_timestamp_ms - trace_start_wallclock_ms) * 1e6 + trace_start_ts_ns
-- Note: trace start wallclock may not be available. Alternative: use relative time if user says "5 seconds after start".
