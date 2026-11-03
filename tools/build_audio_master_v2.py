import os
import sys
sys.path.insert(0, os.getcwd())
import subprocess
import wave
import numpy as np
from core.env_config import FFMPEG_BIN, FFPROBE_BIN

os.makedirs("assets/firule/norm", exist_ok=True)

# 1. Prepare speech slices
slices_def = [
    ("b1_raw.wav", "assets/firule/audio_2_intro_isai.wav", 0.0, 3.45),
    ("b2_raw.wav", "assets/firule/audio_1_narracion.wav", 3.65, 49.70),
    ("b3_raw.wav", "assets/firule/audio_1_narracion.wav", 58.35, 106.85),
    ("b4_raw.wav", "assets/firule/audio_3_cierre_silabas.wav", 0.0, 7.52),
    ("b5_raw.wav", "assets/firule/audio_1_narracion.wav", 113.10, 113.85),
    ("b6_raw.wav", "assets/firule/audio_3_cierre_silabas.wav", 7.52, 9.85),
]

for out_name, src, t0, t1 in slices_def:
    with wave.open(src, "rb") as w_in:
        sr = w_in.getframerate()
        n_ch = w_in.getnchannels()
        sw = w_in.getsampwidth()
        w_in.setpos(int(t0 * sr))
        frames = w_in.readframes(int((t1 - t0) * sr))
    out_path = f"assets/firule/{out_name}"
    with wave.open(out_path, "wb") as w_out:
        w_out.setnchannels(n_ch)
        w_out.setsampwidth(sw)
        w_out.setframerate(sr)
        w_out.writeframes(frames)

# B1 with 0.4s pause
with wave.open("assets/firule/b1_raw.wav", "rb") as w_in:
    sr = w_in.getframerate()
    data = w_in.readframes(w_in.getnframes())
silence_04s = b"\x00" * int(0.4 * sr * 2)
with wave.open("assets/firule/b1_with_pause.wav", "wb") as w_out:
    w_out.setnchannels(1)
    w_out.setsampwidth(2)
    w_out.setframerate(sr)
    w_out.writeframes(data + silence_04s)

# Normalize each slice to -16 LUFS
norm_inputs = [
    ("assets/firule/b1_with_pause.wav", "assets/firule/norm/b1_norm.wav"),
    ("assets/firule/b2_raw.wav", "assets/firule/norm/b2_norm.wav"),
    ("assets/firule/b3_raw.wav", "assets/firule/norm/b3_norm.wav"),
    ("assets/firule/b4_raw.wav", "assets/firule/norm/b4_norm.wav"),
    ("assets/firule/b5_raw.wav", "assets/firule/norm/b5_norm.wav"),
    ("assets/firule/b6_raw.wav", "assets/firule/norm/b6_norm.wav"),
]

for src, dst in norm_inputs:
    cmd = [
        FFMPEG_BIN, "-y", "-i", src,
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-ar", "48000", "-ac", "1", dst
    ]
    subprocess.run(cmd, check=True)

# Concatenate speech blocks
filter_concat = (
    "[0:a][1:a]acrossfade=d=0.08:c1=tri:c2=tri[v12];"
    "[v12][2:a]acrossfade=d=0.08:c1=tri:c2=tri[v123];"
    "[v123][3:a]acrossfade=d=0.08:c1=tri:c2=tri[v1234];"
    "[v1234][4:a]acrossfade=d=0.08:c1=tri:c2=tri[v12345];"
    "[v12345][5:a]acrossfade=d=0.08:c1=tri:c2=tri[speech_master]"
)

cmd_concat = [
    FFMPEG_BIN, "-y",
    "-i", "assets/firule/norm/b1_norm.wav",
    "-i", "assets/firule/norm/b2_norm.wav",
    "-i", "assets/firule/norm/b3_norm.wav",
    "-i", "assets/firule/norm/b4_norm.wav",
    "-i", "assets/firule/norm/b5_norm.wav",
    "-i", "assets/firule/norm/b6_norm.wav",
    "-filter_complex", filter_concat,
    "-map", "[speech_master]",
    "-ar", "48000", "-ac", "2",
    "assets/firule/speech_master.wav"
]
subprocess.run(cmd_concat, check=True)

res = subprocess.run(
    [FFPROBE_BIN, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", "assets/firule/speech_master.wav"],
    capture_output=True, text=True, check=True
)
speech_dur = float(res.stdout.strip())
print(f"Speech duration: {speech_dur:.2f}s")

# Extract the authentic Canticuénticos coda (from 138.0 to end of song 153.85, ~15.8s)
# Normalize the coda
cmd_coda = [
    FFMPEG_BIN, "-y",
    "-ss", "138.0", "-to", "153.85",
    "-i", "assets/firule/canticuenticos_cancion.mp3",
    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
    "-ar", "48000", "-ac", "2",
    "assets/firule/coda_norm.wav"
]
subprocess.run(cmd_coda, check=True)

# Suture the coda music onto the end:
# Speech finishes around ~108.6s (with applause).
# The coda music starts playing right when Bloque 4/5 finishes, so applause and coda blend together,
# and coda continues for about 8-10 seconds to its natural resolving final chord!
# Let's align the coda start at t = 105.5s (right when Isaí says "¡Fin!" and applause starts).
# Total master audio duration will be ~ 105.5 + 15.8 = ~121.3 seconds, with a natural musical resolution!

# Background music:
# Guitar loop plays at volume 0.08 (-22dB) from 0s to 105.0s, fading out smoothly between 103s and 105.5s.
# Authentic Canticuénticos Coda starts at 105.5s at full musical volume (0.75), fading in smoothly with applause and concluding naturally.
filter_full_mix = (
    # Background guitar ducked during narration, fades out at 105.5s
    "[1:a]volume=0.08,afade=t=out:st=103.0:d=2.5[bg_guitar];"
    # Delay coda to start at 105.5s
    "[2:a]adelay=105500|105500,volume=0.65[coda_delayed];"
    # Mix speech + bg_guitar + coda
    "[0:a][bg_guitar]amix=inputs=2:duration=first:dropout_transition=2[mix1];"
    "[mix1][coda_delayed]amix=inputs=2:duration=longest:dropout_transition=2,"
    "loudnorm=I=-16:TP=-1.5:LRA=11[master]"
)

cmd_master = [
    FFMPEG_BIN, "-y",
    "-i", "assets/firule/speech_master.wav",
    "-i", "assets/firule/guitarra_chamame_fondo.wav",
    "-i", "assets/firule/coda_norm.wav",
    "-filter_complex", filter_full_mix,
    "-map", "[master]",
    "-c:a", "libmp3lame", "-b:a", "192k",
    "audio_final_master.mp3"
]

print("Mixing master audio with authentic Canticuenticos musical coda...")
subprocess.run(cmd_master, check=True)

# Copy to assets/firule
import shutil
shutil.copyfile("audio_final_master.mp3", "assets/firule/audio_final_master.mp3")

res = subprocess.run(
    [FFPROBE_BIN, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", "audio_final_master.mp3"],
    capture_output=True, text=True, check=True
)
final_dur = float(res.stdout.strip())
print(f"[OK] New audio_final_master.mp3 created! Total duration: {final_dur:.2f} s")
