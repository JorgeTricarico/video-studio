import os
import time

user_folders = [
    r'C:\Users\admin\Downloads',
    r'C:\Users\admin\Desktop',
    r'C:\Users\admin\Pictures',
    r'C:\Users\admin\Documents',
    r'C:\Users\admin\Videos'
]

found = []
for base in user_folders:
    for root, dirs, files in os.walk(base):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in {'.jpg', '.jpeg', '.png', '.webp', '.heic', '.bmp'}:
                p = os.path.join(root, f)
                try:
                    mtime = os.path.getmtime(p)
                    found.append((mtime, p))
                except Exception:
                    pass

found.sort(reverse=True)
print(f"Total imágenes en carpetas de usuario: {len(found)}")
for mtime, p in found[:40]:
    t_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))
    print(f"{t_str} | {os.path.getsize(p):>10} bytes | {p}")
