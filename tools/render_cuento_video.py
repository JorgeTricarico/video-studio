import os
import sys
sys.path.insert(0, os.getcwd())
import subprocess
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import shutil
from core.env_config import FFMPEG_BIN, FFPROBE_BIN

WIDTH = 1920
HEIGHT = 1080
FPS = 30
TOTAL_DURATION = 115.455  # seconds (exact match to audio_final_master.mp3)
TOTAL_FRAMES = int(TOTAL_DURATION * FPS)

FONT_PATH = r"C:\Windows\Fonts\comicbd.ttf"
FONT_S = ImageFont.truetype(FONT_PATH, 36)
FONT_M = ImageFont.truetype(FONT_PATH, 48)
FONT_L = ImageFont.truetype(FONT_PATH, 70)
FONT_XL = ImageFont.truetype(FONT_PATH, 100)
FONT_XXL = ImageFont.truetype(FONT_PATH, 135)

print(f"[*] Total frames to render: {TOTAL_FRAMES} ({TOTAL_DURATION}s @ {FPS}fps)")

# Helper to load and scale illustrations to 1920x1080
def load_img(path):
    im = Image.open(path).convert("RGB")
    im = im.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    return np.array(im)

# Helper for the real whiteboard photo (4:3 aspect ratio preserved with warm blurred background)
def load_real_photo_framed(path):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    bg = im.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(radius=25))
    target_h = HEIGHT
    target_w = int(target_h * (w / h))
    fg = im.resize((target_w, target_h), Image.Resampling.LANCZOS)
    offset_x = (WIDTH - target_w) // 2
    bg.paste(fg, (offset_x, 0))
    return np.array(bg)

print("[*] Loading base illustrations...")
# Escena 1: Foto auténtica de la pizarra de Isaí con atril y letras imantadas (16:9 canvas 100% visible)
img_00 = load_img("assets/firule/00_dibujo_original_isai.jpg")
img_01 = load_img("assets/firule/01_portada_ia.jpg")
img_02 = load_img("assets/firule/02_paseo_parque.jpg")
img_02b = load_img("assets/firule/02b_tropiezo_pantufla_pasillo.jpg")
img_02c = load_img("assets/firule/02c_firule_vereda_vecinos.jpg")
img_04 = load_img("assets/firule/04_cuneta_enamorado.jpg")
img_04b = load_img("assets/firule/04b_enamorados_vereda.jpg")
img_05 = load_img("assets/firule/05_final_casa.jpg")

# Precompute Split Screen for Finale (Real photo on Left vs Cuento on Right, 100% uncropped)
print("[*] Composing split screen for comparative scene...")
split_img = Image.new("RGB", (WIDTH, HEIGHT), (24, 20, 18))
split_draw = ImageDraw.Draw(split_img)
half_w = 950

# Side panels
split_draw.rounded_rectangle([15, 15, half_w - 10, HEIGHT - 275], radius=24, fill=(40, 34, 30), outline=(90, 75, 60), width=2)
split_draw.rounded_rectangle([half_w + 10, 15, WIDTH - 15, HEIGHT - 275], radius=24, fill=(40, 34, 30), outline=(90, 75, 60), width=2)

# Top Badges
split_draw.rounded_rectangle([180, 35, 780, 105], radius=20, fill=(30, 20, 15), outline=(255, 220, 120), width=3)
split_draw.text((220, 48), "El Dibujo Real de Isai", font=FONT_M, fill=(255, 225, 90))

split_draw.rounded_rectangle([1140, 35, 1720, 105], radius=20, fill=(20, 30, 40), outline=(140, 230, 255), width=3)
split_draw.text((1220, 48), "Version Cuento", font=FONT_M, fill=(140, 235, 255))

# Center dividing line
split_draw.line([(half_w, 15), (half_w, HEIGHT - 275)], fill=(200, 180, 140), width=4)

# Real drawing on Left side (100% uncropped, 4:3 ratio)
im_real = Image.open("assets/firule/00_dibujo_original_4x3.jpg").convert("RGB")
w_r, h_r = im_real.size
avail_w = 890
avail_h = 660
scale_l = min(avail_w / w_r, avail_h / h_r)
fit_w_l = int(w_r * scale_l)
fit_h_l = int(h_r * scale_l)
scaled_real = im_real.resize((fit_w_l, fit_h_l), Image.Resampling.LANCZOS)
pos_x_l = 20 + (avail_w - fit_w_l) // 2
pos_y_l = 125 + (avail_h - fit_h_l) // 2
split_draw.rounded_rectangle([pos_x_l - 4, pos_y_l - 4, pos_x_l + fit_w_l + 4, pos_y_l + fit_h_l + 4], radius=12, fill=(230, 232, 235), outline=(180, 185, 190), width=2)
split_img.paste(scaled_real, (pos_x_l, pos_y_l))

