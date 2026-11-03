import json
import whisper

model = whisper.load_model("base")
# transcribe only the tail of audio_1_narracion
# let's slice 108s to 114.61s with ffmpeg and transcribe
import subprocess

subprocess.run([
    "ffmpeg", "-y", "-ss", "107.0", "-i", "assets/firule/audio_1_narracion.m4a",
    "-c", "copy", "assets/firule/tail_audio_1.m4a"
], check=True)

res = model.transcribe("assets/firule/tail_audio_1.m4a", language="es", word_timestamps=True)
print("TAIL TRANSCRIPT:")
for s in res['segments']:
    print(f"[{s['start']:.2f} - {s['end']:.2f}] {s['text']}")
    for w in s.get('words', []):
        print(f"    [{w['start']:.2f} - {w['end']:.2f}] {w['word']}")
