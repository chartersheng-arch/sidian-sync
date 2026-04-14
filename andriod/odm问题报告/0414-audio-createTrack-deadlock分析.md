# IAudioFlinger::createTrack 死锁问题分析

## 概要

| 项目 | 内容 |
|------|------|
| **问题类型** | 多层死锁导致 createTrack 超时 |
| **设备** | Redmi (erhu) |
| **平台** | Android 16 / OS3.0.301.0.WDOCNXM |
| **分析日期** | 2026-04-14 |
| **复现率** | 必现 |

---

## 问题现象

`audioserver` 进程中的 `IAudioFlinger::createTrack` 调用超时（8秒），系统检测到 **mutex wait chain** 并触发 SIGABRT。

**Abort 消息:**
```
TimeCheck timeout for IAudioFlinger::createTrack scheduled 02:45:46.389 on thread 9187
Timeout ms 8000.00 (6000.00 + 2000.00) elapsed steady ms 8000.3472
HAL pids [ 9027 ]
secondChanceCount 12
analysis [ mutex wait chain [ 9187, 9197 (by AudioPolicyService_Mutex), 16289 (by join) ] ]
```

---

## 关键日志时间线（1.txt）

| 时间           | TID   | 事件                                               | 关键点                  |
| ------------ | ----- | ------------------------------------------------ | -------------------- |
| 02:45:46.958 | 9036  | `Drain` → `astream_out_standby`                  | 进入 standby           |
| 02:45:46.965 | 9036  | `voteSleepMonitor: ioctl device is not open`     | **错误：设备未打开**         |
| 02:45:46.968 | 9036  | `pal_stream_close` 开始                            | **开始卡住**             |
| 02:45:46.968 | 9036  | `agm_session_aif_connect: disconnecting aifid:6` | AGM 断开连接             |
| 02:45:46.968 | 9036  | `graph_stop: entry`                              | **进入后无响应，卡住**        |
| 02:45:48.464 | 9027  | `StreamPCM::stop()` INPUT                        | **等待 lockGraph**     |
| 02:45:48.464 | 9027  | `device count = 1`                               | 设备数量正常               |
| 02:45:48.464 | 9027  | 已经阻塞                                             | lockGraph 等待中        |
| 02:45:50.033 | 14796 | `StreamOutPrimary::Standby()`                    | **等待 stream_mutex_** |
| 02:45:54.391 | 9027  | `handling signal: 35`                            | crash 开始             |

---

## 多层死锁分析

### 第一层：AudioFlinger 侧死锁

```
tid 9187: createTrack() → 需要 AudioPolicyService_Mutex
    ↓ 等待
tid 9197: closeOutput() → 持有 AudioPolicyService_Mutex → 等待 tid 16289 退出
    ↓ 等待
tid 16289: PlaybackThread → standby() → ioctl → 等待 HAL 响应
```

### 第二层：HAL 进程内部死锁

```
tid 9027 (主线程): StreamInPrimary::Standby()
    → stream_mutex_.lock() 持有
    → rm->lockGraph() 等待 ←─────────────┐
    ↓                                      │ 等待
tid 9036: StreamCompress::close()         │
    → rm->lockGraph() 已持有               │
    → session->close() 卡住 ←──────────────┘
        (agm_session_aif_connect + graph_stop 无响应)

tid 14796: StreamOutPrimary::Standby()
    → stream_mutex_.lock() 等待 tid 9027 释放
```

---

## 根因链路

```
tid 9036 调用 pal_stream_close
    ↓
session->close() → AGM 内部
    → agm_session_aif_connect (disconnecting)
    → graph_stop: entry → **卡住，无响应**
    ↓
rm->lockGraph() 锁无法释放
    ↓
tid 9027 等待 lockGraph → 持有 stream_mutex_
    ↓
tid 14796 等待 stream_mutex_
    ↓
所有 standby 调用阻塞 → HAL 无响应
    ↓
PlaybackThread 卡住 → closeOutput 等待
    ↓
AudioPolicyService_Mutex 持有 → createTrack 超时
```

