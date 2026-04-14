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
