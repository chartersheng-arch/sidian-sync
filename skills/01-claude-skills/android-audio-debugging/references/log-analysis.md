# Audio 日志分析技巧

## 1. 关键日志位置

### 1.1 系统日志

```bash
# 主日志
adb logcat -b main

# 系统日志 (AudioFlinger级别)
adb logcat -b system | grep -i audio

# 事件日志 (AudioFocus等)
adb logcat -b events | grep -i audio
```

### 1.2 AudioFlinger专用日志

```bash
# 查看PlaybackThreads状态
adb shell "dumpsys audioflinger"

# 查看AudioPolicy状态
adb shell "dumpsys audio_policy"
```

### 1.3 Kernel日志

```bash
# Audio相关kernel日志
adb shell "dmesg | grep -i audio"

# 持续监控
adb shell "adb shell logcat -d | grep -i audio > /data/local/tmp/audio_log.txt"
```

## 2. 日志过滤技巧

### 2.1 按Tag过滤

```
AudioTrack
AudioRecord
AudioFlinger
AudioPolicyService
Audio HAL
ALSAModule
AudioHardware
audio_a2dp_hw
```

### 2.2 按PID过滤

```bash
# 找到AudioFlinger的PID
adb shell "ps -A | grep audioflinger"

# 按PID过滤
adb logcat --pid=<PID>
```

### 2.3 时间范围过滤

```bash
# 查看特定时间段的日志
adb logcat -T "01-15 10:30:00.000" | grep -i audio
```

## 3. 关键日志解析

### 3.1 AudioTrack生命周期

```
// 创建
AudioTrack(0): Creating AudioTrack with:
// 配置参数
AudioTrack: sampleRate=48000, channelMask=0x3, format=0x1
AudioTrack: frameCount=%d, bufferSizeInBytes=%d

// 启动
AudioTrack: start()  // output flags: 0x%x
AudioTrack: ol=%d, requests=%d, underruns=%d

// 写入
AudioTrack: bytes written=%d
AudioTrack: buffer time: %d us

// 停止
AudioTrack: stop()
```

### 3.2 AudioFlinger日志

```
// Track创建
AudioFlinger: createTrack() pid=%d, ID=%d
AudioFlinger: Track(0x%x)::start() output=%d

// Mixer状态
AudioFlinger: MixerThread: %d tracks, masterVolume=%.2f
AudioFlinger: MixerThread: period elapsed, frames=%d

// Buffer状态
AudioFlinger: out_write: hw=0x%x, last=0x%x
AudioFlinger: track(%d): underruns=%d, buffers=%d
```

### 3.3 HAL层日志

```
// 播放
audio_stream_out_write: stream=%p, bytes=%zu
HAL: out_write() returned %d, presentation=%llu

// 参数设置
audio_hw_device_set_parameters: key=%s, value=%s
out_set_parameters: routing=0x%x, format=%d

// 录音
audio_stream_in_read: stream=%p, bytes=%zu
HAL: in_read() returned %d, frames_read=%llu
```

### 3.4 Kernel层日志

```
// ASoC
ASoC: pcmCVDDrv pcmCVDDrv-audio: pcm_ops->prepare()
ASoC: codec: sample rate changed to %d
ASoC: DAPM: stream started

// DMA
DMA: buffer ready, size=%d, period=%d
DMA: transfer completed, irq_count=%d
DMA: underrun detected, frames dropped=%d

// Clock
clk: %s enabled
clk: %s disabled
```

## 4. 异常日志识别

### 4.1 Underrun/Overrun

```
[AF] OutputMixer: ******************* underrun *******************
[AF] PlaybackThread: track 0x1234: backend=%d, underruns=%d
[HAL] out_write: underrun occurred
[Kernel] DMA: underrun at period %d
```

### 4.2 错误码

```
[HAL] out_write: returned error -%d (Connection refused)
[HAL] in_read: returned -ENODEV (No such device)
[AF] createTrack: init failed: invalid parameter
```

