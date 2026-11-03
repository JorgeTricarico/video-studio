import subprocess
from core.env_config import FFPROBE_BIN

res = subprocess.run(
    [FFPROBE_BIN, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", "assets/firule/canticuenticos_cancion.mp3"],
    capture_output=True, text=True, check=True
)
print("Canticuenticos total duration:", float(res.stdout.strip()), "s")
