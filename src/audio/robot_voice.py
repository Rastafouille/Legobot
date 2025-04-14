#!/usr/bin/env python3
import subprocess
import os
import tempfile
import time

class RobotVoice:
    def __init__(self):
        """Initialisation de la voix du robot"""
        print("Initialisation de la voix...")
        # Vérification que piper est installé
        try:
            subprocess.run(['piper', '--version'], check=True, capture_output=True)
            print("Piper est installé")
            
            # Création du dossier wav s'il n'existe pas
            self.wav_dir = os.path.join(os.path.dirname(__file__), 'wav')
            os.makedirs(self.wav_dir, exist_ok=True)
            
        except subprocess.CalledProcessError:
            print("Erreur : Piper n'est pas installé. Veuillez l'installer avec :")
            print("pip install piper-tts")
            raise

    def speak(self, text):
        """Fait parler le robot"""
        try:
            print(f"Le robot dit : {text}")
            
            # Génération d'un nom de fichier unique
            timestamp = int(time.time())
            wav_file = os.path.join(self.wav_dir, f"speech_{timestamp}.wav")
            
            # Utilisation de piper pour la synthèse vocale
            cmd = [
                'piper',
                '--model', 'fr_FR-gilles-low',
                '--output_file', wav_file,
                '--text', text
            ]
            
            subprocess.run(cmd, check=True)
            
            # Lecture du fichier WAV avec aplay sur la sortie I2S
            aplay_cmd = [
                'aplay',
                '-q',            # Mode silencieux
                '-D', 'hw:0,0',  # Utiliser la carte son I2S
                wav_file
            ]
            subprocess.run(aplay_cmd, check=True)
            
            # Suppression du fichier temporaire
            os.remove(wav_file)
            
        except Exception as e:
            print(f"Erreur lors de la parole : {e}")
            if os.path.exists(wav_file):
                os.remove(wav_file)

if __name__ == "__main__":
    # Test de la classe
    voice = RobotVoice()
    voice.speak("Bonjour, je suis le robot LEGO")
    voice.speak("Je peux maintenant parler avec une vraie voix") 