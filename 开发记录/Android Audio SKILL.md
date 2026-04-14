# Android Audio SKILL - 系统化问题诊断方案

> **架构**: SKILL主导 + MCP辅助
> **版本**: 2.0
> **更新**: 2026-04-13

---

## 一、整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                   android-audio-debugging (SKILL)            │
│  负责：推理流程 / 证据管理 / 多轮根因推导 / 报告生成           │
├─────────────────────────────────────────────────────────────┤
│                      Phase 0: 信息收集                       │
│  确认：问题现象 / 平台信息 / 日志 / 对比log                  │
├─────────────────────────────────────────────────────────────┤
│                      Phase 1: 自动分析                       │
│  MCP: audio_log_parser / code_locator / case_matcher        │
├─────────────────────────────────────────────────────────────┤
│                      Phase 2: 疑点验证                       │
│  MCP: device_collector / 源码分析 / 用户确认                 │
├─────────────────────────────────────────────────────────────┤
│                      Phase 3: 多轮推理                       │
│  直接错误 / 时序分析 / 对比分析 / 环境因素                    │
├─────────────────────────────────────────────────────────────┤
│                      Phase 4: 报告输出                       │
│  MCP: report_builder → Markdown报告                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server (辅助层)                        │
│  audio_log_parser / code_locator / device_collector         │
│  case_matcher / report_builder                             │
│  路径: C:\Users\nijiasheng1\.claude\skills\                 │
│        android-audio-debugging\mcp_server\                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、SKILL入口

**触发词**：用户描述音频问题现象、提供日志、提出疑点

**核心职责**：
1. 收集问题信息（现象、log、平台、源码、正常log、历史案例）
2. 调用MCP工具完成自动分析
3. 生成疑点并要求证据
4. 多轮根因推理
5. 调用MCP报告生成工具输出最终报告

---

## 三、诊断流程

### 阶段0：信息收集

**必填信息**：
- 问题现象（无声/杂音/延迟/爆音/断续）
- 设备型号 + Android版本 + 平台（高通/MTK/展锐）

**问题日志**（粘贴或文件）

**可选但强烈建议**：
- 正常场景日志（对比分析）
- 相关源码路径
- 历史案例
- 问题切入点/疑点
- 对比机log（对比正常设备分析差异）

**客制化确认**（主动询问）：
- 是否有平台/供应商客制化？（高通/MTK/展锐/厂商）
- 问题是否与特定供应商模块相关？（DSP/编解码器/外设）
- 是否有自定义AudioPolicy配置？

**分析层面偏向**（根据问题类型）：

| 问题类型 | 优先分析层面 | 原因 |
|----------|-------------|------|
| 无声/无声 | AudioPolicy路由 + HAL设备路径 | 路由是最常见根因 |
| 杂音/破音 | HAL配置 + DMA buffer + Clock | 硬件/配置问题 |
| 延迟 | AudioFlinger buffer + FastMixer | 调度/buffer问题 |
| 断续/卡顿 | CPU调度 + Buffer配置 | 系统层面问题 |
| 通话问题 | VoIP/SCO路由 + AEC/NR | 特定场景问题 |

用户可指定分析偏向，如：`"主要分析HAL层"` 或 `"重点看AudioPolicy路由"`

---

### 阶段1：自动分析

**无用户源码时**：
1. 使用通用Android AOSP代码路径进行分析
2. 提醒用户客制化可能性，建议提供vendor目录下的HAL实现
3. 对比机分析（当用户提供对比log时）

**调用MCP工具**：

**调用MCP工具**：

| MCP工具              | 功能     | 输入         |
| ------------------ | ------ | ---------- |
| `audio_log_parser` | 日志分层解析 | 原始日志       |
| `code_locator`     | 源码文件定位 | 组件名/错误关键字  |
| `device_collector` | ADB取证  | adb命令      |
| `case_matcher`     | 历史案例匹配 | 错误码/模块/关键词 |

**手动降级**：无MCP时，按以下层级分类日志

| 层级 | 关键Tag | 常见错误 |
|------|---------|----------|
| App | AudioTrack/AudioRecord | init failed, buffer empty |
| AudioPolicy | AudioPolicyService | routing, setParameter |
| AudioFlinger | PlaybackThread/RecordThread | underrun, standby, no tracks |
| HAL | audio_hw, HAL | -ENODEV, -EINVAL, write error |
| Kernel | ASoC, DMA, snd_ | xrun, transfer failed, clock |

---

### 阶段2：疑点生成与验证

**疑点结构**：

```
疑点[N]: <描述>
  验证方法: <具体命令/检查点>
  证据要求: <需要什么证据>
  状态: [confirmed / rejected / pending]
```

**验证方式**：

| 验证方式 | 适用场景 | 调用 |
|----------|----------|------|
| MCP自动执行 | adb命令/dumpsys | device_collector |
| 源码分析 | 代码路径检查 | code_locator |
| 用户确认 | 客制化逻辑/硬件 | 向用户提问 |

---

### 阶段3：多轮根因推理

