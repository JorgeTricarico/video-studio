import re
from typing import Dict, List, Optional, Tuple

class JudgeAgent:
    """
    Subagente Juez Editorial:
    Evalúa y audita la coherencia narrativa, el contexto inicial y la completitud
    del cierre de los fragmentos antes de renderizar los videos.
    
    Reglas editoriales:
    1. INICIO CONTEXTUAL: No permitir que el video empiece a mitad de frase o con conectores huérfanos ("y", "pero", "porque", "entonces", "o sea").
    2. CIERRE NARRATIVO: No permitir que el video termine a mitad de una frase o pensamiento. Debe cerrar en una pausa conclusiva o signo de puntuación.
    3. DURACIÓN ADAPTATIVA: Si el tema es profundo/emocional, permitir duración media (35-60s) o extendida (60-85s) sin mutilar la idea.
    4. PRESERVACIÓN DEL MENSAJE: Asegurar que el mensaje central sea auto-conclusivo y entendible para alguien que no vio la entrevista completa.
    """

    DANGLING_START_CONNECTORS = [
        "y", "pero", "porque", "entonces", "o sea", "que", "como", "bueno y",
        "además", "por eso", "o sea que", "es que", "pues", "de", "con", "a veces",
        "o", "a", "bueno", "mira", "entonces que"
    ]

    DANGLING_END_CONNECTORS = [
        "y", "pero", "porque", "entonces", "o sea", "que", "como", "de", "con",
        "para", "a veces", "viste", "por ejemplo", "en", "el", "la", "los", "las",
        "un", "una", "este", "esta", "estos", "estas", "del", "al"
    ]

    def __init__(self, brand_config=None):
        self.brand_config = brand_config

    def evaluate_and_refine(
        self,
        transcript_data: dict,
        proposed_start: float,
        proposed_end: float,
        hook_text: str,
        theme_name: str = ""
    ) -> dict:
        """
        Audita el segmento propuesto y devuelve el veredicto con los límites corregidos.
        """
        all_segments = transcript_data.get("segments", [])
        if not all_segments:
            return {
                "verdict": "APPROVED",
                "score": 7.0,
                "adjusted_start": proposed_start,
                "adjusted_end": proposed_end,
                "hook_text": hook_text,
                "duration_category": "Estándar",
                "diagnosis": "Sin datos de transcripción detallados; se respetan límites.",
                "transcript_snippet": ""
            }

        # Extraer todas las palabras ordenadas
        all_words = []
        for seg in all_segments:
            for w in seg.get("words", []):
                all_words.append(w)

        if not all_words:
            return {
                "verdict": "APPROVED",
                "score": 7.0,
                "adjusted_start": proposed_start,
                "adjusted_end": proposed_end,
                "hook_text": hook_text,
                "duration_category": "Estándar",
                "diagnosis": "Sin palabras detalladas; se respetan límites.",
                "transcript_snippet": ""
            }

        opening_diagnosis = []
        closing_diagnosis = []

        # ----------------------------------------------------
        # 1. AUDITAR INICIO (Boundary & Context Alignment)
        # ----------------------------------------------------
        adj_start = proposed_start

        # Encontrar índice de la palabra más cercana a proposed_start
        closest_start_idx = 0
        min_start_dist = float("inf")
        for idx, w in enumerate(all_words):
            dist = abs(w["start"] - proposed_start)
            if dist < min_start_dist:
                min_start_dist = dist
                closest_start_idx = idx

        # Buscar si hay un punto o fin de oración previo cerca (entre -2.0s y +2.5s de proposed_start)
        best_candidate = None
        min_start_score = float("inf")
        theme_tokens = set(theme_name.lower().split() + hook_text.lower().split())

        for i in range(max(0, closest_start_idx - 8), min(len(all_words) - 1, closest_start_idx + 8)):
            curr_w = all_words[i]
            next_w = all_words[i + 1]
            raw_curr = curr_w["word"].strip()
            if raw_curr.endswith((".", "!", "?")):
                cand_s = next_w["start"]
                dist = abs(cand_s - proposed_start)
                if dist <= 2.5:
                    clean_w1 = re.sub(r"[^\w\s]", "", next_w["word"]).lower().strip()
                    clean_w2 = ""
                    if i + 2 < len(all_words):
                        clean_w2 = re.sub(r"[^\w\s]", "", all_words[i + 2]["word"]).lower().strip()
                    clean_two = f"{clean_w1} {clean_w2}".strip()

                    is_weak = (clean_w1 in self.DANGLING_START_CONNECTORS) or (clean_two in self.DANGLING_START_CONNECTORS)
                    has_theme_kw = (clean_w1 in theme_tokens) or (clean_w2 in theme_tokens)

                    cand_score = dist + (3.0 if is_weak else 0.0) - (1.5 if has_theme_kw else 0.0)
                    if cand_score < min_start_score:
                        min_start_score = cand_score
                        best_candidate = (cand_s, next_w["word"])

        if best_candidate is not None:
            cand_s, w_text = best_candidate
            if abs(cand_s - proposed_start) > 0.15:
                opening_diagnosis.append(
                    f"Inicio alineado a {cand_s:.2f}s al comienzo exacto de la oración ('{w_text}...')."
                )
            adj_start = cand_s
        else:
            # Si no hay frontera de oración inmediata, verificar si el inicio cae a mitad de una frase
            backtracked_start = None
            for i in range(closest_start_idx, max(-1, closest_start_idx - 25), -1):
                if i == 0 or all_words[i - 1]["word"].strip().endswith((".", "!", "?")):
                    start_w = all_words[i]
                    if proposed_start - start_w["start"] <= 7.0:
                        backtracked_start = start_w["start"]
                    break
            
            if backtracked_start is not None and (proposed_start - backtracked_start) > 0.4:
                adj_start = backtracked_start
                opening_diagnosis.append(
                    f"Inicio extendido a {adj_start:.2f}s para no cortar la oración inicial a la mitad."
                )

        # ----------------------------------------------------
        # 2. AUDITAR CIERRE (Sentence Completion & Punchy Climax)
        # ----------------------------------------------------
        adj_end = proposed_end

        # Encontrar palabra más cercana a proposed_end
        closest_end_idx = len(all_words) - 1
        min_end_dist = float("inf")
        for idx in range(len(all_words) - 1, -1, -1):
            w = all_words[idx]
            dist = abs(w["end"] - proposed_end)
            if dist < min_end_dist:
                min_end_dist = dist
                closest_end_idx = idx

        # Buscar el cierre de oración más cercano después o antes de proposed_end
        closure_idx = None
        for i in range(closest_end_idx, min(len(all_words), closest_end_idx + 15)):
            w = all_words[i]
            if w["end"] - proposed_end > 6.0:
                break
            if w["word"].strip().endswith((".", "!", "?")):
                closure_idx = i
                break

        if closure_idx is None:
            for i in range(closest_end_idx, max(0, closest_end_idx - 10), -1):
                w = all_words[i]
                if proposed_end - w["end"] > 4.0:
                    break
                if w["word"].strip().endswith((".", "!", "?")):
                    closure_idx = i
                    break

        if closure_idx is not None:
            end_w = all_words[closure_idx]
            final_end_s = end_w["end"]
            
            # Lookahead para remate contundente (ej. "Es un montón.", < 3.0s y <= 5 palabras)
            if closure_idx + 1 < len(all_words):
                next_closure_idx = None
                for j in range(closure_idx + 1, min(len(all_words), closure_idx + 8)):
                    if all_words[j]["word"].strip().endswith((".", "!", "?")):
                        next_closure_idx = j
                        break
                if next_closure_idx is not None:
                    next_dur = all_words[next_closure_idx]["end"] - all_words[closure_idx + 1]["start"]
                    word_count = next_closure_idx - closure_idx
                    if word_count <= 5 and next_dur <= 2.8:
                        punchline = " ".join(all_words[k]["word"].strip() for k in range(closure_idx + 1, next_closure_idx + 1))
                        closure_idx = next_closure_idx
                        final_end_s = all_words[next_closure_idx]["end"]
                        closing_diagnosis.append(f"Cierre extendido a {final_end_s:.2f}s para incluir remate contundente: '{punchline}'.")

            if abs(final_end_s - proposed_end) > 0.2 and not closing_diagnosis:
                closing_diagnosis.append(f"Cierre ajustado a {final_end_s:.2f}s para concluir la oración en punto.")
            adj_end = final_end_s

        # 4. DETERMINAR DURACIÓN ADAPTATIVA Y CATEGORÍA
        final_dur = adj_end - adj_start
        if final_dur < 35.0:
            dur_cat = "Corta (Snackable / Hook Rápido)"
        elif final_dur <= 65.0:
            dur_cat = "Media (Narrativa Estándar)"
        else:
            dur_cat = "Extendida (Testimonial Profundo)"

        # 5. RECOLECTAR Y LIMPIAR DIÁLOGO FINAL
        included_words = []
        for seg in all_segments:
            for w in seg.get("words", []):
                if w["start"] >= adj_start - 0.02 and w["end"] <= adj_end + 0.05:
                    included_words.append(w)

        full_dialogue = " ".join(w["word"].strip() for w in included_words)

        # 6. CALCULAR SCORE DE COHERENCIA (1 a 10)
        score = 10.0
        warnings = []

        if full_dialogue and full_dialogue.split()[0].lower() in self.DANGLING_START_CONNECTORS:
            score -= 1.5
            warnings.append("El diálogo inicia con un conector huérfano.")

        if full_dialogue and not full_dialogue.endswith((".", "!", "?")):
            score -= 1.5
            warnings.append("El diálogo no termina con puntuación conclusiva.")

        if final_dur > 85.0:
            score -= 1.0
            warnings.append("Duración superior a 85s; verificar retención en Instagram Reels.")

        verdict = "APPROVED" if score >= 7.5 else "ADJUSTED"
        if not opening_diagnosis and not closing_diagnosis:
            main_diagnosis = "Diálogo coherente, apertura y remate balanceados."
        else:
            changes = []
            if opening_diagnosis:
                changes.extend(opening_diagnosis)
            if closing_diagnosis:
                changes.extend(closing_diagnosis)
            main_diagnosis = " | ".join(changes)

        return {
            "verdict": verdict,
            "score": round(score, 1),
            "original_start": proposed_start,
            "original_end": proposed_end,
            "adjusted_start": round(adj_start, 2),
            "adjusted_end": round(adj_end, 2),
            "duration_sec": round(final_dur, 2),
            "duration_category": dur_cat,
            "hook_text": hook_text,
            "words": included_words,
            "full_dialogue": full_dialogue,
            "diagnosis": main_diagnosis,
            "warnings": warnings
        }

    def print_judgment_report(self, judgment: dict, theme_name: str = ""):
        """Imprime un reporte visual y claro del dictamen editorial."""
        v = judgment["verdict"]
        score = judgment["score"]
        dur = judgment["duration_sec"]
        cat = judgment["duration_category"]

        print(f"\n  [JudgeAgent] ================= DICTAMEN EDITORIAL =================")
        print(f"  [JudgeAgent] Tema: '{theme_name}' | Estado: {v} | Score: {score}/10")
        print(f"  [JudgeAgent] Duración estimada: {dur}s ({cat})")
        print(f"  [JudgeAgent] Límites: [{judgment['adjusted_start']}s -> {judgment['adjusted_end']}s] "
              f"(Original: [{judgment['original_start']}s -> {judgment['original_end']}s])")
        print(f"  [JudgeAgent] Diagnóstico: {judgment['diagnosis']}")
        if judgment["warnings"]:
            for w in judgment["warnings"]:
                print(f"  [JudgeAgent] [!] Advertencia: {w}")
        print(f"  [JudgeAgent] Guion a escuchar:")
        print(f"               \"{judgment['full_dialogue'][:140]}...\"")
        print(f"  [JudgeAgent] ========================================================\n")
