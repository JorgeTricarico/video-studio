"""
SMART CROPPER & FRAMING ASSISTANT • REELS STUDIO
Analiza el video fuente y sugiere coordenadas de recorte 9:16 (1080x1920)
centradas en el sujeto para nuevos programas de radio o televisión.
"""
import os
import re
import subprocess
import json
import argparse

FFMPEG = os.path.expandvars(
    r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe"
)
FFPROBE = FFMPEG.replace("ffmpeg.exe", "ffprobe.exe")

def analyze_crop(video_path: str, start_sec: float = 30.0, duration: float = 10.0):
    if not os.path.exists(video_path):
        print(f"Error: No se encuentra el archivo {video_path}")
        return

    print(f"[*] Analizando encuadre en: {video_path} ({start_sec}s - {start_sec + duration}s)...")
    
    # 1. Obtener dimensiones originales
    res = subprocess.check_output([
        FFPROBE, "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", "-of", "json", video_path
    ], text=True)
    meta = json.loads(res)["streams"][0]
    orig_w, orig_h = int(meta["width"]), int(meta["height"])
    print(f"  Dimensiones originales: {orig_w}x{orig_h} (Aspect Ratio: {orig_w/orig_h:.2f})")

    # 2. Análisis de cropdetect
    cmd = [
        FFMPEG, "-hide_banner", "-ss", str(start_sec), "-t", str(duration),
        "-i", video_path, "-vf", "cropdetect=24:16:0", "-f", "null", "-"
    ]
    p = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
    crop_matches = re.findall(r"crop=([0-9]+):([0-9]+):([0-9]+):([0-9]+)", p.stderr)
    
    if crop_matches:
        last_crop = crop_matches[-1]
        w, h, x, y = [int(v) for v in last_crop]
        print(f"  Detección de contenido activo: {w}x{h} en x={x}, y={y}")
    else:
        w, h, x, y = orig_w, orig_h, 0, 0

    # 3. Calcular recomendación 9:16 para primer plano y fondo
    target_ratio = 9 / 16
    rec_fg_w = int(orig_h * 0.75)
    rec_fg_h = int(rec_fg_w * 0.95)
    rec_fg_x = max(0, min(orig_w - rec_fg_w, int(orig_w * 0.45)))
    rec_fg_y = int(orig_h * 0.05)

    print("\n" + "="*70)
    print("CONFIGURACION RECOMENDADA PARA shows.json:")
    print("="*70)
    print(f'"crop_speaker": "crop={rec_fg_w}:{rec_fg_h}:{rec_fg_x}:{rec_fg_y},scale=1080:1040,setsar=1:1",')
    print(f'"crop_background": "crop={int(orig_w*0.8)}:{orig_h}:{int(orig_w*0.1)}:0,scale=270:480,boxblur=20:2,scale=1080:1920,setsar=1:1",')
    print(f'"overlay_y": 260,')
    print(f'"live_pill_y": 1320,')
    print(f'"subs_y": 1460')
    print("="*70 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("video", help="Ruta al video a analizar")
    parser.add_argument("--start", type=float, default=30.0, help="Segundo inicial para muestreo")
    args = parser.parse_args()
    analyze_crop(args.video, args.start)
