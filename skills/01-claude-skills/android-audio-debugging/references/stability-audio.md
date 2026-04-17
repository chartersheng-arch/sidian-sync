# Android Audio 稳定性问题专项分析

## 1. 稳定性问题分类

| 问题类型 | 特征 | 关键指标 |
|----------|------|----------|
| ANR | 主线程阻塞>5s | traces.txt / wtf |
| Crash | 进程异常退出 | tombstone / logcat FATAL |
| Deadlock | 多线程相互等待 | lockdep / hang dump |
| Hang | 系统无响应 | Watchdog / binder诊疗 |

---

## 2. ANR分析

### 2.1 Audio相关ANR场景

| 场景 | 阻塞位置 | 超时阈值 |
|------|----------|----------|
| AudioTrack.write() | App主线程 | >5s |
| AudioRecord.read() | App主线程 | >5s |
| dumpsys media.audio_policy | AudioPolicyService | >10s |
| AudioFocus请求 | AudioPolicyService | >1s |

### 2.2 关键日志标记

```
[ANR] Reason: executing service audio.xxx
[ANR] Thread main: tid=1, waiting for lock 0xxxxx held by tid=xx
[ANR] CPU usage from 0ms to 9277ms later:
[ANR]   DALVIK THREADS:
[ANR]   "main" prio=5 tid=1 Runnable
[ANR]     waiting for <lock> held by Thread-<N>

[Binder] BLOCKING pid=xxx uid=xxx interface=IAudioPolicy
[Binder] DEADLOCK detected between threads
```

### 2.3 traces.txt分析模板

```
----- pid <pid> at <timestamp> -----
Cmd line: com.android.audio

"main" prio=5 tid=1 Runnable
  | group="main" sCount=0 dsCount=0 flags=0 obj=0x<addr> self=0x<addr>
  | sysTid=<tid> nice=0 cgrp=default handle=xxx
  | state=? sched=(0, 0)亲和......
  | stack=<stack_addr>
  at android.media.AudioTrack.writeNative(Native method)
  at android.media.AudioTrack.write(AudioTrack.java:<line>)

  Lockers involved: <lock_addr>
  Locked by: Thread-<N>
```

### 2.4 ANR根因快速定位

| 阻塞类型 | 日志特征 | 常见根因 |
|----------|----------|----------|
| 锁等待 | waiting for lock + Locked by | AudioPolicy锁竞争 |
| 同步调用 | pcm_write blocked | HAL层blocking I/O |
| 内存分配 | allocating... + blocked | lowmemorykiller |
| Binder阻塞 | binder_transaction... blocked | AudioFlinger未响应 |

---

## 3. Crash分析

### 3.1 Audio相关Crash模式

| 模式 | 信号 | 常见位置 | 根因 |
|------|------|----------|------|
| 空指针 | SIGSEGV(11) | AudioTrack::cblk | 异步销毁后访问 |
| 内存越界 | SIGABRT(6) | Buffer::write | 写入超过分配大小 |
| ASSERT失败 | SIGABRT(6) | AudioFlinger | 状态机非法转换 |
| 死循环 | WATCHDOG | MixerThread | Buffer永远不空 |

### 3.2 关键日志标记

```
[libc] Fatal signal 11 (SIGSEGV), code 1 (SEGV_MAPERR)
[libc] Fatal signal 6 (SIGABRT), code 0 (SI_USER)

[Crash] Build fingerprint: xxx
[Crash] #00  pc <addr>  /system/lib/libaudiofoundation.so
[Crash] #01  pc <addr>  /system/lib/libaudiofoundation.so
[Crash] #02  pc <addr>  android.media.AudioTrack._writeNative

[DEBUG] Assertion failed: mState == STATE_INITIALIZED
[DEBUG] Abort message: 'audio_written != 0 in flush()'
```

### 3.3 Tombstone分析模板

```
--- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
Build fingerprint: 'xxx'
Revision: 'xxx'
ABI: 'arm64'

 signal 11 (SIGSEGV), code 1 (SEGV_MAPERR), fault addr 0x0

 registers:
  x0  = 0x0000000000000000   ← Crash时x0=NULL
  x1  = 0x0000007f8a4c8a00
  pc  = 0x0000007b8d2c3c4c   ← Crash指令地址

 backtrace:
  #00 pc <addr>  libaudiofoundation.so  AudioTrack::writeNative()
  #01 pc <addr>  libaudiofoundation.so  AudioTrack::write()
  #02 pc <addr>  libaudiofoundation.so  AudioTrack::obtain()
```

### 3.4 Crash根因分类

