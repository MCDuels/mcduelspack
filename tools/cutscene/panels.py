"""The two coloured halves meeting on the slanted seam, cut into strips, plus full-screen covers.

Every texture is white; the backend tints it. Panel edges are hard so two halves tinted the same
colour cover the screen without a hairline gap.
"""
import math

from PIL import Image

from . import geometry as g
from .font_builder import padded

FLASH_ALPHAS = [230, 128, 51]
SEAM_SAMPLES = 4


def _edge_tiles(band, texels_per_unit):
    top, bottom = band['top'], band['bottom']
    left = math.floor(min(g.seam_x(top), g.seam_x(bottom))) - 1
    right = math.ceil(max(g.seam_x(top), g.seam_x(bottom))) + 1
    size = ((right - left) * texels_per_unit, (bottom - top) * texels_per_unit)
    tiles = {side: Image.new('RGBA', size, (0, 0, 0, 0)) for side in ('a', 'b', 'seam')}
    for ty in range(size[1]):
        y = top + (ty + 0.5) / texels_per_unit
        for tx in range(size[0]):
            x = left + (tx + 0.5) / texels_per_unit
            tiles['a' if x < g.seam_x(y) else 'b'].putpixel((tx, ty), (255, 255, 255, 255))
            coverage = _seam_coverage(left, top, tx, ty, texels_per_unit)
            if coverage:
                tiles['seam'].putpixel((tx, ty), (255, 255, 255, round(255 * coverage)))
    return left, right, tiles


def _seam_coverage(left, top, tx, ty, texels_per_unit):
    """Share of a texel the seam line covers, so the line itself is smooth over the hard panel edge."""
    hits = 0
    for sy in range(SEAM_SAMPLES):
        y = top + (ty + (sy + 0.5) / SEAM_SAMPLES) / texels_per_unit
        for sx in range(SEAM_SAMPLES):
            x = left + (tx + (sx + 0.5) / SEAM_SAMPLES) / texels_per_unit
            hits += abs(x - g.seam_x(y)) < g.SEAM_WIDTH / 2
    return hits / SEAM_SAMPLES ** 2


def _span(height, top):
    """Units a glyph `height` tall must span to sit at `top`: whole multiples of its height."""
    return height * max(1, math.ceil((-3 - top) / height))


def _solid(size, rows):
    image = Image.new('RGBA', (size[0], size[1] * rows), (0, 0, 0, 0))
    image.paste((255, 255, 255, 255), (0, 0, size[0], size[1]))
    return image


def _block(font, height, top):
    """A white bar `height` units tall reaching at least PANEL_REACH units."""
    texels = math.ceil(g.PANEL_REACH / height)
    rows = _span(height, top) // height
    name = 'block_%dx%d' % (height, rows)
    font.texture(name, _solid((texels, 1), rows))
    return name, texels * height


def _edge_bar(font, height, top):
    """A white bar 2 units wide down one strip, for the trailing edge as the strip leaves."""
    rows = _span(height, top) // height
    name = 'edge_%dx%d' % (height, rows)
    font.texture(name, _solid((1, height // 2), rows))
    return name


def strips(font):
    """Per strip: the blue half, the orange half and the seam, with the strip's outer edges."""
    layout = []
    for index, band in enumerate(g.strips()):
        height = band['bottom'] - band['top']
        span = max(height, -3 - band['top'])
        texels_per_unit = next(scale for scale in (4, 2, 1) if span * scale <= 256)
        left, right, tiles = _edge_tiles(band, texels_per_unit)
        glyphs = {}
        for side, tile in tiles.items():
            name = 'strip%d_%s' % (index, side)
            canvas, units = padded(tile, band['top'], texels_per_unit)
            font.texture(name, canvas)
            glyphs[side] = font.glyph(name, units, band['top'])
        block, reach = _block(font, height, band['top'])
        block_glyph = font.glyph(block, _span(height, band['top']), band['top'])
        layout.append({
            'top': band['top'], 'order': band['order'], 'direction': band['direction'],
            'a': [[block_glyph, left - reach], [glyphs['a'], left]],
            'b': [[glyphs['b'], left], [block_glyph, right]],
            'seam': [[glyphs['seam'], left]],
            'edge': font.glyph(_edge_bar(font, height, band['top']), _span(height, band['top']), band['top']),
            'left': left - reach, 'right': right + reach,
        })
    return layout


def covers(font):
    """Full-screen rectangles: an opaque one tinted per stage and three fading white flashes."""
    def cover(name, alpha):
        font.texture(name, Image.new('RGBA', (4, 2), (255, 255, 255, alpha)))
        return [font.glyph(name, g.COVER_HEIGHT, g.COVER_TOP), -g.COVER_HEIGHT]
    return {'solid': cover('cover', 255),
            'flash': [cover('flash_%d' % index, alpha) for index, alpha in enumerate(FLASH_ALPHAS)]}


def bars(font, height, top, widths, strip=None):
    """Bars of each width in `widths`, `height` units tall, for rules and boxes that grow."""
    pieces = {}
    for width in widths:
        canvas, units = padded(Image.new('RGBA', (width, height), (255, 255, 255, 255)), top, 1)
        texture = 'bar_%dx%d_%d' % (width, height, units)
        font.texture(texture, canvas)
        pieces[str(width)] = font.glyph(texture, units, top)
    return {'pieces': pieces} if strip is None else {'pieces': pieces, 'strip': strip}
