# AudioReach 架构概述

## 1. 定位与范围

AudioReach 是高通音频架构的**总称**，覆盖：
- **Music** — 音乐播放
- **Voice** — 语音通话（VoLTE/VoIP/CSFB）
- **LL Audio** — 低延迟音频（游戏音效/实时监听）
- **Pro Audio** — 专业音频场景

## 2. 核心设计思想

### 2.1 统一框架 (SPF)

所有音频场景共享同一个 Signal Processing Framework：
- 模块化信号处理（Graph + Module + Port）
- 统一的可视化配置工具
- 跨平台移植（Linux / Android）

### 2.2 分层隔离

```
┌──────────────────────────────────────┐
│        Framework / App               │
├──────────────────────────────────────┤
│         Audio HAL                   │  ← 厂商定制
├──────────────────────────────────────┤
│     Audio Policy Manager             │
├──────────────────────────────────────┤
│      Audio Fabric (AFM)             │  ← 路由矩阵
├──────────────────────────────────────┤
│     SPF Graph (ADSP / Hexagon)      │  ← 核心处理
├──────────────────────────────────────┤
│        CODEC / BT SoC               │
└──────────────────────────────────────┘
```

## 3. Audio Fabric (AFM)

Audio Fabric = 片上音频**路由交换矩阵**，实现音频数据在各个模块之间的灵活路由。

**核心功能：**
- 路由配置（Crossbar）
- 时钟管理（Clock Gating / PLL 配置）
- 采样率转换 (SRC)
- 功耗管理

**典型路由场景：**
- I2S: 外接 DSP / CODEC
- PCM: 蓝牙 Voice
- Slimbus: 内部连接
- BT PCM: 蓝牙语音

## 4. 场景化路径

| 场景 | 路径特点 |
|------|----------|
| Music | Playback Graph → AFM → DAC → Speaker |
| Voice | Radio ↔ Voice Graph ↔ AFM ↔ CODEC |
| LL Audio | App → Fast Path → DSP → AFM → DAC |
| Record | Mic → ADC → AFM → Record Graph → Memory |

## 5. 与 Android 关系

AudioReach 通过 **Audio HAL** 与 Android 集成：
- Qualcomm HAL 实现: `hardware/qcom/audio/`
- AudioFlinger 通过 HAL 访问 AudioReach 功能
- Audio Policy 配置路由规则

## 6. 关键设计优势

1. **统一调试工具链**: QACT / GPR Sniffer 覆盖全场景
2. **可配置的 Graph**: 无需修改 DSP 代码即可调整音频处理链路
3. **低延迟路径**: LL Audio 通过 Fast Path 绕过高延迟的 AudioFlinger
4. **可移植性**: SPF Graph 定义与平台解耦
