import os
import sys
import json
import time
import subprocess
import shutil
import argparse
from typing import List, Dict, Any

# Ensure core and project are in path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from core.audio_boundary_auditor import AudioBoundaryAuditor
from core.subtitle_engine import SubtitleEngine, TextQualityAssurance
from core.qa_auditor import PostRenderAuditor
from core.visual_inspector import VisualInspector

FFMPEG = os.path.expandvars(
    r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe"
)
FFPROBE = FFMPEG.replace("ffmpeg.exe", "ffprobe.exe")

SRC_VIDEO = r"C:\Users\admin\Downloads\WhatsApp Video 2026-10-14 at 13.49.59.mp4"
BADGE_PNG = os.path.abspath(r"assets\logos\soygarrahan_badge.png")
OUTRO_PNG = os.path.abspath(r"assets\logos\outro_card.png")
WHISPER_JSON = os.path.abspath(r"scratch\analysis_2026_10_14\transcript.json")

OUTPUT_LOCAL = os.path.join(BASE_DIR, "REELS_Octubre_Johanna_Diputados")
FINAL_REPO = os.path.join(BASE_DIR, "..", "..", "01_Reels_Finales_Subtitulados")
COPIES_DIR = os.path.join(BASE_DIR, "..", "..", "05_Documentos_Copies_y_Transcripciones", "Copys_Redes")
TEMP_DIR = os.path.join(BASE_DIR, "scratch", "temp_render_diputados")

DRIVE_CAMPAIGN = r"G:\.shortcut-targets-by-id\1ksGmRs2YYQhI4pF6HMkNZ886H4mvIKF2\VIDEOS IA SOYGARRAHAN\06_Campaña_Octubre_Johanna_Diputados_ComisionSalud"

