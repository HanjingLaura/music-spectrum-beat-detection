from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .core import AnalysisResult


BG = (255, 255, 255)
INK = (28, 35, 43)
MUTED = (100, 112, 126)
GRID = (224, 229, 236)
BLUE = (42, 112, 184)
ORANGE = (217, 114, 49)
GREEN = (45, 145, 95)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _draw_axes(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], title: str, x_label: str, y_label: str) -> None:
    left, top, right, bottom = box
    draw.rectangle((left, top, right, bottom), outline=GRID, width=1)
    for k in range(1, 5):
        x = left + (right - left) * k / 5
        y = top + (bottom - top) * k / 5
        draw.line((x, top, x, bottom), fill=GRID, width=1)
        draw.line((left, y, right, y), fill=GRID, width=1)
    draw.text((left, 22), title, fill=INK, font=_font(24, bold=True))
    draw.text(((left + right) // 2 - 35, bottom + 34), x_label, fill=MUTED, font=_font(14))
    draw.text((16, (top + bottom) // 2 - 8), y_label, fill=MUTED, font=_font(14))


def _line_plot(
    x: np.ndarray,
    y: np.ndarray,
    path: str | Path,
    title: str,
    x_label: str = "Time (s)",
    y_label: str = "Amplitude",
    color: tuple[int, int, int] = BLUE,
    markers: np.ndarray | None = None,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 1100, 620
    margin_left, margin_top, margin_right, margin_bottom = 92, 78, 46, 92
    box = (margin_left, margin_top, width - margin_right, height - margin_bottom)
    image = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(image)
    _draw_axes(draw, box, title, x_label, y_label)

    left, top, right, bottom = box
    y_min, y_max = float(np.min(y)), float(np.max(y))
    if abs(y_max - y_min) < 1e-9:
        y_min -= 1
        y_max += 1

    max_points = 1800
    if len(x) > max_points:
        idx = np.linspace(0, len(x) - 1, max_points).astype(int)
        x_plot = x[idx]
        y_plot = y[idx]
    else:
        x_plot, y_plot = x, y

    x_min, x_max = float(x_plot.min()), float(x_plot.max())
    points = []
    for xv, yv in zip(x_plot, y_plot):
        px = left + (float(xv) - x_min) / max(1e-9, x_max - x_min) * (right - left)
        py = bottom - (float(yv) - y_min) / max(1e-9, y_max - y_min) * (bottom - top)
        points.append((px, py))
    if len(points) > 1:
        draw.line(points, fill=color, width=2)

    if markers is not None:
        for marker in markers:
            if x_min <= marker <= x_max:
                px = left + (float(marker) - x_min) / max(1e-9, x_max - x_min) * (right - left)
                draw.line((px, top, px, bottom), fill=ORANGE, width=2)

    draw.text((left, bottom + 10), f"{x_min:.1f}", fill=MUTED, font=_font(12))
    draw.text((right - 34, bottom + 10), f"{x_max:.1f}", fill=MUTED, font=_font(12))
    draw.text((left - 54, top - 4), f"{y_max:.2f}", fill=MUTED, font=_font(12))
    draw.text((left - 54, bottom - 8), f"{y_min:.2f}", fill=MUTED, font=_font(12))
    image.save(path)


def save_waveform(result: AnalysisResult, path: str | Path) -> None:
    _line_plot(result.times, result.signal, path, "Waveform", "Time (s)", "Amplitude", BLUE)


def save_spectrum(result: AnalysisResult, path: str | Path, max_freq: float = 5000.0) -> None:
    mask = result.spectrum_freqs <= max_freq
    freqs = result.spectrum_freqs[mask]
    magnitude = result.spectrum_magnitude[mask]
    bucket_count = min(1400, len(freqs))
    if bucket_count > 0:
        edges = np.linspace(0, len(freqs), bucket_count + 1).astype(int)
        freqs = np.array([freqs[start:end].mean() for start, end in zip(edges[:-1], edges[1:]) if end > start])
        magnitude = np.array([magnitude[start:end].max() for start, end in zip(edges[:-1], edges[1:]) if end > start])
    magnitude = np.log1p(80 * magnitude) / np.log1p(80)
    _line_plot(
        freqs,
        magnitude,
        path,
        "Frequency Spectrum (FFT)",
        "Frequency (Hz)",
        "Log magnitude",
        GREEN,
    )


def save_beat_detection(result: AnalysisResult, path: str | Path) -> None:
    _line_plot(
        result.onset_times,
        result.onset_envelope,
        path,
        f"Beat Detection: estimated BPM = {result.bpm:.1f}",
        "Time (s)",
        "Onset strength",
        BLUE,
        markers=result.beat_times,
    )


def save_spectrogram(result: AnalysisResult, path: str | Path, max_freq: float = 5000.0) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    freq_mask = result.stft_freqs <= max_freq
    mag = result.stft_magnitude[freq_mask, :]
    mag = np.log1p(mag)
    mag = mag / max(1e-9, mag.max())
    mag = np.flipud(mag)

    red = (255 * mag).astype(np.uint8)
    green = (170 * np.sqrt(mag)).astype(np.uint8)
    blue = (80 * (1 - mag)).astype(np.uint8)
    heat = np.dstack([red, green, blue])
    heat_img = Image.fromarray(heat, "RGB").resize((962, 430), Image.Resampling.BILINEAR)

    width, height = 1100, 620
    image = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(image)
    left, top = 92, 78
    image.paste(heat_img, (left, top))
    draw.rectangle((left, top, left + 962, top + 430), outline=GRID, width=1)
    draw.text((left, 22), "Spectrogram (STFT)", fill=INK, font=_font(24, bold=True))
    draw.text((width // 2 - 35, top + 468), "Time (s)", fill=MUTED, font=_font(14))
    draw.text((16, top + 190), "Frequency", fill=MUTED, font=_font(14))
    draw.text((left, top + 440), f"0.0", fill=MUTED, font=_font(12))
    draw.text((left + 920, top + 440), f"{result.duration:.1f}", fill=MUTED, font=_font(12))
    draw.text((left - 62, top - 4), f"{max_freq / 1000:.1f} kHz", fill=MUTED, font=_font(12))
    draw.text((left - 24, top + 420), "0", fill=MUTED, font=_font(12))
    image.save(path)


def save_pipeline_diagram(path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 1100, 420
    image = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(image)
    title_font = _font(24, bold=True)
    body_font = _font(16)
    draw.text((48, 28), "Processing Pipeline", fill=INK, font=title_font)
    steps = [
        ("WAV Input", "mono + normalize"),
        ("FFT / STFT", "frequency analysis"),
        ("Spectral Flux", "onset envelope"),
        ("Peak Picking", "beat timestamps"),
        ("BPM Estimate", "tempo result"),
    ]
    box_w, box_h = 170, 100
    start_x, y = 52, 155
    gap = 38
    for i, (heading, detail) in enumerate(steps):
        x = start_x + i * (box_w + gap)
        draw.rounded_rectangle((x, y, x + box_w, y + box_h), radius=12, fill=(245, 248, 252), outline=(190, 205, 220), width=2)
        draw.text((x + 18, y + 24), heading, fill=INK, font=_font(17, bold=True))
        draw.text((x + 18, y + 58), detail, fill=MUTED, font=body_font)
        if i < len(steps) - 1:
            ax = x + box_w + 8
            ay = y + box_h // 2
            draw.line((ax, ay, ax + gap - 18, ay), fill=BLUE, width=3)
            draw.polygon([(ax + gap - 18, ay - 7), (ax + gap - 18, ay + 7), (ax + gap - 7, ay)], fill=BLUE)
    image.save(path)


def save_all_plots(result: AnalysisResult, output_dir: str | Path) -> None:
    output_dir = Path(output_dir)
    save_waveform(result, output_dir / "waveform.png")
    save_spectrum(result, output_dir / "spectrum.png")
    save_spectrogram(result, output_dir / "spectrogram.png")
    save_beat_detection(result, output_dir / "beat_detection.png")
    save_pipeline_diagram(output_dir / "pipeline.png")
