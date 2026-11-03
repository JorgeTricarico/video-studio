import os
import sys
sys.path.insert(0, os.getcwd())
import subprocess
import json
from core.env_config import FFMPEG_BIN, FFPROBE_BIN

# Scan every 10 seconds of canticuenticos_cancion.mp3
cmd = [
    FFPROBE_BIN, "-v", "error", "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1", "assets/firule/canticuenticos_cancion.mp3"
]
dur = float(subprocess.check_output(cmd).decode().strip())
print(f"Total song duration: {dur:.2f}s")

# Let's extract 5s previews of instrumental parts:
# 1. 0:35 - 0:45 (interludio instrumental)
# 2. 1:05 - 1:18 (puente rítmico)
# 3. 1:25 - 1:38 (rítmica instrumental antes del final)
# 4. 1:38 - 1:50 (coda)

sections = [
    ("interludio_35_45", 35.0, 45.0),
    ("puente_65_75", 65.0, 75.0),
    ("ritmica_105_120", 105.0, 120.0),
    ("ritmica_122_136", 122.0, 136.0),
    ("antes_coda_130_142", 130.0, 142.0)
]

for name, t0, t1 in sections:
    out = f"assets/firule/sample_{name}.wav"
    cmd = [
        FFMPEG_BIN, "-y", "-ss", str(t0), "-to", str(t1),
        "-i", "assets/firule/canticuenticos_cancion.mp3",
        "-ar", "48000", "-ac", "2", out
    ]
    subprocess.run(cmd, capture_output=True)
    print(f"Extracted {name} ({t0}s - {t1}s)")
