#!/usr/bin/env python3
import threading
import time

from agent import AgentAction


class MockFace:
    def set_expression(self, name):
        print(f"[mouth] {name}")

    def show_expression(self, name, duration=0):
        print(f"[mouth] {name}")

    def animate_talk(self, duration=1, speed=0.12):
        print("[mouth] talk")
        time.sleep(duration)

    def clear(self):
        print("[mouth] clear")


class MockVoice:
    def speak(self, text):
        print(f"[voice] {text}")


class MockMotion:
    def perform(self, command):
        print(f"[motion] {command}")

    def stop(self):
        print("[motion] stop")


class LegoBotRobot:
    def __init__(self, mock=False):
        self.face = self._load_face(mock)
        self.voice = self._load_voice(mock)
        self.motion = self._load_motion(mock)

    def perform(self, action: AgentAction):
        if action.motion:
            self.motion.perform(action.motion)

        self.set_expression(action.expression)
        self.say(action.say)
        self.set_expression("neutre")

    def set_expression(self, name):
        if hasattr(self.face, "set_expression"):
            self.face.set_expression(name)
        else:
            self.face.show_expression(name, duration=0)

    def say(self, text):
        stop_animation = threading.Event()

        def animate_mouth():
            while not stop_animation.is_set():
                self.face.animate_talk(duration=0.35, speed=0.12)

        animation_thread = threading.Thread(target=animate_mouth, daemon=True)
        animation_thread.start()
        try:
            self.voice.speak(text)
        finally:
            stop_animation.set()
            animation_thread.join(timeout=1)

    def shutdown(self):
        self.motion.stop()
        self.face.clear()

    def _load_face(self, mock):
        if mock:
            return MockFace()
        from display.mouth_display import MatrixFace

        return MatrixFace()

    def _load_voice(self, mock):
        if mock:
            return MockVoice()
        from audio.robot_voice import RobotVoice

        return RobotVoice()

    def _load_motion(self, mock):
        if mock:
            return MockMotion()
        from motion.buildhat_motion import BuildHatMotion

        return BuildHatMotion()