### 4.3 状态异常

```
[AudioTrack] Session(%d): stale global config, expected %d, got %d
[AudioFlinger] Thread(%s): standby: %d
[AudioPolicy] setOutputDevice: incompatible device flags
```

## 5. 性能日志分析

### 5.1 延迟计算

```
// HAL层报告的延迟
[HAL] out_get_latency: latency=%u ms

// AudioFlinger计算的延迟
[AF] output latency=%u ms (min=%u, max=%u)

// 实际测量
PlaybackDuration: %lld ms (frames=%llu, sample_rate=%u)
```

### 5.2 Buffer监控

```
// /proc/audiooutput
Output 0 (primary):
  Sampling rate: 48000
  Format: PCM 16-bit
  Channel mask: stereo
  Buffer size: 1920 frames
  Period count: 2
  Latency: 20 ms
  Underruns: 0
```

### 5.3 CPU占用

```
// Mixer CPU占用
AudioFlinger: CPU=%lld, "%"=%llu (wall=%lld)

// 查看调度
dumpsys audioflinger | grep "Scheduling"
```

## 6. 场景化日志分析

### 6.1 通话建立

```
// 1. 创建通话路由
[AudioPolicy] setPhoneState(0)
[AudioPolicy] setOutputDevice(0x2)
[AudioPolicy] setInputDevice(0x8004)

// 2. 启动通话
[AudioFlinger] openOutput() output=0
[HAL] out_set_parameters: incall_mode=1
[HAL] in_set_parameters: echo_ref=1

// 3. 通话中
[AudioFlinger] VoIP track started
[HAL] VoIP stream active
```

### 6.2 蓝牙连接

```
// A2DP连接
[BluetoothAudio] A2DP connection state: connected
[AudioPolicy] setOutputDevice(0x100) // BT device

// AAC编码
[BluetoothAudio] Codec: AAC, bitrate=%d
[BluetoothAudio] Buffer: %d/%d frames

// SCO连接 (通话)
[BluetoothAudio] SCO connection established
[AudioFlinger] SCO path enabled
```

## 7. 常用调试命令

```bash
# 完整Audio系统状态
adb shell dumpsys audio

# AudioFlinger详细信息
adb shell dumpsys audioflinger

# 查看特定输出
adb shell dumpsys audioflinger | grep -A20 "PlaybackThread"

# 查看特定输入
adb shell dumpsys audioflinger | grep -A20 "RecordThread"

# AudioPolicy配置
adb shell dumpsys audio_policy

# 音频参数
adb shell getprop | grep audio
adb shell getprop | grep persist.audio

# Kernel日志
adb shell dmesg | grep -E "audio|ASoC|DMA"

# 音频设备节点
adb shell ls -la /dev/snd/

# ALSA配置
adb shell cat /system/etc/audio_policy.conf
```

## 8. 日志时间戳同步

### 8.1 多源日志对齐

```bash
# 同时抓取logcat和dmesg
adb shell "logcat -d > /data/local/tmp/logcat.txt"
adb shell "dmesg > /data/local/tmp/dmesg.txt"
adb pull /data/local/tmp/

# 在分析时按时间戳对齐
# logcat格式: 01-15 10:30:00.123
# dmesg格式: [  123.456789]
```

### 8.2 perfetto trace

```bash
# 使用perfetto抓取audio相关事件
adb shell "perfetto -c - --txt -o /data/misc/perfetto-traces/audio_trace.perfetto-trace <<EOF
buffers: {
    size_kb: 896
    fill_policy: DISCARD
}
duration_ms: 10000
data_sources: {
    config {
        name: "linux.ftrace"
        ftrace_config {
            ftrace_events: "audio/*"
            ftrace_events: "snd/*"
            ftrace_events: "dma/*"
        }
    }
}
EOF"
```

## 9. 典型问题日志特征

