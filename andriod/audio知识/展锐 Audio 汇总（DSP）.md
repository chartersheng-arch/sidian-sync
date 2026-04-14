# 一、展锐平台（DSP）架构

## Audio Hal

![](images/01.png)

### 主要由如下各模块构成：

策略执行模块：

− audio_module、audio_stream：HAL 层 common code，实现 Android Audio HAL 

标准接口，包含输入/输出数据流控制，设备控制等逻辑。

− audio_voice：根据音频架构定制的通话相关流程控制，提供通话相关控制接口。

− device_manager：设备切换逻辑控制。

策略定制模块：

audio_platform：根据音频架构定制Unisoc UNISOC的参数、设备等相关策略。

音频子功能模块：

audio_external：包含 FM、AGDSPUSB、HIFI、SMARTAMP 等子功能，该子功能依赖audio_hw模块的标准接口。

不依赖 HAL 层的独立功能模块：

device_route：属于设备控制模块（device_manager），负责解析audio_route.xml，以及按 HAL层要求控制相关 kcontrol

libunisocaudioparam.so：音频参数库，负责解析所有参数相关 XML 文件，以及按照 HAL 层要求下发相关参数选项。

其他外部库或工具：音频维测库、音频算法库、pcm_dump、audio_utils。

### 文件

![](images/02.png)

### 关键结构体

![](images/03.png)

### 单独编译hal so

UMS9230：

---

---

---

---

UMS9632：

---

---

---

---

### 蓝牙播放音乐

![](images/04.jpg)

原生 Bluetooth Audio HAL 的代码路径：
packages/modules/Bluetooth/system/audio_bluetooth_hw/

展锐 Bluetooth Audio HAL 的代码路径：
vendor/sprd/modules/audio/vendor/a2dp_offload_hw/

App 发起播放时，数据到 framework 有一个区分：

---

---

展锐 Bluetooth Audio HAL 既可以是普通播放，也可以是 offload 播放，而原生 Bluetooth Audio HAL 只能是普通播放。

抓取到的数据保存在设备的 data/vendor/ylog/Audio_track.pcm。

---

---

## Audio Driver

![](images/05.png)

# 二、audio BringUp流程（I2C）

Somalia 5G config图

![](images/06.png)

## 2.1 移除平台默认的外置PA

### 2.1.1 删除驱动配置

UMS9632平台上，默认使用ucp1301作为外置PA

删除如下配置

kernel6.6/unisoc/arch/arm64/boot/dts/sprd/ums9632-base.dts

删除i2c节点

kernel/unisoc/arch/arm64/configs/sprd_gki_qogirn6.fragment

修改如下：

CONFIG_UNISOC_AUDIO_CODEC_UCP1301=y

CONFIG_UNISOC_AUDIO_CODEC_UCP1201 is not set

注意，ucp1301驱动没有单独ko，集成在audio-codec.ko里了，只要宏去掉了，相关代码逻辑就不参与编译了

### 2.1.2 smartamp算法关闭

device/sprd/qogirn5/ums9632_1h10/module/audio/md.mk

增加配置：

+AUDIO_SMARTAMP_CONFIG = unsupport

修改mk后：

1）在没有创建客制化参数目录时，编译默认使用的参数就从（xxxx表示平台，如qogirn5）

   device/sprd/vnd_mpool/module/odm/audio/msoc/xxxx/system/etc/audio_param/unisoc_default

   调整为目录

   device/sprd/vnd_mpool/module/odm/audio/msoc/xxxx/system/etc/audio_param/unisoc_smartamp

2）如有创建客制化参数目录时，编译默认使用的参数就从（xxxx表示平台，如qogirn5；yyyy表示board，如ums9632_1h10）

   device/sprd/xxxx/yyyy/system/etc/audio_param/unisoc_default

   改为

   device/sprd/xxxx/yyyy/system/etc/audio_param/unisoc_smartamp

3）编译后的package写到设备中，其设备下的目录

   odm/etc/audio_params/unisoc/

   不会包含dep_smartamp.xml；且audioparam_config.xml不应该包含以下内容：SmartAmpSupport="xxx" SmartAmpUseCase="xxx"

关系到关闭算法后，AudioTool调音工具能否正确连接读写参数

vendor/sprd/modules/audio/vendor/audio-unit/audioscenetest/

vendor/sprd/modules/audio/vendor/audio-param/

vendor/sprd/modules/audio/vendor/audio-hal/

