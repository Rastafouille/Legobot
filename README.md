# LegoBot - Robot LEGO Technic avec Raspberry Pi 5

## Description du Projet
LegoBot est un robot construit avec des composants LEGO Technic, contrôlé par une Raspberry Pi 5. Il combine la puissance des moteurs LEGO avec des capacités avancées de vision par ordinateur, d'audio et d'affichage LED.

## Composants Matériels

### Composants Principaux
- Raspberry Pi 5
- LEGO Build HAT
- 4 moteurs LEGO Technic
- PiCamera
- Matrice LED 8x8 (pour l'affichage d'expressions)
- Microphone INMP441 MEMS I2S (MH-ET LIVE)
- Amplificateur audio MAX98357 I2S 3W classe D avec haut-parleur

### Alimentation
- Alimentation Raspberry Pi 5 : 5V/5A minimum
- Alimentation séparée pour le Build HAT et les moteurs

## Schéma de Câblage

### Build HAT (Broches réservées)
- GPIO 0/1 : ID PROM
- GPIO 4 : Reset
- GPIO 14 : Tx
- GPIO 15 : Rx
- GPIO 16 : RTS
- GPIO 17 : CTS

### PiCamera
- Connexion via le port CSI dédié de la Raspberry Pi 5

### Matrice LED 8x8 (MAX7219)
- VCC → 5V
- GND → GND
- DIN → GPIO 25
- CS → GPIO 24
- CLK → GPIO 23

### Amplificateur Audio MAX98357 I2S
- VDD → 3.3V
- GND → GND
- BCLK → GPIO 21
- LRCLK → GPIO 20
- DIN → GPIO 26
- SD_MODE → 3.3V (pour mode normal)
- GAIN → non connecté (gain par défaut 12dB)
- Sortie haut-parleur sur les bornes + et -
- Puissance de sortie : 3W classe D
- DAC intégré sans filtre

### Microphone INMP441 MEMS I2S
- VDD → 3.3V
- GND → GND
- SD (Serial Data) → GPIO 19
- SCK (Serial Clock) → GPIO 21 (partagé avec MAX98357)
- WS (Word Select) → GPIO 20 (partagé avec MAX98357)
- L/R → GND (pour canal gauche)
Caractéristiques :
- Type : Omnidirectionnel MEMS
- SNR : 61dB
- Sensibilité : -26dBFS
- Faible consommation d'énergie
- Format de données : 24-bit, I2S

## Configuration Logicielle

### Configuration système requise
Ajouter dans `/boot/config.txt` :
```
# Active le pilote audio I2S
dtoverlay=i2s-mmap

# Configuration pour la matrice LED
dtoverlay=spi1-3cs

# Active le Build HAT
dtoverlay=buildhat
```

### Dépendances logicielles
- buildhat (bibliothèque Python pour le LEGO Build HAT)
- picamera2
- python3-numpy
- python3-smbus (pour I2C)
- python3-spidev (pour SPI)

## Précautions
1. **Refroidissement**
   - Installer un dissipateur thermique sur la Raspberry Pi 5
   - Prévoir une ventilation adéquate

2. **Alimentation**
   - Utiliser une alimentation de qualité pour la Raspberry Pi 5
   - Ne pas oublier l'alimentation séparée pour les moteurs via le Build HAT

3. **Protection**
   - Vérifier toutes les connexions avant la mise sous tension
   - S'assurer d'une bonne masse commune
   - Protéger les composants des interférences électromagnétiques

## Structure du Projet
```
legobot/
├── README.md
├── src/
│   ├── motor_control/
│   ├── vision/
│   ├── audio/
│   └── display/
├── config/
└── tests/
```

## Statut du Projet
🚧 En développement

## Licence
[À définir] 