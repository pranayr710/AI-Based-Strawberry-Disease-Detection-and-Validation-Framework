from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QComboBox, QPushButton, QListView, QLineEdit
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QModelIndex


class CustomMultiSelectComboBox(QComboBox):
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.setView(QListView())
        self.model = QStandardItemModel()
        self.setModel(self.model)
        
        self.items = items  # Store the items for reference

        # Add placeholder
        self.placeholder = QStandardItem("Select an option")
        self.placeholder.setFlags(Qt.ItemIsEnabled)
        self.model.appendRow(self.placeholder)

        # Add checkable items
        for label in items:
            item = QStandardItem(label)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.model.appendRow(item)

        self.setCurrentIndex(0)
        self.view().pressed.connect(self.toggle_item)

    def toggle_item(self, index: QModelIndex):
        if index.row() == 0:
            return
        item = self.model.itemFromIndex(index)
        item.setCheckState(Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked)
        self.update_display_text()
        
    def update_display_text(self):
        selected = self.get_selected_items()
        if selected:
            display_text = ", ".join(selected)
            # Temporarily change the placeholder to show selections
            self.placeholder.setText(display_text)
        else:
            self.placeholder.setText("Select an option")

    def get_selected_items(self):
        selected = []
        for row in range(1, self.model.rowCount()):
            item = self.model.item(row)
            if item.checkState() == Qt.Checked:
                selected.append(item.text())
        return selected

    def reset_all(self):
        for row in range(1, self.model.rowCount()):
            item = self.model.item(row)
            item.setCheckState(Qt.Unchecked)
            item.setBackground(Qt.white)
        self.update_display_text()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ComboBox with Search")
        layout = QVBoxLayout()

        # Search Bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Type here to search...")
        layout.addWidget(self.search_bar)

        # Custom ComboBox
        self.combo = CustomMultiSelectComboBox(["Apple", "Banana", "Cherry", "Grapes", "Mango"])
        layout.addWidget(self.combo)

        # Button to show selected + searched text
        btn = QPushButton("Print Info")
        btn.clicked.connect(self.print_info)
        layout.addWidget(btn)

        self.setLayout(layout)

    def print_info(self):
        print("Search Input:", self.search_bar.text() or "")
        print("Selected:", self.combo.get_selected_items())


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()