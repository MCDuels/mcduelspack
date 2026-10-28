"""Each fighter's 8x8 face: one white row glyph per pixel row, tinted per pixel, on an ink plate."""
import math

from PIL import Image, ImageDraw

from . import geometry as g
from .font_builder import padded, place_sliced

ROW_TEXELS_PER_UNIT = 2
PLATE_TEXELS_PER_UNIT = 4


def _row(font, y):
    top = math.floor(y)
    pad = round((y - top) * ROW_TEXELS_PER_UNIT)
    side = round(g.FACE_PIXEL * ROW_TEXELS_PER_UNIT)
    rows = math.ceil((pad + side) / ROW_TEXELS_PER_UNIT) * ROW_TEXELS_PER_UNIT
    image = Image.new('RGBA', (side, rows), (0, 0, 0, 0))
    ImageDraw.Draw(image).rectangle([0, pad, side - 1, pad + side - 1], fill=(255, 255, 255, 255))
    canvas, units = padded(image, top, ROW_TEXELS_PER_UNIT)
    name = 'face_row_%d_%d' % (pad, units)
    font.texture(name, canvas)
    return [font.glyph(name, units, top), 0, g.strip_at(y + g.FACE_PIXEL / 2)]


def _plate():
    """The frame around the face with a hard drop shadow, drawn from the frame's top-left corner."""
    scale = PLATE_TEXELS_PER_UNIT
    frame = round((8 * g.FACE_PIXEL + 2 * g.FACE_BORDER) * scale)
    shadow = round(g.FACE_SHADOW * scale)
    image = Image.new('RGBA', (frame + shadow, frame + shadow), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle([shadow, shadow, frame + shadow - 1, frame + shadow - 1], fill=(255, 255, 255, 255))
    draw.rectangle([0, 0, frame - 1, frame - 1], fill=(255, 255, 255, 255))
    return image


def faces(font):
    rows = [_row(font, g.FACE_TOP + index * g.FACE_PIXEL) for index in range(8)]
    plate = place_sliced(font, 'face_plate', _plate(), -g.FACE_BORDER, g.FACE_TOP - g.FACE_BORDER,
                         PLATE_TEXELS_PER_UNIT, g.strips())
    return {'pixel': g.FACE_PIXEL, 'border': g.FACE_BORDER, 'x': g.FACE_X, 'rows': rows, 'plate': plate}
