---
name: perfetto-priority
description: Analyze thread priorities in Perfetto traces to detect anomalies, compare with a healthy reference trace, and recommend priority adjustments. Use when the problem symptom (e.g., jank, startup lag, binder delay) could be caused by incorrect or suboptimal thread priority settings.
---

# Perfetto Priority Analysis

This skill is guidance only.

## Goal

Identify whether thread priority misconfigurations contribute to the observed performance problem, and if so, propose concrete priority adjustments with justification. The analysis compares the problematic trace against a healthy reference trace (when available) and uses common Linux/Android priority heuristics.

## When to use

Use this skill when:
- The user's problem involves latency, jank, scheduling delays, or binder transaction delays.
- Initial queries (e.g., `perfetto-scheduling`, `perfetto-cpu-scheduler-stall`) show threads running on suboptimal CPUs, being preempted too often, or having unexpectedly low/high priority.
- The user explicitly asks about thread priorities or scheduler configuration.
- The user provides a reference trace (normal scenario) to compare priorities.

## Core concepts

In Android/Linux:
- **Nice value**: -20 (highest priority) to +19 (lowest). Lower nice = higher scheduling priority.
- **RT (real-time) priority**: 0-99, higher value = higher priority. Used for time-critical threads (e.g., audio, display).
- **Policy**: SCHED_NORMAL (CFS), SCHED_FIFO, SCHED_RR.
- **Common thread groups**: render threads, UI threads, binder threads, background tasks.

Typical priority patterns for performance-critical threads:
- **UI thread (main thread of foreground app)**: nice = 0 or -2 (Android’s `THREAD_PRIORITY_DEFAULT` or `URGENT_DISPLAY`).
- **RenderThread**: nice = -2 or -4 (`THREAD_PRIORITY_URGENT_DISPLAY`).
- **SurfaceFlinger main thread**: RT priority 98 or 99.
- **Binder threads**: nice = 0 (default), sometimes -2 for critical services.
- **Background work**: nice = +10 or higher.

## Inputs required

Before analysis, confirm:
1. **Problem trace path** (must already be open or loadable)
2. **Target threads or process** – the component suspected of priority issues
3. **Symptom description** – e.g., “render thread gets preempted by background I/O”
4. **Reference trace path** (optional but recommended) – a trace from the same device + workload under normal/healthy conditions
5. **Expected normal priority values** (optional, can derive from reference trace)

## Analysis steps

### Step 1: Identify relevant threads

Use MCP queries to list threads in the target process:

```sql
SELECT tid, thread_name, nice 
FROM thread 
JOIN process USING(upid) 
WHERE process.name = 'com.example.app'