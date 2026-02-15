from PyQt5.QtWidgets import QApplication, QWidget, QFrame, QVBoxLayout, QSplitter,QHBoxLayout,QScrollArea
from PyQt5.QtCore import Qt
import sys
from image_panel import ImageViewer
from PyQt5.QtGui import QPainter
app = QApplication(sys.argv)

# Main window
window = QWidget()
window.setWindowTitle("Resizable Frames with Splitter")
window.setGeometry(100, 100, 400, 400)

# Frame 1
image_frame = QFrame()
image_frame.setFrameShape(QFrame.Box)
image_frame.setLineWidth(3)
image_frame.setStyleSheet("background-color: lightgray;")

image_frame_painter = QPainter(image_frame)
image_frame_layout = QHBoxLayout()
image_frame.setLayout(image_frame_layout)

window.show()
sys.exit(app.exec_())