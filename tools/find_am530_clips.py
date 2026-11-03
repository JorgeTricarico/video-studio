import json

with open("assets/am530_whisper.json", "r", encoding="utf-8") as f:
    data = json.load(f)

segments = data.get("segments", [])

print("=== BUSCANDO CLIPS EN AM530 ===")

# Clip 1: Nena de Salta y DNI (alrededor de 105s - 170s)
print("\n--- CANDIDATO REEL 1: Nena de Salta & DNI (100s - 180s) ---")
for s in segments:
    if 100 <= s["start"] <= 180:
        print(f"[{s['start']:.2f} - {s['end']:.2f}] {s['text']}")

# Clip 2: Cáncer y Auditorías Eternas (alrededor de 290s - 340s)
print("\n--- CANDIDATO REEL 2: Cáncer & Auditorías (285s - 340s) ---")
for s in segments:
    if 285 <= s["start"] <= 340:
        print(f"[{s['start']:.2f} - {s['end']:.2f}] {s['text']}")

# Clip 3: Sector Privado no vio el tumor (alrededor de 330s - 400s)
print("\n--- CANDIDATO REEL 3: Sector Privado & Tumor (330s - 410s) ---")
for s in segments:
    if 330 <= s["start"] <= 410:
        print(f"[{s['start']:.2f} - {s['end']:.2f}] {s['text']}")

# Clip 4: Muñecas Quita Penas (alrededor de 415s - 475s)
print("\n--- CANDIDATO REEL 4: Muñecas Quita Penas (415s - 475s) ---")
for s in segments:
    if 415 <= s["start"] <= 475:
        print(f"[{s['start']:.2f} - {s['end']:.2f}] {s['text']}")

# Clip 5: Cristian en Santiago (alrededor de 525s - 575s)
print("\n--- CANDIDATO REEL 5: Cristian Santiago del Estero (525s - 575s) ---")
for s in segments:
    if 525 <= s["start"] <= 575:
        print(f"[{s['start']:.2f} - {s['end']:.2f}] {s['text']}")
