import sys
from PyQt5.QtWidgets import QSlider
from PyQt5.QtCore import Qt, QRect, QPoint, QSize, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPolygon

class AnnotatedSlider(QSlider):
    img_changed = pyqtSignal(str)
    
    def __init__(self, all_images, checked_images=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setOrientation(Qt.Horizontal)
        self.all_images = all_images
        self.checked_images = set(checked_images or [])
        self.setMinimum(0)
        self.setMaximum(len(self.all_images) - 1)
        self.setTickPosition(QSlider.TicksBelow)
        self.setTickInterval(1)
        self.groove_height = 10
        self.marker_width = 10
        self.thumb_height = 20
        
        # Set width proportional to number of images
        self.setFixedWidth(len(self.all_images) * 10)
        
        self.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 0px;
            }
            QSlider::handle:horizontal {
                width: 0px;
            }
        """)
        
        self.valueChanged.connect(self._handle_value_change)

    def _handle_value_change(self, value):
        """Handle slider movement and emit image name"""
        if 0 <= value < len(self.all_images):
            image_name = self.all_images[value]
            self.img_changed.emit(image_name)

    def setCheckedImages(self, images):
        self.checked_images = set(images)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        groove_rect = QRect(
            10,
            (self.height() - self.groove_height) // 2,
            self.width() - 20,
            self.groove_height
        )

        # Draw groove
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(230, 230, 230))
        painter.drawRoundedRect(groove_rect, self.groove_height // 2, self.groove_height // 2)

        # Draw markers for checked images
        for index, image_name in enumerate(self.all_images):
            if image_name in self.checked_images:
                ratio = (index - self.minimum()) / (self.maximum() - self.minimum())
                x = groove_rect.left() + int(ratio * groove_rect.width())
                marker_rect = QRect(
                    x - self.marker_width // 2,
                    groove_rect.top(),
                    self.marker_width,
                    groove_rect.height()
                )
                painter.setBrush(QColor(100, 200, 255))
                painter.drawRect(marker_rect)

        # Draw pointer
        ratio = (self.value() - self.minimum()) / (self.maximum() - self.minimum())
        thumb_x = groove_rect.left() + int(ratio * groove_rect.width())

        pointer = QPolygon([
            QPoint(thumb_x - 8, groove_rect.bottom() + 2),
            QPoint(thumb_x + 8, groove_rect.bottom() + 2),
            QPoint(thumb_x, groove_rect.bottom() + self.thumb_height)
        ])

        painter.setPen(QColor(255, 0, 0))
        painter.setBrush(QColor(255, 0, 0))
        painter.drawPolygon(pointer)

        painter.drawLine(thumb_x, groove_rect.top(), thumb_x, groove_rect.bottom() + 2)
        painter.end()

    def sizeHint(self):
        return QSize(self.width(), 60)