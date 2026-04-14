# SPF Technical Overview

## 1. Graph Engine

Graph Engine 是 SPF 的**运行时引擎**，负责：
- 加载 Graph 描述文件
- 管理 Module 实例
- 调度音频数据处理
- 处理数据流和控制命令

**Graph 描述文件格式:** XML 或二进制格式

## 2. Module 架构

### 2.1 Module 结构

```
Module Instance
    ├── CAPI v2 Interface (对外接口)
    ├── Module Private Data (内部状态)
    └── Algorithm (信号处理逻辑)
```

### 2.2 Module 类型

| 类型 | 说明 | 示例 |
|------|------|------|
| **Source** | 数据源 | I2S Rx, BT Rx, Memory |
| **Sink** | 数据目的地 | I2S Tx, BT Tx, Memory |
| **Processing** | 处理单元 | AEC, NS, EQ, Mixer |
| **Encoder** | 编码器 | EVRC, AMR, Opus |
| **Decoder** | 解码器 | EVRC, AMR, Opus |

## 3. Port 连接模型

```
Module A                Module B
  Out Port ──────────→ In Port
  [Buffer 0]           [Buffer 0]
                        Out Port ────→ Module C
```

- **1:1 连接**: 标准连接
- **1:N 连接**: 数据复制 (如录音 + 播放同时)
- **N:1 连接**: 数据混合 (如多路输入混音)

## 4. 数据 Buffer 机制

- Port 之间通过**共享内存**传递数据
- 每个 Buffer 有固定大小 (由 Graph 配置决定)
- 使用**Ping-Pong 双 Buffer** 避免读写冲突

## 5. 媒体格式协商

Module 之间需要协商媒体格式：
```c
// 支持的格式
typedef enum {
    CAPI_V2_PCM_FORMAT           // PCM 格式
    CAPI_V2_ENCODED_FORMAT       // 编码格式
} capi_v2_data_format_t;

// PCM 格式定义
typedef struct {
    uint32_t sample_rate;
    uint16_t bit_depth;
    uint16_t channels;
    uint16_t interleaved;
} capi_v2_pcm_format_t;
```

## 6. 控制命令

Module 通过 `set_param` / `get_param` 接口接收控制命令：

```c
// 典型参数 ID
#define PARAM_ID_AEC_ENABLE        0x10001
#define PARAM_ID_NS_LEVEL          0x10002
#define PARAM_ID_GAIN             0x10003
#define PARAM_ID_EQ_CURVE         0x10004
```

## 7. 生命周期管理

```
1. Load        → 加载 Module Library
2. Create      → 创建 Module 实例
3. Init        → 初始化 Module
4. Set Params  → 配置初始参数
5. Start       → 开始处理
6. Process     → 数据处理循环
7. Stop        → 停止处理
8. Deinit      → 释放资源
9. Destroy     → 销毁实例
```

## 8. DSP 多线程模型

- **独立 Thread**: 每个 Graph 运行在独立 DSP 线程
- **共享 Services**: 公共服务 (Clock, Memory) 可被多 Graph 共享
- **优先级**: Voice Graph 优先于 Music Graph

## 9. 调试接口

### 9.1 CAPI 日志
- Module 可以输出调试信息到共享内存
- 日志通过 Diag 端口上传到 Host

### 9.2 GPR 追踪
- 每个 Module 可以写入 GPR
- Sniffer Tool 抓取并可视化

### 9.3 性能监控
- 每个 Module 可报告 CPU 负载
- 用于定位性能瓶颈
