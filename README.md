# SFlow - Audio to Text

SFlow is a lightweight voice-to-text application for Windows. It runs as a small floating widget on your screen, captures audio through hotkeys, transcribes it using Groq's Whisper API, and automatically pastes the text into the active window.

## Features

- **Voice transcription** - Hold a hotkey, speak, release, and the text is pasted instantly.
- **Two recording modes**:
  - `Ctrl+Shift` (hold) - Records while you hold both keys.
  - `Ctrl` double-tap - Hands-free: tap Ctrl twice quickly to start, tap again to stop.
- **Spanish to English translation** - Toggle from the right-click menu to translate your speech to English.
- **Floating widget** - Minimal, draggable pill with microphone icon, audio wave visualization, and pencil animation while transcribing.
- **Web dashboard** - View and search your transcription history at `http://localhost:5000`.
- **Transcription history** - All transcriptions are stored locally in SQLite.

## Requirements

- Windows 10/11
- Python 3.10+
- A [Groq API key](https://console.groq.com/keys) (free tier available)
- A working microphone

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/seismilesia-create/sflow.git
cd sflow
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example file and add your Groq API key:

```bash
copy .env.example .env
```

Edit `.env` and replace the placeholder with your actual key:

```
GROQ_API_KEY=your_groq_api_key_here
```

You can get a free API key at [https://console.groq.com/keys](https://console.groq.com/keys).

### 5. Run the application

```bash
python main.py
```

## Desktop Shortcut (optional)

Double-click `launch.bat` to start SFlow without opening a terminal manually. You can also create a desktop shortcut pointing to `launch.bat` for quick access.

## Usage

1. **Start the app** - Run `python main.py` or use `launch.bat`.
2. **Record audio** - Hold `Ctrl+Shift` and speak, or double-tap `Ctrl` for hands-free mode.
3. **Text is pasted** - When you release the keys (or tap Ctrl again), the transcription is automatically pasted into whatever window was active.
4. **Right-click the widget** to:
   - Toggle **Translate to English** mode.
   - **Close SFlow**.
5. **View history** - Open `http://localhost:5000` in your browser.

## Project Structure

```
sflow/
├── core/
│   ├── clipboard.py      # Clipboard and window management
│   ├── hotkey.py          # Hotkey listener (Ctrl+Shift / double-tap)
│   ├── recorder.py        # Audio recording with sounddevice
│   └── transcriber.py     # Groq Whisper transcription + translation
├── db/
│   └── database.py        # SQLite storage for transcriptions
├── ui/
│   ├── audio_visualizer.py  # Real-time audio wave bars
│   └── pill_widget.py      # Floating pill widget
├── web/
│   └── server.py          # Flask dashboard
├── config.py              # App configuration
├── main.py                # Entry point
├── launch.bat             # Windows launcher
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variables template
└── sflow.ico              # App icon
```

## Tech Stack

- **GUI**: PyQt6
- **Audio capture**: sounddevice + numpy
- **Hotkeys**: pynput
- **Transcription**: Groq Whisper API (`whisper-large-v3-turbo`)
- **Translation**: Groq LLM (`llama-3.3-70b-versatile`)
- **Web dashboard**: Flask
- **Database**: SQLite3
- **Clipboard**: pyperclip + pywin32

## License

MIT
