from fastapi import FastAPI, HTTPException, Response, UploadFile, File
from pydantic import BaseModel
from gtts import gTTS
import subprocess
import tempfile
import os

app = FastAPI()

class TTSRequest(BaseModel):
    text: str

@app.post("/tts-wav")
def tts_wav(req: TTSRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Texto requerido")

    mp3_path = tempfile.mktemp(suffix=".mp3")
    wav_path = tempfile.mktemp(suffix=".wav")

    try:
        tts = gTTS(text=req.text, lang="es")
        tts.save(mp3_path)

        subprocess.run([
            "ffmpeg", "-y",
            "-i", mp3_path,
            "-ac", "1",
            "-ar", "22050",
            "-sample_fmt", "s16",
            wav_path
        ], check=True)

        with open(wav_path, "rb") as f:
            return Response(content=f.read(), media_type="audio/wav")

    finally:
        if os.path.exists(mp3_path):
            os.remove(mp3_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)


@app.post("/audio-to-wav")
async def audio_to_wav(file: UploadFile = File(...)):
    input_path = tempfile.mktemp(suffix="_input")
    wav_path = tempfile.mktemp(suffix=".wav")

    try:
        content = await file.read()

        if not content:
            raise HTTPException(status_code=400, detail="Archivo vacío")

        with open(input_path, "wb") as f:
            f.write(content)

        subprocess.run([
            "ffmpeg", "-y",
            "-i", input_path,
            "-ac", "1",
            "-ar", "22050",
            "-sample_fmt", "s16",
            wav_path
        ], check=True)

        with open(wav_path, "rb") as f:
            return Response(content=f.read(), media_type="audio/wav")

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail="No se pudo convertir el audio")

    finally:
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)
