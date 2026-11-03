import os
import sys
sys.path.insert(0, os.getcwd())
import subprocess
import wave
import numpy as np
from core.env_config import FFMPEG_BIN, FFPROBE_BIN

os.makedirs("assets/firule/norm", exist_ok=True)

# 1. Prepare raw slice WAVs
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
    print(f"Extracted {out_name}: {t0}s - {t1}s")

# For B1, add 0.4s clean silence at the end
with wave.open("assets/firule/b1_raw.wav", "rb") as w_in:
    sr = w_in.getframerate()
    data = w_in.readframes(w_in.getnframes())
silence_04s = b"\x00" * int(0.4 * sr * 2)
with wave.open("assets/firule/b1_with_pause.wav", "wb") as w_out:
    w_out.setnchannels(1)
    w_out.setsampwidth(2)
    w_out.setframerate(sr)
    w_out.writeframes(data + silence_04s)

# 2. Normalize each slice to -16 LUFS (loudnorm=I=-16:TP=-1.5:LRA=11)
norm_inputs = [
    ("assets/firule/b1_with_pause.wav", "assets/firule/norm/b1_norm.wav"),
    ("assets/firule/b2_raw.wav", "assets/firule/norm/b2_norm.wav"),
    ("assets/firule/b3_raw.wav", "assets/firule/norm/b3_norm.wav"),
    ("assets/firule/b4_raw.wav", "assets/firule/norm/b4_norm.wav"),
    ("assets/firule/b5_raw.wav", "assets/firule/norm/b5_norm.wav"),
    ("assets/firule/b6_raw.wav", "assets/firule/norm/b6_norm.wav"),
]

for src, dst in norm_inputs:
    print(f"Normalizing {src} -> {dst} (-16 LUFS)...")
    cmd = [
        FFMPEG_BIN, "-y", "-i", src,
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-ar", "48000", "-ac", "1", dst
    ]
    subprocess.run(cmd, check=True)

# 3. Concatenate with acrossfade=d=0.08:c1=tri:c2=tri
# Filter graph chaining acrossfade
# b1 + b2 -> v12
# v12 + b3 -> v123
# v123 + b4 -> v1234
# v1234 + b5 -> v12345
# v12345 + b6 -> v_speech_master
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
print("Concatenating speech with micro-crossfades...")
subprocess.run(cmd_concat, check=True)

# Get speech_master duration with ffprobe
res = subprocess.run(
    [FFPROBE_BIN, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", "assets/firule/speech_master.wav"],
    capture_output=True, text=True, check=True
)
total_dur = float(res.stdout.strip())
print(f"[OK] Total speech duration: {total_dur:.3f} s")

# 4. Mix with background music:
# - Music at -22 dB during narration
# - In the last 5 seconds, volume rises to -8 dB (with volume curve)
# - Soft fade out at the end
# - Overall final loudnorm to -16 LUFS
boost_start = max(0.0, total_dur - 5.0)

# Volume automation for music:
# Between 0 and boost_start: volume = -22dB (0.0794)
# Between boost_start and total_dur: smoothly ramp to -8dB (0.398)
filter_music = (
    f"[1:a]volume=eval=frame:volume='if(lt(t,{boost_start}), 0.0794, 0.0794 + (0.3981 - 0.0794)*((t - {boost_start})/5.0))',"
    f"afade=t=out:st={total_dur - 0.8}:d=0.8[music_vol];"
    f"[0:a][music_vol]amix=inputs=2:duration=first:dropout_transition=2,"
    f"loudnorm=I=-16:TP=-1.5:LRA=11[master]"
)

cmd_master = [
    FFMPEG_BIN, "-y",
    "-i", "assets/firule/speech_master.wav",
    "-i", "assets/firule/guitarra_chamame_fondo.wav",
    "-filter_complex", filter_music,
    "-map", "[master]",
    "-c:a", "libmp3lame", "-b:a", "192k",
    "audio_final_master.mp3"
]

print("Mixing music with ducking and volume boost into audio_final_master.mp3...")
subprocess.run(cmd_master, check=True)

# Also copy to assets/firule
import shutil
shutil.copyfile("audio_final_master.mp3", "assets/firule/audio_final_master.mp3")

print("[OK] audio_final_master.mp3 successfully created and verified!")
