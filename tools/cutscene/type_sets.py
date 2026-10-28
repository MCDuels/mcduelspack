"""Text rows drawn from real fonts: one glyph per character, all sharing a baseline.

The backend lays a string out itself: each letter goes at the pen position plus its ink offset,
and the pen moves on by the letter's advance plus the row's tracking.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

from .font_builder import padded

FONTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fonts')
ANTON = os.path.join(FONTS, 'Anton-Regular.ttf')
GEIST_MONO = os.path.join(FONTS, 'GeistMono.ttf')

DISPLAY_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_ '
MONO_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.- '


class Face:
    def __init__(self, path, weight=None):
        self.path = path
        self.weight = weight
        probe = self.sized(1000)
        self.cap_ratio = -probe.getbbox('H', anchor='ls')[1] / 1000

    def sized(self, pixels):
        face = ImageFont.truetype(self.path, pixels)
        if self.weight is not None:
            face.set_variation_by_axes([self.weight])
        return face

    def key(self):
        return '%s_%s' % (os.path.splitext(os.path.basename(self.path))[0].lower(), self.weight or 'r')


def anton():
    return Face(ANTON)


def geist_mono(weight):
    return Face(GEIST_MONO, weight)


def text_row(font, face, chars, cap, baseline, texels_per_unit, tracking=0.0, strip=None):
    """Glyphs for `chars` with capital letters `cap` units tall standing on y = baseline."""
    cap_texels = round(cap * texels_per_unit)
    pil_font = face.sized(round(cap_texels / face.cap_ratio))
    top = math.floor(baseline - cap)
    pad = round((baseline - cap - top) * texels_per_unit)
    descent = max(max(pil_font.getbbox(c, anchor='ls')[3], 0) for c in chars if c != ' ')
    rows = math.ceil((pad + cap_texels + descent) / texels_per_unit) * texels_per_unit
    letters, advances = {}, {}
    for char in chars:
        advances[char] = pil_font.getlength(char) / texels_per_unit
        if char == ' ':
            continue
        left, _, right, _ = pil_font.getbbox(char, anchor='ls')
        image = Image.new('RGBA', (max(1, right - left), rows), (0, 0, 0, 0))
        ImageDraw.Draw(image).text((-left, pad + cap_texels), char, font=pil_font,
                                   fill=(255, 255, 255, 255), anchor='ls')
        canvas, units = padded(image, top, texels_per_unit)
        name = '%s_%d_%d_%d_%04x' % (face.key(), cap_texels, pad, units, ord(char))
        font.texture(name, canvas)
        letters[char] = [font.glyph(name, units, top), left / texels_per_unit]
    row = {'chars': letters, 'advances': advances, 'tracking': tracking}
    if strip is not None:
        row['strip'] = strip
    return row
