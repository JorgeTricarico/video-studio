import os
import sys
sys.path.insert(0, os.getcwd())
import subprocess
import wave
import numpy as np
import shutil
from core.env_config import FFMPEG_BIN, FFPROBE_BIN

os.makedirs("assets/firule/norm3", exist_ok=True)

# 1. Prepare raw slices
# B1: Intro Isai (0.0 to 3.45s)
# B2: Narracion A (3.65 to 49.70s)
# B3: Narracion B (58.35 to 106.85s)
# B4: Cierre Silabas (0.0 to 7.92s) -> Covers "cuen... ¡TO!", "suer... ¡TE!", "que se llama... ¡FIRULÉ!" completely without clipping
# B5: Isai "¡Fin!" (113.10 to 113.90s)
# B6: Mamá "¡Muy bien!" + Aplausos (7.92 to 10.35s)

slices_def = [
    ("b1_raw.wav", "assets/firule/audio_2_intro_isai.wav", 0.0, 3.45),
    ("b2_raw.wav", "assets/firule/audio_1_narracion.wav", 3.65, 49.70),
    ("b3_raw.wav", "assets/firule/audio_1_narracion.wav", 58.35, 106.85),
    ("b4_raw.wav", "assets/firule/audio_3_cierre_silabas.wav", 0.0, 7.92),
    ("b5_raw.wav", "assets/firule/audio_1_narracion.wav", 113.10, 113.90),
    ("b6_raw.wav", "assets/firule/audio_3_cierre_silabas.wav", 7.92, 10.35),
]

for out_name, src, t0, t1 in slices_def:
    with wave.open(src, "rb") as w_in:
        sr = w_in.getframerate()
        n_ch = w_in.getnchannels()
        sw = w_in.getsampwidth()
        w_in.setpos(int(t0 * sr))
        frames = w_in.readframes(int((t1 - t0) * sr))
    out_path = f"assets/firule/norm3/{out_name}"
    with wave.open(out_path, "wb") as w_out:
        w_out.setnchannels(n_ch)
        w_out.setsampwidth(sw)
        w_out.setframerate(sr)
        w_out.writeframes(frames)

# B1 with 0.4s clean pause
with wave.open("assets/firule/norm3/b1_raw.wav", "rb") as w_in:
    sr = w_in.getframerate()
    data = w_in.readframes(w_in.getnframes())
silence_04s = b"\x00" * int(0.40 * sr * 2)
with wave.open("assets/firule/norm3/b1_with_pause.wav", "wb") as w_out:
    w_out.setnchannels(1)
    w_out.setsampwidth(2)
    w_out.setframerate(sr)
    w_out.writeframes(data + silence_04s)

# B4 with 0.45s natural pause before "¡Fin!"
with wave.open("assets/firule/norm3/b4_raw.wav", "rb") as w_in:
    sr = w_in.getframerate()
    data = w_in.readframes(w_in.getnframes())
silence_b4_pause = b"\x00" * int(0.45 * sr * 2)
with wave.open("assets/firule/norm3/b4_with_pause.wav", "wb") as w_out:
    w_out.setnchannels(1)
    w_out.setsampwidth(2)
    w_out.setframerate(sr)
    w_out.writeframes(data + silence_b4_pause)

# B5 with 0.35s natural pause before applause
with wave.open("assets/firule/norm3/b5_raw.wav", "rb") as w_in:
    sr = w_in.getframerate()
    data = w_in.readframes(w_in.getnframes())
silence_b5_pause = b"\x00" * int(0.35 * sr * 2)
with wave.open("assets/firule/norm3/b5_with_pause.wav", "wb") as w_out:
    w_out.setnchannels(1)
    w_out.setsampwidth(2)
    w_out.setframerate(sr)
    w_out.writeframes(data + silence_b5_pause)

# Normalize each slice to -16 LUFS
norm_inputs = [
    ("assets/firule/norm3/b1_with_pause.wav", "assets/firule/norm3/b1_norm.wav"),
    ("assets/firule/norm3/b2_raw.wav", "assets/firule/norm3/b2_norm.wav"),
    ("assets/firule/norm3/b3_raw.wav", "assets/firule/norm3/b3_norm.wav"),
    ("assets/firule/norm3/b4_with_pause.wav", "assets/firule/norm3/b4_norm.wav"),
    ("assets/firule/norm3/b5_with_pause.wav", "assets/firule/norm3/b5_norm.wav"),
    ("assets/firule/norm3/b6_raw.wav", "assets/firule/norm3/b6_norm.wav"),
]

for src, dst in norm_inputs:
    cmd = [
        FFMPEG_BIN, "-y", "-i", src,
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-ar", "48000", "-ac", "1", dst
    ]
    subprocess.run(cmd, check=True, capture_output=True)

