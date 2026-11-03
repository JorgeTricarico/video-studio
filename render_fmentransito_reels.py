import os
import sys
import json
import subprocess
import time
import shutil
import whisper
from reels_production_harness import SubtitleEngine, PostRenderAuditor, FFMPEG, FFPROBE

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VIDEO_INPUT = r"C:\Users\admin\Desktop\Reels_Instagram_Edicion\02_Entrevistas_Completas\Entrevista_Johanna_FMEnTransito.mp4"
BADGE_PNG = r"C:\Users\admin\Desktop\Reels_Instagram_Edicion\assets\logos\soygarrahan_badge.png"
OUTRO_PNG = r"C:\Users\admin\Desktop\Reels_Instagram_Edicion\assets\logos\outro_card.png"
OUT_DIR = r"C:\Users\admin\Desktop\Reels_Instagram_Edicion\REELS_Octubre_Johanna_FMEnTransito"
FINAL_DIR = r"C:\Users\admin\Desktop\Reels_Instagram_Edicion\01_Reels_Finales_Subtitulados"

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(FINAL_DIR, exist_ok=True)
os.makedirs("assets/fmentransito_slices", exist_ok=True)

REELS_SPECS = [
    {
        "id": "01_Johanna_Vencimiento_Ley_Pediatrica_Colectivo",
        "title": "El 21 de Octubre Vence la Ley de Salud Pediátrica",
        "hook": "EL 21 DE OCTUBRE SE VENCE LA LEY",
        "live": "JOHANNA TRICARICO • SOY GARRAHAN",
        "start": 126.5,
        "end": 202.6,
        "filename": "01_Johanna_Vencimiento_Ley_Pediatrica_21Oct.mp4"
    },
    {
        "id": "02_Johanna_Nombre_y_Apellido_Voto_Legisladores",
        "title": "Que se Sepa con Nombre y Apellido Quién Vota a Favor y Quién en Contra",
        "hook": "QUE SE SEPA CON NOMBRE Y APELLIDO",
        "live": "EN VIVO • FM EN TRANSITO",
        "start": 331.5,
        "end": 368.0,
        "filename": "02_Johanna_Nombre_y_Apellido_Voto_Legisladores.mp4"
    },
    {
        "id": "03_Johanna_Motosierra_Garrahan_Presupuesto",
        "title": "Motosierra al Hospital Garrahan en el Presupuesto",
        "hook": "LE METIERON LA MOTOSIERRA AL GARRAHAN",
        "live": "ALERTA PRESUPUESTO NACIONAL",
        "start": 247.0,
        "end": 299.3,
        "filename": "03_Johanna_Motosierra_Garrahan_Presupuesto.mp4"
    },
    {
        "id": "04_Johanna_F16_vs_Discapacidad_Yates_de_Lujo",
        "title": "Más Plata para los F16 que para Discapacidad",
        "hook": "MAS PLATA A LOS F16 QUE A DISCAPACIDAD",
        "live": "EMERGENCIA EN DISCAPACIDAD",
        "start": 905.5,
        "end": 1003.8,
        "filename": "04_Johanna_F16_vs_Discapacidad_Yates_Lujo.mp4"
    },
    {
        "id": "05_Johanna_Llamado_Familias_Pais_Caso_Nena_Cobrada",
        "title": "Llamado a las Familias de Todo el País: Exijan a Diputados y Senadores",
        "hook": "HINCHENLE A SUS DIPUTADOS Y SENADORES",
        "live": "CONVOCATORIA FEDERAL • SOY GARRAHAN",
        "start": 1085.35,
        "end": 1135.8,
        "filename": "05_Johanna_Llamado_Familias_Pais_Caso_Nena.mp4"
    }
]

