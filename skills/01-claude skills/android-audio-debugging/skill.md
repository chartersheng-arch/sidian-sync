---
name: android-audio-debugging
description: "Android Audio系统化问题分析技能。当用户报告音频故障（无声、杂音、延迟、爆音）、描述音频场景问题、提供audio相关log/trace/源码时激活。整合四阶段调试方法论+多轮根因推理+MCP自动化工具，输出带凭证的分析报告。必须使用此技能分析任何Android audio相关问题。"
version: "2.0"
author: audio-engineer
tags:
  - android
  - audio
  - debugging
  - hal
  - audioflinger
department: embedded
---

# Android Audio Debugging Skill

> **架构**: SKILL主导 + MCP辅助
> - SKILL负责：推理流程、证据管理、多轮根因推导、报告生成
> - MCP负责：日志解析、源码定位、设备取证、案例匹配

---

## 触发条件

当用户提供以下任何信息时，**必须激活此技能**：
- 音频问题现象描述（无声/杂音/延迟/爆音/断续）
- audio相关log（logcat、dmesg、audio_dump）
- Audio HAL或Framework源码
- 问题切入点或关键疑点
- 平台资料或历史案例
- 对比正常log
- **"开始归纳BUGrecord"** → 执行反馈归纳流程

---

## 核心方法论

### ⚠️ 铁律：未经完整调查，禁止给出修复结论

```
阶段0: 信息收集 → 阶段1: 自动分析 → 阶段2: 疑点验证 → 阶段3: 多轮推理 → 阶段4: 报告输出
```

---

## 阶段0：信息收集

### 0.1 必填信息

向用户确认以下内容（如未提供则主动询问）：

| 信息 | 必填 | 说明 |
|------|------|------|
| 问题现象 | ✅ | 客观描述（无声/杂音/延迟/爆音/卡顿） |
| 设备型号 | ✅ | 如 Xiaomi 12, Samsung S24 |
| Android版本 | ✅ | 如 Android 13, Android 14 |
| 平台 | ✅ | 高通(Qualcomm)/MTK/展锐(Spreadtrum)/其他 |
| 问题日志 | ✅ | logcat/dmesg/trace，可粘贴或文件 |

### 0.2 可选但强烈建议

| 信息 | 作用 |
|------|------|
| 正常场景日志 | 对比分析，找出差异点 |
| 相关源码路径 | 定位用户修改的关键代码 |
| 历史案例 | 匹配已知问题加速定位 |
| 问题切入点 | 用户已怀疑的方向 |
| **对比机log** | 对比正常设备分析差异 |
| **项目代码** | 判断问题是bug还是代码逻辑设计如此 |

### 0.2.1 "设计如此"的判断

**⚠️ 重要**：有些现象并非bug，而是代码逻辑设计如此。判断方式：

```
当用户提供项目代码时，分析步骤：
1. 提取问题相关的代码路径
2. 对比代码逻辑：
   - 如果行为与代码逻辑一致 → 可能是"设计如此"
   - 如果行为与代码逻辑矛盾 → 确认是bug
3. 向用户确认：
   - "此行为与代码实现一致，是预期的吗？"
   - "请确认这是bug还是设计需求？"
```

**按问题层级提醒用户提供对应代码**：

| 问题类型 | 建议提供的代码层 |
|----------|-----------------|
| 路由/策略问题 | AudioPolicyManager / AudioPolicyConfiguration |
| HAL行为问题 | audio_hw.cpp / stream_out/stream_in |
| 通话/SCO问题 | VoiceInterface / BT Sco相关 |
| Buffer/延迟问题 | AudioFlinger / MixerThread |
| 电源管理问题 | AudioPowerManager / suspend/resume |

**需提供项目代码的场景**：
- 用户报告的现象与AOSP标准实现不符
- 涉及平台客制化代码
- 行为与用户预期的产品需求不符

### 0.3 客制化提醒

**当用户提供问题时，主动询问：**

```
【客制化确认】
- 是否有平台/供应商客制化？（高通/MTK/展锐/厂商）
- 问题是否与特定供应商模块相关？（DSP/编解码器/外设）
- 是否有自定义AudioPolicy配置？
```

