#!/usr/bin/env python3
import time
from display.mouth_display import MatrixFace
from audio.robot_voice import RobotVoice

def main():
    print("Démarrage du test des fonctionnalités...")
    
    # Initialisation des modules
    face = MatrixFace(rotate=0, block_orientation=90)
    voice = RobotVoice()
    time.sleep(1)  # Attendre que les modules s'initialisent
    
    try:
        # Test des expressions de bouche
        print("\nTest des expressions de bouche...")
        face.show_expression("sourire", duration=2)
        face.show_expression("triste", duration=2)
        face.show_expression("neutre", duration=2)
        face.show_expression("coeur", duration=2)
        face.show_expression("colere", duration=2)
        face.show_expression("vague", duration=2)
        
        # Test du haut-parleur avec animation de bouche
        print("\nTest de la parole avec animation...")
        face.animate_talk(repeat=3, speed=0.2)
        voice.speak("Bonjour, je suis le robot LEGO")
        
        face.animate_talk(repeat=5, speed=0.2)
        voice.speak("Je peux parler et afficher des expressions")
        
    except KeyboardInterrupt:
        print("\nProgramme interrompu par l'utilisateur")
        face.clear()
    except Exception as e:
        print(f"\nErreur: {e}")
        face.clear()
    finally:
        print("\nProgramme terminé")

if __name__ == "__main__":
    main()
