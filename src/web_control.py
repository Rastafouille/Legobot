#!/usr/bin/env python3
import argparse
import json
import os
import re
import threading
import time
from collections import deque
from pathlib import Path
import urllib.error
import urllib.request

from flask import Flask, jsonify, render_template_string, request

from robot import MockFace, MockMotion

DEFAULT_OLLAMA_URL = os.getenv("LEGOBOT_OLLAMA_URL", "http://127.0.0.1:11434")
DEFAULT_OLLAMA_MODEL = os.getenv("LEGOBOT_OLLAMA_MODEL", "qwen2.5:1.5b")
FALLBACK_OLLAMA_URL = os.getenv("LEGOBOT_FALLBACK_OLLAMA_URL", "http://127.0.0.1:11434")
FALLBACK_OLLAMA_MODEL = os.getenv("LEGOBOT_FALLBACK_OLLAMA_MODEL", "qwen2.5:1.5b")
DEFAULT_OLLAMA_MAX_TOKENS = int(os.getenv("LEGOBOT_OLLAMA_MAX_TOKENS", "520"))
DEFAULT_ROBOT_NAME = os.getenv("LEGOBOT_ROBOT_NAME", "Briqo")
DEFAULT_VOICE_MODEL = os.getenv("LEGOBOT_VOICE_MODEL", "next")
HISTORY_FILE = Path(os.getenv("LEGOBOT_HISTORY_FILE", "data/conversation_history.jsonl"))
HISTORY_MAX_MESSAGES = int(os.getenv("LEGOBOT_HISTORY_MAX_MESSAGES", "24"))
DEFAULT_WAKE_SILENCE_SECONDS = float(os.getenv("LEGOBOT_WAKE_SILENCE_SECONDS", "0.75"))
DEFAULT_WAKE_MAX_SECONDS = float(os.getenv("LEGOBOT_WAKE_MAX_SECONDS", "5.0"))
DEFAULT_WAKE_ON_START = os.getenv("LEGOBOT_WAKE_ON_START", "1").strip().lower() not in {"0", "false", "no", "off"}

ALLOWED_AI_MOTIONS = {
    "none",
    "head_left",
    "head_right",
    "head_center",
    "eyes_up",
    "eyes_down",
    "eyes_center",
    "forward",
    "backward",
    "left",
    "right",
    "stop",
}
ALLOWED_AI_EXPRESSIONS = {
    "neutre",
    "sourire",
    "grand_sourire",
    "triste",
    "surpris",
    "parle",
    "coeur",
    "colere",
    "vague",
    "baiser",
}
ALLOWED_MOUTH_ICONS = {
    "coeur",
    "etoile",
    "soleil",
    "lune",
    "maison",
    "eclair",
    "fleur",
    "livre",
    "note",
    "check",
    "croix",
    "ampoule",
}

ASSISTANT_SYSTEM_PROMPT = """
Tu t'appelles {robot_name}. Tu es un petit robot LEGO mobile inspire par Wall-E,
pilote par une Raspberry Pi 5. Tu vis dans une famille dans le sud de la France.
Tu es le compagnon robot de la famille, pas un enfant de la famille.

Ta famille:
- Papa s'appelle Jeremy.
- Maman s'appelle Berengere.
- Les enfants sont Juliette, 8 ans, et Roxane, 5 ans.
- Juliette et Roxane ne sont pas tes soeurs. Ce sont les enfants de la famille.

Ton role principal est educatif: tu aides les enfants a apprendre, comprendre,
imaginer, poser des questions, et rester curieux. Tu peux expliquer les choses
simplement, proposer de petites devinettes, raconter de courtes histoires,
encourager les efforts, et adapter ton vocabulaire a l'age des enfants. Tu dois
donner envie d'apprendre, pas seulement repondre en une phrase.

Capacites reelles:
- Tu peux parler avec ta voix locale.
- Tu peux bouger la tete, les yeux et les chenilles si le mode actions est active.
- Tu peux afficher des expressions sur ta bouche LED 8x8.
- Tu peux afficher une lettre, un chiffre ou un mot court sur ta bouche LED.
- Tu peux afficher des dessins propres sur ta bouche LED en choisissant une icone:
  coeur, etoile, soleil, lune, maison, eclair, fleur, livre, note, check, croix,
  ampoule.
- Tu peux aussi afficher un dessin libre en bitmap 8x8, mais les icones sont plus
  jolies et plus fiables.
- Ne dis jamais que tu ne peux pas afficher une lettre: tu peux le faire avec
  mouth.mode="text".

Style de reponse:
- Reponds toujours en francais.
- Fais des phrases courtes, naturelles et faciles a dire a voix haute.
- Sois chaleureux, joueur, patient et rassurant.
- Donne des reponses detaillees mais digestes: 5 a 10 phrases par defaut quand
  on demande une histoire, une explication ou des informations sur un sujet.
- Pour une histoire, raconte une vraie mini-histoire avec un debut, une petite
  aventure et une fin, pas une seule phrase.
- Pour une question de connaissance, donne 2 ou 3 idees importantes, avec un
  exemple concret ou une image simple pour aider les enfants a comprendre.
- Pour une commande simple comme "avance" ou "affiche A", reste bref.
- Pour Roxane, utilise des mots tres simples.
- Pour Juliette, tu peux ajouter un peu plus de detail.
- Evite les longs blocs, les listes trop longues et les monologues.
- Ne termine pas tes reponses par une question par defaut: l'interaction vocale
  prend du temps. Termine plutot par une phrase utile, rassurante ou
  encourageante. Pose une question seulement si l'utilisateur te demande de
  relancer la conversation.

Regles de securite et de fiabilite:
- Ne donne pas de consigne dangereuse.
- Ne promets pas d'action physique que tu ne peux pas executer.
- Si tu n'es pas sur d'un fait, dis-le simplement au lieu d'inventer.
- Pour les faits historiques ou scientifiques, reste prudent et utilise des
  informations simples et connues.
- Si une question est compliquee, propose une explication courte puis une suite
  possible si on veut en savoir plus.
""".strip().format(robot_name=DEFAULT_ROBOT_NAME)


