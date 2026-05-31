# LegoBot / Briqo

Briqo est un robot LEGO mobile pilote par une Raspberry Pi 5. Il combine un LEGO
Build HAT, quatre moteurs, une bouche LED MAX7219, une voix locale avec Piper et
un assistant local base sur Ollama.

Le robot est pense comme un compagnon educatif pour Juliette et Roxane. Il vit
dans le sud de la France avec Jeremy, Berengere et les enfants. Il repond en
francais, garde le fil de la conversation, peut parler, afficher une expression
sur sa bouche LED, bouger la tete, les yeux et les chenilles.

## Etat Actuel

- Interface web de pilotage sur `http://192.168.1.62:8080`
- Service systemd `legobot-web.service` lance au demarrage de la Raspberry Pi
- Ollama principal sur le PC du reseau: `http://192.168.1.12:11434`
- Modele principal: `qwen3.5:latest`
- Fallback local sur la Raspberry Pi: `qwen2.5:1.5b`
- Voix locale avec Piper, par defaut sur le modele `next`
- Selecteur de voix Piper base sur les fichiers `.onnx` presents dans `src/audio`
- Bouche LED MAX7219 avec expressions et animations
- Historique de conversation persistant dans `data/conversation_history.jsonl`
- Gestes IA optionnels, limites par liste blanche

## Architecture

```text
Navigateur
  -> Flask sur Raspberry Pi 5
      -> Build HAT: moteurs, tete, yeux, chenilles
      -> MAX7219: bouche LED
      -> Piper + MAX98357A: voix
      -> Ollama PC: qwen3.5:latest
      -> Ollama Raspberry: qwen2.5:1.5b en secours
```

Ollama ne controle jamais directement les moteurs. Il propose une intention sous
forme de texte ou de JSON. Le code Flask valide ensuite les expressions et les
mouvements autorises avant d'agir.

## Interface Web

Lancer dans un navigateur:

```text
http://192.168.1.62:8080
```

L'interface permet de:

- piloter les chenilles avec un joystick
- bouger la tete et les yeux
- choisir une expression de bouche
- lancer une animation de bouche
- afficher une lettre, un chiffre, un mot court ou un bitmap 8x8 sur la bouche
- reinitialiser la bouche LED
- redemarrer le service moteur si le Build HAT devient muet
- faire parler Briqo
- choisir une voix Piper
- ecouter le micro USB et transcrire en local
- envoyer la transcription directement a l'assistant
- lancer une veille vocale avec le mot-cle `ok briko`
- envoyer une question a l'assistant
- autoriser ou non les gestes simples de l'IA
- effacer l'historique de conversation

## Assistant

Par defaut, Briqo utilise le modele du PC:

```text
LEGOBOT_OLLAMA_URL=http://192.168.1.12:11434
LEGOBOT_OLLAMA_MODEL=qwen3.5:latest
```

Si le PC ou ce modele ne repond pas, le code bascule sur la Raspberry:

```text
LEGOBOT_FALLBACK_OLLAMA_URL=http://127.0.0.1:11434
LEGOBOT_FALLBACK_OLLAMA_MODEL=qwen2.5:1.5b
```

Le PC doit lancer Ollama avec:

```text
OLLAMA_HOST=0.0.0.0:11434
```

Sous Windows, cette variable est configuree avec `setx`, et Ollama est ajoute au
demarrage de session utilisateur.

## Voix Piper

Les voix disponibles sont detectees automatiquement dans:

```text
src/audio/*.onnx
```

Chaque modele doit avoir son fichier de configuration associe:

```text
src/audio/nom-de-voix.onnx
src/audio/nom-de-voix.onnx.json
```

L'interface appelle `GET /api/voices` puis remplit le selecteur de voix. La voix
choisie est envoyee a `/api/say` et `/api/ask` avec `voice_model`.

Voix installees:

```text
fr_FR-gilles-low
tom1
tom2
next
```

Les voix `tom1`, `tom2` et `next` viennent du depot
`tjiho/French-tts-model-piper`, qui fournit trois modeles francais Piper
entraines a partir de textes francais.

Voix par defaut configurable:

```text
LEGOBOT_VOICE_MODEL=next
```

## Memoire De Conversation

Les messages utilisateur et assistant sont conserves dans une memoire courte et
sauvegardes dans:

```text
data/conversation_history.jsonl
```

Au redemarrage du service, les derniers messages sont relus puis reinjectes dans
les appels Ollama. Cela permet a Briqo de garder le fil de la discussion.

Parametres utiles:

