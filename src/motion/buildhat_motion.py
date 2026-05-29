#!/usr/bin/env python3
import os
import subprocess
import threading
import time


class BuildHatMotion:
    """Controle simple des moteurs LEGO via Build HAT.

    Les ports peuvent etre ajustes sans modifier le code:
    LEGOBOT_EYES_PORT=A LEGOBOT_HEAD_PORT=B LEGOBOT_RIGHT_PORT=C LEGOBOT_LEFT_PORT=D
    """

    def __init__(
        self,
        left_port=None,
        right_port=None,
        head_port=None,
        eyes_port=None,
        speed=35,
        move_seconds=0.5,
        head_degrees=35,
        eyes_degrees=25,
        left_inverted=False,
        right_inverted=True,
    ):
        try:
            from buildhat import Motor
            from buildhat.devices import Device
        except ImportError as exc:
            raise RuntimeError("Installez python3-build-hat sur la Raspberry Pi.") from exc

        self.setup_error = None
        self._release_reset_pin()
        device = os.getenv("LEGOBOT_BUILDHAT_DEVICE")
        try:
            if device:
                Device._setup(device=device)
            elif not os.path.exists("/dev/serial0") and os.path.exists("/dev/ttyAMA0"):
                Device._setup(device="/dev/ttyAMA0")
        except Exception as exc:
            self.setup_error = str(exc)

        self.Motor = Motor
        self.left_port = left_port if left_port is not None else os.getenv("LEGOBOT_LEFT_PORT", "D")
        self.right_port = right_port if right_port is not None else os.getenv("LEGOBOT_RIGHT_PORT", "C")
        self.head_port = head_port if head_port is not None else os.getenv("LEGOBOT_HEAD_PORT", "B")
        self.eyes_port = eyes_port if eyes_port is not None else os.getenv("LEGOBOT_EYES_PORT", "A")
        self.speed = speed
        self.move_seconds = move_seconds
        self.head_degrees = head_degrees
        self.eyes_degrees = eyes_degrees
        self.left_sign = -1 if self._env_bool("LEGOBOT_LEFT_INVERTED", left_inverted) else 1
        self.right_sign = -1 if self._env_bool("LEGOBOT_RIGHT_INVERTED", right_inverted) else 1
        self._lock = threading.Lock()

        self.left = self._motor(self.left_port, "left")
        self.right = self._motor(self.right_port, "right")
        self.head = self._motor(self.head_port, "head")
        self.eyes = self._motor(self.eyes_port, "eyes")

    def perform(self, command):
        if command == "forward":
            return self.drive(self.speed, self.speed)
        elif command == "backward":
            return self.drive(-self.speed, -self.speed)
        elif command == "left":
            return self.drive(-self.speed, self.speed)
        elif command == "right":
            return self.drive(self.speed, -self.speed)
        elif command == "head_left":
            return self.turn_head(-self.head_degrees)
        elif command == "head_right":
            return self.turn_head(self.head_degrees)
        elif command == "head_center":
            return self.center_head()
        elif command == "eyes_up":
            return self.move_eyes(self.eyes_degrees)
        elif command == "eyes_down":
            return self.move_eyes(-self.eyes_degrees)
        elif command == "eyes_center":
            return self.center_eyes()
        elif command == "stop":
            return self.stop()
        return {"ok": False, "message": f"Commande inconnue: {command}"}

    def drive_for(self, command, speed=None, seconds=None):
        original_speed = self.speed
        original_seconds = self.move_seconds
        if speed is not None:
            self.speed = abs(int(speed))
        if seconds is not None:
            self.move_seconds = max(0.05, float(seconds))
        try:
            return self.perform(command)
        finally:
            self.speed = original_speed
            self.move_seconds = original_seconds

    def drive_vector(self, x, y, speed=None, seconds=0.15, continuous=False):
        base_speed = self.speed if speed is None else abs(int(speed))
        x = max(-1.0, min(1.0, float(x)))
        y = max(-1.0, min(1.0, float(y)))

        left = y + x
        right = y - x
        max_value = max(1.0, abs(left), abs(right))
        left_speed = int((left / max_value) * base_speed)
        right_speed = int((right / max_value) * base_speed)

        if continuous:
            return self.drive_continuous(left_speed, right_speed)

        original_seconds = self.move_seconds
        self.move_seconds = max(0.05, float(seconds))
        try:
            return self.drive(left_speed, right_speed)
        finally:
            self.move_seconds = original_seconds

    def turn_head(self, degrees=None):
        if self.head is None:
            return {"ok": False, "message": "Moteur de tete indisponible"}

        degrees = self.head_degrees if degrees is None else int(degrees)
        self._pulse_motor(self.head, degrees, self.speed, max_seconds=0.45)
        return {"ok": True, "message": f"Tete impulsion {degrees}"}

    def center_head(self):
        if self.head is None:
            return {"ok": False, "message": "Moteur de tete indisponible"}

        self.head.stop()
        return {"ok": True, "message": "Tete stop/centre"}

    def set_head_position(self, position, speed=None):
        if self.head is None:
            return {"ok": False, "message": "Moteur de tete indisponible"}

        run_speed = self.speed if speed is None else abs(int(speed))
        position = max(-90, min(90, int(position)))
        self._pulse_motor(self.head, position, run_speed, max_seconds=0.7)
        return {"ok": True, "message": f"Tete position {position}", "position": position}

    def move_eyes(self, degrees=None):
        if self.eyes is None:
            return {"ok": False, "message": "Moteur des yeux indisponible"}

        degrees = self.eyes_degrees if degrees is None else int(degrees)
        self._pulse_motor(self.eyes, degrees, self.speed, max_seconds=0.35)
        return {"ok": True, "message": f"Yeux impulsion {degrees}"}

    def center_eyes(self):
        if self.eyes is None:
            return {"ok": False, "message": "Moteur des yeux indisponible"}

        self.eyes.stop()
        return {"ok": True, "message": "Yeux stop/centre"}

    def set_eyes_position(self, position, speed=None):
        if self.eyes is None:
            return {"ok": False, "message": "Moteur des yeux indisponible"}

        run_speed = self.speed if speed is None else abs(int(speed))
        position = max(-45, min(45, int(position)))
        self._pulse_motor(self.eyes, position, run_speed, max_seconds=0.45)
        return {"ok": True, "message": f"Yeux position {position}", "position": position}

    def stop(self):
        with self._lock:
            for motor in (self.left, self.right, self.head, self.eyes):
                if motor is not None:
                    motor.stop()
        return {"ok": True, "message": "Stop"}

    def drive(self, left_speed, right_speed):
        if self.setup_error:
            return {"ok": False, "message": f"Build HAT indisponible: {self.setup_error}"}
        if self.left is None or self.right is None:
            return {"ok": False, "message": "Moteurs gauche/droite indisponibles"}
        hardware_left_speed = left_speed * self.left_sign
        hardware_right_speed = right_speed * self.right_sign
        with self._lock:
            self.left.start(hardware_left_speed)
            self.right.start(hardware_right_speed)
        time.sleep(self.move_seconds)
        self.stop()
        return {
            "ok": True,
            "message": f"Drive L={left_speed} R={right_speed}",
            "hardware": {
                "left": hardware_left_speed,
                "right": hardware_right_speed,
            },
        }

    def drive_continuous(self, left_speed, right_speed):
        if self.setup_error:
            return {"ok": False, "message": f"Build HAT indisponible: {self.setup_error}"}
        if self.left is None or self.right is None:
            return {"ok": False, "message": "Moteurs gauche/droite indisponibles"}

        hardware_left_speed = left_speed * self.left_sign
        hardware_right_speed = right_speed * self.right_sign
        with self._lock:
            self.left.start(hardware_left_speed)
            self.right.start(hardware_right_speed)
        return {
            "ok": True,
            "message": f"Continuous L={left_speed} R={right_speed}",
            "hardware": {
                "left": hardware_left_speed,
                "right": hardware_right_speed,
            },
        }

    def _motor(self, port, label):
        if self.setup_error:
            return None
        if not port:
            return None
        try:
            return self.Motor(port)
        except Exception as exc:
            print(f"Moteur {label} sur port {port} indisponible: {exc}")
            return None

    def _run_motor(self, motor, method_name, *args, **kwargs):
        with self._lock:
            method = getattr(motor, method_name)
            try:
                return method(*args, **kwargs)
            except TypeError:
                kwargs.pop("blocking", None)
                return method(*args, **kwargs)

    def _pulse_motor(self, motor, direction_value, speed, max_seconds=0.4):
        direction_value = int(direction_value)
        if direction_value == 0:
            with self._lock:
                motor.stop()
            return

        signed_speed = abs(int(speed)) if direction_value > 0 else -abs(int(speed))
        seconds = min(max_seconds, max(0.08, abs(direction_value) / 120.0))

        def run_pulse():
            with self._lock:
                motor.start(signed_speed)
            time.sleep(seconds)
            with self._lock:
                motor.stop()

        threading.Thread(target=run_pulse, daemon=True).start()

    def status(self):
        return {
            "ok": self.setup_error is None,
            "setup_error": self.setup_error,
            "ports": {
                "left": self.left_port,
                "right": self.right_port,
                "head": self.head_port,
                "eyes": self.eyes_port,
            },
            "motors": {
                "left": self.left is not None,
                "right": self.right is not None,
                "head": self.head is not None,
                "eyes": self.eyes is not None,
            },
            "inverted": {
                "left": self.left_sign == -1,
                "right": self.right_sign == -1,
            },
        }

    def _release_reset_pin(self):
        commands = [
            ["pinctrl", "set", "22", "op", "dl"],
            ["pinctrl", "set", "4", "op", "dl"],
            ["pinctrl", "set", "4", "op", "dh"],
        ]
        try:
            subprocess.run(commands[0], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(commands[1], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.2)
            subprocess.run(commands[2], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1)
        except FileNotFoundError:
            pass

    def _env_bool(self, name, default):
        value = os.getenv(name)
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "on"}
