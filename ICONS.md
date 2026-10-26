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
