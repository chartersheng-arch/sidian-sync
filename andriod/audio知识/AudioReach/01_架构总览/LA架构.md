# LA — Low Audio Architecture

## 1. LA 定位

LA (Low Audio) 架构专为**低延迟音频**场景设计，核心目标是：
- **游戏语音/音效**: 实时反馈，延迟感知强
- **实时监听**: 耳机监听、乐器音效
- **语音唤醒**: SoundTrigger 协同

## 2. 延迟指标

| 指标 | 典型值 | 说明 |
|------|--------|------|
| Round-trip Latency | ~20ms | Mic → DSP → DAC 完整环 |
| App → DSP Latency | ~5ms | 共享内存高速通路 |
| Buffer Duration | 5-10ms | 每级 Buffer 大小 |

## 3. 架构特点

### 3.1 Fast Audio Path

LA 使用 **Fast Path** 绕开传统 Android AudioFlinger 的高延迟：
```
App (AudioTrack)
    ↓ 共享内存
ADSP (LL Graph)
    ↓ AFM
DAC → Speaker
```

### 3.2 LL Graph vs 普通 Graph

| 特性 | LL Graph | 普通 Music Graph |
|------|----------|------------------|
| Buffer Size | 小 (5ms) | 大 (20ms+) |
| Path | Fast Path | Normal Path |
| APM 介入 | 否 | 是 |
| 延迟 | 低 | 高 |
| 功耗 | 低 | 正常 |

### 3.3 与 SoundTrigger 协同

LL Audio 路径可以与 SoundTrigger 共存：
- SoundTrigger 负责语音唤醒
- LL Graph 负责唤醒后的实时音频处理

## 4. 关键配置参数

- **Buffer Size**: LL Graph 的 PCM buffer 长度
- **Sample Rate**: 通常 48kHz
- **Channels**: Mono / Stereo
- **Bit Depth**: 16-bit / 32-bit

## 5. LA Customizations

可定制项（参考 `80-vn500-11_b`）：
- Buffer Size 调优
- Clock Gating 策略
- Module 组合/旁路
- 与 LL Input/Output 路径的耦合

## 6. 调试方法

- QACT: 调整 LL 通路增益
- GPR Sniffer: 抓取 DSP trace 分析延迟
- 示波器: 测量 Mic 到 Speaker 的物理延迟
