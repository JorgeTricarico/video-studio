import whisper

model = whisper.load_model("base")
# Let's slice the last 30s of canticuenticos_cancion.mp3
import subprocess
subprocess.run([
    "ffmpeg", "-y", "-ss", "125.0", "-i", "assets/firule/canticuenticos_cancion.mp3",
    "assets/firule/canticuenticos_tail.mp3"
], check=True)

res = model.transcribe("assets/firule/canticuenticos_tail.mp3", language="es", word_timestamps=True, fp16=False)
for s in res['segments']:
    print(f"[{125.0 + s['start']:6.2f} - {125.0 + s['end']:6.2f}] {s['text']}")
