# filepath: core/video_editor.py
import os
import json
from typing import Dict, Any, List, Optional, Union

from .env_config import (
    FFMPEG_BIN,
    FFPROBE_BIN,
    SHOWS_PATH,
    resolve_asset,
    load_brand_config
)
from .subtitle_engine import SubtitleEngine, TextQualityAssurance
from .video_compositor import VideoCompositor
from .audio_boundary_auditor import AudioBoundaryAuditor
from .qa_auditor import VideoEvaluator, PostRenderAuditor
from .visual_inspector import VisualInspector
from .visual_patcher import VisualPatcher
from .distributor import Distributor


class VideoEditor:
    """
    Fachada Principal del Motor de Edición de Video (Video Studio Engine).
    Proporciona una interfaz unificada y determinista para todas las operaciones audiovisuales:
    - Subtitulado viral Hormozi y estilos modernos.
    - Corte y ensamble de clips con auto-alineación acústica de silencios.
    - Transformación y re-encuadre de relaciones de aspecto (9:16 vertical, 1:1, etc.).
    - Normalización de audio broadcast (-14 LUFS).
    - Inspección técnica, hojas de contacto visuales y generación de pasaportes QA.
    - Generación de placas gráficas de impacto (Motion Title Cards).
    - Pipeline integral de Reels con soporte multi-marca y control de calidad de 5 etapas.
    """

    def __init__(self, brand: str = "generic"):
        self.brand_config = load_brand_config(brand)

    # 1. SUBTITULADO
    @classmethod
    def subtitle(
        cls,
        video_path: str,
        transcript: Union[str, Dict, List],
        out_path: str,
        style: str = "hormozi",
        font_name: str = "Arial Black",
        font_size: int = 58,
        active_color: str = "&H0000FFFF&",
        y_pos: int = 1450,
        use_gpu: bool = True
    ) -> str:
        """
        Subtitula cualquier video a partir de Whisper JSON, SRT, VTT o lista de palabras.
        """
        words = SubtitleEngine.load_words_from_transcript(transcript)
        if not words:
            raise ValueError(f"No se pudieron extraer palabras válidas de la transcripción: {transcript}")

        base_dir = os.path.dirname(os.path.abspath(out_path))
        ass_path = os.path.join(base_dir, "temp_subtitles.ass")
        try:
            SubtitleEngine.generate_ass(
                words=words,
                out_path=ass_path,
                font_name=font_name,
                font_size=font_size,
                active_color=active_color,
                y_pos=y_pos,
                style_preset=style
            )
            return VideoCompositor.burn_subtitles(
                video_path=video_path,
                ass_path=ass_path,
                out_path=out_path,
                use_gpu=use_gpu
            )
        finally:
            if os.path.exists(ass_path):
                os.remove(ass_path)

    # 2. CORTE Y ALINEACIÓN ACÚSTICA
    @classmethod
    def cut(
        cls,
        video_path: str,
        start_sec: float,
        end_sec: float,
        out_path: str,
        auto_align_silence: bool = False,
        copy_codecs: bool = False,
        use_gpu: bool = True
    ) -> str:
        """
        Corta un video con opción de auto-calibración acústica para evitar palabras truncadas.
        """
        st = float(start_sec)
        en = float(end_sec)
        if auto_align_silence:
            cal_res = AudioBoundaryAuditor.validate_boundary_gating(video_path, st, en, auto_fix=True)
            if not cal_res.get("passed"):
                st = cal_res.get("suggested_start", st)
                en = cal_res.get("suggested_end", en)
                print(f"  [Auto-Align] Timestamps ajustados acústicamente: {st:.2f}s -> {en:.2f}s")

        return VideoCompositor.cut_video(
            video_path=video_path,
            start_sec=st,
            end_sec=en,
            out_path=out_path,
            copy_codecs=copy_codecs,
            use_gpu=use_gpu
        )

    # 3. CONCATENACIÓN
    @classmethod
    def concat(
        cls,
        video_paths: List[str],
        out_path: str,
        use_gpu: bool = False
    ) -> str:
        return VideoCompositor.concat_videos(video_paths, out_path, use_gpu=use_gpu)

    # 4. RE-ENCUADRE DE FORMATO
    @classmethod
    def reframe(
        cls,
        video_path: str,
        out_path: str,
        target_aspect: str = "9:16",
        mode: str = "blur_bg",
        use_gpu: bool = True
    ) -> str:
        return VideoCompositor.reframe_video(
            video_path=video_path,
            out_path=out_path,
            target_aspect=target_aspect,
            mode=mode,
            use_gpu=use_gpu
        )

    # 5. MASTERIZACIÓN DE AUDIO
    @classmethod
    def master_audio(
        cls,
        video_path: str,
        out_path: str,
        target_lufs: float = -14.0
    ) -> str:
        return VideoCompositor.master_audio(video_path, out_path, target_lufs=target_lufs)

    # 6. INSPECCIÓN TÉCNICA Y QA
    @classmethod
    def inspect(cls, video_path: str) -> Dict[str, Any]:
        """Auditoría completa técnica de video y audio."""
        return PostRenderAuditor.audit_reel(video_path)

    @classmethod
    def inspect_visual(cls, video_path: str, out_dir: str = None) -> Dict[str, Any]:
        """Inspección de fotogramas clave, métricas de luminancia y hoja de contacto 3x2."""
        return VisualInspector.inspect_video(video_path, output_dir=out_dir)

    # 7. PARCHES Y PLACAS GRÁFICAS
    @classmethod
    def create_title_card(
        cls,
        headline_text: str,
        category_tag: str = "ALERTA INFORMATIVA",
        out_path: str = "scratch/headline_card.png"
    ) -> str:
        return VisualPatcher.generate_headline_card(
            headline_text=headline_text,
            category_tag=category_tag,
            output_path=out_path
        )