### 0.4 分析层面偏向

**根据问题类型，建议用户偏向的分析层面：**

| 问题类型 | 优先分析层面 | 原因 |
|----------|-------------|------|
| 无声/无声 | AudioPolicy路由 + HAL设备路径 | 路由是最常见根因 |
| 杂音/破音 | HAL配置 + DMA buffer + Clock | 硬件/配置问题 |
| 延迟 | AudioFlinger buffer + FastMixer | 调度/buffer问题 |
| 断续/卡顿 | CPU调度 + Buffer配置 | 系统层面问题 |
| 通话问题 | VoIP/SCO路由 + AEC/NR | 特定场景问题 |

**用户可指定分析偏向**，如：`"主要分析HAL层"` 或 `"重点看AudioPolicy路由"`

### 0.5 多份Log综合分析

**当用户提供多份log时：**

```
多log分析策略:
1. 时间轴对齐
   - 以问题发生时刻为基准(T=0)
   - 将各log按时间戳对齐
   - 标记问题发生前/后的关键节点

2. 交叉验证
   - 不同log来源的同一事件是否一致
   - 验证异常是否在各log中同时出现
   - 排除无关log的干扰信息

3. 证据链构建
   - App层log: 确认问题现象
   - AudioFlinger log: 确认处理状态
   - HAL/Kernel log: 确认硬件层响应
   - 完整证据链必须有层级间的因果对应

4. 矛盾点标注
   - 当不同log出现矛盾时
   - 标注"[log来源A]" vs "[log来源B]"
   - 说明可能原因（时序/缓存/过滤）
```

**多log类型说明：**

| Log类型 | 格式 | 关键信息 |
|---------|------|----------|
| logcat | 文本 | App/Framework层状态 |
| dmesg | 文本 | Kernel层事件 |
| bugreport | tar.gz | 全量系统快照 |
| perfetto | trace | 时序/性能分析 |
| audio_dump | 二进制 | PCM数据（需专用工具） |

### 0.6 多份Log专项提取命令

**当用户提供多份log或需要主动提取log时，使用以下命令模板：**

#### 0.6.1 bugreport 提取

```bash
# 获取完整bugreport（推荐，问题初期必提）
adb bugreport <output>.zip

# 或获取纯文本版本（体积小，但信息不全）
adb bugreport -z <output>.zip

# 解压bugreport获取主文本文件
unzip -o <output>.zip bugreport-*.txt

# 从bugreport中提取audio相关段落
grep -E "audio|Audio|AF_|AudioFlinger|audio_hw|ALS|AudioPolicy" bugreport-*.txt > audio_section.txt

# 提取dumpsys media.audio_policy段落
grep -A 100 "DUMP OF SERVICE media.audio_policy" bugreport-*.txt > audio_policy_dump.txt
```

**bugreport内部关键文件：**

| 文件 | 包含内容 |
|------|----------|
| `bugreport-*.txt` | 主文本报告，包含所有dumpsys |
| `FS/data/log/` | 系统日志片段 |
| `PROcrash/` | 崩溃日志 |
| `MAIN_SYSTEM/` | 系统服务dump |

#### 0.6.2 kernel log (dmesg) 提取

```bash
# 提取完整dmesg（带可读时间戳）
adb shell dmesg -T > kernel_log_full.txt

# 提取最近N行dmesg
adb shell dmesg -T | tail -n 500 > kernel_log_recent.txt

# 提取特定时间段dmesg（需配合时间过滤）
adb shell "dmesg -T | grep '2024-01-15 14:'" > kernel_log_时段.txt

# 提取audio driver相关dmesg
adb shell dmesg -T | grep -E "ASoC|snd_|DMA|Audio|HAL" > kernel_audio.txt

# 提取ALSA PCM状态
adb shell "cat /proc/asound/card0/pcm0p/sub0/status" > pcm_status.txt
adb shell "cat /proc/asound/card0/pcm0p/sub0/hw_params" > pcm_hw_params.txt
```

#### 0.6.3 logcat 提取

