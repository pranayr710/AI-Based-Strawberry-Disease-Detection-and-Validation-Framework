import sys
import os
import pandas as pd 
from PyQt5.QtWidgets import (
    QApplication, QWidget, QFrame, QVBoxLayout, QSplitter,
    QHBoxLayout, QScrollArea, QPushButton, QMessageBox, QLineEdit
)
from PyQt5.QtCore import QStringListModel
from PyQt5.QtWidgets import QCompleter
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from change_frame import ChangeFrame
from image_panel import ImagePanel
from image_buttons import ImageGrid
from current_btns import ActiveLabels
from btn_grid import ButtonGrid
from drop_down import CustomMultiSelectComboBox
from key_value_selector import AtomicKeyValueSelector
from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QTextDocument
from SignedHighlightDelegate import SignedHighlightDelegate

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Annotation Tool")
        self.setGeometry(100, 100, 1000, 800)
        self.setStyleSheet("""
            QWidget { color: white; background-color: black; }
            QPushButton { color: black; background-color: #444; }
            QLabel { color: white; }
            QLineEdit { color: black; background-color: black; }
            QComboBox { color: black; background-color: black; }
        """)
        self.buttons_df = pd.read_csv("buttons.csv")
        self.image_names_df = pd.read_csv("img_names.csv")  # Read once and store
        self.init_ui()
        
    def init_ui(self):  
        # Initialize all components
        self.setup_image_section()
        self.setup_navigation()
        self.setup_label_sections()
        self.setup_main_layout()
        
    def setup_image_section(self):
        """Setup the image panel and viewer"""
        self.image_panel = ImagePanel()
        labels = self.buttons_df["xml_labels"].tolist()

        self.imggrid = ImageGrid("20240302_095020_0_0_373_346.jpg")
        image_viewer = QFrame()
        self.output_df = pd.read_csv("output_cm.csv")
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Type image name here")
        
        # Get unique base image names
        img_names_df = pd.read_csv("img_names.csv")
        base_names = img_names_df["Image Name"].unique().tolist()
        
        self.completer = QCompleter(base_names)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        
        # Set our custom delegate with access to the data
        self.delegate = SignedHighlightDelegate(self.completer)
        self.completer.popup().setItemDelegate(self.delegate)
        
        self.search_bar.setCompleter(self.completer)
    
        image_viewer.setFrameShape(QFrame.Box)
        image_viewer_layout = QVBoxLayout()
        image_viewer.setLayout(image_viewer_layout)
        self.search_btn = QPushButton("Search")
        self.confirm_btn = QPushButton("Confirm the multi-label change")
        self.deselect_btn = QPushButton("Deselect All")

        # Create a horizontal layout for the buttons
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.search_btn)
        button_layout.addWidget(self.confirm_btn)
        button_layout.addWidget(self.deselect_btn)

        # Add combo box and search bar to the main layout
        labels_sorted = sorted(labels)
        self.drop_down = CustomMultiSelectComboBox(labels_sorted)
        image_viewer_layout.addWidget(self.drop_down)
        image_viewer_layout.addWidget(self.search_bar)

        # Add the horizontal button layout to the main layout
        image_viewer_layout.addLayout(button_layout)

        def deselect_images():
            """Deselect all images in the grid"""
            print("deselect_images called")
            self.imggrid.primary_selection = None
            self.imggrid.secondary_selection = set()
            for btn in self.imggrid.buttons:
                self.imggrid.update_button_style(btn)


        def multi_change():
            if not self.imggrid.primary_selection:
                QMessageBox.warning(self, "Warning", "No source image selected (green highlight)")
                return
                
            if not self.imggrid.secondary_selection:
                QMessageBox.warning(self, "Warning", "No target images selected (red highlight)")
                return
            self.delegate.output_df = pd.read_csv("output_cm.csv")  
            try:
                df = pd.read_csv("output_cm.csv")
                source_img = self.imggrid.primary_selection
                
                # Get all labels from source image
                source_row = df[df["Image Name"] == source_img].iloc[0]
                labels_to_copy = {col: val for col, val in source_row.items() 
                                if col != "Image Name" and col != "Signed"}
                
                # Apply to all target images
                for target_img in self.imggrid.secondary_selection:
                    for col, val in labels_to_copy.items():
                        df.loc[df["Image Name"] == target_img, col] = val
                    df.loc[df["Image Name"] == target_img, "Signed"] = 1  # Mark as signed
                    
                # Save changes
                df.to_csv("output_cm.csv", index=False)
                
                QMessageBox.information(self, "Success", 
                    f"Copied labels from {source_img} to {len(self.imggrid.secondary_selection)} images")
                
                # Clear selections after operation
                self.imggrid.primary_selection = None
                self.imggrid.secondary_selection = set()
                self.imggrid.load_images()  # Refresh button highlights
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to copy labels: {str(e)}")
                print(f"Error copying labels: {str(e)}")            
       
        def search_images():
            
            if  self.imggrid.thread_running:
                QMessageBox.warning(self, "Warning", "Image loading is still in progress")
                return
            
            img_name = self.search_bar.text().strip()
            img_labels = self.drop_down.get_selected_items()
            df = pd.read_csv("output_cm.csv")
            all_label_columns = [col for col in df.columns if col not in ['Image Name', 'Signed','xtl', 'ytl', 'xbr', 'ybr']]

            # CASE 1: Only image name provided
            if img_name and not img_labels:
                filtered_df = df[df["Image Name"].str.contains(img_name)]
                all_imgs = filtered_df["Image Name"].tolist()
                # Then modify the line to:
                try:
                    self.current_base_index = self.image_names_df["Image Name"].tolist().index(img_name)
                except ValueError:
                    self.current_base_index = 0  # Default to first image if not found
                    print(f"Image {img_name} not found in image_names.csv")


            # CASE 2: Only labels provided
            elif not img_name and img_labels:
                positive_labels = set(img_labels)
                negative_labels = set(all_label_columns) - positive_labels
                query = " & ".join(
                    [f"(`{label}` == 1)" for label in positive_labels] +
                    [f"(`{label}` == 0)" for label in negative_labels]
                )
                filtered_df = df.query(query)
                all_imgs = filtered_df.sort_values('Signed', ascending=False)["Image Name"].tolist()

            # CASE 3: Both image name and labels provided
            elif img_name and img_labels:
                name_filtered = df[df["Image Name"].str.contains(img_name)]
                positive_labels = set(img_labels)
                negative_labels = set(all_label_columns) - positive_labels
                query = " & ".join(
                    [f"(`{label}` == 1)" for label in positive_labels] +
                    [f"(`{label}` == 0)" for label in negative_labels]
                )
                label_filtered = df.query(query)
                all_imgs = [img for img in name_filtered["Image Name"] if img in label_filtered["Image Name"].values]
                try:
                    self.current_base_index = self.image_names_df["Image Name"].tolist().index(img_name)
                except ValueError:
                    self.current_base_index = 0  # Default to first image if not found
                    print(f"Image {img_name} not found in image_names.csv")

            # CASE 4: Nothing provided
            else:
                all_imgs = df["Image Name"].tolist()
            
            # Optimized signed fraction calculation
            if len(all_imgs) > 0:
                # Use pandas isin() for fast filtering
                signed_df = df[df["Image Name"].isin(all_imgs)]
                signed_count = signed_df["Signed"].sum()  # Fast sum of 1s
                total_count = len(all_imgs)
                self.number_signed_status_label.setText(f"Fraction: {int(signed_count)}/{total_count}")
            else:
                self.number_signed_status_label.setText("Fraction: 0/0")
            self.number_signed_status_label.setStyleSheet("color: white;")

            # Update image grid
            self.imggrid.images = all_imgs
            self.imggrid.load_images()

        self.search_btn.clicked.connect(search_images)
        self.confirm_btn.clicked.connect(multi_change)
        self.deselect_btn.clicked.connect(deselect_images)

        # Create navigation buttons
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(0)
        nav_layout.setContentsMargins(0, 0, 0, 0)

        # Load base image names
        self.img_names = pd.read_csv("img_names.csv")
        self.current_base_index = 0  # Track current position in base images

        # Navigation buttons setup
        self.btn_jump_start = QPushButton("<<<")
        self.btn_jump_start.setFixedSize(40, 25)
        self.btn_jump_start.setToolTip("Jump to first image")
        self.btn_jump_start.clicked.connect(self.jump_to_start)
        
        self.btn_jump_back = QPushButton("<<")
        self.btn_jump_back.setFixedSize(40, 25)
        self.btn_jump_back.setToolTip("Jump back 10 base images")
        self.btn_jump_back.clicked.connect(self.jump_back)
        
        self.btn_prev = QPushButton("<")
        self.btn_prev.setFixedSize(30, 25)
        self.btn_prev.setToolTip("Previous base image")
        self.btn_prev.clicked.connect(self.previous_image)
        
        self.btn_next = QPushButton(">")
        self.btn_next.setFixedSize(30, 25)
        self.btn_next.setToolTip("Next base image")
        self.btn_next.clicked.connect(self.next_image)
        
        self.btn_jump_forward = QPushButton(">>")
        self.btn_jump_forward.setFixedSize(40, 25)
        self.btn_jump_forward.setToolTip("Jump forward 10 base images")
        self.btn_jump_forward.clicked.connect(self.jump_forward)
        
        self.btn_jump_end = QPushButton(">>>")
        self.btn_jump_end.setFixedSize(40, 25)
        self.btn_jump_end.setToolTip("Jump to last base image")
        self.btn_jump_end.clicked.connect(self.jump_to_end)

        # Add buttons to the layout
        nav_layout.addWidget(self.btn_jump_start)
        nav_layout.addWidget(self.btn_jump_back)
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addWidget(self.btn_next)
        nav_layout.addWidget(self.btn_jump_forward)
        nav_layout.addWidget(self.btn_jump_end)

        # Add navigation to viewer
        image_viewer_layout.addLayout(nav_layout)
        image_viewer_layout.addWidget(self.imggrid)

        # Connect image selection
        self.imggrid.image_selected.connect(self.handle_image_selection)

        # Setup image frame
        splitter_image_frame = QSplitter(Qt.Horizontal)
        splitter_image_frame.addWidget(self.image_panel)
        splitter_image_frame.addWidget(image_viewer)

        self.image_frame = QFrame()
        self.image_frame.setFrameShape(QFrame.Box)
        self.image_frame.setLineWidth(3)
        self.image_frame.setStyleSheet("background-color: lightgray;")
        self.image_frame.setLayout(QHBoxLayout())
        self.image_frame.layout().addWidget(splitter_image_frame)

    def jump_to_start(self):
        if  self.imggrid.thread_running:
            QMessageBox.warning(self, "Warning", "Image loading is still in progress")
            return
        
        if len(self.img_names) > 0:
            self.current_base_index = 0
            base_img = self.img_names.iloc[0]['Image Name']
            arr = [img for img in self.output_df['Image Name'] if base_img in img]
            self.imggrid.images = arr
            self.search_bar.setText(base_img)

            self.imggrid.load_images()

    def jump_back(self):
        if  self.imggrid.thread_running:
            QMessageBox.warning(self, "Warning", "Image loading is still in progress")
            return
        
        if len(self.img_names) > 0:
            self.current_base_index = max(0, self.current_base_index - 10)
            base_img = self.img_names.iloc[self.current_base_index]['Image Name']
            arr = [img for img in self.output_df['Image Name'] if base_img in img]
            self.imggrid.images = arr
            self.search_bar.setText(base_img)
            self.imggrid.load_images()

    def previous_image(self):
        if  self.imggrid.thread_running:
            QMessageBox.warning(self, "Warning", "Image loading is still in progress")
            return
        
        if len(self.img_names) > 0 and self.current_base_index > 0:
            self.current_base_index -= 1
            base_img = self.img_names.iloc[self.current_base_index]['Image Name']
            arr = [img for img in self.output_df['Image Name'] if base_img in img]
            self.imggrid.images = arr
            self.search_bar.setText(base_img)
            self.imggrid.load_images()

    def next_image(self):
        if  self.imggrid.thread_running:
            QMessageBox.warning(self, "Warning", "Image loading is still in progress")
            return
        

        if len(self.img_names) > 0 and self.current_base_index < len(self.img_names) - 1:
            self.current_base_index += 1
            print("0")
            base_img = self.img_names.iloc[self.current_base_index]['Image Name']
            print("1")
            arr = [img for img in self.output_df['Image Name'] if base_img in img]
            print("2")
            self.imggrid.images = arr
            print("3")
            self.search_bar.setText(base_img)
            print("4")
            self.imggrid.load_images()
            print("5")

    def jump_forward(self):
        if len(self.img_names) > 0:
            self.current_base_index = min(len(self.img_names) - 1, self.current_base_index + 10)
            base_img = self.img_names.iloc[self.current_base_index]['Image Name']
            arr = [img for img in self.output_df['Image Name'] if base_img in img]
            self.imggrid.images = arr
            self.search_bar.setText(base_img)
            self.imggrid.load_images()

    def jump_to_end(self):
        if len(self.img_names) > 0:
            self.current_base_index = len(self.img_names) - 1
            base_img = self.img_names.iloc[-1]['Image Name']
            arr = [img for img in self.output_df['Image Name'] if base_img in img]
            self.imggrid.images = arr
            self.search_bar.setText(base_img)
            self.imggrid.load_images()

    def handle_image_selection(self, img):
        print("handle_image_selection called ")
        """Handle image selection with proper error handling"""
        try:
            image_path = os.path.join("image_patches_20250426", img)
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found at: {image_path}")
            
            self.image_panel.filename = img
            self.image_panel.set_image(QPixmap(image_path))
            
            # Update signed status
            signed_status = self.get_signed_status(img)
            self.signed_status_label.setText(f"Signed: {'Yes' if signed_status else 'No'}")
            
            # Extract base image name by splitting at the 4th underscore
            parts = img.split('_')
            if len(parts) >= 5:  # Ensure there are at least 4 underscores
                base_image_name = '_'.join(parts[:len(parts)-4])  # Join first 4 parts
            else:
                base_image_name = img  # Fallback if format is unexpected
            
            # Remove file extension if present (e.g., ".jpg")
            base_image_name = base_image_name.split('.')[0]
            
            # Set the extracted name in the search bar
            self.search_bar.setText(base_image_name)
            
            # Update current base index if needed
            try:
                self.current_base_index = self.image_names_df["Image Name"].tolist().index(base_image_name)
            except ValueError:
                print(f"Base image {base_image_name} not found in index")
            
            self.update_all_label_frames(img)
            
            # Load any existing comment for this image
            self.load_comment_for_image(img)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load image: {str(e)}")
            print(f"Error loading image {img}: {str(e)}")

    def load_comment_for_image(self, img_name):
        """Load and display any existing comment for the image"""
        try:
            if os.path.exists(self.comments_file):
                comments_df = pd.read_csv(self.comments_file)
                comment_row = comments_df[comments_df["Image Name"] == img_name]
                
                if not comment_row.empty:
                    self.comment_textbox.setText(comment_row.iloc[0]["Comment"])
                else:
                    self.comment_textbox.clear()
                self.comment_textbox.setStyleSheet("color: white; background-color: black;")

        except Exception as e:
            print(f"Error loading comment: {str(e)}")
            self.comment_textbox.clear()


    def get_signed_status(self, img_name):
        """Check if image is signed in the output CSV"""
        try:
            df = pd.read_csv("output_cm.csv")
            img_row = df[df["Image Name"] == img_name]
            if not img_row.empty:
                return bool(img_row.iloc[0]["Signed"])
            return False
        except Exception as e:
            print(f"Error checking signed status: {str(e)}")
            return False



    def setup_navigation(self):
        """Setup navigation frame with just the confirm button"""
        self.nav_frame = QFrame()
        self.nav_frame.setFrameShape(QFrame.Box)
        self.nav_frame.setLineWidth(3)
        nav_layout = QHBoxLayout(self.nav_frame)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setAlignment(Qt.AlignLeft)

        # Add signed status label
        self.signed_status_label = QLabel("Signed: Unknown")
        self.number_signed_status_label = QLabel("Fraction")
        
        # Add confirm button
        nav_layout.addWidget(self.create_confirm_button())
        nav_layout.addWidget(self.signed_status_label)
        nav_layout.addWidget(self.number_signed_status_label)
        
        # Add comment section
        self.comment_textbox = QLineEdit()
        self.comment_textbox.setPlaceholderText("Add comment...")
        self.comment_textbox.setStyleSheet("color: white; background-color: black;")

        
        self.comment_textbox.setFixedWidth(600)
        self.save_comment_btn = QPushButton("Save Comment")
        self.save_comment_btn.setFixedWidth(100)
        self.save_comment_btn.clicked.connect(self.save_comment)
        self.save_comment_btn.setStyleSheet("color: white; background-color: black;")
        
        nav_layout.addWidget(QLabel("Comments:"))
        nav_layout.addWidget(self.comment_textbox)
        nav_layout.addWidget(self.save_comment_btn)
        
        # Load existing comments file or create if doesn't exist
        self.comments_file = "comments.csv"
        if not os.path.exists(self.comments_file):
            pd.DataFrame(columns=["Image Name", "Comment"]).to_csv(self.comments_file, index=False)

    def setup_label_sections(self):
        print("setup_label_sections called ")
        """Setup all label-related sections"""
        self.label_frame = QFrame()
        self.label_frame.setFrameShape(QFrame.Box)
        self.label_frame.setLineWidth(3)
        self.label_frame.setStyleSheet("background-color: black;")
        self.label_layout = QVBoxLayout()
        self.label_frame.setLayout(self.label_layout)

        # Initialize label frames
        initial_img = "20240302_095020_0_0_373_346.jpg"
        self.label_frame_delete = ActiveLabels(initial_img)
        self.label_frame_change = ChangeFrame(initial_img)
        self.label_frame_delete.selection_change.connect(self.handle_deletion_selection)
        self.label_frame_change.all_labels_selection_changed.connect(
        self.handle_all_labels_selection)
    
        self.label_frame_add = ButtonGrid()
        self.label_frame_add.set_buttons_disabled(self.label_frame_delete.btn_list)
        # Add sections to label frame
        self.label_layout.addWidget(self.nav_frame)
        self.label_layout.addWidget(self.label_frame_delete)
        self.label_layout.addWidget(self.label_frame_change)
        self.label_layout.addWidget(self.label_frame_add)

    def update_all_label_frames(self, img):
        print("update_all_label_frames called ")
        """Update all label frames when image changes"""
        try:
            self.update_label_frame_delete(img)
            self.update_change_frame(img)
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Failed to update labels: {str(e)}")
            print(f"Error updating labels for {img}: {str(e)}")

    def update_label_frame_delete(self, img):
        print("update_label_frame_delete called ")
        """Update the delete labels frame"""
        self.label_layout.removeWidget(self.label_frame_delete)
        self.label_frame_delete.deleteLater()
        self.label_frame_delete = ActiveLabels(img)
        self.label_layout.insertWidget(1, self.label_frame_delete)


    def save_comment(self):
        """Save comment for current image to CSV file"""
        current_image = self.imggrid.img_start
        if not current_image:
            QMessageBox.warning(self, "Warning", "No image selected")
            return
            
        comment = self.comment_textbox.text().strip()
        if not comment:
            QMessageBox.warning(self, "Warning", "Comment cannot be empty")
            return
            
        try:
            # Read existing comments
            comments_df = pd.read_csv(self.comments_file)
            
            # Remove any existing entry for this image
            comments_df = comments_df[comments_df["Image Name"] != current_image]
            
            # Add new comment
            new_entry = pd.DataFrame([[current_image, comment]], 
                                columns=["Image Name", "Comment"])
            comments_df = pd.concat([comments_df, new_entry], ignore_index=True)
            
            # Save back to file
            comments_df.to_csv(self.comments_file, index=False)
            


            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save comment: {str(e)}")
            print(f"Error saving comment: {str(e)}")

    def handle_deletion_selection(self, selected_labels):
        print("handle_deletion_selection called")
        """
        Handle when labels are selected/deselected for deletion in ActiveLabels frame.
        Toggles the enabled state of corresponding buttons in ChangeFrame.
        """
        # Check if change frame exists and has buttons
        if not hasattr(self, 'label_frame_change') or not hasattr(self.label_frame_change, 'current_buttons'):
            return
            
        current_buttons = self.label_frame_change.current_buttons
        
        # Create a mapping of button text to button object
        button_map = {btn.text(): btn for btn in current_buttons}
        
        # Process all current buttons
        for btn_text, button in button_map.items():
            if btn_text in selected_labels:
                # Label is selected for deletion - disable it
                button.setDisabled(True)
                button.setStyleSheet("background-color: #ffcccc;")  # Light red
                
                # If this button was selected in change frame, deselect it
                if (hasattr(self.label_frame_change, 'selected_current_label') and 
                    button == self.label_frame_change.selected_current_label):
                    self.label_frame_change.deselect_current_label(button)
            else:
                # Label is NOT selected for deletion - enable it
                button.setDisabled(False)
                
                # Only reset style if not currently selected in change frame
                if (not hasattr(self.label_frame_change, 'selected_current_label') or 
                    button != self.label_frame_change.selected_current_label):
                    button.setStyleSheet("background-color: lightgray;")
                else:
                    # If it's the selected button, keep its selection color
                    if (hasattr(self.label_frame_change, 'current_label_colors') and 
                        button in self.label_frame_change.current_label_colors):
                        color = self.label_frame_change.current_label_colors[button]
                        button.setStyleSheet(f"background-color: {color};")


    def handle_all_labels_selection(self, selected_all_labels):
        print("handle_all_labels_selection called ")
        """
        Disable buttons in Add section that are selected as change targets in all_labels
        """
        if not hasattr(self, 'label_frame_add'):
            return
        
        print("Handling all labels selection:", selected_all_labels)
        # Get all buttons in the Add section
        add_buttons = self.label_frame_add.buttons  # Assuming ButtonGrid has a 'buttons' attribute
        print(selected_all_labels)
        # Create mapping of button texts to buttons
        button_map = {btn.text(): btn for btn in add_buttons}
        print("1")
        current_buttons = [btn.text() for btn in self.label_frame_change.current_buttons]
        print(current_buttons)
        # Toggle disabled state
        for btn_text, button in button_map.items():
            if btn_text in selected_all_labels:
                # Disable buttons that are selected as change targets
                button.setDisabled(True)
                button.setStyleSheet("background-color: #ffcccc;")

            elif btn_text in current_buttons:
                print(f"re--enabl : {button.text()}")
                button.setDisabled(True)
                button.setStyleSheet("background-color: red")
            else:
                # Re-enable buttons that aren't change targets
                button.setDisabled(False)
                button.setStyleSheet("background-color: lightgray;")
        



    def update_change_frame(self, img):
        print("update_change_frame called")
        """Update the change labels frame"""
        # Remove old frame
        self.label_layout.removeWidget(self.label_frame_change)
        self.label_frame_change.deleteLater()
        
        # Create new frame
        self.label_frame_change = ChangeFrame(img)
        self.label_layout.insertWidget(2, self.label_frame_change)
        
        # Reconnect ALL signals properly
        self.label_frame_delete.selection_change.connect(self.handle_deletion_selection)
        self.label_frame_change.all_labels_selection_changed.connect(
            self.handle_all_labels_selection
        )
        
        # Force immediate layout update
        self.label_frame_change.setVisible(True)
        self.label_frame_change.updateGeometry()
        self.label_frame_change.resizeEvent(None)
        
        # Sync current deletion selections to the new frame
        if hasattr(self, 'label_frame_delete'):
            current_selections = list(self.label_frame_delete.selected_buttons)
            self.handle_deletion_selection(current_selections)  # This will update the new frame
            
        # Sync all_labels selections
        if hasattr(self.label_frame_change, 'reverse_mapping'):
            selected_all_labels = [btn.text() for btn in self.label_frame_change.reverse_mapping.keys()]
            self.handle_all_labels_selection(selected_all_labels)
            
        

    def get_current_labels(self, img):
        print("get_current_labels called ")
        """Helper to get current labels for an image"""
        labels_df = pd.read_csv("output_cm.csv")
        img_row = labels_df[labels_df["Image Name"] == img]
        
        if img_row.empty:
            return []
            
        img_row = img_row.iloc[0]
        current_labels = []
        label_to_short = dict(zip(self.buttons_df["xml_labels"], self.buttons_df["short_forms"]))
        
        for label, value in img_row.items():
            if label == "Image Name":
                continue
            if value == 1 and label in label_to_short:
                current_labels.append(label_to_short[label])
                
        return current_labels

    def create_confirm_button(self):
        """Create and configure the confirm button"""
        self.conf_button = QPushButton('CONFIRM')
        self.conf_button.setStyleSheet("background-color: lightgreen;")
        self.conf_button.setFixedSize(100, 30)
        self.conf_button.clicked.connect(self.on_confirm)
        return self.conf_button

    def on_confirm(self):
        """Handle confirmation of label changes"""
        image_name = self.imggrid.img_start
        if not image_name:
            QMessageBox.warning(self, "Warning", "No image selected")
            return

        try:
            df = pd.read_csv("output_cm.csv")
            short_to_full = dict(zip(self.buttons_df["short_forms"], self.buttons_df["xml_labels"]))
            full_to_short = dict(zip(self.buttons_df["xml_labels"], self.buttons_df["short_forms"]))

            row_idx = df[df["Image Name"] == image_name].index
            if row_idx.empty:
                QMessageBox.warning(self, "Warning", f"Image {image_name} not found in CSV")
                return
            row_idx = row_idx[0]

            print("Processing additions:", self.label_frame_add.selected_buttons)
            # Process additions
            for short_label in self.label_frame_add.selected_buttons:
                full_label = short_to_full.get(short_label)
                if full_label in df.columns:
                    df.at[row_idx, full_label] = 1
            self.label_frame_add.selected_buttons.clear()  # Clear after processing

            print("Processing deletions:", self.label_frame_delete.selected_buttons)
            # Process deletions
            for short_label in self.label_frame_delete.selected_buttons:
                full_label = short_to_full.get(short_label)
                if full_label in df.columns:
                    df.at[row_idx, full_label] = 0
            
            self.label_frame_delete.selected_buttons.clear()  # Clear after processing

            # Process label changes
            for current_button, new_button in self.label_frame_change.color_mapping.items():
                current_short = current_button.text()
                new_short = new_button.text()
                current_full = short_to_full.get(current_short)
                new_full = short_to_full.get(new_short)
                
                if current_full in df.columns and new_full in df.columns:
                    df.at[row_idx, current_full] = 0
                    df.at[row_idx, new_full] = 1
            
            df.at[row_idx, "Signed"] = 1
            df.to_csv("output_cm.csv", index=False)
            
            # Clear mappings
            self.label_frame_change.color_mapping.clear()
            self.label_frame_change.reverse_mapping.clear()
            self.label_frame_change.selected_current_label = None
            
            # Update tooltip for the image button
            for btn in self.imggrid.buttons:
                if btn.property("img_file") == image_name:
                    # Get all active labels (columns with value 1)
                    img_row = df[df["Image Name"] == image_name].iloc[0]
                    label_cols = [col for col in df.columns 
                                if col not in ['Image Name', 'Signed', 'xtl', 'ytl', 'xbr', 'ybr']]
                    active_labels = [col for col in label_cols if img_row[col] == 1]
                    
                    # Set tooltip with filename and active labels
                    tooltip = f"{image_name}\nLabels: {', '.join(active_labels)}" if active_labels else image_name
                    btn.setToolTip(tooltip)
                    break
            self.delegate.output_df = pd.read_csv("output_cm.csv")  # Update delegate's cached DataFrame
            signed_status = self.get_signed_status(image_name)
            self.signed_status_label.setText(f"Signed: {'Yes' if signed_status else 'No'}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save changes: {str(e)}")
            print(f"Error saving changes: {str(e)}")


    def setup_main_layout(self):
        """Setup the main window layout"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.label_frame)

        main_splitter = QSplitter(Qt.Vertical)
        main_splitter.addWidget(self.image_frame)
        main_splitter.addWidget(scroll_area)
        main_splitter.setSizes([500, 300])

        layout = QVBoxLayout(self)
        layout.addWidget(main_splitter)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())