---

## tid 9036 卡住详细分析

### 日志证据

```
02:45:46.968  9036 I PAL: API: pal_stream_close: 259: Enter. Stream handle :0xb400007d86295f50K
02:45:46.968  9036 I AGM: API: agm_session_aif_connect: 603 disconnecting aifid:6 with session id=105
02:45:46.968  9036 D AGM: graph: graph_stop: 960 entry graph_handle 0x547534c
// 之后无日志，卡住
```

### 代码流程（StreamCompress::close）

```cpp
// line 249-251
rm->lockGraph();                    // 获取锁
status = session->close(this);      // 卡在这里！
rm->unlockGraph();                  // 永远不会执行
```

### 卡住点推测

| 可能原因 | 依据 |
|----------|------|
| **DSP/固件无响应** | AGM 库与 DSP 通信，graph_stop 后无响应 |
| **graph 资源死锁** | graph_handle 0x547534c 可能被多线程共享 |
| **AGM 内部调用链死锁** | disconnect + graph_stop 可能相互等待 |
| **设备状态异常** | `ioctl device is not open` 表明设备状态异常 |

---

## 根因总结

### 第一层根因：session->close() 阻塞

**tid 9036** 调用 `session->close(this)` 后，AGM 层的 `graph_stop` 开始执行但永远不返回，导致：
- `rm->lockGraph()` 永久持有
- 所有等待 `lockGraph()` 的线程全部卡住

### 第二层根因：HAL 内部锁设计缺陷

- `lockGraph()` 是全局锁，被多个 stream 操作共享
- 没有超时保护机制
- `session->close()` 阻塞导致全局死锁

### 第三层根因：设备状态异常

```
voteSleepMonitor: ioctl device is not open
```

设备未打开就执行操作，可能触发了异常的处理路径。

---

## 修复建议

### P0 - 紧急

| 方案 | 说明 |
|------|------|
| **给 session->close() 增加超时** | 避免永久阻塞，建议 2-5 秒超时 |
| **lockGraph 使用 try_lock** | 超时后强制释放或重试 |
| **AGM 层 graph_stop 增加超时保护** | 防止与 DSP 通信死锁 |

### P1 - 重要

| 方案 | 说明 |
|------|------|
| **分离 lockGraph 锁粒度** | 改为 per-graph 锁，避免全局影响 |
| **增加设备状态校验** | 操作前确认设备已正确打开 |
| **添加超时打断机制** | 定期检查 graph 状态，超时强制 cleanup |

### P2 - 优化

| 方案 | 说明 |
|------|------|
| **分离 standby 和 close 流程** | 避免 close 阻塞影响 standby |
| **添加死锁检测** | 定期检测 lockGraph 持有时间 |

---

## 待验证项

- [ ] **查 dmesg** - 确认是否有 ASoC/DMA 驱动层错误
- [ ] **查 AGM graph 资源管理** - graph_handle 0x547534c 是否被多线程共享
- [ ] **查 DSP 固件日志** - 确认 graph_stop 为何无响应
- [ ] **查设备 open/close 状态机** - 为何 device is not open

---

## 关键代码位置

| 文件 | 行号 | 说明 |
|------|------|------|
| `StreamCompress.cpp` | 249-251 | lockGraph + session->close() 卡住 |
| `StreamPCM.cpp` | 727 | INPUT stop 等待 lockGraph |
| `AudioStream.cpp` | 4235 | StreamInPrimary::Standby 流锁 |
| `AudioStream.cpp` | 2186 | StreamOutPrimary::Standby 流锁 |

---

## 相关文件

- 日志: `D:\BUG\audio crash\1.txt`
- Tombstone: `tombstone_03`, `tombstone_04`, `tombstone_05`
- 代码: `D:\BUG\audio crash\code\`