```bash
# 提取audio相关logcat（过滤后）
adb logcat -d -v threadtime | grep -E "Audio|AudioTrack|AudioFlinger|AudioPolicy|HAL" > logcat_audio.txt

# 提取特定时间段logcat（需先重现问题）
adb logcat -d -v threadtime -t 10000 > logcat_recent.txt

# 提取缓冲区外的log（重启后立即执行）
adb logcat -b main -b system -b crash -d > logcat_buffers.txt

# 提取带格式的完整logcat
adb logcat -d -v long | head -n 5000 > logcat_full_5000.txt
```

#### 0.6.4 多log时间轴对齐脚本

```python
# 时间轴对齐辅助脚本（用于综合分析）
# 将不同来源log按时间戳统一对齐

import re
from datetime import datetime

def extract_timestamps(log_line, log_type):
    """提取各类型log的时间戳"""
    patterns = {
        'logcat': r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})',
        'dmesg': r'(\[?\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})',
        'bugreport': r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})',
    }
    match = re.search(patterns.get(log_type, ''), log_line)
    return match.group(1) if match else None

def align_logs(logs_by_source, reference_time):
    """
    logs_by_source: {source: [(timestamp, line), ...]}
    reference_time: 基准时间（问题发生时刻）
    返回: 按相对时间排序的合并列表
    """
    aligned = []
    for source, entries in logs_by_source.items():
        for ts, line in entries:
            if ts:
                delta = ts - reference_time
                aligned.append((delta, source, line))
    return sorted(aligned, key=lambda x: x[0])
```

#### 0.6.5 快速提取模板（紧急场景）

**当用户无法完整提取时，按优先级执行：**

```
P0 - 最小集（必须）:
  1. adb shell dmesg -T > kernel.txt
  2. adb logcat -d -v threadtime | grep -E "Audio|audio" > audio_logcat.txt

P1 - 标准集（推荐）:
  3. adb bugreport -z bugreport.zip
  4. adb shell dumpsys media.audio_policy > audio_policy.txt
  5. adb shell "cat /proc/asound/card*/pcm*/sub*/status" > pcm_status.txt

P2 - 完整集（深度分析）:
  6. adb shell "cat /sys/kernel/debug/asoc/*" > asoc_debug.txt
  7. adb shell "cat /proc/asound/cards" > sound_cards.txt
  8. 提取 perfetto trace（如涉及调度问题）
```

#### 0.6.6 展锐(Spreadtrum) ylog ap log解析

**平台**: 展锐 (Spreadtrum/Sprd)

**ylog目录结构**:
```
\Audiologs\ylog\ap\
├── 000-0209_172537--0209_172929.ylog    # 原始ylog二进制文件
└── analyzer.py                            # 解析脚本（通常在ylog目录下）
```

**解析方法**:
```bash
# 1. 进入ylog目录（确保analyzer.py在同一目录）
cd "xxx\Audiologs\ylog\ap"

# 2. 执行解析脚本
python.exe .\analyzer.py

# 3. 解析完成后，会生成对应的时间戳目录
#    例如: 000-0209_172537--0209_172929\
#    目录内包含多种类型的日志文件
```

**解析产物示例**:
```
000-0209_172537--0209_172929\
├── audio_log.txt       # Audio相关日志
├── kernel_log.txt      # 内核日志
├── system_log.txt      # 系统日志
└── ...                 # 其他类型日志
```

**适用场景**: 当用户提供展锐平台的ylog文件时使用此方法解析ap log

#### 0.6.7 284log 多层解压

**平台**: ALL

**bugreport结构**: 展锐平台的bugreport通常采用多层压缩格式，需要多次解压才能获取最终文本log。

**解压步骤**:

```bash
# 第一层解压：获取外层目录
unzip "bugreport-2026-02-09-173041.zip"
# 结果: bugreport-2026-02-09-173041\

# 第二层解压：进入目录，找到下一层zip并解压
cd bugreport-2026-02-09-173041
unzip "bugreport-REDMI 17 5G-2026-02-09-173257.zip"
# 结果: bugreport-somalia-BP2A.250605.031.A3-2026-02-09-17-30-41.txt
```

