# Audio模块研发手册

> 来源：[飞书文档](https://longcheer.feishu.cn/wiki/wikcnZlqdnyAsOPegsMa3us1HZc)
> 文档标题：Audio模块研发手册

---

## 版本历史

| 版本号 | 修改日期 | 作者 | 审核 | 备注 |
|--------|----------|------|------|------|
| V0.1 | 2022/5/27 | 李小娜，程福勇，倪家胜，党家乐、石康军、杨妍 | 王法杰 | 初版制成 |
| V0.2 | 2023/4/17 | 李小娜 | - | 1.增加5.3.6 2.增加5.5~5.21 3.增加九、稳定分支Audio通路新增的评审流程 4.增加4.5 |
| V0.3 | 2023/7/18 | 李小娜 | - | 1.增加5.22~5.27 2.增加十、三方audio问题处理流程 |
| v0.4 | 2023/12/21 | 李小娜，程福勇，石康军 | - | 1.整理5.13~5.27 2.增加5.28 3.增加3.5.1 高通平台工厂测试集成 |

---

## 一、音频基础知识

### 1.1 音频定义

音频是个专业术语，音频一词已用作一般性描述音频范围内和声音有关的设备及其作用。

人类能够听到的所有声音都称之为音频。声音被录制下来后通过数字音乐软件处理，或是制作成CD，声音不会产生变化，因为CD本来就是音频文件的一种类型，而音频只是储存在计算机里的声音。

计算机再加上相应的音频卡，可录制任何声音，声音的声学特性如音的高低等都可以用计算机硬盘文件的方式储存下来，而计算机储存的声音就是音频。

人耳可以听到的声音频率在20Hz~20kHz之间。

### 1.2 模拟信号与数字信号

大家都承认是一个数码时代，为追求优良的音质很多人做出了不懈的努力。随着数码时代的来临，数字信号比模拟信号优越已成为共识。

**模拟信号**：任何我们可以听见的声音经过音频线或话筒的传输都是一系列的模拟信号。模拟信号是我们可以听见的。

**数字信号**：用一堆数字记号(其实只有二进制的1和0)来记录声音，而不是用物理手段来保存信号。我们实际上听不到数字信号。

### 1.3 模拟时代 vs 数码时代

- **模拟时代**：把原始信号以物理方式录制到磁带上，然后加工、剪接、修改，最后录制到磁带、LP等。每一步都会损失一些信号。
- **数码时代**：第一步就把原始信号录成数码音频资料，用硬件设备或各种软件进行加工处理，几乎不会有任何损耗。

### 1.4 音频参数说明

1. **响度（Loudness）**：人类可以感知到的各种声音的大小，也就是音量。响度与声波的振幅有直接关系。

2. **音调（Pitch）**：与声音的频率有关系，当声音的频率越大时，人耳所感知到的音调就越高，否则就越低。

3. **音色(Quality)**：同一种乐器，使用不同的材质来制作，所表现出来的音色效果是不一样的，这是由物体本身的结构特性所决定的。

4. **样本(Sample)**：采样的初始资料，比如一段连续的声音波形。

5. **采样器(Sampler)**：将样本转换成终态信号的关键。它可以是一个子系统，也可以指一个操作过程，甚至是一个算法。

6. **量化(Quantization)**：采样后的值还需要通过量化，也就是将连续值近似为某个范围内有限多个离散值的处理过程。

7. **编码(Coding)**：计算机的世界里，所有数值都是用二进制表示的，因而我们还需要把量化值进行二进制编码。

8. **采样率（samplerate）**：采样就是把模拟信号数字化的过程。根据奈奎斯特理论，采样频率只要不低于音频信号最高频率的两倍，就可以无损失地还原原始的声音。

   ![图1-采样信号](../../assets res/images/img1.png)

   常用的音频采样频率有：8kHz、11.025kHz、22.05kHz、16kHz、32kHz、37.8kHz、44.1kHz、48kHz、96kHz、192kHz等。

9. **量化精度（位宽）**：常见的位宽有：8bit、16bit、24bit、32bit。位数越多，表示得就越精细，声音质量自然就越好。

   ![图2-量化](../../assets res/images/img2.png)

10. **声道数（channels）**：单声道（Mono）和双声道（Stereo）比较常见。

11. **音频帧（frame）**：在实际的应用中，一般约定俗成取2.5ms~60ms为单位的数据量为一帧音频。通常用20ms为一帧。

    假设某音频信号是采样率为8kHz、双通道、位宽为16bit，20ms一帧，则一帧音频数据的大小为：
    ```
    int size = 8000 x 2 x 16bit x 0.02s = 5120 bit = 640 byte
    ```

12. **常见的音频编码方式**：PCM 和 ADPCM，这些数据代表着无损的原始数字音频信号。

13. **常见的音频压缩格式**：MP3，AAC，OGG，WMA，Opus，FLAC，APE，M4A，AMR，AC3，E-AC-3，AIFF，DSF，DFF，WAV等

14. **奈奎斯特采样理论**："当对被采样的模拟信号进行还原时，其最高频率只有采样频率的一半"。

---

## 二、Audio系统框架

Audio系统框架：**Application 层 → Framework 层 → Libraries 层 → HAL 层 → Tinyalsa 层 → Kernel部分 → Audio Devices**

![图3-Audio系统框架](../../assets res/images/img3.png)

### 2.1 Application 层

应用层，音乐播放器软件等

### 2.2 Framework 层

Android也提供了另两个相似功能的类，即AudioTrack和AudioRecord。

MediaPlayerService内部的实现就是通过它们来完成的。Android系统还为我们控制音频系统提供了AudioManager、AudioService及AudioSystem类。

### 2.3 Libraries 层

Framework只是向应用程序提供访问Android库的桥梁，具体功能放在库中完成。

1. frameworks/av/media/libmedia【libmedia.so】
2. frameworks/av/services/audioflinger【libaudioflinger.so】
3. frameworks/av/media/libmediaplayerservice【libmediaplayerservice.so】

### 2.4 HAL 层

硬件抽象层是AudioFlinger直接访问的对象。音频方面的硬件抽象层主要分为两部分，即AudioFlinger和AudioPolicyService。

HAL层的任务是将AudioFlinger/AudioPolicyService真正地与硬件设备关联起来。

### 2.5 Tinyalsa 层

源码在external/tinyalsa目录下：tinyplay/tinycap/tinymix，这些用户程序直接调用alsa用户库接口来实现放音、录音、控制。

### 2.6 Kernel部分

#### 6-1 ALSA（Advanced Linux Sound Architecture）

- **Native ALSA Application**：tinyplay / tinycap / tinymix
- **ALSA Library API**：alsa用户库接口，常见有tinyalsa、alsa-lib
- **ALSA CORE**：向上提供逻辑设备（PCM / CTL / MIDI / TIMER /…）系统调用，向下驱动硬件设备
- **ASoC CORE**：为了更好支持嵌入式系统和应用于移动设备的音频codec的一套软件体系
- **Hardware Driver**：音频硬件设备驱动，由三大部分组成：Machine / I2S / DMA / CODEC

#### 6-2 ASoC（ALSA System on Chip）

ASoC被分为**Machine**、**Platform**和**Codec**三大部分。

![图4-ASoC架构](../../assets res/images/img4.png)

##### Machine

用于描述设备组件信息和特定的控制如耳机/外放等。Machine驱动负责Platform和Codec之间的耦合以及部分和设备或板子特定的代码。

##### Platform

用于实现平台相关的DMA驱动和音频接口等。一般是指某一个SoC平台，比如MT6765、MT6761、SDM6225、JR510等。

主要处理两个问题：DMA引擎和SoC集成的PCM、I2S、AC97、SoundWire和SLIMbus数字接口控制。

##### Codec

用于实现平台无关的功能。如寄存器读写接口，音频接口，各widgets的控制接口和DAPM的实现等。

在移动设备中Codec的作用可以归结为四种：
- A）对PCM等信号进行D/A转换
- B）对Mic、Linein或者其他输入源的模拟信号进行A/D转换
- C）对音频通路进行控制
- D）对音频信号做出相应的处理

### 2.7 DAPM (Dynamic Audio Power Management)

DAPM是为了使基于linux的移动设备上的音频子系统，在任何时候都工作在最小功耗状态下。

### 2.8 Audio Devices 部分

| 设备 | 说明 |
|------|------|
| Headphone | 头戴耳机，音频输出 |
| Headset | 头戴耳机+microphone，支持输出和录音输入 |
| Speaker | 扬声器，外放，音频输出 |
| Receiver | 听筒，受话器，语音输出 |
| Microphone | 送话器，麦克，录音输入 |
| Main mic | 主MIC，用于通话输入 |
| Second mic | 耳机MIC的语音输入 |
| Sub mic | 副MIC，用来通话时降噪 |

---

## 三、名词解释

| 缩写 | 全称 | 说明 |
|------|------|------|
| ALSA | Advanced Linux Sound Architecture | linux内核音频架构 |
| ASoC | ALSA System on Chip | - |
| Codec | Coder / Decoder | 音频编解码器 |
| I2C/SPI | - | cpu与codec/smartpa之间的控制接口/总线 |
| I2S/PCM/AC97/SLIMBus/TDM/PDM | - | 传输音频数据 |
| DAI | Digital Audio Interface | 数字音频接口 |
| DAC | Digit to Analog Conversion | 数模转换器 |
| ADC | Analog to Digit Conversion | 模数转换器 |
| DSP | Digital Signal Process | 数字信号处理器 |
| Mixer | - | 混音器，将多个输入混合到输出 |
| Mux | multiplexer | 多路复用器，只能选择一个输出 |
| Mute | - | 静音 |
| PMIC | Power Management IC | 电源管理集成电路 |
| WB | Wideband | 宽带编码范围50~7000Hz |
| NB | Narrowband | 窄带编码范围300~3400Hz |
| DAPM | Dynamic Audio Power Management | 动态音频电源管理 |
| SRC | Sample Rate Convertor | 采样率转换 |
| SVA | Snapdragon Voice Activation | - |
| Voice UI | - | 语音用户界面 |

---

## 四、Voice Wake Up

### 4.1 准备工作

### 4.2 代码修改

#### 2.1 Kernel driver移植

主要Bring up步骤

#### 2.2 Mixer paths配置

#### 2.3 音频参数acdb data文件修改

### 4.3 烧录

### 4.4 Check audio通路

- 4.1 听筒测试
- 4.2 喇叭测试
- 4.3 耳机测试
- 4.4 主MIC测试
- 4.5 副MIC测试
- 4.6 耳机MIC测试

### 4.5 DTSI静态检测

参考：[工厂测试集成文档](https://wayawbott0.f.mioffice.cn/docx/doxk4FbrMlwXRsPLyPOy9ZkKidf)

![img5](../../assets res/images/img5.png)
![img6](../../assets res/images/img6.png)
![img7](../../assets res/images/img7.png)
![img8](../../assets res/images/img8.png)
![img9](../../assets res/images/img9.png)
![img10](../../assets res/images/img10.png)
![img11](../../assets res/images/img11.png)
![img12-QACT设置](../../assets res/images/img12.png)

---

## 五、PA Bring Up（以Awinic的aw87390为例）

### 5.1 准备工作

### 5.2 代码修改

#### 2.1 驱动代码移植及dts配置

#### 2.2 项目配置文件修改

#### 2.3 bin文件配置

#### 2.4 通路配置

#### 2.5 参考电路图，配置MIC mode

#### 2.6 音频参数提交

#### 2.7 驱动移植有效性验证

### 5.3 烧录

### 5.4 Check audio通路

- 4.1 主mic到听筒
- 4.2 副mic到喇叭
- 4.3 耳机MIC到听筒
- 4.4 耳机MIC到耳机

---

## 六、高通平台差异

同高通，差异部分主要从下面几个方面介绍。

---

## 七、稳定分支Audio通路新增的评审流程

（内容待补充）

---

## 八、术语表

（见上方名词解释第三节）

---

## 九、三方audio问题处理流程

（内容待补充）
