import os
from PIL import Image, ImageOps, ImageDraw
from PIL import ImageQt
from PyQt5.QtWidgets import (QApplication, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QLabel)
from PyQt5.QtGui import QPixmap, QImage, QPainter, QColor
from PyQt5.QtCore import Qt, QPoint
import pandas as pd
from PyQt5.QtWidgets import QMenu, QApplication  # Add to existing imports
from PyQt5.QtGui import QClipboard  # Add to existing imports




def extract_coordinates_from_filename(filename):
    """Extracts base_name, xtl, ytl, xbr, ybr from patch filename."""
    base_part = os.path.splitext(os.path.basename(filename))[0]
    parts = base_part.split('_')
    if len(parts) >= 5:
        *base_parts, xtl, ytl, xbr, ybr = parts
        base_name = '_'.join(base_parts)
        try:
            return base_name, int(xtl), int(ytl), int(xbr), int(ybr)
        except ValueError:
            return None, None, None, None, None
    return None, None, None, None, None

class ImagePanel(QLabel):
    def __init__(self):
        super().__init__()
        self.pixmap = None
        self.setStyleSheet("background-color: black;")  # <<< add this line

        self.patch_pixmap = None
        self.base_pixmap = None
        self.zoom = 1.0
        self.offset = QPoint(0, 0)
        self.drag_start_pos = None
        self.showing_base = False
        self.bbox_coords = None
        self.rotation_angle = 0
        self.setMinimumSize(400, 400)
        self.current_base_path = None
        self.image_info_label = QLabel("No image selected")
        self.filename = None

        self.current_labels = []
        self.output_df = pd.read_csv("output_cm.csv")  # Load your label data
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos):
        """Show context menu on right-click"""
        if not self.pixmap:
            return
            
        menu = QMenu(self)
        copy_action = menu.addAction("Copy Image")
        copy_action.triggered.connect(self.copy_image_to_clipboard)
        menu.exec_(self.mapToGlobal(pos))

    def copy_image_to_clipboard(self):
        """Copy current image to clipboard"""
        if self.pixmap:
            clipboard = QApplication.clipboard()
            clipboard.setPixmap(self.pixmap)
            print("Image copied to clipboard")



    def process_image(self, img_path, draw_bbox=False):
        """Process image with EXIF correction and transformations"""
        try:
            img = Image.open(img_path)
            print(f"[DEBUG] Opened image: {img_path}")
            rot_df = pd.read_excel("strawberry_rotation.xlsx")
            img_name = img_path[5:]
            print(f"[DEBUG] Image name for rotation lookup: {img_name}")
            rot_angle = rot_df.loc[rot_df['image_name'] == img_name, 'rotation']
            
            rot_angle = int(rot_angle)
            print(f"[DEBUG] Rotation angle found: {rot_angle}")
            # 1. Apply EXIF orientation correction
            img = ImageOps.exif_transpose(img).convert("RGB")
            print("[DEBUG] Applied EXIF transpose and converted to RGB.")

            # 2. Apply manual rotation if needed
            print("rot_angle", rot_angle)
            if rot_angle:
                img = img.rotate(-rot_angle, expand=True)
                print(f"[DEBUG] Rotated image by {self.rotation_angle} degrees.")

            # 3. Draw bounding box if requested and coordinates are available
            if draw_bbox and self.bbox_coords:
                try:
                    xtl, ytl, xbr, ybr = self.bbox_coords
                    print(f"[DEBUG] Drawing box at: {xtl},{ytl} to {xbr},{ybr}")
                    print(f"[DEBUG] Image size: {img.size}")
                    
                    # Create a copy of the image to draw on
                    img_with_box = img.copy()
                    draw = ImageDraw.Draw(img_with_box)
                    
                    # Draw rectangle
                    draw.rectangle([xtl, ytl, xbr, ybr], outline="red", width=3)
                    print("[DEBUG] Successfully drew rectangle")
                    return img_with_box
                    
                except Exception as bbox_e:
                    print(f"[ERROR] Exception drawing rectangle: {bbox_e}")
                    import traceback
                    traceback.print_exc()
                    return img  # Return original image if drawing fails
            
            return img

        except Exception as e:
            print(f"[ERROR] Image processing error: {str(e)}")
            import traceback
            traceback.print_exc()
            return Image.new("RGB", (800, 600), color="gray")

    def get_labels_for_image(self, image_name):
        print("get labels ")
        """Get the labels for a specific image from the CSV"""
        try:
            # Find the row for this image
            self.output_df = pd.read_csv("output_cm.csv")  # Reload in case it was modified
            row = self.output_df[self.output_df["Image Name"] == image_name].iloc[0]
            
            # Get all labels that are marked as 1 (True)
            labels = []
            for col in self.output_df.columns:
                if col not in ["Image Name", "Signed"] and row[col] == 1:
                    labels.append(col)
                    
            return labels
        except Exception as e:
            print(f"Error getting labels: {str(e)}")
            return []




    def set_image(self, pixmap=None, filename=None):
        print("set_iamge ")
        """Load and process image"""
        if filename:
            print(f"Setting image with filename: {filename}")

            print(f"Setting image with filename: {filename}")
            self.filename = filename
            
            # Extract base name to check if this is a patchdob
            base_name, xtl, ytl, xbr, ybr = extract_coordinates_from_filename(filename)
            
            if None not in (xtl, ytl, xbr, ybr):
                # This is a patch image - get its labels
                self.current_labels = self.get_labels_for_image(filename)
                info_text = f"{filename}\nLabels: {', '.join(self.current_labels)}"
            else:
                # This is a base image
                self.current_labels = []
                info_text = filename
                

            print("print 1")
            self.image_info_label.setText(info_text)
            print("print 2")



            self.filename = filename  # Store filename as attribute
            pil_img = self.process_image(filename)
            
            # Convert PIL Image to QImage
            if pil_img.mode == "RGB":
                qimage = QImage(pil_img.tobytes(), pil_img.size[0], pil_img.size[1], 
                            pil_img.size[0] * 3, QImage.Format_RGB888)
            elif pil_img.mode == "RGBA":
                qimage = QImage(pil_img.tobytes(), pil_img.size[0], pil_img.size[1], 
                            pil_img.size[0] * 4, QImage.Format_RGBA8888)
            else:
                pil_img = pil_img.convert("RGB")
                qimage = QImage(pil_img.tobytes(), pil_img.size[0], pil_img.size[1], 
                            pil_img.size[0] * 3, QImage.Format_RGB888)
                
            self.patch_pixmap = QPixmap.fromImage(qimage)
        else:
            self.patch_pixmap = pixmap
            
        self.pixmap = self.patch_pixmap
        self.zoom = 1.0
        self.offset = QPoint(0, 0)
        self.update()

    def paintEvent(self, event):
        print("paint event ")
        if self.pixmap:
            painter = QPainter(self)
            scaled_pixmap = self.pixmap.scaled(
                self.pixmap.size() * self.zoom,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            x = (self.width() - scaled_pixmap.width()) // 2 + self.offset.x()
            y = (self.height() - scaled_pixmap.height()) // 2 + self.offset.y()
            painter.drawPixmap(x, y, scaled_pixmap)


            if self.filename:
                filename = self.filename
                print(f"Setting image with filename: {filename}")

                print(f"Setting image with filename: {filename}")
                self.filename = filename
                
                # Extract base name to check if this is a patch
                base_name, xtl, ytl, xbr, ybr = extract_coordinates_from_filename(filename)
                
                if None not in (xtl, ytl, xbr, ybr):
                    # This is a patch image - get its labels
                    self.current_labels = self.get_labels_for_image(filename)
                    info_text = f"{filename}\nLabels: {', '.join(self.current_labels)}"
                else:
                    # This is a base image
                    self.current_labels = []
                    info_text = filename
                    

                print("print 1")
                self.image_info_label.setText(info_text)
                print("print 2")





            # Draw the info label
            if hasattr(self, 'image_info_label') and self.image_info_label.text():
                print("hasattr")
                # Position label at bottom center
                label_width = self.image_info_label.sizeHint().width()
                label_x = (self.width() - label_width) // 2
                label_y = self.height() - 40  # 40 pixels from bottom
                
                # Save painter state
                painter.save()
                
                # Draw semi-transparent background
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(0, 0, 0, 150))  # Semi-transparent black
                painter.drawRoundedRect(
                    label_x - 5, label_y - 5,
                    label_width + 10, 40,
                    5, 5
                )
                
                # Draw text
                painter.setPen(Qt.white)
                painter.drawText(
                    label_x, label_y,
                    label_width, 30,
                    Qt.AlignCenter,
                    self.image_info_label.text()
                )
                
                # Restore painter state
                painter.restore()






    def wheelEvent(self, event):
        if self.pixmap:
            angle = event.angleDelta().y()
            factor = 1.1 if angle > 0 else 0.9
            self.zoom *= factor
            self.zoom = max(0.1, min(self.zoom, 10))
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()

    def mouseMoveEvent(self, event):
        if self.drag_start_pos:
            delta = event.pos() - self.drag_start_pos
            self.offset += delta
            self.drag_start_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = None

    def mouseDoubleClickEvent(self, event):
        if not hasattr(self, 'filename') or not self.filename:
            print("[ERROR] No filename available")
            return

        try:
            if not self.showing_base:
                print("[DEBUG] Switching to base image")
                base_name, xtl, ytl, xbr, ybr = extract_coordinates_from_filename(self.filename)
                print(f"[DEBUG] Extracted coordinates: {base_name}, {xtl}, {ytl}, {xbr}, {ybr}")
                
                if None in (base_name, xtl, ytl, xbr, ybr):
                    print("[ERROR] Could not extract coordinates from filename")
                    return

                # Look for base image with any extension
                base_path = None
                for ext in ['.jpg', '.JPG', '.jpeg', '.JPEG']:
                    test_path = os.path.join("imgs", f"{base_name}{ext}")
                    if os.path.exists(test_path):
                        base_path = test_path
                        print(f"[DEBUG] Found base image: {base_path}")
                        break

                print("info 1")
                info_text = f"{base_name}"
                self.image_info_label.setText(info_text)
                print("info 2")

                if not base_path:
                    print(f"[ERROR] Base image not found for: {base_name} with any extension")
                    return

                # Store coordinates and base path
                self.bbox_coords = (int(xtl), int(ytl), int(xbr), int(ybr))
                self.current_base_path = base_path
                print(f"[DEBUG] Bounding box coordinates: {self.bbox_coords}")

                # Load base image with bounding box
                pil_img = self.process_image(base_path, draw_bbox=True)
                if pil_img is None:
                    print("[ERROR] Failed to process base image")
                    return

                # Convert PIL Image to QImage properly
                if pil_img.mode == "RGB":
                    qimage = QImage(pil_img.tobytes(), pil_img.size[0], pil_img.size[1], 
                                pil_img.size[0] * 3, QImage.Format_RGB888)
                elif pil_img.mode == "RGBA":
                    qimage = QImage(pil_img.tobytes(), pil_img.size[0], pil_img.size[1], 
                                pil_img.size[0] * 4, QImage.Format_RGBA8888)
                else:
                    # Convert to RGB if in another format
                    pil_img = pil_img.convert("RGB")
                    qimage = QImage(pil_img.tobytes(), pil_img.size[0], pil_img.size[1], 
                                pil_img.size[0] * 3, QImage.Format_RGB888)

                self.base_pixmap = QPixmap.fromImage(qimage)
                if self.base_pixmap.isNull():
                    print("[ERROR] Failed to create QPixmap from base image")
                    return

                self.pixmap = self.base_pixmap
                self.showing_base = True
            else:
                print("[DEBUG] Reverting to patch image")
                self.pixmap = self.patch_pixmap
                self.showing_base = False

            self.zoom = 1.0
            self.offset = QPoint(0, 0)
            self.update()

        except Exception as e:
            print(f"[ERROR] Exception in double click handler: {str(e)}")
            import traceback
            traceback.print_exc()