def render_all():
    print("[*] Iniciando motor de renderizado profesional para FM En Tránsito (5 Reels)")
    print("Cargando modelo Whisper 'base'...")
    model = whisper.load_model("base")

    badge_escaped = os.path.abspath(BADGE_PNG).replace("\\", "/").replace(":", "\\:")
    target_idx = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else None

    for idx, spec in enumerate(REELS_SPECS, 1):
        if target_idx is not None and idx != target_idx:
            continue
        print(f"\n{'='*70}")
        print(f"[{idx}/5] PROCESANDO: {spec['title']}")
        print(f"      Hook: {spec['hook']}")
        print(f"      Rango: {spec['start']:.1f}s -> {spec['end']:.1f}s (Duración voz: {spec['end']-spec['start']:.1f}s)")
        print(f"{'='*70}")

        rid = spec["id"]
        dur = spec["end"] - spec["start"]

        slice_wav = f"assets/fmentransito_slices/{rid}.wav"
        ass_path = f"assets/fmentransito_slices/{rid}_subs.ass"
        raw_slice_mp4 = f"assets/fmentransito_slices/{rid}_raw.mp4"

        cmd_wav = [
            FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
            "-ss", f"{spec['start']:.3f}", "-t", f"{dur:.3f}",
            "-i", VIDEO_INPUT,
            "-vn", "-ar", "16000", "-ac", "1",
            slice_wav
        ]
        subprocess.run(cmd_wav, check=True)

        print("  -> Transcribiendo con Whisper para subtítulos palabra por palabra...")
        trans_res = model.transcribe(
            slice_wav, language="es", word_timestamps=True,
            initial_prompt="Hospital Garrahan, Johanna Tricarico, Ley de Salud Pediátrica, residencias dotacionales, yates de lujo, nena, Bayron, presupuesto, F16."
        )
        words = []
        for s in trans_res["segments"]:
            for w in s.get("words", []):
                words.append({
                    "word": w["word"].strip(),
                    "start": round(w["start"], 3),
                    "end": round(w["end"], 3)
                })
        print(f"  -> {len(words)} palabras identificadas con timestamp.")

        # Generar ASS con el motor uniforme agrandado (Fontsize=58 constante)
        SubtitleEngine.generate_ass(
            words, ass_path,
            font_name="Arial Black", font_size=58,
            active_color="&H0000FFFF&", y_pos=1460,
            max_hang_time=1.4, use_dynamic=True
        )

        cmd_vcut = [
            FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
            "-ss", f"{spec['start']:.3f}", "-t", f"{dur:.3f}",
            "-i", VIDEO_INPUT,
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k",
            raw_slice_mp4
        ]
        subprocess.run(cmd_vcut, check=True)

        probe_res = subprocess.check_output([
            FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", raw_slice_mp4
        ], text=True)
        speech_duration = float(probe_res.strip())
        outro_duration = 3.2
        total_duration = speech_duration + outro_duration

        ass_escaped = os.path.abspath(ass_path).replace("\\", "/").replace(":", "\\:")

        clean_hook = spec["hook"].upper().replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U").replace("Ñ", "N").replace(":", "\\:")
        clean_live = spec["live"].upper().replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U").replace("Ñ", "N").replace(":", "\\:")
        audio_filter = "volume=1.8dB,loudnorm=I=-14:TP=-2.0:LRA=11" if "05" in rid else "loudnorm=I=-14:TP=-2.0:LRA=11"

        filter_complex = (
            # 1. Fondo desenfocado 1080x1920 con SAR 1:1
            "[0:v]crop=960:1080:960:0,scale=270:480,boxblur=20:2,scale=1080:1920,setsar=1:1,eq=brightness=-0.14:contrast=1.1[bg]; "
            # 2. Foreground Johanna limpio con SAR 1:1
            "[0:v]crop=800:770:1060:26,scale=1080:1040,setsar=1:1[fg]; "
            "[bg][fg]overlay=0:260[v_comp]; "
            # 3. Badge Soy Garrahan borderless premium relleno superior (980x170 a y=35)
            f"movie='{badge_escaped}'[badge_raw]; "
            "[v_comp][badge_raw]overlay=(W-w)/2:35:eof_action=repeat[v_brand]; "
            # 4. Live Pill indicador a y=1320
            f"[v_brand]drawtext=text='{clean_live}':fontfile='C\\:/Windows/Fonts/arialbd.ttf':fontsize=28:"
            f"fontcolor=white:box=1:boxcolor=0xCC0000@0.92:boxborderw=10:x=(w-text_w)/2:y=1320[v_live]; "
            # 5. Subtítulos Karaoke Dinámicos Adaptables (tamaño auto-escalado)
            f"[v_live]subtitles='{ass_escaped}'[v_subs]; "
            # 6. Outro Card estandarizado oficial
            f"[v_subs]tpad=stop_duration={outro_duration:.2f}:stop_mode=clone[v_pad]; "
            f"[1:v]format=rgba,fade=t=in:st={speech_duration:.2f}:d=0.5:alpha=1[outro_raw]; "
            f"[v_pad][outro_raw]overlay=0:0:shortest=1:enable='gte(t,{speech_duration:.2f})'[v_final]; "
            # 7. Audio Loudnorm y Fadeout
            f"[0:a]apad=pad_dur={outro_duration:.2f},afade=t=out:st={speech_duration:.2f}:d=1.5,{audio_filter}[a_final]"
        )

        out_local = os.path.join(OUT_DIR, spec["filename"])
        out_final = os.path.join(FINAL_DIR, spec["filename"])

        cmd_render = [
            FFMPEG, "-y", "-hide_banner", "-loglevel", "warning",
            "-i", raw_slice_mp4,
            "-loop", "1", "-i", OUTRO_PNG,
            "-filter_complex", filter_complex,
            "-map", "[v_final]", "-map", "[a_final]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-pix_fmt", "yuv420p", "-r", "60",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-t", f"{total_duration:.2f}",
            "-movflags", "+faststart",
            out_local
        ]

        print(f"  -> Ejecutando FFmpeg render profesional a {out_local}...")
        t_start = time.time()
        subprocess.run(cmd_render, check=True)
        t_render = time.time() - t_start
        print(f"  -> [OK] Render completado en {t_render:.1f}s!")

        shutil.copy2(out_local, out_final)
        print(f"  -> Copiado a carpeta unificada: {out_final}")

        qa = PostRenderAuditor.audit_reel(out_final)
        print(f"  -> [QA AUDIT] Res: {qa['width']}x{qa['height']} | SAR: {qa['sar']} | FPS: {qa['fps']} | Audio: {qa['lufs']} LUFS -> {qa['status']}")

    print("\n" + "="*70)
    print("[SUCCESS] ¡Los 5 Reels de FM En Tránsito han sido re-renderizados con la nueva identidad borderless y subtítulos dinámicos!")
    print("="*70)

if __name__ == "__main__":
    render_all()
