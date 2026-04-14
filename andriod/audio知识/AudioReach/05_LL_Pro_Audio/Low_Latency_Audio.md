# Pro Audio & Low Latency (LL) Audio

## 1. Pro Audio 场景

**目标用户:** 专业音乐制作、游戏音效、实时监听

**核心诉求:**
- 极低延迟 (< 10ms)
- 高音质 (24-bit / 96kHz)
- 稳定的 Buffer 供应

## 2. Low Latency 架构

### 2.1 延迟构成

```
总延迟 = App Buffer + DSP Buffer + AFM + DAC Buffer
```

| 阶段 | 正常延迟 | LL 延迟 |
|------|----------|---------|
| App → DSP | 5-10ms | 2-3ms |
| DSP Processing | 5ms | 2-3ms |
| AFM | 1ms | <1ms |
| DAC | 3-5ms | 2-3ms |
| **总计** | **~20ms** | **~10ms** |

### 2.2 Fast Path vs Normal Path

```
Normal Path:
App → AudioFlinger → Audio HAL → APM → DSP → AFM → DAC
      (高延迟)        (Buffering)  (Policy) (Graph)

Fast Path (LL):
App ──→ DSP (共享内存) ──→ AFM ──→ DAC
  (极低延迟)    (LL Graph)
```

### 2.3 LL Graph 特点

- 独立于 APM (Audio Policy Manager)
- 最小化 Buffer 级数
- 绕过 AudioFlinger 的 Session 管理
- 使用 **共享内存** 直接与 App 通信

## 3. LL Audio 配置参数

| 参数 | 说明 | LL 典型值 |
|------|------|-----------|
| Buffer Size | 每级 Buffer 大小 | 5ms |
| Buffer Count | Ping-Pong Buffer 数 | 2 |
| Sample Rate | 采样率 | 48kHz |
| Bit Depth | 位深 | 16-bit |
| Channels | 通道 | Mono / Stereo |

## 4. 与 SoundTrigger 协同

```
语音唤醒事件 → SoundTrigger → 唤醒 App
                           → 激活 LL Graph
```

- SoundTrigger 监听关键词 (OK Google / Alexa)
- 唤醒后 LL Graph 接管实时音频

## 5. Pro Audio 使用场景

| 场景 | 延迟要求 | 实现方式 |
|------|----------|----------|
| 游戏语音 | 20ms | LL Audio + 共享内存 |
| 实时监听 | 10ms | LL + 双 DAC |
| 乐器音效 | 5ms | Pro Audio Path |
| 录音监耳 | 10ms | LL + Full-Duplex |

## 6. 功耗考虑

LL Audio 虽然延迟低，但功耗更高：
- 更多 DSP 占用时间
- 禁用 Clock Gating
- 保持更高时钟频率

## 7. 调试方法

```bash
# 测量延迟
adb shell dumpsys audio | grep latency

# 检查 LL Path 是否激活
adb shell logcat | grep -i "ll_audio\|fast_path"
```

## 8. 常见问题

| 问题 | 根因 | 解决 |
|------|------|------|
| LL 模式不激活 | App 未请求 LL flag | 检查 AudioTrack flags |
| 延迟仍高 | Buffer 级数过多 | 减少 Graph Module |
| 杂音 | Buffer Underrun | 增加 Buffer Size |
| 功耗过高 | LL Path 常开 | 动态切换 LL/Normal |
