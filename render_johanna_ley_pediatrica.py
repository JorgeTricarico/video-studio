import os
import sys
import json
import subprocess
import time
import shutil
from reels_production_harness import SubtitleEngine, PostRenderAuditor, FFMPEG, FFPROBE

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VIDEO_INPUT = r"C:\Users\admin\Desktop\Reels_Instagram_Edicion\02_Entrevistas_Completas\Entrevista_Johanna_Radio10.mp4"
BADGE_PNG = r"C:\Users\admin\Desktop\Reels_Instagram_Edicion\assets\logos\soygarrahan_badge.png"
OUTRO_PNG = r"C:\Users\admin\Desktop\Reels_Instagram_Edicion\assets\logos\outro_card.png"
OUT_DIR = r"C:\Users\admin\Desktop\Reels_Instagram_Edicion\REELS_Octubre_Johanna_Nueva_Ley_Pediatrica"
FINAL_DIR = r"C:\Users\admin\Desktop\Reels_Instagram_Edicion\01_Reels_Finales_Subtitulados"
WHISPER_JSON = "assets/johanna_radio10_whisper.json"

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(FINAL_DIR, exist_ok=True)

def render_reel(slices, words, hook_text, live_text, out_mp4):
    print(f"\n=======================================================")
    print(f"[*] RENDERIZANDO: {os.path.basename(out_mp4)}")
    print(f"    Hook: '{hook_text}'")
    print(f"=======================================================")
    t0 = time.time()

    # 1. Pre-corte de rebanadas
    temp_slices = []
    for i, sl in enumerate(slices):
        s_file = f"temp_raw_slice_{i}.mp4"
        dur = sl["end"] - sl["start"]
        cmd = [
            FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
            "-ss", f"{sl['start']:.3f}", "-t", f"{dur:.3f}",
            "-i", VIDEO_INPUT,
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k",
            s_file
        ]
        subprocess.run(cmd, check=True)
        temp_slices.append(s_file)

    concat_txt = "temp_concat_list.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for sf in temp_slices:
            f.write(f"file '{sf}'\n")

    condensed_mp4 = "temp_condensed.mp4"
    cmd_cat = [
        FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", concat_txt,
        "-c", "copy", condensed_mp4
    ]
    subprocess.run(cmd_cat, check=True)

    res = subprocess.check_output([
        FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", condensed_mp4
    ], text=True)
    speech_duration = float(res.strip())
    outro_duration = 3.2
    total_duration = speech_duration + outro_duration

    # 2. Generar subtítulos ASS con motor uniforme agrandado (Fontsize=58 constante)
    ass_path = f"temp_subtitles_{int(time.time())}.ass"
    SubtitleEngine.generate_ass(
        words, ass_path,
        font_name="Arial Black", font_size=58,
        active_color="&H0000FFFF&", y_pos=1400,
        max_hang_time=1.4, use_dynamic=True
    )
    ass_escaped = os.path.abspath(ass_path).replace("\\", "/").replace(":", "\\:")

    # 3. VFX Filtergraph
    badge_escaped = os.path.abspath(BADGE_PNG).replace("\\", "/").replace(":", "\\:")
    clean_live = live_text.upper().replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U").replace("Ñ", "N").replace(":", "\\:")

    filter_complex = (
        # Fondo desenfocado 1080x1920 con SAR 1:1 nativo
        "[0:v]crop=608:1080:656:0,scale=270:480,boxblur=20:2,scale=1080:1920,setsar=1:1,eq=brightness=-0.14:contrast=1.1[bg]; "
        # Video principal encuadrado limpiamente en cabina con SAR 1:1
        "[0:v]crop=840:705:540:60,scale=1080:906,setsar=1:1[fg]; "
        "[bg][fg]overlay=0:260[v_comp]; "
        # Badge Soy Garrahan oficial borderless relleno superior (980x170 a y=35)
        f"movie='{badge_escaped}'[badge_raw]; "
        "[v_comp][badge_raw]overlay=(W-w)/2:35:eof_action=repeat[v_brand]; "
        # Live pill indicator a y=1190
        f"[v_brand]drawtext=text='{clean_live}':fontfile='C\\:/Windows/Fonts/arialbd.ttf':fontsize=28:"
        f"fontcolor=white:box=1:boxcolor=0xCC0000@0.92:boxborderw=10:x=(w-text_w)/2:y=1190[v_live]; "
        # Subtítulos Karaoke Dinámicos Adaptables (tamaño auto-escalado)
        f"[v_live]subtitles='{ass_escaped}'[v_subs]; "
        # Outro Card final estandarizada 100% opaca
        f"[v_subs]tpad=stop_duration={outro_duration:.2f}:stop_mode=clone[v_pad]; "
        f"[1:v]format=rgba,fade=t=in:st={speech_duration:.2f}:d=0.5:alpha=1[outro_raw]; "
        f"[v_pad][outro_raw]overlay=0:0:shortest=1:enable='gte(t,{speech_duration:.2f})'[v_final]; "
        # Audio loudnorm y fadeout en el outro
        f"[0:a]apad=pad_dur={outro_duration:.2f},afade=t=out:st={speech_duration:.2f}:d=1.5,loudnorm=I=-14:TP=-2.0:LRA=11[a_final]"
    )

    cmd_render = [
        FFMPEG, "-y", "-hide_banner", "-loglevel", "warning",
        "-i", condensed_mp4,
        "-loop", "1", "-i", OUTRO_PNG,
        "-filter_complex", filter_complex,
        "-map", "[v_final]", "-map", "[a_final]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-r", "60",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-t", f"{total_duration:.2f}",
        "-movflags", "+faststart",
        out_mp4
    ]

    subprocess.run(cmd_render, check=True)

    # Limpieza
    for sf in temp_slices:
        if os.path.exists(sf):
            os.remove(sf)
    if os.path.exists(concat_txt):
        os.remove(concat_txt)
    if os.path.exists(condensed_mp4):
        os.remove(condensed_mp4)
    if os.path.exists(ass_path):
        os.remove(ass_path)

    elapsed = time.time() - t0
    print(f"  [OK] Renderizado completado en {elapsed:.1f}s: {out_mp4} (Total: {total_duration:.1f}s)")

    qa = PostRenderAuditor.audit_reel(out_mp4)
    print(f"  -> [QA AUDIT] Res: {qa['width']}x{qa['height']} | SAR: {qa['sar']} | FPS: {qa['fps']} | Audio: {qa['lufs']} LUFS -> {qa['status']}")
    return out_mp4

print("Render engine initialized successfully.")
