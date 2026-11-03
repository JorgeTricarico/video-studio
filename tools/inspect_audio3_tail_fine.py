import wave
import numpy as np

# Let's inspect audio_3_cierre_silabas from 6.0 to 9.85s
with wave.open('assets/firule/audio_3_cierre_silabas.wav', 'rb') as w:
    sr = w.getframerate()
    w.setpos(int(6.0 * sr))
    frames = w.readframes(int(3.85 * sr))
    audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32)

step = int(0.05 * sr)
for i in range(0, len(audio), step):
    t = 6.0 + i / sr
    chunk = audio[i:i+step]
    rms = np.sqrt(np.mean(chunk**2))
    print(f"t={t:5.2f}s | RMS={rms:6.1f}")
