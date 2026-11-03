import re
from typing import Dict, List, Optional

class CuratorAgent:
    """
    Agente 2: Curador de Hooks y Guiones Virales.
    Analiza la transcripción y selecciona los momentos de máximo impacto emocional
    y noticioso, aplicando la estructura viral: Hook (0-3s) -> Problema -> Cierre (~30s).
    """

    PRESET_THEMES = {
        "cristian": {
            "title": "Caso Cristian: Tenía 15 años",
            "hook_text": "CRISTIAN TENÍA 15 AÑOS",
            "start": 62.0,
            "end": 114.5,
            "keywords": ["cristian", "falleció", "años", "incluir salud", "leches", "meses", "latas"]
        },
        "hospital": {
            "title": "El Hospital No Te Pregunta Qué Votaste",
            "hook_text": "EL HOSPITAL NO PREGUNTA QUÉ VOTASTE",
            "start": 177.0,
            "end": 206.0,
            "keywords": ["hospital", "partido", "banderas", "abraza", "cura", "política"]
        },
        "politica": {
            "title": "El Hospital No Te Pregunta Qué Votaste",
            "hook_text": "EL HOSPITAL NO PREGUNTA QUÉ VOTASTE",
            "start": 177.0,
            "end": 206.0,
            "keywords": ["hospital", "partido", "banderas", "abraza", "cura", "política"]
        },
        "medicacion": {
            "title": "Mientras los Pibes se Deterioran",
            "hook_text": "MIENTRAS LOS PIBES SE DETERIORAN",
            "start": 464.0,
            "end": 520.0,
            "keywords": ["pibes", "medicación", "provincias", "nación", "deterioran", "hijos"]
        },
        "fiebre": {
            "title": "Mientras los Pibes se Deterioran",
            "hook_text": "MIENTRAS LOS PIBES SE DETERIORAN",
            "start": 464.0,
            "end": 520.0,
            "keywords": ["pibes", "medicación", "provincias", "nación", "deterioran", "hijos"]
        },
        "futuro": {
            "title": "¿A Dónde Van a Ir Nuestros Hijos?",
            "hook_text": "¿A DÓNDE VAN A IR NUESTROS HIJOS?",
            "start": 293.0,
            "end": 323.5,
            "keywords": ["hijos", "crecer", "posadas", "colapsado", "salud pública"]
        },
        "marcha": {
            "title": "¿A Dónde Van a Ir Nuestros Hijos?",
            "hook_text": "¿A DÓNDE VAN A IR NUESTROS HIJOS?",
            "start": 293.0,
            "end": 323.5,
            "keywords": ["hijos", "crecer", "posadas", "colapsado", "salud pública"]
        }
    }

    def __init__(self, target_duration: float = 30.0):
        self.target_duration = target_duration

    def get_available_themes(self) -> List[str]:
        return list(self.PRESET_THEMES.keys())

    def curate(self, transcript_data: dict, theme_or_query: str = "cristian", start_override: float = None, end_override: float = None) -> dict:
        """
        Selecciona las palabras y fragmentos que conformarán el reel viral.
        """
        theme_key = theme_or_query.lower()
        preset = self.PRESET_THEMES.get(theme_key)

        if start_override is not None and end_override is not None:
            hook_text = "TESTIMONIO DE JOHANNA"
            t_start = start_override
            t_end = end_override
        elif preset:
            hook_text = preset["hook_text"]
            t_start = preset["start"]
            t_end = preset["end"]
        else:
            # Búsqueda semántica básica por palabras clave
            print(f"  [CuratorAgent] Buscando coincidencias para '{theme_or_query}'...")
            best_segment = None
            best_score = 0
            for seg in transcript_data.get("segments", []):
                score = sum(1 for w in theme_key.split() if w in seg["text"].lower())
                if score > best_score:
                    best_score = score
                    best_segment = seg
            
            if best_segment:
                t_start = max(0.0, best_segment["start"] - 2.0)
                t_end = t_start + self.target_duration + 8.0
                hook_text = best_segment["text"][:30].upper()
            else:
                # Fallback a los primeros 35s
                t_start = 60.0
                t_end = 95.0
                hook_text = "CRISIS EN EL GARRAHAN"

        # Extraer todas las palabras dentro del rango seleccionado
        curated_words = []
        for seg in transcript_data.get("segments", []):
            for w in seg.get("words", []):
                if w["start"] >= t_start and w["end"] <= t_end:
                    curated_words.append(w)

        print(f"  [CuratorAgent] Segmento seleccionado: [{t_start:.1f}s -> {t_end:.1f}s] ({len(curated_words)} palabras)")
        return {
            "hook_text": hook_text,
            "raw_start": t_start,
            "raw_end": t_end,
            "words": curated_words
        }
