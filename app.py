import os
import re
import uuid
import json
import time
import threading
import numpy as np
import soundfile as sf
from flask import Flask, request, jsonify, send_file, send_from_directory
from kokoro import KPipeline

app = Flask(__name__, static_folder="static")

AUDIO_DIR  = os.path.join(os.path.dirname(__file__), "generated_audio")
SOUNDS_DIR = os.path.join(os.path.dirname(__file__), "sounds")
os.makedirs(AUDIO_DIR, exist_ok=True)

# Pipelines keyed by lang_code, loaded on demand
_pipelines: dict = {}
_pipeline_lock = threading.Lock()

# Job state: {job_id: {status, progress, filename, error}}
_jobs = {}
_jobs_lock = threading.Lock()

# Voice prefix → Kokoro lang_code
VOICE_LANG = {
    "a": "a",  # American English  (af_*, am_*)
    "b": "b",  # British English   (bf_*, bm_*)
    "e": "e",  # Spanish           (ef_*, em_*)
}


def lang_code_for_voice(voice: str) -> str:
    prefix = voice[0] if voice else "a"
    return VOICE_LANG.get(prefix, "a")


def get_pipeline(lang_code: str) -> KPipeline:
    with _pipeline_lock:
        if lang_code not in _pipelines:
            _pipelines[lang_code] = KPipeline(lang_code=lang_code)
    return _pipelines[lang_code]


def make_title(text: str) -> str:
    words = text.split()
    if len(words) <= 10:
        return text
    return " ".join(words[:10]) + "…"


def meta_path(filename: str) -> str:
    return os.path.join(AUDIO_DIR, filename.replace(".wav", ".json"))


def split_into_chunks(text: str, max_chars: int = 500) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= max_chars:
            current = (current + " " + sentence).strip()
        else:
            if current:
                chunks.append(current)
            if len(sentence) > max_chars:
                sub = re.split(r"(?<=,)\s+", sentence)
                sub_current = ""
                for part in sub:
                    if len(sub_current) + len(part) + 1 <= max_chars:
                        sub_current = (sub_current + " " + part).strip()
                    else:
                        if sub_current:
                            chunks.append(sub_current)
                        sub_current = part
                if sub_current:
                    chunks.append(sub_current)
            else:
                current = sentence
    if current:
        chunks.append(current)
    return chunks


def generate_audio_job(job_id: str, text: str, voice: str, speed: float, title: str):
    try:
        pipeline = get_pipeline(lang_code_for_voice(voice))
        chunks = split_into_chunks(text, max_chars=400)
        total = len(chunks)
        all_audio = []
        sample_rate = 24000
        silence = np.zeros(int(sample_rate * 0.4), dtype=np.float32)

        for i, chunk in enumerate(chunks):
            with _jobs_lock:
                _jobs[job_id]["progress"] = int((i / total) * 90)

            generator = pipeline(chunk, voice=voice, speed=speed, split_pattern=None)
            for _, _, audio in generator:
                if audio is not None:
                    all_audio.append(audio)
                    all_audio.append(silence)

        if not all_audio:
            raise ValueError("No audio generated")

        combined = np.concatenate(all_audio)
        duration_secs = len(combined) / sample_rate
        filename = f"{job_id}.wav"
        filepath = os.path.join(AUDIO_DIR, filename)
        sf.write(filepath, combined, sample_rate)

        # Persist metadata next to the WAV
        meta = {
            "filename": filename,
            "title": title,
            "voice": voice,
            "speed": speed,
            "duration": round(duration_secs),
            "created_at": int(time.time()),
        }
        with open(meta_path(filename), "w") as f:
            json.dump(meta, f)

        with _jobs_lock:
            _jobs[job_id]["status"] = "done"
            _jobs[job_id]["progress"] = 100
            _jobs[job_id]["filename"] = filename
            _jobs[job_id]["duration"] = round(duration_secs)

    except Exception as e:
        with _jobs_lock:
            _jobs[job_id]["status"] = "error"
            _jobs[job_id]["error"] = str(e)


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/voices")
def voices():
    voice_list = [
        {"id": "af_heart",   "name": "Heart (calm female)",      "lang": "English",  "recommended": True},
        {"id": "af_sky",     "name": "Sky (soft female)",         "lang": "English",  "recommended": False},
        {"id": "af_bella",   "name": "Bella (gentle female)",     "lang": "English",  "recommended": False},
        {"id": "af_nicole",  "name": "Nicole (airy female)",      "lang": "English",  "recommended": False},
        {"id": "am_fenrir",  "name": "Fenrir (deep male)",        "lang": "English",  "recommended": False},
        {"id": "am_michael", "name": "Michael (warm male)",       "lang": "English",  "recommended": False},
        {"id": "bf_emma",    "name": "Emma (British female)",     "lang": "English",  "recommended": False},
        {"id": "bm_george",  "name": "George (British male)",     "lang": "English",  "recommended": False},
        {"id": "ef_dora",    "name": "Dora (female)",             "lang": "Spanish",  "recommended": False},
        {"id": "em_alex",    "name": "Alex (male)",               "lang": "Spanish",  "recommended": False},
        {"id": "em_santa",   "name": "Santa (male)",              "lang": "Spanish",  "recommended": False},
    ]
    return jsonify(voice_list)


