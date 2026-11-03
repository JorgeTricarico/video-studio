# filepath: core/visual_inspector.py
import os
import sys
import json
import subprocess
from typing import Dict, Any, List
from PIL import Image, ImageStat, ImageFilter
from .env_config import FFMPEG_BIN, FFPROBE_BIN


class VisualInspector:
    """
    Auditor de Inspección Visual Previa a la Entrega (Gate 5 Visual QA).
    Extrae fotogramas clave, genera la Hoja de Contacto 3x2 y calcula métricas objetivas
    de luminancia, contraste y nitidez para validación automática por agentes Flash.
    """

    @staticmethod
    def get_video_duration(video_path: str) -> float:
        try:
            cmd = [
                FFPROBE_BIN, "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", video_path
            ]
            out = subprocess.check_output(cmd, text=True).strip()
            return float(out)
        except Exception:
            return 60.0

    @staticmethod
    def analyze_frame_metrics(frame_path: str) -> Dict[str, Any]:
        """Calcula brillo medio, contraste (desviación estándar) y nitidez de bordes."""
        if not frame_path or not os.path.exists(frame_path):
            return {"valid": False, "reason": "Archivo inexistente"}
        try:
            with Image.open(frame_path) as img:
                gray = img.convert("L")
                stat = ImageStat.Stat(gray)
                mean_luma = round(stat.mean[0], 2)
                std_contrast = round(stat.stddev[0], 2)
                edges = gray.filter(ImageFilter.FIND_EDGES)
                edge_stat = ImageStat.Stat(edges)
                sharpness = round(edge_stat.mean[0], 2)

                is_black = mean_luma < 12.0 or std_contrast < 8.0
                return {
                    "valid": not is_black,
                    "width": img.width,
                    "height": img.height,
                    "mean_luma": mean_luma,
                    "contrast_std": std_contrast,
                    "edge_sharpness": sharpness,
                    "is_black_or_flat": is_black
                }
        except Exception as e:
            return {"valid": False, "reason": str(e)}

    @classmethod
    def inspect_video(cls, video_path: str, output_dir: str = None) -> Dict[str, Any]:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video no encontrado: {video_path}")

        base_name = os.path.splitext(os.path.basename(video_path))[0]
        if output_dir is None:
            output_dir = os.path.join("scratch", "visual_inspection", base_name)
        os.makedirs(output_dir, exist_ok=True)

        duration = cls.get_video_duration(video_path)

        sample_points = [
            ("01_intro_0.0s", 0.0, "Apertura Inicial (Frame 0)"),
            ("02_intro_0.5s", min(0.5, duration * 0.05), "Entrada Hook (0.5s)"),
            ("03_hook_1.5s", min(1.5, duration * 0.1), "Gancho & Subtítulos (1.5s)"),
            ("04_early_3.0s", min(3.0, duration * 0.15), "Primeros 3 Segundos"),
            ("05_mid_speech", duration * 0.50, f"Discurso Medio ({duration*0.5:.1f}s)"),
            ("06_outro_card", max(0.5, duration - 1.5), f"Tarjeta Final ({duration-1.5:.1f}s)")
        ]

        extracted_frames = []
        for tag, ts, label in sample_points:
            out_jpg = os.path.join(output_dir, f"{tag}.jpg")
            cmd = [
                FFMPEG_BIN, "-y", "-ss", f"{ts:.2f}", "-i", video_path,
                "-vframes", "1", "-q:v", "2", out_jpg
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(out_jpg):
                metrics = cls.analyze_frame_metrics(out_jpg)
                extracted_frames.append({
                    "tag": tag,
                    "timestamp": round(ts, 2),
                    "label": label,
                    "path": os.path.abspath(out_jpg),
                    "metrics": metrics
                })

        contact_sheet_path = os.path.join(output_dir, "contact_sheet.jpg")
        cls._create_contact_sheet(extracted_frames, contact_sheet_path)

        opening_audit = cls._audit_opening(extracted_frames[0] if extracted_frames else None)

        report = {
            "video_path": os.path.abspath(video_path),
            "video_name": os.path.basename(video_path),
            "duration": round(duration, 2),
            "samples_count": len(extracted_frames),
            "samples": extracted_frames,
            "contact_sheet": os.path.abspath(contact_sheet_path) if os.path.exists(contact_sheet_path) else None,
            "opening_audit": opening_audit,
            "requires_agent_review": opening_audit.get("status") != "PASS"
        }

        report_json_path = os.path.join(output_dir, "visual_audit.json")
        with open(report_json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return report

    @classmethod
    def _create_contact_sheet(cls, frames: List[Dict[str, Any]], output_path: str):
        if len(frames) < 6:
            return
        try:
            grid = Image.new("RGB", (360 * 3, 640 * 2))
            for idx, f in enumerate(frames[:6]):
                with Image.open(f["path"]) as im:
                    thumb = im.convert("RGB").resize((360, 640), Image.Resampling.LANCZOS)
                    col = idx % 3
                    row = idx // 3
                    grid.paste(thumb, (col * 360, row * 640))
            grid.save(output_path, "JPEG", quality=90)
        except Exception:
            pass

    @classmethod
    def _audit_opening(cls, first_sample: Dict[str, Any]) -> Dict[str, Any]:
        if not first_sample or not first_sample.get("metrics", {}).get("valid"):
            return {
                "status": "FAIL",
                "reason": "Frame 0 inválido, pantalla negra o plano sin contraste",
                "metrics": first_sample.get("metrics") if first_sample else {}
            }
        return {
            "status": "PASS",
            "frame_0": first_sample["path"],
            "metrics": first_sample["metrics"],
            "checklist": [
                "1. Rostro del vocero encuadrado y visible.",
                "2. Sin capturas de navegador o artefactos externos.",
                "3. Badge Soy Garrahan y píldora en vivo correctamente ubicados.",
                "4. Subtítulos dentro de la zona segura."
            ]
        }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        rep = VisualInspector.inspect_video(sys.argv[1])
        print(f"[OK] Inspección visual completada. Hoja de contacto: {rep['contact_sheet']}")
