import os
import sys
sys.path.insert(0, os.getcwd())
import subprocess
from core.env_config import FFMPEG_BIN

os.makedirs("assets/firule/qa_frames", exist_ok=True)

timestamps = [
    (2.0, "01_dibujo_isai_header.jpg"),
    (5.2, "02_transicion_magica.jpg"),
    (9.0, "03_portada_ia.jpg"),
    (16.0, "04_paseo_parque.jpg"),
    (35.0, "05_escape_pantufla.jpg"),
    (56.0, "06_cuneta_sin_badge.jpg"),
    (90.0, "07_final_casa.jpg"),
    (100.8, "08_split_to.jpg"),
    (103.5, "09_split_te.jpg"),
    (105.3, "10_split_firule.jpg"),
    (106.5, "11_split_fin.jpg"),
    (109.0, "12_muy_bien_confeti.jpg"),
    (117.0, "13_canticuenticos_coda_outro.jpg"),
]

for t, name in timestamps:
    out_path = f"assets/firule/qa_frames/{name}"
    cmd = [
        FFMPEG_BIN, "-y", "-ss", str(t), "-i", "cuento_firule_isai.mp4",
        "-frames:v", "1", "-q:v", "2", out_path
    ]
    subprocess.run(cmd, check=True)
    print(f"[OK] Extracted QA frame at {t:5.1f}s -> {out_path}")