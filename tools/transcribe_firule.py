import os
import json
import whisper

os.makedirs("assets/firule", exist_ok=True)
print("[*] Cargando modelo Whisper...")
model = whisper.load_model("base")

files = [
    ("assets/firule/audio_2_intro_isai.m4a", "assets/firule/audio_2_intro_isai_whisper.json"),
    ("assets/firule/audio_1_narracion.m4a", "assets/firule/audio_1_narracion_whisper.json"),
    ("assets/firule/audio_3_cierre_silabas.m4a", "assets/firule/audio_3_cierre_silabas_whisper.json"),
]

for audio_path, json_path in files:
    print(f"[*] Transcribiendo {audio_path}...")
    res = model.transcribe(audio_path, language="es", word_timestamps=True, verbose=False)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print(f"[OK] {json_path} guardado.")
