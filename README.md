# Read for Sleep

A local web app that converts any text into calm, sleep-friendly audio using the [Kokoro TTS](https://github.com/hexgrad/kokoro) text-to-speech model. Paste an article, story, or meditation script and get a WAV file read to you at a soothing pace — with optional ambient sound mixing (rain, fire, ocean, etc.).

## Features

- Text-to-speech via Kokoro (runs fully offline after first model download)
- 11 voices: American/British English and Spanish
- Adjustable reading speed (0.5× – 1.2×)
- Ambient sound mixer (rain, fire, ocean, wind chimes, and more)
- Persistent library of previously generated recordings
- Download recordings as WAV files

## Requirements

- Python 3.11
- macOS, Linux, or WSL (the `start.sh` script uses bash)

## Setup

```bash
# 1. Create a virtual environment
python3.11 -m venv venv

# 2. Install dependencies
venv/bin/pip install kokoro flask soundfile numpy scipy torch
```

The Kokoro model (~330 MB) is downloaded automatically on the first run.

## Running

```bash
./start.sh
```

This opens `http://127.0.0.1:5050` in your browser automatically. Alternatively, run the server directly:

```bash
venv/bin/python app.py
```

Then open [http://127.0.0.1:5050](http://127.0.0.1:5050) in your browser.

## Usage

1. Paste any text (up to 200,000 characters) into the text area.
2. Choose a voice and set your preferred reading speed.
3. Click **Generate Sleep Audio** and wait for synthesis to complete.
4. Play the audio in the browser or download the WAV file.
5. Toggle the ambient mixer to layer background sounds while you listen.
6. Previously generated recordings appear in the **Previous recordings** library.

## Project Structure

```
read-for-sleep/
├── app.py              # Flask server and TTS logic
├── start.sh            # Launch script (creates venv check, opens browser)
├── static/
│   └── index.html      # Single-page frontend
├── sounds/             # Ambient MP3 files served by the mixer
└── generated_audio/    # WAV files and metadata for generated recordings
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Serves the web UI |
| GET | `/api/voices` | Lists available TTS voices |
| POST | `/api/generate` | Starts an async audio generation job |
| GET | `/api/status/<job_id>` | Polls job progress |
| GET | `/api/audio/<filename>` | Streams a generated WAV file |
| DELETE | `/api/audio/<filename>` | Deletes a recording and its metadata |
| GET | `/api/library` | Lists all saved recordings |
| GET | `/api/sounds` | Lists available ambient sound files |
| GET | `/sounds/<filename>` | Serves an ambient MP3 |
