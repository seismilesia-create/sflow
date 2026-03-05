import sys
from PyQt6.QtWidgets import QWidget, QApplication, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QPainter, QColor, QPainterPath, QFont, QPixmap
import win32gui
import win32con

from config import PILL_IDLE_WIDTH, PILL_RECORDING_WIDTH, PILL_HEIGHT, PILL_MARGIN_BOTTOM, LOGO_SMALL
from ui.audio_visualizer import AudioVisualizer


class PillWidget(QWidget):
    set_state_signal = pyqtSignal(str)

    # Estados
    STATE_IDLE = "idle"
    STATE_RECORDING = "recording"
    STATE_PROCESSING = "processing"
    STATE_DONE = "done"
    STATE_ERROR = "error"

    # Colores
    BG_COLOR = QColor(30, 30, 30, 220)
    BG_RECORDING = QColor(180, 40, 40, 220)
    BG_PROCESSING = QColor(50, 50, 80, 220)
    BG_DONE = QColor(30, 120, 50, 220)
    BG_ERROR = QColor(180, 40, 40, 220)

    def __init__(self):
        super().__init__()
        self._state = self.STATE_IDLE
        self._current_width = float(PILL_IDLE_WIDTH)
        self._target_width = float(PILL_IDLE_WIDTH)
        self._drag_pos = None
        self._visualizer = None
        self._status_label = None

        self._setup_window()
        self._setup_ui()
        self._setup_animation()

        # Signal para set_state desde hilos secundarios
        self.set_state_signal.connect(self.set_state, Qt.ConnectionType.QueuedConnection)

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedHeight(PILL_HEIGHT)
        self.setFixedWidth(PILL_IDLE_WIDTH)

        # Posicionar en el centro inferior de la pantalla
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - PILL_IDLE_WIDTH) // 2
        y = screen.height() - PILL_HEIGHT - PILL_MARGIN_BOTTOM
        self.move(x, y)

    def _setup_ui(self):
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(8, 4, 8, 4)
        self._layout.setSpacing(6)

        # Logo
        self._logo_label = QLabel()
        logo_pixmap = QPixmap(str(LOGO_SMALL))
        if logo_pixmap.isNull():
            # Fallback: circulo blanco si no hay logo
            self._logo_label.setText("SF")
            self._logo_label.setStyleSheet("color: white; font-weight: bold; font-size: 11px;")
        else:
            self._logo_label.setPixmap(
                logo_pixmap.scaled(QSize(22, 22), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            )
        self._logo_label.setFixedSize(22, 22)
        self._layout.addWidget(self._logo_label)

        # Status label (para processing/done/error)
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: white; font-size: 12px;")
        self._status_label.setVisible(False)
        self._layout.addWidget(self._status_label)

    def _setup_animation(self):
        self._anim_timer = QTimer()
        self._anim_timer.timeout.connect(self._animate_width)
        self._anim_timer.start(16)  # ~60 FPS

        # Timer para auto-volver a idle
        self._reset_timer = QTimer()
        self._reset_timer.setSingleShot(True)
        self._reset_timer.timeout.connect(lambda: self.set_state(self.STATE_IDLE))

    def set_visualizer(self, visualizer: AudioVisualizer):
        """Conecta el visualizador de audio."""
        self._visualizer = visualizer
        self._layout.addWidget(self._visualizer)
        self._visualizer.setVisible(False)

    def set_state(self, state: str):
        self._state = state

        if state == self.STATE_IDLE:
            self._target_width = PILL_IDLE_WIDTH
            if self._visualizer:
                self._visualizer.setVisible(False)
            self._status_label.setVisible(False)

        elif state == self.STATE_RECORDING:
            self._target_width = PILL_RECORDING_WIDTH
            if self._visualizer:
                self._visualizer.setVisible(True)
            self._status_label.setVisible(False)

        elif state == self.STATE_PROCESSING:
            self._target_width = 90
            if self._visualizer:
                self._visualizer.setVisible(False)
            self._status_label.setText("...")
            self._status_label.setVisible(True)

        elif state == self.STATE_DONE:
            self._target_width = 70
            if self._visualizer:
                self._visualizer.setVisible(False)
            self._status_label.setText("\u2713")
            self._status_label.setStyleSheet("color: #4ade80; font-size: 16px; font-weight: bold;")
            self._status_label.setVisible(True)
            self._reset_timer.start(1500)

        elif state == self.STATE_ERROR:
            self._target_width = 70
            if self._visualizer:
                self._visualizer.setVisible(False)
            self._status_label.setText("\u2717")
            self._status_label.setStyleSheet("color: #f87171; font-size: 16px; font-weight: bold;")
            self._status_label.setVisible(True)
            self._reset_timer.start(2000)

        self.update()

    def _animate_width(self):
        diff = self._target_width - self._current_width
        if abs(diff) < 1:
            self._current_width = self._target_width
        else:
            self._current_width += diff * 0.22  # lerp factor

        new_width = int(self._current_width)
        if new_width != self.width():
            # Reposicionar para mantener centrado
            center_x = self.x() + self.width() // 2
            self.setFixedWidth(new_width)
            self.move(center_x - new_width // 2, self.y())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Color de fondo segun estado
        bg = {
            self.STATE_IDLE: self.BG_COLOR,
            self.STATE_RECORDING: self.BG_RECORDING,
            self.STATE_PROCESSING: self.BG_PROCESSING,
            self.STATE_DONE: self.BG_DONE,
            self.STATE_ERROR: self.BG_ERROR,
        }.get(self._state, self.BG_COLOR)

        # Dibujar pill redondeada
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), PILL_HEIGHT / 2, PILL_HEIGHT / 2)
        painter.fillPath(path, bg)

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_windows_native_flags()

    def _apply_windows_native_flags(self):
        """
        Equivalente Windows de NSFloatingWindowLevel + NSNonactivatingPanel.
        Hace que la ventana flote sin robar nunca el foco del usuario.
        """
        hwnd = int(self.winId())

        # Obtener estilos extendidos actuales
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)

        # WS_EX_NOACTIVATE — no roba foco al aparecer
        # WS_EX_TOOLWINDOW — no aparece en la barra de tareas
        ex_style |= win32con.WS_EX_NOACTIVATE
        ex_style |= win32con.WS_EX_TOOLWINDOW

        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)

        # Setear como topmost (siempre encima de todas las ventanas)
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOPMOST,
            0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE,
        )

    # Drag support
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
