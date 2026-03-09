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
        self._device_samplerate = SAMPLE_RATE

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

        # Detectar sample rate nativo del dispositivo
        try:
            dev = AUDIO_DEVICE if AUDIO_DEVICE is not None else sd.default.device[0]
            device_info = sd.query_devices(dev, kind='input')
            self._device_samplerate = int(device_info['default_samplerate'])
        except Exception:
            self._device_samplerate = SAMPLE_RATE

        self.is_recording = True
        self._stream = sd.InputStream(
            samplerate=self._device_samplerate,
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

    def _resample(self, data, orig_rate, target_rate):
        """Resamplea audio de orig_rate a target_rate."""
        if orig_rate == target_rate:
            return data
        duration = len(data) / orig_rate
        target_len = int(duration * target_rate)
        indices = np.linspace(0, len(data) - 1, target_len).astype(int)
        return data[indices]

    def get_wav_buffer(self):
        if not self.frames:
            return None
        buffer = io.BytesIO()
        data = np.concatenate(self.frames, axis=0)

        # Resamplear a 16kHz si el dispositivo grabó a otra frecuencia
        if self._device_samplerate != SAMPLE_RATE:
            data = self._resample(data, self._device_samplerate, SAMPLE_RATE)

        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)  # int16 = 2 bytes
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(data.tobytes())
        buffer.seek(0)
        return buffer

    def get_duration(self):
        total_frames = sum(len(f) for f in self.frames)
        return total_frames / self._device_samplerate