# Concatenate speech blocks cleanly:
# v12 = b1_norm + b2_norm with acrossfade 0.08
# v123 = v12 + b3_norm with acrossfade 0.08
# v1234 = v123 + b4_norm (b4 has 0.45s pause at end) with acrossfade 0.08
# v12345 = concat v1234 and b5_norm (b5 has 0.35s pause at end)
# final = concat with b6_norm
filter_concat = (
    "[0:a][1:a]acrossfade=d=0.08:c1=tri:c2=tri[v12];"
    "[v12][2:a]acrossfade=d=0.08:c1=tri:c2=tri[v123];"
    "[v123][3:a]acrossfade=d=0.08:c1=tri:c2=tri[v1234];"
    "[v1234][4:a]acrossfade=d=0.08:c1=tri:c2=tri[v12345];"
    "[v12345][5:a]acrossfade=d=0.08:c1=tri:c2=tri[speech_master]"
)

cmd_concat = [
    FFMPEG_BIN, "-y",
    "-i", "assets/firule/norm3/b1_norm.wav",
    "-i", "assets/firule/norm3/b2_norm.wav",
    "-i", "assets/firule/norm3/b3_norm.wav",
    "-i", "assets/firule/norm3/b4_norm.wav",
    "-i", "assets/firule/norm3/b5_norm.wav",
    "-i", "assets/firule/norm3/b6_norm.wav",
    "-filter_complex", filter_concat,
    "-map", "[speech_master]",
    "-ar", "48000", "-ac", "2",
    "assets/firule/speech_master_v3.wav"
]
subprocess.run(cmd_concat, check=True)

# Get speech duration
res = subprocess.run(
    [FFPROBE_BIN, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", "assets/firule/speech_master_v3.wav"],
    capture_output=True, text=True, check=True
)
speech_dur = float(res.stdout.strip())
print(f"Speech master v3 duration: {speech_dur:.2f}s")

# Extract authentic rhythmic instrumental Chamamé intro/groove from Canticuénticos (0.5s to 18.0s, 17.5s duration)
cmd_rhythm = [
    FFMPEG_BIN, "-y",
    "-ss", "0.5", "-to", "18.0",
    "-i", "assets/firule/canticuenticos_cancion.mp3",
    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
    "-ar", "48000", "-ac", "2",
    "assets/firule/norm3/rhythm_canticuenticos.wav"
]
subprocess.run(cmd_rhythm, check=True, capture_output=True)

# Musical Mix:
# 1. Background guitar loop at volume 0.08 (-22dB) throughout narration, fading out smoothly starting around speech_dur - 12.0s
# 2. Canticuénticos authentic rhythmic acoustic groove starts at speech_dur - 11.5s (right as the closing syllables start)
#    Starts at volume 0.18 (-15dB) during syllables, rises slightly to 0.28 during applause, and does a smooth 3.5s fade out!
# Total final duration = speech_dur + 3.0s of gentle musical tail!

bg_fadeout_st = max(0, speech_dur - 11.5)
coda_delay_ms = int((speech_dur - 11.5) * 1000)
coda_fadeout_st = 14.0 # after 14s of the 17.5s clip
total_target_dur = speech_dur + 2.5

filter_full_mix = (
    f"[1:a]volume=0.08,afade=t=out:st={bg_fadeout_st:.2f}:d=2.0[bg_guitar];"
    f"[2:a]volume=0.22,afade=t=in:st=0:d=1.5,afade=t=out:st={coda_fadeout_st:.2f}:d=3.5,adelay={coda_delay_ms}|{coda_delay_ms}[coda_groove];"
    "[0:a][bg_guitar]amix=inputs=2:duration=first:dropout_transition=2[mix1];"
    f"[mix1][coda_groove]amix=inputs=2:duration=longest:dropout_transition=2,"
    "loudnorm=I=-16:TP=-1.5:LRA=11[master]"
)

cmd_master = [
    FFMPEG_BIN, "-y",
    "-i", "assets/firule/speech_master_v3.wav",
    "-i", "assets/firule/guitarra_chamame_fondo.wav",
    "-i", "assets/firule/norm3/rhythm_canticuenticos.wav",
    "-filter_complex", filter_full_mix,
    "-map", "[master]",
    "-c:a", "libmp3lame", "-b:a", "192k",
    "audio_final_master.mp3"
]

print("Mixing master audio v3 with soft rhythmic Canticuenticos groove...")
subprocess.run(cmd_master, check=True)

shutil.copyfile("audio_final_master.mp3", "assets/firule/audio_final_master.mp3")

res = subprocess.run(
    [FFPROBE_BIN, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", "audio_final_master.mp3"],
    capture_output=True, text=True, check=True
)
final_dur = float(res.stdout.strip())
print(f"[OK] Master audio v3 generado con éxito. Duración: {final_dur:.2f}s")
