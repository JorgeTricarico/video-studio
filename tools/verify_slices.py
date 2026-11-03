import wave
import numpy as np

def inspect_range(wav_file, t_start, t_end, label):
    with wave.open(wav_file, "rb") as w:
        sr = w.getframerate()
        n = w.getnframes()
        w.setpos(int(t_start * sr))
        frames_to_read = int(min(t_end - t_start, (n - int(t_start * sr)) / sr) * sr)
        raw = w.readframes(frames_to_read)
        data = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
    rms = np.sqrt(np.mean(data**2))
    peak = np.max(np.abs(data))
    duration = len(data) / sr
    print(f"[{label}] {t_start:.2f}s - {t_end:.2f}s (dur={duration:.2f}s) | Peak: {peak:.0f}, RMS: {rms:.1f}")

print("=== CHECKING SLICE CANDIDATES ===")
inspect_range("assets/firule/audio_2_intro_isai.wav", 0.0, 3.45, "B1 Intro Isaí")
inspect_range("assets/firule/audio_1_narracion.wav", 3.65, 49.70, "B2 Narración A")
inspect_range("assets/firule/audio_1_narracion.wav", 58.35, 106.85, "B3 Narración B")
inspect_range("assets/firule/audio_3_cierre_silabas.wav", 0.0, 7.52, "B4 Cierre Sílabas")
inspect_range("assets/firule/audio_1_narracion.wav", 113.10, 113.85, "B5 Isaí Fin")
inspect_range("assets/firule/audio_3_cierre_silabas.wav", 7.52, 9.85, "B6 Aplausos")
