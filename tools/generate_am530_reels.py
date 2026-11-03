import os
import sys
import json
import time
import subprocess
from typing import List, Dict, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from core.audio_boundary_auditor import AudioBoundaryAuditor
from core.subtitle_engine import SubtitleEngine, TextQualityAssurance
from core.video_compositor import VideoCompositor
from core.visual_inspector import VisualInspector

FFMPEG = os.path.expandvars(
    r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe"
)
FFPROBE = FFMPEG.replace("ffmpeg.exe", "ffprobe.exe")

SOURCE_VIDEO = os.path.join(BASE_DIR, "..", "..", "02_Entrevistas_Completas", "Entrevista_Johanna_AM530.mp4")
WHISPER_JSON = os.path.join(BASE_DIR, "assets", "am530_whisper.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "..", "01_Reels_Finales_Subtitulados")
TEMP_DIR = os.path.join(BASE_DIR, "temp_am530")
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

SHOW_PROFILE = {
    "name": "Somos Radio AM 530 • Entrevista Johanna Tricarico",
    "crop_speaker": "scale=1080:608,setsar=1:1",
    "crop_background": "scale=270:480,boxblur=25:2,scale=1080:1920,setsar=1:1",
    "overlay_y": 340,
    "live_pill_y": 980,
    "subs_y": 1380,
    "audio_filter": "loudnorm=I=-14:TP=-2.0:LRA=11"
}

REELS_SPEC = [
    {
        "id": "01_Johanna_Caso_Nena_Salta_DNI_Cirugia",
        "title": "Caso Nena de Salta: Suspendieron su Cirugía por Falta de DNI",
        "hook": "LE SUSPENDIERON LA CIRUGÍA POR FALTA DE DNI",
        "live": "JOHANNA TRICARICO • SOMOS RADIO AM 530",
        "start": 112.50,
        "end": 175.75,
        "filename": "01_Johanna_Caso_Nena_Salta_DNI_Cirugia.mp4"
    },
    {
        "id": "02_Johanna_Cancer_No_Espera_Auditorias_Mata",
        "title": "El Cáncer No Va a Esperar una Auditoría: El Estado los Está Matando",
        "hook": "EL CÁNCER NO VA A ESPERAR A UNA AUDITORÍA",
        "live": "ALERTA ONCOLÓGICA • AM 530",
        "start": 300.20,
        "end": 324.20,
        "filename": "02_Johanna_Cancer_No_Espera_Auditorias_Mata.mp4"
    },
    {
        "id": "03_Johanna_Sector_Privado_No_Vio_Tumor_3_Resonancias",
        "title": "En 3 Resonancias Privadas No Vieron el Tumor: El Garrahan Salva Vidas",
        "hook": "EN 3 RESONANCIAS PRIVADAS NO LO VIERON",
        "live": "ALTA COMPLEJIDAD • SOY GARRAHAN",
        "start": 336.00,
        "end": 408.30,
        "filename": "03_Johanna_Sector_Privado_No_Vio_Tumor_3_Resonancias.mp4"
    },
    {
        "id": "04_Johanna_Munecas_Quita_Penas_Plaza_De_Mayo",
        "title": "Marchamos con las Muñecas Quita Penas por los Chicos que No Pueden Hablar",
        "hook": "MARCHAMOS POR LOS QUE NO PUEDEN HABLAR",
        "live": "CONVOCATORIA • 15 DE OCTUBRE",
        "start": 425.00,
        "end": 459.20,
        "filename": "04_Johanna_Munecas_Quita_Penas_Plaza_De_Mayo.mp4"
    },
    {
        "id": "05_Johanna_Caso_Cristian_Santiago_Murio_De_Hambre",
        "title": "Cristian se Murió de Hambre en Santiago: Incluir Salud No Entregó las Leches",
        "hook": "CRISTIAN SE MURIÓ DE HAMBRE POR FALTA DE LECHE",
        "live": "TESTIMONIO URGENTE • SOY GARRAHAN",
        "start": 530.80,
        "end": 562.10,
        "filename": "05_Johanna_Caso_Cristian_Santiago_Murio_De_Hambre.mp4"
    }
]

def load_whisper_words() -> List[Dict[str, Any]]:
    with open(WHISPER_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    all_words = []
    for s in data.get("segments", []):
        for w in s.get("words", []):
            all_words.append({
                "word": w["word"],
                "start": float(w["start"]),
                "end": float(w["end"])
            })
    return all_words

def get_words_for_range(all_words: List[Dict[str, Any]], start: float, end: float) -> List[Dict[str, Any]]:
    slice_words = []
    for w in all_words:
        if w["start"] >= (start - 0.20) and w["end"] <= (end + 0.35):
            # Calcular tiempo relativo respecto al corte inicial
            rel_start = max(0.0, round(w["start"] - start, 3))
            rel_end = max(rel_start + 0.08, round(w["end"] - start, 3))
            slice_words.append({
                "word": w["word"],
                "start": rel_start,
                "end": rel_end
            })
    return slice_words

def process_reel(reel_spec: Dict[str, Any], all_words: List[Dict[str, Any]]) -> str:
    reel_id = reel_spec["id"]
    filename = reel_spec["filename"]
    start_sec = reel_spec["start"]
    end_sec = reel_spec["end"]
    duration = end_sec - start_sec
    out_mp4 = os.path.join(OUTPUT_DIR, filename)

    print(f"\n=======================================================")
    print(f"[*] PROCESANDO: {filename} [{start_sec:.2f}s - {end_sec:.2f}s] ({duration:.1f}s)")
    print(f"    Hook: {reel_spec['hook']}")
    print(f"=======================================================")

    # Paso 1: Extraer rebanada cruda limpia
    raw_slice = os.path.join(TEMP_DIR, f"{reel_id}_raw.mp4")
    cmd_cut = [
        FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-ss", f"{start_sec:.3f}", "-to", f"{end_sec:.3f}",
        "-i", SOURCE_VIDEO,
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        raw_slice
    ]
    subprocess.run(cmd_cut, check=True)

    # Paso 2: Auditoría acústica de límites (Head & Tail gating)
    raw_wav = os.path.join(TEMP_DIR, f"{reel_id}_audio.wav")
    subprocess.run([
        FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-i", raw_slice, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", raw_wav
    ], check=True)

    gating = AudioBoundaryAuditor.validate_boundary_gating(SOURCE_VIDEO, start_sec, end_sec)
    print(f"  [Gating Acústico]: {gating['notes']}")

    # Paso 3: Subtítulos ASS Karaoke con saneamiento fonético
    words = get_words_for_range(all_words, start_sec, end_sec)
    ass_path = os.path.join(TEMP_DIR, f"{reel_id}.ass")
    SubtitleEngine.generate_ass(
        words=words,
        out_path=ass_path,
        font_name="Arial Black",
        font_size=56,
        active_color="&H0000FFFF&",
        y_pos=1380,
        use_dynamic=True
    )

    # Paso 4: Renderizado y Composición Vertical 9:16 a 60 FPS con Outro Card
    VideoCompositor.render_reel(
        raw_slice_mp4=raw_slice,
        ass_path=ass_path,
        show_profile=SHOW_PROFILE,
        live_text=reel_spec["live"],
        out_path=out_mp4
    )

    # Paso 5: Contact Sheet 3x2 e Inspección Visual de fotogramas
    audit_dir = os.path.join(OUTPUT_DIR, "thumbnails", f"{reel_id}_audit")
    try:
        audit_rep = VisualInspector.inspect_video(out_mp4, output_dir=audit_dir)
        print(f"  [Visual Inspector] Contact sheet y reporte visual generado en: {audit_dir}")
    except Exception as e:
        print(f"  [!] Advertencia Visual Inspector: {e}")

    # Paso 6: Verificación de sonoridad LUFS final
    cmd_lufs = [FFMPEG, "-hide_banner", "-i", out_mp4, "-af", "ebur128", "-f", "null", "-"]
    res_lufs = subprocess.run(cmd_lufs, stderr=subprocess.PIPE, text=True)
    import re
    matches = re.findall(r"I:\s*([-\d\.]+)\s*LUFS", res_lufs.stderr)
    lufs_val = matches[-1] if matches else "N/A"
    print(f"  [Sonoridad Final]: {lufs_val} LUFS (Objetivo: -14.0 LUFS)")

    return out_mp4

def main():
    print("[*] INICIANDO PRODUCCIÓN AUTOMATIZADA: SOMOS RADIO AM 530 (5 REELS)")
    all_words = load_whisper_words()
    print(f"    Total palabras en transcripción de audio: {len(all_words)}")

    generated = []
    for spec in REELS_SPEC:
        out = process_reel(spec, all_words)
        generated.append(out)

    print("\n=======================================================")
    print(f"[OK] ¡LOS 5 REELS DE AM 530 HAN SIDO PRODUCIDOS CON ÉXITO!")
    for g in generated:
        print(f"  • {os.path.basename(g)}")
    print("=======================================================\n")

if __name__ == "__main__":
    main()
