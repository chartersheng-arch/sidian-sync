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
