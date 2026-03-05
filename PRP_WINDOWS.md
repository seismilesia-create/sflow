# PRP-001: SFlow — Voice-to-Text Desktop Tool (Wispr Flow Alternative) — Windows Edition

> **Status**: READY TO BUILD
> **Date**: 2026-03-05
> **Author**: Claude Sonnet 4.6 (adapted from macOS version by Claude Opus 4.6)
> **Project**: sflow-windows
> **OS Target**: Windows 10 / Windows 11

---

## Objective

Build a Windows desktop voice-to-text tool in Python that captures microphone audio via a global hotkey (press-and-hold or double-tap), transcribes it using Groq Whisper API (~$0.02/hour), and auto-pastes the text wherever the cursor is. Includes a floating "pill" overlay with real-time audio visualization, an SQLite database for transcription history, and a web dashboard at localhost:5000.

This is a fully functional replacement for Wispr Flow ($15/month) built from scratch, adapted to run natively on Windows 10+.

---

## Why

| Current Problem | Proposed Solution |
|-----------------|-------------------|
| Wispr Flow costs $15/month ($180/year) | Groq Whisper API costs ~$0.60/month con uso intenso |
| Dependencia de un servicio de terceros | App propia, local, sin dependencias externas más allá de la API STT |
| Sin control sobre datos/privacidad | Todo corre local, solo el audio se envía a Groq para transcribir |
| Sin historial de transcripciones | SQLite local guarda todas las transcripciones con timestamps |
| Limitado a la UI/UX de ellos | Control total — pill personalizada, hotkeys, web dashboard |
| **Solo disponible en macOS** | **100% compatible con Windows 10/11** |

**Valor**: Eliminar $180/año de costo recurrente y tener control total, en Windows.

---

## Diferencias clave vs. la versión macOS

| Componente macOS | Reemplazo Windows | Motivo |
|---|---|---|
| `PyObjC / AppKit` | `pywin32` (win32gui, win32con, win32api) | Las APIs nativas de macOS no existen en Windows |
| `AppleScript` | `win32gui.SetForegroundWindow()` | AppleScript es exclusivo de macOS |
| `pbcopy` (comando terminal) | `pyperclip` + `win32clipboard` | pbcopy no existe en Windows |
| `brew install portaudio` | `pip install sounddevice` (incluye portaudio) | Homebrew es exclusivo de macOS |
| `NSFloatingWindowLevel` | `win32con.HWND_TOPMOST` + `SetWindowPos()` | Cocoa no existe en Windows |
| `NSWindowStyleMaskNonactivatingPanel` | Flags `WS_EX_NOACTIVATE` + `WS_EX_TOOLWINDOW` | Mismo efecto: flotar sin robar foco |

---

## What

### Expected Behavior

1. Lanzar `sflow` — aparece una pequeña píldora flotante en la parte inferior-central de la pantalla (solo logo)
2. **Hold Mode**: El usuario mantiene **Ctrl+Shift** — la píldora se expande mostrando barras de audio animadas
3. **Hands-Free Mode**: El usuario hace doble tap en **Ctrl** — graba; tap Ctrl de nuevo para detener
4. Las barras de audio reaccionan en tiempo real al volumen del micrófono
5. El usuario suelta las teclas (o tapa Ctrl en modo hands-free)
6. La píldora muestra un spinner brevemente mientras Groq procesa
7. El texto transcripto se copia al portapapeles y se auto-pega (Ctrl+V) donde estaba el cursor
8. La píldora muestra un checkmark verde brevemente, luego vuelve a idle
9. Si ocurre un error, la píldora muestra una X roja brevemente
10. La transcripción se guarda en SQLite con timestamp y duración
11. Web dashboard en `http://localhost:5000` muestra el historial completo con búsqueda

