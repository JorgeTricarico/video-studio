# filepath: core/video_compositor.py
import os
import time
import tempfile
import subprocess
from typing import Dict, Any, List, Optional
from .env_config import FFMPEG_BIN, FFPROBE_BIN, BADGE_PNG, OUTRO_PNG


class VideoCompositor:
    """
    Compositor Audiovisual Universal FFmpeg para Edición de Video y Reels.
    Soporta:
    - Composición vertical 9:16 con split-screen, recorte de hablante y fondo desenfocado.
    - Quemado directo de subtítulos ASS dinámicos en cualquier video.
    - Corte preciso de clips (stream copy o re-encodeo exacto).
    - Concatenación de tomas/partes con normalización.
    - Re-encuadre de formatos (16:9 -> 9:16, 1:1, etc.) con fondo desenfocado o recorte.
    - Normalización de sonoridad profesional EBU R128 (-14.0 LUFS).
    - Soporte acelerado por hardware NVIDIA NVENC con fallback transparente a libx264.
    """
    _nvenc_available = None

    @classmethod
    def has_nvenc(cls) -> bool:
        if cls._nvenc_available is None:
            try:
                cmd = [
                    FFMPEG_BIN, "-hide_banner", "-f", "lavfi",
                    "-i", "color=black:s=64x64:d=0.1",
                    "-c:v", "h264_nvenc", "-f", "null", "-"
                ]
                res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                cls._nvenc_available = (res.returncode == 0)
            except Exception:
                cls._nvenc_available = False
        return cls._nvenc_available

    @staticmethod
    def _escape_ffmpeg_path(path_str: str) -> str:
        return os.path.abspath(path_str).replace("\\", "/").replace(":", "\\:")

    @classmethod
    def get_video_info(cls, video_path: str) -> Dict[str, Any]:
        """Obtiene metadatos técnicos del archivo de video vía FFprobe."""
        try:
            cmd = [
                FFPROBE_BIN, "-v", "error",
                "-show_entries", "stream=index,codec_name,codec_type,width,height,sample_aspect_ratio,r_frame_rate,duration",
                "-show_entries", "format=duration,size,bit_rate",
                "-of", "json",
                video_path
            ]
            res = subprocess.check_output(cmd, text=True)
            import json
            data = json.loads(res)
            v_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
            a_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), {})
            fmt = data.get("format", {})
            return {
                "duration": float(fmt.get("duration", v_stream.get("duration", 0.0))),
                "width": int(v_stream.get("width", 0)),
                "height": int(v_stream.get("height", 0)),
                "v_codec": v_stream.get("codec_name", "unknown"),
                "a_codec": a_stream.get("codec_name", "none"),
                "fps": v_stream.get("r_frame_rate", "30/1"),
                "sar": v_stream.get("sample_aspect_ratio", "1:1"),
                "size_bytes": int(fmt.get("size", 0))
            }
        except Exception as e:
            return {"error": str(e), "duration": 0.0, "width": 0, "height": 0}

    @classmethod
    def build_filter_complex(
        cls,
        show_profile: Dict[str, Any],
        ass_path: Optional[str],
        speech_duration: float,
        live_text_file: Optional[str],
        outro_duration: float = 3.2,
        outro_input_index: int = 1
    ) -> str:
        """
        Construye la cadena de filtros para composición 9:16 con soporte modular
        de branding, insignias, píldoras informativas y outro cards opcionales.
        """
        crop_bg = show_profile.get(
            "crop_background",
            "crop=960:1080:960:0,scale=270:480,boxblur=20:2,scale=1080:1920,setsar=1:1"
        )
        crop_fg = show_profile.get(
            "crop_speaker",
            "crop=800:770:1060:26,scale=1080:1040,setsar=1:1"
        )
        overlay_y = show_profile.get("overlay_y", 260)
        live_y = show_profile.get("live_pill_y", 1320)
        live_color = show_profile.get("live_pill_color", "0xCC0000@0.92")
        audio_filter = show_profile.get("audio_filter", "loudnorm=I=-14:TP=-2.0:LRA=11")

        is_fullscreen_fg = ("1080:1920" in crop_fg and overlay_y == 0)

        # 1. Composición de base de video
        if is_fullscreen_fg:
            filter_parts = [f"[0:v]{crop_fg}[v_comp]; "]
        else:
            filter_parts = [
                f"[0:v]{crop_bg},eq=brightness=-0.14:contrast=1.1[bg]; ",
                f"[0:v]{crop_fg}[fg]; ",
                f"[bg][fg]overlay=0:{overlay_y}[v_comp]; "
            ]

        current_v = "v_comp"

        # 2. Insignia / Badge de Marca (Opcional)
        badge_path = show_profile.get("badge_path")
        if badge_path is None and show_profile.get("enable_badge", True):
            badge_path = BADGE_PNG

        if badge_path and os.path.exists(badge_path) and show_profile.get("enable_badge", True):
            badge_escaped = cls._escape_ffmpeg_path(badge_path)
            filter_parts.append(
                f"movie='{badge_escaped}'[badge_raw]; "
                f"[{current_v}][badge_raw]overlay=(W-w)/2:35:eof_action=repeat[v_brand]; "
            )
            current_v = "v_brand"

        # 3. Píldora de Texto en Vivo / Titular (Opcional)
        enable_live = show_profile.get("enable_live", True)
        if enable_live and live_text_file and os.path.exists(live_text_file):
            live_file_escaped = cls._escape_ffmpeg_path(live_text_file)
            filter_parts.append(
                f"[{current_v}]drawtext=textfile='{live_file_escaped}':fontfile='C\\:/Windows/Fonts/arialbd.ttf':fontsize=28:"
                f"fontcolor=white:box=1:boxcolor={live_color}:boxborderw=10:x=(w-text_w)/2:y={live_y}[v_live]; "
            )
            current_v = "v_live"

        # 4. Subtítulos dinámicos ASS
        if ass_path and os.path.exists(ass_path):
            ass_escaped = cls._escape_ffmpeg_path(ass_path)
            filter_parts.append(f"[{current_v}]subtitles='{ass_escaped}'[v_tagged]; ")
            current_v = "v_tagged"

        # 5. Outro card y cierre sonoro (Opcional)
        outro_path = show_profile.get("outro_path")
        if outro_path is None and show_profile.get("enable_outro", True):
            outro_path = OUTRO_PNG

        enable_outro = show_profile.get("enable_outro", True) and outro_duration > 0 and outro_path and os.path.exists(outro_path)

        if enable_outro:
            filter_parts.append(
                f"[{current_v}]tpad=stop_duration={outro_duration:.2f}:stop_mode=clone[v_pad]; "
                f"[{outro_input_index}:v]trim=duration={outro_duration:.2f},format=rgba,fade=t=in:st=0:d=0.5:alpha=1,"
                f"setpts=PTS+{speech_duration:.2f}/TB[outro_raw]; "
                f"[v_pad][outro_raw]overlay=0:0:eof_action=pass:enable='gte(t,{speech_duration:.2f})'[v_final]; "
                f"[0:a]apad=pad_dur={outro_duration:.2f},afade=t=out:st={speech_duration:.2f}:d=1.5,{audio_filter}[a_final]"
            )
        else:
            filter_parts.append(
                f"[{current_v}]null[v_final]; "
                f"[0:a]{audio_filter}[a_final]"
            )

        return "".join(filter_parts)

    @classmethod
    def render_preview_frame(
        cls,
        raw_slice_mp4: str,
        ass_path: Optional[str],
        show_profile: Dict[str, Any],
        live_text: str,
        out_jpg: str,
        timestamp: float = 1.5
    ) -> str:
        """
        Renderiza un único fotograma compuesto en <1.5s para validación previa (Pre-Flight Visual Check).
        """
        os.makedirs(os.path.dirname(os.path.abspath(out_jpg)), exist_ok=True)
        live_txt_path = None
        if live_text:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as tf:
                tf.write(live_text.upper().strip())
                live_txt_path = tf.name

        try:
            filter_complex = cls.build_filter_complex(
                show_profile=show_profile,
                ass_path=ass_path,
                speech_duration=30.0,
                live_text_file=live_txt_path,
                outro_duration=0.0
            )
            # Para preview sólo extraemos el nodo visual final antes del outro
            cmd = [
                FFMPEG_BIN, "-y", "-hide_banner", "-loglevel", "error",
                "-ss", f"{timestamp:.2f}", "-i", raw_slice_mp4,
                "-filter_complex", filter_complex,
                "-map", "[v_final]", "-frames:v", "1", "-q:v", "2", out_jpg
            ]
            subprocess.run(cmd, check=True)
        finally:
            if live_txt_path and os.path.exists(live_txt_path):
                os.remove(live_txt_path)
        return os.path.abspath(out_jpg)

    @classmethod
    def render_reel(
        cls,
        raw_slice_mp4: str,
        ass_path: Optional[str],
        show_profile: Dict[str, Any],
        live_text: str,
        out_path: str,
        use_gpu: bool = False
    ) -> str:
        """
        Renderiza un reel completo con o sin subtítulos, branding modular y normalización de audio.
        """
        res = subprocess.check_output([
            FFPROBE_BIN, "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", raw_slice_mp4
        ], text=True)
        speech_duration = float(res.strip())

        # Configuración de outro
        enable_outro = show_profile.get("enable_outro", True)
        outro_path = show_profile.get("outro_path")
        if outro_path is None and enable_outro:
            outro_path = OUTRO_PNG

        outro_duration = float(show_profile.get("outro_duration", 3.2)) if (enable_outro and outro_path and os.path.exists(outro_path)) else 0.0
        total_duration = speech_duration + outro_duration

        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

        live_txt_path = None
        if live_text and show_profile.get("enable_live", True):
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as tf:
                tf.write(live_text.upper().strip())
                live_txt_path = tf.name

        try:
            inputs = ["-i", raw_slice_mp4]
            outro_input_idx = 1
            if outro_duration > 0 and outro_path and os.path.exists(outro_path):
                inputs.extend(["-loop", "1", "-t", f"{outro_duration + 1.0:.2f}", "-i", outro_path])

            filter_complex = cls.build_filter_complex(
                show_profile=show_profile,
                ass_path=ass_path,
                speech_duration=speech_duration,
                live_text_file=live_txt_path,
                outro_duration=outro_duration,
                outro_input_index=outro_input_idx
            )

            if use_gpu and cls.has_nvenc():
                vcodec_args = ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "19"]
            else:
                vcodec_args = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18"]

            cmd_render = [
                FFMPEG_BIN, "-y", "-hide_banner", "-loglevel", "warning",
                *inputs,
                "-filter_complex", filter_complex,
                "-map", "[v_final]", "-map", "[a_final]",
                *vcodec_args,
                "-pix_fmt", "yuv420p", "-r", "60",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                "-t", f"{total_duration:.2f}",
                "-movflags", "+faststart",
                out_path
            ]

            t0 = time.time()
            subprocess.run(cmd_render, check=True)
            elapsed = time.time() - t0
            print(f"  [OK] Renderizado completado en {elapsed:.1f}s: {out_path} ({total_duration:.1f}s)")
        finally:
            if live_txt_path and os.path.exists(live_txt_path):
                os.remove(live_txt_path)

        return out_path

    # =========================================================================
    # CAPACIDADES GENERALES DE EDICIÓN DE VIDEO
    # =========================================================================

    @classmethod
    def burn_subtitles(
        cls,
        video_path: str,
        ass_path: str,
        out_path: str,
        use_gpu: bool = True
    ) -> str:
        """
        Incrusta (quema) subtítulos ASS sobre cualquier video existente sin modificar
        su resolución, relación de aspecto ni encuadre.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video no encontrado: {video_path}")
        if not os.path.exists(ass_path):
            raise FileNotFoundError(f"Archivo de subtítulos no encontrado: {ass_path}")

        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        ass_escaped = cls._escape_ffmpeg_path(ass_path)
        vf = f"subtitles='{ass_escaped}'"

        if use_gpu and cls.has_nvenc():
            vcodec_args = ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "19"]
        else:
            vcodec_args = ["-c:v", "libx264", "-preset", "medium", "-crf", "18"]

        cmd = [
            FFMPEG_BIN, "-y", "-hide_banner", "-loglevel", "warning",
            "-i", video_path,
            "-vf", vf,
            *vcodec_args,
            "-c:a", "copy",
            "-movflags", "+faststart",
            out_path
        ]
        t0 = time.time()
        subprocess.run(cmd, check=True)
        print(f"  [OK] Subtítulos quemados en {time.time() - t0:.1f}s -> {out_path}")
        return os.path.abspath(out_path)

    @classmethod
    def cut_video(
        cls,
        video_path: str,
        start_sec: float,
        end_sec: float,
        out_path: str,
        copy_codecs: bool = False,
        use_gpu: bool = True
    ) -> str:
        """
        Corta un fragmento de video entre start_sec y end_sec.
        - copy_codecs=True: Copia directa de streams (-c copy), instantáneo sin pérdida.
        - copy_codecs=False: Re-encodeo exacto de fotogramas clave.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video no encontrado: {video_path}")

        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        dur = max(0.1, end_sec - start_sec)

        if copy_codecs:
            codec_args = ["-c", "copy"]
        else:
            if use_gpu and cls.has_nvenc():
                codec_args = ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "18", "-c:a", "aac", "-b:a", "192k"]
            else:
                codec_args = ["-c:v", "libx264", "-preset", "fast", "-crf", "18", "-c:a", "aac", "-b:a", "192k"]

        cmd = [
            FFMPEG_BIN, "-y", "-hide_banner", "-loglevel", "error",
            "-ss", f"{start_sec:.3f}",
            "-t", f"{dur:.3f}",
            "-i", video_path,
            *codec_args,
            "-movflags", "+faststart",
            out_path
        ]
        t0 = time.time()
        subprocess.run(cmd, check=True)
        print(f"  [OK] Corte completado en {time.time() - t0:.1f}s: [{start_sec:.2f}s - {end_sec:.2f}s] -> {out_path}")
        return os.path.abspath(out_path)

    @classmethod
    def concat_videos(
        cls,
        video_paths: List[str],
        out_path: str,
        use_gpu: bool = False
    ) -> str:
        """
        Concatena una lista de videos en secuencia usando el filtro de concatenación de FFmpeg.
        """
        if not video_paths:
            raise ValueError("La lista de videos está vacía.")

        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        inputs = []
        for p in video_paths:
            if not os.path.exists(p):
                raise FileNotFoundError(f"Clip no encontrado: {p}")
            inputs.extend(["-i", p])

        n = len(video_paths)
        filter_inputs = "".join(f"[{i}:v][{i}:a]" for i in range(n))
        fc = f"{filter_inputs}concat=n={n}:v=1:a=1[outv][outa]"

        if use_gpu and cls.has_nvenc():
            vcodec_args = ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "18"]
        else:
            vcodec_args = ["-c:v", "libx264", "-preset", "fast", "-crf", "18"]

        cmd = [
            FFMPEG_BIN, "-y", "-hide_banner", "-loglevel", "warning",
            *inputs,
            "-filter_complex", fc,
            "-map", "[outv]", "-map", "[outa]",
            *vcodec_args,
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            out_path
        ]
        t0 = time.time()
        subprocess.run(cmd, check=True)
        print(f"  [OK] Concatenación de {n} clips completada en {time.time() - t0:.1f}s -> {out_path}")
        return os.path.abspath(out_path)

    @classmethod
    def reframe_video(
        cls,
        video_path: str,
        out_path: str,
        target_aspect: str = "9:16",
        mode: str = "blur_bg",
        use_gpu: bool = True
    ) -> str:
        """
        Convierte la relación de aspecto de un video (ej. 16:9 a 9:16 vertical, 1:1 cuadrado, etc.).
        Modos:
        - 'blur_bg': Centra el video sobre una versión ampliada y desenfocada de fondo (estilo TikTok/Reels).
        - 'crop': Recorte central directo para llenar la pantalla.
        - 'fit': Ajuste proporcional con barras negras de relleno.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video no encontrado: {video_path}")

        aspect_dims = {
            "9:16": (1080, 1920),
            "1:1": (1080, 1080),
            "16:9": (1920, 1080),
            "4:5": (1080, 1350)
        }
        tw, th = aspect_dims.get(target_aspect, (1080, 1920))
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

        if mode == "blur_bg":
            fc = (
                f"[0:v]scale={tw}:{th}:force_original_aspect_ratio=increase,crop={tw}:{th},boxblur=25:2[bg]; "
                f"[0:v]scale={tw}:{th}:force_original_aspect_ratio=decrease[fg]; "
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2[outv]"
            )
        elif mode == "crop":
            fc = (
                f"[0:v]scale={tw}:{th}:force_original_aspect_ratio=increase,crop={tw}:{th}[outv]"
            )
        else: # fit con pad
            fc = (
                f"[0:v]scale={tw}:{th}:force_original_aspect_ratio=decrease,pad={tw}:{th}:(ow-iw)/2:(oh-ih)/2:black[outv]"
            )

        if use_gpu and cls.has_nvenc():
            vcodec_args = ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "19"]
        else:
            vcodec_args = ["-c:v", "libx264", "-preset", "fast", "-crf", "18"]

        cmd = [
            FFMPEG_BIN, "-y", "-hide_banner", "-loglevel", "warning",
            "-i", video_path,
            "-filter_complex", fc,
            "-map", "[outv]", "-map", "0:a?",
            *vcodec_args,
            "-c:a", "copy",
            "-movflags", "+faststart",
            out_path
        ]
        t0 = time.time()
        subprocess.run(cmd, check=True)
        print(f"  [OK] Re-encuadre a {target_aspect} ({mode}) completado en {time.time() - t0:.1f}s -> {out_path}")
        return os.path.abspath(out_path)

    @classmethod
    def master_audio(
        cls,
        video_path: str,
        out_path: str,
        target_lufs: float = -14.0
    ) -> str:
        """
        Aplica normalización de sonoridad profesional EBU R128 (loudnorm) al audio de un video
        manteniendo la pista de video intacta sin recodificar.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video no encontrado: {video_path}")

        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        af = f"loudnorm=I={target_lufs:.1f}:TP=-2.0:LRA=11"

        cmd = [
            FFMPEG_BIN, "-y", "-hide_banner", "-loglevel", "warning",
            "-i", video_path,
            "-c:v", "copy",
            "-af", af,
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-movflags", "+faststart",
            out_path
        ]
        t0 = time.time()
        subprocess.run(cmd, check=True)
        print(f"  [OK] Audio masterizado a {target_lufs} LUFS en {time.time() - t0:.1f}s -> {out_path}")
        return os.path.abspath(out_path)
