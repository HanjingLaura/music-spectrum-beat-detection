# 音乐频谱分析与节拍检测

本项目是数字信号处理课程专题报告的配套代码，使用 Python 对音乐音频进行频谱分析、短时傅里叶变换分析和节拍检测。项目可以生成一段免版权的合成测试音频，也可以分析用户自己提供的 WAV 音频文件。

项目目标不是简单画图，而是根据音频信号计算频谱变化，检测节拍点，并估计音乐 BPM。

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

## 输出文件夹说明

如果运行过多次测试，可能会看到类似目录：

```text
outputs/
outputs_bpm90/
outputs_bpm150/
```

这些目录都是运行代码后自动生成的实验输出：

- `outputs/`：默认 demo 测试结果
- `outputs_bpm90/`：90 BPM demo 测试结果
- `outputs_bpm150/`：150 BPM demo 测试结果

它们不是核心代码，主要用于查看实验结果和放入报告。

## 开源上传建议

上传到 GitHub / Gitee 时，建议保留：

- `main.py`
- `requirements.txt`
- `README.md`
- `.gitignore`
- `data/README.md`
- `outputs/.gitkeep`
- `music_spectrum_beat_detection/`

不建议上传：

- 商业音乐原文件
- 大体积音频文件
- 临时生成的输出文件夹

如果需要展示效果，可以上传少量自录音频、免版权音频，或者只上传生成后的图片。

## 数据与版权说明

开源仓库中不建议上传完整商业歌曲。可以使用：

- 本项目自动生成的合成测试音频
- 自己录制的拍手、敲击、节拍器声音
- 免版权音乐或公开数据集音频

如果课程报告中使用了商业歌曲进行本地测试，建议只展示分析结果，不把原始音频上传到公开仓库。
