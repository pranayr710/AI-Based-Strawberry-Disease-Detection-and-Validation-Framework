import sys
import random
import colorsys
import pandas as pd
from functools import partial
from PyQt5.QtWidgets import (
    QApplication, QWidget, QScrollArea, QVBoxLayout, QGridLayout, QPushButton, QLabel, QHBoxLayout
)
from PyQt5.QtCore import QSize, Qt, pyqtSignal

BUTTON_SIZE = QSize(160, 30)
PADDING = 10  # space between buttons


class ChangeFrame(QWidget):
    all_labels_selection_changed = pyqtSignal(list)
    current_label_deselected = pyqtSignal(str)

    def __init__(self, img_name):
        super().__init__()
        self.setWindowTitle("Change Frame - all_labels & current Labels")
        self.selected_current_label = None
        self.current_label_colors = {}
        self.all_label_colors = {}
        self.color_mapping = {}
        self.reverse_mapping = {}

        # Load data
        self.buttons_df = pd.read_csv("buttons.csv")
        self.all_labels_btn_list = self.buttons_df["short_forms"].tolist()
        self.label_to_short = dict(zip(self.buttons_df["xml_labels"], self.buttons_df["short_forms"]))
        
        # Get current labels for image
        labels_df = pd.read_csv("output_cm.csv")
        img_row = labels_df[labels_df["Image Name"] == img_name]
        if img_row.empty:
            raise ValueError(f"No data found for image: {img_name}")
        
        img_row = img_row.iloc[0]
        self.current_btn_list = [
            self.label_to_short[label] 
            for label, value in img_row.items() 
            if label != "Image Name" and value == 1 and label in self.label_to_short
        ]

        # Setup UI
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(PADDING, PADDING, PADDING, PADDING)
        main_layout.setSpacing(PADDING)

        # Current labels section
        current_widget = QWidget()
        current_layout = QVBoxLayout(current_widget)
        current_layout.setContentsMargins(0, 0, 0, 0)
        current_layout.setSpacing(PADDING)
        current_layout.addWidget(QLabel("Change Current Labels"))
        
        self.current_scroll_area = QScrollArea()
        self.current_scroll_area.setWidgetResizable(True)
        current_layout.addWidget(self.current_scroll_area)
        
        self.current_container = QWidget()
        self.current_grid_layout = QGridLayout(self.current_container)
        self.current_grid_layout.setSpacing(PADDING)
        self.current_grid_layout.setContentsMargins(PADDING, PADDING, PADDING, PADDING)
        self.current_grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.current_scroll_area.setWidget(self.current_container)

        # all_labels section
        all_labels_widget = QWidget()
        all_labels_layout = QVBoxLayout(all_labels_widget)
        all_labels_layout.setContentsMargins(0, 0, 0, 0)
        all_labels_layout.setSpacing(PADDING)
        all_labels_layout.addWidget(QLabel("Available Labels"))
        
        self.all_labels_scroll_area = QScrollArea()
        self.all_labels_scroll_area.setWidgetResizable(True)
        all_labels_layout.addWidget(self.all_labels_scroll_area)
        
        self.all_labels_container = QWidget()
        self.all_labels_grid_layout = QGridLayout(self.all_labels_container)
        self.all_labels_grid_layout.setSpacing(PADDING)
        self.all_labels_grid_layout.setContentsMargins(PADDING, PADDING, PADDING, PADDING)
        self.all_labels_grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.all_labels_scroll_area.setWidget(self.all_labels_container)

        main_layout.addWidget(current_widget)
        main_layout.addWidget(all_labels_widget)

        # Create buttons
        self.all_labels_buttons = []
        self.current_buttons = []
        self.load_all_labels_buttons()
        self.relayout_buttons(self.all_labels_grid_layout, self.all_labels_buttons, self.all_labels_scroll_area)
        self.load_current_buttons()
        self.resize(1000, 600)

    def load_all_labels_buttons(self):
        for short_name in self.all_labels_btn_list:
            btn = QPushButton(short_name)
            btn.setFixedSize(BUTTON_SIZE)
            if short_name in self.current_btn_list:
                btn.setDisabled(True)
                btn.setStyleSheet("background-color: red;")
            else:
                btn.setStyleSheet("background-color: lightgray;")
            btn.clicked.connect(partial(self.all_labels_button_clicked, btn))
            self.all_labels_buttons.append(btn)
        self.relayout_buttons(self.all_labels_grid_layout, self.all_labels_buttons, self.all_labels_scroll_area)

    def load_current_buttons(self):
        for short_name in self.current_btn_list:
            btn = QPushButton(short_name)
            btn.setFixedSize(BUTTON_SIZE)
            btn.setStyleSheet("background-color: lightgray;")
            btn.clicked.connect(partial(self.current_button_clicked, btn))
            self.current_buttons.append(btn)
        self.relayout_buttons(self.current_grid_layout, self.current_buttons, self.current_scroll_area)

    def relayout_buttons(self, layout, buttons, scroll_area):
        # Clear the layout first
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Calculate available width (accounting for scrollbar if present)
        viewport_width = scroll_area.viewport().width()
        button_width = BUTTON_SIZE.width() + PADDING
        columns = max(1, viewport_width // button_width)

        row, col = 0, 0
        for button in buttons:
            layout.addWidget(button, row, col)
            col += 1
            if col >= columns:
                col = 0
                row += 1

        # Update the container size
        rows = (len(buttons) + columns - 1) // columns
        height = rows * (BUTTON_SIZE.height() + PADDING) + PADDING
        layout.parent().setMinimumHeight(height)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Always relayout buttons on resize
        self.relayout_buttons(self.all_labels_grid_layout, 
                            self.all_labels_buttons, 
                            self.all_labels_scroll_area)
        self.relayout_buttons(self.current_grid_layout,
                            self.current_buttons,
                            self.current_scroll_area)

    def current_button_clicked(self, button):
        if self.selected_current_label == button:
            self.deselect_current_label(button)
            return

        if self.selected_current_label:
            prev_button = self.selected_current_label
            if prev_button not in self.color_mapping:
                prev_button.setStyleSheet("background-color: lightgray;")
                if prev_button in self.current_label_colors:
                    del self.current_label_colors[prev_button]
            else:
                prev_color = self.current_label_colors.get(prev_button, 'lightgray')
                prev_button.setStyleSheet(f"background-color: {prev_color};")

        self.selected_current_label = button
        if button not in self.current_label_colors:
            self.current_label_colors[button] = self.generate_distinct_color()
        button.setStyleSheet(f"background-color: {self.current_label_colors[button]};")

    def deselect_current_label(self, button):
        button.setStyleSheet("background-color: lightgray;")
        self.current_label_deselected.emit(button.text())
        self.selected_current_label = None
        
        if button in self.color_mapping:
            all_labels_button = self.color_mapping[button]
            all_labels_button.setStyleSheet("background-color: lightgray;")
            del self.reverse_mapping[all_labels_button]
            del self.color_mapping[button]
            del self.all_label_colors[all_labels_button]
            selected_all_labels = list(self.reverse_mapping.keys())
            self.all_labels_selection_changed.emit([btn.text() for btn in selected_all_labels])
        
        if button in self.current_label_colors:
            color = self.current_label_colors[button]
            if color not in self.all_label_colors.values():
                del self.current_label_colors[button]

    def all_labels_button_clicked(self, button):
        if not self.selected_current_label:
            return
        
        current_button = self.selected_current_label
        current_color = self.current_label_colors[current_button]
        
        if current_button in self.color_mapping and self.color_mapping[current_button] == button:
            button.setStyleSheet("background-color: lightgray;")
            del self.color_mapping[current_button]
            del self.reverse_mapping[button]
            del self.all_label_colors[button]
            selected_all_labels = list(self.reverse_mapping.keys())
            self.all_labels_selection_changed.emit([btn.text() for btn in selected_all_labels])
            return
        
        if button in self.reverse_mapping:
            old_current_button = self.reverse_mapping[button]
            old_current_button.setStyleSheet("background-color: lightgray;")
            del self.color_mapping[old_current_button]
        
        if current_button in self.color_mapping:
            prev_all_labels_button = self.color_mapping[current_button]
            prev_all_labels_button.setStyleSheet("background-color: lightgray;")
            del self.reverse_mapping[prev_all_labels_button]
            del self.all_label_colors[prev_all_labels_button]
        
        self.color_mapping[current_button] = button
        self.reverse_mapping[button] = current_button
        button.setStyleSheet(f"background-color: {current_color};")
        self.all_label_colors[button] = current_color
        
        selected_all_labels = list(self.reverse_mapping.keys())
        self.all_labels_selection_changed.emit([btn.text() for btn in selected_all_labels])

    def generate_distinct_color(self):
        h = random.random()
        while 0.95 < h < 1.0 or 0.0 <= h < 0.05:
            h = random.random()
        s = 0.7 + random.random() * 0.3
        v = 0.7 + random.random() * 0.3
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255))

    def set_buttons_disabled_all_labels(self, button_names):
        for button in self.all_labels_buttons:
            if button.text() in button_names:
                button.setDisabled(True)
                button.setStyleSheet("background-color: red;")
            else:
                button.setDisabled(False)
                if button not in self.reverse_mapping:
                    button.setStyleSheet("background-color: lightgray;")
                else:
                    button.setStyleSheet(f"background-color: {self.all_label_colors.get(button, 'lightblue')};")

    def set_buttons_disabled_current_labels(self, button_names):
        for button in self.current_buttons:
            if button.text() in button_names:
                button.setDisabled(True)
                button.setStyleSheet("background-color: red;")
                if button == self.selected_current_label:
                    self.deselect_current_label(button)
            else:
                button.setDisabled(False)
                if button != self.selected_current_label:
                    button.setStyleSheet("background-color: lightgray;")
                else:
                    button.setStyleSheet(f"background-color: {self.current_label_colors.get(button, 'lightblue')};")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChangeFrame("20240302_095020_660_941_880_1149.jpg")
    window.show()
    sys.exit(app.exec_())