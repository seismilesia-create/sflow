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
AUDIO_DEVICE = 2  # Redragon Gaming Headset (cambiar si usas otro mic)
MIN_RECORDING_DURATION = 0.3  # segundos — evitar taps accidentales

# UI
PILL_IDLE_WIDTH = 44
PILL_RECORDING_WIDTH = 130
PILL_HEIGHT = 34
PILL_MARGIN_BOTTOM = 40  # pixeles desde el borde inferior

# Paths (compatible Windows)
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "sflow.db"
LOGO_SMALL = BASE_DIR / "logo_small.png"
