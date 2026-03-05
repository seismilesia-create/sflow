import time
from PyQt6.QtCore import QObject, pyqtSignal
from pynput import keyboard


class HotkeyListener(QObject):
    pressed = pyqtSignal()
    released = pyqtSignal()

    DOUBLE_TAP_WINDOW = 0.4  # segundos

    def __init__(self):
        super().__init__()
        self._ctrl_pressed = False
        self._shift_pressed = False
        self._hold_active = False
        self._handsfree_active = False
        self._last_ctrl_tap = 0.0
        self._listener = None
        self._suppressed = False

    def start(self):
        self._listener = keyboard.Listener(
            on_press=self._on_press, on_release=self._on_release
        )
        self._listener.daemon = True
        self._listener.start()

    def stop(self):
        if self._listener:
            self._listener.stop()

    def suppress(self):
        """Ignorar teclas temporalmente (durante auto-paste)."""
        self._suppressed = True

    def unsuppress(self):
        """Reactivar deteccion y limpiar estado."""
        self._ctrl_pressed = False
        self._shift_pressed = False
        self._hold_active = False
        self._handsfree_active = False
        self._last_ctrl_tap = 0.0
        self._suppressed = False

    def _on_press(self, key):
        if self._suppressed:
            return
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            if not self._ctrl_pressed:
                now = time.time()
                if not self._handsfree_active:
                    if now - self._last_ctrl_tap < self.DOUBLE_TAP_WINDOW:
                        # Double-tap detectado -> iniciar hands-free
                        self._handsfree_active = True
                        self.pressed.emit()
                    self._last_ctrl_tap = now
                else:
                    # Segundo tap en hands-free -> detener
                    self._handsfree_active = False
                    self.released.emit()
            self._ctrl_pressed = True

        if key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
            self._shift_pressed = True

        # Hold mode: ambos presionados
        if (
            self._ctrl_pressed
            and self._shift_pressed
            and not self._hold_active
            and not self._handsfree_active
        ):
            self._hold_active = True
            self.pressed.emit()

    def _on_release(self, key):
        if self._suppressed:
            return
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            self._ctrl_pressed = False
        if key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
            self._shift_pressed = False

        # Hold mode: cualquiera suelto -> detener
        if self._hold_active and (not self._ctrl_pressed or not self._shift_pressed):
            self._hold_active = False
            self.released.emit()
