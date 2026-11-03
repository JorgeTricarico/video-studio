import wave
import whisper

model = whisper.load_model("base")

def extract_and_transcribe(t0, t1, name):
    with wave.open("assets/firule/audio_1_narracion.wav", "rb") as w_in:
        sr = w_in.getframerate()
        n_channels = w_in.getnchannels()
        sampwidth = w_in.getsampwidth()
        
        w_in.setpos(int(t0 * sr))
        frames = w_in.readframes(int((t1 - t0) * sr))
        
    out_path = f"assets/firule/chunk_{name}.wav"
    with wave.open(out_path, "wb") as w_out:
        w_out.setnchannels(n_channels)
        w_out.setsampwidth(sampwidth)
        w_out.setframerate(sr)
        w_out.writeframes(frames)
        
    res = model.transcribe(out_path, language="es", fp16=False)
    print(f"[{t0:5.2f} - {t1:5.2f}] -> '{res['text'].strip()}'")

chunks = [
    (104.5, 107.0, "104.5_107.0"),
    (107.2, 108.0, "107.2_108.0"),
    (108.5, 110.0, "108.5_110.0"),
    (110.5, 112.5, "110.5_112.5"),
    (112.8, 114.2, "112.8_114.2"),
]

for t0, t1, name in chunks:
    extract_and_transcribe(t0, t1, name)