**完整目录结构示例**:
```
D:\BUG\xxx\
└── bugreport-2026-02-09-173041.zip           # 第一层压缩包
    └── bugreport-2026-02-09-173041\          # 第一层解压结果
        └── bugreport-REDMI 17 5G-2026-02-09-173257.zip   # 第二层压缩包
            └── bugreport-somalia-BP2A.250605.031.A3-2026-02-09-17-30-41.txt  # 最终文本log
```

**解压后操作**:
```bash
# 提取audio相关段落（以展锐平台实际关键词为准）
grep -E "audio|Audio|AudioFlinger|audio_hw|ALSA" "bugreport-somalia-BP2A.250605.031.A3-2026-02-09-17-30-41.txt" > audio_section.txt
```

**适用场景**: 当用户提供展锐平台的bugreport-*.zip文件时使用此方法解压

### 0.7 信息提取模板

```
【问题提取】
现象: <客观描述>
平台: <设备> / <Android版本> / <平台>
日志范围: <时间戳或行数>
关键错误: <提取的关键日志>
疑点: <用户提供或"待分析">
```

---

## 阶段1：自动分析

### 1.1 调用MCP工具

**优先使用MCP进行自动分析（如果MCP可用）：**

```
可用MCP工具（按需调用）:

1. audio_log_parser     → 日志分层解析、错误聚合、时间线
2. code_locator         → 源码文件定位、调用链映射
3. device_collector     → adb命令执行、dumpsys获取
4. case_matcher        → 历史案例匹配
5. context7             → Android官方文档查询
```

### 1.2 无用户提供源码时的处理

**当用户未提供源码时：**

```
分析策略:
1. 使用通用Android AOSP代码路径进行分析
   - 基于用户提供的Android大版本（13/14/15）
   - 使用code_locator内置映射表定位标准代码

2. 提醒用户客制化可能性
   - "此问题可能在平台/供应商客制化中有不同实现"
   - "建议提供vendor目录下的HAL实现"

3. 对比机分析（当用户提供对比log时）
   - 正常设备 vs 异常设备的日志差异
   - 找出差异点对应的代码路径
```

### 1.2 日志分层解析

**无MCP时，手动按以下层级分类日志：**

| 层级 | 关键Tag | 常见错误关键字 |
|------|---------|----------------|
| App | `AudioTrack`, `AudioRecord` | `init failed`, `buffer is empty` |
| AudioPolicy | `AudioPolicyService` | `setParameter`, `routing` |
| AudioFlinger | `AudioFlinger` | `underrun`, `no tracks`, `standby` |
| HAL | `audio_hw`, `HAL` | `-ENODEV`, `-EINVAL`, `write error` |
| Kernel | `ASoC`, `DMA`, `snd_` | `xrun`, `transfer failed`, `clock` |

### 1.3 错误聚合

**识别并统计关键错误：**

```
错误模式识别:
├── 错误码类: -ENODEV, -EINVAL, -11(EAGAIN), -12(ENOMEM)
├── 状态异常类: standby without start, no tracks active
├── 时序类: underrun, gap, xrun, dropped
└── 资源类: clock disabled, DMA not ready, memory alloc failed
```

### 1.4 案例匹配

**调用case_matcher或手动检索历史案例：**

```
匹配特征:
- error_code: <主要错误码>
- module: <AudioFlinger/HAL/Kernel>
- platform: <qcom/mtk/sprd>
- keywords: <无声/杂音/延迟等>
- android_version: <版本>
```

---

## 阶段2：疑点生成与验证

### 2.1 疑点结构

**每个疑点必须包含：**

```markdown
疑点[N]: <描述>
  验证方法: <可执行的具体命令/检查点>
  证据要求: <需要什么证据>
  状态: [confirmed / rejected / pending]
```

### 2.2 疑点验证方式

| 验证方式 | 适用场景 | 调用 |
|----------|----------|------|
| MCP自动执行 | adb命令/dumpsys | `device_collector` |
| 源码分析 | 代码路径检查 | `code_locator` / 手动阅读 |
| 用户确认 | 客制化逻辑/硬件状态 | 向用户提问 |

### 2.3 疑点示例

