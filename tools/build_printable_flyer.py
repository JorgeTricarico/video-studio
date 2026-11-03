import os
import qrcode
from PIL import Image, ImageDraw, ImageFont, ImageOps
import cv2
import numpy as np

# Dimensions: 1200 x 1600 (A4 proportion, crisp print ready)
PAGE_W = 1200
PAGE_H = 1600
TARGET_URL = "https://cuento-firule-isai-lila.netlify.app/"

# 1. Generate QR Code
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=16,
    border=2
)
qr.add_data(TARGET_URL)
qr.make(fit=True)
qr_img = qr.make_image(fill_color="#1a1a1a", back_color="#ffffff").convert("RGB")

# Save qr_code_solo.png (clean 532x532 px)
qr_solo = qr_img.resize((532, 532), Image.Resampling.LANCZOS)
qr_solo.save("qr_code_solo.png", quality=95)
print(f"[OK] Saved qr_code_solo.png ({qr_solo.size})")

# 2. Build Printable A4 Flyer
canvas = Image.new("RGB", (PAGE_W, PAGE_H), (253, 250, 243)) # warm ivory background
draw = ImageDraw.Draw(canvas)

# Fonts
def get_font(size, bold=False):
    names = ["calibrib.ttf" if bold else "calibri.ttf", "arialbd.ttf" if bold else "arial.ttf", "segoeuib.ttf" if bold else "segoeui.ttf"]
    for n in names:
        p = os.path.join(r"C:\Windows\Fonts", n)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

FONT_TITLE = get_font(52, bold=True)
FONT_SUB = get_font(28, bold=True)
FONT_BADGE = get_font(26, bold=True)
FONT_BODY = get_font(26, bold=True)
FONT_FOOTER = get_font(20, bold=False)
FONT_LINK = get_font(22, bold=True)

# Outer double borders with safe print margins (60px edge margin)
margin = 55
draw.rounded_rectangle(
    [margin, margin, PAGE_W - margin, PAGE_H - margin],
    radius=28,
    outline=(230, 126, 34),
    width=5
)
draw.rounded_rectangle(
    [margin + 10, margin + 10, PAGE_W - margin - 10, PAGE_H - margin - 10],
    radius=20,
    outline=(243, 156, 18),
    width=2
)

