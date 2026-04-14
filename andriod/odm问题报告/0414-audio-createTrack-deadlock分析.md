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

### 日志证据（基于 -1_ne_2.log 修正）

**关键发现：`gsl_send_spf_cmd opcode 0x1001004` (GRAPH_CLOSE) 在 `graph_stop exit` 之前发送！**

#### 异常流程原log（tid 9036, 02:45:46.968）

```
1033423:04-11 02:45:46.968  9027  9036 I PAL: API: pal_stream_close: 259: Enter. Stream handle :0xb400007d86295f50K
1033424:04-11 02:45:46.968  9027  9036 I AGM: API: agm_session_aif_connect: 603 disconnecting aifid:6 with session id=105
1033425:04-11 02:45:46.968  9027  9036 D AGM: graph: graph_stop: 960 entry graph_handle 0x547534c
1033426:04-11 02:45:46.968  9027  9036 D AGM: metadata: metadata_print: 82 *************************Metadata*************************
1033442:04-11 02:45:46.968  9027  9036 D AGM: metadata: metadata_print: 96 key:0x800000, value:0x1
1033453:04-11 02:45:46.968  9027  9036 D AGM: metadata:
1033454:04-11 02:45:46.968  9027  9036 I gsl     : gsl_graph_close_sgids_and_connections:2056 num_sgid= 1
1033455:04-11 02:45:46.968  9027  9036 I gsl     : gsl_graph_close_sgids_and_connections:2057 sg list:
1033456:04-11 02:45:46.968  9027  9036 I gsl     : gsl_graph_close_sgids_and_connections:2059 b0000021
1033457:04-11 02:45:46.968  9027  9036 I gsl     : gsl_print_sg_conn_info:191 num_sg_conn = 2
1033458:04-11 02:45:46.968  9027  9036 I gsl     : gsl_print_sg_conn_info:193 sg b0000021 has 1 children:
1033459:04-11 02:45:46.968  9027  9036 I gsl     : gsl_print_sg_conn_info:196 b0000008,
1033460:04-11 02:45:46.968  9027  9036 I gsl     : gsl_print_sg_conn_info:193 sg b0000012 has 1 children:
1033461:04-11 02:45:46.968  9027  9036 I gsl     : gsl_print_sg_conn_info:196 b0000021,
1033462:04-11 02:45:46.968  9027  9036 I gsl     : gsl_send_spf_cmd:165 sending pkt with token 0x21230000, opcode 0x1001004
1033463:04-11 02:45:46.970  9081  9082 D AF::Track: stop(1875): calling pid 3508
1033464:04-11 02:45:46.973  9027  9036 D AGM: graph: graph_stop: 1005 exit, ret 0
1033465:04-11 02:45:46.973  9027  9036 I PAL: SessionAlsaUtils: close: 647: No need to free device metadata as device is still active
1033466:04-11 02:45:46.973  9027  9036 I AGM: session: session_obj_set_sess_aif_metadata: 1760 Setting metadata for sess aif id 6
// 之后无日志，卡在 gsl_close 内部
```

#### 正常 close 流程原log（tid 9356, 02:42:58.212）

```
35604:04-11 02:42:58.212  9027  9356 D AGM: session: session_close: 1270 enter
35605:04-11 02:42:58.212  9027  9356 D AGM: graph: graph_close: 791 entry handle 0x447534c
35606:04-11 02:42:58.212  9027  9356 I gsl     : gsl_graph_close_sgids_and_connections:2056 num_sgid= 1
35607:04-11 02:42:58.212  9027  9356 I gsl     : gsl_graph_close_sgids_and_connections:2057 sg list:
35608:04-11 02:42:58.212  9027  9356 I gsl     : gsl_graph_close_sgids_and_connections:2059 b000010f
35609:04-11 02:42:58.212  9027  9356 I gsl     : gsl_print_sg_conn_info:191 num_sg_conn = 0
35610:04-11 02:42:58.212  9027  9356 I gsl     : gsl_send_spf_cmd:165 sending pkt with token 0x10a3d000, opcode 0x1001004
35611:04-11 02:42:58.214 30393 11899 D AudioTrackImpl: [audioTrackData][fine] 30s...
35612:04-11 02:42:58.214  9027  9356 D AGM: graph: graph_close: 816 exit, ret 0
35613:04-11 02:42:58.214  9027  9356 D AGM: session: session_close: 1319 exit, ret 0
35614:04-11 02:42:58.214  9027  9356 I PAL: ResourceManager: freeFrontEndIds: 6643: stream type 2, freeing 115
```

#### 关键差异对比

