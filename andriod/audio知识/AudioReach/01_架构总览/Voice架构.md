# Voice 架构

## 1. Voice 覆盖的场景

Voice 架构支持三大语音通话模式：

| 模式 | 说明 |
|------|------|
| **CSFB** | Circuit Switched Fallback，传统 2G/3G 语音 |
| **VoLTE** | Voice over LTE，4G 语音 |
| **VoIP** | Voice over Wi-Fi/Internet，微信/QQ 等 App 语音 |

## 2. 语音通话路径

```
上行 (Mic → Network):
Mic → ADC → Audio Fabric → Voice SPF Graph
    → VOCPROC (语音处理) → VBI (编码)
    → Radio (4G/5G Modem)

下行 (Network → Speaker):
Radio → VBI (解码) → VOCPROC
    → Audio Fabric → DAC → Speaker
```

## 3. 语音处理模块 (VOCPROC)

VOCPROC 是 Voice SPF Graph 中的**核心处理单元**，包含：

| 子模块 | 功能 |
|--------|------|
| **AEC** | Acoustic Echo Cancellation，消除扬声器回声 |
| **NS** | Noise Suppression，抑制背景噪声 |
| **ENC** | 编码器 (EVRC/AMR/WB-AMR/Opus) |
| **DEC** | 解码器 |
| **Tty/HAC** | 听障无障碍支持 |

## 4. 关键设计点

### 4.1 Half-duplex vs Full-duplex

- **Full-duplex**: 双方同时说话（免提场景）
- **Half-duplex**: 单向通话（需要 PTT）

### 4.2 DTX (Discontinuous Transmission)

通话期间无话音时暂停传输，节省网络资源。

### 4.3 语音质量增强

- **Wideband AMR (WB-AMR)**: 宽带语音，音质更好
- **EVS**: 增强语音服务
- **PLC (Packet Loss Concealment)**: 丢包补偿

## 5. VoIP 特殊考虑

VoIP 场景额外涉及：
- **RTP/RTCP**: 实时传输协议
- **Jitter Buffer**: 缓冲网络抖动
- **Codec Selection**: Opus / G.711 / G.722
- **Echo Cancellation**: 需处理网络延迟带来的回声

## 6. 调试要点

| 问题 | 可能原因 | 排查工具 |
|------|----------|----------|
| 回声 | AEC 未启用 / AEC Path 错误 | QACT |
| 单通 | Half-duplex 误开启 / Routing 错误 | Voice Test |
| 延迟高 | Jitter Buffer 过大 / Codec 帧长 | GPR Sniffer |
| 杂音 | NS 强度不足 / 麦克风故障 | QACT + Voice Test |
