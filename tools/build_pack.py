#!/usr/bin/env python3
"""Builds mcduelspack.zip as small as it can be without changing what the client shows.

- PNGs are re-encoded losslessly with oxipng (libdeflate level 12, best filters, metadata chunks
  stripped). Every pixel keeps its exact alpha, and every pixel that is not fully transparent
  keeps its exact colour; only the hidden colour of alpha-0 pixels may change. That matters for
  the cutscene font, whose glyph widths are pinned by single alpha-1 pixels. The script decodes
  each result and fails the build if any visible pixel differs.
- JSON and .mcmeta files are minified (no whitespace, private-use glyphs written as UTF-8
  instead of \\uXXXX escapes). Duplicate keys fail the build, since minifying would drop them.
- Only files the client reads go in the zip, with no folder entries, sorted, and with a fixed
  timestamp so the same sources always give the same SHA-1. Each entry is zopfli-deflated, or
  stored when that is smaller (the .ogg music).

The sources in the repo stay readable; only the zip is optimized.
Needs: pip install pyoxipng zopfli pillow
Usage: tools/build_pack.py [output.zip]   (default: mcduelspack.zip in the repo root)
"""
import io
import json
import os
import struct
import sys
import zlib

import oxipng
import zopfli.zopfli
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOP_LEVEL = ['pack.mcmeta', 'pack.png']
CLIENT_FILES = {'.png', '.json', '.mcmeta', '.ogg', '.fsh', '.vsh', '.glsl', '.txt', '.properties'}
JSON_FILES = {'.json', '.mcmeta'}
ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def pack_files():
    files = [name for name in TOP_LEVEL if os.path.isfile(os.path.join(ROOT, name))]
    for folder, dirs, names in os.walk(os.path.join(ROOT, 'assets')):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        for name in names:
            if name.startswith('.') or os.path.splitext(name)[1].lower() not in CLIENT_FILES:
                continue
            files.append(os.path.relpath(os.path.join(folder, name), ROOT).replace(os.sep, '/'))
    return sorted(files)


def no_duplicates(pairs):
    keys = [key for key, _ in pairs]
    duplicates = {key for key in keys if keys.count(key) > 1}
    if duplicates:
        raise ValueError(f'duplicate keys {sorted(duplicates)}')
    return dict(pairs)


def minify_json(data, name):
    try:
        parsed = json.loads(data.decode('utf-8-sig'), object_pairs_hook=no_duplicates)
    except ValueError as error:
        sys.exit(f'{name}: {error}')
    return json.dumps(parsed, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def visible_pixels(data):
    image = Image.open(io.BytesIO(data)).convert('RGBA')
    return image.size, [p if p[3] else (0, 0, 0, 0) for p in image.get_flattened_data()]


def optimize_png(data, name):
    optimized = oxipng.optimize_from_memory(
        data,
        level=6,
        strip=oxipng.StripChunks.all(),
        optimize_alpha=True,
        grayscale_reduction=False,
        deflate=oxipng.Deflaters.libdeflater(12),
    )
    if visible_pixels(optimized) != visible_pixels(data):
        sys.exit(f'{name}: optimized PNG does not match the original')
    return optimized if len(optimized) < len(data) else data


def deflate(data):
    # zopfli writes a zlib stream: drop the 2-byte header and the 4-byte Adler-32 trailer.
    return zopfli.zopfli.compress(data, numiterations=15)[2:-4]


def write_zip(path, entries):
    dos_time = (ZIP_TIME[3] << 11) | (ZIP_TIME[4] << 5) | (ZIP_TIME[5] // 2)
    dos_date = ((ZIP_TIME[0] - 1980) << 9) | (ZIP_TIME[1] << 5) | ZIP_TIME[2]
    central = bytearray()
    with open(path, 'wb') as out:
        for name, data in entries:
            packed = deflate(data)
            method = 8 if len(packed) < len(data) else 0
            body = packed if method else data
            crc = zlib.crc32(data)
            encoded = name.encode('utf-8')
            offset = out.tell()
            fields = struct.pack('<HHHHHIIIHH', 20, 0x0800, method, dos_time, dos_date,
                                 crc, len(body), len(data), len(encoded), 0)
            out.write(b'PK\x03\x04' + fields + encoded + body)
            central += (b'PK\x01\x02' + struct.pack('<H', 20) + fields
                        + struct.pack('<HHHII', 0, 0, 0, 0, offset) + encoded)
        start = out.tell()
        out.write(central)
        out.write(b'PK\x05\x06' + struct.pack('<HHHHIIH', 0, 0, len(entries), len(entries),
                                               len(central), start, 0))


def main():
    output = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'mcduelspack.zip'))
    entries = []
    before = 0
    for name in pack_files():
        with open(os.path.join(ROOT, name), 'rb') as source:
            data = source.read()
        before += len(data)
        extension = os.path.splitext(name)[1].lower()
        if extension in JSON_FILES:
            data = minify_json(data, name)
        elif extension == '.png':
            data = optimize_png(data, name)
        entries.append((name, data))
    write_zip(output, entries)
    after = sum(len(data) for _, data in entries)
    print(f'{len(entries)} files, {before:,} -> {after:,} bytes before zipping, '
          f'{output} is {os.path.getsize(output):,} bytes')


if __name__ == '__main__':
    main()
