import whisper
import json

model = whisper.load_model("base")
print("[*] Transcribing audio_final_master.mp3 to get exact master timeline...")
res = model.transcribe("audio_final_master.mp3", language="es", word_timestamps=True, fp16=False)

with open("assets/firule/master_whisper.json", "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=2)

print("TIMELINE IN MASTER AUDIO:")
for s in res['segments']:
    print(f"[{s['start']:6.2f} - {s['end']:6.2f}] {s['text']}")
