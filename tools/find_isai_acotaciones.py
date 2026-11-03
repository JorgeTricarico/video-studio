import wave
import numpy as np

with wave.open("assets/firule/b3_narracion_b.wav", "rb") as w:
    sr = w.getframerate()
    n = w.getnframes()
    data = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32)

# Bloque 3 starts at 58.35s of audio_1_narracion.
# So 1:03.5 is at (63.5 - 58.35) = 5.15s into b3.
# 1:11.0 is at (71.0 - 58.35) = 12.65s into b3.
print("Scanning around 1:03.5 (b3 ~ 4.0s - 7.0s) and 1:11.0 (b3 ~ 11.0s - 14.0s)")

# Let's write small audio snippets to listen/inspect
def save_snippet(t0, t1, name):
    sub = data[int(t0*sr):int(t1*sr)].astype(np.int16)
    with wave.open(f"assets/firule/isai_{name}.wav", "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(sr)
        out.writeframes(sub.tobytes())
    print(f"Saved isai_{name}.wav ({t0:.2f}s - {t1:.2f}s in b3)")

save_snippet(4.5, 7.5, "check_no")
save_snippet(11.5, 14.0, "check_si")