### Success Criteria
- [ ] Global hotkey funciona en cualquier app (Notepad, Chrome, Slack, etc.)
- [ ] Audio capturado correctamente desde el micrófono
- [ ] Las barras de audio visualizan en tiempo real
- [ ] Transcripción via Groq Whisper retorna texto correcto en español e inglés
- [ ] El texto se auto-pega donde está el cursor SIN robar el foco
- [ ] Transcripciones guardadas en SQLite con búsqueda
- [ ] UI fluida — no bloquea, se ve profesional (píldora oscura semi-transparente)
- [ ] Web dashboard para historial de transcripciones
- [ ] Double-tap Ctrl hands-free mode
- [ ] La píldora flota sobre todas las ventanas sin robar foco (APIs nativas de Windows)

---

## Required Context

### Documentation & References
```yaml
- doc: https://console.groq.com/docs/speech-to-text
  critical: "whisper-large-v3-turbo es el modelo más rápido. Máx 25MB. Soporta WAV."

- doc: https://python-sounddevice.readthedocs.io/en/latest/
  critical: "Usar InputStream con callback. dtype=int16 para WAV. 16kHz mono."
  nota_windows: "En Windows, sounddevice ya incluye portaudio. No se necesita instalar por separado."

- doc: https://pynput.readthedocs.io/en/latest/keyboard.html
  critical: "En Windows NO se necesitan permisos especiales de accesibilidad."

- doc: https://doc.qt.io/qtforpython-6/
  critical: "FramelessWindowHint + WindowStaysOnTopHint + Tool. WA_TranslucentBackground."

- doc: https://pywin32.readthedocs.io/
  critical: "win32gui.SetForegroundWindow() para restaurar foco. win32con.HWND_TOPMOST para flotar.
             WS_EX_NOACTIVATE + WS_EX_TOOLWINDOW para no robar foco. Usar win32clipboard para portapapeles."

- doc: https://pyperclip.readthedocs.io/
  critical: "Fallback simple para copiar texto al portapapeles en Windows."
```

### Architecture
```
sflow/
├── main.py                 # Entry point — conecta hotkey → recorder → transcriber → clipboard
├── config.py               # Configuración centralizada (carga .env)
├── ui/
│   ├── __init__.py
│   ├── pill_widget.py      # Floating pill overlay (ventana nativa Windows via pywin32)
│   └── audio_visualizer.py # Barras de audio animadas (QPainter + QTimer)
├── core/
│   ├── __init__.py
│   ├── recorder.py         # Captura de audio con sounddevice InputStream
│   ├── transcriber.py      # Cliente Groq Whisper API
│   ├── hotkey.py           # Detección de hotkey global (Ctrl+Shift hold + double-tap Ctrl)
│   └── clipboard.py        # Guardar/restaurar foco + portapapeles + paste Windows
├── db/
│   ├── __init__.py
│   └── database.py         # SQLite CRUD para transcripciones
├── web/
│   ├── __init__.py
│   └── server.py           # Flask web dashboard (localhost:5000)
├── logo.png                # SF brand logo (tamaño completo)
├── logo_small.png          # SF brand logo (22x22 para la píldora)
├── requirements.txt
├── .env                    # GROQ_API_KEY (no se sube al repo)
├── .env.example
└── .gitignore
```

### Data Model (SQLite)
```sql
CREATE TABLE IF NOT EXISTS transcriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    language TEXT,
    duration_seconds REAL,
    model TEXT DEFAULT 'whisper-large-v3-turbo',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_transcriptions_created_at ON transcriptions(created_at);
```

---

## Implementation Blueprint

### Phase 0: Project Setup (Windows)
**Objetivo**: Instalar dependencias y crear la estructura del proyecto

- [ ] Verificar que Python 3.12+ está instalado: `python --version`
  - Si no está instalado, descargar desde https://www.python.org/downloads/
  - **IMPORTANTE**: Durante la instalación, marcar ✅ "Add Python to PATH"
- [ ] Abrir una terminal (CMD o PowerShell) en la carpeta del proyecto
- [ ] Crear entorno virtual: `python -m venv venv`
- [ ] Activar entorno virtual: `venv\Scripts\activate`
  - Deberías ver `(venv)` al inicio de la línea de tu terminal
