import os
from .badge_generator import generate_soygarrahan_badge
from .ffmpeg_utils import escape_filter_path

class VFXAgent:
    """
    Agente 4: Director de Arte, Encuadre y Efectos Visuales (VFX).
    Reencuadra verticalmente a Johanna (eliminando barras negras y conductores),
    aplica alternancia de punch-in zooms, hook card inicial, badge @soygarrahan.ok
    y barra de progreso animada de retención.
    """

    def __init__(self, crop_mode: str = "johanna", enable_zooms: bool = True, enable_branding: bool = True):
        self.crop_mode = crop_mode
        self.enable_zooms = enable_zooms
        self.enable_branding = enable_branding

    def get_filtergraph_parts(
        self,
        duration: float,
        hook_text: str = "",
        badge_png_path: str = "soygarrahan_badge.png",
        input_is_1080x1920: bool = True
    ) -> dict:
        """
        Construye la cadena de filtros FFmpeg para el ensamblado visual.
        Retorna los filtros intermedios y el nombre de la etiqueta de salida de video.
        """
        filters = []

        # 1. Encuadre centrado en la oradora (Johanna o Antonela)
        if self.crop_mode == "antonela":
            crop_filter = "crop=206:220:6:65"
            scale_fg = "scale=1080:1153"
            overlay_fg = "overlay=0:380"
        elif input_is_1080x1920:
            crop_filter = "crop=420:608:655:656"
            scale_fg = "scale=1080:1563"
            overlay_fg = "overlay=0:120"
        else:
            crop_filter = "crop=500:720:775:0"
            scale_fg = "scale=1080:1563"
            overlay_fg = "overlay=0:120"

        # Crear base vertical 1080x1920 con fondo desenfocado y oradora al centro protagonista
        filters.append(
            f"[0:v]{crop_filter},split=2[j_bg][j_fg]; "
            f"[j_bg]scale=270:480,boxblur=8:1,scale=1080:1920[bg]; "
            f"[j_fg]{scale_fg}[fg]; "
            f"[bg][fg]{overlay_fg}[v_framed]"
        )
        current_v = "v_framed"

        # 2. Punch-in Zooms dinámicos (1.0x -> 1.14x cada 4 segundos)
        if self.enable_zooms:
            filters.append(
                f"[{current_v}]split=2[v_norm][v_to_zoom]; "
                f"[v_to_zoom]scale=1.14*1080:-1,crop=1080:1920:(in_w-out_w)/2:(in_h-out_h)/2[v_zoomed]; "
                f"[v_norm][v_zoomed]overlay=0:0:enable='between(mod(t,8),4,8)'[v_punch]"
            )
            current_v = "v_punch"

        # 3. Hook Title Card en los primeros 3 segundos (si se especifica texto)
        if hook_text:
            repl = {"Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U", "Ñ": "N",
                    "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n"}
            clean_hook = hook_text
            for k, v in repl.items():
                clean_hook = clean_hook.replace(k, v)
            clean_hook = clean_hook.replace("'", "").replace(":", "\\:").upper()

            filters.append(
                f"[{current_v}]drawtext=text='{clean_hook}':"
                f"fontfile='C\\:/Windows/Fonts/arialbd.ttf':fontsize=52:"
                f"fontcolor=0x111111:box=1:boxcolor=0x00E5FF@0.95:boxborderw=20:"
                f"x=(w-text_w)/2:y=340:"
                f"enable='between(t,0,3)':"
                f"alpha='if(lt(t,0.2),t/0.2,if(gt(t,2.8),(3-t)/0.2,1))'[v_hook]"
            )
            current_v = "v_hook"

        # 4. Badge superior oficial Soy Garrahan (watermark continuo)
        if self.enable_branding:
            if not os.path.exists(badge_png_path):
                from .brand_manager import create_top_watermark_badge
                create_top_watermark_badge(badge_png_path)
            
            badge_escaped = escape_filter_path(badge_png_path)
            filters.append(
                f"movie='{badge_escaped}'[badge_raw]; "
                f"[{current_v}][badge_raw]overlay=(W-w)/2:130:eof_action=repeat[v_brand]"
            )
            current_v = "v_brand"

        # 5. Outro Card final (Logo oficial en grande + Slogan + Instagram + CTA)
        outro_card_path = "outro_card.png"
        outro_duration = 3.2
        total_d = duration + outro_duration
        if not os.path.exists(outro_card_path):
            from .brand_manager import create_outro_card
            create_outro_card(outro_card_path)

        outro_escaped = escape_filter_path(outro_card_path)
        filters.append(
            f"[{current_v}]tpad=stop_duration={outro_duration:.2f}:stop_mode=clone[v_pad]; "
            f"[1:v]format=rgba,fade=t=in:st={duration:.2f}:d=0.5:alpha=1[outro_raw]; "
            f"[v_pad][outro_raw]overlay=0:0:shortest=1:enable='gte(t,{duration:.2f})'[v_outro]"
        )
        current_v = "v_outro"

        return {
            "filter_string": "; ".join(filters),
            "output_label": current_v,
            "speech_duration": duration,
            "outro_duration": outro_duration,
            "outro_card_path": outro_card_path,
            "total_duration": total_d
        }
