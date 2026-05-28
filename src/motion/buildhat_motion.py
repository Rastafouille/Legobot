#!/usr/bin/env python3
import time


class BuildHatMotion:
    """Controle simple de deux moteurs LEGO via Build HAT.

    Par defaut, les moteurs gauche/droite sont attendus sur les ports A/B.
    """

    def __init__(self, left_port="A", right_port="B", speed=35, move_seconds=0.8):
        try:
            from buildhat import Motor
        except ImportError as exc:
            raise RuntimeError("Installez python3-build-hat sur la Raspberry Pi.") from exc

        self.left = Motor(left_port)
        self.right = Motor(right_port)
        self.speed = speed
        self.move_seconds = move_seconds

    def perform(self, command):
        if command == "forward":
            self._drive(self.speed, self.speed)
        elif command == "backward":
            self._drive(-self.speed, -self.speed)
        elif command == "left":
            self._drive(-self.speed, self.speed)
        elif command == "right":
            self._drive(self.speed, -self.speed)
        elif command == "stop":
            self.stop()

    def stop(self):
        self.left.stop()
        self.right.stop()

    def _drive(self, left_speed, right_speed):
        self.left.start(left_speed)
        self.right.start(right_speed)
        time.sleep(self.move_seconds)
        self.stop()
