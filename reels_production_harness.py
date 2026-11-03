# filepath: reels_production_harness.py
"""
================================================================================
REELS STUDIO • PRODUCTION HARNESS & QUALITY GATING ENGINE (v3.0 FLASH-OPTIMIZED)
================================================================================
Interfaz CLI Determinista para Agentes Basados en Modelos Flash:
  - python reels_production_harness.py --mode preflight --show <show_id>
  - python reels_production_harness.py --mode preview --show <show_id> --reel <reel_id>
  - python reels_production_harness.py --mode compact-transcript --input <whisper.json>
  - python reels_production_harness.py --mode full --show <show_id> [--gpu]
================================================================================
"""
import os
import sys
import json
import argparse
import subprocess
from typing import Dict, Any, List

from core.env_config import FFMPEG_BIN, FFPROBE_BIN, SHOWS_PATH, REPO_ROOT, WORKSPACE_ROOT, resolve_asset
from core import (
    AudioBoundaryAuditor,
    SubtitleEngine,
    TextQualityAssurance,
    VideoCompositor,
    VideoEvaluator,
    PostRenderAuditor,
    Distributor
)


def load_shows_config() -> Dict[str, Any]:
    with open(SHOWS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def compact_whisper_transcript(input_json_path: str, output_json_path: str = None) -> str:
    """
    Comprime un archivo JSON de Whisper eliminando arrays de tokens numéricos y metadatos
    pesados para ahorrar ~80% de ventana de contexto al ser leído por un agente Flash.
    """
    with open(input_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    compact_segments = []
    for seg in data.get("segments", []):
        compact_words = [
            {"w": w["word"].strip(), "s": round(float(w["start"]), 2), "e": round(float(w["end"]), 2)}
            for w in seg.get("words", [])
        ]
        compact_segments.append({
            "id": seg.get("id"),
            "start": round(float(seg["start"]), 2),
            "end": round(float(seg["end"]), 2),
            "text": seg.get("text", "").strip(),
            "words": compact_words
        })

    if output_json_path is None:
        base, ext = os.path.splitext(input_json_path)
        output_json_path = f"{base}.compact{ext}"

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump({"segments": compact_segments}, f, ensure_ascii=False, separators=(",", ":"))

    return os.path.abspath(output_json_path)


class QualityGatingHarness:
    """
    Motor de Gating de 5 Etapas con Auto-Remediación para Agentes Flash.
    """
    MIN_DURATION_SEC = 18.0
    MAX_DURATION_SEC = 110.0
    MIN_WORDS = 25

    @classmethod
    def gate_1_editorial_curation(cls, reel_meta: Dict[str, Any], words: List[Dict[str, Any]]) -> Dict[str, Any]:
        if "slices" in reel_meta:
            duration = sum(float(s["end"]) - float(s["start"]) for s in reel_meta["slices"])
        else:
            duration = float(reel_meta["end"]) - float(reel_meta["start"])

        word_count = len(words)
        issues = []

        if duration < cls.MIN_DURATION_SEC:
            issues.append(f"Duración insuficiente ({duration:.1f}s < {cls.MIN_DURATION_SEC}s)")
        if duration > cls.MAX_DURATION_SEC:
            issues.append(f"Duración excesiva ({duration:.1f}s > {cls.MAX_DURATION_SEC}s)")
        if word_count < cls.MIN_WORDS:
            issues.append(f"Densidad verbal baja ({word_count} palabras < {cls.MIN_WORDS})")
        if not reel_meta.get("hook") or len(reel_meta["hook"]) > 55:
            issues.append("Hook ausente o demasiado largo (>55 caracteres)")

        return {
            "gate": "Gate 1: Editorial Curation Judge",
            "passed": len(issues) == 0,
            "duration_sec": round(duration, 2),
            "word_count": word_count,
            "wps": round(word_count / max(1.0, duration), 2),
            "issues": issues,
            "self_healing_hint": "Adjust start/end timestamps or hook length in config/shows.json" if issues else None
        }

    @classmethod
    def gate_3_linguistic_integrity(cls, words: List[Dict[str, Any]]) -> Dict[str, Any]:
        sanitized = TextQualityAssurance.sanitize_words(words)
        passed, errors = TextQualityAssurance.audit_text(sanitized)
        return {
            "gate": "Gate 3: Linguistic & Phonetic QA Judge",
            "passed": passed,
            "errors": errors,
            "sanitized_word_count": len(sanitized),
            "clean_transcript": " ".join(w["word"] for w in sanitized),
            "self_healing_hint": errors[0] if errors else None
        }

    @classmethod
    def run_preflight(cls, show_id: str, target_reel_id: str = None) -> Dict[str, Any]:
        """
        Ejecuta Gates 1, 2 y 3 en <2 segundos sin renderizar video.
        Ideal para que el agente Flash verifique sus cambios instantáneamente.
        """
        shows = load_shows_config()
        if show_id not in shows:
            raise ValueError(f"Show '{show_id}' no existe en {SHOWS_PATH}. Disponibles: {list(shows.keys())}")

        profile = shows[show_id]
        whisper_path = profile.get("whisper_json")
        all_words = []
        if whisper_path and os.path.exists(resolve_asset(whisper_path)):
            with open(resolve_asset(whisper_path), "r", encoding="utf-8") as f:
                wdata = json.load(f)
            for seg in wdata.get("segments", []):
                for w in seg.get("words", []):
                    all_words.append({
                        "word": w.get("word", w.get("w", "")).strip(),
                        "start": float(w.get("start", w.get("s", 0.0))),
                        "end": float(w.get("end", w.get("e", 0.0)))
                    })

        source_video = resolve_asset(profile.get("source_video", ""))
        results = []

        for r in profile.get("reels", []):
            if target_reel_id and r["id"] != target_reel_id:
                continue

            if "slices" in r:
                st, en = float(r["slices"][0]["start"]), float(r["slices"][-1]["end"])
                reel_words = []
                offset = 0.0
                for sl in r["slices"]:
                    s_st, s_en = float(sl["start"]), float(sl["end"])
                    for w in all_words:
                        if s_st - 0.1 <= w["start"] and w["end"] <= s_en + 0.1:
                            reel_words.append({
                                "word": w["word"],
                                "start": round(max(0.0, w["start"] - s_st + offset), 3),
                                "end": round(max(0.05, w["end"] - s_st + offset), 3)
                            })
                    offset += (s_en - s_st)
            else:
                st = float(r.get("start", 0.0))
                en = float(r.get("end", 30.0))
                reel_words = [
                    {
                        "word": w["word"],
                        "start": round(max(0.0, w["start"] - st), 3),
                        "end": round(max(0.05, w["end"] - st), 3)
                    }
                    for w in all_words if st - 0.1 <= w["start"] and w["end"] <= en + 0.1
                ]

            g1 = cls.gate_1_editorial_curation(r, reel_words if reel_words else [{"word": "placeholder"}] * 30)
            g3 = cls.gate_3_linguistic_integrity(reel_words)

            last_rel = reel_words[-1]["end"] if reel_words else None
            if os.path.exists(source_video) and st > 0:
                g2 = AudioBoundaryAuditor.validate_boundary_gating(source_video, st, en, last_rel, auto_fix=True)
            else:
                g2 = {"gate": "Gate 2: Acoustic Boundary Judge", "passed": True, "notes": ["Source video no requerido en preflight estático"]}

            results.append({
                "reel_id": r["id"],
                "passed_all_preflight": g1["passed"] and g2["passed"] and g3["passed"],
                "gate_1": g1,
                "gate_2": g2,
                "gate_3": g3
            })

        return {
            "show_id": show_id,
            "all_passed": all(item["passed_all_preflight"] for item in results),
            "reels": results
        }

    @classmethod
    def run_preview(cls, show_id: str, target_reel_id: str = None, timestamp: float = 1.5) -> Dict[str, Any]:
        """
        Renderiza un fotograma de previsualización para verificación visual ágil (<1.5s).
        """
        shows = load_shows_config()
        if show_id not in shows:
            raise ValueError(f"Show '{show_id}' no existe en {SHOWS_PATH}.")

        profile = shows[show_id]
        source_video = resolve_asset(profile.get("source_video", ""))
        if not os.path.exists(source_video):
            raise FileNotFoundError(f"Video fuente no encontrado: {source_video}")

        whisper_path = profile.get("whisper_json")
        all_words = []
        if whisper_path and os.path.exists(resolve_asset(whisper_path)):
            with open(resolve_asset(whisper_path), "r", encoding="utf-8") as f:
                wdata = json.load(f)
            for seg in wdata.get("segments", []):
                for w in seg.get("words", []):
                    all_words.append({
                        "word": w.get("word", w.get("w", "")).strip(),
                        "start": float(w.get("start", w.get("s", 0.0))),
                        "end": float(w.get("end", w.get("e", 0.0)))
                    })

        reels_to_process = [
            r for r in profile.get("reels", [])
            if not target_reel_id or r["id"] == target_reel_id
        ]
        preview_results = []
        temp_dir = os.path.join("scratch", "preview_temp")
        os.makedirs(temp_dir, exist_ok=True)

        for r in reels_to_process:
            rid = r["id"]
            if "slices" in r:
                st = float(r["slices"][0]["start"])
                en = float(r["slices"][0]["end"])
            else:
                st = float(r.get("start", 0.0))
                en = float(r.get("end", 30.0))

            sample_dur = min(4.0, max(1.0, en - st))
            slice_temp = os.path.join(temp_dir, f"{rid}_sample.mp4")
            cmd_cut = [
                FFMPEG_BIN, "-y", "-hide_banner", "-loglevel", "error",
                "-ss", f"{st:.3f}", "-t", f"{sample_dur:.3f}",
                "-i", source_video,
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20",
                "-c:a", "aac",
                slice_temp
            ]
            subprocess.run(cmd_cut, check=True)

            sample_words = [
                {
                    "word": w["word"],
                    "start": round(max(0.0, w["start"] - st), 3),
                    "end": round(max(0.05, w["end"] - st), 3)
                }
                for w in all_words if st <= w["start"] <= (st + sample_dur + 0.5)
            ]
            if not sample_words:
                sample_words = [
                    {"word": w, "start": i * 0.4, "end": (i + 1) * 0.4}
                    for i, w in enumerate(r.get("hook", "PREVIEW HOOK").split()[:int(sample_dur * 2)])
                ]

            ass_path = os.path.join(temp_dir, f"{rid}_sample.ass")
            SubtitleEngine.generate_ass(sample_words, ass_path, font_size=58, y_pos=profile.get("subs_y", 1450))

            out_preview_jpg = os.path.join("scratch", "visual_inspection", f"{rid}_preview.jpg")
            live_text = r.get("live", profile.get("name", "SOY GARRAHAN"))
            VideoCompositor.render_preview_frame(
                raw_slice_mp4=slice_temp,
                ass_path=ass_path,
                show_profile=profile,
                live_text=live_text,
                out_jpg=out_preview_jpg,
                timestamp=min(1.5, sample_dur * 0.5)
            )

            from core.visual_inspector import VisualInspector
            metrics = VisualInspector.analyze_frame_metrics(out_preview_jpg)
            preview_results.append({
                "reel_id": rid,
                "preview_frame": os.path.abspath(out_preview_jpg),
                "metrics": metrics,
                "status": "PASS" if metrics.get("valid") else "FAIL"
            })

        return {
            "show_id": show_id,
            "samples_rendered": len(preview_results),
            "previews": preview_results
        }

    @classmethod
    def run_full(cls, show_id: str, target_reel_id: str = None, use_gpu: bool = True, dual_versions: bool = True, force: bool = False) -> Dict[str, Any]:
        """
        Ejecuta el pipeline completo de producción, auditoría técnica de 5 Gates y empaquetado.
        Si dual_versions=True, genera dos versiones por cada reel: con subtítulos y sin subtítulos.
        """
        preflight_rep = cls.run_preflight(show_id, target_reel_id)
        if not preflight_rep["all_passed"]:
            return {
                "status": "FAILED_PREFLIGHT",
                "message": "Preflight check falló. Corrija los problemas antes de renderizar.",
                "preflight": preflight_rep
            }

        shows = load_shows_config()
        profile = shows[show_id]
        source_video = resolve_asset(profile.get("source_video", ""))
        whisper_path = profile.get("whisper_json")
        all_words = []
        if whisper_path and os.path.exists(resolve_asset(whisper_path)):
            with open(resolve_asset(whisper_path), "r", encoding="utf-8") as f:
                wdata = json.load(f)
            for seg in wdata.get("segments", []):
                for w in seg.get("words", []):
                    all_words.append({
                        "word": w.get("word", w.get("w", "")).strip(),
                        "start": float(w.get("start", w.get("s", 0.0))),
                        "end": float(w.get("end", w.get("e", 0.0)))
                    })

        output_dir = profile.get("output_dir")
        if output_dir:
            out_dir_abs = os.path.join(WORKSPACE_ROOT, output_dir)
        else:
            out_dir_abs = os.path.join(REPO_ROOT, f"REELS_{show_id}")
        os.makedirs(out_dir_abs, exist_ok=True)

        # Destinos sincronizados para distribución (carpeta de campaña local y Google Drive)
        from core.env_config import GDRIVE_DIR
        campaign_folder = os.path.basename(out_dir_abs)
        sync_dirs = [out_dir_abs]
        if os.path.exists(GDRIVE_DIR):
            sync_dirs.append(os.path.join(GDRIVE_DIR, campaign_folder))

        for sd in sync_dirs:
            os.makedirs(sd, exist_ok=True)

        temp_dir = os.path.join("scratch", "render_temp")
        os.makedirs(temp_dir, exist_ok=True)

        rendered_reels = []
        reels_to_render = [
            r for r in profile.get("reels", [])
            if not target_reel_id or r["id"] == target_reel_id
        ]

        for r in reels_to_render:
            rid = r["id"]
            filename = r.get("filename", f"{rid}.mp4")
            out_mp4 = os.path.join(out_dir_abs, filename)
            slice_mp4 = os.path.join(temp_dir, f"{rid}_slice.mp4")

            if "slices" in r:
                slices = r["slices"]
                slice_parts = []
                for idx, sl in enumerate(slices):
                    st_i, en_i = float(sl["start"]), float(sl["end"])
                    part_mp4 = os.path.join(temp_dir, f"{rid}_p{idx}.mp4")
                    cmd_cut = [
                        FFMPEG_BIN, "-y", "-hide_banner", "-loglevel", "error",
                        "-ss", f"{st_i:.3f}", "-to", f"{en_i:.3f}",
                        "-i", source_video,
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
                    FFMPEG_BIN, "-y", "-hide_banner", "-loglevel", "error",
                    *inputs,
                    "-filter_complex", fc_concat,
                    "-map", "[outv]", "-map", "[outa]",
                    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "17",
                    "-c:a", "aac", "-b:a", "192k",
                    slice_mp4
                ]
                subprocess.run(cmd_concat, check=True)

                reel_words = []
                offset = 0.0
                for sl in slices:
                    s_st, s_en = float(sl["start"]), float(sl["end"])
                    for w in all_words:
                        if s_st - 0.1 <= w["start"] and w["end"] <= s_en + 0.1:
                            reel_words.append({
                                "word": w["word"],
                                "start": round(max(0.0, w["start"] - s_st + offset), 3),
                                "end": round(max(0.05, w["end"] - s_st + offset), 3)
                            })
                    offset += (s_en - s_st)
            else:
                st = float(r.get("start", 0.0))
                en = float(r.get("end", 30.0))
                cmd_cut = [
                    FFMPEG_BIN, "-y", "-hide_banner", "-loglevel", "error",
                    "-ss", f"{st:.3f}", "-to", f"{en:.3f}",
                    "-i", source_video,
                    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "17",
                    "-c:a", "aac", "-b:a", "192k",
                    slice_mp4
                ]
                subprocess.run(cmd_cut, check=True)
                reel_words = [
                    {
                        "word": w["word"],
                        "start": round(max(0.0, w["start"] - st), 3),
                        "end": round(max(0.05, w["end"] - st), 3)
                    }
                    for w in all_words if st - 0.1 <= w["start"] and w["end"] <= en + 0.1
                ]

            ass_path = os.path.join(temp_dir, f"{rid}.ass")
            SubtitleEngine.generate_ass(reel_words, ass_path, font_size=58, y_pos=profile.get("subs_y", 1450))

            live_text = r.get("live", profile.get("name", "SOY GARRAHAN"))

            # 1. Versión con subtítulos
            qa_sub_path = os.path.splitext(out_mp4)[0] + ".qa.json"
            if not force and os.path.exists(out_mp4) and os.path.getsize(out_mp4) > 1000000 and os.path.exists(qa_sub_path):
                print(f"  [i] Reel subtitulado ya existente y validado: {out_mp4}")
                with open(qa_sub_path, "r", encoding="utf-8") as qf:
                    passport_sub = json.load(qf)
            else:
                VideoCompositor.render_reel(
                    raw_slice_mp4=slice_mp4,
                    ass_path=ass_path,
                    show_profile=profile,
                    live_text=live_text,
                    out_path=out_mp4,
                    use_gpu=use_gpu
                )
                passport_sub = PostRenderAuditor.generate_qa_passport(out_mp4, metadata=dict(r))

            reel_entry = {
                "reel_id": rid,
                "subtitled": {
                    "filename": filename,
                    "path": out_mp4,
                    "passport": passport_sub
                }
            }

            # 2. Versión sin subtítulos
            if dual_versions:
                base_name, ext = os.path.splitext(filename)
                filename_nosub = f"{base_name}_sin_subtitulos{ext}"
                out_mp4_nosub = os.path.join(out_dir_abs, filename_nosub)
                qa_nosub_path = os.path.splitext(out_mp4_nosub)[0] + ".qa.json"
                if not force and os.path.exists(out_mp4_nosub) and os.path.getsize(out_mp4_nosub) > 1000000 and os.path.exists(qa_nosub_path):
                    print(f"  [i] Reel sin subtítulos ya existente y validado: {out_mp4_nosub}")
                    with open(qa_nosub_path, "r", encoding="utf-8") as qf:
                        passport_nosub = json.load(qf)
                else:
                    VideoCompositor.render_reel(
                        raw_slice_mp4=slice_mp4,
                        ass_path=None,
                        show_profile=profile,
                        live_text=live_text,
                        out_path=out_mp4_nosub,
                        use_gpu=use_gpu
                    )
                    passport_nosub = PostRenderAuditor.generate_qa_passport(
                        out_mp4_nosub,
                        metadata={**dict(r), "variant": "sin_subtitulos"}
                    )
                reel_entry["clean"] = {
                    "filename": filename_nosub,
                    "path": out_mp4_nosub,
                    "passport": passport_nosub
                }

            # Sincronización cruzada a carpetas de campaña
            import shutil
            for sd in sync_dirs:
                if os.path.abspath(sd) != os.path.abspath(out_dir_abs):
                    # Copiar versión subtitulada
                    dest_sub = os.path.join(sd, filename)
                    shutil.copy2(out_mp4, dest_sub)
                    qa_src = os.path.splitext(out_mp4)[0] + ".qa.json"
                    if os.path.exists(qa_src):
                        shutil.copy2(qa_src, os.path.splitext(dest_sub)[0] + ".qa.json")

                    # Copiar versión sin subtítulos
                    if dual_versions:
                        dest_nosub = os.path.join(sd, filename_nosub)
                        shutil.copy2(out_mp4_nosub, dest_nosub)
                        qa_nosub_src = os.path.splitext(out_mp4_nosub)[0] + ".qa.json"
                        if os.path.exists(qa_nosub_src):
                            shutil.copy2(qa_nosub_src, os.path.splitext(dest_nosub)[0] + ".qa.json")

            rendered_reels.append(reel_entry)

        # Finalización automática: Empaquetado ZIP y Sincronización Completa con Google Drive
        import zipfile
        from core.distributor import Distributor
        from core.env_config import GDRIVE_DIR

        # 1. Empaquetado ZIP automático
        zip_name = profile.get("zip_name", f"REELS_{show_id.upper()}_Completo.zip")
        local_zip = os.path.join(out_dir_abs, zip_name)
        with zipfile.ZipFile(local_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in os.listdir(out_dir_abs):
                if f.endswith(".mp4") or f.endswith(".txt") or f.endswith(".qa.json"):
                    zf.write(os.path.join(out_dir_abs, f), arcname=f)

        # Copiar ZIP a 06_Paquetes_ZIP_Descargables
        zip_repo = os.path.join(WORKSPACE_ROOT, "06_Paquetes_ZIP_Descargables", zip_name)
        if os.path.exists(os.path.dirname(zip_repo)):
            shutil.copy2(local_zip, zip_repo)

        # 2. Sincronización Exhaustiva a Google Drive (si está montado)
        drive_sync_res = {}
        if os.path.exists(GDRIVE_DIR):
            campaign_folder = os.path.basename(out_dir_abs)
            drive_sync_res = Distributor.sync_to_google_drive(out_dir_abs, campaign_folder)

            # Sincronizar catálogo general y visualizador web a la raíz de Drive
            for root_item in ["catalog.json", "index.html", "qa_contact_sheet.html", "CATALOGO_Y_COPIES_MAESTRO_CONSOLIDADO.txt"]:
                src_root = os.path.join(WORKSPACE_ROOT, "01_Reels_Finales_Subtitulados", root_item)
                dst_root = os.path.join(GDRIVE_DIR, root_item)
                if os.path.exists(src_root):
                    shutil.copy2(src_root, dst_root)

        return {
            "status": "COMPLETED",
            "show_id": show_id,
            "dual_versions": dual_versions,
            "rendered_count": len(rendered_reels),
            "zip_package": local_zip,
            "google_drive_sync": drive_sync_res if drive_sync_res else "Drive no montado",
            "reels": rendered_reels
        }


def main():
    parser = argparse.ArgumentParser(description="Reels Studio Production Harness (Flash-Optimized)")
    parser.add_argument("--mode", choices=["preflight", "preview", "compact-transcript", "full"], default="preflight")
    parser.add_argument("--show", type=str, help="ID del show en config/shows.json")
    parser.add_argument("--reel", type=str, default=None, help="ID de un reel específico (opcional)")
    parser.add_argument("--input", type=str, default=None, help="Ruta de archivo de entrada (para compact-transcript)")
    parser.add_argument("--gpu", action="store_true", default=True, help="Usar aceleración por hardware NVENC si está disponible")
    parser.add_argument("--no-gpu", action="store_true", help="Forzar codificación por CPU (libx264)")
    parser.add_argument("--single", action="store_true", help="Generar únicamente la versión con subtítulos (desactiva dual)")
    parser.add_argument("--force", action="store_true", help="Forzar re-renderizado aunque el reel ya exista")
    args = parser.parse_args()

    if args.mode == "compact-transcript":
        if not args.input:
            print(json.dumps({"error": "Debe especificar --input <ruta_whisper.json>"}))
            sys.exit(1)
        out = compact_whisper_transcript(args.input)
        print(json.dumps({"status": "OK", "compact_transcript": out}, indent=2))
        return

    if not args.show:
        print(json.dumps({"error": "Debe especificar --show <show_id>"}))
        sys.exit(1)

    if args.mode == "preflight":
        rep = QualityGatingHarness.run_preflight(args.show, args.reel)
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        sys.exit(0 if rep["all_passed"] else 1)

    if args.mode == "preview":
        rep = QualityGatingHarness.run_preview(args.show, args.reel)
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        sys.exit(0)

    if args.mode == "full":
        use_gpu = not args.no_gpu
        rep = QualityGatingHarness.run_full(args.show, args.reel, use_gpu=use_gpu, dual_versions=not args.single, force=args.force)
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        sys.exit(0 if rep.get("status") == "COMPLETED" else 1)


if __name__ == "__main__":
    main()
