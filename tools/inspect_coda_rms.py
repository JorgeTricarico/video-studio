import wave
import numpy as np

with wave.open("assets/firule/canticuenticos_coda.wav", "rb") as w:
    sr = w.getframerate()
    n = w.getnframes()
    data = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32)

print(f"Coda duration: {n/sr:.2f} s")
step = int(0.5 * sr)
for i in range(0, n, step):
    t0 = i / sr
    t1 = min((i + step) / sr, n / sr)
    chunk = data[i:i+step]
    rms = np.sqrt(np.mean(chunk**2))
    print(f"[{t0:4.1f}s - {t1:4.1f}s] RMS: {rms:6.1f} | {'#' * int(rms/250)}")