```
疑点1: 路由策略返回空设备导致AudioStreamOut永久standby
  验证方法: adb shell dumpsys media.audio_policy | grep output
  证据: output device = NULL (预期应为 speaker/headphone)
  状态: [confirmed]

疑点2: HAL standby后底层PCM未重新prepare
  验证方法: cat /proc/asound/card0/pcm0p/sub0/status
  证据: state: SUSPENDED (预期应为 RUNNING)
  状态: [rejected] - 时间线上 PCM prepare 先于 standby
```

---

## 阶段3：多轮根因推理

### ⚡ 必须执行至少三轮独立推理

#### 第一轮：直接错误分析

```
检查内容:
├── 日志中的显式错误码 (-ENODEV, -EINVAL, pcm_write error -11)
├── HAL返回值的含义
└── 是否是常见错误路径

输出: <直接原因描述> + 置信度 [高/中/低]
```

#### 第二轮：时序与状态变化

```
检查内容:
├── 问题发生前2秒内的关键事件
│   ├── 设备连接/断开
│   ├── 路由切换
│   ├── 音量调节
│   └── suspend/resume
├── 事件A → 问题B 的因果关系
└── 状态机转换是否异常

输出: <时序相关原因> + 置信度 [高/中/低]
```

#### 第三轮：对比分析

```
检查内容（当用户提供正常log时）:
├── 相同操作步骤下的差异点
├── 异常log中缺少的关键步骤
└── 正常log中有但异常log中没有的步骤

输出: <差异点相关原因> + 置信度 [高/中/低]
```

#### 第四轮：环境与并发因素

```
检查内容:
├── 电源管理 (suspend/resume时序)
├── 多应用并发 (多个AudioTrack竞争)
├── DSP加载/卸载
├── 热插拔中断竞争
└── AudioFlinger线程状态 / AudioPolicy死锁

输出: <环境相关原因> + 置信度 [高/中/低]
```

### 3.1 假设输出格式

```markdown
## 根因假设

| 假设 | 置信度 | 支持证据 | 缺失证据 |
|------|--------|----------|----------|
| 假设A: 路由空设备 | 高 | 日志显示device=NULL | 无 |
| 假设B: DMA buffer不足 | 中 | underrun次数>10 | 需对比正常值 |
| 假设C: CPU降频 | 低 | 无直接证据 | 需获取cpuinfo |
```

### 3.2 证据标准

| 等级 | 证据类型 | 可信度 |
|------|----------|--------|
| A级 | 直接日志证据 | ✅ 可靠 |
| B级 | 源码逻辑推导 | ✅ 可靠 |
| C级 | 平台文档支持 | ✅ 可靠 |
| D级 | 推测/猜测 | ❌ 需排除 |

---

## 阶段4：结论与报告

### 4.0 客制化代码修改建议规则

**⚠️ 重要：平台/供应商客制化代码的特殊处理**

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

### 4.1 首选根因

```
选择置信度最高的假设作为首选根因
如果存在多个可能性，列出次要根因及验证建议
```

### 4.2 报告结构

```markdown
# Android Audio 问题诊断报告

## 基本信息
- **问题类型**: <无声/杂音/延迟/爆音/断续>
- **设备**: <型号>
- **平台**: <Android版本> / <平台>
- **影响范围**: <哪些场景>
- **复现率**: <必现/偶发/条件触发>

## 问题现象
<客观描述>

## 分析过程

### 证据链
[按时间顺序排列关键证据，标注来源]

### 疑点验证
| 疑点 | 验证方法 | 证据 | 结论 |
|------|----------|------|------|
| ... | ... | ... | confirmed/rejected |

### 多轮推理
**第一轮（直接错误）**: ...
**第二轮（时序）**: ...
**第三轮（对比）**: ...
**第四轮（环境）**: ...

### 根因假设
| 假设 | 置信度 | 证据 |
|------|--------|------|
| 首选: ... | 高 | ... |
| 次要: ... | 中 | ... |

## 根因结论

### 直接原因
<一句话说明>

### 根因分析
<为什么会发生，传播路径>

## 修复建议

| 优先级 | 方案 | 改动范围 | 风险 |
|--------|------|----------|------|
| P0 | <紧急规避> | ... | ... |
| P1 | <常规根本> | ... | ... |

## 验证计划
- [ ] 验证方法
- [ ] 预期结果
- [ ] 判断标准

## 附件
- 关键日志片段
- 相关代码引用
```

