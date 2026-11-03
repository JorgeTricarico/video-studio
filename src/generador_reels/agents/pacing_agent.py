from typing import List, Dict

class PacingAgent:
    """
    Agente 3: Cirujano de Ritmo y Jump-Cuts Inteligentes.
    Elimina silencios muertos (>0.35s) y pausas de respiración, aplicando la técnica
    de padding y crossfade para evitar clicks y mantener el ritmo dinámico viral.
    Remapea las marcas de tiempo para garantizar sincronía perfecta de subtítulos.
    """

    def __init__(self, target_duration: float = 30.0, max_pause_sec: float = 0.35, pad_start: float = 0.12, pad_end: float = 0.15):
        self.target_duration = target_duration
        self.max_pause_sec = max_pause_sec
        self.pad_start = pad_start
        self.pad_end = pad_end

    def process(self, words: List[Dict], global_start_limit: float = 0.0, global_end_limit: float = 999999.0) -> dict:
        """
        Agrupa palabras continuas en rebanadas (slices), recortando cualquier pausa mayor a max_pause_sec.
        Produce una lista de cortes físicos de video/audio y una lista de palabras con timestamps remapeados.
        """
        if not words:
            # Si no hay palabras, hacer un corte continuo estándar
            dur = min(self.target_duration, global_end_limit - global_start_limit)
            return {
                "cuts": [{"start": global_start_limit, "end": global_start_limit + dur, "duration": dur}],
                "remapped_words": [],
                "total_duration": dur
            }

        # 1. Agrupar palabras continuas en bloques donde el silencio sea menor a max_pause_sec
        slices_words = []
        current_slice = [words[0]]

        for i in range(1, len(words)):
            prev_w = words[i - 1]
            curr_w = words[i]
            gap = curr_w["start"] - prev_w["end"]

            if gap > self.max_pause_sec:
                # Silencio detectado: cerrar rebanada actual y abrir nueva
                slices_words.append(current_slice)
                current_slice = [curr_w]
            else:
                current_slice.append(curr_w)
        
        if current_slice:
            slices_words.append(current_slice)

        # 2. Calcular los límites físicos de cada corte (con márgenes de seguridad para consonantes)
        cuts = []
        remapped_words = []
        timeline_cursor = 0.0

        for slice_idx, s_words in enumerate(slices_words):
            raw_s = max(global_start_limit, s_words[0]["start"] - self.pad_start)
            raw_e = min(global_end_limit, s_words[-1]["end"] + self.pad_end)
            slice_dur = raw_e - raw_s

            if slice_dur <= 0.05:
                continue

            # Asegurar que se complete la idea narrativa sin cortar a la mitad de una frase
            # Solo aplicar tope si excede el límite máximo de formato de video corto
            if timeline_cursor + slice_dur > max(self.target_duration + 35.0, 75.0):
                break

            cuts.append({
                "index": slice_idx,
                "start": round(raw_s, 3),
                "end": round(raw_e, 3),
                "duration": round(slice_dur, 3),
                "timeline_start": round(timeline_cursor, 3)
            })

            # Remapear las palabras de este slice al nuevo tiempo continuo
            for w in s_words:
                time_offset = timeline_cursor - raw_s
                remapped_words.append({
                    "word": w["word"].strip(),
                    "start": round(max(timeline_cursor, w["start"] + time_offset), 3),
                    "end": round(min(timeline_cursor + slice_dur, w["end"] + time_offset), 3),
                    "probability": w.get("probability", 1.0)
                })

            timeline_cursor += slice_dur

        total_condensed = round(timeline_cursor, 3)
        print(f"  [PacingAgent] Video condensado: {len(cuts)} cortes, duración final = {total_condensed}s (sin pausas muertas)")

        return {
            "cuts": cuts,
            "remapped_words": remapped_words,
            "total_duration": total_condensed
        }