@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json()
    text = (data.get("text") or "").strip()
    voice = data.get("voice", "af_heart")
    speed = float(data.get("speed", 0.8))

    if not text:
        return jsonify({"error": "No text provided"}), 400
    if len(text) > 200_000:
        return jsonify({"error": "Text too long (max 200,000 characters)"}), 400

    job_id = str(uuid.uuid4())
    title = make_title(text)

    with _jobs_lock:
        _jobs[job_id] = {"status": "processing", "progress": 0, "filename": None, "error": None}

    thread = threading.Thread(
        target=generate_audio_job,
        args=(job_id, text, voice, speed, title),
        daemon=True,
    )
    thread.start()
    return jsonify({"job_id": job_id})


@app.route("/api/status/<job_id>")
def status(job_id):
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        return jsonify({"error": "Unknown job"}), 404
    return jsonify(job)


@app.route("/api/library")
def library():
    items = []
    for fname in sorted(os.listdir(AUDIO_DIR), reverse=True):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(AUDIO_DIR, fname)) as f:
                meta = json.load(f)
            wav = os.path.join(AUDIO_DIR, meta["filename"])
            if os.path.exists(wav):
                items.append(meta)
        except Exception:
            pass
    return jsonify(items)


@app.route("/api/audio/<filename>", methods=["GET"])
def audio_get(filename):
    filename = os.path.basename(filename)
    filepath = os.path.join(AUDIO_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404
    return send_file(filepath, mimetype="audio/wav", as_attachment=False)


@app.route("/api/audio/<filename>", methods=["DELETE"])
def audio_delete(filename):
    filename = os.path.basename(filename)
    wav = os.path.join(AUDIO_DIR, filename)
    meta = meta_path(filename)
    deleted = []
    for p in (wav, meta):
        if os.path.exists(p):
            os.remove(p)
            deleted.append(p)
    if not deleted:
        return jsonify({"error": "File not found"}), 404
    return jsonify({"deleted": filename})


@app.route("/api/sounds")
def sounds_list():
    if not os.path.isdir(SOUNDS_DIR):
        return jsonify([])
    files = sorted(f for f in os.listdir(SOUNDS_DIR) if f.lower().endswith(".mp3"))
    return jsonify([{"filename": f, "name": os.path.splitext(f)[0]} for f in files])


@app.route("/sounds/<filename>")
def sounds_serve(filename):
    filename = os.path.basename(filename)
    filepath = os.path.join(SOUNDS_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404
    return send_file(filepath, mimetype="audio/mpeg")


if __name__ == "__main__":
    print("Starting Read for Sleep on http://127.0.0.1:5050")
    app.run(host="127.0.0.1", port=5050, debug=False)
