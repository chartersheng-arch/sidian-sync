# Android Audio 常见故障模式库

## 1. 无声问题 (No Audio Output)

### 1.1 分类排查表

| 层级 | 症状 | 关键日志 | 常见原因 |
|------|------|----------|----------|
| App | AudioTrack创建失败 | "AudioTrack: init failed" | 采样率不支持 |
| App | start()后无数据 | "AudioTrack: buffer is empty" | App未write |
| Framework | track未注册 | "no tracks active in thread" | Mixer未激活 |
| HAL | write返回成功但无声 | "out_write completed" | 路由未设置 |
| Kernel | DMA未启动 | "DMA transfer not started" | Clock未使能 |

### 1.2 典型案例

**案例1: 路由未切换到正确输出**
```
[AudioFlinger] Thread::getBufferTimeMs: no tracks active
[AudioPolicy] setOutputDevice(0x2, 0)
[HAL] out_set_parameters: routing=0x2 (speaker)
```
根因: 路由已设置，但Codec未切换到SPK路径

**案例2: HAL write但数据未送出**
```
[HAL] out_write: bytes=4096, returned=4096
[HAL] no DMA interrupt received
```
根因: DMA配置正确但未触发中断，可能是Clock门控问题

---

## 2. 杂音/破音 (Audio Distortion)

### 2.1 分类

| 类型 | 特征 | 根因 |
|------|------|------|
| 爆音(Pop) | 单一脉冲噪声 | Gain突变/切换 |
| 削波(Clipping) | 持续失真 | 音量过大/数据溢出 |
| 射频干扰(RF) | 高频杂声 | 模拟地/屏蔽不良 |
| 量化噪声 | 底噪增大 | Bit depth不匹配 |

### 2.2 典型案例

**案例1: 播放开始时的爆音**
```
[HAL] out_set_parameters: mode=0 → 1
[HAL] pop_noise: speaker gain jumped from 0 to 100%
[DMA] transfer completed, underrun detected
```
根因: Codec切换模式时Gain设置未经fade，直接跳变导致爆音

**案例2: DMA buffer过小导致underrun**
```
[AudioFlinger] Mixer: 10ms latency configured
[Kernel] period_size=240, period_count=2
[HAL] out_write: underrun, frames=0
```
根因: CPU繁忙时10ms buffer不足以填补间隙

**案例3: 采样率不匹配导致破音**
```
[App] AudioTrack: 44100Hz
[HAL] codec_dai: 48000Hz configured
[DMA] sampling rate mismatch detected
```
根因: HAL自动重采样质量差或未使能重采样

---

## 3. 延迟问题 (Audio Latency)

### 3.1 延迟分解

```
总延迟 = App buffer + AudioFlinger buffer + HAL buffer + DMA buffer + Codec latency
```

| 阶段 | 典型值 | 可优化性 |
|------|--------|----------|
| App buffer | 10-20ms | App可控 |
| AF buffer | 5-20ms | 系统配置 |
| HAL buffer | 5-10ms | HAL厂商 |
| DMA buffer | 5-10ms | Kernel配置 |
| Codec | 5-15ms | 硬件固定 |

### 3.2 关键日志

```
[AudioFlinger] output latency=%u ms
[HAL] out_get_presentation_position: frames=%llu, timestamp=%lld
[HAL] latency_limiter: target=%ums, actual=%ums
```

### 3.3 低延迟配置

```cpp
// FastMixer路径 (低延迟)
AUDIO_OUTPUT_FLAG_FAST | AUDIO_OUTPUT_FLAG_FAST_MIXER

// 配置参数
audio_policy_configuration.xml:
  <mixPort name="low_latency" ...
    <profile samplingRates="48000"
            format="AUDIO_FORMAT_PCM_16_BIT"
            latencyMs="20"/>  <!-- 必须<20ms -->
```

---

## 4. 断续/卡顿 (Audio Dropout)

### 4.1 根因分类

| 根因 | 现象 | 关键指标 |
|------|------|----------|
| CPU繁忙 | 周期性卡顿 | CPU idle < 20% |
| Buffer过小 | 偶发卡顿 | underruns > 0 |
| 电源管理 | 长时间卡顿 | CPU降频 |
| 中断丢失 | 随机卡顿 | DMA irq miss |

