#!/usr/bin/env python3
import sounddevice as sd
import numpy as np
import time

def generate_tone(frequency, duration, sample_rate=44100):
    """Génère un son pur à la fréquence spécifiée"""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = np.sin(2 * np.pi * frequency * t) * 0.5
    return tone

def test_speaker():
    print("Test du haut-parleur...")
    
    # Paramètres audio
    sample_rate = 44100
    duration = 1.0
    
    try:
        # Test de différentes fréquences
        frequencies = [440, 880, 1760]  # La3, La4, La5
        
        for freq in frequencies:
            print(f"\nTest à {freq} Hz...")
            tone = generate_tone(freq, duration)
            
            # Lecture du son
            sd.play(tone, sample_rate)
            sd.wait()  # Attend que la lecture soit terminée
            
            time.sleep(0.5)  # Pause entre les sons
            
        print("\nTest terminé avec succès!")
        
    except Exception as e:
        print(f"\nErreur lors du test: {e}")

if __name__ == "__main__":
    test_speaker() 