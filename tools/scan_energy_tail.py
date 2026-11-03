import numpy as np
from scipy.io import wavfile

sr, data = wavfile.read("assets/firule/audio_1_narracion.wav")
total_sec = len(data) / sr
print(f"Total duration: {total_sec:.3f} s")

# Check between 105s and end
start_s = 105.0
start_idx = int(start_s * sr)
chunk = data[start_idx:]

# Let's inspect energy in 100ms intervals
step = int(0.1 * sr)
print("Time(s) | RMS")
for i in range(0, len(chunk), step):
    sub = chunk[i:i+step]
    rms = np.sqrt(np.mean(sub.astype(np.float32)**2))
    t = start_s + i / sr
    bar = "#" * int(rms / 200)
    print(f"{t:6.2f}s | {rms:6.1f} | {bar}")
