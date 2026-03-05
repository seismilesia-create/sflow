import time
import pyperclip
import win32gui
import win32con
import win32api


class ClipboardManager:
    def __init__(self):
        self._saved_hwnd = None

    def save_frontmost_window(self):
        """Guarda el handle de la ventana actualmente enfocada."""
        self._saved_hwnd = win32gui.GetForegroundWindow()

    def paste_text(self, text):
        """Copia el texto y lo pega en la ventana guardada."""
        # 1. Copiar al portapapeles (con espacio al inicio para separar del texto anterior)
        pyperclip.copy(" " + text)

        # 2. Restaurar foco a la ventana original
        if self._saved_hwnd:
            try:
                win32gui.SetForegroundWindow(self._saved_hwnd)
                time.sleep(0.12)  # 120ms para que Windows cambie el foco
            except Exception as e:
                print(f"No se pudo restaurar foco: {e}")

        # 3. Simular Ctrl+V
        # VK_CONTROL = 0x11, VK_V = 0x56
        win32api.keybd_event(0x11, 0, 0, 0)  # Ctrl down
        win32api.keybd_event(0x56, 0, 0, 0)  # V down
        win32api.keybd_event(0x56, 0, win32con.KEYEVENTF_KEYUP, 0)  # V up
        win32api.keybd_event(0x11, 0, win32con.KEYEVENTF_KEYUP, 0)  # Ctrl up
