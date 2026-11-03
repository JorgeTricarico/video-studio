import wave
import numpy as np

with wave.open("assets/firule/audio_1_narracion.wav", "rb") as w:
    sr = w.getframerate()
    # Read between 48.0s and 60.0s
    w.setpos(int(48.0 * sr))
    data = np.frombuffer(w.readframes(int(12.0 * sr)), dtype=np.int16)

# Print energy in 100ms chunks from 48.0 to 60.0
print("Time(s) | RMS")
step = int(0.1 * sr)
for i in range(0, len(data), step):
    t = 48.0 + i / sr
    chunk = data[i:i+step]
    rms = np.sqrt(np.mean(chunk.astype(np.float32)**2))
    print(f"{t:5.2f}s | {rms:6.1f} | {'#' * int(rms/200)}")