- [ ] Crear `requirements.txt` con el siguiente contenido:
```txt
PyQt6
sounddevice
numpy
pynput
groq
python-dotenv
flask
pywin32
pyperclip
```
- [ ] Instalar dependencias: `pip install -r requirements.txt`
- [ ] Crear estructura de carpetas: `ui/`, `core/`, `db/`, `web/`
- [ ] Crear `.env` con `GROQ_API_KEY=tu_api_key_aqui`
- [ ] Crear `.env.example` y `.gitignore`

**Nota Windows**: NO se necesita instalar portaudio por separado. El paquete `sounddevice` para Windows ya lo incluye internamente.

**Validación**: 
```bash
python -c "import PyQt6, sounddevice, pynput, groq, flask, win32gui; print('Todo OK')"
```

---

### Phase 1: Config & Database
**Objetivo**: Configuración centralizada y SQLite funcionando

- [ ] Crear `config.py` — carga `.env`, define todas las constantes (dimensiones UI, params audio, paths)
- [ ] Crear `db/database.py` — init DB, insert, get_recent, search, count
- [ ] Validar que la DB se crea y puede insertar/leer

**Código de referencia para `config.py`**:
```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "whisper-large-v3-turbo"

# Audio
SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "int16"
MIN_RECORDING_DURATION = 0.3  # segundos — evitar taps accidentales

# UI
PILL_IDLE_WIDTH = 44
PILL_RECORDING_WIDTH = 130
PILL_HEIGHT = 34
PILL_MARGIN_BOTTOM = 40  # píxeles desde el borde inferior

# Paths (compatible Windows)
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "sflow.db"
LOGO_SMALL = BASE_DIR / "logo_small.png"
```

**Validación**:
```bash
python -c "from db.database import TranscriptionDB; db = TranscriptionDB(); print('DB OK')"
```

---

### Phase 2: Audio Capture
**Objetivo**: Capturar audio del micrófono con sounddevice

- [ ] Crear `core/recorder.py` — InputStream con callback
- [ ] El callback alimenta `queue.Queue` (para visualización) Y lista `frames` (para WAV)
- [ ] Implementar `get_wav_buffer()` — convierte frames a WAV en memoria (BytesIO)
- [ ] Implementar `get_duration()` — calcula duración desde cantidad de frames

**Código de referencia para `core/recorder.py`**:
```python
import sounddevice as sd
import numpy as np
import queue
import wave
import io
from config import SAMPLE_RATE, CHANNELS, DTYPE

class AudioRecorder:
    def __init__(self):
        self.frames = []
        self.audio_queue = queue.Queue()
        self._stream = None
        self.is_recording = False

    def _callback(self, indata, frames, time, status):
        if self.is_recording:
            self.frames.append(indata.copy())
            # Para el visualizador
            amplitude = np.abs(indata).mean()
            self.audio_queue.put(amplitude)

    def start(self):
        self.frames = []
        self.is_recording = True
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE,
            callback=self._callback
        )
        self._stream.start()

    def stop(self):
        self.is_recording = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def get_wav_buffer(self):
        if not self.frames:
            return None
        buffer = io.BytesIO()
        data = np.concatenate(self.frames, axis=0)
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)  # int16 = 2 bytes
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(data.tobytes())
        buffer.seek(0)
        return buffer

    def get_duration(self):
        total_frames = sum(len(f) for f in self.frames)
        return total_frames / SAMPLE_RATE
```

**Validación**:
```bash
python -c "from core.recorder import AudioRecorder; print('Recorder OK')"
```

---

### Phase 3: Groq Transcription
**Objetivo**: Enviar audio a Groq Whisper y recibir texto

- [ ] Crear `core/transcriber.py` — envía buffer WAV a la API de Groq
- [ ] Manejar errores de API con gracia

**Código de referencia para `core/transcriber.py`**:
```python
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL

class Transcriber:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)

    def transcribe(self, wav_buffer):
        try:
            wav_buffer.name = "audio.wav"  # Groq necesita un nombre de archivo
            result = self.client.audio.transcriptions.create(
                file=wav_buffer,
                model=GROQ_MODEL,
            )
            return result.text.strip()
        except Exception as e:
            print(f"Error Groq: {e}")
            return None
```

