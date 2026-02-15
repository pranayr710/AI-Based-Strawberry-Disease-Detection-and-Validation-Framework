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
from PyQt5.QtWidgets import QLabel, QStyledItemDelegate
from PyQt5.QtGui import QTextDocument



class SignedHighlightDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.valid_color = "#a8e6cf"  # Light green for fully signed

        # ✅ Load data once and keep it cached
        self.output_df = pd.read_csv("output_cm.csv")
        self.img_names_df = pd.read_csv("img_names.csv")

    def is_fully_signed(self, base_image_name):
        """Check if ALL patches for this base image have Signed=1"""
        base_name_lower = base_image_name.lower()
        patch_images = [
            img for img in self.output_df["Image Name"]
            if img.lower().startswith(base_name_lower)
        ]
        
        if not patch_images:
            return False
            
        signed_status = self.output_df[
            self.output_df["Image Name"].isin(patch_images)
        ]["Signed"]
        
        return all(signed_status == 1)

    
    def paint(self, painter, option, index):
        text = index.data(Qt.DisplayRole)
        
        # Determine if this base image is fully signed
        is_signed = self.is_fully_signed(text)
        
        # Only apply styling if fully signed
        if is_signed:
            html = f'<span style="background-color:{self.valid_color}">{text}</span>'
        else:
            html = text  # No styling for unsigned images
        
        # Render the HTML or plain text
        doc = QTextDocument()
        doc.setHtml(html)
        
        painter.save()
        painter.translate(option.rect.topLeft())
        doc.drawContents(painter)
        painter.restore()
