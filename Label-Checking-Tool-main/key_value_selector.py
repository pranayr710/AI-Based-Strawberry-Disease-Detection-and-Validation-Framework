import random
from PyQt5.QtWidgets import QPushButton, QVBoxLayout, QWidget
class AtomicKeyValueSelector:
    def __init__(self):
        self._selected_key = None
        self._key_buttons = {}
        self._value_buttons = {}
        self._color_map = {}
        self._current_color = None

    def register_buttons(self, key_buttons, value_buttons):
        """Connect your existing button widgets"""
        self._key_buttons = {btn.text(): btn for btn in key_buttons}
        self._value_buttons = {btn.text(): btn for btn in value_buttons}

    def select_key(self, key_text):
        """Handle key selection with automatic coloring"""
        if self._selected_key:
            self._key_buttons[self._selected_key].setStyleSheet("")
            
        self._selected_key = key_text
        self._current_color = f"background-color: #{random.randint(0x99,0xEE):02x}{random.randint(0x99,0xEE):02x}{random.randint(0x99,0xEE):02x};"
        self._key_buttons[key_text].setStyleSheet(self._current_color)

    def select_value(self, value_text):
        """Handle value selection if valid key exists"""
        if not self._selected_key:
            return False
            
        self._value_buttons[value_text].setStyleSheet(self._current_color)
        self._color_map[self._selected_key] = (value_text, self._current_color)
        self._selected_key = None
        return True

    def get_selections(self):
        return self._color_map.copy()