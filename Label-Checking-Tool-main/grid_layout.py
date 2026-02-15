from PyQt5.QtWidgets import QWidget, QGridLayout
from PyQt5.QtCore import QSize, Qt, pyqtSignal

PADDING = 10  # Space between items

class DynamicGridLayout(QWidget):
    imageClicked = pyqtSignal(str) # Custom signal to emit the clicked image name
    def __init__(self, parent=None):
        super().__init__(parent)

        # Grid layout setup
        self.grid_layout = QGridLayout(self)
        self.grid_layout.setSpacing(PADDING)
        self.grid_layout.setContentsMargins(PADDING, PADDING, PADDING, PADDING)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.setLayout(self.grid_layout)

    def add_widget(self, widget):
        """Adds a widget to the grid layout."""
        self.grid_layout.addWidget(widget)

    def relayout(self):
        """Relayout the grid based on available width."""
        area_width = self.width()
        columns = max(1, area_width // (widget.sizeHint().width() + PADDING))

        row, col = 0, 0
        for i in range(self.grid_layout.count()):
            item = self.grid_layout.itemAt(i)
            widget = item.widget()

            if widget:
                self.grid_layout.addWidget(widget, row, col)
                col += 1
                if col >= columns:
                    col = 0
                    row += 1

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.relayout()
