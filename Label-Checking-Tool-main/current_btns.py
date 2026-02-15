import os
import sys
import pandas as pd
from functools import partial
from PyQt5.QtWidgets import (
    QApplication, QWidget, QScrollArea, QVBoxLayout, QGridLayout, QPushButton, QLabel
)
from PyQt5.QtCore import QSize, Qt, pyqtSignal

BUTTON_SIZE = QSize(160, 30)
PADDING = 10  # No spacing between buttons


# Custom scroll area that triggers relayout on resize
class ResizableScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.parent():
            self.parent().relayout_buttons()


class ActiveLabels(QWidget):
    selection_change = pyqtSignal(list)
    def __init__(self, img_name):
        super().__init__()
        self.setWindowTitle(f"Labels for {img_name}")
        self.selected_buttons = []

        # Load button definitions
        self.buttons_df = pd.read_csv("buttons.csv")
        self.label_to_short = dict(zip(self.buttons_df["xml_labels"], self.buttons_df["short_forms"]))

        # Load image-specific label info
        labels_df = pd.read_csv("output_cm.csv")
        img_row = labels_df[labels_df["Image Name"] == img_name]

        if img_row.empty:
            raise ValueError(f"No data found for image: {img_name}")

        img_row = img_row.iloc[0]

        # Get only the short forms of labels which have value == 1
        self.btn_list = []
        for label, value in img_row.items():
            if label == "Image Name":
                continue
            if value == 1 and label in self.label_to_short:
                self.btn_list.append(self.label_to_short[label])

        self.selected_buttons = []

        # Main layout
        self.layout = QVBoxLayout(self)

        # Scroll area
        self.scroll_area = ResizableScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.layout.addWidget(self.scroll_area)

        # Container and layout inside scroll area
        self.container = QWidget()
        self.wrapper_layout = QVBoxLayout(self.container)

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.grid_layout.setSpacing(PADDING)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)

        self.wrapper_layout.addWidget(QLabel("Delete Section"))
        self.wrapper_layout.addWidget(self.grid_container)
        
        self.wrapper_layout.addStretch(1)

        self.scroll_area.setWidget(self.container)

        # Button list
        self.buttons = []
        self.load_buttons()

    def load_buttons(self):
        for short_name in self.btn_list:
            button = QPushButton(short_name)
            button.setFixedSize(BUTTON_SIZE)
            button.setStyleSheet("background-color: lightgray;")
            button.clicked.connect(partial(self.on_button_click, button, short_name))
            self.buttons.append(button)

        self.relayout_buttons()

    def relayout_buttons(self):
        # Clear existing layout
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)

        area_width = self.scroll_area.viewport().width()
        columns = max(1, area_width // (BUTTON_SIZE.width() + PADDING))

        row, col = 0, 0
        for button in self.buttons:
            self.grid_layout.addWidget(button, row, col)
            col += 1
            if col >= columns:
                col = 0
                row += 1

    def on_button_click(self, button, name):
        if name in self.selected_buttons:
            self.selected_buttons.remove(name)
            button.setStyleSheet("background-color: lightgray;")
        else:
            self.selected_buttons.append(name)
            button.setStyleSheet("border: 2px solid yellow; background-color: lightblue;")

        print("Selected:", self.selected_buttons)
        self.selection_change.emit(self.selected_buttons)  # 🔥 emit signal here


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ActiveLabels("20240302_095020_660_941_880_1149.jpg")
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())
