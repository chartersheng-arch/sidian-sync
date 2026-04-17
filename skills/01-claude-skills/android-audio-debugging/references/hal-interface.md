# Audio HAL 接口与状态机

## HAL接口概览

### audio_hw_device

```cpp
struct audio_hw_device {
    struct hw_device_t common;

    // 通用接口
    int (*init_check)();
    int (*set_voice_volume)(float volume);
    int (*set_master_volume)(float volume);

    // 输出相关
    int (*create_output_stream)();
    int (*dump)();

    // 输入相关
    int (*set_mode)();
    int (*set_parameters)();
    int (*get_parameters)();
};
```

### audio_stream_out

```cpp
struct audio_stream_out {
    // 基本信息
    uint32_t (*get_sample_rate)(const struct audio_stream_out *stream);
    int (*set_sample_rate)(struct audio_stream_out *stream, uint32_t rate);
    audio_channel_mask_t (*get_channels)(const struct audio_stream_out *stream);
    audio_format_t (*get_format)(const struct audio_stream_out *stream);

    // 数据传输
    int (*write)(struct audio_stream_out *stream, const void *buffer, size_t bytes);

    // 位置/时间
    int (*get_render_position)(const struct audio_stream_out *stream, uint32_t *frames);
    int (*get_presentation_position)(const struct audio_stream_out *stream,
                                      uint64_t *frames, struct timespec *timestamp);
};

// 标志位
AUDIO_OUTPUT_FLAG_NONE = 0
AUDIO_OUTPUT_FLAG_PRIMARY = 0x1
AUDIO_OUTPUT_FLAG_FAST = 0x2     // 低延迟路径
AUDIO_OUTPUT_FLAG_DEEP_BUFFER = 0x4
AUDIO_OUTPUT_FLAG_COMPRESS_OFFLOAD = 0x8
AUDIO_OUTPUT_FLAG_NON_BLOCKING = 0x10
```

### audio_stream_in

```cpp
struct audio_stream_in {
    uint32_t (*get_sample_rate)(const struct audio_stream_in *stream);
    audio_channel_mask_t (*get_channels)(const struct audio_stream_in *stream);
    audio_format_t (*get_format)(const struct audio_stream_in *stream);

    size_t (*read)(struct audio_stream_in *stream, void *buffer, size_t bytes);

    // 位置追踪
    int (*get_input_frames_read)(struct audio_stream_in *stream);
};
```

## HAL状态机

### Output Stream状态机

```
                    ┌─────────────────────────────────────┐
                    │                                     │
                    ▼                                     │
    CLOSED ──────► OPENING ──────► IDLE                   │
        │              │              │                    │
        │              │              │ (write called)      │
        │              │              ▼                    │
        │              │          ACTIVE ─────────────────┤
        │              │              │                    │
        │              │              │ (stop/flush)       │
        │              │              ▼                    │
        │              └────────► FLUSHING ───────────────┘
        │                               │
        │                               │ (flush complete)
        └───────────────────────────────┘
                            (close)
```

### 状态转换关键日志

```
[HAL] open_output_stream: output_flags=0x%x, sampling_rate=%u
[HAL] out_set_parameters: routing=0x%x, format=%d
[HAL] out_write: bytes=%zu, frames=%zu
[HAL] out_get_presentation_position: frames=%llu, time=%lld
```

## 关键HAL API分析

### write() 流程

```cpp
// AudioFlinger调用链
PlaybackThread::threadLoop()
  → Track::write()
    → OutputStream::write()
      → audio_stream_out->write()

// 返回值分析
ssize_t write_result = stream->write(stream, buffer, bytes);

// 成功: 返回写入的bytes数
// 失败: 返回负数 errno
```

### get_presentation_position()

```cpp
// 用于AudioTrack获取播放位置
int (*get_presentation_position)(
    struct audio_stream_out *stream,
    uint64_t *frames,           // 已提交的帧数
    struct timespec *timestamp    // 时间戳
);

// 用途:
// 1. AudioTrack.getPlaybackHeadPosition()
// 2. A/V sync
// 3. 延迟计算
```

## 常见HAL配置问题

### Sample Rate不匹配

```cpp
// App请求
AudioTrack::setSampleRate(48000)

// HAL支持
stream->get_sample_rate() = 44100

// 结果: -EINVAL 或 自动重采样
```

### Channel Mask不匹配

```cpp
// App请求
AudioTrack::setChannelMask(AUDIO_CHANNEL_OUT_5_1)

// HAL支持
stream->get_channels() = AUDIO_CHANNEL_OUT_STEREO

// 结果: 下混或失败
```

### Buffer Size配置

```cpp
// 关键参数
period_size: 一次DMA中断的帧数
period_count: buffer中的period数
buffer_size = period_size * period_count

// 延迟计算
latency_ms = (buffer_size * 1000) / sample_rate

// 典型值:
- 低延迟: 5ms (240 frames @ 48kHz)
- 普通: 20ms (960 frames @ 48kHz)
- Deep buffer: 100ms+
```

## HAL调试技巧

### 查看当前HAL配置

```bash
# 通过AudioParameter
adb shell "dumpsys audio"

# 查看AudioFlinger状态
adb shell "dumpsys audioflinger"

# 查看HAL层日志
adb shell "logcat | grep -i audio_hal"
adb shell "logcat | grep -i audio_stream"
```

### 常见错误码

| errno | HAL错误 | 根因 |
|-------|---------|------|
| ENOMEM | -ENOMEM | buffer配置过大 |
| ENODEV | -ENODEV | 设备路径未打开 |
| EINVAL | -EINVAL | 参数不支持 |
| EBUSY | -EBUSY | 资源被占用 |
| ETIMEDOUT | -ETIMEDOUT | 超时（DSP/HAL响应慢）|

## Vendor HAL扩展

### MTK HAL特征

```cpp
// MTK特定的参数
AUDIO_PARAMETER_KEY_TDM_TX_ENABLE
AUDIO_PARAMETER_KEY_HDMI_OUTPUT
MTK_AUDIO_TUNING_TOOL_ID
```

### Qualcomm HAL特征

```cpp
// Snapdragon特有的优化路径
AUDIO_OUTPUT_FLAG_FAST | AUDIO_OUTPUT_FLAG_COMPRESS_OFFLOAD
// FastMixer路径
```

### Samsung HAL特征

```cpp
// Samsung的SoundAlive优化
AUDIO_PARAMETER_KEY_SND_FLAVOR
AUDIO_PARAMETER_KEY_ANC
```

---

## HAL与Framework交互

### 设置参数流程

```
App.setParameters("key=value")
  → AudioSystem.setParameters()
    → AudioFlinger::setParameters()
      → AudioPolicyService::setParameters()
        → audio_hw_device::set_parameters()
```

### 获取参数流程

```
App.getParameters("key")
  → AudioSystem.getParameters()
    → AudioFlinger::getParameters()
      → audio_hw_device::get_parameters()
```

## 故障排查清单

- [ ] HAL是否正确打开（检查日志中的open_output_stream）
- [ ] Sample rate是否匹配
- [ ] Channel mask是否支持
- [ ] Buffer配置是否合理
- [ ] 设备路由是否正确
- [ ] 电源状态（DAPM）是否正常
