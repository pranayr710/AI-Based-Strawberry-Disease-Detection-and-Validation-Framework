import os
import pandas as pd
from PIL import Image, ImageOps, ImageDraw
import logging
import pandas as pd
# Configure logging
logging.basicConfig(filename='draw_boxes_single_image.log', level=logging.WARNING)

# #######################################################
# SET YOUR IMAGE NAME HERE (without path, just the filename)
INPUT_IMAGE_NAME = "nihal_ooty_tnau_real_20230912_00124"
# #######################################################

def draw_boxes_on_rotated_images(input_image_name):
    # Read CSV
    print(f"Processing image: {input_image_name}")
    df = pd.read_csv('output_cm.csv')
    output_dir = f'boxed_images_{input_image_name}'
    os.makedirs(output_dir, exist_ok=True)

    # Get base name
    base_name = input_image_name
    
    # Find all patches for this image
    patches_df = df[df['Image Name'].str.contains(base_name)]
    if patches_df.empty:
        print(f"No patches found for base image: {base_name}")
        return
    
    # Check if base image exists
    img_folder = 'imgs/'
    image_path = os.path.join(img_folder, f"{base_name}.jpg")
    
    if not os.path.exists(image_path):
        logging.error(f"Base image not found: {image_path}")
        print(f"Error: Base image not found at {image_path}")
        return

    try:
        # Open and process image
        with Image.open(image_path) as original_img:
            original_img = ImageOps.exif_transpose(original_img)
            
            # Define all rotations we want to process
            rotations = [
                (0, "0"),    # No rotation
                (90, "90"),  # 90° clockwise (using -90 as per your negation requirement)
                (180, "180"),
                (270, "270")
            ]
            
            for rotation_degrees, rotation_suffix in rotations:
                # Rotate the image (applying negation as requested)
                if rotation_degrees == 0:
                    img = original_img.copy()
                else:
                    img = original_img.rotate(-rotation_degrees, expand=True)
                
                # Create drawing context
                draw = ImageDraw.Draw(img)
                
                # Process each patch to draw boxes
                for index, row in patches_df.iterrows():
                    xtl, ytl, xbr, ybr = map(float, row[1:5])
                    
                    # Get labels for this box
                    labels = [col for col, val in row[5:].items() if val == 1]
                    combined_label = '-'.join(sorted(labels)) if labels else "unlabeled"
                    
                    # Draw rectangle
                    draw.rectangle([(xtl, ytl), (xbr, ybr)], outline="red", width=3)
                    
                    # Draw label text
                    text_position = (xtl, ytl - 15) if ytl > 15 else (xtl, ytl + 5)
                    draw.text(text_position, combined_label, fill="red")
                
                # Save the image with boxes
                output_path = os.path.join(output_dir, f"boxed_{base_name}_{rotation_suffix}.jpg")
                img.save(output_path)
                print(f"Saved boxed image ({rotation_suffix}°): {output_path}")
            
    except Exception as e:
        logging.error(f"Error processing {input_image_name}: {str(e)}")
        print(f"Error processing {input_image_name}: {str(e)}")

    print(f"Processing complete. Output saved in: {output_dir}")

if __name__ == "__main__":
    df = pd.read_csv("rotated_img_names.csv")
    list_of_images = df['Image Name'].tolist()
    for img in list_of_images:
        draw_boxes_on_rotated_images(img)