**Validación**: Grabar audio → transcribir → verificar texto correcto

---

### Phase 4: Clipboard + Auto-Paste (Windows)
**Objetivo**: Copiar texto al portapapeles y auto-pegar donde está el cursor

- [ ] Crear `core/clipboard.py`
- [ ] `save_frontmost_window()` — guarda la ventana activa via `win32gui.GetForegroundWindow()`
- [ ] `paste_text()` — copia con `pyperclip` + restaura foco + simula Ctrl+V con `pywin32`

**Código de referencia para `core/clipboard.py`**:
```python
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
        # 1. Copiar al portapapeles
        pyperclip.copy(text)

        # 2. Restaurar foco a la ventana original
        if self._saved_hwnd:
            try:
                win32gui.SetForegroundWindow(self._saved_hwnd)
                time.sleep(0.12)  # 120ms para que Windows cambie el foco
            except Exception as e:
                print(f"No se pudo restaurar foco: {e}")

        # 3. Simular Ctrl+V
        # VK_CONTROL = 0x11, VK_V = 0x56
        win32api.keybd_event(0x11, 0, 0, 0)          # Ctrl down
        win32api.keybd_event(0x56, 0, 0, 0)          # V down
        win32api.keybd_event(0x56, 0, win32con.KEYEVENTF_KEYUP, 0)  # V up
        win32api.keybd_event(0x11, 0, win32con.KEYEVENTF_KEYUP, 0)  # Ctrl up
```

**Nota Windows**: En Windows NO se necesita AppleScript. `win32gui.SetForegroundWindow()` hace el trabajo equivalente para restaurar el foco.

**Validación**: Copiar texto, abrir Notepad, verificar que pega correctamente.

---

### Phase 5: UI — Floating Pill (Windows)
**Objetivo**: Ventana sin bordes flotante que NUNCA roba el foco

- [ ] Crear `ui/pill_widget.py` — sin bordes, transparente, siempre encima
- [ ] Estados: idle (solo logo, 44px), recording (expandida 130px con barras), processing (spinner), done (checkmark), error (X)
- [ ] Animación suave de ancho entre estados (lerp factor 0.22)
- [ ] Arrastrable (mouse press+move)
- [ ] **Flotante nativo Windows**: Usar `pywin32` para setear `HWND_TOPMOST` + flags `WS_EX_NOACTIVATE` y `WS_EX_TOOLWINDOW` — equivalente Windows al `NSNonactivatingPanel` de macOS

**Código crítico de Windows para `ui/pill_widget.py`**:
```python
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
import win32gui
import win32con

class PillWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

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

        # Agregar:
        # WS_EX_NOACTIVATE  — no roba foco al aparecer
        # WS_EX_TOOLWINDOW  — no aparece en la barra de tareas
        ex_style |= win32con.WS_EX_NOACTIVATE
        ex_style |= win32con.WS_EX_TOOLWINDOW

        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)

        # Setear como topmost (siempre encima de todas las ventanas)
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOPMOST,
            0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE
        )
```

**Validación**: La píldora aparece, se puede arrastrar, transiciona entre estados, NO roba el foco.

---

### Phase 6: Audio Visualizer
**Objetivo**: Barras animadas que reaccionan al audio en tiempo real

- [ ] Crear `ui/audio_visualizer.py` — QPainter + QTimer a 30 FPS
- [ ] 8 barras, blanco monocromático, opacidad escala con amplitud
- [ ] Decaimiento suave (factor 0.80) para caída elegante
- [ ] Lee de `recorder.audio_queue` (thread-safe via `queue.Queue`)

