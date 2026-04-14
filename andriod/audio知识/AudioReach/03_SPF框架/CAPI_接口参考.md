# CAPI v2 — Common Audio Processor Interface

## 1. CAPI 定位

CAPI v2 是 **Module 与 SPF Graph Engine 之间的标准接口**，保证：
- Module 可跨平台复用
- Graph Builder 可统一配置
- 调试工具可通用访问 Module 参数

## 2. 核心数据结构

### 2.1 Module Handle

```c
typedef struct capi_v2 {
    capi_v2_vtbl_t* vtbl;  // 函数表指针
} capi_v2_t;
```

### 2.2 函数表

```c
typedef struct capi_v2_vtbl {
    capi_v2_err_t (*init)(capi_v2_t* _this,
                          capi_v2_proplist_t* init_proplist);
    capi_v2_err_t (*process)(capi_v2_t* _this,
                             capi_v2_buf_t* input[],
                             capi_v2_buf_t* output[]);
    capi_v2_err_t (*set_param)(capi_v2_t* _this,
                               uint16_t param_id,
                               capi_v2_buf_t* params);
    capi_v2_err_t (*get_param)(capi_v2_t* _this,
                               uint16_t param_id,
                               capi_v2_buf_t* params,
                               uint32_t* size_is);
    capi_v2_err_t (*end)(capi_v2_t* _this);
} capi_v2_vtbl_t;
```

### 2.3 Buffer 结构

```c
typedef struct {
    void*  data;       // 数据指针
    uint32_t max_size; // Buffer 最大长度
    uint32_t actual_size; // 实际数据长度
} capi_v2_buf_t;
```

## 3. init() — 初始化

```c
capi_v2_err_t capi_v2_init(capi_v2_t* _this,
                           capi_v2_proplist_t* init_proplist);
```

**功能:** 创建 Module 实例，初始化内部状态

**常用初始化属性:**
| 属性 | 说明 |
|------|------|
| `CAPI_V2_SAMPLE_RATE` | 采样率 |
| `CAPI_V2_CHANNEL_COUNT` | 通道数 |
| `CAPI_V2_BIT_DEPTH` | 位深 |
| `CAPI_V2_MAX_BUFFER_SIZE` | 最大 Buffer |

## 4. process() — 数据处理

```c
capi_v2_err_t capi_v2_process(capi_v2_t* _this,
                              capi_v2_buf_t* input[],
                              capi_v2_buf_t* output[]);
```

**功能:** 处理输入数据，产生输出数据

**输入/输出规则:**
- `input[]`: 输入 Buffer 数组
- `output[]`: 输出 Buffer 数组
- Buffer 可能是 in-place (输入输出共享 Buffer)
- 返回 `CAPI_V2EOK` 表示处理成功

## 5. set_param() / get_param() — 参数访问

```c
capi_v2_err_t capi_v2_set_param(capi_v2_t* _this,
                                uint16_t param_id,
                                capi_v2_buf_t* params);

capi_v2_err_t capi_v2_get_param(capi_v2_t* _this,
                                uint16_t param_id,
                                capi_v2_buf_t* params,
                                uint32_t* size_is);
```

**常用参数 ID:**
| ID | Module | 说明 |
|----|--------|------|
| `0x10001` | AEC | 启用/禁用 |
| `0x10002` | NS | 降噪强度 |
| `0x10003` | Gain | 增益值 |
| `0x10004` | EQ | EQ 曲线 |
| `0x10005` | Resampler | 重采样比 |

## 6. end() — 资源释放

```c
capi_v2_err_t capi_v2_end(capi_v2_t* _this);
```

**功能:** 释放 Module 内部资源，不销毁 Module 实例

## 7. 媒体格式协商

```c
typedef enum {
    CAPI_V2_PCM_FORMAT        // PCM
    CAPI_V2_ENCODED_FORMAT    // 编码数据
} capi_v2_data_format_t;

typedef union {
    capi_v2_pcm_format_t pcm;
    capi_v2_encoded_format_t encoded;
} capi_v2_media_format_t;
```

## 8. 错误码

| 错误码 | 说明 |
|--------|------|
| `CAPI_V2EOK` | 成功 |
| `CAPI_V2EINVAL` | 无效参数 |
| `CAPI_V2ENOMEMORY` | 内存不足 |
| `CAPI_V2EFAILED` | 通用失败 |
| `CAPI_V2ENOTREADY` | 未就绪 |

## 9. Module 实现模板

```c
// 1. 定义 Module 私有数据
typedef struct {
    uint32_t sample_rate;
    uint16_t channels;
    float gain;
    bool enabled;
} my_module_data_t;

// 2. 实现 init
static capi_v2_err_t my_init(capi_v2_t* _this,
                              capi_v2_proplist_t* proplist) {
    my_module_data_t* p = malloc(sizeof(my_module_data_t));
    // 初始化...
    _this->vtbl = &my_vtbl;
    return CAPI_V2EOK;
}

// 3. 实现 process
static capi_v2_err_t my_process(capi_v2_t* _this,
                                 capi_v2_buf_t* input[],
                                 capi_v2_buf_t* output[]) {
    // 信号处理逻辑
    return CAPI_V2EOK;
}

// 4. 函数表
static capi_v2_vtbl_t my_vtbl = {
    my_init,
    my_process,
    my_set_param,
    my_get_param,
    my_end
};
```

## 10. 调试建议

- `set_param` / `get_param` 用于动态调试，避免重新加载 Graph
- 优先使用已有参数 ID，新 ID 需在 Graph 配置中声明
- Module 应实现所有 `vtbl` 函数，即使只是返回 `CAPI_V2EOK`
