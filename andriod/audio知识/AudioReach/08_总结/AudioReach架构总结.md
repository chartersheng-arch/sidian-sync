# AudioReach 架构总结

## 一、AudioReach 是什么

AudioReach 是高通设计的**全链路音频架构**，覆盖从应用层到 DSP/硬件的完整音频通路。旨在统一 Voice（语音通话）、Music（音乐播放）、LL Audio（低延迟音频）三大场景的信号处理。

**设计目标：**
- 统一音频信号处理框架（SPF）
- 标准化 DSP 接口（CAPI）
- 支持可配置的音频路由（Audio Fabric）
- 适配 Android/Linux 多平台

---

## 二、核心组件

### 2.1 整体分层架构

```
┌─────────────────────────────────────┐
│         Android / Linux App        │
├─────────────────────────────────────┤
│           Audio HAL (厂商实现)       │
├─────────────────────────────────────┤
│     Audio Policy Manager (APM)      │
├──────────┬──────────────┬───────────┤
│  Voice   │   LL Audio   │  Music    │
│  Path    │    Path      │   Path    │
├──────────┴──────────────┴───────────┤
│        Audio Fabric (路由矩阵)        │
├─────────────────────────────────────┤
│    SPF (Signal Processing FW)       │
│  ┌────────────────────────────────┐ │
│  │   Graph Engine (运行在 ADSP)    │ │
│  │   - CAPI (DSP 接口标准化层)     │ │
│  │   - Module Library (算法模块)   │ │
│  └────────────────────────────────┘ │
├─────────────────────────────────────┤
│      Hardware (DSP / CODEC / BT)    │
└─────────────────────────────────────┘
```

### 2.2 SPF — Signal Processing Framework

**核心定位：** 可配置的音频信号处理引擎，运行在高通 Hexagon DSP (ADSP) 上。

**关键特性：**
- 基于 **Graph** 模型：音频流被建模为"模块图"
- 每个算法封装为 **Module**，模块之间通过 **Port** 连接
- **CAPI v2** (Common Audio Processor Interface) 是 Module 与 DSP 之间的标准化接口
- 支持静态 Graph（编译时配置）和动态 Graph（运行时重配置）
- 平台无关：同一套 Graph 配置可跨 Linux/Android 移植

**Graph 组成：**
| 元素 | 说明 |
|------|------|
| Module | 独立信号处理单元（如 AEC、NS、EQ、Mixer） |
| Port | 模块输入/输出端口 |
| Connection | 端口之间的连接（1:1 或 1:N） |
| Buffer | 模块间传递音频数据的共享内存 |
| Stream | 音频流（PCM data/I2S/BT PCM 等） |

### 2.3 Voice 架构

**Voice 场景**涵盖三大模式：
- **CSFB** (Circuit Switched Fallback) — 传统 2G/3G 语音
- **VoLTE** (Voice over LTE)
- **VoIP** (Voice over Wi-Fi/Internet)

**Voice 通话路径：**
```
Mic → ADC → AFM → Voice SPF Graph → VOCPROC (语音处理) → VBI (语音编解码) → Radio
                                                                         ↓
Radio → VBI → VOCPROC → AFM → Audio DAC → Speaker
```

**关键模块：**
- **AEC** (Acoustic Echo Cancellation)
- **NS** (Noise Suppression)
- **ENC/DEC** (语音编解码：EVRC/AMR/WB-AMR)
- **Tty/HAC** (无障碍支持)

### 2.4 LL Audio (低延迟音频)

**目标场景：** 游戏语音、实时音效、耳机监控

**关键指标：**
- **Round-trip Latency**: ~20ms (取决于 SoC)
- 使用 **Fast Audio Path** 绕过传统 Audio HAL 的 Buffer 延迟
- LL Graph 与普通 Music Graph 独立，支持更短的 Buffer 配置

**架构特点：**
- LL Path 绕过 APM (Audio Policy Manager)，直接路由到 DSP
- 使用共享内存实现 App → DSP 的低延迟通信
- 支持 SoundTrigger (语音唤醒) 协同工作

### 2.5 Audio Fabric

**Audio Fabric = 音频路由矩阵**，管理 SoC 内部音频数据的路由。

**典型路由场景：**
- Playback: 内存 → Audio DAC → Speaker/Headphone
- Record: Mic → ADC → 内存
- Voice Call: Radio ↔ DSP ↔ CODEC
- BT Audio: 内存 ↔ BT SoC ↔ 蓝牙音频设备

**AFM (Audio Fabric Manager):**
- 负责配置路由交叉点 (Crossbar)
- 管理 Clock Gating（节省功耗）
- 处理 Sample Rate Conversion (SRC)

---

## 三、CAPI — Common Audio Processor Interface

### 3.1 定位

CAPI 是 **DSP 上运行的 Module 与 ADSP Framework 之间的 ABI 接口**，定义了：
- Module 的生命周期 (create/destroy/start/stop)
- 数据 buffer 的传递方式
- 控制命令 (set_param/get_param) 的格式

### 3.2 CAPIv2 主要接口

```c
// Module 实例创建
capi_v2_err_t capi_v2_init(capi_v2_t*,
                           capi_v2_proplist_t* init_proplist);

// 主动请求输入数据
capi_v2_err_t capi_v2_process(capi_v2_t*,
                              capi_v2_buf_t* input[],
                              capi_v2_buf_t* output[]);

// 媒体格式协商
capi_v2_err_t capi_v2_set_media_type(capi_v2_t*,
                                     capi_v2_stream_type_t,
                                     capi_v2_media_format_t*);

// 参数设置/获取
capi_v2_err_t capi_v2_set_param(capi_v2_t*, uint16_t id,
                                capi_v2_buf_t*);
capi_v2_err_t capi_v2_get_param(capi_v2_t*, uint16_t id,
                                capi_v2_buf_t*);
```