### 4.2 典型日志

**Buffer Underrun (HAL层)**
```
[HAL] out_write: underrun occurred, frames lost=%d
[HAL] out_write: recovering from underrun
[AudioFlinger] track(0x1234): backend=%d, underruns=%d
```

**中断丢失 (Kernel层)**
```
[Kernel] DMA: irq status=0x0, expected=0x1
[Kernel] DMA: transfer error, retry count=3
[ASoC] codec: xrun detected
```

### 4.3 排查命令

```bash
# 查看AudioFlinger buffer状态
adb shell "dumpsys audioflinger" | grep -A5 "PlaybackThreads"

# 查看CPU调度
adb shell "dumpsys cpuinfo" | grep "busy"

# 查看电源状态
adb shell "dumpsys power" | grep -i "modes"
```

---

## 5. 录音问题 (Recording Issues)

### 5.1 录音无声

```
App: AudioRecord.read() returns 0
AF: RecordThread buffer is empty
HAL: in_read() returns -1, errno=ENODEV
Kernel: DMIC clock not enabled
```

### 5.2 录音杂音

| 杂音类型 | 特征 | 根因 |
|----------|------|------|
| 电源纹波 | 50/100Hz哼声 | DC-DC干扰 |
| 热噪声 | 持续底噪 | 模拟前端增益过高 |
| 数字噪声 | 不规则杂声 | I2S/TDM时序问题 |

### 5.3 录音断续

```
[HAL] in_read: buffer overflow, dropped=%d frames
[AudioFlinger] RecordThread: capture data gap detected
[App] AudioRecord: read returned partial data
```

---

## 6. 特定场景故障

### 6.1 通话场景

```
[VoIP] AudioRecord: source=VOICE_COMMUNICATION
[AudioPolicy] setInputDevice(0x8004)  // BT SCO
[HAL] in_set_parameters: incall_mute=0, echo_ref=1
```

**常见问题:**
- 回声: AEC未启用或配置错误
- 对方听不到: 上行路由错误
- 杂音: BT SCO带宽不足

### 6.2 蓝牙音频

```
[BluetoothAudio] offload encoding: %s
[BluetoothAudio] BT SCO: 16kHz, CVSD codec
[AudioFlinger] offload path enabled
```

**常见问题:**
- 延迟高: BT SCO固有的200ms延迟
- 断续: BT干扰导致packet loss

### 6.3 USB Audio

```
[USB] audio_stream_in: altsetting=%d, max_psize=%d
[USB] UAC: format=%d, sample_rate=%u
[HAL] UAC setup complete, iso transfer active
```

---

## 7. 厂商特定问题

### 7.1 Qualcomm

```
[QCOM] asm_stream: buffer_size=%u,bytes_per_frame=%u
[QCOM] afe: tx port started, port_id=%d
[QCOM] lpass: codec lock acquired
```

**常见问题:**
- Hexagon DSP挂死: 需要重启AFE
- 通话结束异常: AFE port未正确释放

### 7.2 MTK

```
[MTK] aud_drv: allocate buffer size=%u
[MTK] spk_mgr: speaker protection enabled
[MTK] afe: memory interface=%d
```

**常见问题:**
- 扬声器保护触发: 过温/过流误报
- 内存接口异常: EMI问题

### 7.3 Samsung

```
[Samsung] soundalive: effect enabled, mode=%d
[Samsung] anc: noise_level=%ddB, status=active
[Samsung] vss: voice sensor detected
```

---

## 8. 故障排查决策树

### 8.1 无声问题决策树

```
无声
├── 检查音量
│   └── 音量=0 → 确认用户设置
├── 检查输出设备
│   ├── 耳机模式 → 检查插拔检测
│   └── 扬声器模式 → 检查路由切换
├── 检查HAL write
│   ├── 返回成功 → 检查DMA
│   └── 返回失败 → 检查错误码
└── 检查AudioFlinger
    └── 无活跃track → 检查App start()
```

### 8.2 杂音问题决策树

```
杂音
├── 爆音(Pop)
│   └── 检查Gain切换是否有ramp
├── 削波(Clipping)
│   └── 降低音量/检查数据范围
├── 持续杂音
│   ├── 检查接地
│   └── 检查屏蔽
└── 偶发杂音
    └── 检查Buffer underrun
```
