import sounddevice as sd
import numpy as np
import queue
import wave
import io
from config import SAMPLE_RATE, CHANNELS, DTYPE, AUDIO_DEVICE


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
        # Limpiar la cola de audio
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
        self.is_recording = True
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE,
            device=AUDIO_DEVICE,
            callback=self._callback,
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
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)  # int16 = 2 bytes
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(data.tobytes())
        buffer.seek(0)
        return buffer

    def get_duration(self):
        total_frames = sum(len(f) for f in self.frames)
        return total_frames / SAMPLE_RATE
