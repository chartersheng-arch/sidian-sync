# SPF Software Porting Manual (Linux/Android)

## 1. 移植概述

SPF 设计为**跨平台**，核心 Graph 定义与底层 OS/Hardware 解耦。

## 2. 移植层次

```
┌─────────────────────────────────────┐
│  Graph / Module (平台无关)           │
├─────────────────────────────────────┤
│  CAPI v2 Interface (平台无关)         │
├─────────────────────────────────────┤
│  ADSP Framework (OS 相关)            │
├─────────────────────────────────────┤
│  OS / Hardware Abstraction          │
└─────────────────────────────────────┘
```

## 3. 移植关键步骤

### 3.1 平台适配层 (PAL)

实现 Platform Adaptation Layer，提供：
- 内存管理 (`malloc` / `free` / `shared memory`)
- 线程管理 (DSP thread 创建/同步)
- 时钟配置
- DMA / 共享内存操作

### 3.2 Audio HAL 适配

```
Audio HAL
    ↓
Audio Fabric Driver
    ↓
AFM (Audio Fabric Manager)
    ↓
SPF Graph (ADSP)
```

### 3.3 Graph 适配

- 根据 SoC 资源配置正确的 Module 组合
- 配置 AFM 路由表
- 调整 Buffer Size 以匹配硬件延迟要求

## 4. Linux 特定移植

- 使用 **ALSA** 作为音频驱动框架
- DSP 通信: **Rapid Data Channel** 或 **Shared Memory**
- 加载 DSP Firmware (`.elf` / `.hex`)

## 5. Android 特定移植

- 使用 **Audio HAL** 标准接口
- DSP 固件通过 `audio.extn` 扩展加载
- 与 **AudioFlinger** 深度集成

## 6. 常见移植问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| Graph 加载失败 | Module Library 路径错误 | 检查固件路径 |
| Buffer 不通 | AFM 路由未配置 | 配置路由表 |
| 延迟过高 | Buffer Size 配置过大 | 调小 Buffer |
| 编译失败 | 缺少平台适配层 | 实现 PAL |