**必须执行至少四轮独立推理**：

#### 第一轮：直接错误分析
- 显式错误码（-ENODEV, -EINVAL, pcm_write error -11）
- HAL返回值含义
- 常见错误路径

#### 第二轮：时序与状态变化
- 问题发生前2秒内关键事件
- 设备连接/断开、路由切换、音量调节、suspend/resume
- 事件A → 问题B 的因果关系

#### 第三轮：对比分析（需正常log）
- 相同操作步骤下的差异点
- 异常log中缺少的关键步骤

#### 第四轮：环境与并发因素
- 电源管理（suspend/resume）
- 多应用并发
- DSP加载/卸载
- 热插拔中断竞争

**假设输出格式**：

| 假设 | 置信度 | 支持证据 | 缺失证据 |
|------|--------|----------|----------|
| 假设A | 高 | 日志显示device=NULL | 无 |
| 假设B | 中 | underrun次数>10 | 需对比正常值 |

**证据标准**：

| 等级 | 证据类型 | 可信度 |
|------|----------|--------|
| A级 | 直接日志证据 | ✅ 可靠 |
| B级 | 源码逻辑推导 | ✅ 可靠 |
| C级 | 平台文档支持 | ✅ 可靠 |
| D级 | 推测/猜测 | ❌ 需排除 |

---

### 阶段4：结论与报告

**调用 `report_builder` 生成Markdown报告**：

```markdown
# Android Audio 问题诊断报告

## 基本信息
- 问题类型: <无声/杂音/延迟/爆音/断续>
- 设备: <型号>
- 平台: <Android版本> / <平台>

## 问题现象
<客观描述>

## 分析过程
### 证据链
### 疑点验证
### 多轮推理

## 根因结论

### 直接原因
### 根因分析

**⚠️ 客制化代码修改建议规则**

```
修改建议前提条件:
1. 必须获取到实际的客制化源码
2. 必须完整分析代码逻辑和调用路径
3. 必须确认问题与客制化代码的直接关联

禁止直接给出修改建议的情况:
- ❌ 未获取到实际vendor代码时
- ❌ 仅基于通用AOSP代码分析时
- ❌ 不确定问题是否与客制化相关时

正确做法:
- ✅ 先确认是否存在客制化（询问用户）
- ✅ 基于对比机/对比日志推断可能位置
- ✅ 建议用户提供相关vendor源码进一步分析
- ✅ 给出通用代码的标准修改方向作为参考

示例:
[推测] 根据对比log分析，问题可能在MTK的AudioALSAStreamOut.cpp中
[建议] 请提供 vendor/mediatek/.../AudioALSAStreamOut.cpp 以进一步确认
```

## 修复建议
### 优先级方案

## 验证计划
```

---

## 四、MCP工具详解

### 4.1 audio_log_parser

```json
{
  "log_text": "原始日志文本",
  "platform": "qcom|mtk|sprd|auto",
  "time_range": {"start": "", "end": ""}
}

// 返回
{
  "layers": {
    "kernel_driver": [...],
    "audio_hal": [...],
    "audio_flinger": [...],
    "audio_policy": [...],
    "app": [...]
  },
  "errors": [{"count": 0, "message": "", "layer": ""}],
  "state_changes": [{"from": "", "to": "", "component": ""}],
  "timeline": []
}
```

**日志分层规则**：
- Kernel: ASoc, DMA, snd_soc, /dev/snd/
- HAL: audio_hw, out_write, in_read, HAL:
- AudioFlinger: PlaybackThread, MixerThread, AudioTrack
- AudioPolicy: setOutputDevice, routing, getDeviceForStrategy
- App: android.media, AudioTrack, pid=xxx

---

### 4.2 code_locator

```json
{
  "android_version": "14",
  "platform": "qcom",
  "component": "AudioPolicyManager::getDeviceForStrategy",
  "error_keyword": "pcm_write returned -11"
}

// 返回
{
  "files": [
    {"path": "frameworks/av/services/audiopolicy/enginedefault/src/EngineDefault.cpp", "lines": [1150, 1180]}
  ],
  "call_chain": [
    "AudioTrack::start() → AudioFlinger::PlaybackThread::start() → AudioStreamOut::standby()"
  ],
  "customization_points": [
    {"path": "device/qcom/common/audio/audio_policy_configuration.xml", "description": "设备路由策略配置"}
  ]
}
```

**组件映射**：

| 组件 | 高通路径 | MTK路径 | 展锐路径 |
|------|----------|----------|----------|
| out_write | hardware/qcom/audio/hal/audio_hw.c | vendor/mediatek/.../AudioALSAStreamOut.cpp | vendor/sprd/.../sprd_audio_hw.c |
| AudioFlinger | frameworks/av/services/audioflinger/ | 同左 | 同左 |
| AudioPolicy | frameworks/av/services/audiopolicy/managerdefault/ | 同左 | 同左 |

---

### 4.3 device_collector