| 问题 | 关键日志特征 |
|------|--------------|
| 无声 | "underrun", "no tracks active", "device not found" |
| 杂音 | "clip", "overflow", "gain jump", "pop" |
| 延迟 | "latency high", "buffer full", "CPU stuck" |
| 断续 | "underrun", "gap", "xrun", "dropped" |
| 爆音 | "gain ramp", "pop", "clamp", "mute state change" |

---

## 10. 代码与日志解析准则（重要）

### ⚠️ 铁律：区分格式化字符串与实际输出

**常见误区：混淆C++ printf 格式占位符与实际日志输出值**

#### 10.1 典型错误案例

**代码：**
```cpp
PAL_VERBOSE(LOG_TAG, "Inside PAL_AUDIO_OUTPUT device count - %zu", mDevices.size());
```

**日志实际输出：**
```
Inside PAL_AUDIO_OUTPUT device count - 1
```

**❌ 错误分析：**
```
AI误判：mDevices.size() = -1 (严重错误！size_t被解析为负数)
```

**✅ 正确理解：**
```
日志中的 "-1" 不是数学减法，而是格式化字符串中 %zu 输出的正数 "1"
mDevices.size() 的实际值 = 1（表示有1个设备）
```

#### 10.2 常见格式化占位符解析表

| 占位符 | 类型 | 日志示例 | 实际含义 |
|--------|------|----------|----------|
| `%zu` | size_t (无符号) | `count - 1` | count = 1 (正整数) |
| `%d` | int (有符号) | `value - 5` | value = 5 或 value = -5 |
| `%u` | unsigned int | `bytes - 1024` | bytes = 1024 (正数) |
| `%x` | hex (无符号) | `flags - 0x2` | flags = 0x2 |
| `%llu` | unsigned long long | `frames - 1000` | frames = 1000 |
| `%lld` | long long | `timestamp - 5000` | timestamp = 5000 或 -5000 |
| `%s` | string | `device - speaker` | device = "speaker" |

#### 10.3 关键判断原则

**1. 看上下文判断正负**
```
// 代码
PAL_VERBOSE(LOG_TAG, "device count - %zu", mDevices.size());

// 日志
device count - 1

// 分析：size_t 永远 >= 0，所以 "1" 是正数，不是 "-1"
```

**2. 数值来源决定类型**
```
// mDevices.size() 返回 size_t (无符号)，绝不可能为负
// 所以日志中的 "1" 就是 1，不是 -1
```

**3. 减号在格式化字符串中的位置**
```
// 错误：认为 "-1" 是负数
"count - %zu"  →  输出 "count - 1"  (1是正数)

// 如果要输出负数，代码会这样写：
"count = %zd"  →  输出 "count = -1"  (只有%zd才可能输出负数)
```

#### 10.4 快速判断方法

```
当看到日志中有 "- 数字" 时，按以下步骤判断：

1. 找到对应的代码行
2. 确认 %与d/z/u/l 等修饰符的组合
3. 判断类型：
   - %zu → 绝对正值，不可能为负
   - %zd → 可能为负（size_t的signed版本）
   - %d  → 需要看上下文才能确定正负
4. 确认后，再判断该值是否异常
```

#### 10.5 避免混淆的验证方法

```bash
# 搜索源码确认变量类型
grep -rn "mDevices.size()" vendor/xxx/audio/

# 搜索类似日志的格式化字符串
grep -rn "device count - %zu" vendor/xxx/audio/

# 查看该变量在其他日志中的输出
grep -rn "mDevices.size()" vendor/xxx/audio/ | grep -E "LOG|PRINT|VERBOSE"
```

#### 10.6 分析自检清单

```
[ ] 日志中的 "-" 是格式化字符串的分隔符，还是数学减法的结果？
[ ] 占位符类型（%zu/%d/%zd）对应的变量是否可能为负？
[ ] size_t 类型的变量（如 .size()）是否被误判为负数？
[ ] hex值（如 0xFFFFFFFF）是否被误认为有符号整数？
```
