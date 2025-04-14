#!/usr/bin/env python3
import subprocess
import os
import tempfile
import time
import wave
from piper.voice import PiperVoice

class RobotVoice:
    def __init__(self):
        """Initialisation de la voix du robot"""
        print("Initialisation de la voix...")
        try:
            # Chemin vers le modèle dans le même dossier
            model_path = os.path.join(os.path.dirname(__file__), "fr_FR-gilles-low.onnx")
            
            # Chargement du modèle
            self.voice = PiperVoice.load(model_path)
            print("Modèle de voix chargé avec succès")
            
            # Création du dossier wav s'il n'existe pas
            self.wav_dir = os.path.join(os.path.dirname(__file__), 'wav')
            os.makedirs(self.wav_dir, exist_ok=True)
            
            # Configuration du volume maximum pour la carte MAX98357A
            #subprocess.run(['amixer', '-c', '0', 'set', 'Speaker', '100%'], check=True)
            
        except Exception as e:
            print(f"Erreur lors de l'initialisation de la voix : {e}")
            raise

    def speak(self, text):
        """Fait parler le robot"""
        try:
            print(f"Le robot dit : {text}")
            
            # Génération d'un nom de fichier unique
            timestamp = int(time.time())
            wav_file = os.path.join(self.wav_dir, f"speech_{timestamp}.wav")
            
            # Création du fichier WAV avec les paramètres corrects
            with wave.open(wav_file, 'wb') as wav:
                # Configuration du fichier WAV
                wav.setnchannels(1)  # Mono
                wav.setsampwidth(2)  # 16 bits
                wav.setframerate(22050)  # 22.05 kHz
                
                try:
                    # Synthèse vocale
                    self.voice.synthesize(text, wav)
                except Exception as e:
                    print(f"Erreur de synthèse vocale : {e}")
                    # Tentative avec un texte plus simple
                    self.voice.synthesize("Bonjour", wav)
            
            # Conversion du fichier WAV en mono 16 bits si nécessaire
            temp_file = os.path.join(self.wav_dir, f"temp_{timestamp}.wav")
            sox_cmd = [
                'sox',
                wav_file,
                '-c', '1',  # Mono
                '-b', '16',  # 16 bits
                '-r', '22050',  # 22.05 kHz
                temp_file
            ]
            subprocess.run(sox_cmd, check=True)
            
            # Remplacement du fichier original par le fichier converti
            os.replace(temp_file, wav_file)
            
            # Lecture du fichier WAV avec aplay sur la sortie I2S MAX98357A
            aplay_cmd = [
                'aplay',
                '-q',            # Mode silencieux
               # '-D', 'hw:0,0',  # Utiliser la carte son 0 comme dans /etc/asound.conf
                '-f', 'S16_LE',  # Format 16 bits little-endian
                '-r', '22050',   # Fréquence d'échantillonnage
                wav_file
            ]
            
            # Lecture du fichier WAV et récupération de la durée
            with wave.open(wav_file, 'rb') as wav:
                frames = wav.getnframes()
                rate = wav.getframerate()
                duration = frames / float(rate)
            
            # Lecture du fichier WAV
            subprocess.run(aplay_cmd, check=True)
            
            # Suppression du fichier temporaire
            os.remove(wav_file)
            
            return duration
            
        except Exception as e:
            print(f"Erreur lors de la parole : {e}")
            if os.path.exists(wav_file):
                os.remove(wav_file)
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return 0

if __name__ == "__main__":
    # Test de la classe
    voice = RobotVoice()
    voice.speak("Bonjour, je suis le robot LEGO")
    voice.speak("Je peux maintenant parler avec une vraie voix") 