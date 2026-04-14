# 0121-daily-cam-screen 音频Pop音问题分析报告

## 问题概述

**设备**: REDMI 17 5G
**问题现象**: 录像时开启录屏，对应时间点录像出现pop音
**问题时间点**: 19:09:10（开始录屏时刻）
**trace文件**: trace-somalia-BP2A.250605.031.A3-2026-01-21-19-10-51.perfetto-trace

---

## 关键事件时间线

| 时间 | 事件 | 线程/Session | 说明 |
|------|------|--------------|------|
| 19:09:00.824 | PowerHAL enter camera_video_1080p scene | system_server | 开始录像场景 |
| 19:09:02.667 | AudioRecord start session 47801 | com.android.camera | 录像录音启动 |
| 19:09:10.624 | AudioRecord start session 47817 | com.miui.screenrecorder | 录屏主录音启动 |
| 19:09:10.751 | AudioRecord start session 47809 | com.miui.screenrecorder | 录屏副录音启动 |
| 19:09:10.912 | **Critical HAL Block** | AudioIn_4E (tid=25965) | 录像录音HAL阻塞 |
| 19:09:16.160 | AudioRecord stop session 47817 | com.miui.screenrecorder | 停止录屏 |
| 19:09:17.190 | AudioRecord stop session 47801 | com.android.camera | 停止录像 |

---

## 问题根因分析

### 1. HAL资源竞争 - 直接原因

在19:09:10.624时刻，录屏应用同时创建了**3个AudioRecord输入流**：

| 输入ID | 采样率 | 通道数 | 类型 | TID |
|--------|--------|--------|------|-----|
| AudioIn_56 | 44100 | 2ch | RemoteSubmix | 26059 |
| AudioIn_5E | 44100 | 1ch | MIC | 26064 |
| AudioIn_66 | 44100 | 1ch | Voice_communication | 26067 |

而此时**录像录音线程 AudioIn_4E (tid=25965)** 正在运行，其正常周期为40.27ms。

### 2. 关键错误日志

**第一次阻塞 (19:09:10.906-19:09:10.912)**:
```
PerfSense: [AudioIn_4E] NT Xruns counter increased to 1 (cycle: 162.16ms), expected=40.27ms
PerfSense: [AudioIn_4E] Critical Jitter Error: Cycle=162.16ms, exceeds 3.00x!
PerfSense: [AudioIn_4E] Critical HAL Block: HAL write blocked for 161.71ms, exceeds 3.0x period (40.27ms)
```

**第二次阻塞 (19:09:16.390-19:09:16.391)**:
```
PerfSense: [AudioIn_4E] NT Xruns counter increased to 2 (cycle: 186.22ms), expected=40.27ms
PerfSense: [AudioIn_4E] Critical Jitter Error: Cycle=186.22ms, exceeds 3.00x!
PerfSense: [AudioIn_4E] Critical HAL Block: HAL write blocked for 186.15ms, exceeds 3.0x period (40.27ms)
```

### 3. 阻塞机理

```
[AudioIn_4E 录像录音]
       ↓
    占用Audio HAL
       ↓
[AudioIn_56/5E/66 录屏录音启动]
       ↓
   竞争同一HAL资源
       ↓
   HAL write() 阻塞等待
       ↓
   阻塞时间 161.71ms / 186.15ms
   (正常周期仅为 40.27ms)
       ↓
   数据中断 → Pop音产生
```

---

## 问题定位

### 受影响线程

| 线程名 | TID | 所属应用 | 问题 |
|--------|-----|----------|------|
| AudioIn_4E | 25965 | com.android.camera (录像) | HAL write阻塞161.71ms |
| AudioIn_56 | 26059 | com.miui.screenrecorder | RemoteSubmix录音 |
| AudioIn_5E | 26064 | com.miui.screenrecorder | MIC录音 |
| AudioIn_66 | 26067 | com.miui.screenrecorder | Voice_communication录音 |

### 涉及端口

| 端口ID | 来源 | 采样率 | 通道 |
|--------|------|--------|------|
| 0x4E (78) | 录像MIC | 44100 | 1ch |
| 0x56 (86) | 录屏RemoteSubmix | 44100 | 2ch |
| 0x5E (94) | 录屏MIC | 44100 | 1ch |
| 0x66 (102) | 录屏Voice comm | 44100 | 1ch |

---

## 结论

**问题类型**: HAL资源竞争导致的音频underrun

**根本原因**:
1. 录像和录屏同时使用音频输入，共享同一个Audio HAL硬件资源
2. 录屏启动时新增3个AudioRecord，与原有录像录音竞争HAL
3. HAL层面无法及时处理多个并发输入请求，导致录像录音线程的HAL write操作阻塞
4. 阻塞时间超过正常周期的4倍（161.71ms vs 40.27ms），导致数据中断产生pop音

**建议**:
1. 检查Audio HAL是否支持多路音频输入的并发处理
2. 评估录像录音与录屏录音的Audio Path是否应该共享HAL
3. 考虑在录屏启动时对录像录音进行优先级保护或buffer调整

---

## 附件

- trace文件: `trace-somalia-BP2A.250605.031.A3-2026-01-21-19-10-51.perfetto-trace`
- 日志文件: `0-android.log` (line 69695-69697, 75729-75731)
- 音频参数: `audio_param/audio_structure`, `audio_param/dsp_vbc`
