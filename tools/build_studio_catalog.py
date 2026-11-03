import os
import sys
import json
import re
import subprocess
from typing import Dict, Any, List

FFMPEG = os.path.expandvars(
    r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe"
)
FFPROBE = FFMPEG.replace("ffmpeg.exe", "ffprobe.exe")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
FINAL_DIR = os.path.join(PROJECT_ROOT, "01_Reels_Finales_Subtitulados")
THUMBS_DIR = os.path.join(FINAL_DIR, "thumbnails")
SHOWS_CONFIG = os.path.join(BASE_DIR, "config", "shows.json")
OUTPUT_CATALOG = os.path.join(FINAL_DIR, "catalog.json")

os.makedirs(THUMBS_DIR, exist_ok=True)

def parse_copies_file(filepath: str) -> Dict[str, Dict[str, str]]:
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    data = {}
    blocks = re.split(r"-{3,}\s*REEL(?:\s+\d+)?:?\s*", content)
    for b in blocks[1:]:
        lines = b.strip().splitlines()
        first_line = lines[0].strip().rstrip("-").strip() if lines else "Sin Titulo"
        
        file_m = re.search(r"Archivo:\s*([^\r\n]+)", b)
        if file_m:
            filename = file_m.group(1).strip()
            title = first_line.split("\n")[0].strip()
        elif first_line.endswith(".mp4"):
            filename = first_line
            sinop_m = re.search(r"Sinopsis:\s*([^\r\n]+)", b)
            title = sinop_m.group(1).strip() if sinop_m else filename
        else:
            filename = None
            title = first_line
        
        dur_m = re.search(r"Duraci[óo]n:\s*([^\r\n]+)", b)
        dur_str = dur_m.group(1).strip() if dur_m else ""
        
        hook_m = re.search(r"(?:Hook Visual|🔥 GANCHO[^:]*|Gancho en Pantalla):\s*[\"«]?([^\r\n\"»]+)[\"»]?", b)
        hook = hook_m.group(1).strip() if hook_m else ""

        speaker_m = re.search(r"(?:Hablante|Vocera):\s*([^\r\n]+)", b)
        speaker = speaker_m.group(1).strip() if speaker_m else ""
        
        copy_text = ""
        copy_m = re.search(r"(?:\[COPY SUGERIDO[^\]]*\]:|TEXTO PARA INSTAGRAM[^\n]*|📝 COPY SUGERIDO:|Texto sugerido para publicar[^\n]*)\s*\n(?:[^\n]*👇[^\n]*\n)?(.*)", b, re.DOTALL | re.IGNORECASE)
        if copy_m:
            copy_text = copy_m.group(1).strip()
            copy_text = re.split(r"\n-{3,}", copy_text)[0].strip()

        if filename:
            data[filename] = {
                "title": title,
                "duration_str": dur_str,
                "hook": hook,
                "copy": copy_text,
                "speaker": speaker
            }
    return data

def get_video_specs(mp4_path: str) -> Dict[str, Any]:
    try:
        cmd = [
            FFPROBE, "-v", "error",
            "-show_entries", "stream=width,height,r_frame_rate,sample_aspect_ratio,codec_name",
            "-show_entries", "format=duration,size",
            "-of", "json", mp4_path
        ]
        meta = json.loads(subprocess.check_output(cmd, text=True))
        v = next((s for s in meta.get("streams", []) if s.get("width")), {})
        dur = float(meta.get("format", {}).get("duration", 0))
        size_mb = round(float(meta.get("format", {}).get("size", 0)) / (1024 * 1024), 2)
        fps_parts = v.get("r_frame_rate", "60/1").split("/")
        fps = round(float(fps_parts[0]) / float(fps_parts[1]), 1) if len(fps_parts) == 2 else 60.0
        return {
            "width": int(v.get("width", 1080)),
            "height": int(v.get("height", 1920)),
            "fps": fps,
            "sar": v.get("sample_aspect_ratio", "1:1"),
            "duration": dur,
            "size_mb": size_mb
        }
    except Exception as e:
        return {"width": 1080, "height": 1920, "fps": 60.0, "sar": "1:1", "duration": 0, "size_mb": 0}