```text
LEGOBOT_HISTORY_FILE=data/conversation_history.jsonl
LEGOBOT_HISTORY_MAX_MESSAGES=24
LEGOBOT_OLLAMA_MAX_TOKENS=520
```

## Micro Et Speech-To-Text

Le micro USB est utilise via ALSA. Par defaut:

```text
LEGOBOT_MIC_DEVICE=plughw:CARD=Device,DEV=0
LEGOBOT_MIC_RATE=16000
LEGOBOT_VOSK_MODEL=models/vosk-model-small-fr-0.22
LEGOBOT_WAKE_ON_START=1
LEGOBOT_WAKE_SILENCE_SECONDS=0.75
LEGOBOT_WAKE_MAX_SECONDS=5.0
LEGOBOT_MIC_SPEECH_RMS=900
```

Le modele local installe sur la Raspberry est:

```text
models/vosk-model-small-fr-0.22
```

Installation du moteur STT et du modele Vosk:

```bash
cd ~/Legobot
python3 -m pip install --break-system-packages vosk
mkdir -p models
wget https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip -O /tmp/vosk-fr.zip
unzip /tmp/vosk-fr.zip -d models
```

Endpoints:

```text
POST /api/listen
```

Exemple transcription seule:

```json
{
  "duration": 4,
  "ask": false
}
```

Exemple transcription puis reponse de Briqo:

```json
{
  "duration": 4,
  "ask": true,
  "speak": true,
  "allow_actions": true
}
```

Veille vocale:

```text
POST /api/wake/start
POST /api/wake/stop
GET  /api/wake/status
```

La veille ecoute en continu le mot-cle `ok briko` ou `ok brico`. Elle demarre
par defaut avec le service web. Au repos, la
bouche reste sur `sourire`. Quand le mot-cle est detecte, Briqo passe sur une
bouche d'ecoute, enregistre la phrase suivante, attend environ 0,75 seconde de
silence, transcrit localement avec Vosk puis envoie la demande a Ollama. Le
plafond `LEGOBOT_WAKE_MAX_SECONDS` evite une attente longue si le bruit de fond
empeche la detection de silence. Les
gestes simples sont actives par defaut dans l'interface.

## Gestes IA

Le mode "Autoriser gestes simples" demande a Ollama de repondre avec un JSON:

```json
{
  "say": "Bonjour Juliette !",
  "expression": "grand_sourire",
  "motion": "head_center"
}
```

Les expressions autorisees:

```text
neutre, sourire, grand_sourire, triste, surpris, parle,
coeur, colere, vague, baiser
```

Les mouvements autorises:

```text
none, head_left, head_right, head_center,
eyes_up, eyes_down, eyes_center,
forward, backward, left, right, stop
```

Tout mouvement ou expression hors liste est ignore ou remplace par une valeur
sure.

La bouche peut aussi recevoir une sortie visuelle plus libre:

```json
{
  "mouth": {
    "mode": "text",
    "value": "OK"
  }
}
```

ou un bitmap 8x8 strict:

```json
{
  "mouth": {
    "mode": "bitmap",
    "pixels": [
      "........",
      "..####..",
      ".#....#.",
      ".#.##.#.",
      ".#....#.",
      "..####..",
      "........",
      "........"
    ]
  }
}
```

Le code valide exactement 8 lignes de 8 caracteres. `#` allume une LED, `.`
l'eteint. Les lettres et chiffres sont rendus avec une petite police 5x7 et les
mots defilent automatiquement.

Pour les dessins, preferer les icones integrees au bitmap libre. Une matrice 8x8
est tres limitee, donc les bitmaps generes directement par le LLM sont souvent
peu lisibles. Les icones disponibles sont:

```text
coeur, etoile, soleil, lune, maison, eclair, fleur, livre, note, check, croix,
ampoule
```

Exemple:

```json
{
  "mouth": {
    "mode": "icon",
    "value": "etoile"
  }
}
```

Apres un defilement de texte, la bouche revient automatiquement sur `sourire`.

## Materiel

- Raspberry Pi 5
- LEGO Build HAT
- 4 moteurs LEGO Technic
- Matrice LED 8x8 MAX7219 pour la bouche
- Amplificateur MAX98357A I2S + haut-parleur
- Micro USB pour la reconnaissance vocale locale
- Alimentation separee pour le Build HAT et les moteurs

## Ports Moteurs

```text
A: yeux
B: rotation de la tete
C: chenille droite
D: chenille gauche
```

La chenille droite est inversee dans le code pour compenser le montage. Les
chenilles C/D sont pilotees en PWM pour donner plus de couple et eviter les
commandes de vitesse trop molles du Build HAT.