| Crash类型 | 日志证据 | 根因 |
|-----------|----------|------|
| 空指针解引用 | fault addr 0x0 | 对象已销毁 |
| 内存双重释放 | double free | 生命周期管理错误 |
| 栈溢出 | stack overflow | 递归调用过深 |
| 整数溢出 | heap overflow | size计算错误 |

---

## 4. Deadlock分析

### 4.1 Audio常见死锁模式

| 锁类型 | 锁位置 | 死锁场景 |
|--------|--------|----------|
| AudioPolicy锁 | mpPolicyLock | AudioPolicy + AudioFlinger双锁 |
| AudioFlinger锁 | mLock | Mixer + RecordThread竞争 |
| HAL锁 | pcm_lib | 多session同步调用 |
| Binder锁 | IPC thread | AudioService跨进程调用 |

### 4.2 关键日志标记

```
[DEADLOCK] Circular wait detected:
  Thread-A holding Lock-X waiting for Lock-Y
  Thread-B holding Lock-Y waiting for Lock-X

[Binder] WARNING: possible deadlock:城乡

[AudioFlinger] Thread tid=<id> blocked for <ms>ms
[AudioPolicy] potential deadlock in getOutputforAttributes()

[lockdep] Possible deadlock: AudioPolicy::mx
```

### 4.3 Lockdep输出分析

```
[  123.456] ==========================
[  123.456] [ BUG ] possible deadlock (lockdep_chain)
[  123.456] ==========================
[  123.456] Chain exists in:
[  123.456]  Thread-A: Lock-X -> Lock-Y  (AudioPolicy -> AudioFlinger)
[  123.456]  Thread-B: Lock-Y -> Lock-X  (AudioFlinger -> AudioPolicy)

[  123.456] CPU: <id>
[  123.456] Current: Task <name>:<tid>
```

### 4.4 死锁验证方法

```bash
# 获取AudioFlinger线程状态
adb shell "dumpsys audioflinger" | grep -A10 "Threads"

# 获取锁等待信息
adb shell "dumpsys audioflinger" | grep -i "lock"

# 获取Binder状态
adb shell "dumpsys media.audio_policy" | grep -i "waiting"

# 触发hang dump
adb shell "dumpsys activity hang"
```

---

## 5. Hang分析

### 5.1 系统Hang场景

| 场景 | 影响范围 | 日志标记 |
|------|----------|----------|
| AudioFlinger挂死 | 仅音频 | Thread stuck |
| AudioPolicyService挂死 | 全局音频 | service hung |
| HAL层挂死 | 底层输出 | pcm_write blocked |
| Watchdog触发 | 系统级 | system_server ANR |

### 5.2 关键日志标记

```
[WATCHDOG] AudioFlinger not responding, blocking policy service
[WATCHDOG] BLOCKED: Thread MixerThread (tid=xxx) for >10s

[SYSTEM] system_server not responding
[SYSTEM] Native crash at AudioFlinger

[hang_detect] dump for process audio.xxx
[hang_detect] Thread main: stack:
```

### 5.3 Watchdog配置参考

```cpp
// AudioFlinger线程超时配置
static const int kMaxSleepTimeUs = 10000;  // 10ms
static const int kMinBufferSize = 256;

// Watchdog检测间隔
#define HW_WATCHDOG_TIMEOUT_MS  30000
#define SW_WATCHDOG_TIMEOUT_MS  10000
```

---

## 6. 稳定性问题分析流程

### 6.1 信息收集清单

| 信息 | 来源 | 优先级 |
|------|------|--------|
| traces.txt | /data/anr/ | P0 |
| tombstone | /data/tombstones/ | P0 |
| logcat | kernel/logcat | P0 |
| bugreport | adb bugreport | P1 |
| perfetto trace | /data/misc/perfetto-traces | P1 |

### 6.2 分析决策树

```
稳定性问题
├── ANR
│   ├── 主线程阻塞
│   │   ├── AudioTrack.write  → 检查App调用链
│   │   ├── Binder调用      → 检查AudioPolicyService
│   │   └── 锁等待          → 检查死锁
│   └── Background线程
│       └── 检查调度优先级
├── Crash
│   ├── SIGSEGV            → 分析tombstone
│   ├── SIGABRT            → 分析ASSERT
│   └── Native Crash       → 分析backtrace
├── Deadlock
│   ├── 锁顺序问题         → 分析lockdep
│   └── 条件变量问题       → 分析wait/notify
└── Hang
    ├── Watchdog触发       → 分析阻塞点
    └── 系统无响应         → 检查CPU/内存
```

### 6.3 三轮推理模板

**第一轮（直接证据）**
```
证据: <直接日志/堆栈>
结论: <直接原因>
置信度: [高/中/低]
```

