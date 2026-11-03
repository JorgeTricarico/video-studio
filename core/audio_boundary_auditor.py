# filepath: core/audio_boundary_auditor.py
import re
import math
import struct
import subprocess
from typing import List, Dict, Any, Tuple
from .env_config import FFMPEG_BIN


class AudioBoundaryAuditor:
    """
    Auditor y Auto-Calibrador Acústico de Límites de Audio (Gate 2):
    - Poda fragmentos iniciales huérfanos.
    - Mide energía en cabeza y cola del corte.
    - Auto-calibra timestamps buscando valles de silencio en ventanas de 50ms.
    """
    ORPHAN_START_FRAGMENTS = {
        "elamiento", "amiento", "miento", "ción", "sión", "mente", "endo", "ando", "aron", "eron"
    }
    VALID_SHORT_WORDS = {"y", "o", "a", "e", "u", "el", "la", "de", "en", "un", "no", "sí", "si", "ya", "yo", "mi", "tu", "su", "es", "al", "lo", "se", "me", "te", "le", "ni"}

    @classmethod
    def audit_and_trim_start(cls, words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        while words:
            first_w = words[0]["word"].strip().lower()
            clean_first = re.sub(r"[^\wáéíóúÁÉÍÓÚñÑüÜ]", "", first_w)
            dur = float(words[0]["end"]) - float(words[0]["start"])
            if clean_first in cls.ORPHAN_START_FRAGMENTS or (
                len(clean_first) <= 2 and dur < 0.12 and clean_first not in cls.VALID_SHORT_WORDS
            ):
                print(f"  [AUDIO BOUNDARY AUDITOR] Descartando residuo truncado al inicio: '{words[0]['word']}' ({words[0]['start']}s - {words[0]['end']}s)")
                words = words[1:]
            else:
                break
        return words

    @staticmethod
    def _measure_max_volume_db(wav_path: str, start_s: float, end_s: float) -> float:
        if end_s <= start_s:
            return -99.0
        cmd = [
            FFMPEG_BIN, "-hide_banner", "-ss", f"{max(0.0, start_s):.3f}", "-to", f"{end_s:.3f}",
            "-i", wav_path, "-af", "volumedetect", "-f", "null", "-"
        ]
        res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True)
        match = re.search(r"max_volume:\s*([-\d\.]+)\s*dB", res.stderr)
        return float(match.group(1)) if match else -99.0

    @classmethod
    def auto_calibrate_boundaries(
        cls,
        wav_path: str,
        start_sec: float,
        end_sec: float,
        first_word_start_abs: float = None,
        last_word_end_abs: float = None,
        search_radius: float = 0.80
    ) -> Tuple[float, float, List[str]]:
        """
        Escanea el audio crudo PCM a 16kHz alrededor del inicio y fin para encontrar el valle
        de menor energía acústica (<= -18 dB) sin mutilar la primera ni la última palabra.
        """
        logs = []
        best_start = start_sec
        best_end = end_sec

        # 1. Calibrar inicio (buscar ventana de 200ms más silenciosa antes de la primera palabra)
        anchor_start = first_word_start_abs if first_word_start_abs is not None else start_sec
        scan_st_0 = max(0.0, anchor_start - search_radius)
        scan_st_1 = anchor_start + 0.05
        best_head_db = 0.0
        cur = scan_st_0
        while cur + 0.20 <= scan_st_1:
            db = cls._measure_max_volume_db(wav_path, cur, cur + 0.20)
            if db < best_head_db:
                best_head_db = db
                best_start = round(cur + 0.20, 2)
            cur += 0.05
        logs.append(f"[AUTO-CALIBRATE HEAD] {start_sec:.2f}s -> {best_start:.2f}s (min pre-window: {best_head_db:.1f} dB)")

        # 2. Calibrar final (al menos 0.22s después de la última palabra, buscando ventana de 150ms <= -15 dB)
        anchor_end = max(end_sec, (last_word_end_abs + 0.22) if last_word_end_abs else end_sec)
        scan_en_0 = anchor_end
        scan_en_1 = anchor_end + search_radius
        best_tail_db = 0.0
        cur = scan_en_0
        while cur <= scan_en_1:
            db = cls._measure_max_volume_db(wav_path, cur - 0.15, cur)
            if db < best_tail_db:
                best_tail_db = db
                best_end = round(cur, 2)
                if db <= -22.0:
                    break
            cur += 0.05
        logs.append(f"[AUTO-CALIBRATE TAIL] {end_sec:.2f}s -> {best_end:.2f}s (min tail-window: {best_tail_db:.1f} dB)")

        return best_start, best_end, logs

    @classmethod
    def validate_boundary_gating(
        cls,
        wav_path: str,
        start_sec: float,
        end_sec: float,
        last_word_end_rel: float = None,
        auto_fix: bool = True
    ) -> Dict[str, Any]:
        """
        Gate 2: Valida acústicamente el inicio (Head Trim) y final (Tail Trim).
        Si falla y `auto_fix=True`, calcula y devuelve `suggested_start` y `suggested_end`.
        """
        passed = True
        notes = []

        # 1. Chequeo de inicio (Head Boundary)
        max_vol_head = cls._measure_max_volume_db(wav_path, max(0.0, start_sec - 0.25), start_sec)
        if max_vol_head > -18.0:
            passed = False
            notes.append(f"[HEAD] Posible residuo acústico previo ({max_vol_head:.1f} dB > -18 dB)")
        else:
            notes.append(f"[HEAD] Silencio previo limpio ({max_vol_head:.1f} dB)")

        # 2. Chequeo de final (Tail Boundary)
        duration = end_sec - start_sec
        if last_word_end_rel is not None:
            tail_margin = duration - last_word_end_rel
            if tail_margin < 0.20:
                passed = False
                notes.append(
                    f"[TAIL VETO] Corte abrupto: última palabra termina a {last_word_end_rel:.2f}s "
                    f"pero el clip corta a {duration:.2f}s (margen {tail_margin:.2f}s < 0.20s)"
                )
            else:
                notes.append(f"[TAIL] Margen posterior adecuado ({tail_margin:.2f}s >= 0.20s)")

        tail_vol = cls._measure_max_volume_db(wav_path, end_sec - 0.15, end_sec)
        if tail_vol > -15.0:
            passed = False
            notes.append(f"[TAIL VETO] Señal cortada con volumen alto al final ({tail_vol:.1f} dB > -15 dB)")
        else:
            notes.append(f"[TAIL] Decaimiento sonoro final limpio ({tail_vol:.1f} dB)")

        result = {
            "gate": "Gate 2: Acoustic Boundary Judge",
            "passed": passed,
            "start_sec": start_sec,
            "end_sec": end_sec,
            "duration": round(end_sec - start_sec, 2),
            "notes": notes
        }

        if not passed and auto_fix:
            last_abs = (start_sec + last_word_end_rel) if last_word_end_rel is not None else end_sec
            sug_st, sug_en, cal_logs = cls.auto_calibrate_boundaries(
                wav_path, start_sec, end_sec, first_word_start_abs=start_sec, last_word_end_abs=last_abs
            )
            result["suggested_start"] = sug_st
            result["suggested_end"] = sug_en
            result["self_healing_hint"] = (
                f"Update reel boundaries in config/shows.json to start={sug_st}, end={sug_en}"
            )
            result["notes"].extend(cal_logs)

        return result
