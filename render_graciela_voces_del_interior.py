import os
import sys
import json
import subprocess
import time
import shutil

sys.path.insert(0, os.path.abspath("."))
from core.subtitle_engine import SubtitleEngine, TextQualityAssurance

FFMPEG = os.path.expandvars(
    r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe"
)
FFPROBE = FFMPEG.replace("ffmpeg.exe", "ffprobe.exe")

SRC_VIDEO = r"C:\Users\admin\Downloads\WhatsApp Video 2026-10-06 at 22.36.16.mp4"
BADGE_PNG = os.path.abspath(r"assets\logos\soygarrahan_badge.png")
OUTRO_PNG = os.path.abspath(r"assets\logos\outro_card.png")

OUTPUT_DIR = "REELS_Octubre_Graciela_Voces_Del_Interior"
FINAL_REPO = "01_Reels_Finales_Subtitulados"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(FINAL_REPO, exist_ok=True)
os.makedirs("scratch/temp_graciela", exist_ok=True)

REELS = [
    {
        "id": "01_Graciela_La_Ilusion_De_La_Prepaga_Garrahan",
        "title": "La Ilusión de la Prepaga: Llegar al Garrahan Desesperado",
        "live": "GRACIELA DEL VALLE • SOY GARRAHAN",
        "start": 54.50,
        "end": 121.25,
        "filename": "01_Graciela_La_Ilusion_De_La_Prepaga_Garrahan.mp4",
        "words_file": "scratch/sanitized_words/reel_01_words.json"
    },
    {
        "id": "02_Graciela_Que_Es_Soy_Garrahan_Red_Federal",
        "title": "Qué es Soy Garrahan: Red Federal en Defensa de la Salud Pediátrica",
        "live": "GRACIELA DEL VALLE • SOY GARRAHAN",
        "start": 262.60,
        "end": 312.00,
        "filename": "02_Graciela_Que_Es_Soy_Garrahan_Red_Federal.mp4",
        "words_file": "scratch/sanitized_words/reel_02_words.json"
    },
    {
        "id": "03_Graciela_21Oct_Cae_Ley_Emergencia_Pediatrica",
        "title": "21 de Octubre: Cae la Ley de Emergencia Pediátrica",
        "live": "ALERTA • VENCE LEY DE EMERGENCIA",
        "start": 429.70,
        "end": 489.00,
        "filename": "03_Graciela_21Oct_Cae_Ley_Emergencia_Pediatrica.mp4",
        "words_file": "scratch/sanitized_words/reel_03_words.json"
    },
    {
        "id": "04_Graciela_El_Garrahan_No_Gano_Hablo_Al_Distraido",
        "title": "El Garrahan NO Ganó: Le Hablo al Distraído",
        "live": "EL GARRAHAN NO GANO • EN LUCHA",
        "start": 489.20,
        "end": 538.00,
        "filename": "04_Graciela_El_Garrahan_No_Gano_Hablo_Al_Distraido.mp4",
        "words_file": "scratch/sanitized_words/reel_04_words.json"
    },
    {
        "id": "05_Graciela_15Oct_Plaza_De_Mayo_Quita_Penas",
        "title": "15 de Octubre 15hs: Plaza de Mayo con las Quita Penas",
        "live": "CONVOCATORIA • 15 DE OCTUBRE 15 HS",
        "start": 538.10,
        "end": 581.50,
        "filename": "05_Graciela_15Oct_Plaza_De_Mayo_Quita_Penas.mp4",
        "words_file": "scratch/sanitized_words/reel_05_words.json"
    }
]

print("===================================================================")
print("INICIANDO PRODUCCIÓN DE 5 REELS: GRACIELA DEL VALLE FERREIRA")
print("===================================================================")

badge_esc = BADGE_PNG.replace("\\", "/").replace(":", "\\:")
outro_esc = OUTRO_PNG.replace("\\", "/").replace(":", "\\:")
fg_filter = "crop=288:512:456:45,scale=1080:1920:flags=lanczos,unsharp=5:5:0.8:3:3:0.4,setsar=1:1"

rendered_files = []

