from PIL import Image, ImageDraw, ImageFilter, ImageOps
import numpy as np

# Load original
orig = Image.open('C:/Users/admin/Downloads/WhatsApp Image 2026-10-27 at 21.17.56.jpeg').convert('RGB')
w, h = orig.size # 1600, 1204

W_16_9, H_16_9 = 1920, 1080

# OPTION 1: Natural Whiteboard Extension (seamless edges matching the whiteboard color, subtle border)
# The whiteboard border color is ~ [168, 169, 164]
bg_color = (170, 172, 168)
opt1 = Image.new('RGB', (W_16_9, H_16_9), bg_color)
# Scale original to fit entirely within height with 30px margin top and bottom
scale = (H_16_9 - 60) / h # ~ 1020 / 1204 = 0.847
new_w = int(w * scale)
new_h = int(h * scale)
scaled_orig = orig.resize((new_w, new_h), Image.Resampling.LANCZOS)

# Soft gradient blend on left and right edges so it merges seamlessly into the whiteboard canvas
# Left and right side margins: (1920 - new_w) // 2
x_off = (W_16_9 - new_w) // 2
y_off = (H_16_9 - new_h) // 2

opt1.paste(scaled_orig, (x_off, y_off))

# Soft blend of edges
arr1 = np.array(opt1)
# Add a thin stylish whiteboard aluminum/wood frame around the whole 16:9 canvas
draw1 = ImageDraw.Draw(opt1)
# Subtle inner shadow / border
draw1.rectangle([10, 10, W_16_9-10, H_16_9-10], outline=(140, 142, 138), width=3)
draw1.rectangle([14, 14, W_16_9-14, H_16_9-14], outline=(200, 202, 198), width=2)
opt1.save('test_opt1_whiteboard_canvas.jpg', quality=95)

# OPTION 2: Warm Playful Classroom Easel (Warm wood frame and subtle cream background)
opt2 = Image.new('RGB', (W_16_9, H_16_9), (248, 244, 236))
# Blurred warm version as atmospheric backdrop
blur_bg = orig.resize((W_16_9, H_16_9), Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(35))
# Dim slightly
blur_arr = np.array(blur_bg).astype(float) * 0.85 + np.array([248, 244, 236]) * 0.15
opt2 = Image.fromarray(blur_arr.astype(np.uint8))

# Frame for the whiteboard in center
frame_draw = ImageDraw.Draw(opt2)
# Center whiteboard with its real 4:3 proportion
board_h = H_16_9 - 80 # 1000
board_w = int(board_h * (w / h)) # 1328
bx = (W_16_9 - board_w) // 2
by = 40

# Shadow behind the board
for i in range(15):
    frame_draw.rounded_rectangle([bx - i, by - i + 4, bx + board_w + i, by + board_h + i + 4], radius=16, outline=(0, 0, 0, 10), fill=None)

# Whiteboard aluminum frame
frame_draw.rounded_rectangle([bx - 8, by - 8, bx + board_w + 8, by + board_h + 8], radius=14, fill=(225, 228, 232), outline=(170, 175, 180), width=4)

# Paste scaled orig inside
opt2.paste(orig.resize((board_w, board_h), Image.Resampling.LANCZOS), (bx, by))
opt2.save('test_opt2_framed_easel.jpg', quality=95)

print("Saved test options")
