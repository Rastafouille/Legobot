#!/usr/bin/env python3
import os
import threading
import time

from luma.core.interface.serial import noop, spi
from luma.core.render import canvas
from luma.led_matrix.device import max7219


FONT_5X7 = {
    " ": [".....", ".....", ".....", ".....", ".....", ".....", "....."],
    "!": ["..#..", "..#..", "..#..", "..#..", ".....", "..#..", "....."],
    "?": [".###.", "#...#", "...#.", "..#..", "..#..", ".....", "..#.."],
    ".": [".....", ".....", ".....", ".....", ".....", "..#..", "..#.."],
    ":": [".....", "..#..", "..#..", ".....", "..#..", "..#..", "....."],
    "-": [".....", ".....", ".....", ".###.", ".....", ".....", "....."],
    "+": [".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."],
    "<": ["...#.", "..#..", ".#...", "#....", ".#...", "..#..", "...#."],
    ">": [".#...", "..#..", "...#.", "....#", "...#.", "..#..", ".#..."],
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["####.", "....#", "...#.", "..##.", "....#", "#...#", ".###."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": [".###.", "#...#", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "#...#", ".###."],
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": [".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "J": ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
}


ICON_8X8 = {
    "coeur": [
        "........",
        ".##..##.",
        "########",
        "########",
        ".######.",
        "..####..",
        "...##...",
        "........",
    ],
    "etoile": [
        "...##...",
        "...##...",
        ".######.",
        "..####..",
        ".######.",
        ".##..##.",
        "........",
        "........",
    ],
    "soleil": [
        "#..##..#",
        ".#....#.",
        "..####..",
        ".#....#.",
        ".#....#.",
        "..####..",
        ".#....#.",
        "#..##..#",
    ],
    "lune": [
        "...###..",
        "..##....",
        ".##.....",
        ".##.....",
        ".##.....",
        "..##....",
        "...###..",
        "........",
    ],
    "maison": [
        "...##...",
        "..####..",
        ".######.",
        "##.##.##",
        "...##...",
        "...##...",
        ".######.",
        "........",
    ],
    "eclair": [
        "....##..",
        "...##...",
        "..##....",
        ".######.",
        "...##...",
        "..##....",
        ".##.....",
        "........",
    ],
    "fleur": [
        "...##...",
        ".#.##.#.",
        "..####..",
        "...##...",
        "...##...",
        "..####..",
        ".#....#.",
        "........",
    ],
    "livre": [
        "........",
        ".###.###",
        ".#.#.#.#",
        ".#.#.#.#",
        ".###.###",
        ".#.....#",
        ".#######",
        "........",
    ],
    "note": [
        "....###.",
        "....#.#.",
        "....#...",
        "....#...",
        ".##.#...",
        "####....",
        ".##.....",
        "........",
    ],
    "check": [
        "........",
        "......#.",
        ".....##.",
        "#...##..",
        "##.##...",
        ".###....",
        "..#.....",
        "........",
    ],
    "croix": [
        "........",
        ".##..##.",
        "..####..",
        "...##...",
        "..####..",
        ".##..##.",
        "........",
        "........",
    ],
    "ampoule": [
        "..####..",
        ".#....#.",
        ".#....#.",
        "..####..",
        "...##...",
        "..####..",
        "...##...",
        "........",
    ],
}


class MatrixFace:
    def __init__(self, rotate=None, block_orientation=90):
        if rotate is None:
            rotate = int(os.getenv("LEGOBOT_MOUTH_ROTATE", "1"))
        self.rotate = rotate
        self.block_orientation = block_orientation
        self._lock = threading.RLock()
        self._init_device()
        self.reset(show_ready=True)

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
                self._draw_pixels(self._expressions()["sourire"])

    def show_expression(self, name, duration=1):
        self.set_expression(name)
        time.sleep(duration)
        self.clear()

    def set_expression(self, name):
        expressions = self._expressions()
        pattern = expressions.get(name, expressions["neutre"])
        self._draw_pixels(pattern)

    def set_bitmap(self, rows):
        self._draw_pixels(self._pattern(self._normalize_bitmap(rows)))

    def set_icon(self, name):
        rows = ICON_8X8.get(str(name or "").strip().lower())
        if rows is None:
            rows = ICON_8X8["etoile"]
        self.set_bitmap(rows)

    @classmethod
    def icon_names(cls):
        return sorted(ICON_8X8)

    def show_text(self, text, duration=None, speed=0.12):
        text = str(text or "").strip()
        if not text:
            self.set_expression("sourire")
            return
        if len(text) == 1:
            self.set_bitmap(self._char_rows(text))
            return
        self.scroll_text(text, duration=duration, speed=speed)

    def scroll_text(self, text, duration=None, speed=0.12):
        columns = self._text_columns(str(text or ""))
        if not columns:
            self.set_expression("sourire")
            return

        blank = [0] * 8
        stream = [blank] * 8 + columns + [blank] * 8
        frame_count = max(1, len(stream) - 7)
        if duration is None:
            duration = frame_count * max(0.03, float(speed))
        max_frames = max(frame_count, int(max(0.2, float(duration)) / max(0.03, float(speed))))
        for offset in range(max_frames):
            frame_columns = stream[offset:offset + 8]
            if len(frame_columns) < 8:
                frame_columns = frame_columns + [blank] * (8 - len(frame_columns))
            self._draw_pixels(self._columns_to_pixels(frame_columns))
            time.sleep(max(0.03, float(speed)))
        self.set_expression("sourire")

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

    def _normalize_bitmap(self, rows):
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

    def _char_rows(self, char):
        char = str(char or " ")[0]
        glyph = FONT_5X7.get(char.upper(), FONT_5X7["?"])
        return ["........"] + [f".{row}.." for row in glyph]

    def _text_columns(self, text):
        columns = []
        for char in text[:24]:
            rows = self._char_rows(char)
            for x in range(8):
                column = []
                for y in range(8):
                    column.append(1 if rows[y][x] != "." else 0)
                columns.append(column)
            columns.append([0] * 8)
        return columns

    def _columns_to_pixels(self, columns):
        pixels = []
        for x, column in enumerate(columns[:8]):
            for y, value in enumerate(column[:8]):
                if value:
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
