import os
import sys
import pandas as pd
from functools import partial
from PyQt5.QtWidgets import (
    QApplication, QWidget, QScrollArea, QVBoxLayout, QGridLayout, QPushButton, QLabel
)
from PyQt5.QtCore import QSize, Qt

BUTTON_SIZE = QSize(160, 30)
PADDING = 10  # space between buttons

class ButtonGrid(QWidget):
    def __init__(self):
        super().__init__()
        self.buttons = []  # List to store button references
        self.selected_buttons = []  # List to track selected buttons

        # Load button data
        self.buttons_df = pd.read_csv("buttons.csv")
        self.btn_list = self.buttons_df["short_forms"].tolist()

        # Main layout setup
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Add section label at the top
        section_label = QLabel("Add Section")
        self.layout.addWidget(section_label)

        # Scroll area setup
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.layout.addWidget(self.scroll_area)

        # Container widget for grid
        self.container = QWidget()
        self.grid_layout = QGridLayout(self.container)
        self.grid_layout.setSpacing(PADDING)
        self.grid_layout.setContentsMargins(PADDING, PADDING, PADDING, PADDING)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.scroll_area.setWidget(self.container)

        # Load buttons
        self.load_buttons()

    def load_buttons(self):
        print("load_buttons")
        for short_name in self.btn_list:
            button = QPushButton(short_name)
            button.setFixedSize(BUTTON_SIZE)
            button.setStyleSheet("background-color: lightgray;")
            button.clicked.connect(partial(self.on_button_click, button, short_name))
            self.buttons.append(button)

        self.relayout_buttons()

    def relayout_buttons(self):
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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.relayout_buttons()

    def on_button_click(self, button, name):
        if name in self.selected_buttons:
            self.selected_buttons.remove(name)
            button.setStyleSheet("background-color: lightgray;")
        else:
            self.selected_buttons.append(name)
            button.setStyleSheet("border: 2px solid yellow; background-color: lightblue;")
        print("Selected:", self.selected_buttons)

    def set_buttons_disabled(self, button_names):
        """
        Disable (make unclickable) buttons whose names are in button_names.
        Disabled buttons will be colored red; others will be enabled and use default color.
        """
        for button, name in zip(self.buttons, self.btn_list):
            if name in button_names:
                button.setDisabled(True)
                button.setStyleSheet("background-color: red;")
            else:
                button.setDisabled(False)
                button.setStyleSheet("background-color: lightgray;")




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ButtonGrid()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())