# Header: Sala Lila Pill Badge
badge_text = "Jardín de Infantes  •  Sala Lila"
bw = 440
bh = 52
bx = (PAGE_W - bw) // 2
by = 85
draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=26, fill=(245, 235, 255), outline=(142, 68, 173), width=3)
bbox = FONT_BADGE.getbbox(badge_text)
draw.text((bx + (bw - (bbox[2] - bbox[0])) // 2, by + 10), badge_text, font=FONT_BADGE, fill=(110, 40, 150))

# Title
title_text = "El Cuento de Firulé"
bbox_t = FONT_TITLE.getbbox(title_text)
draw.text(((PAGE_W - (bbox_t[2] - bbox_t[0])) // 2, 155), title_text, font=FONT_TITLE, fill=(30, 41, 59))

# Subtitle pill
sub_text = "Isaí & Canticuénticos"
sw = 320
sh = 44
sx = (PAGE_W - sw) // 2
sy = 228
draw.rounded_rectangle([sx, sy, sx + sw, sy + sh], radius=22, fill=(255, 243, 230), outline=(230, 126, 34), width=2)
bbox_s = FONT_SUB.getbbox(sub_text)
draw.text((sx + (sw - (bbox_s[2] - bbox_s[0])) // 2, sy + 6), sub_text, font=FONT_SUB, fill=(180, 80, 20))

# 3. Child's Whiteboard Drawing (100% UNCROPPED, 4:3 RATIO, FULL DETAILS VISIBLE)
# Available box: width 640, height 460
raw_photo = Image.open("assets/firule/00_dibujo_original_4x3.jpg").convert("RGB")
w_r, h_r = raw_photo.size

box_w = 640
box_h = 440
box_x = (PAGE_W - box_w) // 2
box_y = 295

# Calculate scale to fit completely inside box_w x box_h without any cropping
scale = min((box_w - 16) / w_r, (box_h - 16) / h_r)
fit_w = int(w_r * scale)
fit_h = int(h_r * scale)
scaled_photo = raw_photo.resize((fit_w, fit_h), Image.Resampling.LANCZOS)

# Outer card frame for the drawing
draw.rounded_rectangle(
    [box_x, box_y, box_x + box_w, box_y + box_h],
    radius=18,
    fill=(240, 243, 246),
    outline=(200, 208, 218),
    width=3
)

# Paste centered inside card
px = box_x + (box_w - fit_w) // 2
py = box_y + (box_h - fit_h) // 2

# Inner border around photo
draw.rounded_rectangle(
    [px - 3, py - 3, px + fit_w + 3, py + fit_h + 3],
    radius=10,
    outline=(160, 170, 180),
    width=2
)
canvas.paste(scaled_photo, (px, py))

# Tiny photo label pill
photo_lbl = "El Dibujo Real de Isaí en la Pizarra"
font_lbl = get_font(18, bold=True)
pl_bbox = font_lbl.getbbox(photo_lbl)
pl_w = (pl_bbox[2] - pl_bbox[0]) + 24
pl_h = 28
pl_x = (PAGE_W - pl_w) // 2
pl_y = box_y + box_h - 14
draw.rounded_rectangle([pl_x, pl_y, pl_x + pl_w, pl_y + pl_h], radius=14, fill=(255, 255, 255), outline=(180, 190, 200), width=2)
draw.text((pl_x + 12, pl_y + 4), photo_lbl, font=font_lbl, fill=(80, 90, 100))

# 4. QR Code Box
qr_size = 440
qr_box_x = (PAGE_W - qr_size) // 2
qr_box_y = 765

# Frame for QR
draw.rounded_rectangle(
    [qr_box_x - 14, qr_box_y - 14, qr_box_x + qr_size + 14, qr_box_y + qr_size + 14],
    radius=24,
    fill=(255, 255, 255),
    outline=(52, 152, 219),
    width=4
)
canvas.paste(qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS), (qr_box_x, qr_box_y))

# 5. Instructions
inst_y = 1255
steps = [
    ("1. Abrí la cámara de tu celular", (44, 62, 80)),
    ("2. Apuntá directo al código QR", (44, 62, 80)),
    ("3. ¡Mirá el video animado y cantá en familia!", (39, 174, 96))
]

for st_text, col in steps:
    bbox_st = FONT_BODY.getbbox(st_text)
    draw.text(((PAGE_W - (bbox_st[2] - bbox_st[0])) // 2, inst_y), st_text, font=FONT_BODY, fill=col)
    inst_y += 42

# Divider line
draw.line([(margin + 40, 1400), (PAGE_W - margin - 40, 1400)], fill=(220, 210, 195), width=2)

# Footer
f1 = "Cuento y canción original de Canticuénticos • Presentado por Isaí"
bbox_f1 = FONT_FOOTER.getbbox(f1)
draw.text(((PAGE_W - (bbox_f1[2] - bbox_f1[0])) // 2, 1430), f1, font=FONT_FOOTER, fill=(120, 110, 100))

f2 = f"Enlace directo: {TARGET_URL}"
bbox_f2 = FONT_LINK.getbbox(f2)
draw.text(((PAGE_W - (bbox_f2[2] - bbox_f2[0])) // 2, 1468), f2, font=FONT_LINK, fill=(41, 128, 185))

# Save output
out_flyer = "qr_imprimible_jardin.png"
canvas.save(out_flyer, quality=95)
print(f"[OK] Saved printable flyer -> {out_flyer}")

# Verify QR decoding with OpenCV
img_cv = cv2.imread(out_flyer)
detector = cv2.QRCodeDetector()
data, bbox_cv, _ = detector.detectAndDecode(img_cv)
if data == TARGET_URL:
    print(f"[VERIFIED] OpenCV successfully decoded QR code from flyer: {data}")
else:
    print(f"[WARN] OpenCV decoded: '{data}' vs expected '{TARGET_URL}'")
