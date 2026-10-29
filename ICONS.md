# Icons

Every PNG in `assets/mcduels/textures/icons/` is a glyph in the default font, so it shows
anywhere text does: chat, scoreboards, tab, titles, holograms and item names.

In the MCDuels plugins write `<icon:trophy>` or `:trophy:` in messages.yml, scoreboards.yml
or the chat formats. The full name list is in [icons.yml](icons.yml).

To add an icon, drop a 16x16 PNG into the icons folder and run:

```
python3 tools/generate_icons.py
```

It keeps every existing icon on its code point and gives new ones the next free one, then
rewrites the font and `icons.yml`. Copy the new `icons:` entries into the plugins'
`icons.yml` (or delete that file so it is regenerated) and run their reload command.

`tools/src/draw_new_icons.py` draws the MCDuels-made icons (kit items, ping bars, status
dots, arrows) from text masks; the rest come from the CushionMC menu icon set.

## Logo

`assets/mcduels/textures/font/logo.png` is the MCDuels title art as one large glyph,
`<icon:logo>` (U+E880, 20 px tall). The lobby sidebar uses it as its title. It is not in the
icons folder, so `generate_icons.py` leaves its font provider alone and only adds it to `icons.yml`.

## Players without the pack

`assets/mcduels/lang/en_us.json` gives every default-font glyph two translation keys:
`mcduels.glyph.<hex code point>` is the glyph (for example `mcduels.glyph.e90f` for `check`)
and `mcduels.nopack.<hex>` is empty. The plugins send each glyph as both keys, with the text
fallback on the second, so a player who declines the pack (or whose download fails) sees the
fallback text, or nothing, instead of empty boxes. The fallbacks
live in the plugins' `icons.yml` under `fallbacks:`.

`tools/generate_icons.py` rewrites the language file too; after hand-editing
`default.json`, run `python3 tools/generate_lang.py`.
