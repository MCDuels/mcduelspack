#!/usr/bin/env python3
"""Renders the VS cutscene the way a client draws the title, for checking the art without a game.

Reads assets/mcduels/font/cutscene.json and tools/cutscene-layout.json, plays the same timeline
the backend uses (default timings) and writes a GIF plus a few still frames. Draws at GUI scale 2
on a 1920x1080 screen: 960x540 GUI pixels, one title unit = 4 pixels.

    python3 tools/preview_cutscene.py [out_dir]
"""
import json
import os
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_FILE = os.path.join(ROOT, 'assets', 'mcduels', 'font', 'cutscene.json')
LAYOUT_FILE = os.path.join(ROOT, 'tools', 'cutscene-layout.json')
TEXTURES = os.path.join(ROOT, 'assets', 'mcduels', 'textures')
SCREEN = (960, 540)
UNIT = 4

FADE, INTRO, HOLD, SPLIT = 10, 8, 30, 10
SLIDE_IN, SPLIT_DISTANCE = 140, 260
SHAKE = [2, -2, 1]
NAME_CLEARANCE = 14
P1_COLOUR, P2_COLOUR, NAME_COLOUR = (229, 64, 64), (64, 104, 229), (255, 255, 255)


def load_glyphs():
    glyphs = {}
    for provider in json.load(open(FONT_FILE, encoding='utf-8'))['providers']:
        if provider['type'] == 'space':
            continue
        namespace, path = provider['file'].split(':')
        image = Image.open(os.path.join(TEXTURES, path)).convert('RGBA')
        scale = provider['height'] / image.height
        for char in provider['chars']:
            glyphs[char] = (image, scale, provider['ascent'])
    return glyphs


def face(seed):
    """A stand-in skin face: skin tone, hair, eyes."""
    pixels = []
    for y in range(8):
        for x in range(8):
            if y < 2 or (y == 2 and x in (0, 7)):
                pixels.append(seed)
            elif y == 4 and x in (1, 2, 5, 6):
                pixels.append((255, 255, 255) if x in (1, 6) else (40, 60, 140))
            elif y == 6 and 2 <= x <= 5:
                pixels.append((110, 60, 40))
            else:
                pixels.append((214, 160, 120))
    return pixels


class Frame:
    def __init__(self, glyphs):
        self.glyphs = glyphs
        self.parts = []

    def place(self, char, x, colour=(255, 255, 255)):
        self.parts.append((char, x, colour))

    def render(self, background):
        screen = background.copy()
        cx, cy = SCREEN[0] // 2, SCREEN[1] // 2
        for char, x, colour in self.parts:
            image, scale, ascent = self.glyphs[char]
            px = UNIT * scale
            glyph = image.resize((max(1, round(image.width * px)), max(1, round(image.height * px))), Image.NEAREST)
            r, g, b, a = glyph.split()
            tinted = Image.merge('RGBA', (
                r.point(lambda v, c=colour[0]: v * c // 255),
                g.point(lambda v, c=colour[1]: v * c // 255),
                b.point(lambda v, c=colour[2]: v * c // 255),
                a))
            screen.alpha_composite(tinted, (cx + round(x * UNIT), cy + round((-3 - ascent) * UNIT)))
        return screen


def compose(layout, glyphs, tick, names):
    frame = Frame(glyphs)
    intro_end, slam_end = FADE + INTRO, FADE + INTRO + len(layout['vs_frames'])
    split_start = slam_end + HOLD
    split = 0
    if tick >= split_start:
        u = min(1.0, (tick - split_start + 1) / SPLIT)
        split = round(u * u * SPLIT_DISTANCE)
    shake = SHAKE[tick - slam_end + 1] if 0 <= tick - slam_end + 1 < len(SHAKE) else 0
    slide = None
    if tick >= FADE:
        u = min(1.0, (tick - FADE + 1) / INTRO)
        slide = round((1 - u) ** 3 * SLIDE_IN)
    sides = {'p1': split + shake, 'p2': -split + shake}
    for char, x in layout['panel_a']:
        frame.place(char, x + sides['p1'])
    for char, x in layout['panel_b']:
        frame.place(char, x + sides['p2'])
    if slide is not None:
        for seat, colour, direction in (('p1', P1_COLOUR, 1), ('p2', P2_COLOUR, -1)):
            dx = sides[seat] + direction * slide
            head = layout['heads'][seat]
            for char, x in head['frame']:
                frame.place(char, x + dx, colour)
            pixel = layout['head_pixel']
            for row, char in enumerate(head['rows']):
                for col in range(8):
                    frame.place(char, head['x'] + col * pixel + dx, names[seat][1][row * 8 + col])
            text = names[seat][0]
            advance = layout['names']['advance']
            width = len(text) * advance - 1
            left = layout['names']['center'][seat] - width / 2
            left = max(left, NAME_CLEARANCE) if seat == 'p1' else min(left, -NAME_CLEARANCE - width)
            for index, letter in enumerate(text):
                frame.place(layout['names']['chars'][seat][letter], left + index * advance + dx, NAME_COLOUR)
    if tick >= intro_end:
        if tick < slam_end:
            for char, x in layout['vs_frames'][tick - intro_end]:
                frame.place(char, x + shake)
        else:
            for char, x in layout['vs_a']:
                frame.place(char, x + sides['p1'])
            for char, x in layout['vs_b']:
                frame.place(char, x + sides['p2'])
    alpha = min(1.0, (tick + 1) / FADE)
    return frame, alpha


def arena():
    image = Image.new('RGBA', SCREEN)
    draw = ImageDraw.Draw(image)
    for y in range(SCREEN[1]):
        if y < SCREEN[1] * 0.55:
            t = y / (SCREEN[1] * 0.55)
            colour = (int(120 + 60 * t), int(170 + 40 * t), 255)
        else:
            colour = (70, 140, 60) if (y // 12) % 2 else (80, 150, 66)
        draw.line([(0, y), (SCREEN[0], y)], fill=colour + (255,))
    draw.rectangle([600, 250, 640, 330], fill=(40, 40, 40, 255))
    return image


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'preview')
    os.makedirs(out, exist_ok=True)
    layout = json.load(open(LAYOUT_FILE, encoding='utf-8'))
    glyphs = load_glyphs()
    names = {'p1': ('Bannerfall', face((60, 40, 20))), 'p2': ('xX_Sw0rdGod_Xx', face((20, 20, 20)))}
    background = arena()
    total = FADE + INTRO + len(layout['vs_frames']) + HOLD + SPLIT + 4
    frames = []
    for tick in range(total):
        if tick >= total - 4:
            frames.append(background.copy())
            continue
        frame, alpha = compose(layout, glyphs, tick, names)
        drawn = frame.render(background)
        frames.append(Image.blend(background, drawn, alpha) if alpha < 1 else drawn)
    for tick in (FADE + INTRO - 1, FADE + INTRO + len(layout['vs_frames']) + 10, total - 4 - SPLIT // 2):
        frames[tick].convert('RGB').save(os.path.join(out, 'frame_%02d.png' % tick))
    frames[0].convert('RGB').save(os.path.join(out, 'cutscene.gif'), save_all=True,
                                  append_images=[f.convert('RGB') for f in frames[1:]], duration=50, loop=0)


if __name__ == '__main__':
    main()
