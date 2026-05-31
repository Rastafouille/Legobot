#!/usr/bin/env python3
import json
import audioop
import os
import subprocess
import time
import wave
from pathlib import Path

from vosk import KaldiRecognizer, Model


class SpeechToText:
    def __init__(self, model_path=None, device=None):
        self.model_path = Path(model_path or os.getenv(
            "LEGOBOT_VOSK_MODEL",
            "models/vosk-model-small-fr-0.22",
        )).resolve()
        self.device = device or os.getenv("LEGOBOT_MIC_DEVICE", "plughw:CARD=Device,DEV=0")
        self.sample_rate = int(os.getenv("LEGOBOT_MIC_RATE", "16000"))
        self.silence_rms = int(os.getenv("LEGOBOT_MIC_SILENCE_RMS", "450"))
        self.speech_rms = int(os.getenv("LEGOBOT_MIC_SPEECH_RMS", str(max(900, self.silence_rms * 2))))
        self.tmp_dir = Path(os.getenv("LEGOBOT_STT_TMP_DIR", "/tmp"))
        self._model = None

    def transcribe(self, duration=4):
        duration = max(1.0, min(12.0, float(duration)))
        wav_path = self.tmp_dir / f"legobot_listen_{int(time.time() * 1000)}.wav"
        self._record(wav_path, duration)
        try:
            text = self._transcribe_wav(wav_path)
        finally:
            try:
                wav_path.unlink()
            except FileNotFoundError:
                pass
        return text

    def _record(self, wav_path, duration):
        subprocess.run(
            [
                "arecord",
                "-q",
                "-D",
                self.device,
                "-d",
                str(int(duration)),
                "-f",
                "S16_LE",
                "-r",
                str(self.sample_rate),
                "-c",
                "1",
                str(wav_path),
            ],
            check=True,
        )

    def _transcribe_wav(self, wav_path):
        recognizer = KaldiRecognizer(self._load_model(), self.sample_rate)
        parts = []
        with wave.open(str(wav_path), "rb") as wav:
            while True:
                data = wav.readframes(4000)
                if not data:
                    break
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = (result.get("text") or "").strip()
                    if text:
                        parts.append(text)

        final = json.loads(recognizer.FinalResult())
        final_text = (final.get("text") or "").strip()
        if final_text:
            parts.append(final_text)
        return " ".join(parts).strip()

    def listen_after_wake(self, wake_words=None, silence_seconds=0.45, max_seconds=5.0, on_event=None, should_stop=None):
        """Attend le mot-cle, puis enregistre la phrase jusqu'au silence."""
        wake_words = wake_words or ["ok briko", "ok brico", "okay briko", "okay brico"]
        silence_seconds = max(0.2, min(2.0, float(silence_seconds)))
        max_seconds = max(2.0, min(12.0, float(max_seconds)))
        model = self._load_model()
        wake_recognizer = KaldiRecognizer(model, self.sample_rate)
        chunk_frames = int(self.sample_rate * 0.2)
        chunk_bytes = chunk_frames * 2

        process = subprocess.Popen(
            [
                "arecord",
                "-q",
                "-D",
                self.device,
                "-f",
                "S16_LE",
                "-r",
                str(self.sample_rate),
                "-c",
                "1",
                "-t",
                "raw",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        try:
            if on_event:
                on_event("idle", "")
            while True:
                if should_stop and should_stop():
                    return ""
                data = process.stdout.read(chunk_bytes)
                if not data:
                    raise RuntimeError("Flux micro interrompu")
                if wake_recognizer.AcceptWaveform(data):
                    text = json.loads(wake_recognizer.Result()).get("text", "")
                else:
                    text = json.loads(wake_recognizer.PartialResult()).get("partial", "")
                if self._has_wake_word(text, wake_words):
                    if on_event:
                        on_event("wake", text)
                    utterance = self._record_until_silence(
                        process,
                        first_chunk=b"",
                        silence_seconds=silence_seconds,
                        max_seconds=max_seconds,
                        chunk_bytes=chunk_bytes,
                        on_event=on_event,
                        should_stop=should_stop,
                    )
                    transcript = self._transcribe_pcm(utterance)
                    return self._strip_wake_word(transcript, wake_words).strip()
        finally:
            process.terminate()
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()

    def _record_until_silence(self, process, first_chunk, silence_seconds, max_seconds, chunk_bytes, on_event=None, should_stop=None):
        # Le seuil de parole est volontairement plus haut que le seuil de bruit:
        # avec un micro USB, le fond sonore peut rester au-dessus de 450 RMS et
        # empecher la fin d'ecoute. LEGOBOT_MIC_SPEECH_RMS permet d'ajuster.
        frames = [first_chunk] if first_chunk else []
        started = False
        silence_started = None
        start_time = time.monotonic()
        no_speech_timeout = min(1.2, max_seconds)
        while time.monotonic() - start_time < max_seconds:
            if should_stop and should_stop():
                break
            data = process.stdout.read(chunk_bytes)
            if not data:
                break
            frames.append(data)
            rms = audioop.rms(data, 2)
            if rms >= self.speech_rms:
                started = True
                silence_started = None
                if on_event:
                    on_event("speech", str(rms))
            elif started:
                if silence_started is None:
                    silence_started = time.monotonic()
                elif time.monotonic() - silence_started >= silence_seconds:
                    break
            elif time.monotonic() - start_time >= no_speech_timeout:
                break
        return b"".join(frames)

    def _transcribe_pcm(self, pcm):
        recognizer = KaldiRecognizer(self._load_model(), self.sample_rate)
        parts = []
        for offset in range(0, len(pcm), 8000):
            data = pcm[offset:offset + 8000]
            if recognizer.AcceptWaveform(data):
                text = (json.loads(recognizer.Result()).get("text") or "").strip()
                if text:
                    parts.append(text)
        final_text = (json.loads(recognizer.FinalResult()).get("text") or "").strip()
        if final_text:
            parts.append(final_text)
        return " ".join(parts)

    def _load_model(self):
        if self._model is None:
            if not self.model_path.exists():
                raise FileNotFoundError(f"Modele Vosk introuvable: {self.model_path}")
            self._model = Model(str(self.model_path))
        return self._model

    def _has_wake_word(self, text, wake_words):
        normalized = self._normalize_text(text)
        return any(self._normalize_text(wake) in normalized for wake in wake_words)

    def _strip_wake_word(self, text, wake_words):
        normalized_text = self._normalize_text(text)
        for wake in wake_words:
            normalized_wake = self._normalize_text(wake)
            if normalized_text.startswith(normalized_wake):
                return text[len(wake):].strip(" ,.!?")
        return text

    def _normalize_text(self, text):
        text = (text or "").lower()
        replacements = {
            "é": "e",
            "è": "e",
            "ê": "e",
            "à": "a",
            "ù": "u",
            "ô": "o",
            "î": "i",
            "ï": "i",
            "ç": "c",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return " ".join(text.split())