### 4.3 证据引用格式

```markdown
证据引用必须标注:
[Log 1] audio_track.cpp:123 - "start() called"
[Log 2] audioflinger.cpp:456 - "track 0x1234 started"
[Src ] enginedefault.cpp:1150 - "getDeviceForStrategy() returns NULL"
```

### 4.4 不确定项标注

```markdown
[待验证] - 需要用户确认或补充证据
[推测] - 缺乏直接证据，谨慎确认
```

---

## MCP工具接口（待实现）

### audio_log_parser

```json
{
  "log_text": "原始日志文本",
  "platform": "qcom|mtk|sprd|auto",
  "time_range": {"start": "optional", "end": "optional"}
}

// 返回
{
  "layers": {
    "kernel_driver": [{"timestamp": "", "message": "", "line_no": 0}],
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

### code_locator

```json
{
  "android_version": "14",
  "platform": "qcom",
  "component": "AudioPolicyManager::getDeviceForStrategy",
  "error_keyword": "pcm_write returned -11"
}

// 返回
{
  "files": [{"path": "", "lines": [], "function": ""}],
  "call_chain": [],
  "customization_points": []
}
```

### device_collector

```json
{
  "device_serial": "optional",
  "commands": [
    "dumpsys media.audio_policy",
    "cat /proc/asound/card0/pcm0p/sub0/status",
    "getprop ro.build.version.sdk"
  ]
}

// 返回
{
  "results": {"command": "output", ...},
  "errors": []
}
```

### case_matcher

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
  "matches": [{
    "title": "",
    "similarity": 0.92,
    "root_cause": "",
    "solution": ""
  }]
}
```

---

## MCP协同

| MCP | 用途 | 调用方式 |
|-----|------|----------|
| `context7` | Android官方文档查证 | `npx ctx7@latest library "Android Audio HAL"` |
| `perfetto-audio` | Perfetto trace分析 | 当用户提供trace时 |
| `obsidian-charter` | 案例保存到知识库 | 分析完成后可选 |

### context7使用场景

```bash
# 查询Audio HAL接口
npx ctx7@latest library "Android Audio HAL"

# 查询AudioFlinger实现
npx ctx7@latest library "Android AudioFlinger"

# 查询AudioPolicy
npx ctx7@latest library "Android Audio Policy"
```

---

## 质量检查清单

在输出最终报告前，自检：

- [ ] 问题类型已分类（无声/杂音/延迟/爆音/断续）
- [ ] 证据链完整且有序（时间/因果）
- [ ] 每个疑点有证据确认（confirmed/rejected）
- [ ] 执行了至少3轮独立推理
- [ ] 根因有A级或B级证据支持
- [ ] 推测已标注或排除
- [ ] 建议方案有优先级（P0/P1）
- [ ] 验证计划可执行
- [ ] **已排除"设计如此"的可能性**：当用户提供项目代码时，需对比代码逻辑确认问题确实与设计不符

---

## 自动记录机制

### 触发条件

**当满足以下条件时，自动将分析过程追加到 `BUGrecord.md`**：

1. ✅ 已分析出至少一个根因（置信度中/高）
2. ❌ 用户没有采纳/纠正第一个根因，包括：
   - 用户明确说"继续分析其他方向"
   - 用户说"根因不对"、"不是这个"
   - 用户追问但未确认根因正确
   - 分析轮次 ≥ 3 轮但未收敛
3. ❗ **排除"设计如此"**：如果最终确认问题是代码逻辑设计如此（而非bug），则不记录

**不触发记录的情况**：
- 最终结论为"设计如此"，用户确认接受该行为
- 问题已被用户明确判定为非bug

### 记录格式

每个问题单独一个 section，用 `---` 分隔，**必须包含时间戳**：

