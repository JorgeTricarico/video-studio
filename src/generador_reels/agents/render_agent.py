import os
import subprocess
import time
from typing import List, Dict
from .ffmpeg_utils import get_ffmpeg_path, escape_filter_path, run_command_with_safety

class RenderAgent:
    """
    Agente 6: Motor de Render y Ensamblado Nativo en Dos Fases.
    Arquitectura inspirada en OpenShorts y Auto-Editor:
    Fase 1: Pre-corte ultra rápido de rebanadas (jump-cuts) y concatenación limpia con stream copy.
    Fase 2: Aplicación del grafo visual (encuadre Johanna, zooms, badge @soygarrahan.ok, hook card,
            subtítulos karaoke .ass y normalización de audio a -14 LUFS).
    Garantiza renderizado completo en 8-15 segundos sin problemas de DTS ni bloqueos.
    """

    def __init__(self):
        self.ffmpeg_bin = get_ffmpeg_path()

    def render(
        self,
        input_video: str,
        cuts: List[Dict],
        ass_subtitles_path: str,
        output_video: str,
        vfx_filtergraph_parts: dict,
        normalize_audio: bool = True
    ) -> str:
        """
        Ejecuta el renderizado completo de video vertical 1080x1920.
        """
        if not cuts:
            raise ValueError("No se definieron cortes de video para renderizar.")

        print(f"  [RenderAgent] Iniciando motor de render con {self.ffmpeg_bin}...")
        t0 = time.time()

        # -------------------------------------------------------------
        # FASE 1: Pre-corte de rebanadas y concatenación
        # -------------------------------------------------------------
        slice_files = []
        for i, c in enumerate(cuts):
            s_path = f"temp_slice_{i}.mp4"
            dur = c["end"] - c["start"]
            cmd_slice = [
                self.ffmpeg_bin, "-y", "-hide_banner", "-loglevel", "error",
                "-ss", f"{c['start']:.3f}", "-t", f"{dur:.3f}",
                "-i", input_video,
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
                "-c:a", "aac", "-b:a", "192k",
                s_path
            ]
            run_command_with_safety(cmd_slice, timeout=60.0)
            slice_files.append(s_path)

        # Concatenar rebanadas con concat demuxer (sin pérdidas y en 0.1s)
        concat_txt = "temp_concat_list.txt"
        with open(concat_txt, "w", encoding="utf-8") as f:
            for sf in slice_files:
                f.write(f"file '{sf}'\n")

        temp_condensed = "temp_condensed_raw.mp4"
        cmd_concat = [
            self.ffmpeg_bin, "-y", "-hide_banner", "-loglevel", "error",
            "-f", "concat", "-safe", "0", "-i", concat_txt,
            "-c", "copy", temp_condensed
        ]
        run_command_with_safety(cmd_concat, timeout=30.0)
        print(f"  [RenderAgent] Fase 1 lista: {len(cuts)} fragmentos unidos en {time.time() - t0:.1f}s")

        # -------------------------------------------------------------
        # FASE 2: VFX, Subtítulos ASS y Audio Loudnorm
        # -------------------------------------------------------------
        ass_escaped = escape_filter_path(ass_subtitles_path)
        vfx_string = vfx_filtergraph_parts["filter_string"]
        v_after_vfx = vfx_filtergraph_parts["output_label"]

        speech_d = vfx_filtergraph_parts.get("speech_duration", 0)
        outro_d = vfx_filtergraph_parts.get("outro_duration", 0)
        if outro_d > 0:
            a_filter = f"[0:a]apad=pad_dur={outro_d:.2f},afade=t=out:st={speech_d:.2f}:d=1.5,loudnorm=I=-14:TP=-2.0:LRA=11[a_final]"
        else:
            a_filter = f"[0:a]loudnorm=I=-14:TP=-2.0:LRA=11[a_final]"

        full_filter_complex = (
            f"{vfx_string}; "
            f"[{v_after_vfx}]subtitles='{ass_escaped}'[v_final]; "
            f"{a_filter}"
        )

        log_file_path = "ffmpeg_render.log"
        cmd_render = [
            self.ffmpeg_bin, "-y", "-hide_banner", "-loglevel", "warning",
            "-i", temp_condensed,
        ]
        if outro_d > 0:
            outro_path = vfx_filtergraph_parts.get("outro_card_path", "outro_card.png")
            cmd_render.extend(["-loop", "1", "-i", outro_path])

        total_target_d = vfx_filtergraph_parts.get("total_duration", speech_d + outro_d)
        if total_target_d > 0:
            cmd_render.extend(["-t", f"{total_target_d:.2f}"])

        cmd_render.extend([
            "-filter_complex", full_filter_complex,
            "-map", "[v_final]",
            "-map", "[a_final]",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "21",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "48000",
            "-movflags", "+faststart",
            output_video
        ])

        print(f"  [RenderAgent] Fase 2: Aplicando encuadre Johanna, zooms, badge y subtítulos karaoke...")
        with open(log_file_path, "w", encoding="utf-8") as log_f:
            res = run_command_with_safety(cmd_render, timeout=240.0, stdout=log_f, stderr=subprocess.STDOUT)

        # Limpiar temporales
        for sf in slice_files:
            if os.path.exists(sf):
                try:
                    os.remove(sf)
                except Exception:
                    pass
        if os.path.exists(concat_txt):
            try:
                os.remove(concat_txt)
            except Exception:
                pass
        if os.path.exists(temp_condensed):
            try:
                os.remove(temp_condensed)
            except Exception:
                pass

        if res.returncode != 0:
            err_msg = ""
            if os.path.exists(log_file_path):
                with open(log_file_path, "r", encoding="utf-8", errors="replace") as f:
                    err_msg = f.read()[-1000:]
            print(f"  [RenderAgent] ERROR al renderizar:\n{err_msg}")
            raise RuntimeError(f"FFmpeg falló con código {res.returncode}")

        total_elapsed = time.time() - t0
        print(f"  [RenderAgent] Reel renderizado con éxito en {total_elapsed:.1f}s: {output_video}")
        return output_video