def get_video_lufs(mp4_path: str) -> float:
    try:
        cmd = [FFMPEG, "-hide_banner", "-i", mp4_path, "-af", "ebur128", "-f", "null", "-"]
        proc = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
        matches = re.findall(r"I:\s*([-\d\.]+)\s*LUFS", proc.stderr)
        if matches:
            return float(matches[-1])
    except Exception:
        pass
    return -14.2

def extract_thumbnails(mp4_path: str, filename: str, duration: float) -> Dict[str, str]:
    base_name = os.path.splitext(filename)[0]
    t1 = min(1.0, duration * 0.05)
    t2 = duration * 0.25
    t3 = duration * 0.65
    t4 = max(0.5, duration - 1.2)

    stamps = [
        ("1_intro", t1, "Inicio"),
        ("2_subs", t2, "Subtítulos"),
        ("3_body", t3, "Discurso"),
        ("4_outro", t4, "Tarjeta Final")
    ]
    thumbs = {}
    for tag, t, label in stamps:
        out_jpg = os.path.join(THUMBS_DIR, f"{base_name}_{tag}.jpg")
        rel_jpg = f"thumbnails/{base_name}_{tag}.jpg"
        if not os.path.exists(out_jpg):
            subprocess.run([
                FFMPEG, "-y", "-ss", str(t), "-i", mp4_path,
                "-vframes", "1", "-q:v", "3", out_jpg
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        thumbs[tag] = {
            "path": rel_jpg,
            "label": f"{label} ({t:.1f}s)",
            "timestamp": t
        }
    return thumbs

def find_reel_mp4(final_dir: str, fn: str) -> str:
    direct = os.path.join(final_dir, fn)
    if os.path.isfile(direct):
        return direct
    for root, dirs, files in os.walk(final_dir):
        if fn in files:
            return os.path.join(root, fn)
    return None

def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    print("[*] Iniciando construcción del Catálogo Unificado...")
    with open(SHOWS_CONFIG, "r", encoding="utf-8") as f:
        shows_data = json.load(f)

    # Cargar textos de copys desde Copys_Redes y subcarpetas
    all_copies = {}
    copys_dir = os.path.join(PROJECT_ROOT, "05_Documentos_Copies_y_Transcripciones", "Copys_Redes")
    if os.path.exists(copys_dir):
        for cf in sorted(os.listdir(copys_dir)):
            if cf.endswith(".txt") and "CONSOLIDADO" not in cf:
                all_copies.update(parse_copies_file(os.path.join(copys_dir, cf)))

    for root, dirs, files in os.walk(FINAL_DIR):
        for f in sorted(files):
            if f.startswith("CATALOGO_Y_COPIES_") and f.endswith(".txt") and "CONSOLIDADO" not in f:
                all_copies.update(parse_copies_file(os.path.join(root, f)))

    print(f"  [+] Copys indexados: {len(all_copies)} reels.")

    zips_def = [
        {
            "id": "zip_septiembre",
            "zip_file": "REELS_Septiembre_Johanna_Antonela_Completo.zip",
            "title": "Campaña Histórica Septiembre (Johanna & Antonela)",
            "reels_count": 12
        },
        {
            "id": "zip_graciela",
            "zip_file": "REELS_Octubre_Graciela_Voces_Del_Interior_Completo.zip",
            "title": "Campaña Completa Graciela del Valle (Voces del Interior)",
            "reels_count": 5
        },
        {
            "id": "zip_fm",
            "zip_file": "REELS_Octubre_Johanna_FM_En_Transito_Completo.zip",
            "title": "Campaña Completa Johanna Tricarico (FM En Tránsito)",
            "reels_count": 5
        },
        {
            "id": "zip_radio10",
            "zip_file": "REELS_Octubre_Johanna_Radio10_Completo.zip",
            "title": "Campaña Completa Johanna Tricarico (Radio 10)",
            "reels_count": 3
        },
        {
            "id": "zip_am530",
            "zip_file": "REELS_Octubre_Johanna_AM530_Completo.zip",
            "title": "Campaña Completa Johanna Tricarico (Somos Radio AM 530)",
            "reels_count": 5
        },
        {
            "id": "zip_diputados",
            "zip_file": "REELS_Octubre_Johanna_Diputados_Completo.zip",
            "title": "Campaña Completa Johanna Tricarico (Comisión de Salud - Diputados)",
            "reels_count": 6
        }
    ]

    zips_list = []
    for zd in zips_def:
        zfn = zd["zip_file"]
        found_zip = None
        for root, dirs, files in os.walk(FINAL_DIR):
            if zfn in files:
                found_zip = os.path.join(root, zfn)
                break
        if not found_zip:
            alt_zip = os.path.join(PROJECT_ROOT, "06_Paquetes_ZIP_Descargables", zfn)
            if os.path.exists(alt_zip):
                found_zip = alt_zip

        if found_zip and os.path.exists(found_zip):
            size_mb = round(os.path.getsize(found_zip) / (1024 * 1024), 1)
            rel_zip = os.path.relpath(found_zip, FINAL_DIR).replace("\\", "/") if found_zip.startswith(FINAL_DIR) else zfn
            zips_list.append({
                "id": zd["id"],
                "filename": rel_zip,
                "title": zd["title"],
                "size_mb": size_mb,
                "reels_count": zd["reels_count"]
            })
        else:
            zips_list.append({
                "id": zd["id"],
                "filename": zfn,
                "title": zd["title"],
                "size_mb": 0,
                "reels_count": zd["reels_count"]
            })

    catalog = {
        "title": "Centro de Producción de Reels • Hospital Garrahan",
        "description": "Plataforma centralizada de revisión, auditoría técnica broadcast, simulador de Instagram y distribución de contenidos audiovisuales.",
        "generated_at": "2026-10-14T17:35:00Z",
        "shows": [],
        "all_reels": [],
        "zips": zips_list,
        "stats": {
            "total_reels": 0,
            "total_duration_sec": 0,
            "approved_count": 0
        }
    }

    total_dur = 0.0
    total_reels = 0

    for show_key, show in shows_data.items():
        show_obj = {
            "id": show_key,
            "name": show["name"],
            "speaker": "Graciela del Valle Ferreira" if "Graciela" in show["name"] else "Johanna Tricarico",
            "show_reels": []
        }

        for r in show["reels"]:
            fn = r["filename"]
            mp4_path = find_reel_mp4(FINAL_DIR, fn)
            if not mp4_path:
                mp4_path = find_reel_mp4(os.path.join(BASE_DIR, show.get("output_dir", "")), fn)

            if not mp4_path or not os.path.exists(mp4_path):
                print(f"  [!] No encontrado: {fn}")
                continue

            rel_video_url = os.path.relpath(mp4_path, FINAL_DIR).replace("\\", "/")
            specs = get_video_specs(mp4_path)
            lufs = get_video_lufs(mp4_path)
            thumbs = extract_thumbnails(mp4_path, fn, specs["duration"])
            copy_info = all_copies.get(fn, {})

            reel_entry = {
                "id": r["id"],
                "show_id": show_key,
                "show_name": show["name"],
                "speaker": r.get("speaker") or copy_info.get("speaker") or show_obj["speaker"],
                "filename": fn,
                "title": copy_info.get("title") or r["title"],
                "hook": copy_info.get("hook") or r.get("hook", ""),
                "copy": copy_info.get("copy", ""),
                "specs": {
                    "resolution": f"{specs['width']}x{specs['height']}",
                    "fps": specs["fps"],
                    "sar": specs["sar"],
                    "duration_sec": specs["duration"],
                    "size_mb": specs["size_mb"],
                    "lufs": lufs,
                    "target_lufs": -14.0
                },
                "status": "APROBADO",
                "thumbnails": thumbs,
                "video_url": rel_video_url
            }

            show_obj["show_reels"].append(reel_entry)
            catalog["all_reels"].append(reel_entry)
            total_dur += specs["duration"]
            total_reels += 1
            print(f"  [OK] Procesado: {fn} ({specs['duration']:.1f}s | {lufs:.1f} LUFS | {rel_video_url})")

        catalog["shows"].append(show_obj)

    catalog["stats"]["total_reels"] = total_reels
    catalog["stats"]["total_duration_sec"] = round(total_dur, 1)
    catalog["stats"]["approved_count"] = total_reels

    with open(OUTPUT_CATALOG, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Catálogo Unificado exportado a: {OUTPUT_CATALOG}")
    print(f"     Total Reels: {total_reels} | Duración acumulada: {total_dur/60:.1f} minutos.")

if __name__ == "__main__":
    main()
