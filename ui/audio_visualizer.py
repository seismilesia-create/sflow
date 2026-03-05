import random
import queue
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPainter, QColor


class AudioVisualizer(QWidget):
    NUM_BARS = 8
    MAX_HEIGHT = 20
    BAR_WIDTH = 4
    BAR_SPACING = 3
    DECAY = 0.80

    def __init__(self, audio_queue: queue.Queue, parent=None):
        super().__init__(parent)
        self.audio_queue = audio_queue
        self.bar_heights = [0.0] * self.NUM_BARS
        self.setFixedSize(
            self.NUM_BARS * (self.BAR_WIDTH + self.BAR_SPACING) - self.BAR_SPACING + 4,
            self.MAX_HEIGHT + 6,
        )

        self._timer = QTimer()
        self._timer.timeout.connect(self._update_bars)
        self._timer.start(33)  # ~30 FPS

    def _update_bars(self):
        amplitude = 0.0
        while not self.audio_queue.empty():
            try:
                amplitude = max(amplitude, self.audio_queue.get_nowait())
            except queue.Empty:
                break

        normalized = min(amplitude / 3000.0, 1.0)

        for i in range(self.NUM_BARS):
            variation = normalized * random.uniform(0.6, 1.0)
            target = variation * self.MAX_HEIGHT
            if target > self.bar_heights[i]:
                self.bar_heights[i] = target
            else:
                self.bar_heights[i] *= self.DECAY

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        total_width = self.NUM_BARS * (self.BAR_WIDTH + self.BAR_SPACING) - self.BAR_SPACING
        x_start = (self.width() - total_width) // 2
        center_y = self.height() // 2

        for i, h in enumerate(self.bar_heights):
            h = max(h, 3)
            x = x_start + i * (self.BAR_WIDTH + self.BAR_SPACING)
            y = center_y - int(h) // 2
            opacity = min(0.4 + (h / self.MAX_HEIGHT) * 0.6, 1.0)
            color = QColor(255, 255, 255, int(opacity * 255))
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(x, y, self.BAR_WIDTH, int(h), 2, 2)
