import whisper

model = whisper.load_model("base")
res = model.transcribe("assets/firule/canticuenticos_cancion.mp3", language="es")

prev_end = 0.0
for s in res['segments']:
    start = s['start']
    end = s['end']
    gap = start - prev_end
    if gap > 2.0:
        print(f"INSTRUMENTAL GAP: {prev_end:.2f}s to {start:.2f}s (duration: {gap:.2f}s)")
    print(f"[{start:.2f}s - {end:.2f}s]: {s['text']}")
    prev_end = end
print(f"End gap: {prev_end:.2f}s to 153.86s (duration: {153.86 - prev_end:.2f}s)")
