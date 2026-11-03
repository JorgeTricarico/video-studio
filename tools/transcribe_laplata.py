import os
import sys
import json
import re
import whisper

audio_path = "assets/radio_laplata_audio.m4a"
out_json = "assets/radio_laplata_whisper.json"
out_compact = "assets/radio_laplata_whisper_compact.json"

print(f"[*] Cargando modelo Whisper 'small'...")
model = whisper.load_model("small")

prompt = (
    "Hospital Garrahan, Johanna Tricarico, colectivo Soy Garrahan, "
    "Radio Universidad Nacional de La Plata, Radio U La Plata, Señal de Ajuste, "
    "ley de emergencia pediátrica, presupuesto nacional, Congreso de la Nación, "
    "discapacidad, oncología pediátrica, tratamientos complejos."
)

print(f"[*] Transcribiendo '{audio_path}' con word_timestamps=True...")
result = model.transcribe(
    audio_path,
    language="es",
    word_timestamps=True,
    initial_prompt=prompt,
    verbose=False
)

# Guardar transcripción completa
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"[OK] Transcripción completa guardada en: {out_json}")

# Generar versión compacta para análisis rápido
compact_segments = []
for s in result.get("segments", []):
    compact_segments.append({
        "id": s.get("id"),
        "start": round(s.get("start", 0), 2),
        "end": round(s.get("end", 0), 2),
        "text": s.get("text", "").strip()
    })

with open(out_compact, "w", encoding="utf-8") as f:
    json.dump(compact_segments, f, ensure_ascii=False, indent=2)

print(f"[OK] Versión compacta guardada en: {out_compact} ({len(compact_segments)} segmentos)")
