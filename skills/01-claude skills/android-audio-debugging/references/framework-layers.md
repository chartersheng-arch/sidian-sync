# Android Audio 框架分层知识库

## 整体架构

```
┌──────────────────────────────────────────────────────────────┐
│                        App Layer                              │
│  AudioTrack (playback) / AudioRecord (capture)               │
│  android.media.AudioTrack / AudioRecord                       │
├──────────────────────────────────────────────────────────────┤
│                     Audio Framework                           │
│  AudioFlinger / AudioPolicyService                           │
│  libaudiofligner / libaudiopolicy                            │
├──────────────────────────────────────────────────────────────┤
│                        Audio HAL                              │
│  IAudioFlinger / IAudioPolicyService                          │
│  Vendor-specific HAL implementation                          │
├──────────────────────────────────────────────────────────────┤
│                       Kernel Layer                            │
│  ASoC (Sound subsystem) / ALSA / DMA / Clock                 │
└──────────────────────────────────────────────────────────────┘
```

## Layer 1: App Layer

### AudioTrack (播放)

```cpp
// 关键流程
AudioTrack::createTrack()  // 创建track
AudioTrack::start()       // 开始播放
AudioTrack::write()       // 写入数据
AudioTrack::stop()        // 停止播放

// 状态机
STOPPED → STARTING → STARTED → STOPPING → STOPPED
```

### AudioRecord (录音)

```cpp
// 关键流程
AudioRecord::AudioRecord()  // 构造
AudioRecord::startRecording()  // 开始录音
AudioRecord::read()         // 读取数据
AudioRecord::stop()         // 停止录音
```

### 关键日志标签

```
AudioTrack: "AudioTrack: ol=x, requests=%d, underruns=%d"
AudioRecord: "AudioRecord: il=x, records=%d, underruns=%d"
```

---

## Layer 2: AudioFlinger

### PlaybackThread

```cpp
// 核心线程循环
PlaybackThread::threadLoop()
  ├── MixerThread::mixerLoop()
  │     └── AudioFlinger::mixerProcess()
  │           └── Track::mix()
  └── OutputMixerThread
        └── outputStream->write()
```

### RecordThread

```cpp
// 核心线程循环
RecordThread::threadLoop()
  ├── readFromHidl()
  ├── processOneRecordingState()
  └── AudioRecord::read()
```

### 关键日志标签

```
AudioFlinger: "AP_audioFlinger_PlaybackThreads pid=%d"
AudioFlinger: "createRecord() pid=%d, ID=%d"
AudioFlinger: "AudioOut_2 (or XXX): CPU=%lld, "%"=%llu"
```

### MixerThread 关键参数

```cpp
// /proc/audioMixerState
PlaybackThread:
  - mMasterVolume
  - mMasterMute
  - mActiveTracks (活跃track列表)
  - mFastMixer (FastMixerThread标志)
```

---

## Layer 3: Audio HAL

### HAL 版本演进

| 版本 | 关键变化 | 兼容性 |
|------|----------|--------|
| HAL 1.0 | 传统 struct audio_hw_device | 旧设备 |
| HAL 2.0 | HIDL接口化 | Android 8.0+ |
| HAL 3.0 | 多通道支持/模块化 | Android 10+ |
| HAL 4.0 | VLASE/Offload增强 | Android 12+ |

### 核心接口

```cpp
// audio_stream_out (播放)
struct audio_stream_out {
    uint32_t (*get_sample_rate)();
    int (*set_sample_rate)();
    size_t (*write)();
    int (*get_presentation_position)();
    // ...
};

// audio_stream_in (录音)
struct audio_stream_in {
    uint32_t (*get_sample_rate)();
    size_t (*read)();
    int (*get_input_frames_read)();
    // ...
};
```

### 关键HAL日志

```
audio_stream_out_write: stream=%p, bytes=%zu
audio_hal: out_write() returned %d bytes, latency=%ums
HAL: prepare_for_output_stream() output_flags=0x%x
```

### HAL返回码分析

| 返回值 | 含义 | 可能原因 |
|--------|------|----------|
| 0 | 成功 | 正常 |
| -ENOMEM | 内存不足 | Buffer配置过大 |
| -ENODEV | 设备未就绪 | 路径未打开/CPU占用 |
| -EINVAL | 参数无效 | Sample rate/bit depth不匹配 |

---

## Layer 4: Kernel (ASoC)

### ASoC 架构

```
Machine Driver (板级配置)
    │
    ├── CODEC Driver (编解码器)
    │     └── wm8994, cs47l35, etc.
    │
    └── Platform Driver (SOC DMA)
          └── samsung, qualcomm, etc.
```

### 关键节点

```cpp
// DAPM (Dynamic Audio Power Management)
snd_soc_dapm_stream_event()
snd_soc_dapm_sync()

// PCM Operations
snd_pcm_lib_ioctl()
snd_pcm_hw_params()
snd_pcm_prepare()
snd_pcm_writei()
```

### 关键日志标签

```
dmesg | grep -i audio
dmesg | grep -i asoc
dmesg | grep -i dma
dmesg | grep -i dai
```

### 常见Kernel日志

```
[  123.456789] asoc-simple-card sound: HiFi <-> tx-macro-grp mapping ok
[  123.456789] asoc-simple-card sound: ASoC: no backend playback stream
[  123.456789] q6asm-dai q6asm-dai: invalid param to set 32Khz
[  123.456789] q6lsm-dai q6lsm-dai: wait_for_timeout AFE port start failed
```

---

## 数据流图

### Playback 数据流

```
App write() → AudioTrack → AudioFlinger MixerThread
  → OutputStream → Audio HAL → Kernel DMA
    → I2S/TDM → Codec → Speaker
```

### Record 数据流

```
Mic → Codec → I2S/TDM → DMA → Kernel ALSA
  → Audio HAL → AudioFlinger RecordThread
    → AudioRecord read() → App
```

---

## 关键配置参数

### AudioFlinger配置

```cpp
// device/qcom/audio/audio_policy_configuration.xml
<audioPolicyConfiguration>
  <modules>
    <module name="primary" halVersion="3.0">
      <mixPorts>
        <mixPort name="primary output" flags="AUDIO_OUTPUT_FLAG_PRIMARY">
          <profile name="" format="AUDIO_FORMAT_PCM_16_BIT"
                   samplingRates="48000"
                   channelMasks="AUDIO_CHANNEL_OUT_STEREO"/>
      </mixPorts>
    </module>
  </modules>
</audioPolicyConfiguration>
```

### HAL Buffer配置

```cpp
// 典型配置
period_size = 240    // frames per period
period_count = 2     // periods per buffer
sample_rate = 48000
channel_mask = STEREO
format = PCM_16_BIT

// 计算
buffer_size = period_size * period_count = 480 frames
latency = buffer_size / sample_rate * 1000 = 10ms
```
