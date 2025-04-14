#!/usr/bin/env python3
import time
from display.mouth_display import MatrixFace
from audio.robot_voice import RobotVoice

def main():
    # Initialisation de l'affichage de la bouche
    print("Initialisation de l'affichage de la bouche...")
    #mouth = MatrixFace()
    time.sleep(1)  # Attente pour la stabilisation de la matrice LED
    
    # Initialisation de la voix
    print("Initialisation de la voix...")
    voice = RobotVoice()
    
    # Test de la parole avec animation de bouche
    print("Test de la parole avec animation de bouche...")
    phrases = [
        "Bonjour, je suis le robot LEGO",
        "Je peux parler et faire des expressions",
        "Regardez mes expressions de bouche",
        "Je suis heureux de vous rencontrer"
    ]
    
    for phrase in phrases:
        print(f"Le robot dit : {phrase}")
        # Animation de bouche pendant la parole
       # mouth.animate_talk(repeat=3, speed=0.3)
        voice.speak(phrase)
        time.sleep(0.5)
    
    # Nettoyage
    print("Nettoyage...")
  #  mouth.clear()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgramme arrêté par l'utilisateur")
    except Exception as e:
        print(f"Erreur : {e}")
    finally:
        print("Fin du programme") 