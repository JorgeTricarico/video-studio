import os
import sys

# Asegurar compatibilidad con consola de Windows (evitar errores cp1252)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from .agents import (
    TranscriptionAgent,
    CuratorAgent,
    JudgeAgent,
    PacingAgent,
    VFXAgent,
    SubtitleAgent,
    RenderAgent,
    get_media_info
)

class ReelPipeline:
    """
    Orquestador del Pipeline Multi-Agente para la creación de Reels Virales.
    Coordina secuencialmente la labor de cada agente especializado.
    """

    def __init__(
        self,
        target_duration: float = 30.0,
        crop_mode: str = "johanna",
        active_color: str = "amarillo",
        enable_zooms: bool = True,
        enable_branding: bool = True,
        whisper_model: str = "small",
        brand_config = None
    ):
        self.target_duration = target_duration
        self.crop_mode = crop_mode
        self.active_color = active_color
        self.enable_zooms = enable_zooms
        self.enable_branding = enable_branding
        self.brand_config = brand_config
        
        self.transcription_agent = TranscriptionAgent(model_name=whisper_model)
        self.curator_agent = CuratorAgent(target_duration=target_duration)
        if self.brand_config and hasattr(self.brand_config, "themes") and self.brand_config.themes:
            for k, t in self.brand_config.themes.items():
                self.curator_agent.PRESET_THEMES[k] = {
                    "title": t.title,
                    "hook_text": t.hook_text,
                    "start": t.start,
                    "end": t.end,
                    "keywords": t.keywords
                }
        self.judge_agent = JudgeAgent(brand_config=brand_config)
        self.pacing_agent = PacingAgent(target_duration=target_duration)
        self.vfx_agent = VFXAgent(crop_mode=crop_mode, enable_zooms=enable_zooms, enable_branding=enable_branding)
        self.subtitle_agent = SubtitleAgent(active_color=active_color)
        self.render_agent = RenderAgent()

    def run(
        self,
        video_input: str,
        output_video: str,
        theme_or_query: str = "cristian",
        hook_override: str = None,
        start_sec: float = None,
        end_sec: float = None,
        cache_json: str = "transcript_cache.json"
    ) -> str:
        print("\n========================================================")
        print(f"[*] INICIANDO PIPELINE MULTI-AGENTE: REEL VIRAL")
        print(f"    Video: {video_input}")
        print(f"    Tema: '{theme_or_query}' | Objetivo: {self.target_duration}s")
        print("========================================================\n")

        # Determinar ventana tentativa para transcribir ultra-rápido
        win_s = start_sec
        win_e = end_sec
        if win_s is None or win_e is None:
            preset = self.curator_agent.PRESET_THEMES.get(theme_or_query.lower())
            if preset:
                win_s = preset["start"]
                win_e = preset["end"]

        # 1. Transcripción con timestamps a nivel palabra
        print("[Paso 1/7] Agente de Transcripción...")
        transcript = self.transcription_agent.transcribe(
            video_input,
            cache_json=cache_json if win_s is None else None,
            window_start=win_s,
            window_end=win_e
        )

        # 2. Curaduría del Momento Clave y Hook
        print("\n[Paso 2/7] Agente Curador de Hooks y Guion...")
        soundbite = self.curator_agent.curate(
            transcript,
            theme_or_query=theme_or_query,
            start_override=start_sec,
            end_override=end_sec
        )
        hook_text = hook_override if hook_override else soundbite["hook_text"]
        print(f"    Hook inicial asignado: '{hook_text}'")

        # 3. Juez Editorial: Auditar coherencia, contexto inicial, cierre completo y duración adaptativa
        print("\n[Paso 3/7] Agente Juez Editorial (Auditoría de Coherencia)...")
        judgment = self.judge_agent.evaluate_and_refine(
            transcript_data=transcript,
            proposed_start=soundbite["raw_start"],
            proposed_end=soundbite["raw_end"],
            hook_text=hook_text,
            theme_name=theme_or_query
        )
        self.judge_agent.print_judgment_report(judgment, theme_name=theme_or_query)

        # Asignar fragmento auditado por el Juez
        curated_words = judgment["words"]
        curated_start = judgment["adjusted_start"]
        curated_end = judgment["adjusted_end"]

        # 4. Pacing, Jump-Cuts y Eliminación de Silencios
        print("\n[Paso 4/7] Agente Cirujano de Ritmo (Jump-Cuts)...")
        pacing_result = self.pacing_agent.process(
            curated_words,
            global_start_limit=curated_start,
            global_end_limit=curated_end
        )
        cuts = pacing_result["cuts"]
        remapped_words = pacing_result["remapped_words"]
        total_duration = pacing_result["total_duration"]

        # 5. Generación de Subtítulos Karaoke en Safe Zone
        print("\n[Paso 5/7] Agente Tipógrafo y Subtítulos Virales...")
        temp_ass = "temp_subtitulos_viral.ass"
        self.subtitle_agent.generate(remapped_words, temp_ass, words_per_chunk=3)

        # 6. Diseño y Plan de Filtros Visuales (VFX, Johanna Crop, Badge)
        print("\n[Paso 6/7] Agente Director de Arte y VFX...")
        badge_path = "soygarrahan_badge.png"
        
        media_info = get_media_info(video_input)
        is_1080x1920 = True
        try:
            w = media_info["streams"][0]["width"]
            h = media_info["streams"][0]["height"]
            if w == 1280 and h == 720:
                is_1080x1920 = False
        except Exception:
            pass

        vfx_parts = self.vfx_agent.get_filtergraph_parts(
            duration=total_duration,
            hook_text=hook_text,
            badge_png_path=badge_path,
            input_is_1080x1920=is_1080x1920
        )

        # 7. Render Final Multipass con FFmpeg
        print("\n[Paso 7/7] Agente Ingeniero de Render...")
        final_video = self.render_agent.render(
            input_video=video_input,
            cuts=cuts,
            ass_subtitles_path=temp_ass,
            output_video=output_video,
            vfx_filtergraph_parts=vfx_parts,
            normalize_audio=True
        )

        # Limpiar temporal ASS
        if os.path.exists(temp_ass):
            try:
                os.remove(temp_ass)
            except Exception:
                pass

        print("\n========================================================")
        print(f"[OK] REEL VIRAL GENERADO CON EXITO: {final_video}")
        print("========================================================\n")
        return final_video
