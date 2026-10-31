#!/usr/bin/env python3
"""Draws the pre-duel VS cutscene glyphs and writes the font plus the layout the backend reads.

The cutscene is one title component re-sent every tick; tools/cutscene/geometry.py explains the
coordinates. Needs Pillow; the fonts it draws with live in tools/fonts.

Outputs:
  assets/mcduels/textures/cutscene/*.png    glyph bitmaps
  assets/mcduels/font/cutscene.json         the mcduels:cutscene font
  tools/cutscene-layout.json                where each piece goes; the backend ships a copy as
                                            src/main/resources/cutscene/layout.json
"""
import json
import os

from cutscene import geometry as g
from cutscene.card import kit_card, mono_row, names, tag
from cutscene.cinema import cinema
from cutscene.faces import faces
from cutscene.font_builder import FONT_KEY, FontBuilder
from cutscene.impact import impact
from cutscene.panels import covers, strips
from cutscene.type_sets import anton
from cutscene.vs import vs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXTURES = os.path.join(ROOT, 'assets', 'mcduels', 'textures', 'cutscene')
FONT_FILE = os.path.join(ROOT, 'assets', 'mcduels', 'font', 'cutscene.json')
LAYOUT_FILE = os.path.join(ROOT, 'tools', 'cutscene-layout.json')


def build(font):
    panel_strips = strips(font)
    return {
        'font': FONT_KEY,
        'cover': covers(font),
        'strips': panel_strips,
        'seam_wipe': [g.STRIPS_TOP, g.STRIPS_TOP + g.CENTRE_STRIPS * g.STRIP_HEIGHT],
        'travel': max(max(-strip['left'], strip['right']) for strip in panel_strips) + g.VISIBLE_HALF_WIDTH,
        'kit': kit_card(font),
        'faces': faces(font),
        'names': names(font),
        'rank': mono_row(font, 500, g.MONO_CAP, g.STATS_BASELINE, g.TRACKING['stats']),
        'impact': impact(font),
        'vs': vs(font, anton()),
        'tag': tag(font),
        'ranked': mono_row(font, 700, g.MONO_CAP, g.RANKED_BASELINE, g.TRACKING['ranked']),
        'footer': mono_row(font, 700, g.FOOTER_CAP, g.FOOTER_BASELINE, g.TRACKING['footer']),
        # Drawn last so the card's code points stay where they were.
        'cinema': cinema(font),
    }


def main():
    os.makedirs(TEXTURES, exist_ok=True)
    os.makedirs(os.path.dirname(FONT_FILE), exist_ok=True)
    for name in os.listdir(TEXTURES):
        os.remove(os.path.join(TEXTURES, name))
    font = FontBuilder(TEXTURES)
    font.add_spaces()
    layout = build(font)
    layout['spaces'] = font.spaces
    layout['advances'] = font.advances
    with open(FONT_FILE, 'w', encoding='utf-8') as out:
        json.dump(font.provider_json(), out, indent=2)
        out.write('\n')
    with open(LAYOUT_FILE, 'w', encoding='utf-8') as out:
        json.dump(layout, out, indent=1)
        out.write('\n')


if __name__ == '__main__':
    main()
