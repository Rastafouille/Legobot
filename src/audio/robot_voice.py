#!/usr/bin/env python3
import time
import subprocess
import os
import tempfile

class RobotVoice:
    def __init__(self):
        """Initialisation de la voix du robot"""
        # Vérification que piper est installé
        try:
            subprocess.run(['piper', '--version'], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print("Erreur : Piper TTS n'est pas installé. Veuillez l'installer avec :")
            print("pip install piper-tts")
            raise

    def speak(self, text):
        """Fait parler le robot"""
        try:
            print(f"Le robot dit : {text}")
            
            # Création d'un fichier temporaire pour le son
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_filename = temp_file.name
            
            # Utilisation de piper pour la synthèse vocale
            cmd = [
                'piper',
                '--model', 'fr_FR-upmc-medium',
                '--output_file', temp_filename,
                '--text', text
            ]
            
            subprocess.run(cmd, check=True)
            
            # Lecture du fichier audio
            subprocess.run(['aplay', temp_filename], check=True)
            
            # Suppression du fichier temporaire
            os.unlink(temp_filename)
            
        except Exception as e:
            print(f"Erreur lors de la parole : {e}")
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

if __name__ == "__main__":
    # Test de la classe
    voice = RobotVoice()
    
    # Test de parole
    print("Test de parole...")
    voice.speak("Bonjour, je suis le robot LEGO")
    voice.speak("Je peux maintenant parler avec une vraie voix") 