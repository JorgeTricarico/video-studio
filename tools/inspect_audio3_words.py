import json

with open('assets/firule/audio_3_cierre_silabas_whisper.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for seg in data['segments']:
    print(f"[{seg['start']:.2f}s - {seg['end']:.2f}s]: {seg['text']}")
    for w in seg.get('words', []):
        print(f"   {w['start']:.2f}s - {w['end']:.2f}s: {w['word']}")
