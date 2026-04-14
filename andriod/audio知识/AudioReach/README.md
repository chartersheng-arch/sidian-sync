# AudioReach 知识库

高通 Qualcomm AudioReach 架构完整知识库，基于官方文档整理。

## 目录结构

```
audio/
├── 01_架构总览/          # 核心架构文档
├── 02_Android集成/       # Android 平台集成
├── 03_SPF框架/           # Signal Processing Framework 详解
├── 04_音频场景/          # 播放、录制、蓝牙编码场景
├── 05_LL_Pro_Audio/      # Low Latency & Pro Audio
├── 06_调试工具/          # QACT、GPR Sniffer 等工具
├── 07_调试定制/          # LA Customizations、Audio Device Customization
└── 08_总结/              # 综合总结
```

## 核心概念速查

| 概念 | 说明 |
|------|------|
| **AudioReach** | 高通音频架构总称，覆盖 Voice、Music、LL Audio 三大场景 |
| **SPF** | Signal Processing Framework，音频信号处理框架，基于 Graph/CAPI 架构 |
| **CAPI** | Common Audio Processor Interface，SPF 中的标准化 DSP 接口层 |
| **AFM** | Audio Fabric Manager，片上音频路由管理 |
| **Audio HAL** | Android Audio HAL，厂商定制层 |
| **Voice** | 语音通话架构，包含 VoIP/CSFB/VoLTE 多模式 |
| **LL Audio** | Low Latency Audio，游戏/实时音频场景 |
| **GPR** | General Purpose Register，调试用寄存器 |
| **QACT** | Qualcomm Audio Calibration Tool，音频校准工具 |

## 文档来源

- `80-VN500-3_c` — SPF Overview
- `80-VN500-2_ab` — Voice Architecture
- `80-VN500-7_b` — LA Architecture
- `80-VN500-19_aa` — AudioReach on Android
- `80-VN500-16_aa` — SPF Technical Overview
- `80-VN500-6_aa` — CAPI API Reference
- `80-VN500-14_ac` — SPF Porting Manual
- `80-VN500-26` — Playback & Record
- `80-VN500-21` — Bluetooth Encoder
- `80-PB802-2Pro` — LL Audio
- `80-vn500-11_b` — LA Customizations
- `80-vm407-18` — QACT v8 User Guide
- `80-vn500-12_ab` — GPR Packet Sniffer
- `80-pv345-49` — Audio Device Customization