| 特征 | 正常流程 (tid 9356) | 异常流程 (tid 9036) |
|------|-------------------|---------------------|
| 函数入口 | `session_close: 1270 enter` | `pal_stream_close: Enter` |
| graph_close entry | ✅ 有 `graph_close: 791 entry` | ❌ **缺失** |
| graph_close exit | ✅ 有 `graph_close: 816 exit, ret 0` | ❌ **缺失** |
| session_close exit | ✅ 有 `session_close: 1319 exit, ret 0` | ❌ **缺失** |
| graph_stop entry/exit | 无（走的是 close 路径） | ✅ 有 `graph_stop entry/exit` |
| `gsl_send_spf_cmd` 时机 | 在 `graph_close entry` 之后 | 在 `graph_stop` 期间 |
| 最终状态 | 正常返回 | **卡住，无后续日志** |

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

### GSL 深层代码分析

#### gsl_close 完整调用链 (gsl_main.c:1325)

```c
gsl_close(graph_handle) {
    gsl_main_start_client_op_blocking(&gsl_ctxt);  // 1331
    gsl_graph_stop(graph, gsl_ctxt.start_stop_lock);  // 1340
    gsl_graph_close(graph, gsl_ctxt.open_close_lock);  // 1344 ← 卡住点
    release_graph_handle(graph_handle);
    gsl_graph_deinit(graph);
}
```

#### gsl_graph_close 实现 (gsl_graph.c:4292)

```c
int32_t gsl_graph_close(struct gsl_graph *graph, ar_osal_mutex_t lock)
{
    GSL_MUTEX_LOCK(lock);  // 4298 - 获取 open_close_lock

    while (!ar_list_is_empty(&graph->gkv_list)) {
        rc = gsl_graph_close_single_gkv(graph, gkv_node, ...);  // 4304
    }

    gsl_graph_signal_event_all(graph, GSL_SIG_EVENT_MASK_CLOSE);  // 4320
    gsl_wait_for_all_buffs_to_be_avail(...);  // 4327-4328

    GSL_MUTEX_UNLOCK(lock);  // 4338 - 永不执行
    return first_rc;
}
```

#### gsl_graph_close_single_gkv → gsl_graph_close_sgids_and_connections (gsl_graph.c:2395)

```c
static int32_t gsl_graph_close_sgids_and_connections(...)
{
    // ... 构建 GRAPH_CLOSE 命令 ...

    rc = gsl_send_spf_cmd_wait_for_basic_rsp(&gsl_msg.gpr_packet,  // 2142
        &graph->graph_signal[GRAPH_CTRL_GRP3_CMD_SIG]);
    if (rc)
        GSL_ERR("Graph close failed:%d", rc);  // 2145 - 永不打印

    return rc;
}
```

#### gsl_send_spf_cmd 等待响应 (gsl_common.c:142)

```c
int32_t gsl_send_spf_cmd(...) {
    rc = __gpr_cmd_async_send(*packet);  // 169 - 发送命令

    if (sig_p != NULL) {
        GSL_INFO("sending pkt with token 0x%x, opcode 0x%x", ...);  // 165 - 已有日志
        rc = gsl_signal_timedwait(sig_p, GSL_SPF_TIMEOUT_MS, ...);  // 189
        GSL_DBG("Wait done rc[0x%x] ...", rc);  // 198 - **永不打印！**
        if (rc)
            rc = AR_ETIMEOUT;  // 204
    }
}
```

#### 关键发现：gsl_signal_timedwait 永久阻塞

日志中：
```
1033462: gsl_send_spf_cmd:165 sending pkt with token 0x21230000, opcode 0x1001004
// 之后没有 "Wait done" 日志
```

**说明 `gsl_signal_timedwait` 等待的信号永远没有被设置！**

可能原因：
1. **DSP 固件 GRAPH_CLOSE 处理异常**：命令到达但未处理，无响应
2. **graph_signal 被异常清除或未正确设置**
3. **GPR/SPD 通信断路**：命令根本没有到达 DSP

---

## 根因总结

### 第一层根因：gsl_send_spf_cmd_wait_for_basic_rsp() 永久等待 DSP 响应

**tid 9036** 调用 `session->close(this)` 后：
- `graph_stop` 正常返回（exit ret 0）
- `gsl_graph_close_sgids_and_connections` 发送 GRAPH_CLOSE 命令（opcode 0x1001004）
- `gsl_signal_timedwait` 等待 `graph_signal[GRAPH_CTRL_GRP3_CMD_SIG]`
- **DSP 永远不响应，信号永不设置，`gsl_signal_timedwait` 永久阻塞**
- 调用栈一直卡在 `gsl_send_spf_cmd_wait_for_basic_rsp` 内部

### 第二层根因：gsl_graph_close() 获取 open_close_lock 后永不释放

- `gsl_graph_close` 在 line 4298 获取 `open_close_lock`
- 由于 `gsl_send_spf_cmd_wait_for_basic_rsp` 永不返回
- `gsl_graph_close` 永远无法执行到 `GSL_MUTEX_UNLOCK(lock)` (line 4338)
- **`open_close_lock` 被永久持有**