### 3.3 CAPI Module 开发流程

1. 实现 `capi_v2_vtbl_t` 函数表
2. 在 `init()` 中分配 Module 私有数据
3. 在 `process()` 中实现信号处理逻辑
4. 在 `set_param()` 中处理 DSP 参数
5. 注册到 Module Library 供 Graph Builder 调用

---

## 四、Android 集成

### 4.1 整体 Android 音频架构

```
App (AudioTrack/AudioRecord)
    ↓
AudioFlinger (Audio HAL Client)
    ↓
Audio HAL (vendor/qcom/...)
    ↓
Audio DSP (ADSP via SPF Graph)
    ↓
Hardware (CODEC / BT SoC)
```

### 4.2 高通 Android Audio HAL

**Audio HAL 路径：** `hardware/qcom/audio/`

**关键组件：**
- `audio_hw.c` — HAL 主实现，映射到 AFM
- `voice.c` — VoIP/VoLTE 通话控制
- `platform.c` — 平台特定路由逻辑
- `，声音路由策略：speaker/headphone/bt-sco/bt-a2dp`

**Audio Policy 配置：** `audio_policy.conf` 定义输出设备优先级、采样率、通道数等。

### 4.3 关键 HAL 接口

```c
// playback
int adev_open_output_stream(...);
int adev_close_output_stream(...);
ssize_t out_stream_write(...);

// record
int adev_open_input_stream(...);
int adev_close_input_stream(...);
ssize_t in_stream_read(...);

// voice
int adev_set_voice_volume(float);
int adev_start_voice_call(...);
int adev_stop_voice_call(...);
```

---

## 五、调试工具链

### 5.1 QACT — Qualcomm Audio Calibration Tool

**用途：** 校准音频通路增益、EQ、麦克风参数。

**工作流程：**
1. 连接设备，配置 COM port
2. 通过 UART/Diag 端口发送调试命令
3. 播放标准测试音，测量频响
4. 调整参数后固化到 NV memory

**关键调试项：**
- 播放/录制增益 (dB)
- EQ 曲线 ( parametric EQ )
- AEC/NS 强度
- TTY/HAC 电平

### 5.2 GPR Packet Sniffer

**用途：** 抓取 DSP GPR (General Purpose Register) 轨迹，分析 DSP 运行状态。

**使用方式：**
- 启用后抓取指定时间窗口的 GPR 数据
- 解析 Sniffer Log 分析音频事件、DSP 中断、Buffer 状态

**典型场景：**
- 音频 Dropout 分析
- DSP 负载过高排查
- Buffer Underrun/Overrun 诊断

### 5.3 LA Customizations

**用途：** Low Audio 场景的定制化参数配置。

**可定制项：**
- LL Graph 的 Buffer Size
- Clock Gating 策略
- 特定平台的 Module 组合

---

## 六、分析方法论

### 6.1 音频问题通用排查流程

```
┌─────────────────────────────────────────┐
│ Step 1: 确认问题边界                      │
│ - Playback / Record / Voice Call ?      │
│ - 是否有特定触发条件（特定 App/编解码/设备）│
└───────────────┬─────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│ Step 2: 检查路由和 HAL 层                │
│ - audio_policy.conf 是否正确             │
│ - 是否走到正确的 Audio HAL path          │
│ - adev_open_output_stream 日志           │
└───────────────┬─────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│ Step 3: 检查 DSP / SPF Graph            │
│ - Graph 是否正确加载                      │
│ - CAPI Module 是否初始化成功             │
│ - Buffer 是否正常传递                    │
│ → GPR Sniffer + QACT 定位               │
└───────────────┬─────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│ Step 4: 检查硬件/CODEC                   │
│ - Clock 配置是否正确                     │
│ - I2S/TDM 通道配置是否匹配               │
│ - Codec 寄存器状态                       │
└─────────────────────────────────────────┘
```

### 6.2 延迟类问题分析

| 指标 | 正常范围 | 异常指向 |
|------|----------|----------|
| LL Round-trip | ~20ms | Buffer Size 过大 |
| Playback 首次出音 | <100ms | Graph 加载延迟 |
| Voice 延迟 | 50-150ms | Jitter Buffer 配置 |

**排查工具：**
- `out_stream_write()` 到 Speaker 出音的时间差
- DSP trace (GPR Sniffer)
- `audioflinger` 统计信息

### 6.3 音质类问题分析

| 问题 | 根因 | 工具 |
|------|------|------|
| 杂音/破音 | Buffer Underrun / Clock Glitch | GPR Sniffer |
| 低声/无声 | 增益配置错误 / Mute 状态 | QACT |
| 回声 | AEC 未启用 / 强度不足 | Voice Test |
| 噪声 | NS 关闭 / 强度过低 | Voice Test |

### 6.4 Voice 问题分析

```
VoIP 延迟高 → 检查 Jitter Buffer / RTP 打包
回声       → 检查 AEC enable + AEC Path 配置
单通       → 检查 Half duplex / Duplex mode
无声       → 检查 Codec enable / Routing
```

---

## 七、参考资料

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
