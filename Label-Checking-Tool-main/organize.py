import os
import shutil

BASE = "image_patches_20250426"

for f in os.listdir(BASE):
    if f.lower().endswith((".jpg", ".png", ".jpeg")):
        prefix = f.split("_")[0]  # e.g. 20240302_095020
        folder = os.path.join(BASE, prefix)
        os.makedirs(folder, exist_ok=True)

        src = os.path.join(BASE, f)
        dst = os.path.join(folder, f)

        shutil.move(src, dst)

print("DONE — All images moved into their correct folders!")
