import os
import sys
import subprocess
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1920, 1080
FPS = 30
AUDIO_PATH = "audio_final_master.mp3"
OUT_VIDEO = "cuento_firule_15escenas_preview.mp4"
TOTAL_FRAMES = 3463 # 115.455s * 30fps

FFMPEG_BIN = "ffmpeg"

# Fonts
def get_font(size, bold=True):
    names = ["comicbd.ttf" if bold else "comic.ttf", "arialbd.ttf" if bold else "arial.ttf"]
    for n in names:
        p = os.path.join(r"C:\Windows\Fonts", n)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

FONT_TITLE = get_font(42, bold=True)
FONT_SUB = get_font(56, bold=True)
FONT_XXL = get_font(96, bold=True)

def load_bgr(path):
    if not os.path.exists(path):
        im = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        im[:] = (220, 230, 240)
        return im
    img = cv2.imread(path)
    if img.shape[1] != WIDTH or img.shape[0] != HEIGHT:
        img = cv2.resize(img, (WIDTH, HEIGHT), interpolation=cv2.INTER_AREA)
    return img

def apply_ken_burns(img_bgr, zoom=1.0, pan_x=0.0, pan_y=0.0):
    if zoom <= 1.001 and abs(pan_x) < 0.001 and abs(pan_y) < 0.001:
        return img_bgr
    h, w = img_bgr.shape[:2]
    nw = int(w / zoom)
    nh = int(h / zoom)
    cx = int(w / 2 + pan_x * (w - nw) / 2)
    cy = int(h / 2 + pan_y * (h - nh) / 2)
    x1 = max(0, min(w - nw, cx - nw // 2))
    y1 = max(0, min(h - nh, cy - nh // 2))
    cropped = img_bgr[y1:y1+nh, x1:x1+nw]
    return cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)

def draw_stroked_text(draw, text, y_center, font, fill_color, stroke_color=(0, 0, 0), stroke_w=6):
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (WIDTH - tw) // 2
    y = y_center - th // 2
    draw.text((x + 4, y + 4), text, font=font, fill=(0, 0, 0, 180), stroke_width=stroke_w, stroke_fill=(0, 0, 0))
    draw.text((x, y), text, font=font, fill=fill_color, stroke_width=stroke_w, stroke_fill=stroke_color)

def render_video():
    print(f"[*] Pre-loading 15 scene images...")
    scenes = [
        ("assets/firule/00_dibujo_original_isai.jpg", 0.0, 3.85, "Escena 0: El Dibujo Real de Isaí"),
        ("assets/firule/01_portada_ia.jpg", 3.85, 11.5, "Escena 1: Firulé, un perro con suerte"),
        ("assets/firule/02_paseo_parque.jpg", 11.5, 19.5, "Escena 2: Paseo en el parque con María"),
        ("assets/firule/02_b_timbre_encomienda.jpg", 19.5, 27.0, "Escena 3: Suena el timbre de la encomienda"),
        ("assets/firule/02b_tropiezo_pantufla_pasillo.jpg", 27.0, 35.0, "Escena 4: La pantufla voladora en el pasillo"),
        ("assets/firule/02_c_puerta_escape_sigiloso.jpg", 35.0, 42.0, "Escena 5: Firulé asomándose por la puerta abierta"),
        ("assets/firule/02c_firule_vereda_vecinos.jpg", 42.0, 49.5, "Escena 6: Firulé en la vereda saludando vecinos"),
        ("assets/firule/03_atardecer_frio_vereda.jpg", 49.5, 57.0, "Escena 7: Atardecer frío y faroles encendiéndose"),
        ("assets/firule/03_b_firule_armando_camita.jpg", 57.0, 65.0, "Escena 8: Firulé armando su camita en la cuneta"),
        ("assets/firule/03_c_misterio_montoncito_hojas.jpg", 65.0, 72.5, "Escena 9: El montoncito de hojas que se mueve"),
        ("assets/firule/04_cuneta_enamorado.jpg", 72.5, 80.0, "Escena 10: Aparece la perrita blanca entre las hojas"),
        ("assets/firule/04b_enamorados_vereda.jpg", 80.0, 87.0, "Escena 11: Firulé y la perrita paseando juntos enamorados"),
        ("assets/firule/04_c_maria_encuentra_vereda.jpg", 87.0, 93.0, "Escena 12: María sale a la vereda y los encuentra"),
        ("assets/firule/05_final_casa.jpg", 93.0, 98.0, "Escena 13: María recibe a los dos perritos en casa"),
        ("assets/firule/05_b_festejo_isai_confeti.jpg", 98.0, 108.5, "Escena 14: Festejo interactivo con confeti"),
        ("assets/firule/05_c_coda_dormidos_juntos.jpg", 108.5, 115.455, "Escena 15: Buenas noches, dormidos juntos"),
    ]

    loaded_bgr = [load_bgr(p) for p, _, _, _ in scenes]
    print(f"[*] Loaded {len(loaded_bgr)} scene frames successfully.")

    cmd = [
        FFMPEG_BIN, "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "bgr24",
        "-r", str(FPS),
        "-i", "-",
        "-i", AUDIO_PATH,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "veryfast",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        OUT_VIDEO
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    for frame_idx in range(TOTAL_FRAMES):
        t = frame_idx / FPS

        # Find active scene
        active_idx = 0
        for i, (_, t_start, t_end, _) in enumerate(scenes):
            if t_start <= t < t_end:
                active_idx = i
                break
        if t >= scenes[-1][2]:
            active_idx = len(scenes) - 1

        _, t_s, t_e, _ = scenes[active_idx]
        dur = max(0.1, t_e - t_s)
        p = (t - t_s) / dur

        # Smooth Ken Burns directly in BGR
        curr_bgr = loaded_bgr[active_idx]
        pan_dir = 0.08 if active_idx % 2 == 0 else -0.08
        frame_bgr = apply_ken_burns(curr_bgr, zoom=1.0 + p * 0.04, pan_x=p * pan_dir)

        # Crossfade at start of scene (0.4s)
        if active_idx > 0 and (t - t_s) < 0.4:
            cf_p = (t - t_s) / 0.4
            prev_bgr = loaded_bgr[active_idx - 1]
            frame_bgr = cv2.addWeighted(prev_bgr, 1.0 - cf_p, frame_bgr, cf_p, 0)

        # Subtitles and Badges only when needed
        if t < 3.85 or (98.0 <= t < 108.5):
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            frame_pil = Image.fromarray(frame_rgb)
            draw = ImageDraw.Draw(frame_pil)

            if t < 3.85:
                draw.rounded_rectangle([WIDTH//2 - 420, 25, WIDTH//2 + 420, 95], radius=20, fill=(255, 255, 255, 240), outline=(230, 160, 40), width=3)
                draw.text((WIDTH//2 - 370, 38), "Dibujado y presentado por Isai", font=FONT_TITLE, fill=(60, 40, 20))

            elif 98.0 <= t < 108.5:
                # Subtítulos limpios flotantes sin franja negra inferior
                Y_SUB = HEIGHT - 130
                if 98.0 <= t < 100.5:
                    draw_stroked_text(draw, "Y asi termina este cuen...", Y_SUB, FONT_SUB, (255, 255, 255))
                elif 100.5 <= t < 101.6:
                    draw_stroked_text(draw, "¡ TO !", Y_SUB, FONT_XXL, (255, 230, 20), stroke_color=(200, 20, 0), stroke_w=10)
                elif 101.6 <= t < 103.2:
                    draw_stroked_text(draw, "de un perro con mucha suer...", Y_SUB, FONT_SUB, (255, 255, 255))
                elif 103.2 <= t < 104.2:
                    draw_stroked_text(draw, "¡ TE !", Y_SUB, FONT_XXL, (50, 255, 120), stroke_color=(0, 80, 40), stroke_w=10)
                elif 104.2 <= t < 104.9:
                    draw_stroked_text(draw, "que se llama...", Y_SUB, FONT_SUB, (255, 255, 255))
                elif 104.9 <= t < 106.2:
                    draw_stroked_text(draw, "¡ FIRULE !", Y_SUB, FONT_XXL, (255, 160, 20), stroke_color=(120, 30, 0), stroke_w=10)
                elif 106.2 <= t < 107.5:
                    draw_stroked_text(draw, "¡ FIN !", Y_SUB, FONT_XXL, (255, 80, 160), stroke_color=(40, 0, 60), stroke_w=10)
                elif 107.5 <= t < 108.5:
                    draw_stroked_text(draw, "¡Muy bien! (Aplausos)", Y_SUB, FONT_SUB, (255, 240, 150))

            frame_bgr = cv2.cvtColor(np.array(frame_pil), cv2.COLOR_RGB2BGR)

        proc.stdin.write(frame_bgr.tobytes())

    proc.stdin.close()
    proc.wait()
    print(f"[SUCCESS] Preview video generated: {OUT_VIDEO}")

if __name__ == "__main__":
    render_video()
