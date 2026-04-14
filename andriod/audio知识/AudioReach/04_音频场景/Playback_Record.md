# Audio Playback & Record in AudioReach

## 1. Playback 路径

```
App (AudioTrack)
    ↓  PCM Data
AudioFlinger
    ↓
Audio HAL
    ↓
AFM (Audio Fabric Manager)
    ↓
Playback Graph (DSP)
    ↓
DAC / I2S Output
    ↓
Speaker / Headphone
```

### 1.1 Playback Graph 模块

| Module | 功能 |
|--------|------|
| Resampler | 重采样 (如 44.1k → 48k) |
| EQ | 均衡器 |
| Volume | 音量控制 |
| Mixer | 多路混音 |
| SRC | Sample Rate Converter |

## 2. Record 路径

```
Mic / External Input
    ↓
ADC / I2S Input
    ↓
AFM (Audio Fabric Manager)
    ↓
Record Graph (DSP)
    ↓
Audio HAL
    ↓
AudioFlinger
    ↓
App (AudioRecord)
```

### 2.1 Record Graph 模块

| Module | 功能 |
|--------|------|
| AEC | 声学回声消除 (免提场景) |
| NS | 噪声抑制 |
| AGC | 自动增益控制 |
| Resampler | 重采样 |
| Encoder | 编码 (AAC/AMR/PCM) |

## 3. Full-Duplex 场景

**例:** 免提通话 / 实时音频监控

```
上行: Mic → ADC → AFM → Record Graph → App
下行: App → Playback Graph → AFM → DAC → Speaker
          ↑
          └── 同时进行，不互相干扰
```

## 4. 关键配置参数

| 参数 | Playback | Record |
|------|----------|--------|
| Sample Rate | 44.1k / 48k / 96k | 8k / 16k / 48k |
| Bit Depth | 16 / 24 / 32-bit | 16 / 24-bit |
| Channels | Mono / Stereo | Mono / Stereo |
| Buffer Size | 20ms (Normal) / 5ms (LL) | 20ms / 5ms |

## 5. 音频格式

| 格式 | Playback | Record |
|------|----------|--------|
| PCM | 支持 | 支持 |
| AAC | 支持 | 支持 |
| MP3 | 支持 | — |
| AMR | — | 支持 |
| SBC (BT) | A2DP Sink | A2DP Source |

## 6. 调试检查项

- [ ] Audio HAL `out_stream_write()` 是否被调用
- [ ] AFM 路由是否指向正确的 CODEC
- [ ] DAC 是否使能
- [ ] Buffer 是否填满 (排除 underrun)
- [ ] Clock 配置是否匹配采样率
