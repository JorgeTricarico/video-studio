import json
import os
import shutil
import render_johanna_ley_pediatrica as engine

# 1. Cargar datos de Whisper
with open("assets/johanna_radio10_whisper.json", "r", encoding="utf-8") as f:
    whisper_data = json.load(f)

all_words = []
for s in whisper_data["segments"]:
    if "words" in s:
        for w in s["words"]:
            all_words.append(w)

def extract_words_for_slice(start_t, end_t, offset=0.0):
    res = []
    for w in all_words:
        if start_t <= w["start"] <= end_t:
            res.append({
                "word": w["word"].strip(),
                "start": max(0.0, w["start"] - start_t + offset),
                "end": max(0.05, w["end"] - start_t + offset)
            })
    return res

# -------------------------------------------------------------
# REEL 1: PROYECTO NUEVA LEY DE SALUD PEDIÁTRICA NACIONAL
# -------------------------------------------------------------
slices_1 = [{"start": 471.5, "end": 520.0}]
words_1 = extract_words_for_slice(471.5, 520.0, offset=0.0)

out_1 = os.path.join(engine.OUT_DIR, "01_Johanna_Nueva_Ley_Salud_Pediatrica_Nacional.mp4")
engine.render_reel(slices_1, words_1, "NUESTROS HIJOS EN PELIGRO", "COMUNICACION EN VIVO - RADIO 10", out_1)
shutil.copy2(out_1, os.path.join(engine.FINAL_DIR, os.path.basename(out_1)))

# -------------------------------------------------------------
# REEL 2: LA TRAMPA DEL GOBIERNO - QUISIERON APAGAR LA LUCHA
# -------------------------------------------------------------
slices_2 = [{"start": 66.8, "end": 111.8}]
words_2 = extract_words_for_slice(66.8, 111.8, offset=0.0)

out_2 = os.path.join(engine.OUT_DIR, "02_Johanna_La_Trampa_Del_Gobierno_Quisieron_Apagar_La_Lucha.mp4")
engine.render_reel(slices_2, words_2, "QUISIERON APAGAR LA LUCHA", "COMUNICACION EN VIVO - RADIO 10", out_2)
shutil.copy2(out_2, os.path.join(engine.FINAL_DIR, os.path.basename(out_2)))

# -------------------------------------------------------------
# REEL 3: MEDICAMENTOS MILLONARIOS Y EL CASO BAYRON
# -------------------------------------------------------------
dur_a = 291.8 - 280.7
slices_3 = [
    {"start": 280.7, "end": 291.8},
    {"start": 330.4, "end": 361.5}
]
words_3_a = extract_words_for_slice(280.7, 291.8, offset=0.0)
words_3_b = extract_words_for_slice(330.4, 361.5, offset=dur_a)
words_3 = words_3_a + words_3_b

out_3 = os.path.join(engine.OUT_DIR, "03_Johanna_Medicamentos_Millonarios_Caso_Bayron.mp4")
engine.render_reel(slices_3, words_3, "QUE ESPERAN QUE QUEDE CIEGO", "COMUNICACION EN VIVO - RADIO 10", out_3)
shutil.copy2(out_3, os.path.join(engine.FINAL_DIR, os.path.basename(out_3)))

print("\n[OK] LOS 3 REELS DE RADIO 10 HAN SIDO RENDERIZADOS CON EXITO.")
