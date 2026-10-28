"""The VS: it drops from 3x onto the seam, then its ink and paper echoes spring back into place.

Every frame is two white layers, the ink echo and the paper (echo plus letters), tinted by the
backend. The resting frame is cut into strips so it can leave with the slice exit.
"""
import math

from PIL import Image, ImageDraw

from . import geometry as g
from .font_builder import place, place_sliced
from .motion import drop_scales, spring_depths

DROP_DEPTH = 1.4
SUPERSAMPLE = 4


def _render(face, scale, depth):
    cap = g.VS_CAP * scale
    texels_per_unit = max(1, min(4, int(240 / (cap * 1.35))))
    pil_font = face.sized(round(cap * texels_per_unit * SUPERSAMPLE / face.cap_ratio))
    width = pil_font.getlength('VS') / (texels_per_unit * SUPERSAMPLE)
    step_x, step_y = (step * depth * scale for step in g.VS_ECHO_STEP)
    left, top = -width / 2, g.VS_BASELINE * scale - cap
    right, bottom = width / 2 + 2 * step_x + 1, g.VS_BASELINE * scale + 2 * step_y + 1
    left, top = math.floor(left), math.floor(top)
    unit = texels_per_unit * SUPERSAMPLE
    size = (math.ceil((right - left) * unit), math.ceil((bottom - top) * unit))
    layers = {'ink': Image.new('L', size, 0), 'paper': Image.new('L', size, 0)}
    origin = ((-width / 2 - left) * unit, (g.VS_BASELINE * scale - top) * unit)
    for layer, steps in (('ink', 2), ('paper', 1), ('paper', 0)):
        position = (origin[0] + steps * step_x * unit, origin[1] + steps * step_y * unit)
        ImageDraw.Draw(layers[layer]).text(position, 'VS', font=pil_font, fill=255, anchor='ls')
    shrunk = (size[0] // SUPERSAMPLE, size[1] // SUPERSAMPLE)
    images = {}
    for layer, mask in layers.items():
        image = Image.new('RGBA', shrunk, (255, 255, 255, 0))
        image.putalpha(mask.resize(shrunk, Image.LANCZOS))
        images[layer] = image
    return left, top, texels_per_unit, images


def _frame(font, face, name, scale, depth, sliced=False):
    left, top, texels_per_unit, images = _render(face, scale, depth)
    frame = {}
    for layer, image in images.items():
        texture = '%s_%s' % (name, layer)
        if sliced:
            frame[layer] = place_sliced(font, texture, image, left, top, texels_per_unit, g.strips())
        else:
            frame[layer] = [place(font, texture, image, left, top, texels_per_unit)]
    return frame


def vs(font, face):
    drop = [_frame(font, face, 'vs_drop%d' % index, scale, DROP_DEPTH)
            for index, scale in enumerate(drop_scales())]
    depths = spring_depths()
    spring = [_frame(font, face, 'vs_spring%d' % index, 1, depth) for index, depth in enumerate(depths)]
    rest = _frame(font, face, 'vs_rest', 1, depths[-1], sliced=True)
    return {'drop': drop, 'spring': spring, 'rest': rest}
