#!/usr/bin/env python3
import time
import threading
from display.mouth_display import MatrixFace
from audio.robot_voice import RobotVoice

def main():
    """Fonction principale du robot"""
    try:
        # Initialisation des composants
        mouth = MatrixFace()
        voice = RobotVoice()
        
        # Affichage de l'expression neutre par défaut
        mouth.show_expression("neutre")
        
        # Liste des phrases à dire
        phrases = [
            "Bonjour, je suis le robot LEGO moumoute",
            "Je suis heureux de vous rencontrer",
            "je suis un robot rigolo",
            "prete a jouer les filles !"
        ]
        
        # Test de la parole avec animation de bouche
        print("\nTest de la parole avec animation de bouche...")
        for phrase in phrases:
            # Variable pour contrôler l'animation
            stop_animation = False
            
            # Fonction pour l'animation de bouche
            def animate_mouth():
                while not stop_animation:
                    mouth.animate_talk(speed=0.2)
            
            # Création des threads
            voice_thread = threading.Thread(target=voice.speak, args=(phrase,))
            animation_thread = threading.Thread(target=animate_mouth)
            
            # Démarrage des threads
            voice_thread.start()
            animation_thread.start()
            
            # Attente de la fin de la voix
            voice_thread.join()
            
            # Arrêt de l'animation
            stop_animation = True
            animation_thread.join()
            
            # Retour à la bouche neutre
            mouth.show_expression("neutre")
            # Pause entre les phrases
            time.sleep(1)
        
    except KeyboardInterrupt:
        print("\nArrêt du programme...")
    except Exception as e:
        print(f"Erreur : {e}")
    finally:
        # Nettoyage
        try:
            mouth.clear()
        except:
            pass

if __name__ == "__main__":
    main() 