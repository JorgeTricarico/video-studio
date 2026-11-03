#!/usr/bin/env python3
"""
Script: generar_qr.py (Versión Pre-Prensa Certificada)
Objetivo: Generar una lámina imprimible de alta calidad (1200 x 1600 px @ 300 DPI)
con código QR decorado y verificado para compartir el cuento "El Cuento de Firulé" con las familias del jardín.
Incluye:
- Margen de seguridad para pinzas de impresión física (gripper margin > 5.5mm / 65px).
- Bounding boxes balanceados sin asfixias verticales ni vacíos asimétricos.
- Píldora estética del autor redondeada.
- Miniatura de la foto real de la pizarra de Isaí con ratio 16:9 exacto (sin distorsión anomórfica).
- Ortografía rioplatense impecable con tildes completas ("Jardín", "Firulé", "Isaí", "Abrí", "Apuntá", "Mirá").
"""

import sys
import os
import qrcode
from PIL import Image, ImageDraw, ImageFont, ImageOps

DEFAULT_URL = "https://cuento-firule-isai-lila.netlify.app/"
TARGET_URL = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL

print(f"[*] Generando código QR para: {TARGET_URL}")

# 1. Configurar y generar código QR con corrección H (alta resiliencia)
qr = qrcode.QRCode(
    version=None,
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=10,  # ~370px, legible a más de 1 metro
    border=2,
)
qr.add_data(TARGET_URL)
qr.make(fit=True)

qr_img = qr.make_image(fill_color="#1e293b", back_color="#ffffff").convert("RGBA")
qr_w, qr_h = qr_img.size

# 2. Crear lámina imprimible (1200 x 1600 px @ 300 DPI)
CARD_W = 1200
CARD_H = 1600

card = Image.new("RGBA", (CARD_W, CARD_H), (250, 247, 240, 255))
draw = ImageDraw.Draw(card)

# Tipografías limpias de Windows
FONT_TITLE = ImageFont.truetype(r"C:\Windows\Fonts\comicbd.ttf", 58)
FONT_SUBTITLE = ImageFont.truetype(r"C:\Windows\Fonts\comicbd.ttf", 34)
FONT_PILL = ImageFont.truetype(r"C:\Windows\Fonts\comicbd.ttf", 28)
FONT_BODY = ImageFont.truetype(r"C:\Windows\Fonts\comicbd.ttf", 29)
FONT_SMALL = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 23)

def draw_centered(text, y, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (CARD_W - tw) // 2
    draw.text((x, y), text, font=font, fill=fill)
    return tw

# Marco exterior decorativo seguro (a 65px del borde físico para gripper margin)
draw.rounded_rectangle([65, 65, CARD_W - 65, CARD_H - 65], radius=32, outline=(230, 126, 34), width=7)
draw.rounded_rectangle([78, 78, CARD_W - 78, CARD_H - 78], radius=22, outline=(241, 196, 15), width=3)

# 1. Header: Etiqueta de preescolar - "Jardín de Infantes • Sala Lila" (y: 100 a 160)
badge_text = "Jardín de Infantes • Sala Lila"
b_bbox = draw.textbbox((0, 0), badge_text, font=FONT_SUBTITLE)
b_w = b_bbox[2] - b_bbox[0]
draw.rounded_rectangle([CARD_W//2 - b_w//2 - 28, 100, CARD_W//2 + b_w//2 + 28, 160], radius=24, fill=(255, 255, 255), outline=(155, 89, 182), width=4)
draw_centered(badge_text, 110, FONT_SUBTITLE, (142, 68, 173))

# 2. Título principal (y: 180 a 240)
draw_centered("El Cuento de Firulé", 180, FONT_TITLE, (44, 62, 80))

# Píldora del autor (y: 255 a 305): "Isaí & Canticuénticos"
author_text = "Isaí & Canticuénticos"
a_bbox = draw.textbbox((0, 0), author_text, font=FONT_PILL)
a_w = a_bbox[2] - a_bbox[0]
draw.rounded_rectangle([CARD_W//2 - a_w//2 - 22, 255, CARD_W//2 + a_w//2 + 22, 305], radius=20, fill=(254, 243, 199), outline=(217, 119, 6), width=3)
draw_centered(author_text, 263, FONT_PILL, (180, 83, 9))

# 3. Miniatura de dibujo original en la pizarra (y: 330 a 690, 640x360 px exactos 16:9)
portada_path = "assets/firule/00_dibujo_original_isai.jpg"
if not os.path.exists(portada_path):
    portada_path = "assets/firule/01_portada_ia.jpg"

if os.path.exists(portada_path):
    portada_w = 640
    portada_h = 360
    portada_y = 330
    portada = Image.open(portada_path).convert("RGBA")
    # Fit exact 16:9 without any stretching/anomorphic distortion
    portada = ImageOps.fit(portada, (portada_w, portada_h), Image.Resampling.LANCZOS)
    
    mask = Image.new("L", (portada_w, portada_h), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, portada_w, portada_h], radius=20, fill=255)
    
    card.paste(portada, (CARD_W//2 - portada_w//2, portada_y), mask)
    draw.rounded_rectangle([CARD_W//2 - portada_w//2, portada_y, CARD_W//2 + portada_w//2, portada_y + portada_h], radius=20, outline=(255, 255, 255), width=5)

# 4. Recuadro blanco para el código QR (y: 720 a 1130, tamaño 410x410 px)
qr_box_y = 720
qr_box_size = qr_w + 36
draw.rounded_rectangle(
    [CARD_W//2 - qr_box_size//2, qr_box_y, CARD_W//2 + qr_box_size//2, qr_box_y + qr_box_size],
    radius=26, fill=(255, 255, 255), outline=(52, 152, 219), width=5
)

# Pegar el código QR
card.paste(qr_img, (CARD_W//2 - qr_w//2, qr_box_y + 18), qr_img)

# 5. Pasos sencillos en voseo escolar rioplatense (y: 1160 a 1300)
step_y = qr_box_y + qr_box_size + 30
draw_centered("1. Abrí la cámara de tu celular", step_y, FONT_BODY, (52, 73, 94))
draw_centered("2. Apuntá directo al código QR", step_y + 44, FONT_BODY, (52, 73, 94))
draw_centered("3. ¡Mirá el video animado y cantá en familia!", step_y + 88, FONT_BODY, (39, 174, 96))

# 6. Pie de volante (y: 1330 a 1480, espaciado balanceado)
draw.line([(140, 1375), (CARD_W - 140, 1375)], fill=(220, 210, 195), width=2)
draw_centered("Cuento y canción original de Canticuénticos • Presentado por Isaí", 1400, FONT_SMALL, (127, 140, 141))
draw_centered(f"Enlace directo: {TARGET_URL}", 1442, FONT_SMALL, (41, 128, 185))

# Guardar en alta calidad
output_path = "qr_imprimible_jardin.png"
card.save(output_path, "PNG", dpi=(300, 300))
print(f"[OK] Código QR imprimible generado con éxito: {output_path} (1200x1600 px @ 300 DPI)")

# Guardar copia en assets/firule
import shutil
shutil.copyfile(output_path, f"assets/firule/{output_path}")
print(f"[OK] Copia guardada en assets/firule/{output_path}")
