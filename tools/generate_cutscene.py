#!/usr/bin/env python3
"""Draws the pre-duel VS cutscene glyphs and writes the font plus the layout the backend reads.

The cutscene is one title component re-sent every tick. Titles are drawn 4x scaled, centred on
the screen, so every number here is in "title units" (1 unit = 4 GUI pixels) with x growing to
the right and y growing down from the screen centre. A bitmap glyph drawn in a title has its top
edge at y = -3 - ascent, and Minecraft refuses an ascent above the glyph height, so glyphs that
sit high on the screen carry transparent padding underneath. Font textures are 256x256 pages,
so no glyph bitmap is bigger than that.

Outputs:
  assets/mcduels/textures/cutscene/*.png    glyph bitmaps
  assets/mcduels/font/cutscene.json         the mcduels:cutscene font
  tools/cutscene-layout.json                where each piece goes; the backend ships a copy as
                                            src/main/resources/cutscene/layout.json
"""
import json
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXTURES = os.path.join(ROOT, 'assets', 'mcduels', 'textures', 'cutscene')
FONT_FILE = os.path.join(ROOT, 'assets', 'mcduels', 'font', 'cutscene.json')
LAYOUT_FILE = os.path.join(ROOT, 'tools', 'cutscene-layout.json')
FONT_KEY = 'mcduels:cutscene'

BOLD_FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
MONO_FONT = '/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf'

# The diagonal cut runs through the VS centre, from the top-left to the bottom-right.
CENTER_Y = -4
SLOPE = 1.5            # screen y grows SLOPE units per unit of x along the cut
REACH_X = 250          # panels cover x in [-REACH_X, REACH_X]
SLAB = 48              # panel edge is built from identical tiles, one per SLAB units of height
FIRST_SLAB_TOP = -124  # 6 slabs cover y in [-125, 165]
SLAB_COUNT = 6
EDGE_RES = 0.5         # units per texel along the cut
EDGE_MARGIN = 8
EDGE_RED = (255, 59, 59)
EDGE_DARK = (120, 8, 8)

HEAD_PIXEL = 3
HEADS = {'p1': (18, -31), 'p2': (-42, -1)}   # top-left corner of each 8x8 face
NAME_TOP = {'p1': -4, 'p2': -10}   # just under the first face's frame, just over the second's
NAME_CENTER = {'p1': 30, 'p2': -30}
NAME_HEIGHT = 12                    # 12x24 texel cells (padded to 48 tall) at 0.25 units per texel
NAME_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_'
VS_HEIGHTS = [24, 18, 14, 12]   # slam frames, biggest first; the last one is the resting size


class Font:
    def __init__(self):
        self.providers = []
        self.next_code = 0xE000
        self.advances = {}

    def claim(self):
        char = chr(self.next_code)
        self.next_code += 1
        return char

    def bitmap(self, file, image_height, height, ascent, width_texels):
        if ascent > height:
            raise ValueError('%s: ascent %d above height %d' % (file, ascent, height))
        char = self.claim()
        self.providers.append({'type': 'bitmap', 'file': 'mcduels:cutscene/%s.png' % file,
                               'height': height, 'ascent': ascent, 'chars': [char]})
        scale = height / image_height
        self.advances[char] = int(0.5 + width_texels * scale) + 1
        return char


def save(name, image):
    if image.width > 256 or image.height > 256:
        raise ValueError('%s is %dx%d; font pages are 256x256' % (name, image.width, image.height))
    image.save(os.path.join(TEXTURES, name + '.png'), optimize=True)


def mark_width(image):
    """Glyph width is trimmed to the last non-empty column; an invisible pixel pins it."""
    if image.getpixel((image.width - 1, 0))[3] == 0:
        image.putpixel((image.width - 1, 0), (0, 0, 0, 1))
    return image


def cut_x(y):
    return (y - CENTER_Y) / SLOPE


