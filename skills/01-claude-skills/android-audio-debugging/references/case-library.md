# Android Audio 历史案例库

## 案例格式模板

```markdown
## [案例ID] 案例标题

**基本信息**
- 设备: <型号>
- 平台: <Android版本> / <平台>
- 日期: <YYYY-MM-DD>
- 分类: <无声/杂音/延迟/爆音/断续>

**问题现象**
<客观描述>

**根因**
<直接原因 + 传播路径>

**关键日志**
\`\`\`
[Log] 关键日志片段
\`\`\`

**解决方案**
<代码修改/配置调整/补丁>

**验证方法**
<测试步骤 + 预期结果>

**备注**
<扩展信息/影响范围>
```

---

## 高通平台案例

### 案例-QCOM-001: 空路由导致AudioStreamOut永久standby

**基本信息**
- 设备: Xiaomi 12
- 平台: Android 13 / QCOM SM8450
- 日期: 2024-01-15
- 分类: 无声

**问题现象**
播放音乐10秒后声音消失，日志显示AudioFlinger::Thread进入standby后无start

**根因**
AudioPolicyManager::getDeviceForStrategy在耳机拔出后返回空设备，上层未处理fallback，导致AudioStreamOut无法退出standby

**关键日志**
```
[AudioPolicy] setPhoneState(0)
[AudioPolicy] setOutputDevice(0x0)  // 空设备
[AudioFlinger] PlaybackThread: standby
[AudioFlinger] PlaybackThread: no start received
```

**解决方案**
在getDeviceForStrategy最后增加fallback到DEVICE_OUT_SPEAKER

**验证方法**
播放音乐30秒无断音，日志中standby后应有start

---

### 案例-QCOM-002: FastMixer路径CPU占用过高

**基本信息**
- 设备: Samsung S24
- 平台: Android 14 / QCOM SM8650
- 日期: 2024-03-20
- 分类: 延迟

**问题现象**
VoIP通话延迟高达500ms，用户感知明显

**根因**
FastMixer线程被低优先级任务抢占，调度延迟累积

**关键日志**
```
[AudioFlinger] FastMixerThread: CPU=%lld, "%"=%llu (wall=%lld)
[AudioFlinger] Scheduling: latency=%ums, priority=%d
[Kernel] sched: rt_rq run delayed, wait=%ums
```

**解决方案**
调整FastMixer线程优先级为RT，绑定到特定CPU核心

**验证方法**
VoIP通话延迟<100ms，perfetto trace显示FastMixer无调度延迟

---

## MTK平台案例

### 案例-MTK-001: 扬声器保护触发误报

**基本信息**
- 设备: OPPO Find X7
- 平台: Android 14 / MTK Dimensity 9300
- 日期: 2024-02-10
- 分类: 无声

**问题现象**
通话时扬声器无声，Speaker Protection报错

**根因**
Speaker Protection算法将正常语音判定为异常，过温保护误触发

**关键日志**
```
[MTK] spk_mgr: speaker protection triggered
[MTK] spk_mgr: temperature=%d, threshold=%d
[MTK] aud_drv: speaker muted by protection
```

**解决方案**
调整Speaker Protection阈值，增加确认机制避免误触发

**验证方法**
通话10分钟无保护误触发，录音波形正常

---

### 案例-MTK-002: 录音Buffer Overflow

**基本信息**
- 设备: Vivo X100
- 平台: Android 13 / MTK Dimensity 8200
- 日期: 2024-04-05
- 分类: 断续

**问题现象**
录音出现周期性断续，每隔5秒丢失约0.5秒音频

**根因**
RecordThread buffer配置过小，CPU繁忙时无法及时读取

**关键日志**
```
[HAL] in_read: buffer overflow, dropped=%d frames
[AudioFlinger] RecordThread: capture data gap detected
[AudioFlinger] track(0x1234): overruns=%d
```

**解决方案**
增加RecordThread buffer size从960帧到1920帧

**验证方法**
录音30分钟无断续，overruns计数保持为0

---

## 展锐平台案例

### 案例-SPRD-001: DMA传输错误导致杂音

**基本信息**
- 设备: 某平板
- 平台: Android 13 / 展锐SC9863A
- 日期: 2024-05-12
- 分类: 杂音

**问题现象**
播放音频时随机出现杂音，类似射频干扰声

**根因**
DMA descriptor配置错误，burst size与FIFO大小不匹配

**关键日志**
```
[Kernel] DMA: transfer error, retry count=3
[ASoC] pcmCVDDrv: xrun detected
[dmesg] DMA: alignment error, addr=%x
```

**解决方案**
修正DMA descriptor的burst size配置

**验证方法**
播放24bit/96kHz高采样率音频1小时无杂音

---

## 通用案例

### 案例-GEN-001: Bluetooth A2DP断连后路由未恢复

**基本信息**
- 设备: 通用
- 平台: Android 11+
- 分类: 无声

**问题现象**
蓝牙耳机断开后，音频无法切换到扬声器

**根因**
AudioPolicy未正确处理BT设备断开事件，output device未更新

**关键日志**
```
[BluetoothAudio] A2DP connection state: disconnected
[AudioPolicy] setOutputDevice(0x100)  // BT device仍被引用
[AudioFlinger] output: device not available
```

**解决方案**
在BT断开时强制清除路由缓存，重新计算有效设备

**验证方法**
BT断开后立即播放，音频切换到扬声器

---

## 案例匹配特征索引

### 按问题类型

| 问题类型 | 常见根因 | 案例 |
|----------|----------|------|
| 无声 | 路由空设备 | QCOM-001 |
| 无声 | Speaker Protection | MTK-001 |
| 无声 | BT路由未恢复 | GEN-001 |
| 杂音 | DMA配置错误 | SPRD-001 |
| 延迟 | FastMixer调度 | QCOM-002 |
| 断续 | Buffer过小 | MTK-002 |

### 按平台

| 平台 | 案例数 | 主要问题 |
|------|--------|----------|
| Qualcomm | 2 | 路由、调度 |
| MTK | 2 | 保护、Buffer |
| Spreadtrum | 1 | DMA |
| 通用 | 1 | 蓝牙 |

### 按错误码

| 错误码 | 含义 | 案例 |
|--------|------|------|
| -ENODEV | 设备不存在 | QCOM-001 |
| -EINVAL | 参数无效 | SPRD-001 |
| ETIMEDOUT | 超时 | MTK-001 |
