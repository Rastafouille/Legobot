# Reprise en mode robot agent

## Objectif

Transformer LegoBot en robot agent embarque sur Raspberry Pi 5, capable de:

- ecouter une demande vocale;
- comprendre une intention;
- repondre avec la voix Piper;
- animer la bouche LED pendant la parole;
- bouger via le LEGO Build HAT;
- rester testable sans materiel avec le mode mock.

## Architecture proposee

```text
src/main.py                  boucle agent interactive
src/agent.py                 cerveau local et intentions de base
src/robot.py                 orchestration voix, bouche, mouvements
src/audio/                   entree/sortie audio
src/display/                 matrice LED bouche
src/motion/                  controle LEGO Build HAT
```

## Lancement

Sur un PC de developpement, sans Raspberry ni materiel:

```bash
python3 src/main.py --mock
```

Sur la Raspberry Pi, avec les dependances installees et le materiel branche:

```bash
sudo python3 src/main.py
```

## Commandes deja gerees

- `bonjour`, `salut`
- `avance`
- `recule`
- `gauche`
- `droite`
- `stop`
- `coeur`
- `triste`
- `colere`

## Prochaines etapes conseillees

1. Ajouter une vraie transcription vocale, par exemple Whisper local ou un service distant.
2. Ajouter un fournisseur LLM derriere `LegoBotAgent` pour passer des regles simples a une conversation agentique.
3. Ajouter une configuration materielle pour les ports moteur, les vitesses et les durees de mouvement.
4. Ajouter un mode veille/reveil vocal pour eviter que le robot ecoute en continu inutilement.
5. Ajouter des tests unitaires sur `agent.py`, sans dependances Raspberry Pi.
