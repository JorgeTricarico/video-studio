import os
from typing import List, Dict

def format_ass_time(seconds: float) -> str:
    """Convierte segundos a formato ASS: H:MM:SS.cs"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    if cs >= 100:
        s += 1
        cs = 0
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

class SubtitleAgent:
    """
    Agente 5: Tipógrafo y Subtítulos Virales Karaoke.
    Agrupa palabras en micropíldoras de 2 a 4 palabras, genera formato .ass
    en la Safe Zone de Instagram (Y=1200), y resalta la palabra activa con
    animación pop-in y color de alto impacto.
    """

    COLOR_MAP = {
        "amarillo": "&H0000FFFF&",  # BGR para Amarillo puro
        "verde": "&H0000FF00&",     # BGR para Verde Neón
        "cian": "&H00FFFF00&",      # BGR para Cian eléctrico
        "blanco": "&H00FFFFFF&"
    }

    def __init__(self, font_name: str = "Arial Black", font_size: int = 70, active_color: str = "amarillo", y_pos: int = 1200):
        self.font_name = font_name
        self.font_size = font_size
        self.active_color_hex = self.COLOR_MAP.get(active_color.lower(), "&H0000FFFF&")
        self.y_pos = y_pos

    def generate(self, words: List[Dict], output_ass_path: str, words_per_chunk: int = 3) -> str:
        """
        Genera el archivo .ass con sincronía a nivel palabra a partir de los datos remapeados.
        """
        if not words:
            # Archivo vacío válido
            with open(output_ass_path, "w", encoding="utf-8") as f:
                f.write("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n[Events]\n")
            return output_ass_path

        ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ViralHormozi,{self.font_name},{self.font_size},&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,3,5,30,30,30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []

        # Agrupar en chunks de 2 a 4 palabras
        for i in range(0, len(words), words_per_chunk):
            chunk = words[i:i + words_per_chunk]
            if not chunk:
                continue

            # Para cada palabra dentro del chunk, emitir una línea donde dicha palabra esté activa
            for active_idx, active_word in enumerate(chunk):
                w_start = format_ass_time(max(0.0, active_word["start"]))
                w_end = format_ass_time(max(active_word["start"] + 0.05, active_word["end"]))

                line_parts = []
                for idx, w in enumerate(chunk):
                    raw_text = w["word"].strip().upper()
                    # Limpiar caracteres que rompen sintaxis ASS
                    clean_text = raw_text.replace("{", "").replace("}", "").replace("\\", "")

                    if idx == active_idx:
                        # Palabra activa: Color destacado + Pop-in 118% -> 106%
                        part = f"{{\\c{self.active_color_hex}\\fscx118\\fscy118\\t(0,100,\\fscx106\\fscy106)}}{clean_text}{{\\r\\c&H00FFFFFF&}}"
                    else:
                        # Palabra inactiva: Blanco normal con borde negro
                        part = clean_text

                    line_parts.append(part)

                full_text = " ".join(line_parts)
                # Alineación \an5 (centro) en coordenadas X=540, Y=self.y_pos (Safe Zone)
                event_line = f"Dialogue: 0,{w_start},{w_end},ViralHormozi,,0,0,0,,{{\\an5\\pos(540,{self.y_pos})}}{full_text}"
                events.append(event_line)

        with open(output_ass_path, "w", encoding="utf-8") as f:
            f.write(ass_header + "\n".join(events) + "\n")

        print(f"  [SubtitleAgent] Archivo .ass generado: {len(events)} eventos de karaoke en {output_ass_path}")
        return output_ass_path