def edge_tile(side):
    """One slab of a panel: black on its side of the cut, a red rim along the cut."""
    width_units = SLAB / SLOPE + 2 * EDGE_MARGIN
    tw, th = int(width_units / EDGE_RES), int((SLAB + 2) / EDGE_RES)
    image = Image.new('RGBA', (tw, 256), (0, 0, 0, 0))
    samples = 4
    for ty in range(th):
        for tx in range(tw):
            covered, rim, dark = 0, 0, 0
            for sy in range(samples):
                for sx in range(samples):
                    x = (tx + (sx + 0.5) / samples) * EDGE_RES
                    y = (ty + (sy + 0.5) / samples) * EDGE_RES
                    line = EDGE_MARGIN + (y - 1) / SLOPE
                    depth = (x - line) if side == 'a' else (line - x)
                    if depth < 0:
                        continue
                    covered += 1
                    if depth < 1.5:
                        rim += 1
                    elif depth < 2.0:
                        dark += 1
            if not covered:
                continue
            black = covered - rim - dark
            colour = tuple(int((EDGE_RED[i] * rim + EDGE_DARK[i] * dark) / covered) for i in range(3))
            if black == covered:
                colour = (0, 0, 0)
            image.putpixel((tx, ty), colour + (int(255 * covered / samples ** 2),))
    return mark_width(image)


def panels(font):
    save('panel_a', edge_tile('a'))
    save('panel_b', edge_tile('b'))
    block = Image.new('RGBA', (1, 3), (0, 0, 0, 0))
    block.putpixel((0, 0), (0, 0, 0, 255))
    save('block', block)
    tile_w = int((SLAB / SLOPE + 2 * EDGE_MARGIN) / EDGE_RES)
    parts = {'a': [], 'b': []}
    for slab in range(SLAB_COUNT):
        top = FIRST_SLAB_TOP + slab * SLAB - 1
        ascent = -3 - top
        tile_x = cut_x(top + 1) - EDGE_MARGIN
        tile_units = tile_w * EDGE_RES
        block_char = font.bitmap('block', 3, 150, ascent, 1)
        for side in 'ab':
            tile = font.bitmap('panel_' + side, 256, int(256 * EDGE_RES), ascent, tile_w)
            parts[side].append([tile, tile_x])
        x = tile_x + tile_units - 1
        while x < REACH_X:
            parts['a'].append([block_char, x])
            x += 50
        x = tile_x + 1 - 50
        while x + 50 > -REACH_X:
            parts['b'].append([block_char, x])
            x -= 50
    return parts


