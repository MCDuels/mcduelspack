#!/usr/bin/env python3
"""Writes assets/mcduels/lang/en_us.json: one translation key per glyph of the default font.

The MCDuels plugins send every pack glyph as two translatable components:
mcduels.glyph.<code point in lower-case hex> (falls back to nothing) and, for icons with a
text fallback, mcduels.nopack.<hex> (falls back to that text). This file resolves the first
to the glyph and the second to nothing. A client without the pack has neither key and shows
the fallbacks, so players who decline the pack see readable text instead of empty boxes.
Minecraft always loads en_us under the selected language, so this one file covers all.
Run it after any change to assets/minecraft/font/default.json (generate_icons.py does).
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(ROOT, 'assets', 'minecraft', 'font', 'default.json')
LANG = os.path.join(ROOT, 'assets', 'mcduels', 'lang', 'en_us.json')
PRIVATE_USE = range(0xE000, 0xF900)


def glyphs(font):
    codes = set()
    for provider in font['providers']:
        for row in provider.get('chars', []):
            codes.update(ord(c) for c in row if ord(c) in PRIVATE_USE)
    return sorted(codes)


def main():
    with open(FONT, encoding='utf-8') as source:
        codes = glyphs(json.load(source))
    os.makedirs(os.path.dirname(LANG), exist_ok=True)
    with open(LANG, 'w', encoding='utf-8') as target:
        target.write('{\n')
        entries = ['  "mcduels.glyph.%04x": "\\u%04X"' % (code, code) for code in codes]
        entries += ['  "mcduels.nopack.%04x": ""' % code for code in codes]
        target.write(',\n'.join(entries))
        target.write('\n}\n')
    print('%d glyph translations written' % len(codes))


if __name__ == '__main__':
    main()
