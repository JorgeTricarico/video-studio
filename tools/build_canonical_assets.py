import os
from PIL import Image, ImageDraw, ImageFilter, ImageOps
import numpy as np

# Source raw photo from WhatsApp
RAW_PHOTO_PATH = "C:/Users/admin/Downloads/WhatsApp Image 2026-10-27 at 21.17.56.jpeg"
raw_im = Image.open(RAW_PHOTO_PATH).convert("RGB")
w_raw, h_raw = raw_im.size # 1600, 1204

W_16_9, H_16_9 = 1920, 1080

# We want the complete child drawing visible without ANY zoom or cropping:
# - Full dog ears at top
# - Full dog tail at left
# - Full white puppy at right
# - Full "FIRULE ISA" magnetic letters at bottom

# Target board dimensions inside 1920x1080:
# Leave 110px at top for title pill and 40px at bottom
board_h = 920
board_w = int(board_h * (w_raw / h_raw)) # 920 * 1600 / 1204 = 1222 px
scaled_board = raw_im.resize((board_w, board_h), Image.Resampling.LANCZOS)

# Create 16:9 canvas
# Background: Warm, soft classroom/playroom ambient with subtle gaussian blur of the room
canvas = raw_im.resize((W_16_9, H_16_9), Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(40))
canvas_arr = np.array(canvas).astype(float) * 0.75 + np.array([245, 240, 230]) * 0.25
canvas = Image.fromarray(canvas_arr.astype(np.uint8))

bx = (W_16_9 - board_w) // 2
by = 115

draw = ImageDraw.Draw(canvas)

# Realistic drop shadow behind whiteboard
for i in range(20, 0, -2):
    alpha = int(4 * (20 - i))
    draw.rounded_rectangle(
        [bx - i, by - i + 8, bx + board_w + i, by + board_h + i + 8],
        radius=18,
        outline=None,
        fill=(30, 20, 15, alpha)
    )

# Clean, rounded aluminum/whiteboard frame
frame_pad = 8
draw.rounded_rectangle(
    [bx - frame_pad, by - frame_pad, bx + board_w + frame_pad, by + board_h + frame_pad],
    radius=16,
    fill=(220, 224, 230),
    outline=(160, 168, 178),
    width=3
)

# Inner bevel
draw.rounded_rectangle(
    [bx - 2, by - 2, bx + board_w + 2, by + board_h + 2],
    radius=10,
    outline=(255, 255, 255),
    width=2
)

# Paste the complete, uncropped photo inside the frame
canvas.paste(scaled_board, (bx, by))

# Save canonical framed 16:9 image
out_16x9 = "assets/firule/00_dibujo_original_isai.jpg"
canvas.save(out_16x9, quality=95)
print(f"[OK] Saved canonical 16:9 uncropped whiteboard to {out_16x9}")

# Also save a dedicated 4:3 high-res version for the printable flyer
out_4x3 = "assets/firule/00_dibujo_original_4x3.jpg"
raw_im.save(out_4x3, quality=95)
print(f"[OK] Saved canonical 4:3 raw whiteboard to {out_4x3}")
