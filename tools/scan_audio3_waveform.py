import wave
import numpy as np

with wave.open('assets/firule/audio_3_cierre_silabas.wav', 'rb') as w:
    sr = w.getframerate()
    frames = w.readframes(w.getnframes())
    audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32)

step = int(0.1 * sr)
print(f"Total duration: {len(audio)/sr:.2f}s")
for i in range(0, len(audio), step):
    t = i / sr
    chunk = audio[i:i+step]
    rms = np.sqrt(np.mean(chunk**2))
    peak = np.max(np.abs(chunk))
    bar = '#' * int(min(50, rms / 300))
    print(f"{t:5.2f}s | RMS: {rms:6.1f} | Peak: {peak:6.0f} | {bar}")
