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
        """Convertit le texte en parole et joue le son"""
        try:
            # Génération du fichier WAV avec Piper
            wav_file = self._generate_wav(text)
            
            # Lecture du fichier WAV avec aplay
            aplay_cmd = [
                'aplay', '-q',
                '-f', 'S16_LE',
                '-r', '22050',
                #'-v', '0.8',  # Réduction du volume à 80%
                #'-D', 'hw:0,0',
                wav_file
            ]
            
            subprocess.run(aplay_cmd, check=True)
            
            # Suppression du fichier WAV après lecture
            os.remove(wav_file)
            
        except subprocess.CalledProcessError as e:
            print(f"Erreur lors de la parole : {e}")
            raise

    def _generate_wav(self, text):
        """Générer le fichier WAV à partir du texte"""
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
            
            return wav_file
            
        except Exception as e:
            print(f"Erreur lors de la génération du fichier WAV : {e}")
            raise

if __name__ == "__main__":
    # Test de la classe
    voice = RobotVoice()
    voice.speak("Bonjour, je suis le robot LEGO")
    voice.speak("Je peux maintenant parler avec une vraie voix") 