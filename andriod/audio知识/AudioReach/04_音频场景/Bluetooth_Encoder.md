# AudioReach Bluetooth Encoder

## 1. 蓝牙音频概述

AudioReach 支持两大蓝牙音频场景：

| Profile | 用途 | 典型编解码器 |
|---------|------|------------|
| **A2DP** | 音乐播放 | SBC, AAC, aptX, LDAC |
| **HFP** | 蓝牙语音 | CVSD, mSBC |

## 2. A2DP 音频路径

```
Playback Graph (DSP)
    ↓  PCM 48k Stereo
Bluetooth Encoder Module
    ↓  编码 (SBC/AAC/aptX)
BT SoC (传输层)
    ↓ 无线
BT 耳机 / 音箱
```

**编码流程:**
1. PCM 数据从 Playback Graph 输入
2. Encoder Module 执行编码
3. 编码后数据送到 BT SoC
4. BT SoC 负责无线传输

## 3. HFP 蓝牙语音路径

```
Mic
    ↓
BT SoC (CVSD/mSBC 编码)
    ↓
Bluetooth Decoder Module
    ↓  PCM 8k/16k
Voice Graph (AEC/NS 处理)
    ↓
网络传输
```

**上行:**
- mSBC (Wideband) → 解码 → Voice 处理 → 传输

**下行:**
- 网络 → Voice 处理 → mSBC 编码 → BT SoC → 耳机

## 4. LE Audio (Bluetooth Low Energy Audio)

**新架构:**
- 支持 **LC3** 编解码器
- 比 SBC 更低延迟 + 更高音质
- 广播音频 (Broadcast Audio)

## 5. 关键调试参数

| 参数 | 说明 | 典型值 |
|------|------|--------|
| Bitpool | SBC 编码质量 | 53 (high quality) |
| Sample Rate | 采样率 | 48kHz |
| Channel Mode | 通道模式 | Stereo / Mono |
| MTU Size | BLE 最大传输单元 | 512 bytes (LE) |

## 6. 常见蓝牙音频问题

| 问题 | 根因 | 排查 |
|------|------|------|
| 蓝牙播放卡顿 | A2DP 缓冲不足 / 干扰 | 检查 A2DP Bitpool |
| 蓝牙通话无声 | HFP 未连接 / 编解码器不匹配 | 确认 mSBC 支持 |
| 延迟高 | 蓝牙固有延迟 | 使用 aptX LL / LE Audio |
| 杂音 | RF 干扰 / 编码错误 | 检查 RSSI / 编码器状态 |
