#!/usr/bin/env python3
import os
import subprocess
import time
import wave
from pathlib import Path

from piper.voice import PiperVoice


class RobotVoice:
    def __init__(self, model_name=None):
        print("Initialisation de la voix...")
        try:
            self.audio_dir = Path(__file__).resolve().parent
            self.model_name = None
            self.voice = None
            self.load_voice(model_name or os.getenv("LEGOBOT_VOICE_MODEL", "next"))

            self.wav_dir = str(self.audio_dir / "wav")
            os.makedirs(self.wav_dir, exist_ok=True)
        except Exception as exc:
            print(f"Erreur lors de l'initialisation de la voix : {exc}")
            raise

    @classmethod
    def available_voices(cls):
        audio_dir = Path(__file__).resolve().parent
        voices = []
        for model_path in sorted(audio_dir.glob("*.onnx")):
            voices.append({
                "id": model_path.stem,
                "name": model_path.stem.replace("_", " "),
                "path": str(model_path),
                "config": str(model_path.with_suffix(".onnx.json")),
                "has_config": model_path.with_suffix(".onnx.json").exists(),
            })
        return voices

    def load_voice(self, model_name):
        model_name = (model_name or "next").replace(".onnx", "")
        if self.model_name == model_name and self.voice is not None:
            return

        model_path = self.audio_dir / f"{model_name}.onnx"
        if not model_path.exists():
            raise FileNotFoundError(f"Voix Piper introuvable: {model_name}")

        print(f"Chargement voix Piper: {model_name}")
        self.voice = PiperVoice.load(str(model_path))
        self.model_name = model_name
        print("Modele de voix charge avec succes")

    def speak(self, text, gain_db=None, voice_model=None, on_play_start=None, on_play_end=None):
        if voice_model:
            self.load_voice(voice_model)
        wav_file = self._generate_wav(text, gain_db=gain_db)
        try:
            if on_play_start:
                on_play_start()
            subprocess.run(
                [
                    "aplay",
                    "-q",
                    "-D",
                    os.getenv("LEGOBOT_AUDIO_DEVICE", "plughw:CARD=MAX98357A,DEV=0"),
                    "-f",
                    "S16_LE",
                    "-c",
                    "1",
                    "-r",
                    "22050",
                    wav_file,
                ],
                check=True,
            )
        finally:
            if on_play_end:
                on_play_end()
            if os.path.exists(wav_file):
                os.remove(wav_file)

    def _generate_wav(self, text, gain_db=None):
        print(f"Le robot dit : {text}")
        timestamp = int(time.time() * 1000)
        wav_file = os.path.join(self.wav_dir, f"speech_{timestamp}.wav")
        temp_file = os.path.join(self.wav_dir, f"temp_{timestamp}.wav")

        with wave.open(wav_file, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(22050)
            try:
                self.voice.synthesize(text, wav)
            except Exception as exc:
                print(f"Erreur de synthese vocale : {exc}")
                self.voice.synthesize("Bonjour", wav)

        if gain_db is None:
            gain_db = float(os.getenv("LEGOBOT_VOICE_GAIN_DB", "0"))

        sox_cmd = [
            "sox",
            wav_file,
            "-c",
            "1",
            "-b",
            "16",
            "-r",
            "22050",
            temp_file,
        ]
        if gain_db:
            sox_cmd.extend(["gain", str(float(gain_db))])

        subprocess.run(sox_cmd, check=True)
        os.replace(temp_file, wav_file)
        return wav_file


if __name__ == "__main__":
    voice = RobotVoice()
    voice.speak("Bonjour, je suis le robot LEGO", gain_db=4)
    voice.speak("Je peux maintenant parler avec une vraie voix", gain_db=4)
