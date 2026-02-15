import os
from functools import partial
from PIL import Image
from PyQt5.QtWidgets import (
    QApplication, QWidget, QScrollArea, QVBoxLayout, QGridLayout,
    QPushButton, QMessageBox, QLineEdit
)
from PyQt5.QtGui import QPixmap, QIcon, QFont, QPainter
from PyQt5.QtCore import Qt, QSize, pyqtSignal, pyqtSlot, QObject, QThread 
import pandas as pd


IMAGE_FOLDER = "image_patches_20250426"
BUTTON_SIZE = QSize(150, 150)
PADDING = 10  # Space between buttons


class Worker(QObject):
    progressChanged = pyqtSignal(str, QPixmap, int, int)
    finished = pyqtSignal()

    def __init__(self, image_list, image_folder):
        super().__init__()
        self.image_list = image_list
        self.folder = image_folder

    @pyqtSlot()
    def do_work(self):
        for img_file in self.image_list:
            img_path = os.path.join(self.folder, img_file)
            try:
                # Check if image is signed off
                is_signed = self.is_image_signed(img_file)
                
                with Image.open(img_path) as img:
                    width, height = img.size
                    aspect_ratio = width / height
                    
                    # Calculate dimensions with space for borders
                    max_content_width = BUTTON_SIZE.width() - 6
                    max_content_height = BUTTON_SIZE.height() - 6
                    
                    if width > height:
                        content_width = max_content_width
                        content_height = int(content_width / aspect_ratio)
                        if content_height > max_content_height:
                            content_height = max_content_height
                            content_width = int(content_height * aspect_ratio)
                    else:
                        content_height = max_content_height
                        content_width = int(content_height * aspect_ratio)
                        if content_width > max_content_width:
                            content_width = max_content_width
                            content_height = int(content_width / aspect_ratio)
                
                # Create base pixmap
                pixmap = QPixmap(img_path).scaled(
                    content_width, 
                    content_height,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                
                # Create star overlay if signed
                if is_signed:
                    # Create a larger pixmap to hold both image and star
                    composite = QPixmap(BUTTON_SIZE)
                    composite.fill(Qt.transparent)
                    
                    painter = QPainter(composite)
                    # Draw the image centered
                    painter.drawPixmap(
                        (BUTTON_SIZE.width() - content_width) // 2,
                        (BUTTON_SIZE.height() - content_height) // 2,
                        pixmap
                    )
                    
                    # Draw star in top-right corner
                    star_size = 20
                    painter.setPen(Qt.yellow)
                    painter.setFont(QFont("Arial", star_size))
                    painter.drawText(
                        BUTTON_SIZE.width() - star_size - 5, 
                        5 + star_size, 
                        "★"
                    )
                    painter.end()
                    
                    final_pixmap = composite
                else:
                    final_pixmap = pixmap

                self.progressChanged.emit(img_file, final_pixmap, content_width, content_height)
            except Exception as e:
                print(f"Error processing {img_path}: {e}")
        self.finished.emit()

    def is_image_signed(self, img_file):
        """Check if image is signed off in your database"""
        try:
            df = pd.read_csv("output_cm.csv")
            signed = df.loc[df["Image Name"] == img_file, "Signed"].values[0]
            return bool(signed)
        except:
            return False


class ImageGrid(QWidget):
    image_selected = pyqtSignal(str)
    
    def __init__(self, img_start):
        super().__init__()
        self.img_start = img_start
        self.images = sorted([f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
        
        self.thread_running = False
        # Track selections
        self.primary_selection = None
        self.secondary_selection = set()
        self._thread = None  # Use underscore to avoid naming conflict
        
        self.layout = QVBoxLayout(self)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)

        self.container = QWidget()
        self.grid_layout = QGridLayout(self.container)
        self.grid_layout.setSpacing(PADDING)
        self.scroll_area.setWidget(self.container)

        self.container.setStyleSheet("background-color: black;")
        self.scroll_area.setStyleSheet("background-color: black;")
        self.setStyleSheet("background-color: black;")  # whole widget black

        self.buttons = []
        self.current_start = 0
        self.current_end = 0
        self.load_images()

    def setup_worker(self, image_names):
        # Clean up any existing thread
        if self._thread is not None and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait()
        
        self._thread = QThread()
        self.worker = Worker(image_names, IMAGE_FOLDER)
        self.worker.moveToThread(self._thread)

        self._thread.started.connect(self.worker.do_work)
        self.worker.progressChanged.connect(self.add_image_button)
        self.worker.finished.connect(self._thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(lambda: setattr(self, '_thread', None))
        self.worker.finished.connect(lambda: setattr(self, 'thread_running', False))  # ✅ Add this

        
        self.thread_running = True
        self._thread.start()

    def load_images(self, img_file=None, direction="forward"):
        """Load images with padding for backward navigation"""
        try:
            idx = self.images.index(img_file) if img_file is not None else 0
        except ValueError:
            idx = 0
            
        batch_size = 200
        padding = 2  # Number of images to prepend from previous batch
        
        if direction == "forward":
            start = max(0, idx - padding)
            end = min(len(self.images), start + batch_size + padding)
            if idx == 0:
                start = 0
                end = min(len(self.images), batch_size)
        elif direction == "backward":
            start = max(0, idx - batch_size - padding)
            end = min(len(self.images), idx + padding)
        else:
            start = idx
            end = min(len(self.images), start + batch_size)

        # Update current batch range
        self.current_start = start
        self.current_end = end

        # Clear previous buttons
        for button in self.buttons:
            button.deleteLater()
        self.buttons = []
        self.grid_layout.setColumnMinimumWidth(0, 0)  # Reset column minimums
        
        # Create new buttons
        print(f"Loading images from {start} to {end} (total: {len(self.images)})")
        self.setup_worker(self.images[start:end])

    def add_image_button(self, img_file, final_pixmap, content_width, content_height):
        """Add a new image button to the grid with proper labeling"""
        button = QPushButton()
        button.setIcon(QIcon(final_pixmap))
        button.setIconSize(QSize(content_width, content_height))
        button.setFixedSize(BUTTON_SIZE)
        
        # Store image name as a property
        button.setProperty("img_file", img_file)
        
        # Get all active labels (columns with value 1)
        try:
            output_df = pd.read_csv("output_cm.csv")
            # Get the row for this image
            img_row = output_df[output_df["Image Name"] == img_file].iloc[0]
            # Find all columns (except metadata columns) with value 1
            label_cols = [col for col in output_df.columns 
                        if col not in ['Image Name', 'Signed', 'xtl', 'ytl', 'xbr', 'ybr']]
            active_labels = [col for col in label_cols if img_row[col] == 1]
            
            # Set tooltip with filename and active labels
            tooltip = f"{img_file}\nLabels: {', '.join(active_labels)}" if active_labels else img_file
            button.setToolTip(tooltip)
        except Exception as e:
            print(f"Error loading labels for {img_file}: {str(e)}")
            button.setToolTip(img_file)
        
        self.update_button_style(button)
        button.clicked.connect(partial(self.on_left_click, img_file, button))
        button.setContextMenuPolicy(Qt.CustomContextMenu)
        button.customContextMenuRequested.connect(partial(self.on_right_click, img_file, button))
        
        self.buttons.append(button)
        
        # Grid positioning logic remains the same
        index = len(self.buttons) - 1
        area_width = self.scroll_area.viewport().width()
        columns = max(1, (area_width + PADDING) // (BUTTON_SIZE.width() + PADDING))
        row = index // columns
        col = index % columns
        
        self.grid_layout.addWidget(button, row, col)

    def on_left_click(self, img_file, button):
        """Handle left-click selection, with backward/forward navigation"""
        try:
            current_index = self.images.index(img_file)
            displayed_images = [b.property("img_file") for b in self.buttons]
            padding = 2

            # Update center image FIRST
            old_center = self.img_start
            self.img_start = img_file

            # Check if we need to load previous batch
            if (current_index <= self.current_start + padding and 
                self.current_start > 0):
                if  self.thread_running:
                    QMessageBox.warning(self, "Warning", "Image loading is still in progress")
                    
                    return
        
                self.load_images(img_file, direction="backward")
            # Check if we need to load next batch
            elif (current_index >= self.current_end - padding - 1 and 
                  self.current_end < len(self.images)):
                self.load_images(img_file, direction="forward")
            else:
                # Regular click - just update styles
                if old_center in [b.property("img_file") for b in self.buttons]:
                    old_button = next(b for b in self.buttons if b.property("img_file") == old_center)
                    self.update_button_style(old_button)
                self.update_button_style(button)

            # Always emit after handling navigation
            self.image_selected.emit(img_file)
        except Exception as e:
            print(f"Error handling click: {e}")

    def on_right_click(self, img_file, button, pos):
        """Handle right-click selection for label copying"""
        if self.primary_selection is None:
            self.primary_selection = img_file
        else:
            if img_file == self.primary_selection:
                self.primary_selection = None
            elif img_file in self.secondary_selection:
                self.secondary_selection.remove(img_file)
            else:
                self.secondary_selection.add(img_file)
        
        self.update_button_style(button)

    def update_button_style(self, button):
        """Update button style to show selection state without square background"""
        img_file = button.property("img_file")
        
        if img_file == self.primary_selection:
            # Green border for primary selection (right-click)
            button.setStyleSheet("""
                QPushButton {
                    border: 3px solid green;
                    background: transparent;
                    padding: 0px;
                }
            """)
        elif img_file in self.secondary_selection:
            # Red border for secondary selections (right-click)
            button.setStyleSheet("""
                QPushButton {
                    border: 3px solid red;
                    background: transparent;
                    padding: 0px;
                }
            """)
        elif img_file == self.img_start:
            # Yellow border for currently selected image (left-click)
            button.setStyleSheet("""
                QPushButton {
                    border: 3px solid yellow;
                    background: transparent;
                    padding: 0px;
                }
            """)
        else:
            # No border (just the image)
            button.setStyleSheet("""
                QPushButton {
                    border: none;
                    background: transparent;
                    padding: 0px;
                }
            """)

    def resizeEvent(self, event):
        """Re-layout when window is resized"""
        super().resizeEvent(event)
        self.relayout_buttons()

    def relayout_buttons(self):
        """Reorganize buttons when window size changes"""
        if not self.buttons:
            return
            
        # Clear the layout
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)

        area_width = self.scroll_area.viewport().width()
        columns = max(1, (area_width + PADDING) // (BUTTON_SIZE.width() + PADDING))
        
        row, col = 0, 0
        for button in self.buttons:
            self.grid_layout.addWidget(button, row, col)
            col += 1
            if col >= columns:
                col = 0
                row += 1

    def cleanup(self):
        """Clean up resources when closing"""
        if self._thread is not None and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait()