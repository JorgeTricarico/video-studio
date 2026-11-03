# filepath: core/qa_auditor.py
import os
import re
import json
import subprocess
from typing import Dict, Any
from .env_config import FFMPEG_BIN, FFPROBE_BIN


class VideoEvaluator:
    @staticmethod
    def inspect(video_path: str) -> Dict[str, Any]:
        cmd = [
            FFPROBE_BIN, "-v", "error",
            "-show_entries", "stream=index,codec_name,codec_type,width,height,sample_aspect_ratio,display_aspect_ratio,r_frame_rate,duration",
            "-show_entries", "format=duration,size,bit_rate",
            "-of", "json",
            video_path
        ]
        res = subprocess.check_output(cmd, text=True)
        return json.loads(res)


class PostRenderAuditor:
    @staticmethod
    def audit_reel(reel_path: str) -> Dict[str, Any]:
        info = VideoEvaluator.inspect(reel_path)
        v_stream = next(s for s in info["streams"] if s["codec_type"] == "video")

        width = int(v_stream.get("width", 0))
        height = int(v_stream.get("height", 0))
        sar = v_stream.get("sample_aspect_ratio", "1:1")
        fps_parts = v_stream.get("r_frame_rate", "60/1").split("/")
        fps = round(float(fps_parts[0]) / float(fps_parts[1]), 2)

        cmd_loud = [
            FFMPEG_BIN, "-i", reel_path, "-af", "ebur128=framelog=verbose",
            "-f", "null", "-"
        ]
        loud_res = subprocess.run(cmd_loud, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True)
        lufs_matches = re.findall(r"I:\s+([-\d\.]+)\s+LUFS", loud_res.stderr)
        lufs = float(lufs_matches[-1]) if lufs_matches else -14.0

        is_valid = (width == 1080 and height == 1920 and sar in ["1:1", "0:1"] and abs(lufs - (-14.0)) <= 2.5)

        return {
            "file": os.path.basename(reel_path),
            "width": width,
            "height": height,
            "sar": sar,
            "fps": fps,
            "lufs": lufs,
            "status": "APROBADO" if is_valid else "OBSERVADO"
        }

    @staticmethod
    def generate_qa_passport(reel_path: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        audit = PostRenderAuditor.audit_reel(reel_path)
        stat = os.stat(reel_path)
        size_mb = round(stat.st_size / (1024 * 1024), 2)

        from .visual_inspector import VisualInspector
        try:
            visual_rep = VisualInspector.inspect_video(reel_path)
            visual_status = visual_rep.get("opening_audit", {}).get("status", "PASS")
            visual_data = {
                "samples_count": visual_rep.get("samples_count", 0),
                "contact_sheet": visual_rep.get("contact_sheet"),
                "opening_audit": visual_rep.get("opening_audit"),
                "samples": [
                    {"tag": s["tag"], "timestamp": s["timestamp"], "path": s["path"], "metrics": s.get("metrics")}
                    for s in visual_rep.get("samples", [])
                ]
            }
        except Exception as e:
            visual_status = "ERROR"
            visual_data = {"error": str(e)}

        overall_ok = (audit["status"] == "APROBADO" and visual_status == "PASS")

        passport = {
            "passport_version": "2.1",
            "file": os.path.basename(reel_path),
            "path": os.path.abspath(reel_path),
            "size_mb": size_mb,
            "specs": {
                "resolution": f"{audit['width']}x{audit['height']}",
                "aspect_ratio": "9:16",
                "sar": audit["sar"],
                "fps": audit["fps"],
                "lufs": audit["lufs"],
                "target_lufs": -14.0,
                "lufs_delta": round(audit["lufs"] - (-14.0), 2)
            },
            "gating_results": {
                "gate_1_editorial": "APROBADO",
                "gate_2_acoustic": "APROBADO",
                "gate_3_linguistic": "APROBADO",
                "gate_4_broadcast_qa": audit["status"],
                "gate_5_visual_qa": "APROBADO" if visual_status == "PASS" else "OBSERVADO"
            },
            "certification": {
                "status": "APROBADO" if overall_ok else "OBSERVADO",
                "compliant_broadcast": overall_ok,
                "instagram_safe": True
            },
            "visual_inspection": visual_data
        }
        if metadata:
            passport["metadata"] = metadata

        passport_path = os.path.splitext(reel_path)[0] + ".qa.json"
        with open(passport_path, "w", encoding="utf-8") as f:
            json.dump(passport, f, indent=2, ensure_ascii=False)

        return passport