def draw_vs(height_units):
    res = 0.25
    w, h = int(height_units * 2 / res), int(height_units / res)
    big = 8
    canvas = Image.new('RGBA', (w * big, h * big), (0, 0, 0, 0))
    font = ImageFont.truetype(BOLD_FONT, int(h * big * 1.05))
    text = Image.new('L', canvas.size, 0)
    ImageDraw.Draw(text).text((w * big / 2, h * big / 2), 'VS', font=font, fill=255, anchor='mm')
    skew = 0.22
    text = text.transform(text.size, Image.AFFINE, (1, skew, -skew * h * big / 2, 0, 1, 0), Image.BICUBIC)
    box = text.getbbox()
    text = text.crop(box).resize((int(w * big * 0.86), int(h * big * 0.82)), Image.LANCZOS)
    fill = Image.new('L', canvas.size, 0)
    fill.paste(text, ((canvas.width - text.width) // 2, (canvas.height - text.height) // 2))
    stroke = fill.filter(ImageFilter.MaxFilter(big * 2 + 1 if big * 2 % 2 == 0 else big * 2))
    glow = stroke.filter(ImageFilter.MaxFilter(big + 1 if big % 2 == 0 else big)).filter(
        ImageFilter.GaussianBlur(big))
    gradient = Image.new('RGBA', canvas.size)
    for y in range(canvas.height):
        t = y / canvas.height
        top, bottom = (255, 245, 170), (255, 140, 20)
        colour = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        ImageDraw.Draw(gradient).line([(0, y), (canvas.width, y)], fill=colour + (255,))
    canvas.paste((229, 64, 64, 255), (0, 0), glow.point(lambda v: int(v * 0.9)))
    canvas.paste((30, 0, 0, 255), (0, 0), stroke)
    canvas.paste(gradient, (0, 0), fill)
    return canvas.resize((w, h), Image.LANCZOS)


def split_vs(image):
    res = 0.25
    halves = {'a': image.copy(), 'b': image.copy()}
    left, top = -image.width * res / 2, CENTER_Y - image.height * res / 2
    for ty in range(image.height):
        for tx in range(image.width):
            x, y = left + (tx + 0.5) * res, top + (ty + 0.5) * res
            on_a = (y - CENTER_Y) < SLOPE * x
            halves['b' if on_a else 'a'].putpixel((tx, ty), (0, 0, 0, 0))
    return {side: mark_width(half) for side, half in halves.items()}


def vs(font):
    frames = []
    for height in VS_HEIGHTS:
        image = mark_width(draw_vs(height))
        save('vs_%d' % height, image)
        top = CENTER_Y - height // 2
        char = font.bitmap('vs_%d' % height, image.height, height, -3 - top, image.width)
        frames.append([[char, -height]])
    rest = draw_vs(VS_HEIGHTS[-1])
    halves = {}
    for side, half in split_vs(rest).items():
        save('vs_%s' % side, half)
        top = CENTER_Y - VS_HEIGHTS[-1] // 2
        char = font.bitmap('vs_%s' % side, half.height, VS_HEIGHTS[-1], -3 - top, half.width)
        halves[side] = [[char, -VS_HEIGHTS[-1]]]
    return frames, halves


def heads(font):
    dot = Image.new('RGBA', (1, 16), (0, 0, 0, 0))
    dot.putpixel((0, 0), (255, 255, 255, 255))
    save('dot', dot)
    frame = Image.new('RGBA', (56, 128), (0, 0, 0, 0))
    draw = ImageDraw.Draw(frame)
    draw.rectangle([0, 0, 55, 55], outline=(255, 255, 255, 255), width=2)
    draw.rectangle([2, 2, 53, 53], outline=(90, 90, 90, 255), width=1)
    save('frame', frame)
    layout = {}
    for seat, (x, y) in HEADS.items():
        rows = [font.bitmap('dot', 16, 16 * HEAD_PIXEL, -3 - (y + row * HEAD_PIXEL), 1) for row in range(8)]
        frame_char = font.bitmap('frame', 128, 64, -3 - (y - 2), 56)
        layout[seat] = {'x': x, 'rows': rows, 'frame': [[frame_char, x - 2]]}
    return layout


def names(font):
    cell_w, cell_h = 12, 24
    mono = ImageFont.truetype(MONO_FONT, 20)
    chars = {seat: {} for seat in NAME_TOP}
    for index, char in enumerate(NAME_CHARS):
        image = Image.new('RGBA', (cell_w, cell_h * 2), (0, 0, 0, 0))
        mask = Image.new('L', (cell_w, cell_h), 0)
        ImageDraw.Draw(mask).text((cell_w / 2, cell_h - 5), char, font=mono, fill=255, anchor='ms')
        image.paste((255, 255, 255, 255), (0, 0), mask)
        name = 'name_%02d' % index
        save(name, mark_width(image))
        for seat, top in NAME_TOP.items():
            chars[seat][char] = font.bitmap(name, cell_h * 2, NAME_HEIGHT, -3 - top, cell_w)
    return {'chars': chars, 'advance': font.advances[chars['p1']['A']], 'center': NAME_CENTER}


def spaces(font):
    advances = {}
    for power in range(-1, 10):
        for sign in (1, -1):
            advance = sign * 2 ** power
            char = font.claim()
            advances[char] = advance
    font.providers.insert(0, {'type': 'space', 'advances': advances})
    return {char: advance for char, advance in advances.items()}


def main():
    os.makedirs(TEXTURES, exist_ok=True)
    os.makedirs(os.path.dirname(FONT_FILE), exist_ok=True)
    for name in os.listdir(TEXTURES):
        os.remove(os.path.join(TEXTURES, name))
    font = Font()
    space = spaces(font)
    panel_parts = panels(font)
    vs_frames, vs_halves = vs(font)
    head_layout = heads(font)
    name_layout = names(font)
    layout = {
        'font': FONT_KEY,
        'spaces': space,
        'advances': font.advances,
        'panel_a': panel_parts['a'],
        'panel_b': panel_parts['b'],
        'vs_frames': vs_frames,
        'vs_a': vs_halves['a'],
        'vs_b': vs_halves['b'],
        'head_pixel': HEAD_PIXEL,
        'heads': head_layout,
        'names': name_layout,
    }
    with open(FONT_FILE, 'w', encoding='utf-8') as out:
        json.dump({'providers': font.providers}, out, indent=2)
        out.write('\n')
    with open(LAYOUT_FILE, 'w', encoding='utf-8') as out:
        json.dump(layout, out, indent=1)
        out.write('\n')


if __name__ == '__main__':
    main()
