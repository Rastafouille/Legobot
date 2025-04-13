#!/usr/bin/env python3
from luma.led_matrix.device import max7219
from luma.core.interface.serial import spi, noop
from luma.core.render import canvas
import time

class MatrixFace:
    def __init__(self, rotate=0, block_orientation=90):
        serial = spi(port=0, device=0, gpio=noop())
        self.device = max7219(serial, cascaded=1, block_orientation=block_orientation, rotate=rotate)

    def show_expression(self, name, duration=1):
        expressions = self._expressions()
        pattern = expressions.get(name, [])
        with canvas(self.device) as draw:
            for x, y in pattern:
                draw.point((x, y), fill="white")
        time.sleep(duration)
        self.clear()

    def animate_talk(self, repeat=3, speed=0.3):
        mouth_open = [
            (1,3), (6,3),
            (0,4), (7,4),
            (1,5), (2,6), (3,6), (4,6), (5,6), (6,5)
        ]
        mouth_closed = [
            (1,4), (2,4), (3,4), (4,4), (5,4), (6,4)
        ]
        for _ in range(repeat):
            self._draw_pixels(mouth_open)
            time.sleep(speed)
            self._draw_pixels(mouth_closed)
            time.sleep(speed)
        self.clear()

    def clear(self):
        with canvas(self.device) as draw:
            pass

    def _draw_pixels(self, pixels):
        with canvas(self.device) as draw:
            for x, y in pixels:
                draw.point((x, y), fill="white")

    def _expressions(self):
        return {
            "sourire": [
                (0,5), (7,5),
                (1,6), (2,7), (3,7), (4,7), (5,7), (6,6)
            ],
            "triste": [
                (0,6), (7,6),
                (1,7), (2,6), (3,6), (4,6), (5,6), (6,7)
            ],
            "neutre": [
                (0,6), (1,6), (2,6), (3,6), (4,6), (5,6), (6,6), (7,6)
            ],
            "coeur": [
                (2,1), (5,1),
                (1,2), (3,2), (4,2), (6,2),
                (0,3), (1,3), (2,3), (3,3), (4,3), (5,3), (6,3), (7,3),
                (0,4), (1,4), (2,4), (3,4), (4,4), (5,4), (6,4), (7,4),
                (1,5), (2,5), (3,5), (4,5), (5,5), (6,5),
                (2,6), (3,6), (4,6), (5,6),
                (3,7), (4,7)
            ],
            "colere": [
                (0,2), (1,1), (2,1), (5,1), (6,1), (7,2),
                (1,3), (2,3), (3,3), (4,3), (5,3), (6,3)
            ],
            "vague": [
                (0,4), (1,3), (2,4), (3,3),
                (4,4), (5,3), (6,4), (7,3)
            ]
        }

if __name__ == "__main__":
    mouth = MatrixFace()
    try:
        print("Démarrage du test des expressions...")
        mouth.show_expression("sourire")
        mouth.show_expression("triste")
        mouth.show_expression("neutre")
        mouth.show_expression("coeur")
        mouth.show_expression("colere")
        mouth.show_expression("vague")
        mouth.animate_talk()
    except KeyboardInterrupt:
        mouth.clear()
        print("\nProgramme terminé")