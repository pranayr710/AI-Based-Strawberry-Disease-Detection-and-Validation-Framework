import os
import sys
import pandas as pd
from functools import partial
from PyQt5.QtWidgets import (
    QApplication, QWidget, QScrollArea, QVBoxLayout, QGridLayout, QPushButton
)
from PyQt5.QtCore import QSize, Qt

BUTTON_SIZE = QSize(120, 60)
PADDING = 10  # space between buttons

class ButtonGrid(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Dynamic Button Grid")
        self.buttons_df = pd.read_csv("buttons.csv")
        self.btn_list = self.buttons_df["short_forms"].tolist()

        self.selected_buttons = []  # allow multiple selected buttons

        self.layout = QVBoxLayout(self)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.layout.addWidget(self.scroll_area)

        self.container = QWidget()
        self.grid_layout = QGridLayout(self.container)
        self.scroll_area.setWidget(self.container)

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
            # Unselect
            self.selected_buttons.remove(name)
            button.setStyleSheet("background-color: lightgray;")
        else:
            # Select
            self.selected_buttons.append(name)
            button.setStyleSheet("border: 2px solid yellow; background-color: lightblue;")

        print("Selected:", self.selected_buttons)  # Debug print

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ButtonGrid()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())
