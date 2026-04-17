# 场景LOG专项

> 来源：https://longcheer.feishu.cn/wiki/DLyEwYJifidA7lkuiqIcPA3unQK
> 同步时间：2026-04-16 11:57

---

# 场景LOG专项

### setForceUse

===> mPhoneState

system/media/audio/include/system/audio-base.h

prebuilts/vndk/v30/arm64/include/system/media/audio/include/system/audio-base.h

1. 

 ====> config

1. 

同：frameworks/base/media/java/android/media/AudioSystem.java

1. 

===>usage

1. 

同：frameworks/base/media/java/android/media/AudioSystem.java

1. 

        



### 旋转双声道

AudioSystem: +setParameters(): rotation=90

AudioSystem: +setParameters(): rotation=270



audio_hw_primary: adev_set_parameters: enter: rotation=270 /// 此处会左右声道切换

audio_hw_primary: adev_set_parameters: enter: rotation=0

audio_hw_primary: adev_set_parameters: enter: rotation=90

audio_hw_primary: adev_set_parameters: enter: rotation=270 /// 此处会左右声道切换

audio_hw_primary: adev_set_parameters: enter: rotation=90

audio_hw_primary: adev_set_parameters: enter: rotation=0

### sm6225内核日志

在特定的文件中启用内核日志

adb root  

adb shell 

echo –n “file <filename> +p” > /sys/kernel/debug/dynamic_debug/control 

禁用特定文件echo中的内核日志

echo –n “file <filename> -p” > /sys/kernel/debug/dynamic_debug/control 

收集日志

adb shell cat  /proc/kmsg  | tee  kernel.txt 

启用日志记录一个特定的C或C++文件

Change 【//#define LOG_NDEBUG 0】 to #define LOG_NDEBUG 0 

启用java文件上的日志；根据源文件，设置标志，以便日志、Log.d等，日志行被执行

使用ldblogcat命令收集用户空间日志

adb logcat –v threadtime | tee  logcat.txt

编解码器寄存器转储

adb shell cat /d/regmap/wcd937x-slave.*-wcd937x_csr/registers > codecreg.txt 

MBHC校准数据

adb shell cat /sys/kernel/debug/wcd9xxx_mbhc > mbhc_data.txt



### 开黑语音变音

pubg开黑时，游戏加速器的变声功能在游戏最小化后功能消失

130|spes:/ # logcat | grep "setgameparameters"

//游戏加速设置的变声器（voice chane）设置lady模式，每当点开游戏加速工具箱，就会打印 如下log

1. 

//当最小化游戏后，打印如下log, 可以看到open状态是off， mode不变，说明游戏加速中的变声mode已经关闭，

而非切换成原声，语音变成默认，

1. 

### 录音权限

通话语音上行无声问题：

若排查测试机下行节点无声，需要继续排查辅助机上行节点是否正常；

若正常，再排查apk问题。

抓取audioflinger dump

1.排查测试机上行0x1536节点和0x1586节点有没有异常语音

2.如异常，缺失指定语音，检查log

3.log中检查 audio_route,acdb_id,AudioFlinger,AudioRecord

1. 

1. 



