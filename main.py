from __future__ import annotations

import argparse
from pathlib import Path

from music_spectrum_beat_detection.core import analyze_wav, generate_demo_audio
from music_spectrum_beat_detection.plotting import save_all_plots


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Music spectrum analysis and beat detection")
    parser.add_argument("--input", type=Path, default=None, help="Path to a WAV audio file")
    parser.add_argument("--out", type=Path, default=Path("outputs"), help="Output directory")
    parser.add_argument("--demo", action="store_true", help="Generate and analyze a demo audio track")
    parser.add_argument("--bpm", type=int, default=120, help="BPM used when generating demo audio")
    parser.add_argument("--duration", type=float, default=18.0, help="Demo audio duration in seconds")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    if args.demo or args.input is None:
        audio_path = args.out / "demo_track.wav"
        generate_demo_audio(audio_path, bpm=args.bpm, duration=args.duration)
        print(f"Generated demo audio: {audio_path}")
    else:
        audio_path = args.input

    result = analyze_wav(audio_path)
    save_all_plots(result, args.out)

    print(f"Input audio: {audio_path}")
    print(f"Sample rate: {result.sample_rate} Hz")
    print(f"Duration: {result.duration:.2f} s")
    print(f"Detected beats: {len(result.beat_times)}")
    print(f"Estimated BPM: {result.bpm:.1f}")
    print(f"Figures saved to: {args.out.resolve()}")


if __name__ == "__main__":
    main()
