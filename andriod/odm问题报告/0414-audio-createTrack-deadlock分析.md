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

### 日志证据（已修正）

**关键发现：`graph_stop` 正常退出，`gsl_close` 卡住！**

```
02:45:46.968  9036 I AGM: API: agm_session_aif_connect: 603 disconnecting aifid:6 with session id=105
02:45:46.968  9036 D AGM: graph: graph_stop: 960 entry graph_handle 0x547534c
02:45:46.968  9036 I gsl: gsl_send_spf_cmd:165 sending pkt with token 0x21230000, opcode 0x1001004
02:45:46.973  9036 D AGM: graph: graph_stop: 1005 exit, ret 0     ← graph_stop 正常退出 ✅
02:45:46.973  ... (SessionAlsaUtils, session_obj_set_sess_aif_metadata)
// 02:45:46.973 之后 tid 9036 完全无日志，graph_close 无 exit 日志 ❌
```

### 代码流程（StreamCompress::close）

```cpp
// line 249-251
rm->lockGraph();                    // 获取锁
status = session->close(this);      // 内部 graph_close 卡住！
rm->unlockGraph();                  // 永远不会执行
```

### session_close 内部调用链

```c
session_close() {
    pthread_mutex_lock(&hwep_lock);     // 1277
    if (sess_obj->state == SESSION_STARTED) {
        graph_stop(...);   // 1279 - exit ret 0 ✅
    }
    graph_close(...);      // 1285 - 无 exit 日志 ❌ 卡住点
    pthread_mutex_unlock(&hwep_lock);  // 1316 永远不会执行
}
```

### graph_close 内部卡住点

```c
graph_close() {
    pthread_mutex_lock(&graph_obj->lock);  // 790
    ret = gsl_close(graph_obj->graph_handle);  // 793 ← 卡住！
    // 后续代码不会执行
    pthread_mutex_unlock(&graph_obj->lock);    // 813 不会执行
    pthread_mutex_destroy(&graph_obj->lock);   // 814 不会执行
    free(graph_obj);                           // 815 不会执行
}
```

### 卡住点确认

| 阶段 | 状态 | 证据 |
|------|------|------|
| `graph_stop` | ✅ 正常退出 | exit ret 0，gsl_send_spf_cmd 正常返回 |
| `gsl_close` | ❌ **卡住** | 无 exit 日志，无 gsl_send_spf_cmd 日志 |
| `rm->unlockGraph()` | ❌ 永远不执行 | 被 session->close() 阻塞 |
| `hwep_lock` 释放 | ❌ 永远不执行 | session_close 未返回 |

### 推测：`gsl_close` 内部流程

```
gsl_close(graph_handle)
    → 发送 DSP 命令（可能 opcode 未知或无日志）
    → 等待 DSP 响应 ← 卡住
    → 永不返回
```

可能原因：
1. **DSP 固件无响应**：`gsl_close` 发送的命令无 ACK
2. **graph_handle 状态异常**：graph 已处于异常状态，gsl_close 内部死锁
3. **Global Graph Lock 问题**：`gsl_close` 内部可能也需要获取全局锁，与其他操作冲突

---

## 根因总结

### 第一层根因：gsl_close() 阻塞

**tid 9036** 调用 `session->close(this)` 后，`graph_stop` 正常返回，但 `graph_close()` 内部的 `gsl_close()` 阻塞：
- `gsl_close()` 发送 DSP 命令后无响应，卡在等待
- 导致 `rm->lockGraph()` 和 `hwep_lock` 永久持有
- 所有等待 `lockGraph()` 的线程全部卡住

### 第二层根因：HAL 内部锁设计缺陷

- `lockGraph()` 是全局锁，被多个 stream 操作共享
- `gsl_close()` 没有超时保护机制
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
| **给 gsl_close() 增加超时** | 避免永久阻塞，建议 2-5 秒超时 |
| **给 session->close() 增加超时** | 避免永久阻塞，建议 2-5 秒超时 |
| **lockGraph 使用 try_lock** | 超时后强制释放或重试 |

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
- [ ] **查 DSP 固件日志** - 确认 **gsl_close** 为何无响应（graph_stop 已确认正常）
- [ ] **查设备 open/close 状态机** - 为何 device is not open

---

## 关键代码位置

| 文件 | 行号 | 说明 |
|------|------|------|
| `StreamCompress.cpp` | 249-251 | lockGraph + session->close() |
| `graph.c` | 780-818 | **graph_close 卡住在 gsl_close** |
| `session_obj.c` | 1262-1321 | session_close 流程 |
| `StreamPCM.cpp` | 727 | INPUT stop 等待 lockGraph |
| `AudioStream.cpp` | 4235 | StreamInPrimary::Standby 流锁 |
| `AudioStream.cpp` | 2186 | StreamOutPrimary::Standby 流锁 |

---

## 相关文件

- 日志: `D:\BUG\audio crash\1.txt`
- Tombstone: `tombstone_03`, `tombstone_04`, `tombstone_05`
- 代码: `D:\BUG\audio crash\code\`
