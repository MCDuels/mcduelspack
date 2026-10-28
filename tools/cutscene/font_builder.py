"""Collects bitmap providers for the mcduels:cutscene font.

A bitmap glyph drawn in a title has its top edge at y = -3 - ascent, and Minecraft refuses an
ascent above the glyph height. Font textures are 256x256 pages, so no bitmap is bigger than that.
"""
import math
import os

from PIL import Image

FONT_KEY = 'mcduels:cutscene'
MAX_TEXTURE = 256


class FontBuilder:
    def __init__(self, textures_dir):
        self.textures_dir = textures_dir
        self.providers = []
        self.advances = {}
        self.spaces = {}
        self.next_code = 0xE000
        self.saved = {}

    def claim(self):
        char = chr(self.next_code)
        self.next_code += 1
        return char

    def texture(self, name, image):
        """Saves a texture once; asking again for a saved name returns the size it was saved with."""
        if name in self.saved:
            return self.saved[name]
        if image.width > MAX_TEXTURE or image.height > MAX_TEXTURE:
            raise ValueError('%s is %dx%d; font pages are %dx%d' % (name, image.width, image.height,
                                                                    MAX_TEXTURE, MAX_TEXTURE))
        mark_width(image).save(os.path.join(self.textures_dir, name + '.png'), optimize=True)
        self.saved[name] = image.size
        return image.size

    def glyph(self, texture, height, top):
        """A glyph showing a saved texture `height` units tall with its top edge at y = top."""
        if top != int(top):
            raise ValueError('%s: top %s is not a whole unit' % (texture, top))
        ascent = -3 - int(top)
        if ascent > height:
            raise ValueError('%s: ascent %d above height %d' % (texture, ascent, height))
        width, image_height = self.saved[texture]
        char = self.claim()
        self.providers.append({'type': 'bitmap', 'file': 'mcduels:cutscene/%s.png' % texture,
                               'height': height, 'ascent': ascent, 'chars': [char]})
        self.advances[char] = int(0.5 + width * height / image_height) + 1
        return char

    def add_spaces(self):
        for power in range(-2, 10):
            for sign in (1, -1):
                self.spaces[self.claim()] = sign * 2 ** power
        self.providers.insert(0, {'type': 'space', 'advances': dict(self.spaces)})

    def provider_json(self):
        return {'providers': self.providers}


def mark_width(image):
    """Glyph width is trimmed to the last non-empty column; an invisible pixel pins it."""
    if image.getpixel((image.width - 1, 0))[3] == 0:
        image.putpixel((image.width - 1, 0), (0, 0, 0, 1))
    return image


def padded(image, top, texels_per_unit, pad=0):
    """`image` moved down `pad` texels and padded below to whole units, at least as tall as its ascent."""
    units = max(math.ceil((pad + image.height) / texels_per_unit), -3 - top)
    canvas = Image.new('RGBA', (image.width, units * texels_per_unit), (0, 0, 0, 0))
    canvas.paste(image, (0, pad))
    return canvas, units


def place(font, name, image, x, y, texels_per_unit, strip=None):
    """Shows `image` with its top-left texel at (x, y), padding it so the glyph top is a whole unit."""
    top = math.floor(y)
    canvas, units = padded(image, top, texels_per_unit, round((y - top) * texels_per_unit))
    font.texture(name, canvas)
    char = font.glyph(name, units, top)
    return [char, x] if strip is None else [char, x, strip]


def place_sliced(font, name, image, x, y, texels_per_unit, bands):
    """Cuts `image` along the strip edges so each piece can leave with its own strip."""
    pieces = []
    for index, band in enumerate(bands):
        first = max(0, round((band['top'] - y) * texels_per_unit))
        last = min(image.height, round((band['bottom'] - y) * texels_per_unit))
        if last <= first:
            continue
        piece = image.crop((0, first, image.width, last))
        if piece.getbbox() is None:
            continue
        pieces.append(place(font, '%s_s%d' % (name, index), piece, x, y + first / texels_per_unit,
                            texels_per_unit, index))
    return pieces