**第二轮（时序分析）**
```
问题前2秒事件: <按时间顺序列出>
因果链: <A→B→C>
结论: <时序相关原因>
置信度: [高/中/低]
```

**第三轮（对比分析）**
```
差异点: <正常vs异常>
缺失步骤: <异常中缺少>
结论: <差异点原因>
置信度: [高/中/低]
```

---

## 7. 稳定性问题案例库

### 案例-STAB-001: AudioTrack空指针Crash

**基本信息**
- 设备: 通用
- 平台: Android 12+
- 分类: Crash / 空指针

**问题现象**
播放音乐时偶发Crash，logcat显示SIGSEGV

**关键日志**
```
[Crash] signal 11 (SIGSEGV), fault addr 0x0
[Crash] #00 pc <addr> AudioTrack::writeNative()
[Crash] x0 = 0x0000000000000000  ← AudioTrack对象已销毁
```

**根因**
AudioTrack在另一个线程中被release，主线程继续调用write导致空指针

**解决方案**
增加AudioTrack生命周期保护，write前检查mState != DESTROYED

**验证方法**
并发场景下多次测试无Crash

---

### 案例-STAB-002: AudioPolicy锁死锁

**基本信息**
- 设备: 某高通设备
- 平台: Android 13 / QCOM SM8450
- 分类: Deadlock / ANR

**问题现象**
通话时调节音量导致系统无响应，触发ANR

**关键日志**
```
[DEADLOCK] Thread-A: AudioPolicy::mx waiting for AudioFlinger::mx
[DEADLOCK] Thread-B: AudioFlinger::mx waiting for AudioPolicy::mx
[ANR] Thread main blocked for 15000ms
```

**根因**
AudioPolicy::setPhoneState()持有自身锁后调用AudioFlinger，AudioFlinger回调时请求AudioPolicy锁形成死锁

**解决方案**
重构锁顺序，回调时不直接请求AudioPolicy锁，改为post到主线程

**验证方法**
通话时快速调节音量100次无ANR

---

### 案例-STAB-003: HAL层阻塞导致ANR

**基本信息**
- 设备: 某MTK设备
- 平台: Android 14 / MTK Dimensity 9200
- 分类: ANR / HAL阻塞

**问题现象**
录音时偶尔无响应，dumpsys卡住

**关键日志**
```
[HAL] in_set_parameters: blocking call, tid=<id>
[ANR] executing service media.audio_policy, blocked for 30s
[Binder] tid=<id> stuck in audio_hw device operation
```

**根因**
HAL层in_set_parameters调用了blocking I/O (I2C读取)，在持有锁的情况下阻塞超过30s

**解决方案**
将I2C操作移到独立线程，HAL接口保持异步

**验证方法**
连续录音1小时无ANR，dumpsys media.audio_policy响应<1s

---

### 案例-STAB-004: FastMixer死循环

**基本信息**
- 设备: 某高通设备
- 平台: Android 13
- 分类: Hang / Watchdog

**问题现象**
游戏时音频卡死，Watchdog触发

**关键日志**
```
[Watchdog] MixerThread stuck, loop count=10000
[Watchdog] mBytesWritten never advancing
[AudioFlinger] FastMixer: buffer underrun, but mixer not waking
```

**根因**
FastMixer进入异常状态，检测到underrun后尝试恢复但陷入死循环

**解决方案**
增加FastMixer watchdog，检测到异常循环次数后强制reset thread

**验证方法**
游戏音频场景压测30分钟无Watchdog触发

---

## 8. 常用调试命令

```bash
# ANR相关
adb shell cat /data/anr/traces.txt
adb shell dumpsys activity anr

# Crash相关
adb shell cat /data/tombstones/tombstone_*
adb logcat -d | grep -E "FATAL|signal|Crash"

# 死锁相关
adb shell "dumpsys audioflinger" | grep -i "lock"
adb shell "dumpsys media.audio_policy" | grep -i "waiting"

# 线程状态
adb shell "dumpsys audioflinger" | grep -A5 "Threads"
adb shell "ps -T -p <pid>" | head -20

# Binder状态
adb shell "dumpsys media.audio_policy" | grep -i "binder"

# perfetto trace
adb shell "cat /data/misc/perfetto-traces/boot_trace.perfetto-trace.gz"
```

---

## 9. 稳定性分析质量检查

- [ ] traces.txt / tombstone 已获取
- [ ] 崩溃线程已确认 (main / binder / audio)
- [ ] 阻塞/崩溃原因有直接日志证据
- [ ] 锁竞争场景有lockdep或hang dump
- [ ] 根因有至少3轮独立推理
- [ ] 解决方案可行且风险可控