需要删除对应平台的以下宏定义：

"-DUNISOC_SMARTAMP_SUPPORT"

## 2.2 bootloader

I2C 型外置PA的工作状态通常由I2C总线控制，因此需要正确配置 I2C 属性。展锐平台默认已经对各组 I2C 总线做了正确的配置，因此对于I2C 型外置PA 一般无需修改 Bootloader。

## 2.3 Kernel

### 2.3.1 DTS

添加base.dts

添加到对应项目的overlay.dtsi

### 2.3.2 3rd Driver

将第三方驱动代码移植到 kernel6.6/unisoc-modules/vender/audio/路径下。

kernel6.6/unisoc-modules 路径与 kernel6.6/unisoc/drivers/unisoc_platform/nest路径做了软链接，因此这两个路径下的文件是完全一致的。

三方单仓需额外拉取

![](images/07.png)

### 2.3.3 Kconfig和Makefile

subdir-ccflags需添加I$(srctree)/drivers/unisoc_platform/nest/audio/sprd/include路径

drivers/unisoc_platform路径下的Kconfig文件，将三方的kconfig文件包含进平台

drivers/unisoc_platform路径下的Makefile文件，将三方的Makefile文件包含进平台

### 2.3.4 开启config

fragment中添加config

![](images/08.png)

### 2.3.5 ko打包及加载

unisoc_bazels的bzl文件中"module_outs"添加三方ko文件

### 2.4 modules.load

kernel/devices/qogirn5中modules.load

其中"export RECOVERY_KERNEL_MODULES"和"export BOARD_VENDOR_KERNEL_MODULES"添加三方ko名

### 2.5 HAL

# 三、Audio场景

# 四、Audio调试方式

## 4.1 audiodump抓取

### Fw dump

adb命令

FW dump抓取命令及dump文件存放目录

工程模式

![](images/09.png)

勾选相关FW节点，然后点击“SET”完成设置

adb shell setprop audio.dump.switch 7

adb shell setprop audio.dump.switch 0

保存路径：/data/miuilog/bsp/audio/traces

### Hal dump

![](images/10.png)

![](images/11.png)

### Dsp dump

步骤 1 进入工程模式*#*#83781#*#*，打开 YLog 设置界面。

步骤 2 点击“DEBUG&LOG > YLog > 场景选择 > Audio”

![](images/12.png)

步骤 3 点击“DEBUG&LOG > YLog > 关闭“CP Log存储到PC”> Audio”

![](images/13.png)

复现问题，DSP数据会保存在设备的ylog/audio/ag_.log

要将抓取到的以 .log 结尾的 DSP dump 数据文件，转换为可用的 PCM 数据。

所需工具： Logel （可在 Uni-Support 网站 > 工具管理 > 搜索 Logel 找到并下载）

操作步骤：

![](images/14.png)

---

---

---

步骤 3 点击 “Transfer” 进行转换。

转换成功后会弹出 AudioDsp 文件夹，存放了解析出来的 PCM 文件。文件名会显示编号（0001, 0002, 0003...），与 6.3 节点说明中的编号对应，并显示采样率，如 8kHz、16kHz、32kHz 等。其余的数据格式固定为 Signed 16bit、小端、单声道。

说明：如果录音场景打开了 NR 算法，也可以抓取 DSP log，解析出如下 dump 文件：

---

---

DSP 内部的数据节点可以从调音工具 AudioTool 中查看（Uni-Support 网站 > 工具管理 > 搜索 AudioTool）。分析具体问题时，建议以 AudioTool 的实际显示为准。

![](images/15.png)

图中的红色线条代表上行，蓝色线条代表下行，关键节点如下（只需关注图中带圈的节点）：

---

---

---

---

---

---

---

---

---

---

说明：VoIP 模式时，DSP 和 HAL 交互数据，而不是和网络端交互，因此 VoIP 时可以不关注①和④这两个节点。②、⑦、③节点是分析下行问题（下行卡顿、杂音、无声和大小声等）的关键节点，较为常用，建议重点关注。

DSP 字符串 log 功能默认开启，可以使用 audioutils 命令调整 log 开关状态，命令如下：

adb shell audioutils_client string_log_enable=false/true //false: 关闭, true: 开启

DSP 字符串 log 等级，可以使用 audioutils 命令调整，命令示例如下：

adb shell audioutils_client string_log_level=5

## 4.2 Dump寄存器

### log等级

# FAQ案例