### 第三层根因：HAL 锁连锁阻塞

- `rm->lockGraph()` 在 `session->close()` 之前被 tid 9036 获取
- 由于 `session->close()` 永不返回，`rm->unlockGraph()` 永不执行
- tid 9027 (INPUT stop) 和所有等待 `lockGraph()` 的线程永久阻塞
- 最终导致 `createTrack` 超时

### 第四层根因：DSP 固件 GRAPH_CLOSE 处理异常

- `device is not open` 表明设备状态异常
- 可能导致 DSP 无法正确处理 GRAPH_CLOSE 命令
- 或者 GPR/SPD 通信路径在异常状态下断开

---

## 修复建议

### P0 - 紧急

| 方案 | 说明 | 代码位置 |
|------|------|----------|
| **gsl_send_spf_cmd_wait_for_basic_rsp 超时后强制返回** | 已有超时机制，但超时后应设置错误标志并强制返回，不应永久等待 | gsl_common.c:142 |
| **lockGraph 使用 try_lock** | 超时后强制释放或重试，避免全局死锁 | StreamCompress.cpp:249 |
| **gsl_graph_close 单步超时** | 在 `gsl_send_spf_cmd_wait_for_basic_rsp` 之后检查返回值，超时则强制跳出 | gsl_graph.c:4292 |

### P1 - 重要

| 方案 | 说明 | 代码位置 |
|------|------|----------|
| **分离 lockGraph 锁粒度** | 改为 per-graph 锁，避免全局影响 | ResourceManager.h:893 |
| **增加设备状态校验** | 操作前确认设备已正确打开，避免异常路径 | StreamCompress::close |
| **添加 gsl_signal_set 超时保护** | 确保信号在合理时间内被设置，否则上报异常 | gsl_common.c:80 |
| **DSP 响应监控** | 添加 DSP 命令响应超时监控，快速失败 | gsl_common.c |

### P2 - 优化

| 方案 | 说明 |
|------|------|
| **分离 standby 和 close 流程** | 避免 close 阻塞影响 standby |
| **添加死锁检测** | 定期检测 lockGraph 持有时间 |
| **GPR/SPD 通信健康检查** | 检测命令发送后是否有响应，超时重试或报错 |

---

## 待验证项

- [ ] **查 dmesg** - 确认是否有 ASoC/DMA 驱动层错误
- [ ] **查 DSP 固件日志** - 确认 GRAPH_CLOSE (opcode 0x1001004) 是否有响应
- [ ] **查设备 open/close 状态机** - 为何 device is not open
- [ ] **查 GSL_SPF_TIMEOUT_MS 超时值** - 确认超时值是否合理，是否在合理时间内返回
- [ ] **查 graph_signal 设置时机** - 确认 DSP 响应后是否正确设置了 graph_signal[GRAPH_CTRL_GRP3_CMD_SIG]
- [ ] **查 GPR/SPD 通信路径** - 确认 APM_CMD_GRAPH_CLOSE 命令是否到达 DSP

---

## 关键代码位置

### PAL/AGM 层

| 文件 | 行号 | 说明 |
|------|------|------|
| `StreamCompress.cpp` | 249-251 | lockGraph + session->close() |
| `graph.c` | 780-818 | graph_close → gsl_close |
| `session_obj.c` | 1262-1321 | session_close 流程 |
| `StreamPCM.cpp` | 727 | INPUT stop 等待 lockGraph |

### GSL 层

| 文件 | 行号 | 说明 |
|------|------|------|
| `gsl_main.c` | 1325-1360 | gsl_close 完整流程 |
| `gsl_main.c` | 1331 | gsl_main_start_client_op_blocking |
| `gsl_main.c` | 1344 | gsl_graph_close 调用 |
| `gsl_graph.c` | 4292-4341 | **gsl_graph_close 核心实现** |
| `gsl_graph.c` | 2142-2146 | gsl_send_spf_cmd_wait_for_basic_rsp 调用 |
| `gsl_common.c` | 142-221 | **gsl_send_spf_cmd 等待响应** |
| `gsl_common.c` | 189 | gsl_signal_timedwait 超时等待 |
| `gsl_common.c` | 53-78 | gsl_signal_timedwait 实现 |

### AudioStream 层

| 文件 | 行号 | 说明 |
|------|------|------|
| `AudioStream.cpp` | 2186 | StreamOutPrimary::Standby 流锁 |
| `AudioStream.cpp` | 2296 | Standby Exit 日志 |

---

## 相关文件

- 日志: `D:\BUG\audio crash\1.txt`
- Tombstone: `tombstone_03`, `tombstone_04`, `tombstone_05`
- 代码: `D:\BUG\audio crash\code\`
