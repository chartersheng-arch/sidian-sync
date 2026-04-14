# Audio Device Customization

## 1. 文档概述

此文档描述如何**定制化音频设备参数**，包括：
- CODEC 配置
- 麦克风配置
- 扬声器配置
- 音频通路路由规则

## 2. CODEC 定制

### 2.1 播放通路 (Playback)

| 参数 | 说明 | 典型值 |
|------|------|--------|
| `dac_gain` | DAC 输出增益 | 0 ~ 20 dB |
| `dac_format` | DAC 数据格式 | I2S / TDM / PCM |
| `dac_sample_rate` | 支持的采样率 | 48k / 96k / 192k |
| `dac_clock_mode` | 主/从模式 | Master / Slave |

### 2.2 录制通路 (Record)

| 参数 | 说明 | 典型值 |
|------|------|--------|
| `adc_gain` | ADC 输入增益 | 0 ~ 40 dB |
| `adc_format` | ADC 数据格式 | I2S / TDM / PCM |
| `mic_bias` | 麦克风偏置电压 | 1.8V / 2.1V / 2.8V |
| `mic_type` | 麦克风类型 | Analog / Digital / MEMS |

## 3. 麦克风配置

### 3.1 模拟麦克风

```
配置项:
- MIC_BIAS voltage
- 偏置电阻 (2.2kΩ / 4.7kΩ)
- 输入增益 (PGA)
- 高通滤波 (HPF) cutoff
```

### 3.2 数字麦克风 (PDM / I2S)

```
配置项:
- PDM CLK 频率 (1-3.072MHz)
- PDM 通道映射 (L/R)
- I2S 格式 (Standard / Left-justified)
- 时钟延迟 (Setup / Hold)
```

## 4. 扬声器配置

| 参数 | 说明 | 典型值 |
|------|------|--------|
| `speaker_impedance` | 阻抗检测 | 4Ω / 8Ω / 16Ω |
| `speaker_gain` | 扬声器增益 | 0 ~ 12 dB |
| `speaker_protection` | 保护使能 | ON / OFF |
| `temp_protection` | 过温保护 | ON / OFF |

## 5. 路由规则配置

定义不同场景下的音频路由：

```xml
<!-- 音乐播放路由 -->
<route>
    <source>Playback</source>
    <sink>CODEC_Speaker</sink>
    <devices>speaker headphone</devices>
</route>

<!-- 免提通话路由 -->
<route>
    <source>Voice</source>
    <sink>CODEC_HPH</sink>
    <sink>CODEC_Mic1</sink>
    <devices>voice_call</devices>
</route>

<!-- 蓝牙语音路由 -->
<route>
    <source>BT_HFP</source>
    <sink>BT_SCO</sink>
    <devices>bt_sco</devices>
</route>
```

## 6. 阻抗检测 (RDC)

- 用于检测耳机/扬声器阻抗
- 判断设备类型 (headphone / lineout / none)
- 防止输出到短路负载

## 7. 温度保护

| 阈值 | 动作 |
|------|------|
| 85°C | 告警，降低功率 |
| 105°C | 强制静音 |
| 120°C | 关闭输出 |

## 8. 调试工具

- QACT: 配置上述所有参数
- 示波器/万用表: 验证硬件电平
- Acoustic Test: 验证声学性能

## 9. 常见问题

| 问题 | 根因 | 解决 |
|------|------|------|
| 播放无声 | CODEC 未使能 | 检查时钟配置 |
| 录音无声 | MIC_BIAS 缺失 | 检查偏置电压 |
| 阻抗检测失败 | 硬件故障 | 检查 jack 座子 |
| 过温保护触发 | 散热不良 | 检查温度阈值 |
