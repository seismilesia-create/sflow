import sys
import signal
import threading
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from config import MIN_RECORDING_DURATION
from ui.pill_widget import PillWidget
from ui.audio_visualizer import AudioVisualizer
from core.recorder import AudioRecorder
from core.transcriber import Transcriber
from core.hotkey import HotkeyListener
from core.clipboard import ClipboardManager
from db.database import TranscriptionDB
from web.server import create_app


def main():
    # Salida limpia con Ctrl+C
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Inicializar modulos
    recorder = AudioRecorder()
    transcriber = Transcriber()
    clipboard = ClipboardManager()
    db = TranscriptionDB()
    hotkey = HotkeyListener()

    # UI
    pill = PillWidget()
    visualizer = AudioVisualizer(recorder.audio_queue)
    pill.set_visualizer(visualizer)

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
                hotkey.suppress()
                clipboard.paste_text(text)
                import time
                time.sleep(0.15)
                hotkey.unsuppress()
                db.insert(text=text, duration_seconds=duration)
                pill.set_state_signal.emit("done")
            else:
                pill.set_state_signal.emit("error")

        thread = threading.Thread(target=transcribe_and_paste, daemon=True)
        thread.start()

    # CRITICO: QueuedConnection para senales cross-thread (pynput corre en su propio hilo)
    hotkey.pressed.connect(on_hotkey_pressed, Qt.ConnectionType.QueuedConnection)
    hotkey.released.connect(on_hotkey_released, Qt.ConnectionType.QueuedConnection)

    # Iniciar Flask en hilo daemon
    flask_app = create_app(db)
    flask_thread = threading.Thread(
        target=lambda: flask_app.run(host="127.0.0.1", port=5000, debug=False),
        daemon=True,
    )
    flask_thread.start()

    # Mostrar UI e iniciar hotkey
    pill.show()
    hotkey.start()

    print("SFlow activo!")
    print("  Ctrl+Shift (hold)  = grabar mientras mantienes")
    print("  Ctrl doble-tap     = grabar manos libres")
    print("  Dashboard: http://localhost:5000")
    print("  Ctrl+C para salir")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