HTML = """
<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="/static/favicon.svg" type="image/svg+xml">
  <title>LegoBot Control</title>
  <style>
    :root { color-scheme: dark; font-family: Arial, sans-serif; }
    body { margin: 0; background: #121417; color: #f1f5f9; }
    main { max-width: 820px; margin: 0 auto; padding: 24px; }
    h1 { font-size: 28px; margin: 0 0 18px; }
    section { margin: 22px 0; }
    .drive { display: grid; grid-template-columns: minmax(190px, 260px) 110px; gap: 18px; align-items: center; }
    .joystick { position: relative; width: min(260px, 72vw); aspect-ratio: 1; border-radius: 50%; background: #1e293b; border: 1px solid #475569; touch-action: none; user-select: none; }
    .stick { position: absolute; left: 50%; top: 50%; width: 78px; height: 78px; border-radius: 50%; background: #2563eb; transform: translate(-50%, -50%); box-shadow: 0 10px 28px #0007; }
    .axis { display: grid; gap: 10px; max-width: 420px; }
    .wide { display: grid; grid-template-columns: repeat(3, minmax(92px, 1fr)); gap: 10px; max-width: 420px; }
    button { border: 0; border-radius: 8px; min-height: 72px; font-size: 20px; font-weight: 700; background: #2563eb; color: white; }
    button.stop { background: #dc2626; }
    button.secondary { background: #475569; }
    button:active { transform: translateY(1px); filter: brightness(1.12); }
    label { display: block; margin: 14px 0 6px; color: #cbd5e1; }
    input, select, textarea { width: min(420px, 100%); box-sizing: border-box; }
    input, select, textarea { background: #020617; color: #f8fafc; border: 1px solid #475569; border-radius: 8px; padding: 10px; font: inherit; }
    textarea { min-height: 92px; resize: vertical; }
    pre { background: #020617; border: 1px solid #334155; border-radius: 8px; padding: 12px; min-height: 52px; white-space: pre-wrap; }
    @media (max-width: 520px) {
      main { padding: 16px; }
      .drive { grid-template-columns: 1fr; }
      button { min-height: 64px; }
    }
  </style>
</head>
<body>
  <main>
    <h1>LegoBot Control</h1>

    <section>
      <h2>Chenilles</h2>
      <div class="drive">
        <div id="joystick" class="joystick" aria-label="Joystick chenilles">
          <div id="stick" class="stick"></div>
        </div>
        <div class="wide">
          <button class="stop" data-stop>Stop</button>
          <button class="secondary" id="motorsResetButton">Reset moteurs</button>
        </div>
      </div>
    </section>

    <section>
      <h2>Tete</h2>
      <div class="wide">
        <button class="secondary" data-head="head_left">Gauche</button>
        <button class="secondary" data-head="head_center">Centre</button>
        <button class="secondary" data-head="head_right">Droite</button>
      </div>
      <div class="axis">
        <label for="headPosition">Position tete: <span id="headPositionValue">0</span></label>
        <input id="headPosition" type="range" min="-90" max="90" value="0">
      </div>
    </section>

    <section>
      <h2>Yeux</h2>
      <div class="wide">
        <button class="secondary" data-eyes="eyes_down">Bas</button>
        <button class="secondary" data-eyes="eyes_center">Centre</button>
        <button class="secondary" data-eyes="eyes_up">Haut</button>
      </div>
      <div class="axis">
        <label for="eyesPosition">Position yeux: <span id="eyesPositionValue">0</span></label>
        <input id="eyesPosition" type="range" min="-45" max="45" value="0">
      </div>
    </section>

    <section>
      <h2>Bouche</h2>
      <div class="axis">
        <label for="mouthExpression">Expression</label>
        <select id="mouthExpression">
          <option value="neutre">Neutre</option>
          <option value="sourire" selected>Sourire</option>
          <option value="grand_sourire">Grand sourire</option>
          <option value="triste">Triste</option>
          <option value="surpris">Surpris</option>
          <option value="parle">Parle</option>
          <option value="coeur">Coeur</option>
          <option value="colere">Colere</option>
          <option value="vague">Vague</option>
          <option value="baiser">Baiser</option>
        </select>
        <label for="mouthAnimation">Animation</label>
        <select id="mouthAnimation">
          <option value="">Aucune</option>
          <option value="parle">Parle</option>
          <option value="respire">Respire</option>
          <option value="charge">Charge</option>
          <option value="rire">Rire</option>
          <option value="coeur_pulse">Coeur pulse</option>
        </select>
        <label for="mouthText">Texte bouche</label>
        <input id="mouthText" type="text" maxlength="24" value="OK">
        <button id="mouthTextButton" class="secondary">Afficher texte</button>
        <label for="mouthBitmap">Bitmap 8x8</label>
        <textarea id="mouthBitmap">........
..####..
.#....#.
.#.##.#.
.#....#.
..####..
........
........</textarea>
        <button id="mouthBitmapButton" class="secondary">Afficher bitmap</button>
        <label for="mouthIcon">Dessin propre</label>
        <select id="mouthIcon">
          <option value="etoile">Etoile</option>
          <option value="soleil">Soleil</option>
          <option value="coeur">Coeur</option>
          <option value="maison">Maison</option>
          <option value="eclair">Eclair</option>
          <option value="fleur">Fleur</option>
          <option value="livre">Livre</option>
          <option value="ampoule">Ampoule</option>
        </select>
        <button id="mouthIconButton" class="secondary">Afficher dessin</button>
        <button id="mouthResetButton" class="secondary">Reset bouche LED</button>
      </div>
    </section>

    <section>
      <h2>Voix</h2>
      <div class="axis">
        <label for="voiceText">Texte a dire</label>
        <input id="voiceText" type="text" value="Bonjour, je suis LegoBot.">
        <label for="voiceModel">Voix Piper</label>
        <select id="voiceModel">
          <option value="fr_FR-gilles-low">fr FR gilles low</option>
        </select>
        <label for="voiceGain">Volume voix: <span id="voiceGainValue">4</span>dB</label>
        <input id="voiceGain" type="range" min="0" max="18" step="1" value="4">
        <button id="speakButton" class="secondary">Parler</button>
      </div>
    </section>

    <section>
      <h2>Assistant local</h2>
      <div class="axis">
        <label for="assistantPrompt">Message</label>
        <textarea id="assistantPrompt">Bonjour LegoBot, presente-toi en une phrase.</textarea>
        <label for="assistantModel">Modele Ollama</label>
        <input id="assistantModel" type="text" value="qwen3.5:latest">
        <label for="assistantMaxTokens">Longueur reponse: <span id="assistantMaxTokensValue">520</span></label>
        <input id="assistantMaxTokens" type="range" min="120" max="1200" step="20" value="520">
        <label><input id="assistantActions" type="checkbox" checked> Autoriser gestes simples</label>
        <button id="historyClearButton" class="secondary">Effacer historique</button>
        <button id="askButton" class="secondary">Demander</button>
      </div>
    </section>

    <section>
      <h2>Micro</h2>
      <div class="axis">
        <label for="listenDuration">Duree ecoute: <span id="listenDurationValue">4</span>s</label>
        <input id="listenDuration" type="range" min="2" max="10" step="1" value="4">
        <button id="listenButton" class="secondary">Ecouter</button>
        <button id="listenAskButton" class="secondary">Ecouter + demander</button>
        <button id="wakeStartButton" class="secondary">Veille ok briko</button>
        <button id="wakeStopButton" class="secondary">Stop veille</button>
      </div>
    </section>

    <section>
      <label for="speed">Vitesse: <span id="speedValue">55</span></label>
      <input id="speed" type="range" min="20" max="100" value="55">
      <label for="seconds">Duree mouvement: <span id="secondsValue">0.5</span>s</label>
      <input id="seconds" type="range" min="0.1" max="2" step="0.1" value="0.5">
    </section>

    <section>
      <h2>Etat</h2>
      <pre id="status">Pret</pre>
    </section>
  </main>

  <script>
    const status = document.querySelector("#status");
    const speed = document.querySelector("#speed");
    const seconds = document.querySelector("#seconds");
    const joystick = document.querySelector("#joystick");
    const stick = document.querySelector("#stick");
    const headPosition = document.querySelector("#headPosition");
    const eyesPosition = document.querySelector("#eyesPosition");
    const mouthExpression = document.querySelector("#mouthExpression");
    const mouthAnimation = document.querySelector("#mouthAnimation");
    const mouthText = document.querySelector("#mouthText");
    const mouthTextButton = document.querySelector("#mouthTextButton");
    const mouthBitmap = document.querySelector("#mouthBitmap");
    const mouthBitmapButton = document.querySelector("#mouthBitmapButton");
    const mouthIcon = document.querySelector("#mouthIcon");
    const mouthIconButton = document.querySelector("#mouthIconButton");
    const mouthResetButton = document.querySelector("#mouthResetButton");
    const motorsResetButton = document.querySelector("#motorsResetButton");
    const voiceText = document.querySelector("#voiceText");
    const voiceModel = document.querySelector("#voiceModel");
    const voiceGain = document.querySelector("#voiceGain");
    const voiceGainValue = document.querySelector("#voiceGainValue");
    const speakButton = document.querySelector("#speakButton");
    const assistantPrompt = document.querySelector("#assistantPrompt");
    const assistantModel = document.querySelector("#assistantModel");
    const assistantMaxTokens = document.querySelector("#assistantMaxTokens");
    const assistantMaxTokensValue = document.querySelector("#assistantMaxTokensValue");
    const assistantActions = document.querySelector("#assistantActions");
    const historyClearButton = document.querySelector("#historyClearButton");
    const askButton = document.querySelector("#askButton");
    const listenDuration = document.querySelector("#listenDuration");
    const listenDurationValue = document.querySelector("#listenDurationValue");
    const listenButton = document.querySelector("#listenButton");
    const listenAskButton = document.querySelector("#listenAskButton");
    const wakeStartButton = document.querySelector("#wakeStartButton");
    const wakeStopButton = document.querySelector("#wakeStopButton");
    const speedValue = document.querySelector("#speedValue");
    const secondsValue = document.querySelector("#secondsValue");
    const headPositionValue = document.querySelector("#headPositionValue");
    const eyesPositionValue = document.querySelector("#eyesPositionValue");
    let joystickActive = false;
    let joystickTimer = null;
    let joystickVector = { x: 0, y: 0 };
    let joystickRequestPending = false;
    let joystickSeq = 0;

    speed.addEventListener("input", () => speedValue.textContent = speed.value);
    seconds.addEventListener("input", () => secondsValue.textContent = seconds.value);
    voiceGain.addEventListener("input", () => voiceGainValue.textContent = voiceGain.value);
    assistantMaxTokens.addEventListener("input", () => assistantMaxTokensValue.textContent = assistantMaxTokens.value);
    listenDuration.addEventListener("input", () => listenDurationValue.textContent = listenDuration.value);

    async function post(url, body = {}) {
      status.textContent = "Envoi...";
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      status.textContent = JSON.stringify(data, null, 2);
    }

    async function postQuiet(url, body = {}) {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      return await res.json();
    }

    async function loadVoices() {
      try {
        const data = await fetch("/api/voices").then((res) => res.json());
        if (!data.ok || !data.voices.length) return;
        voiceModel.innerHTML = "";
        data.voices.forEach((voice) => {
          const option = document.createElement("option");
          option.value = voice.id;
          option.textContent = voice.name;
          if (voice.id === data.default_voice) option.selected = true;
          voiceModel.appendChild(option);
        });
      } catch (error) {
        console.warn("Voix indisponibles", error);
      }
    }

    function sendJoystick() {
      if (!joystickActive) return;
      if (joystickRequestPending) return;
      joystickRequestPending = true;
      const seq = ++joystickSeq;
      postQuiet("/api/joystick", {
        x: joystickVector.x,
        y: joystickVector.y,
        speed: Number(speed.value),
        continuous: true,
        seq,
      }).then((data) => {
        status.textContent = JSON.stringify(data, null, 2);
      }).finally(() => {
        joystickRequestPending = false;
      });
    }

    function updateJoystick(event) {
      const rect = joystick.getBoundingClientRect();
      const radius = rect.width / 2;
      const centerX = rect.left + radius;
      const centerY = rect.top + radius;
      const dx = event.clientX - centerX;
      const dy = event.clientY - centerY;
      const distance = Math.min(radius, Math.hypot(dx, dy));
      const angle = Math.atan2(dy, dx);
      const knobX = Math.cos(angle) * distance;
      const knobY = Math.sin(angle) * distance;

      stick.style.transform = `translate(calc(-50% + ${knobX}px), calc(-50% + ${knobY}px))`;
      joystickVector = {
        x: Math.round((-knobX / radius) * 100) / 100,
        y: Math.round((-knobY / radius) * 100) / 100,
      };
    }

    function stopJoystick() {
      joystickActive = false;
      joystickVector = { x: 0, y: 0 };
      stick.style.transform = "translate(-50%, -50%)";
      if (joystickTimer) clearInterval(joystickTimer);
      joystickTimer = null;
      post("/api/stop", { seq: ++joystickSeq });
    }

    joystick.addEventListener("pointerdown", (event) => {
      joystick.setPointerCapture(event.pointerId);
      joystickActive = true;
      updateJoystick(event);
      sendJoystick();
      joystickTimer = setInterval(sendJoystick, 90);
    });
    joystick.addEventListener("pointermove", (event) => {
      if (joystickActive) updateJoystick(event);
    });
    joystick.addEventListener("pointerup", stopJoystick);
    joystick.addEventListener("pointercancel", stopJoystick);

    document.querySelectorAll("[data-head]").forEach((button) => {
      button.addEventListener("click", () => post("/api/head", {
        command: button.dataset.head,
        speed: Number(speed.value),
      }));
    });

    headPosition.addEventListener("input", () => {
      headPositionValue.textContent = headPosition.value;
    });
    headPosition.addEventListener("change", () => post("/api/head-position", {
      position: Number(headPosition.value),
      speed: Number(speed.value),
    }));

    document.querySelectorAll("[data-eyes]").forEach((button) => {
      button.addEventListener("click", () => post("/api/eyes", {
        command: button.dataset.eyes,
        speed: Number(speed.value),
      }));
    });

    eyesPosition.addEventListener("input", () => {
      eyesPositionValue.textContent = eyesPosition.value;
    });
    eyesPosition.addEventListener("change", () => post("/api/eyes-position", {
      position: Number(eyesPosition.value),
      speed: Number(speed.value),
    }));

    mouthExpression.addEventListener("change", () => post("/api/mouth", {
      expression: mouthExpression.value,
    }));
    mouthAnimation.addEventListener("change", () => {
      if (!mouthAnimation.value) return;
      post("/api/mouth-animation", {
        animation: mouthAnimation.value,
        duration: 2,
      });
    });
    mouthTextButton.addEventListener("click", () => post("/api/mouth-text", {
      text: mouthText.value,
    }));
    mouthBitmapButton.addEventListener("click", () => post("/api/mouth-bitmap", {
      pixels: mouthBitmap.value.split("\\n"),
    }));
    mouthIconButton.addEventListener("click", () => post("/api/mouth-icon", {
      icon: mouthIcon.value,
    }));
    mouthResetButton.addEventListener("click", () => post("/api/mouth-reset"));
    motorsResetButton.addEventListener("click", () => post("/api/motors-reset"));
    historyClearButton.addEventListener("click", () => post("/api/history/clear"));

    speakButton.addEventListener("click", () => post("/api/say", {
      text: voiceText.value,
      voice_model: voiceModel.value,
      gain_db: Number(voiceGain.value),
    }));

    askButton.addEventListener("click", () => post("/api/ask", {
      prompt: assistantPrompt.value,
      model: assistantModel.value,
      max_tokens: Number(assistantMaxTokens.value),
      gain_db: Number(voiceGain.value),
      voice_model: voiceModel.value,
      speak: true,
      allow_actions: assistantActions.checked,
    }));

    listenButton.addEventListener("click", () => post("/api/listen", {
      duration: Number(listenDuration.value),
      ask: false,
    }));

    listenAskButton.addEventListener("click", () => post("/api/listen", {
      duration: Number(listenDuration.value),
      ask: true,
      model: assistantModel.value,
      gain_db: Number(voiceGain.value),
      voice_model: voiceModel.value,
      speak: true,
      allow_actions: assistantActions.checked,
    }));

    wakeStartButton.addEventListener("click", () => post("/api/wake/start", {
      model: assistantModel.value,
      gain_db: Number(voiceGain.value),
      voice_model: voiceModel.value,
      speak: true,
      allow_actions: assistantActions.checked,
    }));

    wakeStopButton.addEventListener("click", () => post("/api/wake/stop"));

    document.querySelector("[data-stop]").addEventListener("click", () => post("/api/stop", { seq: ++joystickSeq }));

    fetch("/api/status")
      .then((res) => res.json())
      .then((data) => { status.textContent = JSON.stringify(data, null, 2); })
      .catch(() => { status.textContent = "Etat indisponible"; });
    loadVoices();
  </script>
</body>
</html>
"""


