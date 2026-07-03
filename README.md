# 音乐频谱分析与节拍检测

本项目是数字信号处理课程专题报告的配套代码，使用 Python 对音乐音频进行频谱分析、短时傅里叶变换分析和节拍检测。项目可以生成一段免版权的合成测试音频，也可以分析用户自己提供的 WAV 音频文件。

项目目标不是简单画图，而是根据音频信号计算频谱变化，检测节拍点，并估计音乐 BPM。

项目仓库：[https://github.com/HanjingLaura/music-spectrum-beat-detection](https://github.com/HanjingLaura/music-spectrum-beat-detection)

## 功能

- 读取 WAV 音频并转换为单声道浮点信号
- 绘制音频时域波形图
- 使用 FFT 绘制整体频谱图
- 使用 STFT 绘制声谱图
- 基于谱通量检测节拍点
- 根据节拍间隔估计 BPM
- 生成可放入课程报告的 PNG 实验图

## 项目结构

```text
music-spectrum-beat-detection/
├── main.py
├── requirements.txt
├── README.md
├── .gitignore
├── data/
│   └── README.md
├── outputs/
│   └── .gitkeep
└── music_spectrum_beat_detection/
    ├── __init__.py
    ├── core.py
    └── plotting.py
```

## 环境要求

- Python 3.9 或更高版本
- numpy
- Pillow

安装依赖：

```bash
pip install -r requirements.txt
```

也可以使用虚拟环境：

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 使用方法

### 1. 生成默认测试音频并分析

直接运行：

```bash
python main.py --demo
```

程序会自动生成一段合成测试音频，并把分析结果保存到 `outputs/` 文件夹中。

默认输出包括：

- `demo_track.wav`：程序生成的测试音频
- `waveform.png`：时域波形图
- `spectrum.png`：FFT 频谱图
- `spectrogram.png`：STFT 声谱图
- `beat_detection.png`：节拍检测结果图
- `pipeline.png`：系统处理流程图

### 2. 指定不同 BPM 的测试音频

例如生成并分析 90 BPM 的测试音频：

```bash
python main.py --demo --bpm 90 --duration 18 --out outputs_bpm90
```

例如生成并分析 150 BPM 的测试音频：

```bash
python main.py --demo --bpm 150 --duration 18 --out outputs_bpm150
```

这些命令可以用来验证程序不是写死结果，而是会根据音频节奏变化输出不同 BPM。

### 3. 分析自己的 WAV 音频

把自己的 WAV 文件放入 `data/` 文件夹，例如：

```text
data/my_music.wav
```

然后运行：

```bash
python main.py --input data/my_music.wav --out outputs_my_music
```

运行结束后，`outputs_my_music/` 中会生成该音频对应的波形图、频谱图、声谱图和节拍检测图。

注意：当前代码主要支持 PCM WAV 文件。如果你的音频是 MP3、M4A 或 FLAC，建议先转换为 WAV 再运行。

### 4. 查看命令参数

可以使用：

```bash
python main.py --help
```

常用参数说明：

| 参数 | 说明 |
|---|---|
| `--demo` | 生成合成测试音频并分析 |
| `--input` | 指定要分析的 WAV 音频路径 |
| `--out` | 指定输出目录 |
| `--bpm` | 生成 demo 音频时使用的 BPM |
| `--duration` | 生成 demo 音频的时长，单位为秒 |

## 方法原理

程序的节拍检测流程如下：

1. 读取 WAV 音频，转换为单声道信号。
2. 对音频进行归一化处理。
3. 使用短时傅里叶变换 STFT 分析每一帧的频谱。
4. 计算相邻帧频谱幅值的正向变化，得到谱通量曲线。
5. 对谱通量曲线进行平滑。
6. 通过阈值和局部峰值检测找出节拍点。
7. 根据相邻节拍点间隔估计 BPM。

BPM 估计公式：

```text
BPM = 60 / median(beat_interval_seconds)
```

## 示例结果

使用默认测试音频运行：

```bash
python main.py --demo
```

一次示例输出：

```text
Generated demo audio: outputs\demo_track.wav
Input audio: outputs\demo_track.wav
Sample rate: 22050 Hz
Duration: 18.00 s
Detected beats: 35
Estimated BPM: 117.5
Figures saved to: ...\outputs
```

由于默认测试音频设定为 120 BPM，检测结果 117.5 BPM 与设定值比较接近，说明程序能够根据音频节奏进行估计。