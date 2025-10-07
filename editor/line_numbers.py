from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QFontMetrics
from PySide6.QtCore import Qt

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        
    def sizeHint(self):
        return QSize(self.editor.line_number_width, 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)