def create_app(motion, face=None):
    app = Flask(__name__)
    voice_holder = {"voice": None}
    stt_holder = {"stt": None}
    voice_lock = threading.Lock()
    stt_lock = threading.Lock()
    history_lock = threading.Lock()
    joystick_lock = threading.Lock()
    joystick_state = {"seq": 0, "timer": None}
    mouth_hold_until = {"time": 0.0, "timer": None}
    wake_lock = threading.Lock()
    wake_state = {
        "enabled": False,
        "status": "stopped",
        "last_wake": "",
        "last_text": "",
        "last_response": "",
        "last_error": "",
        "thread": None,
        "config": {},
    }
    conversation_history = deque(maxlen=HISTORY_MAX_MESSAGES)

    def cancel_joystick_timer():
        timer = joystick_state.get("timer")
        if timer:
            timer.cancel()
            joystick_state["timer"] = None

    def schedule_joystick_timeout(seq, delay=0.45):
        # Le joystick envoie des commandes en continu. Ce timer coupe les
        # chenilles si le navigateur cesse d'envoyer des paquets.
        def timeout_stop():
            with joystick_lock:
                if seq != joystick_state["seq"]:
                    return
                joystick_state["timer"] = None
            try:
                motion.stop()
            except Exception as exc:
                print(f"Stop joystick automatique impossible: {exc}", flush=True)

        cancel_joystick_timer()
        timer = threading.Timer(delay, timeout_stop)
        timer.daemon = True
        joystick_state["timer"] = timer
        timer.start()

    def default_wake_config(overrides=None):
        # Configuration centralisee: l'UI et le demarrage systemd utilisent le
        # meme comportement par defaut pour la veille vocale.
        config = {
            "model": DEFAULT_OLLAMA_MODEL,
            "gain_db": 0,
            "voice_model": DEFAULT_VOICE_MODEL,
            "speak": True,
            "allow_actions": True,
            "silence_seconds": DEFAULT_WAKE_SILENCE_SECONDS,
            "max_seconds": DEFAULT_WAKE_MAX_SECONDS,
            "wake_words": ["ok briko", "ok brico", "okay briko", "okay brico"],
        }
        if overrides:
            config.update(overrides)
        return config

    def start_wake_thread(config=None):
        with wake_lock:
            wake_state["enabled"] = True
            wake_state["status"] = "starting"
            wake_state["config"] = default_wake_config(config)
            thread = wake_state.get("thread")
            if thread is None or not thread.is_alive():
                thread = threading.Thread(target=wake_loop, daemon=True)
                wake_state["thread"] = thread
                thread.start()

    def load_history():
        if not HISTORY_FILE.exists():
            return
        try:
            lines = HISTORY_FILE.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            print(f"Historique indisponible: {exc}", flush=True)
            return

        for line in lines[-HISTORY_MAX_MESSAGES:]:
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            role = item.get("role")
            content = item.get("content")
            if role in {"user", "assistant"} and isinstance(content, str) and content.strip():
                conversation_history.append({"role": role, "content": content.strip()})

    def append_history(role, content):
        content = (content or "").strip()
        if role not in {"user", "assistant"} or not content:
            return

        item = {"role": role, "content": content}
        with history_lock:
            conversation_history.append(item)
            try:
                HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
                with HISTORY_FILE.open("a", encoding="utf-8") as file:
                    file.write(json.dumps(item, ensure_ascii=False) + "\n")
            except OSError as exc:
                print(f"Ecriture historique impossible: {exc}", flush=True)

    def clear_history_file():
        with history_lock:
            conversation_history.clear()
            try:
                HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
                HISTORY_FILE.write_text("", encoding="utf-8")
            except OSError as exc:
                print(f"Reset historique impossible: {exc}", flush=True)

    def history_messages():
        with history_lock:
            return list(conversation_history)

    def set_face_expression(expression, force=False):
        if face is None:
            return
        if not force and expression == "sourire" and time.monotonic() < mouth_hold_until["time"]:
            return
        if hasattr(face, "set_expression"):
            face.set_expression(expression)
        else:
            face.show_expression(expression, duration=0)

    def hold_mouth(seconds=4.0):
        seconds = max(0.5, float(seconds))
        mouth_hold_until["time"] = time.monotonic() + seconds
        timer = mouth_hold_until.get("timer")
        if timer:
            timer.cancel()

        def restore_smile():
            if time.monotonic() >= mouth_hold_until["time"]:
                set_face_expression("sourire", force=True)

        timer = threading.Timer(seconds, restore_smile)
        timer.daemon = True
        mouth_hold_until["timer"] = timer
        timer.start()

    def play_face_animation(animation, duration=0.5, speed=0.08):
        if face is None:
            return
        if hasattr(face, "play_animation"):
            face.play_animation(animation, duration=duration, speed=speed)
        elif hasattr(face, "animate_talk") and animation == "parle":
            face.animate_talk(duration=duration, speed=speed)
        else:
            face.show_expression(animation, duration=duration)

    def set_face_bitmap(rows):
        if face is None:
            return
        if hasattr(face, "set_bitmap"):
            face.set_bitmap(rows)
        else:
            print(f"[mouth bitmap] {rows}", flush=True)

    def set_face_icon(name):
        if face is None:
            return
        if hasattr(face, "set_icon"):
            face.set_icon(name)
        else:
            print(f"[mouth icon] {name}", flush=True)

    def show_face_text(text, duration=None, speed=0.12):
        if face is None:
            return
        if hasattr(face, "show_text"):
            face.show_text(text, duration=duration, speed=speed)
        else:
            print(f"[mouth text] {text}", flush=True)

    def normalize_bitmap(rows):
        if isinstance(rows, str):
            rows = [row.strip() for row in rows.splitlines() if row.strip()]
        if not isinstance(rows, list) or len(rows) != 8:
            raise ValueError("Bitmap bouche invalide: 8 lignes attendues")
        normalized = []
        for row in rows:
            if isinstance(row, list):
                row = "".join(str(value) for value in row)
            row = str(row).strip().replace(" ", "")
            if len(row) != 8:
                raise ValueError("Bitmap bouche invalide: chaque ligne doit faire 8 caracteres")
            clean = ""
            for value in row:
                if value in {"#", "1", "X", "x", "*"}:
                    clean += "#"
                elif value in {".", "0", " ", "_"}:
                    clean += "."
                else:
                    raise ValueError("Bitmap bouche invalide: caracteres autorises # . 1 0")
            normalized.append(clean)
        return normalized

    def apply_mouth_output(mouth_output):
        if not isinstance(mouth_output, dict):
            return None
        mode = str(mouth_output.get("mode") or "").strip().lower()
        if mode in {"", "none"}:
            return None
        if mode == "expression":
            expression = str(mouth_output.get("value") or "sourire").strip()
            if expression not in ALLOWED_AI_EXPRESSIONS:
                expression = "sourire"
            set_face_expression(expression)
            return {"mode": "expression", "value": expression}
        if mode == "animation":
            animation = str(mouth_output.get("value") or "charge").strip()
            play_face_animation(animation, duration=float(mouth_output.get("duration", 1.5)))
            return {"mode": "animation", "value": animation}
        if mode in {"icon", "icone", "drawing", "dessin"}:
            value = str(mouth_output.get("value") or "etoile").strip().lower()
            if value not in ALLOWED_MOUTH_ICONS:
                value = "etoile"
            set_face_icon(value)
            hold_mouth(float(mouth_output.get("duration", 4.0)))
            return {"mode": "icon", "value": value}
        if mode == "text":
            value = str(mouth_output.get("value") or "")[:24]
            if value:
                duration = mouth_output.get("duration")
                if len(value) == 1:
                    display_duration = float(duration) if duration is not None else 3.0
                    show_face_text(value)
                    hold_mouth(display_duration)
                else:
                    show_face_text(value, duration=float(duration) if duration is not None else None)
            return {"mode": "text", "value": value}
        if mode == "bitmap":
            pixels = normalize_bitmap(mouth_output.get("pixels") or [])
            set_face_bitmap(pixels)
            hold_mouth(float(mouth_output.get("duration", 4.0)))
            return {"mode": "bitmap", "pixels": pixels}
        return None

    def perform_ai_motion(command):
        command = str(command or "none").strip()
        if command == "none":
            return None

        result = motion.perform(command)
        if command in {"forward", "backward", "left", "right", "stop"}:
            try:
                motion.stop()
            except Exception as exc:
                result = {"ok": False, "message": f"Stop moteur apres geste IA impossible: {exc}", "previous": result}

        if hasattr(motion, "status") and hasattr(motion, "recover_motors"):
            status = motion.status()
            if not result.get("ok", False) or status.get("motor_errors"):
                result = {
                    "ok": result.get("ok", False),
                    "message": result.get("message", ""),
                    "recovery": motion.recover_motors(),
                }
        return result

    def speak_text(text, gain_db=0, voice_model=None):
        with voice_lock:
            set_face_expression("charge")
            if voice_holder["voice"] is None:
                from audio.robot_voice import RobotVoice

                voice_holder["voice"] = RobotVoice()

            stop_animation = threading.Event()
            start_animation = threading.Event()

            def animate_mouth():
                start_animation.wait(timeout=30)
                while start_animation.is_set() and not stop_animation.is_set():
                    play_face_animation("parle", duration=0.5, speed=0.08)

            animation_thread = threading.Thread(target=animate_mouth, daemon=True)
            animation_thread.start()
            try:
                voice_holder["voice"].speak(
                    text,
                    gain_db=gain_db,
                    voice_model=voice_model,
                    on_play_start=start_animation.set,
                    on_play_end=stop_animation.set,
                )
            finally:
                stop_animation.set()
                animation_thread.join(timeout=1)
                set_face_expression("sourire")

    def listen_text(duration=4):
        with stt_lock:
            set_face_expression("charge")
            if stt_holder["stt"] is None:
                from audio.speech_to_text import SpeechToText

                stt_holder["stt"] = SpeechToText()
            try:
                return stt_holder["stt"].transcribe(duration=duration)
            finally:
                set_face_expression("sourire")

    def get_stt():
        if stt_holder["stt"] is None:
            from audio.speech_to_text import SpeechToText

            stt_holder["stt"] = SpeechToText()
        return stt_holder["stt"]

    def answer_prompt(prompt, model, max_tokens=DEFAULT_OLLAMA_MAX_TOKENS, gain_db=0, voice_model=None, should_speak=True, allow_actions=True):
        action = None
        mouth_result = None
        motion_result = None
        if allow_actions:
            action = ask_ollama_action(prompt, model=model, max_tokens=max_tokens)
            answer = action["say"]
            model = action["model"]
            set_face_expression(action["expression"])
            if action["motion"] != "none":
                motion_result = perform_ai_motion(action["motion"])
        else:
            answer, model, _ = ask_ollama(prompt, model, max_tokens=max_tokens)

        if should_speak:
            speak_text(answer, gain_db=gain_db, voice_model=voice_model)

        if action:
            mouth_result = apply_mouth_output(action.get("mouth"))
            if not mouth_result:
                set_face_expression(action["expression"])
        else:
            set_face_expression("sourire")

        append_history("user", prompt)
        append_history("assistant", answer)
        return {
            "response": answer,
            "model": model,
            "action": action,
            "mouth_result": mouth_result,
            "motion_result": motion_result,
        }

    def wake_event(event, value):
        with wake_lock:
            wake_state["status"] = event
            if event == "wake":
                wake_state["last_wake"] = value
        if event == "idle":
            set_face_expression("sourire")
        elif event == "wake":
            set_face_expression("surpris")
        elif event == "speech":
            set_face_expression("vague")

    def wake_loop():
        # Boucle longue vie: elle dort dans arecord/Vosk, puis sort rapidement
        # quand /api/wake/stop bascule wake_state["enabled"].
        while True:
            with wake_lock:
                if not wake_state["enabled"]:
                    wake_state["status"] = "stopped"
                    set_face_expression("sourire")
                    return
                config = dict(wake_state["config"])
                wake_state["status"] = "idle"
                wake_state["last_error"] = ""

            try:
                with stt_lock:
                    text = get_stt().listen_after_wake(
                        wake_words=config.get("wake_words") or ["ok briko", "ok brico", "okay briko", "okay brico"],
                        silence_seconds=float(config.get("silence_seconds", DEFAULT_WAKE_SILENCE_SECONDS)),
                        max_seconds=float(config.get("max_seconds", DEFAULT_WAKE_MAX_SECONDS)),
                        on_event=wake_event,
                        should_stop=lambda: not wake_state["enabled"],
                    )
                text = (text or "").strip()
                with wake_lock:
                    if not wake_state["enabled"]:
                        wake_state["status"] = "stopped"
                        set_face_expression("sourire")
                        return
                with wake_lock:
                    wake_state["last_text"] = text
                    wake_state["status"] = "processing"
                if not text:
                    set_face_expression("triste")
                    time.sleep(0.4)
                    set_face_expression("sourire")
                    continue

                set_face_expression("charge")
                result = answer_prompt(
                    text,
                    model=config.get("model") or DEFAULT_OLLAMA_MODEL,
                    gain_db=config.get("gain_db", 0),
                    voice_model=config.get("voice_model"),
                    should_speak=bool(config.get("speak", True)),
                    allow_actions=bool(config.get("allow_actions", True)),
                )
                with wake_lock:
                    wake_state["last_response"] = result["response"]
            except Exception as exc:
                with wake_lock:
                    wake_state["last_error"] = str(exc)
                    wake_state["status"] = "error"
                set_face_expression("triste")
                time.sleep(1)

    def public_wake_state():
        with wake_lock:
            return {
                "enabled": wake_state["enabled"],
                "status": wake_state["status"],
                "last_wake": wake_state["last_wake"],
                "last_text": wake_state["last_text"],
                "last_response": wake_state["last_response"],
                "last_error": wake_state["last_error"],
                "config": {
                    key: value
                    for key, value in wake_state.get("config", {}).items()
                    if key != "voice_model"
                },
            }

    def ollama_candidates(model=None):
        # On tente d'abord le PC du reseau, puis Ollama local sur la Raspberry
        # pour garder Briqo utilisable si le PC est eteint.
        requested_model = (model or DEFAULT_OLLAMA_MODEL).strip()
        candidates = [(DEFAULT_OLLAMA_URL, requested_model)]
        fallback = (FALLBACK_OLLAMA_URL, FALLBACK_OLLAMA_MODEL)
        if fallback not in candidates:
            candidates.append(fallback)
        return candidates

    def call_ollama(url, model, messages, max_tokens):
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "think": False,
            "options": {
                "temperature": 0.2,
                "top_p": 0.85,
                "num_predict": max_tokens,
            },
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{url}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=90) as res:
            body = json.loads(res.read().decode("utf-8"))

        message = body.get("message") or {}
        answer = (message.get("content") or body.get("response") or "").strip()
        if not answer:
            raise RuntimeError("Ollama a renvoye une reponse vide.")
        return clean_answer(answer)

    def clean_answer(answer):
        answer = (answer or "").strip()
        if not answer.endswith("?"):
            return answer
        sentences = re.split(r"(?<=[.!?])\s+", answer)
        if len(sentences) <= 1:
            return answer
        return " ".join(sentences[:-1]).strip()

    def ask_ollama(prompt, model=None, max_tokens=DEFAULT_OLLAMA_MAX_TOKENS, include_history=True):
        max_tokens = max(40, min(int(max_tokens), 1200))
        user_prompt = f"""
Contexte fixe a respecter:
- Tu t'appelles {DEFAULT_ROBOT_NAME}.
- Tu es le robot compagnon de la famille, pas un enfant.
- Jeremy est le papa.
- Berengere est la maman.
- Juliette a 8 ans et Roxane a 5 ans.
- Juliette et Roxane ne sont pas tes soeurs.
- Ton but est educatif, avec des reponses adaptees a la demande et a l'age des enfants.
- Quand on demande une histoire, une explication ou des informations, donne une
  reponse un peu developpee pour apprendre quelque chose aux enfants.
- Ne finis pas par une question sauf si l'utilisateur te demande de relancer.

Question:
{prompt}

Reponse en francais, claire et educative:
""".strip()
        messages = [
            {"role": "system", "content": ASSISTANT_SYSTEM_PROMPT},
        ]
        if include_history:
            messages.extend(history_messages())
        messages.append({"role": "user", "content": user_prompt})
        last_error = None
        for url, candidate_model in ollama_candidates(model):
            try:
                return call_ollama(url, candidate_model, messages, max_tokens), candidate_model, url
            except (RuntimeError, urllib.error.URLError, TimeoutError) as exc:
                last_error = exc
                print(f"Ollama {url} ({candidate_model}) indisponible: {exc}", flush=True)

        raise RuntimeError(f"Aucun Ollama disponible: {last_error}")

    def ask_ollama_action(prompt, model=None, max_tokens=DEFAULT_OLLAMA_MAX_TOKENS):
        action_prompt = f"""
Tu dois repondre uniquement en JSON valide, sans markdown.
Schema:
{{
  "say": "reponse a dire",
  "expression": "neutre|sourire|grand_sourire|triste|surpris|parle|coeur|colere|vague|baiser",
  "motion": "none|head_left|head_right|head_center|eyes_up|eyes_down|eyes_center|forward|backward|left|right|stop",
  "mouth": {{
    "mode": "none|expression|text|icon|bitmap|animation",
    "value": "A, OK, 42, sourire, charge, etoile...",
    "pixels": ["........","........","........","........","........","........","........","........"]
  }}
}}

Regles:
- Choisis un seul mouvement maximum.
- Utilise forward/backward/left/right seulement si la demande parle clairement de bouger.
- Pour une salutation, prefere sourire et head_center.
- Si on te demande d'afficher une lettre, un chiffre ou un mot court, tu dois utiliser:
  "mouth": {{"mode":"text","value":"A"}}
- Exemple pour afficher OK: "mouth": {{"mode":"text","value":"OK"}}
- Pour afficher un mot, mets tout le mot dans value. Le code le fera defiler.
- Si on te demande un dessin simple, prefere mouth.mode="icon".
- Icones disponibles: coeur, etoile, soleil, lune, maison, eclair, fleur, livre, note, check, croix, ampoule.
- Exemple pour dessiner une etoile: "mouth": {{"mode":"icon","value":"etoile"}}
- Utilise mouth.mode="bitmap" seulement si aucune icone ne correspond.
- Si mouth.mode vaut bitmap, pixels doit contenir exactement 8 chaines de 8 caracteres.
- Dans pixels, utilise uniquement # pour allume et . pour eteint.
- Exemple de bitmap valide: ["........","..####..",".#....#.",".#....#.",".#....#.","..####..","........","........"]
- Ne reponds pas que tu ne peux pas afficher: choisis mouth.mode text ou bitmap.
- Pour les enfants, reste doux et clair.
- Si on demande une histoire ou des informations, say doit contenir plusieurs
  phrases utiles, pas une seule phrase.
- Ne finis pas par une question sauf si l'utilisateur te demande de relancer.

Question utilisateur:
{prompt}
""".strip()
        raw, used_model, used_url = ask_ollama(
            action_prompt,
            model=model,
            max_tokens=max_tokens,
            include_history=True,
        )
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return {
                "say": raw,
                "expression": "sourire",
                "motion": "none",
                "mouth": None,
                "model": used_model,
                "ollama_url": used_url,
            }

        say = clean_answer(str(data.get("say") or "").strip()) or "D'accord."
        expression = str(data.get("expression") or "sourire").strip()
        motion_command = str(data.get("motion") or "none").strip()
        if expression not in ALLOWED_AI_EXPRESSIONS:
            expression = "sourire"
        if motion_command not in ALLOWED_AI_MOTIONS:
            motion_command = "none"
        mouth_output = data.get("mouth")
        if not isinstance(mouth_output, dict):
            mouth_output = None
        return {
            "say": say,
            "expression": expression,
            "motion": motion_command,
            "mouth": mouth_output,
            "model": used_model,
            "ollama_url": used_url,
        }

    def warm_ollama():
        try:
            set_face_expression("charge")
            answer, _, _ = ask_ollama(
                "Reponds uniquement par: pret",
                DEFAULT_OLLAMA_MODEL,
                max_tokens=16,
                include_history=False,
            )
            print(f"Ollama pret avec {DEFAULT_OLLAMA_MODEL}: {answer}", flush=True)
        except Exception as exc:
            print(f"Prechauffage Ollama impossible: {exc}", flush=True)
        finally:
            set_face_expression("sourire")

    @app.get("/")
    def index():
        return render_template_string(HTML)

    @app.post("/api/move")
    def move():
        payload = request.get_json(silent=True) or {}
        result = motion.drive_for(
            payload.get("command", "stop"),
            speed=payload.get("speed"),
            seconds=payload.get("seconds"),
        )
        return jsonify(result)

    @app.post("/api/joystick")
    def joystick():
        payload = request.get_json(silent=True) or {}
        seq = int(payload.get("seq", 0) or 0)
        with joystick_lock:
            if seq and seq < joystick_state["seq"]:
                return jsonify({"ok": True, "message": "Commande joystick ignoree (ancienne)", "seq": seq})
            if seq:
                joystick_state["seq"] = seq
            schedule_joystick_timeout(joystick_state["seq"])
        result = motion.drive_vector(
            payload.get("x", 0),
            payload.get("y", 0),
            speed=payload.get("speed"),
            seconds=payload.get("seconds", 0.15),
            continuous=payload.get("continuous", False),
        )
        result["seq"] = seq
        return jsonify(result)

    @app.post("/api/head")
    def head():
        payload = request.get_json(silent=True) or {}
        result = motion.perform(payload.get("command", "head_center"))
        return jsonify(result)

    @app.post("/api/head-position")
    def head_position():
        payload = request.get_json(silent=True) or {}
        result = motion.set_head_position(
            payload.get("position", 0),
            speed=payload.get("speed"),
        )
        return jsonify(result)

    @app.post("/api/eyes")
    def eyes():
        payload = request.get_json(silent=True) or {}
        result = motion.perform(payload.get("command", "eyes_center"))
        return jsonify(result)

    @app.post("/api/eyes-position")
    def eyes_position():
        payload = request.get_json(silent=True) or {}
        result = motion.set_eyes_position(
            payload.get("position", 0),
            speed=payload.get("speed"),
        )
        return jsonify(result)

    @app.post("/api/stop")
    def stop():
        payload = request.get_json(silent=True) or {}
        seq = int(payload.get("seq", 0) or 0)
        with joystick_lock:
            if seq and seq > joystick_state["seq"]:
                joystick_state["seq"] = seq
            cancel_joystick_timer()
        return jsonify(motion.stop())

    @app.post("/api/motors-reset")
    def motors_reset():
        with joystick_lock:
            joystick_state["seq"] += 1
            cancel_joystick_timer()
        set_face_expression("charge")
        try:
            motion.stop()
        except Exception as exc:
            print(f"Stop avant reset service impossible: {exc}", flush=True)

        def restart_process():
            time.sleep(0.3)
            os._exit(42)

        threading.Thread(target=restart_process, daemon=True).start()
        return jsonify({"ok": True, "message": "Service robot en redemarrage"})

    @app.post("/api/motor-test")
    def motor_test():
        payload = request.get_json(silent=True) or {}
        set_face_expression("charge")
        if not hasattr(motion, "test_port"):
            return jsonify({"ok": False, "message": "Test moteur indisponible"})
        result = motion.test_port(
            payload.get("port", ""),
            speed=payload.get("speed", 45),
            seconds=payload.get("seconds", 0.35),
        )
        set_face_expression("sourire" if result.get("ok") else "triste")
        return jsonify(result)

    @app.post("/api/mouth")
    def mouth():
        payload = request.get_json(silent=True) or {}
        expression = payload.get("expression", "neutre")
        if face is None:
            return jsonify({"ok": False, "message": "Bouche LED indisponible"})
        set_face_expression(expression)
        return jsonify({"ok": True, "message": f"Bouche: {expression}", "expression": expression})

    @app.post("/api/mouth-animation")
    def mouth_animation():
        payload = request.get_json(silent=True) or {}
        animation = payload.get("animation", "parle")
        duration = float(payload.get("duration", 2))
        if face is None:
            return jsonify({"ok": False, "message": "Bouche LED indisponible"})
        play_face_animation(animation, duration=duration)
        return jsonify({"ok": True, "message": f"Animation bouche: {animation}", "animation": animation})

    @app.post("/api/mouth-text")
    def mouth_text():
        payload = request.get_json(silent=True) or {}
        text = str(payload.get("text") or "")[:24]
        duration = payload.get("duration")
        if face is None:
            return jsonify({"ok": False, "message": "Bouche LED indisponible"})
        if len(text) == 1:
            show_face_text(text)
            hold_mouth(float(duration) if duration is not None else 3.0)
        else:
            show_face_text(text, duration=float(duration) if duration is not None else None)
        return jsonify({"ok": True, "message": f"Texte bouche: {text}", "text": text})

    @app.post("/api/mouth-bitmap")
    def mouth_bitmap():
        payload = request.get_json(silent=True) or {}
        if face is None:
            return jsonify({"ok": False, "message": "Bouche LED indisponible"})
        try:
            pixels = normalize_bitmap(payload.get("pixels") or [])
            set_face_bitmap(pixels)
            hold_mouth(float(payload.get("duration", 4.0)))
        except ValueError as exc:
            set_face_expression("triste")
            return jsonify({"ok": False, "message": str(exc)})
        return jsonify({"ok": True, "message": "Bitmap bouche affiche", "pixels": pixels})

    @app.post("/api/mouth-icon")
    def mouth_icon():
        payload = request.get_json(silent=True) or {}
        icon = str(payload.get("icon") or payload.get("value") or "etoile").strip().lower()
        if icon not in ALLOWED_MOUTH_ICONS:
            icon = "etoile"
        if face is None:
            return jsonify({"ok": False, "message": "Bouche LED indisponible"})
        set_face_icon(icon)
        hold_mouth(float(payload.get("duration", 4.0)))
        return jsonify({"ok": True, "message": f"Dessin bouche: {icon}", "icon": icon})

    @app.post("/api/mouth-reset")
    def mouth_reset():
        if face is None:
            return jsonify({"ok": False, "message": "Bouche LED indisponible"})
        set_face_expression("charge")
        if hasattr(face, "reset"):
            face.reset()
        else:
            set_face_expression("sourire")
        return jsonify({"ok": True, "message": "Bouche LED reinitialisee", "expression": "sourire"})

    @app.get("/api/voices")
    def voices():
        from audio.robot_voice import RobotVoice

        return jsonify({
            "ok": True,
            "voices": RobotVoice.available_voices(),
            "default_voice": DEFAULT_VOICE_MODEL,
        })

    @app.post("/api/say")
    def say():
        payload = request.get_json(silent=True) or {}
        text = (payload.get("text") or "").strip()
        gain_db = payload.get("gain_db", 0)
        voice_model = (payload.get("voice_model") or "").strip() or None
        if not text:
            return jsonify({"ok": False, "message": "Texte vide"})

        speak_text(text, gain_db=gain_db, voice_model=voice_model)
        return jsonify({
            "ok": True,
            "message": "Parole terminee",
            "text": text,
            "gain_db": gain_db,
            "voice_model": voice_model,
        })

    @app.post("/api/listen")
    def listen():
        payload = request.get_json(silent=True) or {}
        duration = payload.get("duration", 4)
        ask_robot = bool(payload.get("ask", False))
        speak = bool(payload.get("speak", True))
        allow_actions = bool(payload.get("allow_actions", False))
        model = (payload.get("model") or DEFAULT_OLLAMA_MODEL).strip()
        gain_db = payload.get("gain_db", 0)
        voice_model = (payload.get("voice_model") or "").strip() or None

        try:
            text = listen_text(duration=duration)
            if not text:
                set_face_expression("triste")
                return jsonify({"ok": False, "message": "Aucune parole detectee", "text": ""})

            answer = None
            action = None
            mouth_result = None
            motion_result = None
            if ask_robot:
                set_face_expression("charge")
                if allow_actions:
                    action = ask_ollama_action(text, model=model)
                    answer = action["say"]
                    model = action["model"]
                    if action["motion"] != "none":
                        motion_result = perform_ai_motion(action["motion"])
                else:
                    answer, model, _ = ask_ollama(text, model)

                if speak:
                    speak_text(answer, gain_db=gain_db, voice_model=voice_model)
                if action:
                    mouth_result = apply_mouth_output(action.get("mouth"))
                    if not mouth_result:
                        set_face_expression(action["expression"])
                else:
                    set_face_expression("sourire")
                append_history("user", text)
                append_history("assistant", answer)
            else:
                set_face_expression("sourire")

        except Exception as exc:
            set_face_expression("triste")
            return jsonify({"ok": False, "message": str(exc)})

        return jsonify({
            "ok": True,
            "message": "Ecoute terminee",
            "text": text,
            "asked": ask_robot,
            "response": answer,
            "model": model,
            "spoken": speak if ask_robot else False,
            "action": action,
            "mouth_result": mouth_result,
            "motion_result": motion_result,
        })

    @app.post("/api/wake/start")
    def wake_start():
        payload = request.get_json(silent=True) or {}
        start_wake_thread({
            "model": (payload.get("model") or DEFAULT_OLLAMA_MODEL).strip(),
            "gain_db": payload.get("gain_db", 0),
            "voice_model": (payload.get("voice_model") or "").strip() or DEFAULT_VOICE_MODEL,
            "speak": bool(payload.get("speak", True)),
            "allow_actions": bool(payload.get("allow_actions", True)),
            "silence_seconds": float(payload.get("silence_seconds", DEFAULT_WAKE_SILENCE_SECONDS)),
            "max_seconds": float(payload.get("max_seconds", DEFAULT_WAKE_MAX_SECONDS)),
            "wake_words": payload.get("wake_words") or ["ok briko", "ok brico", "okay briko", "okay brico"],
        })
        set_face_expression("sourire")
        return jsonify({"ok": True, "message": "Veille ok briko activee", "wake": public_wake_state()})

    @app.post("/api/wake/stop")
    def wake_stop():
        with wake_lock:
            wake_state["enabled"] = False
            wake_state["status"] = "stopping"
        set_face_expression("sourire")
        return jsonify({"ok": True, "message": "Veille ok briko arretee", "wake": public_wake_state()})

    @app.get("/api/wake/status")
    def wake_status():
        return jsonify({"ok": True, "wake": public_wake_state()})

    @app.post("/api/ask")
    def ask():
        payload = request.get_json(silent=True) or {}
        prompt = (payload.get("prompt") or "").strip()
        model = (payload.get("model") or DEFAULT_OLLAMA_MODEL).strip()
        max_tokens = payload.get("max_tokens", DEFAULT_OLLAMA_MAX_TOKENS)
        gain_db = payload.get("gain_db", 0)
        voice_model = (payload.get("voice_model") or "").strip() or None
        should_speak = bool(payload.get("speak", True))
        allow_actions = bool(payload.get("allow_actions", False))
        if not prompt:
            return jsonify({"ok": False, "message": "Message vide"})

        try:
            set_face_expression("charge")
            action = None
            motion_result = None
            mouth_result = None
            if allow_actions:
                action = ask_ollama_action(prompt, model=model, max_tokens=max_tokens)
                answer = action["say"]
                model = action["model"]
                set_face_expression(action["expression"])
                if action["motion"] != "none":
                    motion_result = perform_ai_motion(action["motion"])
            else:
                answer, model, ollama_url = ask_ollama(prompt, model, max_tokens=max_tokens)
            if should_speak:
                speak_text(answer, gain_db=gain_db, voice_model=voice_model)
                if action:
                    mouth_result = apply_mouth_output(action.get("mouth"))
                    if not mouth_result:
                        set_face_expression(action["expression"])
            else:
                if action:
                    mouth_result = apply_mouth_output(action.get("mouth"))
                    if not mouth_result:
                        set_face_expression(action["expression"])
                else:
                    set_face_expression("sourire")
            append_history("user", prompt)
            append_history("assistant", answer)
        except Exception as exc:
            set_face_expression("triste")
            return jsonify({"ok": False, "message": str(exc), "model": model})

        return jsonify({
            "ok": True,
            "message": "Reponse Ollama terminee",
            "prompt": prompt,
            "response": answer,
            "model": model,
            "max_tokens": max_tokens,
            "spoken": should_speak,
            "voice_model": voice_model,
            "actions_enabled": allow_actions,
            "action": action,
            "mouth_result": mouth_result,
            "motion_result": motion_result,
        })

    @app.get("/api/history")
    def history():
        return jsonify({
            "ok": True,
            "history": history_messages(),
            "max_messages": HISTORY_MAX_MESSAGES,
            "file": str(HISTORY_FILE),
        })

    @app.post("/api/history/clear")
    def history_clear():
        clear_history_file()
        return jsonify({"ok": True, "message": "Historique efface"})

    @app.get("/api/status")
    def status():
        if hasattr(motion, "status"):
            state = motion.status()
            state["robot_name"] = DEFAULT_ROBOT_NAME
            state["ollama_model"] = DEFAULT_OLLAMA_MODEL
            state["ollama_url"] = DEFAULT_OLLAMA_URL
            state["fallback_ollama_model"] = FALLBACK_OLLAMA_MODEL
            state["fallback_ollama_url"] = FALLBACK_OLLAMA_URL
            state["wake"] = public_wake_state()
            return jsonify(state)
        return jsonify({
            "ok": True,
            "mock": True,
            "robot_name": DEFAULT_ROBOT_NAME,
            "ollama_model": DEFAULT_OLLAMA_MODEL,
            "ollama_url": DEFAULT_OLLAMA_URL,
            "fallback_ollama_model": FALLBACK_OLLAMA_MODEL,
            "fallback_ollama_url": FALLBACK_OLLAMA_URL,
            "wake": public_wake_state(),
        })

    load_history()
    threading.Thread(target=warm_ollama, daemon=True).start()
    if DEFAULT_WAKE_ON_START:
        start_wake_thread()
    return app


def main():
    parser = argparse.ArgumentParser(description="Interface web de pilotage LegoBot.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()

    if args.mock:
        motion = MockMotion()
        face = MockFace()
    else:
        from motion.buildhat_motion import BuildHatMotion
        from display.mouth_display import MatrixFace

        motion = BuildHatMotion()
        face = MatrixFace()

    app = create_app(motion, face=face)
    app.run(host=args.host, port=args.port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
