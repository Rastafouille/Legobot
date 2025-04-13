#!/usr/bin/env python3
import sounddevice as sd
import numpy as np
from scipy.io import wavfile
import os
import time

class INMP441Microphone:
    def __init__(self, sample_rate=44100, channels=1):
        """Initialisation du microphone INMP441"""
        self.sample_rate = sample_rate
        self.channels = channels
        
        # Configuration du microphone I2S
        self.mic_config = {
            'device': 'hw:1,0',  # Device I2S
            'channels': self.channels,
            'samplerate': self.sample_rate,
            'dtype': 'int16',
            'blocksize': 1024,
            'latency': 'low'
        }
        
        # Création du dossier pour les enregistrements si nécessaire
        self.recordings_dir = "recordings"
        if not os.path.exists(self.recordings_dir):
            os.makedirs(self.recordings_dir)

    def record(self, duration, filename=None):
        """Enregistre un son avec le microphone INMP441"""
        try:
            if filename is None:
                filename = os.path.join(self.recordings_dir, f"recording_{int(time.time())}.wav")
            
            print(f"Enregistrement pendant {duration} secondes...")
            
            # Enregistrement avec le microphone I2S
            recording = sd.rec(int(duration * self.sample_rate),
                             **self.mic_config)
            
            # Attente de la fin de l'enregistrement
            sd.wait()
            
            # Sauvegarde en WAV
            wavfile.write(filename, self.sample_rate, recording)
            print(f"Son enregistré dans {filename}")
            
            return filename
            
        except Exception as e:
            print(f"Erreur lors de l'enregistrement : {e}")
            print("Vérifiez que le microphone I2S est bien connecté et configuré")
            return None

    def get_audio_level(self, duration=0.1):
        """Mesure le niveau audio actuel"""
        try:
            # Enregistrement court pour mesurer le niveau
            recording = sd.rec(int(duration * self.sample_rate),
                             **self.mic_config)
            sd.wait()
            
            # Calcul du niveau RMS
            rms = np.sqrt(np.mean(recording**2))
            return rms
            
        except Exception as e:
            print(f"Erreur lors de la mesure du niveau audio : {e}")
            return 0

    def is_speaking(self, threshold=1000, duration=0.1):
        """Détecte si quelqu'un parle"""
        level = self.get_audio_level(duration)
        return level > threshold

if __name__ == "__main__":
    # Test de la classe
    mic = INMP441Microphone()
    
    # Test d'enregistrement
    print("Test d'enregistrement avec le microphone I2S...")
    mic.record(3, "test_mic.wav")
    
    # Test de détection de parole
    print("Test de détection de parole...")
    print("Parlez maintenant...")
    if mic.is_speaking():
        print("Parole détectée !")
    else:
        print("Pas de parole détectée") 