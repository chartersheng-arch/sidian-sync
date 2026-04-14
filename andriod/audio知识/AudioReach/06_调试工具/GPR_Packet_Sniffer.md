# GPR Packet Sniffer Tool

## 1. 工具定位

GPR (General Purpose Register) Packet Sniffer 是一种**DSP 运行时 trace 工具**，用于：
- 抓取 DSP 内部寄存器数据
- 分析音频 Buffer 状态
- 诊断音频 Dropout / Glitch
- 测量 DSP 处理延迟

## 2. 工作原理

```
DSP GPR → Sniffer HW → Shared Memory → Host Tool
                                     ↓
                              解析 & 可视化
```

- DSP 上的 Module 可写入特定 GPR
- Sniffer HW 持续采样 GPR 数据
- 数据存到共享内存
- Host 端 Tool 读取并解析

## 3. 抓取配置

| 配置项 | 说明 |
|--------|------|
| **抓取时长** | 10ms - 10s 可配置 |
| **采样率** | GPR 更新率 (e.g., 48kHz) |
| **触发条件** | 立即触发 / 事件触发 |
| **GPR 选择** | 选择感兴趣的 Register |

## 4. 典型使用场景

### 4.1 Buffer Underrun 分析

```
配置:
- 抓取 Buffer Fill Level GPR
- 触发条件: Buffer < Threshold

结果:
- 显示 Buffer 下降沿
- 定位 Underrun 时间点
- 关联 Audio Glitch 发生时刻
```

### 4.2 DSP 负载分析

```
配置:
- 抓取 Module Processing Time GPR
- 抓取 DSP CPU Load GPR

结果:
- 显示每个 Module 的 CPU 占用
- 定位负载过高的 Module
```

### 4.3 音频事件关联

```
配置:
- 抓取 Timestamp GPR
- 关联 App event log

结果:
- 精确还原 Audio 事件时序
- 测量 App → DSP → DAC 的完整延迟
```

## 5. 日志格式

GPR Sniffer 输出典型格式：

```
[Timestamp] GPR_ID: Value
[0.001234] GPR_001: 0x1234  (Buffer Level)
[0.001236] GPR_002: 0x5678  (Module A Output)
[0.001238] GPR_003: 0x0001  (Event: Underrun Detected)
```

## 6. 分析步骤

```
1. 启用 Sniffer 抓取
2. 复现问题场景
3. 停止抓取，导出数据
4. 使用 Tool 可视化
5. 定位异常时间点
6. 关联日志定位根因
```

## 7. 与 QACT 的配合

| 工具 | 用途 | 数据类型 |
|------|------|----------|
| QACT | 参数配置/校准 | 参数值 |
| GPR Sniffer | 运行时 trace | 寄存器 trace |
| **配合使用** | 完整调试闭环 | 配置 → 验证 |
