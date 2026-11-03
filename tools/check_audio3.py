import json

data = json.load(open("assets/firule/audio_3_cierre_silabas_whisper.json", encoding="utf-8"))
print("AUDIO 3 DETAILED WORDS:")
for s in data['segments']:
    print(f"SEG: [{s['start']:.2f} - {s['end']:.2f}] {s['text']}")
    for w in s.get('words', []):
        print(f"    [{w['start']:.2f} - {w['end']:.2f}] {w['word']}")
