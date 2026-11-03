from PIL import Image
import numpy as np

for path in [
    r'C:\Users\admin\Downloads\WhatsApp Image 2026-10-03 at 16.01.07.jpeg',
    r'C:\Users\admin\Downloads\WhatsApp Image 2026-09-10 at 17.52.54.jpeg',
    r'C:\Users\admin\Downloads\WhatsApp Image 2026-09-12 at 20.53.06.jpeg',
    r'C:\Users\admin\Downloads\image (1).png',
    r'C:\Users\admin\Downloads\4a7f5885-9c93-4dd7-afa4-caec0fbfd546.jpg'
]:
    try:
        im = Image.open(path)
        arr = np.array(im)
        mean_c = arr.mean(axis=(0, 1))
        print(f"{path}: mean RGB = {mean_c}")
    except Exception as e:
        print(path, e)
