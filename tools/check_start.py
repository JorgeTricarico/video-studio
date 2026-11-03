import json

data = json.load(open("assets/firule/audio_1_narracion_whisper.json", encoding="utf-8"))
for s in data['segments']:
    if s['start'] < 10.0:
        print(f"SEG: [{s['start']:.2f} - {s['end']:.2f}] {s['text']}")
        for w in s.get('words', []):
            print(f"    [{w['start']:.2f} - {w['end']:.2f}] {w['word']}")
