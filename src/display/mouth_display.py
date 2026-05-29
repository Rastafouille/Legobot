#!/usr/bin/env python3
import os
import threading
import time

from luma.core.interface.serial import noop, spi
from luma.core.render import canvas
from luma.led_matrix.device import max7219


class MatrixFace:
    def __init__(self, rotate=None, block_orientation=90):
        if rotate is None:
            rotate = int(os.getenv("LEGOBOT_MOUTH_ROTATE", "1"))
        self.rotate = rotate
        self.block_orientation = block_orientation
        self._lock = threading.RLock()
        self._init_device()
        self.reset(show_ready=False)

    def _init_device(self):
        serial = spi(port=0, device=0, gpio=noop())
        self.device = max7219(
            serial,
            cascaded=1,
            block_orientation=self.block_orientation,
            rotate=self.rotate,
        )

    def reset(self, show_ready=True):
        with self._lock:
            self._init_device()
            try:
                self.device.contrast(8)
            except AttributeError:
                pass
            self.clear()
            if show_ready:
                self._draw_pixels(self._expressions()["neutre"])

    def show_expression(self, name, duration=1):
        self.set_expression(name)
        time.sleep(duration)
        self.clear()

    def set_expression(self, name):
        expressions = self._expressions()
        pattern = expressions.get(name, expressions["neutre"])
        self._draw_pixels(pattern)

    def play_animation(self, name, duration=2, speed=0.12):
        animations = self._animations()
        frames = animations.get(name)
        if not frames:
            self.set_expression(name)
            return

        end_time = time.time() + duration
        while time.time() < end_time:
            for frame in frames:
                self._draw_pixels(frame)
                time.sleep(speed)
                if time.time() >= end_time:
                    break

    def animate_talk(self, duration=1, speed=0.1):
        self.play_animation("parle", duration=duration, speed=speed)

    def clear(self):
        with self._lock:
            with canvas(self.device):
                pass

    def _draw_pixels(self, pixels):
        with self._lock:
            with canvas(self.device) as draw:
                for x, y in pixels:
                    draw.point((x, y), fill="white")

    def _pattern(self, rows):
        pixels = []
        for y, row in enumerate(rows):
            for x, value in enumerate(row[:8]):
                if value != ".":
                    pixels.append((x, y))
        return pixels

    def _expressions(self):
        return {
            "neutre": self._pattern([
                "........",
                "........",
                "........",
                "........",
                ".######.",
                "........",
                "........",
                "........",
            ]),
            "sourire": self._pattern([
                "........",
                "........",
                "........",
                "#......#",
                ".#....#.",
                "..####..",
                "........",
                "........",
            ]),
            "grand_sourire": self._pattern([
                "........",
                "........",
                "#......#",
                "#.####.#",
                ".#....#.",
                "..####..",
                "........",
                "........",
            ]),
            "triste": self._pattern([
                "........",
                "........",
                "........",
                "..####..",
                ".#....#.",
                "#......#",
                "........",
                "........",
            ]),
            "surpris": self._pattern([
                "........",
                "..####..",
                ".#....#.",
                ".#....#.",
                ".#....#.",
                "..####..",
                "........",
                "........",
            ]),
            "parle": self._pattern([
                "........",
                "........",
                "..####..",
                ".######.",
                ".######.",
                "..####..",
                "........",
                "........",
            ]),
            "coeur": self._pattern([
                "........",
                "..#..#..",
                ".######.",
                "########",
                "########",
                "..####..",
                "...##...",
                "........",
            ]),
            "colere": self._pattern([
                "........",
                "........",
                "#......#",
                ".######.",
                "..#..#..",
                ".######.",
                "........",
                "........",
            ]),
            "vague": self._pattern([
                "........",
                "........",
                "........",
                ".##..##.",
                "#..##..#",
                "........",
                "........",
                "........",
            ]),
            "baiser": self._pattern([
                "........",
                "........",
                "...##...",
                "..####..",
                "...##...",
                "........",
                "........",
                "........",
            ]),
        }

    def _animations(self):
        return {
            "parle": [
                self._pattern([
                    "........",
                    "........",
                    "........",
                    ".######.",
                    "........",
                    "........",
                    "........",
                    "........",
                ]),
                self._pattern([
                    "........",
                    "........",
                    "..####..",
                    ".#....#.",
                    ".#....#.",
                    "..####..",
                    "........",
                    "........",
                ]),
                self._pattern([
                    "........",
                    "..####..",
                    ".######.",
                    ".######.",
                    ".######.",
                    "..####..",
                    "........",
                    "........",
                ]),
            ],
            "respire": [
                self._pattern([
                    "........",
                    "........",
                    "........",
                    "..####..",
                    "........",
                    "........",
                    "........",
                    "........",
                ]),
                self._pattern([
                    "........",
                    "........",
                    "........",
                    ".######.",
                    "........",
                    "........",
                    "........",
                    "........",
                ]),
                self._pattern([
                    "........",
                    "........",
                    "..####..",
                    ".#....#.",
                    "..####..",
                    "........",
                    "........",
                    "........",
                ]),
            ],
            "charge": [
                self._pattern([
                    "........",
                    "........",
                    "........",
                    "#.......",
                    "........",
                    "........",
                    "........",
                    "........",
                ]),
                self._pattern([
                    "........",
                    "........",
                    "........",
                    "###.....",
                    "........",
                    "........",
                    "........",
                    "........",
                ]),
                self._pattern([
                    "........",
                    "........",
                    "........",
                    "#####...",
                    "........",
                    "........",
                    "........",
                    "........",
                ]),
                self._pattern([
                    "........",
                    "........",
                    "........",
                    "########",
                    "........",
                    "........",
                    "........",
                    "........",
                ]),
            ],
            "rire": [
                self._pattern([
                    "........",
                    "........",
                    "#......#",
                    ".######.",
                    ".#....#.",
                    "..####..",
                    "........",
                    "........",
                ]),
                self._pattern([
                    "........",
                    "........",
                    ".#....#.",
                    "..####..",
                    ".######.",
                    "#......#",
                    "........",
                    "........",
                ]),
            ],
            "coeur_pulse": [
                self._expressions()["coeur"],
                self._pattern([
                    ".##..##.",
                    "########",
                    "########",
                    "########",
                    ".######.",
                    "..####..",
                    "...##...",
                    "........",
                ]),
            ],
        }


if __name__ == "__main__":
    mouth = MatrixFace()
    try:
        print("Demarrage du test des expressions...")
        for expression in mouth._expressions():
            print(expression)
            mouth.show_expression(expression)
        mouth.animate_talk()
    except KeyboardInterrupt:
        mouth.clear()
        print("\nProgramme termine")
