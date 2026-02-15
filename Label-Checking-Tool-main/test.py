import os
import pandas as pd
from PIL import Image, ImageOps
import hashlib
import logging
import shutil

# Configure logging
logging.basicConfig(filename='patch_errors_v2.log', level=logging.WARNING)

# Read CSV and create output dir
df = pd.read_csv('Label-Checking-Tool-main/output_cm.csv')
output_dir = 'patches_img_name_2025_04_25'
os.makedirs(output_dir, exist_ok=True)

# Initialize Excel data collection
excel_data = []

# Rotation handling
rotation_df = None
if os.path.exists('Label-Checking-Tool-main/strawberry_rotation.xlsx'):
    rotation_df = pd.read_excel('Label-Checking-Tool-main/strawberry_rotation.xlsx')
    if 'rotation' not in rotation_df.columns:
        rotation_df = None

# Track which base image folders are created
created_folders = set()

# Check if images exist in the "imgs" folder
img_folder = 'Label-Checking-Tool-main/imgs/'
if not os.path.exists(img_folder):
    logging.error(f"The image folder '{img_folder}' does not exist.")
    exit()

for index, row in df.iterrows():
    try:
        # Extract base image name and coordinates
        full_name = row.iloc[0]
        base_name = full_name.split('_')[:-4]
        base_name = '_'.join(base_name).replace('.jpg', '')
        xtl, ytl, xbr, ybr = map(float, row[1:5])
        coords_str = f"{int(xtl)}{int(ytl)}{int(xbr)}_{int(ybr)}"

        # Get labels
        labels = [df.columns[i] for i, val in enumerate(row[5:], start=5) if val == 1]
        combined_label = '-_-'.join(sorted(labels)) if labels else "unlabeled"

        # Generate filename
        ideal_name = f"{coords_str}.jpg"
        if len(ideal_name) > 255:
            ideal_name = f"{combined_label}.jpg"
        if len(ideal_name) > 255:
            name_hash = hashlib.md5(ideal_name.encode()).hexdigest()[:8]
            truncated_name = f"{name_hash}.jpg"
            logging.warning(f"Filename truncated: {ideal_name} -> {truncated_name}")
            ideal_name = truncated_name

        # Create folder and save patch
        image_folder = os.path.join(output_dir, base_name)
        os.makedirs(image_folder, exist_ok=True)
        output_path = os.path.join(image_folder, ideal_name)

        image_path = os.path.join(img_folder, f"{base_name}.jpg")
        if os.path.exists(image_path):
            with Image.open(image_path) as img:
                img = ImageOps.exif_transpose(img)
                if rotation_df is not None:
                    rotation_row = rotation_df.loc[rotation_df['image_name'] == f"{base_name}.jpg"]
                    if not rotation_row.empty:
                        img = img.rotate(-rotation_row['rotation'].values[0], expand=True)
                patch = img.crop((xtl, ytl, xbr, ybr))
                patch.save(output_path)
                print(f"Saved: {output_path}")

        # Copy original image (but don't add to Excel)
        if base_name not in created_folders:
            if os.path.exists(image_path):
                shutil.copy(image_path, os.path.join(image_folder, f"{base_name}.jpg"))
                created_folders.add(base_name)

    except Exception as e:
        logging.error(f"Error processing {full_name}: {str(e)}")
        continue