os.makedirs(OUTPUT_LOCAL, exist_ok=True)
os.makedirs(FINAL_REPO, exist_ok=True)
os.makedirs(COPIES_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

REELS_SPEC = [
    {
        "id": "01_Johanna_Cuanto_Vale_La_Vida_De_Un_Nino",
        "title": "¿Cuánto vale la vida de un niño para este país? (Mensaje a los Diputados)",
        "hook": "¿CUÁNTO VALE LA VIDA DE UN NIÑO PARA ESTE PAÍS?",
        "live": "JOHANNA TRICARICO • COMISIÓN DE SALUD DIPUTADOS",
        "start": 649.20,
        "end": 695.30,
        "priority": 1,
        "filename": "01_Johanna_Cuanto_Vale_La_Vida_De_Un_Nino.mp4",
        "copy_lead": "🔴 \"LA PREGUNTA NO ES CUÁNTO CUESTA CUIDAR A NUESTRAS INFANCIAS. LA PREGUNTA ES CUÁNTO VALE LA VIDA DE UN NIÑO PARA ESTE PAÍS\".\n\nJohanna Tricarico de @soygarrahan.ok le habló cara a cara a los diputados de la Nación en el Congreso.",
        "hashtags": "#ElGarrahanSalvaVidas #Garrahan #SaludPediatrica #Congreso #Diputados #SaludPublica #SoyGarrahan"
    },
    {
        "id": "02_Johanna_Dejen_De_Mirar_Las_Planillas",
        "title": "Dejen de mirar las planillas presupuestarias: El Garrahan salva vidas",
        "hook": "DEJEN DE MIRAR LAS PLANILLAS Y NÚMEROS",
        "live": "JOHANNA TRICARICO • CARTA DE LAS FAMILIAS",
        "start": 105.20,
        "end": 165.60,
        "priority": 1,
        "filename": "02_Johanna_Dejen_De_Mirar_Las_Planillas.mp4",
        "copy_lead": "🔴 \"DEJEN DE MIRAR LOS NÚMEROS Y LAS PLANILLAS. EL GARRAHAN NO ES UNA OPCIÓN ENTRE VARIAS: ES LA ÚNICA OPORTUNIDAD PARA QUE NUESTROS HIJOS VIVAN\".\n\nCarta colectiva de las mamás de todo el país ante los legisladores nacionales.",
        "hashtags": "#SaludPediatrica #PresupuestoGarrahan #LeyDeSaludPediatrica #SoyGarrahan #SaludPublica #Garrahan"
    },
    {
        "id": "03_Johanna_No_Es_Un_Ajuste_Es_Exterminio",
        "title": "No es un ajuste, es un plan de exterminio (Necropolítica) [v1 Original]",
        "hook": "NO ES UN AJUSTE, ES UN PLAN DE EXTERMINIO",
        "live": "JOHANNA TRICARICO • COMISIÓN DE SALUD",
        "start": 58.85,
        "end": 104.50,
        "priority": 2,
        "filename": "03_Johanna_No_Es_Un_Ajuste_Es_Exterminio.mp4",
        "copy_lead": "🔴 \"NO HABLARÍA DE UN PLAN DE AJUSTE, HABLARÍA DE UN PLAN DE EXTERMINIO: NECROPOLÍTICA. QUIÉN DECIDE QUIÉN VIVE Y QUIÉN MUERE LO ESTÁN HACIENDO CON NUESTROS HIJOS\".\n\nContundente intervención de Johanna Tricarico en la Cámara de Diputados (Versión Original).",
        "hashtags": "#Necropolitica #AjusteEnSalud #ElGarrahanSalvaVidas #Garrahan #Diputados #SoyGarrahan"
    },
    {
        "id": "03_Johanna_No_Es_Un_Ajuste_Es_Exterminio_v2",
        "title": "No es un ajuste, es un plan de exterminio (Necropolítica) [v2 Editada sin trabas]",
        "hook": "NO ES UN AJUSTE, ES UN PLAN DE EXTERMINIO",
        "live": "JOHANNA TRICARICO • COMISIÓN DE SALUD",
        "slices": [
            {"start": 58.85, "end": 76.40},
            {"start": 78.85, "end": 104.50}
        ],
        "priority": 2,
        "filename": "03_Johanna_No_Es_Un_Ajuste_Es_Exterminio_v2.mp4",
        "copy_lead": "🔴 \"NO HABLARÍA DE UN PLAN DE AJUSTE, HABLARÍA DE UN PLAN DE EXTERMINIO: NECROPOLÍTICA. QUIÉN DECIDE QUIÉN VIVE Y QUIÉN MUERE LO ESTÁN HACIENDO CON NUESTROS HIJOS\".\n\nContundente intervención de Johanna Tricarico en la Cámara de Diputados (Versión Editada Sin Trabas).",
        "hashtags": "#Necropolitica #AjusteEnSalud #ElGarrahanSalvaVidas #Garrahan #Diputados #SoyGarrahan"
    },
    {
        "id": "04_Johanna_Vence_Ley_Emergencia_Pediatrica",
        "title": "Nuestros hijos no se curan porque se venza una ley (Ley 27.796)",
        "hook": "NUESTROS HIJOS NO SE CURAN PORQUE SE VENZA UNA LEY",
        "live": "ALERTA • VENCE LEY DE EMERGENCIA",
        "start": 291.45,
        "end": 353.30,
        "priority": 2,
        "filename": "04_Johanna_Vence_Ley_Emergencia_Pediatrica.mp4",
        "copy_lead": "⚠️ \"LA EMERGENCIA PUEDE VENCER EN LOS PAPELES, PERO LA NECESIDAD DE NUESTROS HIJOS SIGUE VIVA TODOS LOS DÍAS\".\n\nExigimos el tratamiento urgente de la Ley de Salud Pediátrica (Expediente 4981-D-2026).",
        "hashtags": "#LeyEmergenciaPediatrica #Ley27796 #GarrahanEnLucha #SaludPediatrica #SoyGarrahan"
    },
    {
        "id": "05_Johanna_Las_Enfermedades_No_Preguntan_Que_Votaste",
        "title": "Las enfermedades no preguntan a quién votaste",
        "hook": "LA ENFERMEDAD NO PREGUNTA A QUIÉN VOTASTE",
        "live": "SOY GARRAHAN • DERECHOS HUMANOS",
        "start": 406.25,
        "end": 443.05,
        "priority": 2,
        "filename": "05_Johanna_Las_Enfermedades_No_Preguntan_Que_Votaste.mp4",
        "copy_lead": "🔴 \"LAS ENFERMEDADES DE NUESTROS HIJOS NO PREGUNTAN A QUIÉN VOTAMOS NI DE QUÉ PARTIDO SOMOS. LA SALUD PÚBLICA SOSTIENE LA VIDA DE NUESTRO PUEBLO\".\n\nEl Garrahan salva vidas sin importar banderas políticas.",
        "hashtags": "#SaludPublica #SinBanderas #ElGarrahanSalvaVidas #Garrahan #Diputados #SoyGarrahan"
    },
    {
        "id": "06_Johanna_Detras_De_Cada_Numero_Hay_Un_Nino",
        "title": "Detrás de cada número hay un niño: No queremos venir a contar que murieron",
        "hook": "DETRÁS DE CADA NÚMERO HAY UN NIÑO",
        "live": "JOHANNA TRICARICO • COMISIÓN DE SALUD",
        "start": 498.90,
        "end": 545.35,
        "priority": 2,
        "filename": "06_Johanna_Detras_De_Cada_Numero_Hay_Un_Nino.mp4",
        "copy_lead": "🔴 \"DETRÁS DE CADA NÚMERO HAY UN NIÑO. NO QUEREMOS LLEGAR A ESTE CONGRESO PARA CONTARLES QUE PERDIMOS A NUESTROS HIJOS\".\n\nResponsabilidad política directa frente a la salud pediátrica.",
        "hashtags": "#NoSonNumeros #SonVidas #Garrahan #SaludPediatrica #Congreso #SoyGarrahan"
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

def get_relative_words(all_words: List[Dict[str, Any]], start: float, end: float) -> List[Dict[str, Any]]:
    rel_words = []
    for w in all_words:
        if w["start"] >= (start - 0.20) and w["end"] <= (end + 0.35):
            r_st = max(0.0, round(w["start"] - start, 3))
            r_en = max(r_st + 0.08, round(w["end"] - start, 3))
            rel_words.append({
                "word": w["word"],
                "start": r_st,
                "end": r_en
            })
    return rel_words

def render_single_reel(r: Dict[str, Any], all_words: List[Dict[str, Any]], force: bool = False) -> str:
    rid = r["id"]
    filename = r["filename"]
    live_txt = r["live"]
    
    out_mp4 = os.path.join(OUTPUT_LOCAL, filename)
    slice_mp4 = os.path.join(TEMP_DIR, f"{rid}_slice.mp4")
    ass_path = os.path.join(TEMP_DIR, f"{rid}_subs.ass")
    campaign_repo = os.path.join(FINAL_REPO, "06_Campaña_Octubre_Johanna_Diputados_ComisionSalud")
    os.makedirs(campaign_repo, exist_ok=True)
    
    if "slices" in r:
        slices = r["slices"]
        total_slice_dur = sum(sl["end"] - sl["start"] for sl in slices)
        print(f"\n=======================================================")
        print(f"🎬 RENDERIZANDO (MULTI-CORTE): {r['title']}")
        print(f"   Slices: {len(slices)} fragmentos (Duración voz: {total_slice_dur:.2f}s)")
        print(f"   Hook: {r['hook']}")
        print(f"=======================================================")
    else:
        st = r["start"]
        en = r["end"]
        print(f"\n=======================================================")
        print(f"🎬 RENDERIZANDO: {r['title']}")
        print(f"   Clip: {st:.2f}s -> {en:.2f}s (Duración voz: {en - st:.2f}s)")
        print(f"   Hook: {r['hook']}")
        print(f"=======================================================")

    if not force and os.path.exists(out_mp4) and os.path.getsize(out_mp4) > 5000000:
        print(f"  [i] Video ya renderizado y verificado: {out_mp4} ({os.path.getsize(out_mp4)/1024/1024:.1f} MB)")
        central_file = os.path.join(campaign_repo, filename)
        central_qa = os.path.join(campaign_repo, os.path.splitext(filename)[0] + ".qa.json")
        if not os.path.exists(central_file):
            shutil.copy2(out_mp4, central_file)
        if os.path.exists(os.path.splitext(out_mp4)[0] + ".qa.json") and not os.path.exists(central_qa):
            shutil.copy2(os.path.splitext(out_mp4)[0] + ".qa.json", central_qa)
        return out_mp4
    
    # 1. Cortar slice exacto (simple o multi-slice con empalme limpio)
    if "slices" in r:
        print(f"  [1/4] Cortando y ensamblando {len(slices)} slices de video sin tartamudeo...")
        slice_parts = []
        for idx, sl in enumerate(slices):
            st_i = sl["start"]
            en_i = sl["end"]
            part_mp4 = os.path.join(TEMP_DIR, f"{rid}_part_{idx}.mp4")
            cmd_cut = [
                FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                "-ss", f"{st_i:.3f}", "-to", f"{en_i:.3f}",
                "-i", SRC_VIDEO,
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "17",
                "-c:a", "aac", "-b:a", "192k",
                part_mp4
            ]
            subprocess.run(cmd_cut, check=True)
            slice_parts.append(part_mp4)
            
        inputs = []
        for p in slice_parts:
            inputs.extend(["-i", p])
        filter_inputs = "".join(f"[{i}:v][{i}:a]" for i in range(len(slice_parts)))
        fc_concat = f"{filter_inputs}concat=n={len(slice_parts)}:v=1:a=1[outv][outa]"
        cmd_concat = [
            FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
            *inputs,
            "-filter_complex", fc_concat,
            "-map", "[outv]", "-map", "[outa]",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "17",
            "-c:a", "aac", "-b:a", "192k",
            slice_mp4
        ]
        subprocess.run(cmd_concat, check=True)
        
        # 2. Generar subtítulos desde el slice empalmado con Whisper
        print(f"  [2/4] Generando subtítulos ASS Karaoke 58pt con Whisper en clip empalmado...")
        import whisper
        w_model = whisper.load_model("small")
        whisper_res = w_model.transcribe(
            slice_mp4,
            language="es",
            word_timestamps=True,
            initial_prompt="Hospital Garrahan, Johanna Tricarico, colectivo Soy Garrahan, necropolítica"
        )
        slice_words = []
        for seg in whisper_res.get("segments", []):
            for w in seg.get("words", []):
                slice_words.append({
                    "word": w["word"],
                    "start": round(float(w["start"]), 3),
                    "end": round(float(w["end"]), 3)
                })
        TextQualityAssurance._config = None
        clean_words = TextQualityAssurance.sanitize_words(slice_words)
        SubtitleEngine.generate_ass(clean_words, ass_path, font_size=58, y_pos=1450)
    else:
        st = r["start"]
        en = r["end"]
        print(f"  [1/4] Cortando slice de video ({st}s -> {en}s)...")
        cmd_cut = [
            FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
            "-ss", f"{st:.3f}", "-to", f"{en:.3f}",
            "-i", SRC_VIDEO,
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "17",
            "-c:a", "aac", "-b:a", "192k",
            slice_mp4
        ]
        subprocess.run(cmd_cut, check=True)
        
        # 2. Subtítulos relativos con TextQualityAssurance
        print(f"  [2/4] Generando subtítulos ASS Karaoke 58pt con TQA...")
        rel_words = get_relative_words(all_words, st, en)
        TextQualityAssurance._config = None
        clean_words = TextQualityAssurance.sanitize_words(rel_words)
        SubtitleEngine.generate_ass(clean_words, ass_path, font_size=58, y_pos=1450)
    
    # Obtener duración exacta de voz
    res_dur = subprocess.check_output([
        FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", slice_mp4
    ], text=True)
    speech_dur = float(res_dur.strip())
    outro_dur = 3.20
    total_dur = speech_dur + outro_dur
    
    # 3. Composición broadcast 9:16
    print(f"  [3/4] Composición Audiovisual FFmpeg (1080x1920 60fps, LUFS -14)...")
    badge_esc = BADGE_PNG.replace("\\", "/").replace(":", "\\:")
    outro_esc = OUTRO_PNG.replace("\\", "/").replace(":", "\\:")
    ass_esc = os.path.abspath(ass_path).replace("\\", "/").replace(":", "\\:")
    
    clean_live = live_txt.upper().replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U").replace("Ñ", "N").replace(":", "\\:")
    
    # Background blurred + Foreground centered (crop deputy head on left: crop=728:472:120:0)
    fg_filter = "crop=728:472:120:0,scale=1080:700:flags=lanczos,unsharp=5:5:0.8:3:3:0.4,setsar=1:1"
    bg_filter = "scale=270:480,boxblur=20:2,scale=1080:1920,setsar=1:1,eq=brightness=-0.14:contrast=1.1"
    
    filter_complex = (
        f"[0:v]{bg_filter}[bg]; "
        f"[0:v]{fg_filter}[fg]; "
        f"[bg][fg]overlay=0:310[v_comp]; "
        f"movie='{badge_esc}'[badge_raw]; "
        f"[v_comp][badge_raw]overlay=(W-w)/2:35:eof_action=repeat[v_brand]; "
        f"[v_brand]drawtext=text='{clean_live}':fontfile='C\\:/Windows/Fonts/arialbd.ttf':fontsize=26:"
        f"fontcolor=white:box=1:boxcolor=0xCC0000@0.92:boxborderw=8:x=(w-text_w)/2:y=230[v_live]; "
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
    
    t0_render = time.time()
    subprocess.run(cmd_render, check=True)
    print(f"  [✓] Render completado en {time.time() - t0_render:.1f}s -> {out_mp4}")
    
    # 4. Auditoría Post-Render Gate 4 & Pasaporte QA
    print("  [4/4] Ejecutando Post-Render QA Broadcast Audit...")
    passport = PostRenderAuditor.generate_qa_passport(out_mp4, metadata={
        "campaign": "Diputados Comisión de Salud",
        "speaker": "Johanna Tricarico",
        "title": r["title"],
        "hook": r["hook"]
    })
    print(f"        Resolución: {passport['specs']['resolution']} | LUFS: {passport['specs']['lufs']} | Estado: {passport['certification']['status']}")
    
    # Copiar a repositorio central local (en subcarpeta de campaña)
    central_file = os.path.join(campaign_repo, filename)
    central_qa = os.path.join(campaign_repo, os.path.splitext(filename)[0] + ".qa.json")
    shutil.copy2(out_mp4, central_file)
    shutil.copy2(os.path.splitext(out_mp4)[0] + ".qa.json", central_qa)
    print(f"        Copiado a subcarpeta de campaña: {central_file}")
    
    return out_mp4

def generate_copies_file(reels_to_include: List[Dict[str, Any]], out_path: str):
    lines = [
        "=============================================================================",
        "REELS STUDIO AI • CATÁLOGO OFICIAL Y COPIES PARA REDES",
        "Campaña: 06_Campaña_Octubre_Johanna_Diputados_ComisionSalud",
        "Vocera: Johanna Tricarico (Colectivo Soy Garrahan)",
        "Evento: Comisión de Salud - Honorable Cámara de Diputados de la Nación",
        f"Fecha: 14 de Octubre de 2026",
        "=============================================================================\n"
    ]
    
    for idx, r in enumerate(reels_to_include, start=1):
        lines.append(f"--- REEL {idx:02d}: {r['title']} ---")
        lines.append(f"Archivo: {r['filename']}")
        lines.append(f"Gancho en Pantalla: {r['hook']}")
        if "slices" in r:
            voice_dur = sum(sl["end"] - sl["start"] for sl in r["slices"])
        else:
            voice_dur = r["end"] - r["start"]
        total_dur = voice_dur + 3.2
        lines.append(f"Duración: {total_dur:.1f}s (Voz: {voice_dur:.1f}s + Cierre: 3.2s)")
        lines.append(f"Live Pill: {r['live']}")
        lines.append("\n[COPY SUGERIDO PARA INSTAGRAM / TIKTOK / FACEBOOK]:")
        lines.append(r["copy_lead"])
        lines.append(f"\n{r['hashtags']}\n")
        lines.append("-" * 77 + "\n")
        
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[OK] Archivo de copies generado en: {out_path}")

def sync_to_google_drive(rendered_reels: List[Dict[str, Any]], copies_file: str):
    if not os.path.exists(r"G:\.shortcut-targets-by-id"):
        print("[!] Google Drive G:\\ no está montado o no es accesible.")
        return False
        
    os.makedirs(DRIVE_CAMPAIGN, exist_ok=True)
    print(f"\n[*] Sincronizando a Google Drive: {DRIVE_CAMPAIGN}")
    
    for r in rendered_reels:
        src_mp4 = os.path.join(OUTPUT_LOCAL, r["filename"])
        src_qa = os.path.splitext(src_mp4)[0] + ".qa.json"
        
        dst_mp4 = os.path.join(DRIVE_CAMPAIGN, r["filename"])
        dst_qa = os.path.join(DRIVE_CAMPAIGN, os.path.basename(src_qa))
        
        if os.path.exists(src_mp4):
            shutil.copy2(src_mp4, dst_mp4)
            print(f"  [Drive] Copiado video: {r['filename']}")
        if os.path.exists(src_qa):
            shutil.copy2(src_qa, dst_qa)
            print(f"  [Drive] Copiado pasaporte QA: {os.path.basename(src_qa)}")
            
    # Copiar archivo de copies
    if os.path.exists(copies_file):
        dst_copies = os.path.join(DRIVE_CAMPAIGN, os.path.basename(copies_file))
        shutil.copy2(copies_file, dst_copies)
        print(f"  [Drive] Copiado catálogo de copies: {os.path.basename(copies_file)}")

    # Copiar archivo zip si existe
    zip_local = os.path.join(FINAL_REPO, "06_Campaña_Octubre_Johanna_Diputados_ComisionSalud", "REELS_Octubre_Johanna_Diputados_Completo.zip")
    if os.path.exists(zip_local):
        dst_zip = os.path.join(DRIVE_CAMPAIGN, os.path.basename(zip_local))
        shutil.copy2(zip_local, dst_zip)
        print(f"  [Drive] Copiado paquete ZIP: {os.path.basename(zip_local)}")
        
    print("[✓] Sincronización a Google Drive completada exitosamente.")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--priority-only", action="store_true", help="Renderizar solo los 2 reels de mayor valor")
    parser.add_argument("--all", action="store_true", help="Renderizar todos los 6 reels")
    parser.add_argument("--reel-id", type=str, default=None, help="Renderizar un reel específico por su ID o prefijo (ej: 03 o 03_Johanna...)")
    parser.add_argument("--force", action="store_true", help="Forzar re-renderizado aunque ya exista")
    parser.add_argument("--sync-drive", action="store_true", help="Sincronizar a Google Drive al finalizar")
    args = parser.parse_args()
    
    all_words = load_whisper_words()
    
    if args.reel_id:
        target_reels = [r for r in REELS_SPEC if args.reel_id.lower() == r["id"].lower()]
        if not target_reels:
            target_reels = [r for r in REELS_SPEC if args.reel_id.lower() in r["id"].lower()]
        if not target_reels:
            print(f"[!] No se encontró ningún reel con ID: {args.reel_id}")
            sys.exit(1)
    elif args.priority_only:
        target_reels = [r for r in REELS_SPEC if r["priority"] == 1]
    else:
        target_reels = REELS_SPEC
        
    rendered = []
    for r in target_reels:
        out = render_single_reel(r, all_words, force=args.force)
        rendered.append(r)
        
    # Generar copies actualizados de toda la campaña
    copies_local = os.path.join(COPIES_DIR, "CATALOGO_Y_COPIES_DIPUTADOS_COMISION_SALUD.txt")
    generate_copies_file(REELS_SPEC, copies_local)
    
    if args.sync_drive:
        sync_to_google_drive(target_reels, copies_local)
        
    print("\n=======================================================")
    print(f"PROCESO FINALIZADO: {len(rendered)} REELS RENDERIZADOS Y AUDITADOS")
    print("=======================================================")
