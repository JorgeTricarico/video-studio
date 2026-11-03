import soundfile as sf
import numpy as np

data, sr = sf.read("assets/firule/tail_audio_1.m4a")
duration = len(data) / sr
print(f"Tail duration: {duration:.3f} s, sr: {sr}")

# Let's divide into 0.5s windows and calculate RMS energy
win = int(0.2 * sr)
print("Time (orig) | Time (tail) | RMS energy")
for i in range(0, len(data), win):
    chunk = data[i:i+win]
    rms = np.sqrt(np.mean(chunk**2))
    t_tail = i / sr
    t_orig = 107.0 + t_tail
    if rms > 0.01:
        print(f"{t_orig:6.2f}s    | {t_tail:6.2f}s    | {rms:.4f}")
