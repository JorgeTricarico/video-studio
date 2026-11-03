import json

def dump(title, path):
    print('='*25, title, '='*25)
    data = json.load(open(path, encoding='utf-8'))
    for s in data['segments']:
        print(f"[{s['start']:6.2f} - {s['end']:6.2f}] {s['text']}")

dump('AUDIO 2 (INTRO ISAI)', 'assets/firule/audio_2_intro_isai_whisper.json')
print()
dump('AUDIO 3 (CIERRE SILABAS)', 'assets/firule/audio_3_cierre_silabas_whisper.json')
print()
dump('AUDIO 1 (NARRACION)', 'assets/firule/audio_1_narracion_whisper.json')
