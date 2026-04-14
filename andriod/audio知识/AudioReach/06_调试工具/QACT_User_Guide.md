# QACT — Qualcomm Audio Calibration Tool v8

## 1. 工具定位

QACT 是高通官方的**音频校准工具**，用于：
- 调整播放/录制增益
- 配置 EQ 曲线
- 校准 AEC/NS 参数
- 调试 TTY/HAC 无障碍功能
- 固化参数到 NV Memory

## 2. 界面结构

```
┌─────────────────────────────────────────┐
│  QACT Main Window                       │
│  ├── Device Connection Panel           │
│  ├── Audio Path Selector                │
│  ├── Calibration Controls               │
│  ├── Measurement Panel                 │
│  └── Log Window                         │
└─────────────────────────────────────────┘
```

## 3. 连接方式

| 连接方式 | 说明 |
|----------|------|
| **UART / Diag Port** | 通过串口与设备通信 |
| **USB** | QDSS / Diag over USB |
| **Network** | TCP/IP 远程调试 |

## 4. 核心校准项

### 4.1 播放增益 (Playback Gain)

- **Digital Gain**: DSP 内部数字增益 (dB)
- **Analog Gain**: DAC 前置模拟增益
- **目标**: 播放 1kHz 0dBFS 正弦波，测量输出电平

### 4.2 录制增益 (Record Gain)

- **Mic Gain**: 麦克风前置增益
- **PGIA (Programmable Gain Input Amplifier)**: 可编程输入放大
- **ADC Gain**: 模数转换增益
- **目标**: 录制 94dB SPL 1kHz 参考音，测量 ADC 输入电平

### 4.3 EQ 校准

- **Parametric EQ**: 频率 / 增益 / Q 值可调
- **预设曲线**: Flat / Bass Boost / Treble Boost / Vocal
- **测量工具**: FFT 频谱分析仪

### 4.4 AEC 校准

| 参数 | 说明 | 典型范围 |
|------|------|----------|
| AEC Enable | 启用/禁用 | ON/OFF |
| AEC Level | 抑制强度 | 0-100% |
| NLP Mode | 非线性处理模式 | 0/1/2/3 |
| ERLE | 回声衰减量 | >40dB |

### 4.5 NS 校准

| 参数 | 说明 | 典型范围 |
|------|------|----------|
| NS Enable | 启用/禁用 | ON/OFF |
| NS Level | 降噪强度 | 0-100% |
| Wind Noise Suppression | 风噪抑制 | ON/OFF |

## 5. 校准流程

```
1. 连接设备 (UART/USB)
2. 选择 Audio Path (e.g., HPH_L / MIC1)
3. 播放测试音 / 开始录制
4. 测量电平
5. 调整增益
6. 保存参数到 NV
```

## 6. 日志分析

**Log Window** 显示:
- 命令发送/接收状态
- 参数读写结果
- 错误信息
- DSP 响应时间

## 7. 常见错误

| 错误 | 原因 | 解决 |
|------|------|------|
| Device Not Found | 串口未连接 | 检查 COM port |
| Command Timeout | DSP 无响应 | 重启设备 |
| NV Write Failed | Flash 写保护 | 检查权限 |
| Cal Data Invalid | 校准数据损坏 | 恢复默认 |
