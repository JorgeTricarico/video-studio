import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from typing import Optional

def find_logo_path(custom_path: Optional[str] = None) -> str:
    """Busca el archivo del logo oficial en assets o rutas del sistema."""
    candidates = [
        custom_path,
        "assets/logos/soygarrahan_transparent.png",
        "../assets/logos/soygarrahan_transparent.png",
        "../../assets/logos/soygarrahan_transparent.png",
        "assets/logos/soygarrahan_official.png",
        "../assets/logos/soygarrahan_official.png",
        "../../assets/logos/soygarrahan_official.png",
        r"C:\Users\admin\Desktop\Reels_Instagram_Edicion\assets\logos\soygarrahan_transparent.png",
        r"C:\Users\admin\Desktop\Reels_Instagram_Edicion\assets\logos\soygarrahan_official.png",
        r"C:\Users\admin\Downloads\Logo Soy garrham.png"
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return custom_path or "assets/logos/soygarrahan_transparent.png"

def get_cropped_official_logo(logo_path: Optional[str] = None):
    """
    Corta los márgenes transparentes del logo oficial Soy Garrahan.
    """
    path = find_logo_path(logo_path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Logo no encontrado en: {path}")
    img = Image.open(path).convert("RGBA")
    bbox = img.getbbox() or (111, 437, 1655, 814)
    return img.crop(bbox)

def draw_instagram_icon_raw(size: int) -> Image.Image:
    """Genera el ícono de Instagram en vector de Pillow."""
    ig_icon = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ig_draw = ImageDraw.Draw(ig_icon)
    for i in range(size):
        sub = i / float(size)
        if sub < 0.5:
            s = sub / 0.5
            r = int(254 * (1 - s) + 214 * s)
            g = int(180 * (1 - s) + 41 * s)
            b = int(70 * (1 - s) + 118 * s)
        else:
            s = (sub - 0.5) / 0.5
            r = int(214 * (1 - s) + 150 * s)
            g = int(41 * (1 - s) + 47 * s)
            b = int(118 * (1 - s) + 191 * s)
        ig_draw.line([(0, i), (size, i)], fill=(r, g, b, 255))
        
    mask = Image.new("L", (size, size), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.rounded_rectangle([(0, 0), (size - 1, size - 1)], radius=int(size * 0.26), fill=255)
    ig_icon.putalpha(mask)
    
    icdraw = ImageDraw.Draw(ig_icon)
    margin = int(size * 0.18)
    line_w = max(2, int(size * 0.05))
    icdraw.rounded_rectangle(
        [(margin, margin), (size - margin, size - margin)],
        radius=int(size * 0.16), outline=(255, 255, 255, 255), width=line_w
    )
    center = size // 2
    lens_r = int(size * 0.16)
    icdraw.ellipse(
        [(center - lens_r, center - lens_r), (center + lens_r, center + lens_r)],
        outline=(255, 255, 255, 255), width=line_w
    )
    flash_x = int(size * 0.70)
    flash_y = int(size * 0.28)
    flash_r = max(2, int(size * 0.035))
    icdraw.ellipse(
        [(flash_x - flash_r, flash_y - flash_r), (flash_x + flash_r, flash_y + flash_r)],
        fill=(255, 255, 255, 255)
    )
    return ig_icon

def create_top_watermark_badge(
    output_path: str = "soygarrahan_badge.png",
    handle: str = "@soygarrahan.ok",
    logo_file: Optional[str] = None
) -> str:
    """
    Crea el badge superior (watermark) con fondo violeta de marca, sin recuadros ni bordes
    molestos, usando el logo transparente (letras y corazón sin recuadro).
    Tamaño optimizado y más grande para impacto visual inmediato en Reels.
    """
    official_logo = get_cropped_official_logo(logo_file)
    
    target_h = 94
    aspect = official_logo.width / official_logo.height
    target_w = int(target_h * aspect)
    logo_scaled = official_logo.resize((target_w, target_h), Image.Resampling.LANCZOS)
    
    pad_x = 30
    pad_y = 16
    
    font_bold = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 38)
    dummy_img = Image.new("RGBA", (1, 1))
    dummy_draw = ImageDraw.Draw(dummy_img)
    bb_text = dummy_draw.textbbox((0, 0), handle, font=font_bold)
    text_w = bb_text[2] - bb_text[0]
    
    ig_size = 54
    badge_w = target_w + pad_x + 18 + 18 + ig_size + 14 + text_w + pad_x
    badge_h = target_h + pad_y * 2
    
    canvas = Image.new("RGBA", (badge_w, badge_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    
    # Fondo violeta de marca, SIN línea de borde
    draw.rounded_rectangle(
        [(0, 0), (badge_w, badge_h)],
        radius=badge_h // 2,
        fill=(135, 88, 142, 235),
        outline=None,
        width=0
    )
    
    # Pegar logo transparente (letras y corazón)
    canvas.paste(logo_scaled, (pad_x, pad_y), logo_scaled)
    
    # Divisor sutil blanco
    div_x = pad_x + target_w + 18
    draw.line([(div_x, pad_y + 10), (div_x, badge_h - pad_y - 10)], fill=(255, 255, 255, 120), width=2)
    
    # Ícono Instagram
    ig_x = div_x + 18
    ig_y = (badge_h - ig_size) // 2
    ig_icon = draw_instagram_icon_raw(ig_size)
    canvas.paste(ig_icon, (ig_x, ig_y), ig_icon)
    
    # Handle texto
    text_x = ig_x + ig_size + 14
    text_y = (badge_h - 38) // 2 - 2
    draw.text((text_x, text_y), handle, font=font_bold, fill=(255, 255, 255, 255))
    
    os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
    canvas.save(output_path, "PNG")
    return output_path

def create_outro_card(
    output_path: str = "outro_card.png",
    slogan_main: str = "EL GARRAHAN SALVA VIDAS",
    slogan_sub: str = "Familias en defensa de la salud pública",
    handle: str = "@soygarrahan.ok",
    cta_text: str = "SEGUINOS Y COMPARTÍ ESTE TESTIMONIO",
    logo_file: Optional[str] = None
) -> str:
    """
    Crea la pantalla final (Outro CTA) para el cierre del Reel (1080x1920).
    Diseño 100% full-bleed violeta de marca, logo extra grande y píldora simétrica.
    """
    official_logo = get_cropped_official_logo(logo_file)
    
    width, height = 1080, 1920
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    
    # --- Fondo: degradé vertical violeta cálido e institucional ---
    for y in range(height):
        t = y / height
        r = int(152 * (1 - t) + 95 * t)
        g = int(105 * (1 - t) + 55 * t)
        b = int(158 * (1 - t) + 102 * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
    
    # --- Logo oficial transparente (letras blancas + corazón) AÚN MÁS GRANDE ---
    logo_target_w = 980
    logo_aspect = official_logo.width / official_logo.height
    logo_target_h = int(logo_target_w / logo_aspect)
    logo_large = official_logo.resize((logo_target_w, logo_target_h), Image.Resampling.LANCZOS)
    
    logo_x = (width - logo_target_w) // 2
    logo_y = 480
    
    # Sombra suave para darle volumen al logo sobre el fondo violeta
    shadow_mask = logo_large.getchannel("A").filter(ImageFilter.GaussianBlur(radius=7))
    shadow_layer = Image.new("RGBA", logo_large.size, (40, 18, 44, 190))
    shadow_layer.putalpha(shadow_mask)
    canvas.paste(shadow_layer, (logo_x + 3, logo_y + 7), shadow_layer)
    canvas.paste(logo_large, (logo_x, logo_y), logo_large)
    
    # --- Línea divisoria minimalista (blanco translúcido) ---
    div_y = logo_y + logo_target_h + 75
    draw.line([(140, div_y), (width - 140, div_y)], fill=(255, 255, 255, 180), width=2)
    
    # --- Tipografías más grandes ---
    font_slogan_main = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 58)
    font_slogan_sub = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 40)
    font_user_lg = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 60)
    font_cta = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 42)
    
    # Slogan principal
    bb1 = draw.textbbox((0, 0), slogan_main, font=font_slogan_main)
    w1 = bb1[2] - bb1[0]
    draw.text(((width - w1) // 2, div_y + 45), slogan_main, font=font_slogan_main, fill=(255, 255, 255, 255))
    
    # Sub-slogan
    bb2 = draw.textbbox((0, 0), slogan_sub, font=font_slogan_sub)
    w2 = bb2[2] - bb2[0]
    draw.text(((width - w2) // 2, div_y + 125), slogan_sub, font=font_slogan_sub, fill=(240, 245, 245, 235))
    
    # --- Píldora Instagram con relleno SIMÉTRICO y ajustado al texto ---
    bb_handle = draw.textbbox((0, 0), handle, font=font_user_lg)
    h_text_w = bb_handle[2] - bb_handle[0]
    h_text_h = bb_handle[3] - bb_handle[1]
    
    ig_size_lg = 80
    gap_ig_text = 24
    pad_pill_x = 44  # Padding idéntico a izquierda y derecha
    
    pill_w = pad_pill_x + ig_size_lg + gap_ig_text + h_text_w + pad_pill_x
    pill_h = 140
    pill_x = (width - pill_w) // 2
    pill_y = div_y + 235
    
    # Fondo de la píldora: violeta más oscuro simétrico exacto
    draw.rounded_rectangle(
        [(pill_x, pill_y), (pill_x + pill_w, pill_y + pill_h)],
        radius=pill_h // 2,
        fill=(72, 38, 78, 240),
        outline=None,
        width=0
    )
    
    ig_lg_x = pill_x + pad_pill_x
    ig_lg_y = pill_y + (pill_h - ig_size_lg) // 2
    ig_lg = draw_instagram_icon_raw(ig_size_lg)
    canvas.paste(ig_lg, (ig_lg_x, ig_lg_y), ig_lg)
    
    text_x = ig_lg_x + ig_size_lg + gap_ig_text
    text_y = pill_y + (pill_h - h_text_h) // 2 - 4
    draw.text((text_x, text_y), handle, font=font_user_lg, fill=(255, 255, 255, 255))
    
    # --- CTA inferior en color menta del corazón del logo ---
    bb_cta = draw.textbbox((0, 0), cta_text, font=font_cta)
    w_cta = bb_cta[2] - bb_cta[0]
    draw.text(
        ((width - w_cta) // 2, pill_y + pill_h + 65),
        cta_text, font=font_cta, fill=(83, 216, 165, 255)
    )
    
    os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
    canvas.save(output_path, "PNG")
    return output_path

