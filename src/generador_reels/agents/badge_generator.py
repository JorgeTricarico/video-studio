import os
from PIL import Image, ImageDraw, ImageFont

def draw_instagram_icon(draw, x, y, size):
    """
    Dibuja el ícono vectorial oficial de Instagram:
    Cámara redondeada con lente central y flash, con el gradiente característico.
    """
    # Fondo con esquinas redondeadas
    r = int(size * 0.28)
    
    # Simular gradiente Instagram (de naranja a rosa/fucsia a púrpura)
    # Como Pillow no hace gradiente radial directo fácilmente, creamos un canvas con gradiente
    grad = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(grad)
    
    for i in range(size):
        ratio = i / float(size)
        # De naranja (254, 180, 70) a fucsia (214, 41, 118) a violeta (150, 47, 191)
        if ratio < 0.5:
            sub = ratio / 0.5
            r_c = int(254 * (1 - sub) + 214 * sub)
            g_c = int(180 * (1 - sub) + 41 * sub)
            b_c = int(70 * (1 - sub) + 118 * sub)
        else:
            sub = (ratio - 0.5) / 0.5
            r_c = int(214 * (1 - sub) + 150 * sub)
            g_c = int(41 * (1 - sub) + 47 * sub)
            b_c = int(118 * (1 - sub) + 191 * sub)
        gdraw.line([(0, i), (size, i)], fill=(r_c, g_c, b_c, 255))
        
    # Máscara redondeada
    mask = Image.new("L", (size, size), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.rounded_rectangle([(0, 0), (size - 1, size - 1)], radius=r, fill=255)
    
    grad.putalpha(mask)
    
    # Dibujar contorno de cámara blanca adentro
    cdraw = ImageDraw.Draw(grad)
    margin = int(size * 0.20)
    line_w = max(2, int(size * 0.08))
    
    # Cuadrado redondeado blanco
    cdraw.rounded_rectangle(
        [(margin, margin), (size - margin, size - margin)],
        radius=int(size * 0.16),
        outline=(255, 255, 255, 255),
        width=line_w
    )
    # Círculo del lente
    center = size // 2
    lens_r = int(size * 0.18)
    cdraw.ellipse(
        [(center - lens_r, center - lens_r), (center + lens_r, center + lens_r)],
        outline=(255, 255, 255, 255),
        width=line_w
    )
    # Punto de flash
    flash_x = int(size * 0.70)
    flash_y = int(size * 0.30)
    flash_r = max(2, int(size * 0.04))
    cdraw.ellipse(
        [(flash_x - flash_r, flash_y - flash_r), (flash_x + flash_r, flash_y + flash_r)],
        fill=(255, 255, 255, 255)
    )
    
    return grad

def generate_soygarrahan_badge(output_path: str = "soygarrahan_badge.png", scale: int = 2) -> str:
    """
    Genera un logo/badge de alta resolución ultra visible y profesional
    con el logo oficial de Instagram y la identidad de @soygarrahan.ok.
    """
    # Dimensiones más grandes y llamativas
    width = 540 * scale
    height = 100 * scale
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Fondo cápsula estilo tarjeta moderna
    bg_color = (10, 14, 22, 235)  # Fondo oscuro elegante con 92% opacidad
    border_color = (255, 255, 255, 80) # Borde sutil traslúcido
    
    draw.rounded_rectangle(
        [(2, 2), (width - 3, height - 3)],
        radius=int(height * 0.48),
        fill=bg_color,
        outline=border_color,
        width=2 * scale
    )

    # Pegar el ícono oficial de Instagram a la izquierda
    icon_size = 64 * scale
    icon_x = 18 * scale
    icon_y = (height - icon_size) // 2
    ig_icon = draw_instagram_icon(draw, icon_x, icon_y, icon_size)
    img.paste(ig_icon, (icon_x, icon_y), ig_icon)

    # Fuentes del sistema
    font_bold_path = "C:/Windows/Fonts/arialbd.ttf"
    font_title_size = 32 * scale
    font_sub_size = 22 * scale

    try:
        font_title = ImageFont.truetype(font_bold_path, font_title_size)
        font_sub = ImageFont.truetype(font_bold_path, font_sub_size)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    # Texto a dos líneas para máxima legibilidad y marca
    text_x = icon_x + icon_size + 18 * scale
    
    # Línea 1: "SOY GARRAHAN" en blanco puro
    draw.text((text_x, 14 * scale), "SOY GARRAHAN", font=font_title, fill=(255, 255, 255, 255))
    
    # Línea 2: "@soygarrahan.ok" en cian brillante institucional
    draw.text((text_x, 52 * scale), "@soygarrahan.ok", font=font_sub, fill=(0, 229, 255, 255))

    # Guardar en tamaño final (downsample con antialiasing para máxima nitidez)
    final_w = width // scale
    final_h = height // scale
    img_final = img.resize((final_w, final_h), Image.Resampling.LANCZOS)
    img_final.save(output_path, "PNG")
    print(f"Badge generado en {output_path} ({final_w}x{final_h})")
    return output_path

if __name__ == "__main__":
    generate_soygarrahan_badge("test_badge.png")
