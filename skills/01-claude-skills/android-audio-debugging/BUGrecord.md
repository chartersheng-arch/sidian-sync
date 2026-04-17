# Android Audio Debugging - BUG分析记录

> 用于记录分析过程中的偏离情况，帮助迭代skill方法论
> **自动追加**：当分析出根因但用户未采纳时，skill会自动追加记录
> **用途**: 积累多份后提交给skill作者用于归纳高正确率分析流程

---

## 使用说明

### 自动记录（推荐）
当满足触发条件时，skill会自动将分析过程追加到本文件末尾（每个问题之间用 `---` 分隔）。

### 记录格式
- 时间格式：`YYYY-MM-DD HH:MM`（精确到分钟）
- 分析过程只记录偏离方向和纠正方向的要点

---

## 问题记录

<!-- 下面的内容由skill自动追加，每次追加用 --- 分隔 -->


---
## [问题1] AI通话"小爱帮我回"下行声音泄漏
**记录时间**: 2026-04-15 16:41

### 基本信息
- **设备**: Redmi (somalia), BP2A.250605.031.A3
- **平台**: Android 16 / 展锐(sprd)
- **问题时间**: 2025-12-12 15:36

### 问题现象
AI通话开启"小爱帮我回"时，辅助机说话测试机能听见（应听不见）

### 偏离要点
**初始方向**: AudioPolicy路由策略问题 - Phone state=NORMAL导致Speaker未被静音
**偏离**: 遗漏搜索log中`set_parameters`实际下发记录，直接从源码推导

### 纠正要点
**触发**: 用户提醒`voice_dl_mute`有上层下发
**发现**:
- `persist.vendor.audio.voice_dl_mute=500` 属性存在但code未使用
- log中无`voice_dl_mute=true/false`实际下发记录
- `cvrs_mute`只控制`AUDIO_APP_SCENE_VOICE_CALL`，不处理VOIP场景

### 根因
AI通话VOIP场景的下行静音未被处理，需在上层确认是否下发`voice_dl_mute`参数

### 修复方案
在`audio_voice.c`的`voice_set_parameters()`中添加`voice_dl_mute`参数处理

### Skill改进
- [x] 分析流程增加"搜索log中set_parameters实际下发"步骤
- [ ] 添加"属性存在但未使用"的检查项

<!-- 全程记录: 2026-04-15 16:41 -->

---
## [问题2] 蓝牙A2DP收到消息时暂时无声
**记录时间**: 2026-04-16

### 基本信息
- **设备**: Redmi (测试机) / REDMI 15R 5G (对比机)
- **平台**: Android / 展锐(Unisoc/Sprd)
- **问题时间**: 2025-10-28
- **复现率**: 必现

### 问题现象
连接LDAC蓝牙耳机进入游戏/音乐，收到微信/QQ信息时游戏声音暂时无声（约500ms）

### 初始分析方向
**方向**: A2DP Suspend-Resume Race Condition
**假设**: StartRequest在ack_stream_suspended前被调用，导致状态机处理异常
**证据**:
```
00:53:00.839  SuspendRequest
00:53:00.964  ack_stream_suspended (125ms延迟)
00:53:00.981  StartRequest ← 在ack前被调用!
00:53:01.531  ack_stream_started (550ms延迟!)
```

### 偏离轨迹
**偏离点**: 一开始认为是race condition，在AudioFlinger层需要加锁机制
**分析内容**:
- 分析了AudioFlinger.cpp中setParameters的错误处理逻辑
- Threads.cpp中`INVALID_OPERATION`触发standby的代码路径
- 搜索了ack_stream_suspended/started等回调机制

### 纠正要点
**触发**: 用户解释代码逻辑后确认真正根因
**发现**:
1. **Bluetooth stream使用父类**，不接受任何parameter设置
2. **返回`EX_UNSUPPORTED_OPERATION`**，而不是`INVALID_OPERATION`
3. **unisoc和原生代码一致**，直接使用父类
4. **Primary部分**，unisoc有重新申明此函数，不包含的parameter直接返回OK

