#!/usr/bin/env python3
from dataclasses import dataclass
import unicodedata


@dataclass(frozen=True)
class AgentAction:
    say: str
    expression: str = "neutre"
    motion: str | None = None


class LegoBotAgent:
    """Petit cerveau local du robot, facile a remplacer par un LLM plus tard."""

    def __init__(self, name="Moumoute"):
        self.name = name

    def handle_text(self, text):
        text = text.strip()
        normalized = self._normalize(text)

        if not normalized:
            return AgentAction("Je n'ai rien entendu.", expression="triste")

        if any(word in normalized for word in ("bonjour", "salut", "hello")):
            return AgentAction(
                f"Bonjour, je suis {self.name}. Je suis de retour.",
                expression="sourire",
            )

        if "coeur" in normalized or "amour" in normalized:
            return AgentAction("Avec plaisir.", expression="coeur")

        if "avance" in normalized or "avancer" in normalized:
            return AgentAction("J'avance doucement.", expression="sourire", motion="forward")

        if "recule" in normalized or "reculer" in normalized:
            return AgentAction("Je recule.", expression="neutre", motion="backward")

        if "gauche" in normalized:
            return AgentAction("Je tourne a gauche.", expression="vague", motion="left")

        if "droite" in normalized:
            return AgentAction("Je tourne a droite.", expression="vague", motion="right")

        if "stop" in normalized or "arrete" in normalized:
            return AgentAction("Je m'arrete.", expression="neutre", motion="stop")

        if "triste" in normalized:
            return AgentAction("Je peux faire une tete triste.", expression="triste")

        if "colere" in normalized:
            return AgentAction("Attention, mode sourcils fronces.", expression="colere")

        return AgentAction(
            "J'ai compris. Pour l'instant je sais surtout parler, afficher ma bouche et bouger sur des commandes simples.",
            expression="neutre",
        )

    def _normalize(self, text):
        normalized = unicodedata.normalize("NFKD", text.lower())
        return "".join(char for char in normalized if not unicodedata.combining(char))
