import wave
import whisper

model = whisper.load_model("base")

slices = [
    ("assets/firule/audio_2_intro_isai.wav", 0.0, 3.45, "b1_intro_isai.wav"),
    ("assets/firule/audio_1_narracion.wav", 3.65, 49.70, "b2_narracion_a.wav"),
    ("assets/firule/audio_1_narracion.wav", 58.35, 106.85, "b3_narracion_b.wav"),
    ("assets/firule/audio_3_cierre_silabas.wav", 0.0, 7.52, "b4_cierre_silabas.wav"),
    ("assets/firule/audio_1_narracion.wav", 113.10, 113.85, "b5_isai_fin.wav"),
    ("assets/firule/audio_3_cierre_silabas.wav", 7.52, 9.85, "b6_aplausos.wav"),
]

for src, t0, t1, out_name in slices:
    with wave.open(src, "rb") as w_in:
        sr = w_in.getframerate()
        n_ch = w_in.getnchannels()
        sw = w_in.getsampwidth()
        w_in.setpos(int(t0 * sr))
        frames = w_in.readframes(int((t1 - t0) * sr))
    
    out_path = f"assets/firule/{out_name}"
    with wave.open(out_path, "wb") as w_out:
        w_out.setnchannels(n_ch)
        w_out.setsampwidth(sw)
        w_out.setframerate(sr)
        w_out.writeframes(frames)
        
    res = model.transcribe(out_path, language="es", fp16=False)
    print(f"[{out_name}] ({t0:.2f}s - {t1:.2f}s) -> '{res['text'].strip()}'")
