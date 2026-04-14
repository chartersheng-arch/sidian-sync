# SPF — Signal Processing Framework 概述

## 1. 定位

SPF (Signal Processing Framework) 是 AudioReach 的**核心信号处理引擎**，运行在高通 Hexagon DSP (ADSP) 上。负责所有音频信号处理模块的加载、连接、运行。

**核心思想：** 音频处理链路 = **Graph**（有向图），节点 = **Module**，边 = **Port 连接**。

## 2. 核心概念

### 2.1 Graph

Graph 是 SPF 中音频处理链路的抽象，由多个 Module 通过 Port 连接组成。

**Graph 的定义内容：**
- Module 列表
- Module 之间的 Connection 关系
- 每个 Module 的参数配置
- Buffer size / sample rate 等属性

### 2.2 Module

Module = 独立信号处理单元，封装特定算法。

**典型 Module：**
| Module | 功能 |
|--------|------|
| AEC | 声学回声消除 |
| NS | 噪声抑制 |
| EQ | 均衡器 |
| Resampler | 重采样 |
| Mixer | 混音 |
| Encoder/Decoder | 语音编解码 |
| Gain | 音量控制 |

### 2.3 Port & Connection

- **Port**: Module 的输入/输出端口
- **Connection**: Port 之间的连接关系（1:1 或 1:N）
- **Buffer**: Port 之间传递音频数据的共享内存

### 2.4 CAPI v2

CAPI (Common Audio Processor Interface) v2 是 Module 与 DSP Framework 之间的**标准化接口层**：
- 所有 Module 必须实现 CAPI v2 接口
- 保证了 Module 的可复用性和跨平台性

**CAPI v2 主要接口：**
```c
capi_v2_init()         // 初始化
capi_v2_process()      // 处理音频数据
capi_v2_set_param()    // 设置参数
capi_v2_get_param()    // 获取参数
capi_v2_set_media_type() // 设置媒体格式
```

## 3. Graph 生命周期

```
Load Graph → Init Modules → Start → Process Loop → Stop → Deinit
```

1. **Load**: 解析 Graph XML/二进制描述，加载 Module Library
2. **Init**: 调用每个 Module 的 `capi_v2_init()`
3. **Start**: 所有 Module 进入工作状态
4. **Process**: 数据在 Graph 中流动
5. **Stop**: 停止处理
6. **Deinit**: 释放资源

## 4. 静态 Graph vs 动态 Graph

| 类型 | 说明 | 场景 |
|------|------|------|
| **静态 Graph** | 编译时确定，运行时不可改变 | 普通 Music 播放 |
| **动态 Graph** | 运行时可根据场景重配置 | Voice Call 建立/断开 |

## 5. SPF 在各场景的角色

| 场景 | SPF 用途 |
|------|----------|
| Voice | VoIP/Voice Call 的语音处理 (AEC/NS/ENC/DEC) |
| Music | EQ/Mixer/Resampler 处理 |
| LL Audio | 低延迟处理链路 |
| Record | 前处理 (AEC/NS) + 编码 |

## 6. 调试接口

- **QACT**: 校准 Module 参数（增益/EQ/AEC强度）
- **GPR Sniffer**: 抓取 DSP 寄存器 trace，分析 Graph 运行时状态
- **Diag Port**: 通过 Diag 协议与 DSP 通信
