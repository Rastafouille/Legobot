#!/usr/bin/env python3
import argparse

from agent import LegoBotAgent
from robot import LegoBotRobot


def main():
    parser = argparse.ArgumentParser(description="Lance LegoBot en mode agent.")
    parser.add_argument("--mock", action="store_true", help="Utilise des adaptateurs console sans materiel.")
    args = parser.parse_args()

    robot = None
    try:
        agent = LegoBotAgent()
        robot = LegoBotRobot(mock=args.mock)

        print("LegoBot agent pret. Tape une phrase, ou 'quit' pour sortir.")
        while True:
            text = input("> ")
            if text.strip().lower() in {"quit", "exit"}:
                break
            action = agent.handle_text(text)
            robot.perform(action)

    except KeyboardInterrupt:
        print("\nArret du programme...")
    except Exception as e:
        print(f"Erreur : {e}")
    finally:
        if robot is not None:
            robot.shutdown()


if __name__ == "__main__":
    main()