**Código de referencia para `ui/audio_visualizer.py`**:
```python
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPainter, QColor
import queue

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
        self._timer = QTimer()
        self._timer.timeout.connect(self._update)
        self._timer.start(33)  # ~30 FPS

    def _update(self):
        amplitude = 0.0
        while not self.audio_queue.empty():
            try:
                amplitude = max(amplitude, self.audio_queue.get_nowait())
            except queue.Empty:
                break
        normalized = min(amplitude / 3000.0, 1.0)
        for i in range(self.NUM_BARS):
            import random
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
```

**Validación**: Las barras se mueven cuando se habla.

---

### Phase 7: Global Hotkey
**Objetivo**: Detectar Ctrl+Shift (hold) y double-tap Ctrl (hands-free)

- [ ] Crear `core/hotkey.py` — pynput Listener
- [ ] **Hold mode**: Ctrl+Shift mantenido → señal `pressed`, cualquiera suelto → señal `released`
- [ ] **Hands-free mode**: Double-tap Ctrl en 400ms → señal `pressed`, siguiente Ctrl → señal `released`
- [ ] Emite Qt signals (`pressed`, `released`) para conexión en el hilo principal

**Nota Windows**: A diferencia de macOS, pynput en Windows NO requiere permisos especiales de accesibilidad. Funciona out-of-the-box.

**Código de referencia para `core/hotkey.py`**:
```python
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

    def start(self):
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self._listener.daemon = True
        self._listener.start()

    def stop(self):
        if self._listener:
            self._listener.stop()

    def _on_press(self, key):
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            now = time.time()
            if not self._handsfree_active:
                if now - self._last_ctrl_tap < self.DOUBLE_TAP_WINDOW:
                    # Double-tap detectado → iniciar hands-free
                    self._handsfree_active = True
                    self.pressed.emit()
                self._last_ctrl_tap = now
            else:
                # Segundo tap en hands-free → detener
                self._handsfree_active = False
                self.released.emit()
            self._ctrl_pressed = True

        if key == keyboard.Key.shift:
            self._shift_pressed = True

        # Hold mode: ambos presionados
        if self._ctrl_pressed and self._shift_pressed and not self._hold_active and not self._handsfree_active:
            self._hold_active = True
            self.pressed.emit()

    def _on_release(self, key):
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            self._ctrl_pressed = False
        if key == keyboard.Key.shift:
            self._shift_pressed = False

        # Hold mode: cualquiera suelto → detener
        if self._hold_active and (not self._ctrl_pressed or not self._shift_pressed):
            self._hold_active = False
            self.released.emit()
```

**Validación**: Ambos modos de hotkey detectados en cualquier app.

---

### Phase 8: Integration (main.py)
**Objetivo**: Conectar todos los módulos

- [ ] Crear `main.py` — orquesta hotkey → recorder → transcriber → clipboard → DB
- [ ] **Qt signal threading**: TODAS las señales cross-thread usan `Qt.ConnectionType.QueuedConnection`
- [ ] La transcripción corre en un `threading.Thread` en background (daemon)
- [ ] `signal.signal(signal.SIGINT, signal.SIG_DFL)` para salida limpia con Ctrl+C
- [ ] Inicia Flask web server en puerto 5000 en un hilo daemon
- [ ] Guarda ventana activa al presionar hotkey, restaura al pegar

