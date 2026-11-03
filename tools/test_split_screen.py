from PIL import Image, ImageDraw, ImageFont, ImageOps
import numpy as np
import os

WIDTH, HEIGHT = 1920, 1080
FONT_M = ImageFont.truetype(r"C:\Windows\Fonts\comicbd.ttf", 34)

# Create split canvas
split_img = Image.new("RGB", (WIDTH, HEIGHT), (24, 20, 18)) # warm dark studio backdrop
split_draw = ImageDraw.Draw(split_img)

half_w = 950

# Dividers and backgrounds
# Left side background panel (subtle warm parchment)
split_draw.rounded_rectangle([15, 15, half_w - 10, HEIGHT - 275], radius=24, fill=(40, 34, 30), outline=(90, 75, 60), width=2)
# Right side background panel
split_draw.rounded_rectangle([half_w + 10, 15, WIDTH - 15, HEIGHT - 275], radius=24, fill=(40, 34, 30), outline=(90, 75, 60), width=2)

# Top Badges
# Left pill: El Dibujo Real de Isaí
split_draw.rounded_rectangle([180, 35, 780, 105], radius=20, fill=(30, 20, 15), outline=(255, 220, 120), width=3)
split_draw.text((220, 48), "El Dibujo Real de Isai", font=FONT_M, fill=(255, 225, 90))

# Right pill: Versión Cuento
split_draw.rounded_rectangle([1140, 35, 1720, 105], radius=20, fill=(20, 30, 40), outline=(140, 230, 255), width=3)
split_draw.text((1220, 48), "Version Cuento", font=FONT_M, fill=(140, 235, 255))

# Center dividing line
split_draw.line([(half_w, 15), (half_w, HEIGHT - 275)], fill=(200, 180, 140), width=4)

# Fit raw drawing on Left side (100% visible, no zoom, no crop)
im_real = Image.open("assets/firule/00_dibujo_original_4x3.jpg").convert("RGB")
w_r, h_r = im_real.size
# Target area inside left panel: x: 30..930 (width 900), y: 125..790 (height 665)
avail_w = 890
avail_h = 660
scale_l = min(avail_w / w_r, avail_h / h_r)
fit_w_l = int(w_r * scale_l)
fit_h_l = int(h_r * scale_l)
scaled_real = im_real.resize((fit_w_l, fit_h_l), Image.Resampling.LANCZOS)

pos_x_l = 20 + (avail_w - fit_w_l) // 2
pos_y_l = 125 + (avail_h - fit_h_l) // 2

# Card frame behind real drawing
split_draw.rounded_rectangle([pos_x_l - 4, pos_y_l - 4, pos_x_l + fit_w_l + 4, pos_y_l + fit_h_l + 4], radius=12, fill=(230, 232, 235), outline=(180, 185, 190), width=2)
split_img.paste(scaled_real, (pos_x_l, pos_y_l))

# Fit illustration on Right side
im_cuento = Image.open("assets/firule/01_portada_ia.jpg").convert("RGB")
w_c, h_c = im_cuento.size
scale_r = min(avail_w / w_c, avail_h / h_c)
fit_w_r = int(w_c * scale_r)
fit_h_r = int(h_c * scale_r)
scaled_cuento = im_cuento.resize((fit_w_r, fit_h_r), Image.Resampling.LANCZOS)

pos_x_r = half_w + 15 + (avail_w - fit_w_r) // 2
pos_y_r = 125 + (avail_h - fit_h_r) // 2

split_draw.rounded_rectangle([pos_x_r - 4, pos_y_r - 4, pos_x_r + fit_w_r + 4, pos_y_r + fit_h_r + 4], radius=12, fill=(250, 245, 235), outline=(220, 200, 170), width=2)
split_img.paste(scaled_cuento, (pos_x_r, pos_y_r))

# Bottom banner for subtitles simulation
split_draw.rectangle([0, HEIGHT - 260, WIDTH, HEIGHT], fill=(0, 0, 0, 220))
FONT_XXL = ImageFont.truetype(r"C:\Windows\Fonts\comicbd.ttf", 96)
bbox = FONT_XXL.getbbox("¡ FIRULE !")
tw = bbox[2] - bbox[0]
split_draw.text(((WIDTH - tw)//2, HEIGHT - 180), "¡ FIRULE !", font=FONT_XXL, fill=(255, 160, 20), stroke_width=8, stroke_fill=(120, 30, 0))

split_img.save("test_split_final_clean.jpg", quality=95)
print("[OK] Saved test_split_final_clean.jpg")
