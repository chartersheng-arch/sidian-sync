# AudioReach on Android

## 1. Android 音频架构中的 AudioReach

```
App (AudioTrack / AudioRecord)
    ↓
AudioFlinger
    ↓
Audio HAL (Qualcomm implementation)
    ↓
AudioReach (DSP / Hardware)
    ↓
CODEC / BT SoC
```

## 2. 高通 Audio HAL 实现

**代码路径:** `hardware/qcom/audio/`

```
audio/
├── hal/                    # Audio HAL 实现
│   ├── audio_hw.c          # 主 HAL 入口
│   ├── voice.c             # 语音通话控制
│   ├── platform.c          # 平台路由逻辑
│   └── audio_extn/         # 厂商扩展
├── hal/msm8998/            # SoC 特定实现
└── afm/                    # Audio Fabric Manager
```

## 3. Audio HAL 核心接口

### 3.1 Output Stream (Playback)

```c
// 打开输出流
int adev_open_output_stream(struct audio_hw_device* dev,
                            audio_io_handle_t handle,
                            audio_devices_t devices,
                            audio_format_t* format,
                            struct str_parms* params,
                            struct audio_stream_out** stream_out);

// 写入播放数据
ssize_t out_stream_write(struct audio_stream_out* stream,
                         const void* buffer,
                         size_t bytes);

// 设置音量
int out_stream_set_volume(struct audio_stream_out* stream,
                          float left, float right);
```

### 3.2 Input Stream (Record)

```c
// 打开输入流
int adev_open_input_stream(struct audio_hw_device* dev,
                           audio_io_handle_t handle,
                           audio_devices_t devices,
                           struct audio_config* config,
                           struct audio_stream_in** stream_in,
                           audio_input_flags_t flags,
                           struct str_parms* params,
                           audio_source_t source);

// 读取录制数据
ssize_t in_stream_read(struct audio_stream_in* stream,
                       void* buffer,
                       size_t bytes);
```

### 3.3 Voice Call

```c
int adev_set_voice_volume(struct audio_hw_device* dev, float volume);
int adev_start_voice_call(struct audio_hw_device* dev, uint32_t handle);
int adev_stop_voice_call(struct audio_hw_device* dev, uint32_t handle);
```

## 4. Audio Policy 配置

**配置文件:** `audio_policy.conf` 或 `audio_policy.xml`

**关键配置项:**
```xml
<!-- 输出设备优先级 -->
device: speaker
  sampling_rates: 48000
  channel_masks: AUDIO_CHANNEL_OUT_STEREO
  formats: AUDIO_FORMAT_PCM_16_BIT

<!-- 路由规则 -->
route: VOICE_CALL → device:earpiece
route: MUSIC → device:headphone
```

## 5. Voice over LTE (VoLTE) 集成

```
应用层: AudioTrack (Music) / VoIP App
    ↓
AudioFlinger
    ↓
VoLTE Audio HAL Path
    ↓
Modem (4G/5G Radio)
    ↓
网络: IMS Server
```

## 6. Bluetooth 音频集成

| Profile | 说明 |
|---------|------|
| **A2DP** | 高质量音乐 (SBC/AAC/aptX) |
| **HFP/HSP** | 蓝牙语音 (CVSD/mSBC) |
| **LE Audio** | 低功耗蓝牙音频 |

**AudioReach 蓝牙音频路径:**
```
AudioFlinger → BT A2DP/HFP HAL → BT SoC → 无线传输 → BT 耳机/音箱
```

## 7. 调试方法

### 7.1 日志分析
```bash
# AudioFlinger 日志
adb shell logcat | grep -i audio

# Audio HAL 日志
adb shell logcat | grep -i audio_hw
```

### 7.2 音频 Dump
- 启用 `audioflinger` trace: `adb shell setprop persist.debug.audiodumplvl 3`
- 抓取 PCM 数据分析

### 7.3 关键 Log Tag
| Tag | 内容 |
|-----|------|
| `AudioFlinger` | AudioFlinger 操作 |
| `AudioStreamOut` | Playback 数据流 |
| `AudioStreamIn` | Record 数据流 |
| `voice` | 通话控制 |
| `audio_hw` | HAL 层事件 |
