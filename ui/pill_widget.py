import math
from PyQt6.QtWidgets import QWidget, QApplication, QMenu
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPainterPath, QFont, QPen
import win32gui
import win32con

from config import PILL_MARGIN_BOTTOM
from ui.audio_visualizer import AudioVisualizer


class PillWidget(QWidget):
    set_state_signal = pyqtSignal(str)
    translate_toggled = pyqtSignal(bool)

    # Estados
    STATE_IDLE = "idle"
    STATE_RECORDING = "recording"
    STATE_PROCESSING = "processing"
    STATE_DONE = "done"
    STATE_ERROR = "error"

    # Dimensiones
    CIRCLE_SIZE = 40
    EXPANDED_WIDTH = 150
    HEIGHT = 40

    def __init__(self):
        super().__init__()
        self._state = self.STATE_IDLE
        self._current_width = float(self.CIRCLE_SIZE)
        self._target_width = float(self.CIRCLE_SIZE)
        self._drag_pos = None
        self._visualizer = None
        self._pencil_angle = 0.0
        self._pulse_phase = 0.0
        self._translate_mode = False

        self._setup_window()
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
        self.setFixedHeight(self.HEIGHT)
        self.setFixedWidth(self.CIRCLE_SIZE)

        # Posicionar en el centro inferior de la pantalla
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.CIRCLE_SIZE) // 2
        y = screen.height() - self.HEIGHT - PILL_MARGIN_BOTTOM
        self.move(x, y)

    def _setup_animation(self):
        self._anim_timer = QTimer()
        self._anim_timer.timeout.connect(self._animate)
        self._anim_timer.start(16)  # ~60 FPS

        # Timer para auto-volver a idle
        self._reset_timer = QTimer()
        self._reset_timer.setSingleShot(True)
        self._reset_timer.timeout.connect(lambda: self.set_state(self.STATE_IDLE))

    def set_visualizer(self, visualizer: AudioVisualizer):
        self._visualizer = visualizer

    def set_state(self, state: str):
        self._state = state

        if state == self.STATE_IDLE:
            self._target_width = self.CIRCLE_SIZE

        elif state == self.STATE_RECORDING:
            self._target_width = self.EXPANDED_WIDTH

        elif state == self.STATE_PROCESSING:
            self._target_width = self.EXPANDED_WIDTH
            self._pencil_angle = 0.0

        elif state == self.STATE_DONE:
            self._target_width = 70
            self._reset_timer.start(1500)

        elif state == self.STATE_ERROR:
            self._target_width = 70
            self._reset_timer.start(2000)

        self.update()

    def _animate(self):
        # Animar ancho
        diff = self._target_width - self._current_width
        if abs(diff) < 1:
            self._current_width = self._target_width
        else:
            self._current_width += diff * 0.22

        new_width = int(self._current_width)
        if new_width != self.width():
            center_x = self.x() + self.width() // 2
            self.setFixedWidth(new_width)
            self.move(center_x - new_width // 2, self.y())

        # Animar pulso idle y pencil processing
        self._pulse_phase += 0.05
        if self._state == self.STATE_PROCESSING:
            self._pencil_angle += 3.0

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()

        # --- Fondo ---
        bg_colors = {
            self.STATE_IDLE: QColor(25, 25, 30, 230),
            self.STATE_RECORDING: QColor(160, 30, 30, 235),
            self.STATE_PROCESSING: QColor(35, 35, 60, 235),
            self.STATE_DONE: QColor(25, 110, 45, 235),
            self.STATE_ERROR: QColor(160, 30, 30, 235),
        }
        bg = bg_colors.get(self._state, bg_colors[self.STATE_IDLE])

        path = QPainterPath()
        radius = h / 2
        path.addRoundedRect(0, 0, w, h, radius, radius)

        # Borde sutil
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
        painter.setBrush(bg)
        painter.drawPath(path)

        # --- Dibujar contenido segun estado ---
        if self._state == self.STATE_IDLE:
            self._draw_mic_icon(painter, w / 2, h / 2, QColor(200, 200, 210))
            # Pulso sutil
            pulse = 0.3 + 0.15 * math.sin(self._pulse_phase)
            ring_color = QColor(200, 200, 210, int(pulse * 80))
            painter.setPen(QPen(ring_color, 1.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            r = 16 + 2 * math.sin(self._pulse_phase)
            painter.drawEllipse(QPointF(w / 2, h / 2), r, r)

        elif self._state == self.STATE_RECORDING:
            # Mic icon a la izquierda con punto rojo pulsante
            mic_x = 20
            self._draw_mic_icon(painter, mic_x, h / 2, QColor(255, 120, 120))
            # Punto rojo pulsante
            dot_pulse = 0.6 + 0.4 * math.sin(self._pulse_phase * 2)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 80, 80, int(dot_pulse * 255)))
            painter.drawEllipse(QPointF(mic_x + 12, h / 2 - 8), 3, 3)
            # Ondas de audio
            self._draw_audio_waves(painter, w, h)

        elif self._state == self.STATE_PROCESSING:
            # Icono lapiz animado a la izquierda
            self._draw_pencil_icon(painter, 22, h / 2)
            # Texto con puntos animados
            dots_count = int(self._pencil_angle / 30) % 4
            text = "." * dots_count
            painter.setPen(QColor(180, 180, 220))
            painter.setFont(QFont("Segoe UI", 11))
            painter.drawText(QRectF(38, 0, w - 44, h), Qt.AlignmentFlag.AlignVCenter, f"Transcribiendo{text}")

        elif self._state == self.STATE_DONE:
            # Check verde
            painter.setPen(QPen(QColor(100, 240, 140), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            cx, cy = w / 2, h / 2
            painter.drawLine(QPointF(cx - 8, cy), QPointF(cx - 2, cy + 6))
            painter.drawLine(QPointF(cx - 2, cy + 6), QPointF(cx + 8, cy - 6))

        elif self._state == self.STATE_ERROR:
            # X roja
            painter.setPen(QPen(QColor(255, 120, 120), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            cx, cy = w / 2, h / 2
            painter.drawLine(QPointF(cx - 7, cy - 7), QPointF(cx + 7, cy + 7))
            painter.drawLine(QPointF(cx + 7, cy - 7), QPointF(cx - 7, cy + 7))

    def _draw_mic_icon(self, painter, cx, cy, color):
        """Dibuja un icono de microfono."""
        painter.setPen(QPen(color, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Cuerpo del mic (rectangulo redondeado)
        mic_w, mic_h = 8, 12
        mic_rect = QRectF(cx - mic_w / 2, cy - mic_h / 2 - 2, mic_w, mic_h)
        painter.drawRoundedRect(mic_rect, 4, 4)

        # Arco inferior (soporte)
        arc_rect = QRectF(cx - 8, cy - 8, 16, 16)
        painter.drawArc(arc_rect, -30 * 16, -120 * 16)

        # Linea base
        painter.drawLine(QPointF(cx, cy + 8), QPointF(cx, cy + 12))
        painter.drawLine(QPointF(cx - 4, cy + 12), QPointF(cx + 4, cy + 12))

    def _draw_audio_waves(self, painter, w, h):
        """Dibuja ondas de audio reactivas al sonido real."""
        if not self._visualizer:
            return

        bars = self._visualizer.bar_heights
        num_bars = len(bars)
        bar_area_start = 40
        bar_area_width = w - bar_area_start - 12
        bar_w = max(3, bar_area_width / (num_bars * 2))
        spacing = bar_w
        center_y = h / 2

        for i, bar_h in enumerate(bars):
            # Normalizar altura
            normalized = max(bar_h, 2) / self._visualizer.MAX_HEIGHT
            draw_h = normalized * (h - 10)
            draw_h = max(draw_h, 3)

            x = bar_area_start + i * (bar_w + spacing)
            if x + bar_w > w - 8:
                break

            # Color degradado blanco con opacidad variable
            opacity = 0.4 + normalized * 0.6
            color = QColor(255, 180, 180, int(opacity * 255))

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawRoundedRect(
                QRectF(x, center_y - draw_h / 2, bar_w, draw_h),
                bar_w / 2, bar_w / 2
            )

    def _draw_pencil_icon(self, painter, cx, cy):
        """Dibuja un icono de lapiz con animacion de escritura."""
        painter.save()
        painter.translate(cx, cy)

        # Movimiento sutil del lapiz (simula escribir)
        offset_x = 3 * math.sin(self._pencil_angle * math.pi / 180)
        offset_y = 1.5 * math.cos(self._pencil_angle * 2 * math.pi / 180)

        pen_color = QColor(180, 180, 220)
        painter.setPen(QPen(pen_color, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))

        # Cuerpo del lapiz (inclinado)
        painter.translate(offset_x, offset_y)
        painter.rotate(-45)

        # Cuerpo
        painter.drawLine(QPointF(0, -10), QPointF(0, 4))
        painter.drawLine(QPointF(-3, -10), QPointF(-3, 4))
        painter.drawLine(QPointF(-3, -10), QPointF(0, -10))
        painter.drawLine(QPointF(-3, 4), QPointF(0, 4))

        # Punta
        painter.drawLine(QPointF(-3, 4), QPointF(-1.5, 8))
        painter.drawLine(QPointF(0, 4), QPointF(-1.5, 8))

        painter.restore()

        # Lineas de texto simuladas
        line_y = cy + 8
        line_progress = (self._pencil_angle % 360) / 360
        painter.setPen(QPen(QColor(150, 150, 180, 100), 1))
        max_line_w = 20
        painter.drawLine(
            QPointF(cx - 6, line_y),
            QPointF(cx - 6 + max_line_w * min(line_progress * 2, 1.0), line_y)
        )

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_windows_native_flags()

    def _apply_windows_native_flags(self):
        hwnd = int(self.winId())
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        ex_style |= win32con.WS_EX_NOACTIVATE
        ex_style |= win32con.WS_EX_TOOLWINDOW
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)
        win32gui.SetWindowPos(
            hwnd, win32con.HWND_TOPMOST,
            0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE,
        )

    # --- Drag support ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    # --- Context menu ---
    def contextMenuEvent(self, event):
        # Temporalmente permitir activacion para que el menu funcione correctamente
        hwnd = int(self.winId())
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        ex_style &= ~win32con.WS_EX_NOACTIVATE
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1a1a1e;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 4px;
                font-size: 13px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #3a3a4e;
                color: white;
            }
            QMenu::separator {
                height: 1px;
                background: #444;
                margin: 4px 8px;
            }
        """)

        # Opción traducir al inglés (toggle)
        check = "\u2714 " if self._translate_mode else "   "
        translate_action = menu.addAction(f"{check}Traducir al inglés")
        menu.addSeparator()
        quit_action = menu.addAction("Cerrar SFlow")

        action = menu.exec(event.globalPos())

        # Restaurar WS_EX_NOACTIVATE
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        ex_style |= win32con.WS_EX_NOACTIVATE
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)

        if action == translate_action:
            self._translate_mode = not self._translate_mode
            self.translate_toggled.emit(self._translate_mode)
        elif action == quit_action:
            QApplication.quit()