**Código de referencia para `main.py`**:
```python
import sys
import signal
import threading
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from config import MIN_RECORDING_DURATION
from ui.pill_widget import PillWidget
from core.recorder import AudioRecorder
from core.transcriber import Transcriber
from core.hotkey import HotkeyListener
from core.clipboard import ClipboardManager
from db.database import TranscriptionDB
from web.server import create_app

def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Inicializar módulos
    pill = PillWidget()
    recorder = AudioRecorder()
    transcriber = Transcriber()
    clipboard = ClipboardManager()
    db = TranscriptionDB()
    hotkey = HotkeyListener()

    def on_hotkey_pressed():
        clipboard.save_frontmost_window()
        recorder.start()
        pill.set_state("recording")

    def on_hotkey_released():
        recorder.stop()
        duration = recorder.get_duration()

        if duration < MIN_RECORDING_DURATION:
            pill.set_state("idle")
            return

        pill.set_state("processing")

        def transcribe_and_paste():
            wav_buffer = recorder.get_wav_buffer()
            if wav_buffer is None:
                pill.set_state_signal.emit("error")
                return

            text = transcriber.transcribe(wav_buffer)
            if text:
                clipboard.paste_text(text)
                db.insert(text=text, duration_seconds=duration)
                pill.set_state_signal.emit("done")
            else:
                pill.set_state_signal.emit("error")

        thread = threading.Thread(target=transcribe_and_paste, daemon=True)
        thread.start()

    # CRÍTICO: QueuedConnection para señales cross-thread (pynput corre en su propio hilo)
    hotkey.pressed.connect(on_hotkey_pressed, Qt.ConnectionType.QueuedConnection)
    hotkey.released.connect(on_hotkey_released, Qt.ConnectionType.QueuedConnection)

    # Iniciar Flask en hilo daemon
    flask_app = create_app(db)
    flask_thread = threading.Thread(
        target=lambda: flask_app.run(host="127.0.0.1", port=5000, debug=False),
        daemon=True
    )
    flask_thread.start()

    # Mostrar UI e iniciar hotkey
    pill.show()
    hotkey.start()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

**Validación**: Flujo E2E completo — hotkey → grabar → transcribir → pegar → guardar.

---

### Phase 9: Web Dashboard
**Objetivo**: Visualizador de historial de transcripciones en el navegador

- [ ] Crear `web/server.py` — Flask app con Tailwind CSS
- [ ] Tema oscuro, branding SF, diseño glass morphism
- [ ] Vista de tabla con hora, texto, duración, botón copiar
- [ ] Click para expandir transcripciones largas
- [ ] Filtro de búsqueda
- [ ] Auto-refresh cada 5 segundos
- [ ] Corre en hilo daemon en `localhost:5000`

**Validación**: Abrir navegador en localhost:5000, ver historial de transcripciones.

---

## Validation Loop

### Level 1: Imports
```bash
venv\Scripts\activate
python -c "import PyQt6, sounddevice, pynput, groq, flask, win32gui, pyperclip; print('Todos OK')"
```

### Level 2: Cada Módulo
```bash
python -c "from db.database import TranscriptionDB; db = TranscriptionDB(); print('DB OK')"
python -c "from core.recorder import AudioRecorder; print('Recorder OK')"
python -c "from core.transcriber import Transcriber; print('Transcriber OK')"
python -c "from core.hotkey import HotkeyListener; print('Hotkey OK')"
python -c "from ui.pill_widget import PillWidget; print('Pill OK')"
```

### Level 3: Integración
```bash
python main.py
# Verificar: píldora aparece, hotkey funciona, graba audio, pega texto, dashboard en :5000
```

---

## Known Gotchas (Windows Edition)

```python
# IMPORTANTE: En Windows NO se necesitan permisos especiales de accesibilidad para pynput
# A diferencia de macOS, funciona out-of-the-box en Windows 10/11

# IMPORTANTE: En Windows NO se necesita instalar portaudio por separado
# pip install sounddevice ya incluye los binarios de portaudio para Windows

# CRÍTICO: Qt signal threading — pynput emite señales desde su propio hilo
# DEBE usar Qt.ConnectionType.QueuedConnection, NO AutoConnection
# AutoConnection elige DirectConnection cuando ambos QObjects están en el hilo principal
# pero el emit() viene del hilo de pynput → comportamiento indefinido en Windows

# CRÍTICO: Ventana flotante Windows sin robar foco
# Los flags de Qt solos (WindowDoesNotAcceptFocus) no siempre son suficientes
# Usar pywin32: WS_EX_NOACTIVATE + WS_EX_TOOLWINDOW + HWND_TOPMOST
# Aplicar en showEvent() después de que la ventana nativa sea creada

# CRÍTICO: Auto-paste en Windows
# NO usar pyautogui si hay teclas modificadoras presionadas — puede interferir
# Usar pyperclip para copiar + win32api.keybd_event para simular Ctrl+V
# Restaurar foco primero con win32gui.SetForegroundWindow() + sleep(0.12)