Calibration moteur configurable dans systemd:

```text
LEGOBOT_HEAD_DEGREES=28
LEGOBOT_EYES_DEGREES=14
LEGOBOT_MOTOR_SPEED=35
```

Les yeux ont une amplitude volontairement reduite pour eviter de toucher
l'afficheur LED.

## Cablage Principal

### MAX7219

```text
VCC -> 5V
GND -> GND
DIN -> GPIO 10 / SPI0 MOSI
CS  -> GPIO 8 / SPI0 CE0
CLK -> GPIO 11 / SPI0 SCLK
```

### MAX98357A

```text
VDD   -> 5V
GND   -> GND
BCLK  -> GPIO 18
LRCLK -> GPIO 19
DIN   -> GPIO 21
```

### Build HAT

Le Build HAT reserve notamment:

```text
GPIO 4  : reset
GPIO 14 : TX
GPIO 15 : RX
GPIO 16 : RTS
GPIO 17 : CTS
```

## Installation Raspberry Pi

Dependances systeme principales:

```bash
sudo apt-get update
sudo apt-get install -y python3-build-hat python3-spidev python3-smbus \
  python3-scipy python3-pip python3-full sox
sudo pip3 install --break-system-packages flask luma.led_matrix piper-tts
```

Ollama local de secours:

```bash
ollama pull qwen2.5:1.5b
```

## Demarrage Manuel

Sur la Raspberry Pi:

```bash
cd ~/Legobot
export PYTHONPATH=$PWD/src
export LEGOBOT_ROBOT_NAME=Briqo
export LEGOBOT_VOICE_MODEL=next
export LEGOBOT_OLLAMA_URL=http://192.168.1.12:11434
export LEGOBOT_OLLAMA_MODEL=qwen3.5:latest
export LEGOBOT_FALLBACK_OLLAMA_URL=http://127.0.0.1:11434
export LEGOBOT_FALLBACK_OLLAMA_MODEL=qwen2.5:1.5b
export LEGOBOT_WAKE_ON_START=1
export LEGOBOT_WAKE_SILENCE_SECONDS=0.75
export LEGOBOT_WAKE_MAX_SECONDS=5.0
python3 src/web_control.py --host 0.0.0.0 --port 8080
```

L'interface est ensuite disponible depuis le reseau local:

```text
http://192.168.1.62:8080
```

Pour tester rapidement les briques sans navigateur:

```bash
curl http://127.0.0.1:8080/api/status
curl http://127.0.0.1:8080/api/wake/status
curl -X POST http://127.0.0.1:8080/api/mouth \
  -H 'Content-Type: application/json' \
  -d '{"expression":"sourire"}'
```

## Service Au Demarrage

Le service est versionne dans:

```text
deploy/legobot-web.service
```

Installation sur la Raspberry:

```bash
sudo install -m 0644 deploy/legobot-web.service /etc/systemd/system/legobot-web.service
sudo systemctl daemon-reload
sudo systemctl enable --now legobot-web.service
```

Verification:

```bash
systemctl status legobot-web.service
journalctl -u legobot-web.service -n 100 --no-pager
curl http://127.0.0.1:8080/api/status
```

## Endpoints Utiles

```text
GET  /api/status
POST /api/ask
POST /api/say
GET  /api/voices
POST /api/listen
POST /api/wake/start
POST /api/wake/stop
GET  /api/wake/status
POST /api/mouth
POST /api/mouth-animation
POST /api/mouth-text
POST /api/mouth-bitmap
POST /api/mouth-icon
POST /api/mouth-reset
POST /api/head
POST /api/eyes
POST /api/joystick
POST /api/stop
POST /api/motors-reset
POST /api/motor-test
GET  /api/history
POST /api/history/clear
```

## Notes

- Tete et yeux utilisent des impulsions courtes, car les commandes positionnelles
  Build HAT peuvent bloquer.
- La bouche LED demarre et revient par defaut sur un sourire.
- La bouche LED peut etre reinitialisee depuis l'interface avec "Reset bouche LED".
- Le bouton "Reset moteurs" redemarre le service web via systemd. C'est plus lent
  qu'un reset a chaud, mais plus fiable quand le thread serie Build HAT se bloque.
- Le volume Piper peut clipper si le gain est trop haut. Un gain entre 2 et 4 est
  generalement plus propre que 18.
- Les gros fichiers locaux ne sont pas versionnes: historique `data/`, WAV
  temporaires, caches Python et modeles Vosk dans `models/`.
