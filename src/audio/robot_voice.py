#!/usr/bin/env python3
import os
import subprocess
import time
import wave

from piper.voice import PiperVoice


class RobotVoice:
    def __init__(self):
        print("Initialisation de la voix...")
        try:
            model_path = os.path.join(os.path.dirname(__file__), "fr_FR-gilles-low.onnx")
            self.voice = PiperVoice.load(model_path)
            print("Modele de voix charge avec succes")

            self.wav_dir = os.path.join(os.path.dirname(__file__), "wav")
            os.makedirs(self.wav_dir, exist_ok=True)
        except Exception as exc:
            print(f"Erreur lors de l'initialisation de la voix : {exc}")
            raise

    def speak(self, text, gain_db=None):
        wav_file = self._generate_wav(text, gain_db=gain_db)
        try:
            subprocess.run(
                [
                    "aplay",
                    "-q",
                    "-f",
                    "S16_LE",
                    "-r",
                    "22050",
                    wav_file,
                ],
                check=True,
            )
        finally:
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
