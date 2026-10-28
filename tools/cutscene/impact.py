"""The impact burst: three shock rings and a ring of streaks, one frame per tick after the VS lands.

Each frame is split into quadrants so it stays inside 256x256 pages, and into one white layer
per colour (paper, orange, blue) for the backend to tint.
"""
import math
import random

from PIL import Image, ImageDraw

from .font_builder import place
from .motion import IMPACT_TICKS, ease_out_expo

REACH = 75
TEXELS_PER_UNIT = 3
SUPERSAMPLE = 3
RING_RADIUS = 74.4
RINGS = [(0, 'paper', 3.0), (0.8, 'orange', 1.7), (1.6, 'blue', 0.94)]
STREAK_COLOURS = ['paper', 'orange', 'blue']
STREAK_COUNT = 18
RING_GROW_TICKS = 8
STREAK_TICKS = 6


def _streaks():
    rng = random.Random(1987)
    return [{'angle': index / STREAK_COUNT * 2 * math.pi + rng.random() / 3,
             'reach': (0.55 + rng.random() * 0.6) * 60,
             'colour': STREAK_COLOURS[index % 3]} for index in range(STREAK_COUNT)]


def _draw(elapsed, streaks):
    unit = TEXELS_PER_UNIT * SUPERSAMPLE
    side = 2 * REACH * unit
    layers = {colour: Image.new('L', (side, side), 0) for colour in STREAK_COLOURS}
    centre = side / 2
    for delay, colour, width in RINGS:
        grow = min(1.0, max(0.0, (elapsed - delay) / RING_GROW_TICKS))
        if grow <= 0 or grow >= 1:
            continue
        radius = ease_out_expo(grow) * RING_RADIUS * unit
        stroke = max(1, round(width * (1 - grow) ** 1.5 * unit))
        ImageDraw.Draw(layers[colour]).ellipse([centre - radius, centre - radius, centre + radius, centre + radius],
                                               outline=255, width=stroke)
    flight = min(1.0, elapsed / STREAK_TICKS)
    if flight < 1:
        for streak in streaks:
            head = ease_out_expo(flight) * streak['reach']
            tail = max(0.0, head - 13.1 * (1 - flight))
            dx, dy = math.cos(streak['angle']), math.sin(streak['angle'])
            ImageDraw.Draw(layers[streak['colour']]).line(
                [(centre + dx * tail * unit, centre + dy * tail * unit),
                 (centre + dx * head * unit, centre + dy * head * unit)],
                fill=255, width=max(1, round(0.75 * (1 - flight) * unit)))
    shrunk = side // SUPERSAMPLE
    return {colour: mask.resize((shrunk, shrunk), Image.LANCZOS) for colour, mask in layers.items()}


def impact(font):
    streaks = _streaks()
    frames = []
    for elapsed in range(IMPACT_TICKS):
        frame = {colour: [] for colour in STREAK_COLOURS}
        for colour, mask in _draw(elapsed, streaks).items():
            quarter = mask.width // 2
            for row in range(2):
                for column in range(2):
                    piece = mask.crop((column * quarter, row * quarter, (column + 1) * quarter, (row + 1) * quarter))
                    if piece.getbbox() is None:
                        continue
                    image = Image.new('RGBA', piece.size, (255, 255, 255, 0))
                    image.putalpha(piece)
                    name = 'impact%d_%s_%d%d' % (elapsed, colour, row, column)
                    frame[colour].append(place(font, name, image, -REACH + column * REACH,
                                               -REACH + row * REACH, TEXELS_PER_UNIT))
        frames.append(frame)
    return frames
