# LegoBot - Robot LEGO Technic avec Raspberry Pi 5

## Description du Projet
LegoBot est un robot construit avec des composants LEGO Technic, contrôlé par une Raspberry Pi 5. Il combine la puissance des moteurs LEGO avec des capacités avancées de vision par ordinateur, d'audio et d'affichage LED.

## Installation des Dépendances

### Prérequis système
```bash
# Mise à jour du système
sudo apt-get update
sudo apt-get upgrade

# Installation des dépendances système
sudo apt-get install python3-numpy python3-picamera2 python3-build-hat python3-smbus python3-spidev python3-opencv python3-pyaudio python3-scipy

# Installation des dépendances Python supplémentaires
sudo apt-get install python3-pip python3-full

# Installation des packages Python non disponibles dans apt
sudo pip3 install --break-system-packages sounddevice luma.led_matrix
```

### Configuration système requise
Ajouter dans `/boot/config.txt` :
```
# Active le pilote audio I2S
dtoverlay=i2s-mmap

# Configuration pour la matrice LED
dtoverlay=spi1-3cs

# Active le Build HAT
dtoverlay=buildhat

# Active SPI
dtparam=spi=on
```

### Bibliothèques Python utilisées
- **Contrôle des moteurs** :
  - `python3-build-hat` : Contrôle des moteurs LEGO via Build HAT

- **Audio** :
  - `sounddevice` : Capture et lecture audio (installé via pip)
  - `python3-pyaudio` : Interface avec le microphone I2S
  - `python3-scipy` : Traitement du signal audio

- **Vision** :
  - `python3-opencv` : Traitement d'image et vision par ordinateur
  - `python3-picamera2` : Contrôle de la caméra

- **Affichage** :
  - `luma.led_matrix` : Contrôle de la matrice LED (installé via pip)
  - `python3-spidev` : Communication SPI pour la matrice LED
  - `python3-smbus` : Communication I2C

- **Calculs** :
  - `python3-numpy` : Calculs numériques et traitement de données

## Configuration de l'Environnement

### Prérequis
```bash
# Installation des outils nécessaires
sudo apt-get update
sudo apt-get install python3-venv python3-full

# Création et activation de l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installation des dépendances
pip install -r requirements.txt
```

Pour activer l'environnement virtuel à chaque session :
```bash
source venv/bin/activate
```

Pour désactiver l'environnement virtuel :
```bash
deactivate
```

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
- DIN → GPIO 10 (SPI0_MOSI)
- CS → GPIO 8 (SPI0_CE0)
- CLK → GPIO 11 (SPI0_SCLK)

### Amplificateur Audio MAX98357 I2S
- VDD → 5V
- GND → GND
- BCLK → GPIO 18
- LRCLK → GPIO 19
- DIN → GPIO 20
- SD_MODE → 3.3V (mode mono)
- GAIN → non connecté (gain par défaut 12dB)
- Sortie haut-parleur sur les bornes + et -
- Puissance de sortie : 3W classe D
- DAC intégré sans filtre

### Microphone INMP441 MEMS I2S
- VDD → 3.3V
- GND → GND
- SD (Serial Data) → GPIO 16
- SCK (Serial Clock) → GPIO 17
- WS (Word Select) → GPIO 18
- L/R → GND (pour canal gauche)
Caractéristiques :
- Type : Omnidirectionnel MEMS
- SNR : 61dB
- Sensibilité : -26dBFS
- Faible consommation d'énergie
- Format de données : 24-bit, I2S mono

## Configuration Logicielle

### Dépendances logicielles
- build-hat (bibliothèque Python pour le LEGO Build HAT)
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

## Utilisation

### Test des expressions de bouche
```bash
sudo python3 src/main.py
```

### Expressions disponibles
- `sourire` : Affiche un sourire
- `triste` : Affiche une expression triste
- `neutre` : Affiche une expression neutre
- `coeur` : Affiche un cœur
- `colere` : Affiche une expression de colère
- `vague` : Affiche une ligne ondulée 