class ImageViewer(QWidget):
    def __init__(self, image_folder):
        super().__init__()
        self.image_panel = ImagePanel()
        self.image_folder = image_folder
        self.images = [
            os.path.join(image_folder, f) 
            for f in os.listdir(image_folder) 
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        ]
        self.curr_img_idx = 0
        
        self.init_ui()
        self.load_image()

    def init_ui(self):
        self.next_btn = QPushButton("Next")
        self.prev_btn = QPushButton("Previous")
        self.next_btn.clicked.connect(self.next_image)
        self.prev_btn.clicked.connect(self.prev_image)



        nav_layout = QHBoxLayout()
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.next_btn)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.image_panel)
        main_layout.addWidget(self.image_panel.image_info_label)  # Add the info label
        main_layout.addLayout(nav_layout)
        self.setLayout(main_layout)
        self.setWindowTitle("Image Viewer")
        self.resize(800, 600)

    def load_image(self):
        if self.images:
            img_path = self.images[self.curr_img_idx]
            self.image_panel.filename = img_path
            self.image_panel.set_image(filename=img_path)

    def next_image(self):
        if self.images:
            self.curr_img_idx = (self.curr_img_idx + 1) % len(self.images)
            self.load_image()

    def prev_image(self):
        if self.images:
            self.curr_img_idx = (self.curr_img_idx - 1) % len(self.images)
            self.load_image()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    
    # Example usage - replace with your image folder
    image_folder = "image_patches_20250426"
    if not os.path.exists(image_folder):
        os.makedirs(image_folder, exist_ok=True)
        print(f"Created dummy folder: {image_folder}")
    
    # Also create the base images folder if it doesn't exist
    if not os.path.exists("imgs"):
        os.makedirs("imgs", exist_ok=True)
        print("Created base images folder: imgs")
    
    viewer = ImageViewer(image_folder)
    viewer.show()
    sys.exit(app.exec_())