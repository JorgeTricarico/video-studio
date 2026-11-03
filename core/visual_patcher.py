import os
import sys
import subprocess
from typing import Dict, Any, List
from PIL import Image, ImageDraw, ImageFont
from .env_config import FFMPEG_BIN as FFMPEG, FFPROBE_BIN as FFPROBE, BADGE_PNG as BADGE_PATH

FONT_BLACK = r"C:\Windows\Fonts\ariblk.ttf"
FONT_BOLD = r"C:\Windows\Fonts\arialbd.ttf"

class VisualPatcher:
    """
    Módulo de Cobertura de Baches Visuales (Visual Gap Patcher).
    Permite generar placas gráficas de impacto (Motion Title Cards) o procesar
    imágenes temáticas de apoyo para cubrir tramos donde la señal de video original
    presenta artefactos o imágenes defectuosas, manteniendo el audio original y sus subtítulos.
    """

    @classmethod
    def generate_headline_card(
        cls,
        headline_text: str,
        category_tag: str = "ALERTA INFORMATIVA",
        output_path: str = "scratch/headline_card.png",
        highlight_words: List[str] = None
    ) -> str:
        """
        Genera una placa gráfica vertical 1080x1920 con estética institucional Garrahan,
        diseñada para sostener la atención visual durante un bache de video.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        img = Image.new("RGBA", (1080, 1920), (7, 11, 18, 255))
        draw = ImageDraw.Draw(img)

        # 1. Fondo degradado vertical profundo
        base = Image.new("RGBA", (1080, 1920))
        draw_base = ImageDraw.Draw(base)
        for y in range(1920):
            factor = y / 1920.0
            r = int(10 + (28 - 10) * factor)
            g = int(12 + (16 - 12) * factor)
            b = int(22 + (40 - 22) * factor)
            draw_base.line([(0, y), (1080, y)], fill=(r, g, b, 255))

        # 2. Resplandor radial suave de acento violeta con capa alfa
        glow_layer = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
        draw_glow = ImageDraw.Draw(glow_layer)
        glow_center = (540, 720)
        glow_radius = 500
        for rad in range(glow_radius, 50, -15):
            intensity = int(45 * (1.0 - (rad / glow_radius) ** 2))
            draw_glow.ellipse(
                [glow_center[0] - rad, glow_center[1] - rad, glow_center[0] + rad, glow_center[1] + rad],
                fill=(121, 66, 133, intensity)
            )

        # Fusionar fondo y resplandor
        img = Image.alpha_composite(base, glow_layer)
        draw = ImageDraw.Draw(img)

        # 3. Superponer Badge institucional de Soy Garrahan (y=35)
        if os.path.exists(BADGE_PATH):
            badge_img = Image.open(BADGE_PATH).convert("RGBA")
            # Escalar badge si es necesario
            b_w, b_h = badge_img.size
            pos_x = (1080 - b_w) // 2
            img.paste(badge_img, (pos_x, 35), badge_img)

        # 4. Píldora de categoría / alerta (y=230)
        if category_tag:
            try:
                font_tag = ImageFont.truetype(FONT_BOLD, 28)
            except Exception:
                font_tag = ImageFont.load_default()

            clean_tag = category_tag.upper().strip()
            bbox = font_tag.getbbox(clean_tag)
            tag_w = bbox[2] - bbox[0]
            tag_h = bbox[3] - bbox[1]
            pad_x, pad_y = 20, 10
            rect_x0 = (1080 - (tag_w + pad_x * 2)) // 2
            rect_y0 = 230
            rect_x1 = rect_x0 + tag_w + pad_x * 2
            rect_y1 = rect_y0 + tag_h + pad_y * 2

            # Fondo rojo de alerta con bordes redondeados
            draw.rounded_rectangle([rect_x0, rect_y0, rect_x1, rect_y1], radius=8, fill=(204, 0, 0, 235))
            draw.text((rect_x0 + pad_x, rect_y0 + pad_y - 2), clean_tag, font=font_tag, fill=(255, 255, 255, 255))

        # 5. Titular de impacto (y=500 a y=950)
        try:
            font_title = ImageFont.truetype(FONT_BLACK, 64)
        except Exception:
            font_title = ImageFont.load_default()

        # Word wrapping para 1080px de ancho con margen de 100px a cada lado
        words = headline_text.upper().split()
        lines = []
        cur_line = []
        max_line_w = 880

        for w in words:
            test_line = " ".join(cur_line + [w])
            bbox = font_title.getbbox(test_line)
            w_px = bbox[2] - bbox[0]
            if w_px <= max_line_w:
                cur_line.append(w)
            else:
                if cur_line:
                    lines.append(" ".join(cur_line))
                cur_line = [w]
        if cur_line:
            lines.append(" ".join(cur_line))

        # Dibujar líneas de texto centradas
        line_height = 82
        total_text_h = len(lines) * line_height
        start_y = 560 - (total_text_h // 2)

        highlight_set = set([h.upper() for h in (highlight_words or [])])

        for l_idx, line_str in enumerate(lines):
            line_y = start_y + l_idx * line_height
            line_bbox = font_title.getbbox(line_str)
            line_w = line_bbox[2] - line_bbox[0]
            line_x = (1080 - line_w) // 2

            # Sombra de texto profunda
            draw.text((line_x + 4, line_y + 4), line_str, font=font_title, fill=(0, 0, 0, 210))

            # Verificar si la línea contiene palabras destacadas
            is_highlight = any(hw in line_str for hw in highlight_set)
            text_color = (255, 225, 0, 255) if is_highlight else (255, 255, 255, 255) # Amarillo neón o blanco
            draw.text((line_x, line_y), line_str, font=font_title, fill=text_color)

        # 6. Viñeta inferior oscura para asegurar legibilidad total de los subtítulos Hormozi
        vig_layer = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
        draw_vig = ImageDraw.Draw(vig_layer)
        for y in range(1250, 1920):
            alpha = int(220 * ((y - 1250) / (1920 - 1250)))
            draw_vig.line([(0, y), (1080, y)], fill=(0, 0, 0, alpha))

        img = Image.alpha_composite(img, vig_layer)

        # Convertir a RGB y guardar
        img.convert("RGB").save(output_path, "PNG")
        return os.path.abspath(output_path)

    @classmethod
    def create_motion_patch_clip(
        cls,
        image_path: str,
        duration: float,
        output_clip_path: str,
        fps: int = 60
    ) -> str:
        """
        Convierte una imagen estática 1080x1920 en un clip de video MP4 a 60fps
        con un efecto suave de aproximación cinemática (Ken Burns / Slow Push-In: 1.0 a 1.05x).
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_clip_path)), exist_ok=True)
        total_frames = int(duration * fps)

        # Filtro de zoompan lento y fluido hacia el centro
        # s=1080x1920, zoom gradual de 1.0 a 1.05 en total_frames
        vf = (
            f"scale=1188:2112:flags=lanczos,"
            f"zoompan=z='min(zoom+0.05/{total_frames},1.05)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={total_frames}:s=1080x1920:fps={fps},"
            f"format=yuv420p"
        )

        cmd = [
            FFMPEG, "-y", "-loop", "1", "-i", image_path,
            "-vf", vf,
            "-t", f"{duration:.3f}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-pix_fmt", "yuv420p", "-r", str(fps), "-an",
            output_clip_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return os.path.abspath(output_clip_path)

    @classmethod
    def patch_video_gap(
        cls,
        base_video_path: str,
        gap_start: float,
        gap_end: float,
        patch_clip_path: str,
        output_patched_video: str
    ) -> str:
        """
        Reemplaza quirúrgicamente el segmento visual de un video entre gap_start y gap_end
        utilizando el patch_clip_path, conservando el audio original íntegro y sincronizado.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_patched_video)), exist_ok=True)
        gap_dur = gap_end - gap_start

        # Filtergraph para intercalar el clip visual sobre la base
        filter_complex = (
            f"[0:v][1:v]overlay=0:0:enable='between(t,{gap_start:.3f},{gap_end:.3f})'[v_out]"
        )

        cmd = [
            FFMPEG, "-y",
            "-i", base_video_path,
            "-itsoffset", f"{gap_start:.3f}", "-i", patch_clip_path,
            "-filter_complex", filter_complex,
            "-map", "[v_out]", "-map", "0:a?",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-c:a", "copy",
            output_patched_video
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return os.path.abspath(output_patched_video)


if __name__ == "__main__":
    test_out = "scratch/test_headline_card.png"
    VisualPatcher.generate_headline_card(
        headline_text="El 21 de Octubre vence la Ley de Emergencia Pediátrica",
        category_tag="ALERTA • VENCE LEY DE EMERGENCIA",
        output_path=test_out,
        highlight_words=["21 DE OCTUBRE", "EMERGENCIA"]
    )
    print(f"[OK] Placa de prueba generada en: {test_out}")
