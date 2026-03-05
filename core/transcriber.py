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
