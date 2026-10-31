"""The in-arena cinematic after the VS card: letterbox bars, fade levels and a lower-third caption.

The bars slide in from the screen edges one unit at a time, so each step is its own glyph pair. A
title is the same size in units at every window size, so the bars are tuned for the automatic GUI
scale (about 30 to 34 units from the centre to the top edge): they reach 25 units from the centre
when closed and start just past the edge. The fades are the full-screen cover at lower opacities,
tinted ink by the backend for dips to black.
"""
from PIL import Image

from . import geometry as g
from .card import BAR_WIDTHS, DISPLAY_TEXELS_PER_UNIT, MONO_TEXELS_PER_UNIT
from .panels import bars
from .type_sets import DISPLAY_CHARS, MONO_CHARS, anton, geist_mono, text_row

LETTERBOX_OPEN = 34
LETTERBOX_CLOSED = 25
BAR_PIECE_WIDTH = 170
FADE_LEVELS = 16

CAPTION_NAME_CAP = 5
CAPTION_NAME_BASELINE = 21
CAPTION_LABEL_BASELINE = 14
CAPTION_RULE_TOP = 23


def _bar(font, name, top, bar_height, glyph_height):
    """A white bar `bar_height` units tall at y = top, inside a glyph `glyph_height` units tall."""
    image = Image.new('RGBA', (BAR_PIECE_WIDTH, glyph_height), (0, 0, 0, 0))
    image.paste((255, 255, 255, 255), (0, 0, BAR_PIECE_WIDTH, bar_height))
    font.texture(name, image)
    return font.glyph(name, glyph_height, top)


def letterbox(font):
    """Per step, from just off screen to closed: the top bar and the bottom bar, each drawn twice side by side."""
    steps = []
    reach = -3 - g.COVER_TOP
    for edge in range(LETTERBOX_OPEN, LETTERBOX_CLOSED - 1, -1):
        height = g.COVER_TOP + g.COVER_HEIGHT - edge
        steps.append({
            'edge': edge,
            'top': _bar(font, 'letterbox_top_%d' % edge, g.COVER_TOP, height, max(height, reach)),
            'bottom': _bar(font, 'letterbox_bottom_%d' % edge, edge, height, height),
        })
    return {'steps': steps, 'left': -BAR_PIECE_WIDTH, 'piece': BAR_PIECE_WIDTH}


def fades(font):
    """The cover at 1/16 to 15/16 opacity, lightest first."""
    levels = []
    for level in range(1, FADE_LEVELS):
        name = 'fade_%02d' % level
        font.texture(name, Image.new('RGBA', (4, 2), (255, 255, 255, round(255 * level / FADE_LEVELS))))
        levels.append([font.glyph(name, g.COVER_HEIGHT, g.COVER_TOP), -g.COVER_HEIGHT])
    return levels


def caption(font):
    """Lower third over the bottom bar: a small label, the fighter's name and a rule in their colour."""
    return {
        'label': text_row(font, geist_mono(700), MONO_CHARS, g.MONO_CAP, CAPTION_LABEL_BASELINE,
                          MONO_TEXELS_PER_UNIT, g.TRACKING['label']),
        'name': text_row(font, anton(), DISPLAY_CHARS, CAPTION_NAME_CAP, CAPTION_NAME_BASELINE,
                         DISPLAY_TEXELS_PER_UNIT),
        'rule': bars(font, 1, CAPTION_RULE_TOP, BAR_WIDTHS),
    }


def cinema(font):
    return {'letterbox': letterbox(font), 'fade': fades(font), 'caption': caption(font)}