### 根因结论
**问题本质**: Bluetooth A2DP HAL的stream实现直接使用父类，不处理任何setParameters调用，返回错误。上层AudioFlinger收到错误后触发异常standby逻辑，导致蓝牙音频中断。

**不是race condition问题**，而是**setParameters错误处理问题**。

### 修复方案
在`PlaybackThread::setParameters()`中判断模块类型，**只发给PRIMARY HAL**：
```cpp
if (strcmp(mOutput->audioHwDev->moduleName(), AUDIO_HARDWARE_MODULE_ID_PRIMARY) == 0) {
    status = mOutput->stream->setParameters(keyValuePair);
}
```

### Skill改进
- [x] 增加"区分不同错误码含义"检查项（UNSUPPORTED_OPERATION vs INVALID_OPERATION）
- [x] 增加"确认是race condition还是错误处理问题"的判断步骤
- [ ] 收集更多类似案例：HAL层返回错误时上层的行为差异

<!-- 全程记录: 2026-04-16 -->

### 诊断元信息
| 字段 | 值 |
|------|-----|
| 分析花费时长 | 待补充 |
| 会话数 | 待补充 |
| Token使用量 | 待补充 |
| 分析轮次 | 2轮（第1轮race condition方向 → 第2轮确认错误处理问题） |
| 关键转折点 | 用户解释Bluetooth stream使用父类，返回EX_UNSUPPORTED_OPERATION |
<!-- 元信息记录: 2026-04-16 -->

---
## [问题3] 达音科DT C100 USB耳放通话时声音从听筒出
**记录时间**: 2026-04-16 22:45

### 问题现象
连接达音科 DT C100 USB 耳放，建立通话，声音从听筒出（必现）
期望：声音应该从 USB 耳放设备出

### 初始分析方向
**方向**: AudioPolicy 路由策略问题
**假设**: USB 耳放在通话场景下被错误路由到听筒而非 USB 输出设备
**证据**:
- `createAudioPatch outputDevices=AUDIO_DEVICE_OUT_EARPIECE`（错误）
- `last.outputDevices` 显示 USB_HEADSET 已连接但未使用

### 偏离轨迹
**偏离点**: 一开始认为问题在 AudioPolicy 的 `getDeviceForStrategy()` 路由决策
**触发纠正的契机**: 用户补充了 `vendor/unisoc/audio/.../usb.c` 源码
**发现**: 真正问题在 `usb_call_supported` 参数设置逻辑，而非 AudioPolicy 路由函数
**偏离根因**: [x] 根因在上层参数设置，非路由决策

### 根因结论
**最终确认的分析方向**: Vendor HAL 层 USB 参数解析逻辑错误
**根因**: `vendor/unisoc/audio/.../usb.c` 第 367-373 行中 `usb_call_supported` 逻辑错误

```c
// 错误逻辑（当前）
if (usb_is_playback_supported() && usb_is_capture_supported())
    str_parms_add_str(reply, "usb_call_supported", "true");

// 问题：DTC-100 是纯播放设备（capture=false）
// 导致 usb_call_supported=false，通话时 USB 耳放无法使用
```

**修复建议**:
```c
if (usb_is_playback_supported())  // 只需 playback 支持即可用于通话
    str_parms_add_str(reply, "usb_call_supported", "true");
```

### 诊断元信息
| 字段 | 值 |
|------|-----|
| 分析花费时长 | 约30分钟 |
| 会话数 | 2次 |
| Token使用量 | 约150K |
| 分析轮次 | 2轮（第1轮AudioPolicy方向 → 第2轮确认vendor代码问题） |
| 关键转折点 | 用户补充 vendor/usb.c 源码后定位到 usb_call_supported 参数逻辑 |

<!-- 全程记录: 2026-04-16 22:45 -->
