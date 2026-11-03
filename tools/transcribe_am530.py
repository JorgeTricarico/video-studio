import os
import sys
import json
import whisper

audio_path = "assets/am530_audio.m4a"
out_json = "assets/am530_whisper.json"

print(f"[*] Cargando modelo Whisper 'small'...")
model = whisper.load_model("small")

prompt = "Hospital Garrahan, Johanna Tricarico, colectivo Soy Garrahan, DNI, RENAPER, Madres de Plaza de Mayo, Quita Penas, Incluir Salud, Cristian, Santiago del Estero, Bayron, ley de emergencia pediátrica."

print(f"[*] Transcribiendo '{audio_path}' con word_timestamps=True...")
result = model.transcribe(
    audio_path,
    language="es",
    word_timestamps=True,
    initial_prompt=prompt,
    verbose=False
)

# Diccionario de corrección fonética estricta
REPLACEMENTS = {
    r"\bGarrajam\b": "Garrahan",
    r"\bGarraham\b": "Garrahan",
    r"\bGaram\b": "Garrahan",
    r"\bgarrerjan\b": "Garrahan",
    r"\bSaran Rajan\b": "Soy Garrahan",
    r"\bsoy a Rajan\b": "Soy Garrahan",
    r"\benena\b": "nena",
    r"\buna enena\b": "una nena",
    r"\bJoana\b": "Johanna",
    r"\bJoanna\b": "Johanna",
    r"\bTricarisco\b": "Tricarico",
    r"\bquitenas\b": "Quita Penas",
    r"\bquitenas\b": "Quita Penas",
    r"\bquítenas\b": "Quita Penas",
    r"\bRenaper\b": "RENAPER",
    r"\brenaper\b": "RENAPER",
    r"\bdni\b": "DNI",
}

import re

def clean_text(t):
    for pat, rep in REPLACEMENTS.items():
        t = re.sub(pat, rep, t, flags=re.IGNORECASE)
    return t

result["text"] = clean_text(result["text"])
for seg in result.get("segments", []):
    seg["text"] = clean_text(seg["text"])
    for w in seg.get("words", []):
        w["word"] = clean_text(w["word"])

with open(out_json, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"[OK] Transcripción completada y guardada en {out_json}")
print(f"     Total segmentos: {len(result.get('segments', []))}")
