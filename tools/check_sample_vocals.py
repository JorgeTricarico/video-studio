import whisper
import glob

model = whisper.load_model("base")
files = glob.glob("assets/firule/sample_*.wav")
for f in files:
    res = model.transcribe(f, language="es")
    print(f"{f}: '{res['text'].strip()}'")