```json
{
  "device_serial": "optional",
  "commands": ["dumpsys media.audio_policy", "cat /proc/asound/cards"]
}

// 预定义bundle
{
  "bundle": "audio_full"  // dumpsys audioflinger + audio_policy + ALSA status
}
```

**预定义Diagnostic Bundle**：

| Bundle | 包含命令 |
|--------|----------|
| audio_full | dumpsys audioflinger + dumpsys media.audio_policy + ALSA status |
| audio_playback | PlaybackThread状态 + PCM status |
| audio_capture | RecordThread状态 + PCM capture status |
| kernel_audio | dmesg audio + ASOC + DMA |
| audio_properties | getprop audio相关 |

---

### 4.4 case_matcher

```json
{
  "features": {
    "error_code": "-22",
    "module": "AudioFlinger",
    "platform": "qcom",
    "keywords": ["standby", "no sound"]
  }
}

// 返回
{
  "matches": [
    {
      "title": "高通平台空路由导致AudioStreamOut永久standby",
      "similarity": 0.92,
      "root_cause": "AudioPolicyManager::getDeviceForStrategy返回空设备",
      "solution": "增加fallback到DEVICE_OUT_SPEAKER"
    }
  ]
}
```

**匹配权重**：
- 平台匹配：30%
- 模块匹配：20%
- 错误码匹配：25%
- 关键词匹配：25%

---

### 4.5 report_builder

```json
{
  "title": "Android Audio 问题诊断报告",
  "device_info": "Xiaomi 12, Android 13, QCOM SM8450",
  "phenomenon": "播放音乐10秒后声音消失",
  "problem_type": "无声",
  "evidence_chain": [...],
  "hypothesis_table": [...],
  "root_cause": "路由策略返回空设备",
  "fix_suggestions": [
    {"priority": "P0", "solution": "增加fallback逻辑", "scope": "AudioPolicy", "risk": "低"}
  ],
  "verification_plan": [...]
}
```

---

## 五、部署方式

### 5.1 安装MCP Server

```bash
cd C:\Users\nijiasheng1\.claude\skills\android-audio-debugging\mcp_server
pip install -r requirements.txt
```

### 5.2 Claude Desktop配置

在 `claude_desktop_config.json` 添加：

```json
{
  "mcpServers": {
    "android-audio": {
      "command": "python",
      "args": ["C:/Users/nijiasheng1/.claude/skills/android-audio-debugging/mcp_server/mcp_audio_server.py"]
    }
  }
}
```

### 5.3 手动测试

```bash
cd C:\Users\nijiasheng1\.claude\skills\android-audio-debugging\mcp_server
python mcp_audio_server.py
# 输出demo模式验证各模块功能
```

---

## 六、典型对话示例

**用户**：播放音乐10秒后声音消失，log如下，平台高通SM8450，Android 13，怀疑HAL standby问题。

**Claude（按照SKILL执行）**：

### Phase 1: 调用MCP `audio_log_parser` 分析日志
```
→ 发现 AudioFlinger::Thread standby后无start
→ audio_policy中 output_device=NULL
```

### Phase 2: 调用MCP `code_locator` 查找源码
```
→ getDeviceForStrategy 在 Android 13 高通: enginedefault.cpp:1150
```

### Phase 3: 调用MCP `case_matcher` 匹配案例
```
→ 匹配度0.92: "高通平台空路由导致AudioStreamOut永久standby"
```

### Phase 4: 生成疑点

**疑点1**: 路由策略返回空设备
```
验证方法: dumpsys media.audio_policy
证据: output device = NULL
状态: [confirmed]
```

**疑点2**: HAL standby后底层PCM未重新prepare
```
验证方法: cat /proc/asound/card0/pcm0p/sub0/status
证据: state: SUSPENDED（但预期应为RUNNING）
状态: [rejected] - 时间线上 PCM prepare 先于 standby
```

### Phase 5: 多轮推理

**第一轮（直接错误）**：-ENODEV出现在setOutputDevice后，设备引用为空
**第二轮（时序）**：10秒时耳机拔出事件触发路由重算
**第三轮（对比）**：正常log中耳机拔出会触发fallback到speaker
**第四轮（环境）**：无额外并发因素

### Phase 6: 调用MCP `report_builder` 生成报告

---

## 七、知识库文件

| 文件 | 路径 |
|------|------|
| SKILL.md | `C:\Users\nijiasheng1\.claude\skills\android-audio-debugging\SKILL.md` |
| framework-layers.md | `references/framework-layers.md` |
| hal-interface.md | `references/hal-interface.md` |
| failure-patterns.md | `references/failure-patterns.md` |
| log-analysis.md | `references/log-analysis.md` |
| case-library.md | `references/case-library.md` |
| MCP Server | `mcp_server/` |

---

## 八、扩展建议

- **案例持续积累**：将每次确认的根因加入 case_matcher 数据库
- **自动化测试集成**：修复后调用 device_collector 自动运行测试用例
- **多设备并发**：MCP Server支持同时连接多个设备

---

_文档更新：2026-04-13_
_配套SKILL：android-audio-debugging v2.0_
