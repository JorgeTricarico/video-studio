# filepath: core/subtitle_engine.py
import os
import re
import json
from typing import List, Dict, Any, Tuple, Optional, Union
from .env_config import DICT_PATH, resolve_font
from .audio_boundary_auditor import AudioBoundaryAuditor

_CLEAN_TOKEN_RE = re.compile(r"[^\wáéíóúÁÉÍÓÚñÑüÜ]")
_STRONG_PUNCT_RE = re.compile(r"[\.?!:]$")
_COMMA_PUNCT_RE = re.compile(r"[,;]$")
_CONNECTOR_RE = re.compile(r"^(y|o|pero|porque|que|cuando|donde)\b", re.IGNORECASE)


def format_ass_time(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    total_cs = int(round(seconds * 100))
    cs = total_cs % 100
    total_s = total_cs // 100
    s = total_s % 60
    m = (total_s // 60) % 60
    h = total_s // 3600
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def color_to_ass(color_str: str) -> str:
    """
    Convierte cualquier formato de color (Hex #RRGGBB, nombre o &H00BBGGRR&) a formato ASS (&H00BBGGRR&).
    """
    if not color_str:
        return "&H0000FFFF&"  # Amarillo Hormozi por defecto

    color_str = color_str.strip()
    if color_str.startswith("&H") and color_str.endswith("&"):
        return color_str

    named_colors = {
        "amarillo": "&H0000FFFF&",
        "yellow": "&H0000FFFF&",
        "cyan": "&H00FFFF00&",
        "celeste": "&H00FFFF00&",
        "verde": "&H0000FF00&",
        "green": "&H0000FF00&",
        "rojo": "&H000000FF&",
        "red": "&H000000FF&",
        "blanco": "&H00FFFFFF&",
        "white": "&H00FFFFFF&",
        "naranja": "&H000080FF&",
        "orange": "&H000080FF&",
        "magenta": "&H00FF00FF&",
        "rosa": "&H00FF00FF&",
        "pink": "&H00FF00FF&",
    }
    lower = color_str.lower()
    if lower in named_colors:
        return named_colors[lower]

    if color_str.startswith("#"):
        hex_val = color_str.lstrip("#")
        if len(hex_val) == 6:
            r = hex_val[0:2]
            g = hex_val[2:4]
            b = hex_val[4:6]
            return f"&H00{b}{g}{r}&".upper()

    return "&H0000FFFF&"


class TextQualityAssurance:
    """
    Motor de Control de Calidad Lingüística y Corrección Fonética de Transcripciones.
    Pre-compila patrones n-grama y diccionarios desde config/dictionary.json.
    """
    _config = None
    _compiled_multi = None
    _compiled_blacklist = None

    @classmethod
    def load_config(cls) -> Dict[str, Any]:
        if cls._config is None:
            if os.path.exists(DICT_PATH):
                with open(DICT_PATH, "r", encoding="utf-8") as f:
                    cls._config = json.load(f)
            else:
                cls._config = {"multiword_replacements": [], "word_replacements": {}, "blacklist_typos": []}

            # Pre-procesar reemplazos multipalabra ordenados por longitud descendente
            multi_rules = cls._config.get("multiword_replacements", [])
            cls._compiled_multi = []
            for rule in sorted(multi_rules, key=lambda x: len(x["pattern"]), reverse=True):
                norm_pattern = tuple(_CLEAN_TOKEN_RE.sub("", p).lower() for p in rule["pattern"])
                cls._compiled_multi.append((norm_pattern, rule["replacement"]))

            # Pre-compilar regex de blacklist
            cls._compiled_blacklist = [
                (b, re.compile(r"(?<!\w)" + re.escape(b.lower()) + r"(?!\w)"))
                for b in cls._config.get("blacklist_typos", [])
            ]
        return cls._config

    @classmethod
    def reload_config(cls):
        cls._config = None
        cls.load_config()

    @classmethod
    def clean_word(cls, word: str) -> str:
        cfg = cls.load_config()
        repls = cfg.get("word_replacements", {})
        w = word.strip()
        if not w:
            return w
        clean = _CLEAN_TOKEN_RE.sub("", w)
        lower = clean.lower()
        if lower in repls:
            dst = repls[lower]
            prefix = w[0] if w[0] in "¿¡(\"" else ""
            suffix = w[-1] if w[-1] in "?!.,;:)\"" else ""
            return f"{prefix}{dst}{suffix}"
        return w

    @classmethod
    def sanitize_words(cls, words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        cls.load_config()
        words = AudioBoundaryAuditor.audit_and_trim_start(words)
        if not words:
            return []

        norm_tokens = [_CLEAN_TOKEN_RE.sub("", w["word"]).lower() for w in words]
        sanitized = []
        i = 0
        n = len(words)

        while i < n:
            matched = False
            for target_tuple, replacement in cls._compiled_multi:
                k = len(target_tuple)
                if i + k <= n and tuple(norm_tokens[i:i + k]) == target_tuple:
                    start_t = float(words[i]["start"])
                    end_t = max(start_t + 0.05, float(words[i + k - 1]["end"]))
                    rep_parts = replacement.split(" ")
                    dur_per = (end_t - start_t) / len(rep_parts)
                    for r_idx, rp in enumerate(rep_parts):
                        w_st = round(start_t + r_idx * dur_per, 3)
                        w_en = round(start_t + (r_idx + 1) * dur_per, 3) if r_idx < len(rep_parts) - 1 else round(end_t, 3)
                        sanitized.append({
                            "word": rp,
                            "start": w_st,
                            "end": w_en
                        })
                    i += k
                    matched = True
                    break
            if not matched:
                w_copy = dict(words[i])
                w_copy["word"] = cls.clean_word(w_copy["word"])
                sanitized.append(w_copy)
                i += 1

        return sanitized

    @classmethod
    def audit_text(cls, words: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        cls.load_config()
        full_text = " ".join(w["word"] for w in words).lower()
        errors = []
        for typo_str, pattern_re in cls._compiled_blacklist:
            if pattern_re.search(full_text):
                errors.append(
                    f"Residual blacklisted typo found: '{typo_str}'. "
                    f"ACTION REQUIRED: Add '{typo_str}' to 'word_replacements' or 'multiword_replacements' in config/dictionary.json."
                )
        return (len(errors) == 0, errors)


class SubtitleEngine:
    """
    Motor Universal de Subtítulos Dinámicos e Inteligentes:
    - Estilo Hormozi Viral con karaoke palabra por palabra, pop animado y tipografía destacada.
    - Estilos alternativos: minimal clean, boxed modern, tiktok neon.
    - Eliminación completa de parpadeos y solapamientos en libass.
    - Ingesta de Whisper JSON (completo o compacto), SRT, VTT o estructuras nativas.
    """
    STYLE_PRESETS = {
        "hormozi": {
            "font_name": "Arial Black",
            "font_size": 58,
            "active_color": "&H0000FFFF&",  # Amarillo BGR
            "primary_color": "&H00FFFFFF&", # Blanco
            "outline": 6,
            "shadow": 3,
            "y_pos": 1450,
            "uppercase": True,
            "box_style": False
        },
        "hormozi_cyan": {
            "font_name": "Arial Black",
            "font_size": 58,
            "active_color": "&H00FFFF00&",  # Cyan
            "primary_color": "&H00FFFFFF&",
            "outline": 6,
            "shadow": 3,
            "y_pos": 1450,
            "uppercase": True,
            "box_style": False
        },
        "hormozi_green": {
            "font_name": "Arial Black",
            "font_size": 58,
            "active_color": "&H0000FF00&",  # Verde Neón
            "primary_color": "&H00FFFFFF&",
            "outline": 6,
            "shadow": 3,
            "y_pos": 1450,
            "uppercase": True,
            "box_style": False
        },
        "minimal": {
            "font_name": "Arial",
            "font_size": 46,
            "active_color": "&H0000E5FF&",
            "primary_color": "&H00FFFFFF&",
            "outline": 2,
            "shadow": 1,
            "y_pos": 1600,
            "uppercase": False,
            "box_style": False
        },
        "boxed": {
            "font_name": "Arial Bold",
            "font_size": 50,
            "active_color": "&H0000FFFF&",
            "primary_color": "&H00FFFFFF&",
            "outline": 0,
            "shadow": 0,
            "y_pos": 1480,
            "uppercase": True,
            "box_style": True
        }
    }

    @staticmethod
    def load_words_from_transcript(transcript_source: Union[str, Dict, List]) -> List[Dict[str, Any]]:
        """
        Ingesta palabras y tiempos desde diversas fuentes:
        - Ruta a archivo JSON de Whisper (completo o compacto)
        - Ruta a archivo SRT o VTT
        - Diccionario cargado o lista de palabras
        """
        if isinstance(transcript_source, list):
            return transcript_source

        if isinstance(transcript_source, dict):
            words = []
            for seg in transcript_source.get("segments", []):
                for w in seg.get("words", []):
                    words.append({
                        "word": w.get("word", w.get("w", "")).strip(),
                        "start": float(w.get("start", w.get("s", 0.0))),
                        "end": float(w.get("end", w.get("e", 0.0)))
                    })
            return words

        if isinstance(transcript_source, str) and os.path.exists(transcript_source):
            lower = transcript_source.lower()
            if lower.endswith(".json"):
                with open(transcript_source, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return SubtitleEngine.load_words_from_transcript(data)

            if lower.endswith(".srt") or lower.endswith(".vtt"):
                return SubtitleEngine._parse_srt_vtt_to_words(transcript_source)

        return []

    @staticmethod
    def _parse_srt_vtt_to_words(sub_file_path: str) -> List[Dict[str, Any]]:
        """Parsea SRT/VTT aproximando tiempos palabra por palabra."""
        words = []
        with open(sub_file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        time_re = re.compile(r"(\d{1,2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}[,\.]\d{3})")

        def parse_stamp(ts: str) -> float:
            ts = ts.replace(",", ".")
            parts = ts.split(":")
            if len(parts) == 3:
                return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
            return float(parts[0]) * 60 + float(parts[1])

        i = 0
        n = len(lines)
        while i < n:
            line = lines[i].strip()
            match = time_re.search(line)
            if match:
                st = parse_stamp(match.group(1))
                en = parse_stamp(match.group(2))
                i += 1
                text_lines = []
                while i < n and lines[i].strip() and not time_re.search(lines[i]):
                    if not lines[i].strip().isdigit():
                        text_lines.append(lines[i].strip())
                    i += 1
                full_text = " ".join(text_lines)
                clean_tokens = [w for w in full_text.split() if w]
                if clean_tokens:
                    dur = max(0.1, en - st)
                    dur_per_word = dur / len(clean_tokens)
                    for idx, tok in enumerate(clean_tokens):
                        words.append({
                            "word": tok,
                            "start": round(st + idx * dur_per_word, 3),
                            "end": round(st + (idx + 1) * dur_per_word, 3)
                        })
                continue
            i += 1
        return words

    @staticmethod
    def dynamic_chunk_words(
        words: List[Dict[str, Any]],
        min_words: int = 4,
        max_words: int = 7,
        max_chars: int = 34,
        target_duration: float = 2.4,
        split_pause_gap: float = 0.38
    ) -> List[List[Dict[str, Any]]]:
        if not words:
            return []

        chunks = []
        current_chunk = []
        chunk_start = float(words[0]["start"])
        current_chars = 0

        for i, w in enumerate(words):
            raw_w = w["word"].strip()
            w_start = float(w["start"])
            w_end = float(w["end"])
            w_len = len(raw_w)

            is_last = (i == len(words) - 1)
            next_start = float(words[i + 1]["start"]) if not is_last else None
            gap_to_next = (next_start - w_end) if next_start is not None else 0.0

            current_chunk.append(w)
            current_chars += w_len + 1
            chunk_duration = w_end - chunk_start
            n_words = len(current_chunk)

            should_break = False
            reason = None

            if not is_last and gap_to_next >= split_pause_gap:
                should_break = True
                reason = "gap"
            elif n_words >= min_words and _STRONG_PUNCT_RE.search(raw_w):
                should_break = True
                reason = "strong_punct"
            elif n_words >= max_words:
                should_break = True
                reason = "max_words"
            elif current_chars >= max_chars:
                should_break = True
                reason = "max_chars"
            elif chunk_duration >= target_duration and n_words >= min_words:
                should_break = True
                reason = "target_dur"
            elif not is_last and n_words >= 3:
                next_word = words[i + 1]["word"].strip()
                if _COMMA_PUNCT_RE.search(raw_w) and _CONNECTOR_RE.match(next_word):
                    should_break = True
                    reason = "comma_connector"

            if should_break:
                chunks.append(current_chunk)
                current_chunk = []
                if not is_last:
                    chunk_start = float(words[i + 1]["start"])
                current_chars = 0

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    @staticmethod
    def balance_two_lines(chunk: List[Dict[str, Any]]) -> int:
        n = len(chunk)
        if n <= 3:
            return -1

        total_len = sum(len(TextQualityAssurance.clean_word(w["word"])) for w in chunk) + n - 1
        target_mid = total_len / 2.0

        best_split = n // 2
        best_diff = 999.0
        running_len = 0

        for idx, w in enumerate(chunk[:-1]):
            running_len += len(TextQualityAssurance.clean_word(w["word"])) + 1
            diff = abs(running_len - target_mid)
            next_word_lower = TextQualityAssurance.clean_word(chunk[idx + 1]["word"]).lower()
            if next_word_lower in {"de", "la", "el", "en", "para", "por", "que", "y", "a", "los", "las", "un", "una"}:
                diff -= 2.0
            if diff < best_diff:
                best_diff = diff
                best_split = idx + 1

        return best_split

    @staticmethod
    def _normalize_monotonic_timings(words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not words:
            return []
        norm = [dict(w) for w in words]
        for i in range(len(norm)):
            st = max(0.0, float(norm[i]["start"]))
            en = float(norm[i]["end"])
            if i > 0 and st < norm[i - 1]["end"]:
                st = norm[i - 1]["end"]
            if i + 1 < len(norm):
                next_st = float(norm[i + 1]["start"])
                if next_st <= st:
                    next_st = st + 0.06
                    norm[i + 1]["start"] = round(next_st, 3)
                en = min(max(st + 0.04, en), next_st)
            else:
                en = max(st + 0.08, en)
            norm[i]["start"] = round(st, 3)
            norm[i]["end"] = round(en, 3)
        return norm

    @classmethod
    def generate_ass(
        cls,
        words: List[Dict[str, Any]],
        out_path: str,
        font_name: str = "Arial Black",
        font_size: int = 58,
        active_color: str = "&H0000FFFF&",
        y_pos: int = 1450,
        max_hang_time: float = 1.4,
        use_dynamic: bool = True,
        style_preset: str = None,
        uppercase: bool = None
    ) -> str:
        """
        Genera archivo .ass con subtítulos estilizados y timing calibrado.
        Soporta presets ('hormozi', 'minimal', 'boxed', etc.) o parámetros directos.
        """
        # Resolver presets
        if style_preset and style_preset.lower() in cls.STYLE_PRESETS:
            preset = cls.STYLE_PRESETS[style_preset.lower()]
            font_name = preset.get("font_name", font_name)
            font_size = preset.get("font_size", font_size)
            active_color = preset.get("active_color", active_color)
            if y_pos == 1450:
                y_pos = preset.get("y_pos", y_pos)
            if uppercase is None:
                uppercase = preset.get("uppercase", True)
        else:
            if uppercase is None:
                uppercase = True

        active_color_ass = color_to_ass(active_color)

        words = TextQualityAssurance.sanitize_words(words)
        words = cls._normalize_monotonic_timings(words)
        passed, errors = TextQualityAssurance.audit_text(words)
        if not passed:
            print(f"  [!] ADVERTENCIA AUDITORIA DE TEXTO: {errors}")
        else:
            print("  [OK] TextQualityAssurance: Subtitulos auditados y verificados.")

        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ViralHormozi,{font_name},{font_size},&H00FFFFFF,{active_color_ass},&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,3,5,40,40,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []
        if use_dynamic:
            chunks = cls.dynamic_chunk_words(words)
        else:
            chunks = [words[i:i + 6] for i in range(0, len(words), 6) if words[i:i + 6]]

        for c_idx, chunk in enumerate(chunks):
            next_chunk_start = float(chunks[c_idx + 1][0]["start"]) if c_idx + 1 < len(chunks) else None
            split_idx = cls.balance_two_lines(chunk)

            for active_idx, active_w in enumerate(chunk):
                w_start_sec = float(active_w["start"])

                if active_idx + 1 < len(chunk):
                    w_end_sec = float(chunk[active_idx + 1]["start"])
                else:
                    last_w_end = float(active_w["end"])
                    if next_chunk_start is not None:
                        gap = max(0.0, next_chunk_start - last_w_end)
                        w_end_sec = next_chunk_start if gap <= max_hang_time else (last_w_end + max_hang_time)
                    else:
                        w_end_sec = last_w_end + 0.30

                if w_end_sec <= w_start_sec:
                    w_end_sec = w_start_sec + 0.04

                w_start = format_ass_time(w_start_sec)
                w_end = format_ass_time(w_end_sec)

                line_parts = []
                for idx, w in enumerate(chunk):
                    raw_text = TextQualityAssurance.clean_word(w["word"]).replace("{", "").replace("}", "").replace("\\", "")
                    if uppercase:
                        raw_text = raw_text.upper()
                    if idx == active_idx:
                        part = f"{{\\c{active_color_ass}\\fscx112\\fscy112\\t(0,90,\\fscx104\\fscy104)}}{raw_text}{{\\r\\c&H00FFFFFF&}}"
                    else:
                        part = raw_text
                    line_parts.append(part)

                if split_idx > 0 and split_idx < len(line_parts):
                    full_text = " ".join(line_parts[:split_idx]) + "\\N" + " ".join(line_parts[split_idx:])
                else:
                    full_text = " ".join(line_parts)

                event_line = f"Dialogue: 0,{w_start},{w_end},ViralHormozi,,0,0,0,,{{\\an5\\pos(540,{y_pos})}}{full_text}"
                events.append(event_line)

        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(header + "\n".join(events) + "\n")
        return out_path