# Cuento illustration on Right side
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

img_split = np.array(split_img)

def apply_ken_burns(img_np, zoom_factor=1.0, pan_x=0.0, pan_y=0.0):
    """Zoom and pan smoothly using cv2"""
    if zoom_factor <= 1.001 and abs(pan_x) < 0.001 and abs(pan_y) < 0.001:
        return img_np
    h, w = img_np.shape[:2]
    nw = int(w / zoom_factor)
    nh = int(h / zoom_factor)
    cx = int(w / 2 + pan_x * (w - nw) / 2)
    cy = int(h / 2 + pan_y * (h - nh) / 2)
    x1 = max(0, min(w - nw, cx - nw // 2))
    y1 = max(0, min(h - nh, cy - nh // 2))
    cropped = img_np[y1:y1+nh, x1:x1+nw]
    return cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)

# Helper to draw centered text with stroke and drop shadow
def draw_text_stroked(draw, text, y_center, font, fill_color, stroke_color=(0, 0, 0), stroke_w=6):
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (WIDTH - tw) // 2
    y = y_center - th // 2
    draw.text((x + 4, y + 4), text, font=font, fill=(0, 0, 0, 200), stroke_width=stroke_w, stroke_fill=(0, 0, 0))
    draw.text((x, y), text, font=font, fill=fill_color, stroke_width=stroke_w, stroke_fill=stroke_color)

# Setup FFmpeg output pipe
out_mp4 = "cuento_firule_isai.mp4"
ffmpeg_cmd = [
    FFMPEG_BIN, "-y",
    "-f", "rawvideo",
    "-vcodec", "rawvideo",
    "-s", f"{WIDTH}x{HEIGHT}",
    "-pix_fmt", "bgr24",
    "-r", str(FPS),
    "-i", "-",  # video from stdin
    "-i", "audio_final_master.mp3",
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-preset", "medium",
    "-crf", "19",
    "-c:a", "aac",
    "-b:a", "192k",
    "-shortest",
    out_mp4
]

print(f"[*] Starting FFmpeg process -> {out_mp4}")
proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

# Deterministic seed for confetti in finale
np.random.seed(42)
confetti_particles = [
    {
        "x": np.random.randint(50, WIDTH - 50),
        "y": np.random.randint(-400, 0),
        "speed": np.random.uniform(4, 9),
        "color": (np.random.randint(150, 255), np.random.randint(100, 255), np.random.randint(50, 255)),
        "size": np.random.randint(8, 16)
    }
    for _ in range(80)
]

for frame_idx in range(TOTAL_FRAMES):
    t = frame_idx / FPS
    
    # -------------------------------------------------------------
    # SCENE SELECTION & TRANSITIONS
    # -------------------------------------------------------------
    if t < 4.0:
        # Escena 1: El Dibujo Original de Isaí (Foto real en pizarra)
        progress = t / 4.0
        frame_rgb = apply_ken_burns(img_00, zoom_factor=1.0 + progress * 0.04)
        
    elif t < 5.5:
        # Transición Mágica: Crossfade de la pizarra real a la portada ilustrada
        progress = (t - 4.0) / 1.5
        frame_00 = apply_ken_burns(img_00, zoom_factor=1.04)
        frame_01 = apply_ken_burns(img_01, zoom_factor=1.00 + progress * 0.02)
        frame_rgb = cv2.addWeighted(frame_00, 1.0 - progress, frame_01, progress, 0)
        
    elif t < 11.5:
        # Escena 2A: Portada Ilustrada ("Esta es la historia de un perro...")
        progress = (t - 5.5) / 6.0
        frame_rgb = apply_ken_burns(img_01, zoom_factor=1.02 + progress * 0.05, pan_y=progress * 0.2)
        
    elif t < 19.5:
        # Escena 2B: María paseando a Firulé en el parque con correa
        progress = (t - 11.5) / 8.0
        frame_02 = apply_ken_burns(img_02, zoom_factor=1.0 + progress * 0.06, pan_x=progress * 0.2)
        if t < 12.5:
            cf_p = (t - 11.5) / 1.0
            frame_01_end = apply_ken_burns(img_01, zoom_factor=1.07)
            frame_rgb = cv2.addWeighted(frame_01_end, 1.0 - cf_p, frame_02, cf_p, 0)
        else:
            frame_rgb = frame_02
            
    elif t < 35.0:
        # Escena 3A: María trastabilla en el pasillo, vuela la pantufla hacia la puerta
        progress = (t - 19.5) / 15.5
        frame_02b = apply_ken_burns(img_02b, zoom_factor=1.0 + progress * 0.07, pan_x=progress * 0.2, pan_y=-progress * 0.1)
        if t < 20.5:
            wipe_p = (t - 19.5) / 1.0
            wipe_x = int(WIDTH * wipe_p)
            frame_02_end = apply_ken_burns(img_02, zoom_factor=1.06)
            frame_rgb = frame_02_end.copy()
            frame_rgb[:, :wipe_x] = frame_02b[:, :wipe_x]
            if 0 < wipe_x < WIDTH - 4:
                frame_rgb[:, wipe_x-2:wipe_x+2] = (255, 255, 255)
        else:
            frame_rgb = frame_02b
            
    elif t < 50.0:
        # Escena 3B: Firulé sale tranquilo por la puerta entreabierta a la vereda y saluda a los vecinos
        progress = (t - 35.0) / 15.0
        frame_02c = apply_ken_burns(img_02c, zoom_factor=1.0 + progress * 0.06, pan_x=-progress * 0.2)
        if t < 36.0:
            cf_p = (t - 35.0) / 1.0
            frame_02b_end = apply_ken_burns(img_02b, zoom_factor=1.07)
            frame_rgb = cv2.addWeighted(frame_02b_end, 1.0 - cf_p, frame_02c, cf_p, 0)
        else:
            frame_rgb = frame_02c
            
    elif t < 79.0:
        # Escena 4A: La camita de hojas en la cuneta y el hocico de la perrita
        progress = (t - 50.0) / 29.0
        frame_04 = apply_ken_burns(img_04, zoom_factor=1.0 + progress * 0.07, pan_x=progress * 0.2)
        if t < 51.0:
            cf_p = (t - 50.0) / 1.0
            frame_02c_end = apply_ken_burns(img_02c, zoom_factor=1.06)
            frame_rgb = cv2.addWeighted(frame_02c_end, 1.0 - cf_p, frame_04, cf_p, 0)
        else:
            frame_rgb = frame_04
            
    elif t < 86.5:
        # Escena 4B: Firulé y la perrita caminando juntos enamorados por la vereda otoñal
        progress = (t - 79.0) / 7.5
        frame_04b = apply_ken_burns(img_04b, zoom_factor=1.0 + progress * 0.06, pan_x=-progress * 0.15)
        if t < 80.0:
            cf_p = (t - 79.0) / 1.0
            frame_04_end = apply_ken_burns(img_04, zoom_factor=1.07)
            frame_rgb = cv2.addWeighted(frame_04_end, 1.0 - cf_p, frame_04b, cf_p, 0)
        else:
            frame_rgb = frame_04b
            
    elif t < 98.0:
        # Escena 4C: María lleva a los dos perritos adentro de la casa
        progress = (t - 86.5) / 11.5
        frame_05 = apply_ken_burns(img_05, zoom_factor=1.0 + progress * 0.05, pan_y=-progress * 0.1)
        if t < 87.5:
            cf_p = (t - 86.5) / 1.0
            frame_04b_end = apply_ken_burns(img_04b, zoom_factor=1.06)
            frame_rgb = cv2.addWeighted(frame_04b_end, 1.0 - cf_p, frame_05, cf_p, 0)
        else:
            frame_rgb = frame_05
            
    else:
        # Escena 5: Split Screen Comparativo (Foto Pizarra Real Isaí vs Portada Ilustrada)
        frame_rgb = img_split.copy()

    # -------------------------------------------------------------
    # DYNAMIC OVERLAYS & SUBTITLES (NO EMOJIS, CLEAN GLYPHS)
    # -------------------------------------------------------------
    frame_pil = Image.fromarray(frame_rgb)
    draw = ImageDraw.Draw(frame_pil)
    
    # Escena 1 (0.0 to 4.0s): Top Header Pill (above the whiteboard)
    if t < 4.0:
        draw.rounded_rectangle([WIDTH//2 - 420, 25, WIDTH//2 + 420, 95], radius=20, fill=(255, 255, 255, 240), outline=(230, 160, 40), width=3)
        draw.text((WIDTH//2 - 370, 38), "Dibujado y presentado por Isai", font=FONT_M, fill=(60, 40, 20))
        
    # Escena 5 (98.0s to 115.45s): Dynamic Animated Syllable Subtitles + Finale (Title Safe Area for mobile fullscreen)
    if t >= 98.0:
        # Semi-transparent dark banner on bottom to make big subtitles super legible and safe from mobile controls
        draw.rectangle([0, HEIGHT - 260, WIDTH, HEIGHT], fill=(0, 0, 0, 205))
        
        # Safe center line for big words (y_sub = HEIGHT - 145) leaving generous 75px margin from bottom edge
        Y_SUB = HEIGHT - 145

        if 98.0 <= t < 100.5:
            draw_text_stroked(draw, "Y asi termina este cuen...", Y_SUB, FONT_L, (255, 255, 255))
        elif 100.5 <= t < 101.6:
            # ¡TO! in huge yellow/red
            draw_text_stroked(draw, "¡ TO !", Y_SUB, FONT_XXL, (255, 230, 20), stroke_color=(200, 20, 0), stroke_w=10)
        elif 101.6 <= t < 103.2:
            draw_text_stroked(draw, "de un perro con mucha suer...", Y_SUB, FONT_L, (255, 255, 255))
        elif 103.2 <= t < 104.2:
            # ¡TE! in bright emerald green
            draw_text_stroked(draw, "¡ TE !", Y_SUB, FONT_XXL, (50, 255, 120), stroke_color=(0, 80, 40), stroke_w=10)
        elif 104.2 <= t < 104.9:
            draw_text_stroked(draw, "que se llama...", Y_SUB, FONT_L, (255, 255, 255))
        elif 104.9 <= t < 106.2:
            # ¡FIRULE! in golden orange
            draw_text_stroked(draw, "¡ FIRULE !", Y_SUB, FONT_XXL, (255, 160, 20), stroke_color=(120, 30, 0), stroke_w=10)
        elif 106.2 <= t < 107.5:
            # ¡FIN! in bright cyan/magenta
            draw_text_stroked(draw, "¡ FIN !", Y_SUB, FONT_XXL, (255, 80, 160), stroke_color=(40, 0, 60), stroke_w=10)
        elif 107.5 <= t < 111.5:
            # Final applause and cheers! (NO EMOJIS)
            draw_text_stroked(draw, "¡ MUY BIEN ISAI !", Y_SUB, FONT_XL, (255, 240, 80), stroke_color=(180, 40, 0), stroke_w=8)
            
            # Animate falling confetti over the screen
            confetti_elapsed = t - 107.5
            for p in confetti_particles:
                cy = int(p["y"] + confetti_elapsed * p["speed"] * 60) % HEIGHT
                cx = int(p["x"] + 15 * np.sin(confetti_elapsed * 4 + p["speed"]))
                s = p["size"]
                draw.rectangle([cx, cy, cx + s, cy + s//2], fill=p["color"])
        else:
            # 111.5s to 115.45s: Musical outro coda (soft chamamé groove fading out)
            draw_text_stroked(draw, "Cuento de Firule • Sala Lila", HEIGHT - 165, FONT_L, (255, 255, 255), stroke_color=(0, 0, 0), stroke_w=6)
            draw_text_stroked(draw, "Jardin de Infantes • Familia de Isai", HEIGHT - 95, FONT_M, (255, 230, 120), stroke_color=(0, 0, 0), stroke_w=5)
            
            # Gentle confetti during musical outro
            confetti_elapsed = t - 107.5
            for p in confetti_particles:
                cy = int(p["y"] + confetti_elapsed * p["speed"] * 45) % HEIGHT
                cx = int(p["x"] + 10 * np.sin(confetti_elapsed * 3 + p["speed"]))
                s = p["size"]
                draw.rectangle([cx, cy, cx + s, cy + s//2], fill=p["color"])

    # Convert RGB PIL back to BGR numpy array for ffmpeg
    final_bgr = cv2.cvtColor(np.array(frame_pil), cv2.COLOR_RGB2BGR)
    proc.stdin.write(final_bgr.tobytes())
    
    if frame_idx % 200 == 0:
        pct = (frame_idx / TOTAL_FRAMES) * 100
        print(f"[*] Rendering: {frame_idx}/{TOTAL_FRAMES} frames ({pct:.1f}%) | Time: {t:.1f}s")

proc.stdin.close()
proc.wait()
print(f"[OK] Video successfully rendered to {out_mp4}!")

# Copy to assets/firule
shutil.copyfile(out_mp4, "assets/firule/cuento_firule_isai.mp4")
print(f"[OK] Also saved to assets/firule/{out_mp4}")
