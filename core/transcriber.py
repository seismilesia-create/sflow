from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL

TRANSLATE_MODEL = "llama-3.3-70b-versatile"


class Transcriber:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.translate_to_english = False

    def transcribe(self, wav_buffer):
        try:
            wav_buffer.name = "audio.wav"  # Groq necesita un nombre de archivo

            # Siempre transcribir primero en español
            result = self.client.audio.transcriptions.create(
                file=wav_buffer,
                model=GROQ_MODEL,
                language="es",
            )
            text = result.text.strip()

            if self.translate_to_english and text:
                text = self._translate(text)

            return text
        except Exception as e:
            print(f"Error Groq: {e}")
            return None

    def _translate(self, text):
        """Traduce texto de español a inglés usando Groq LLM."""
        try:
            response = self.client.chat.completions.create(
                model=TRANSLATE_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a translator. Translate the following Spanish text to English. Reply ONLY with the translation, nothing else.",
                    },
                    {"role": "user", "content": text},
                ],
                temperature=0.3,
                max_tokens=2048,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error traducción: {e}")
            return text  # Si falla la traducción, devolver el texto original en español