for idx, r in enumerate(REELS, start=1):
    print(f"\n--- [{idx}/5] Procesando: {r['title']} ---")
    t0_reel = time.time()
    
    slice_mp4 = f"scratch/temp_graciela/slice_{idx:02d}.mp4"
    ass_path = f"scratch/temp_graciela/subs_{idx:02d}.ass"
    out_mp4 = os.path.join(OUTPUT_DIR, r["filename"])
    
    # 1. Cortar slice de video
    print(f"  [1/4] Cortando slice limpio ({r['start']}s -> {r['end']}s)...")
    subprocess.run([
        FFMPEG, "-y", "-ss", str(r["start"]), "-to", str(r["end"]),
        "-i", SRC_VIDEO, "-c", "copy", slice_mp4
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    
    # 2. Generar subtítulos .ass auditados
    print("  [2/4] Generando subtitulos Hormozi 58pt con TQA...")
    with open(r["words_file"], "r", encoding="utf-8") as f:
        words = json.load(f)
    
    TextQualityAssurance._config = None
    clean_words = TextQualityAssurance.sanitize_words(words)
    SubtitleEngine.generate_ass(clean_words, ass_path, font_size=58, y_pos=1450)
    
    # Obtener duracion real de voz
    res = subprocess.check_output([
        FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", slice_mp4
    ], text=True)
    speech_dur = float(res.strip())
    outro_dur = 3.2
    total_dur = speech_dur + outro_dur
    
    # 3. Construir filtergraph y renderizar
    print(f"  [3/4] Renderizando Reel a 1080x1920 60fps (Duración voz: {speech_dur:.2f}s + outro {outro_dur}s)...")
    ass_esc = os.path.abspath(ass_path).replace("\\", "/").replace(":", "\\:")
    clean_live = r["live"].replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U").replace("Ñ", "N").replace(":", "\\:")
    
    filter_complex = (
        f"[0:v]{fg_filter}[fg]; "
        f"movie='{badge_esc}'[badge_raw]; "
        f"[fg][badge_raw]overlay=(W-w)/2:35:eof_action=repeat[v_brand]; "
        f"[v_brand]drawtext=text='{clean_live}':fontfile='C\\:/Windows/Fonts/arialbd.ttf':fontsize=28:"
        f"fontcolor=white:box=1:boxcolor=0xCC0000@0.92:boxborderw=10:x=(w-text_w)/2:y=230[v_live]; "
        f"[v_live]subtitles='{ass_esc}'[v_subs]; "
        f"[v_subs]tpad=stop_duration={outro_dur:.2f}:stop_mode=clone[v_pad]; "
        f"[1:v]format=rgba,fade=t=in:st={speech_dur:.2f}:d=0.5:alpha=1[outro_raw]; "
        f"[v_pad][outro_raw]overlay=0:0:shortest=1:enable='gte(t,{speech_dur:.2f})'[v_final]; "
        f"[0:a]apad=pad_dur={outro_dur:.2f},afade=t=out:st={speech_dur:.2f}:d=1.5,loudnorm=I=-14:TP=-2.0:LRA=11[a_final]"
    )
    
    cmd_render = [
        FFMPEG, "-y", "-hide_banner", "-loglevel", "warning",
        "-i", slice_mp4,
        "-loop", "1", "-i", OUTRO_PNG,
        "-filter_complex", filter_complex,
        "-map", "[v_final]", "-map", "[a_final]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-r", "60",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-t", f"{total_dur:.2f}",
        "-movflags", "+faststart",
        out_mp4
    ]
    
    subprocess.run(cmd_render, check=True)
    
    # 4. Copiar a repositorio central
    final_dest = os.path.join(FINAL_REPO, r["filename"])
    shutil.copy2(out_mp4, final_dest)
    rendered_files.append(out_mp4)
    print(f"  [4/4] [OK] Completado en {time.time() - t0_reel:.1f}s -> {out_mp4}")

print("\n===================================================================")
print(f"PRODUCCIÓN FINALIZADA: {len(rendered_files)} REELS RENDERIZADOS CON ÉXITO")
print("===================================================================")
