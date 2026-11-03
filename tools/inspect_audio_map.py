import json

def load_json(p):
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)

d1 = load_json('assets/firule/audio_1_narracion_whisper.json')
d2 = load_json('assets/firule/audio_2_intro_isai_whisper.json')
d3 = load_json('assets/firule/audio_3_cierre_silabas_whisper.json')

print("=== INTRO ISAI ===")
for s in d2.get('segments', []):
    print(f"[{s['start']:.2f} - {s['end']:.2f}]: {s['text']}")

print("\n=== NARRACION AUDIO 1 ===")
for s in d1.get('segments', []):
    print(f"[{s['start']:.2f} - {s['end']:.2f}]: {s['text']}")

print("\n=== CIERRE SILABAS ===")
for s in d3.get('segments', []):
    print(f"[{s['start']:.2f} - {s['end']:.2f}]: {s['text']}")
