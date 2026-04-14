# LA Customizations

## 1. LA Customization 定位

LA (Low Audio) Customizations 允许定制 LL (Low Latency) Audio 场景的特定行为参数，适用于：
- 平台特定调优
- 功耗/性能平衡
- 特殊音频场景适配

## 2. 可定制参数

### 2.1 Buffer 配置

| 参数 | 说明 | 可选值 |
|------|------|--------|
| `ll_buffer_size` | LL Path Buffer 大小 | 5ms / 10ms |
| `ll_buffer_count` | Ping-Pong Buffer 数量 | 2 / 3 / 4 |
| `ll_latency_target` | 目标延迟 | 10ms / 15ms / 20ms |

### 2.2 Clock 配置

| 参数 | 说明 | 可选值 |
|------|------|--------|
| `clock_gating_enable` | 是否启用时钟门控 | ON / OFF |
| `clock_freq_target` | 目标时钟频率 | 150MHz / 300MHz / 600MHz |

### 2.3 Module 组合

| 参数 | 说明 | 说明 |
|------|------|------|
| `ll_modules_enabled` | LL Graph 启用的 Module | 可选组合 |
| `ll_bypass_aec` | LL Path 是否旁路 AEC | ON / OFF |

### 2.4 数据格式

| 参数 | 说明 | 可选值 |
|------|------|--------|
| `ll_sample_rate` | 采样率 | 44100 / 48000 / 96000 |
| `ll_bit_depth` | 位深 | 16 / 24 / 32 |
| `ll_channels` | 通道配置 | Mono / Stereo |

## 3. 定制流程

```
1. 确定目标场景 (游戏 / 实时监听 / 录音)
2. 测量当前延迟
3. 调整 Buffer 参数
4. 验证延迟和稳定性
5. 如果功耗过高 → 启用 Clock Gating
6. 保存到平台配置
```

## 4. 典型配置场景

| 场景 | Buffer Size | Clock Gating | Module |
|------|-------------|--------------|--------|
| 游戏语音 | 5ms | ON | Minimal |
| 实时监听 | 3ms | OFF | Full |
| 音乐制作 | 10ms | ON | Normal |

## 5. 验证方法

- 使用 `ll_latency_test` 工具测量实际延迟
- 运行 `stress_test` 验证无 Dropout
- 检查功耗计测量电流

## 6. 常见问题

| 问题 | 根因 | 解决 |
|------|------|------|
| 延迟不达标 | Buffer Size 过大 | 减小 Buffer |
| Dropout | Buffer Size 过小 | 增大 Buffer |
| 功耗高 | Clock Gating 关闭 | 启用 Clock Gating |
| 模块不工作 | Module 未加载 | 检查 Graph 配置 |