# IMPORTANTE: Grabaciones cortas (<0.3s) son taps accidentales — ignorar

# IMPORTANTE: Activar el entorno virtual SIEMPRE antes de correr
# venv\Scripts\activate   (Windows CMD)
# venv\Scripts\Activate.ps1  (Windows PowerShell)

# IMPORTANTE: Si PowerShell bloquea la activación del venv:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# IMPORTANTE: pywin32 post-install script
# Si win32gui da error después de instalar, correr:
# python venv\Scripts\pywin32_postinstall.py -install
```

---

## Anti-Patterns to Avoid (Windows Edition)

- DO NOT usar toggle para el hotkey en hold-mode — debe ser press-and-hold
- DO NOT procesar audio en el hilo principal (bloquea la UI)
- DO NOT llamar a la API de Groq en el hilo principal (bloquea la UI)
- DO NOT tocar widgets de Qt desde hilos secundarios
- DO NOT usar pyautogui cuando hay modificadores presionados en Windows — usar win32api.keybd_event
- DO NOT usar Qt's AutoConnection para señales cross-thread — usar QueuedConnection
- DO NOT confiar solo en flags de Qt para ventanas flotantes en Windows — usar pywin32
- DO NOT hardcodear la API key en el código fuente
- DO NOT grabar en float32 y enviar directo a WAV — usar int16
- DO NOT usar `pbcopy` ni `AppleScript` — esos son exclusivos de macOS
- DO NOT usar `PyObjC` ni `AppKit` — esas librerías no existen en Windows

---

## Dependencies

```bash
# Python (dentro del entorno virtual) — Windows
pip install PyQt6 sounddevice numpy pynput groq python-dotenv flask pywin32 pyperclip

# Post-install de pywin32 (solo si hay errores con win32gui):
python venv\Scripts\pywin32_postinstall.py -install
```

**Nota**: A diferencia de macOS, en Windows NO se necesita ningún paquete del sistema instalado externamente (no hay equivalente de Homebrew necesario para esta app).

---

## Environment Variables

```env
# .env
GROQ_API_KEY=tu_groq_api_key_aqui
```

Obtener API key gratuita en: https://console.groq.com/keys

---

## Environment

- **Python**: 3.12+ (probado en 3.12 y 3.13)
- **Windows**: 10 / 11 (64-bit recomendado)
- **Stack**: Python + PyQt6 + sounddevice + Groq Whisper + SQLite + Flask + pywin32
- **Costo**: ~$0.02/hora de transcripción (vs $15/mes de Wispr Flow)
- **Sin dependencias del sistema**: Todo instala via `pip`, sin Homebrew ni instaladores externos

---

## Tabla Resumen de Cambios macOS → Windows

| Archivo | Cambio |
|---|---|
| `requirements.txt` | Reemplazar `pyobjc-framework-Cocoa` → `pywin32` + `pyperclip` |
| `core/clipboard.py` | Reemplazar AppleScript + pbcopy → `win32gui` + `win32api` + `pyperclip` |
| `ui/pill_widget.py` | Reemplazar `AppKit.NSFloatingWindowLevel` → `win32gui.SetWindowPos(HWND_TOPMOST)` + `WS_EX_NOACTIVATE` |
| `config.py` | Paths con `pathlib.Path` ya son compatibles (no cambiar) |
| `core/hotkey.py` | Sin cambios — `pynput` es multiplataforma |
| `core/recorder.py` | Sin cambios — `sounddevice` es multiplataforma |
| `core/transcriber.py` | Sin cambios — API de Groq es multiplataforma |
| `db/database.py` | Sin cambios — SQLite es multiplataforma |
| `web/server.py` | Sin cambios — Flask es multiplataforma |
| `main.py` | Sin cambios de lógica — solo asegurarse de importar los módulos Windows |
| `Phase 0 setup` | Reemplazar `brew install portaudio` → no necesario en Windows |