```markdown
---
## [问题N] <分析标题>
**记录时间**: <YYYY-MM-DD HH:MM>

**现象**: <用户报告的问题现象摘要>

### 初始分析方向
**方向**: <最初认为的问题方向>
**假设**: <基于这个方向的假设>
**证据**: <提取的关键日志/代码>

### 偏离轨迹
**偏离点**: <从哪个判断点开始走偏>
**触发纠正的契机**: <用户追问/补充了什么信息>
**偏离根因**: <分类>
- [ ] <根因分类选项>

### 根因结论
**最终确认的分析方向**: <正确的方向>
**根因**: <最终确定的根因>
**置信度**: <高/中/低>
```

### 自动追加逻辑

使用 Bash 工具追加到 `BUGrecord.md`：

```bash
cat >> "C:/Users/nijiasheng1/.claude/skills/android-audio-debugging/BUGrecord.md" << 'EOF'

---
## [问题N] <分析标题>
**记录时间**: <YYYY-MM-DD HH:MM>

**现象**: <现象>

### 初始分析方向
**方向**: <方向>
**假设**: <假设>
**证据**: <证据>

### 偏离轨迹
**偏离点**: <偏离点>
**触发纠正的契机**: <契机>
**偏离根因**: <根因分类>

### 根因结论
**最终确认的分析方向**: <方向>
**根因**: <根因>
**置信度**: <置信度>
EOF
```

### 触发时机

在以下情况时执行自动记录：
- 每当用户表示第一个根因不正确时
- 每当分析轮次达到3轮时（检查是否需要记录）
- 当用户要求"继续分析其他方向"时

### 触发归纳流程

**当用户提供多份BUGrecord（BUGrecord1.md、BUGrecord2.md...）时**：

1. **读取所有BUGrecord**：扫描 `feedback_pool/` 下所有 `BUGrecord*.md` 文件
2. **检测已归纳标记**：每条问题的 `---` 分隔块末尾检查是否有 `<!-- 已归纳: 时间戳 -->`
3. **只归纳未标记的问题**：提取所有没有「已归纳」标记的记录
4. **执行归纳**：按 `references/feedback-synthesis.md` 归纳
5. **标记已归纳**：在每条归纳完成的记录末尾追加 `<!-- 已归纳: YYYY-MM-DD HH:MM -->`

**触发方式**：
```
用户: 把 BUGrecord1.md、BUGrecord2.md 放到 feedback_pool/ 目录
用户: "开始归纳"
Skill: 读取所有BUGrecord → 过滤已归纳 → 执行归纳 → 标记已归纳
```

**目录结构**：
```
android-audio-debugging/
├── BUGrecord.md
└── feedback_pool/
    ├── BUGrecord1.md
    ├── BUGrecord2.md
    └── ...
```

**已归纳标记格式**：
```markdown
## [问题1] xxx
**记录时间**: 2024-01-15 10:30

...内容...

<!-- 已归纳: 2024-01-20 15:00 -->
---
## [问题2] yyy
**记录时间**: 2024-01-16 09:00

...内容...

<!-- 已归纳: 2024-01-20 15:00 -->
```

---

## 用户自定义知识库

**配置位置**: `user_config.md`

技能启动时自动读取 `user_config.md` 中的知识库目录配置，并在分析过程中扫描这些目录匹配相关案例。

### 目录格式
```
# 注释
D:\AudioCases
D:\AudioFAQ
D:\VendorDocs\Qualcomm
```

### 调用时机
- **阶段1（自动分析）**: 案例匹配时同时检索用户知识库
- **阶段2（疑点验证）**: 可参考用户知识库中的历史解决方案
- **阶段4（报告输出）**: 如有相关知识库内容，附加参考链接

---

## 参考资料

| 文件 | 内容 |
|------|------|
| `references/framework-layers.md` | Audio框架分层知识 |
| `references/hal-interface.md` | HAL接口与状态机 |
| `references/failure-patterns.md` | 常见故障模式库 |
| `references/log-analysis.md` | 日志分析技巧 |
| `references/case-library.md` | 历史案例库格式 |
| `references/feedback-synthesis.md` | BUGrecord归纳方法论 |
| `references/feedback-loop-guide.md` | 反馈收集流程指南 |
| `BUGrecord.md` | 用户侧偏离记录模板 |
| `user_config.md` | 用户自定义知识库目录配置 |
