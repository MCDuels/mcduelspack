const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const packRoot = path.resolve(__dirname, '..');
const font = JSON.parse(fs.readFileSync(path.join(packRoot, 'assets/mcduels/font/cutscene.json'), 'utf8'));
const layout = JSON.parse(fs.readFileSync(path.join(packRoot, 'tools/cutscene-layout.json'), 'utf8'));
const bitmaps = font.providers.filter(provider => provider.type === 'bitmap');
const spaceProvider = font.providers.find(provider => provider.type === 'space');

function pngSize(file) {
  const bytes = fs.readFileSync(file);
  return { width: bytes.readUInt32BE(16), height: bytes.readUInt32BE(20) };
}

test('keeps every cutscene glyph loadable by the client', () => {
  for (const provider of bitmaps) {
    const file = path.join(packRoot, 'assets/mcduels/textures', provider.file.slice('mcduels:'.length));
    assert.ok(fs.existsSync(file), provider.file);
    const { width, height } = pngSize(file);
    assert.ok(width <= 256 && height <= 256, `${provider.file} is ${width}x${height}`);
    assert.ok(provider.ascent <= provider.height, `${provider.file} ascent ${provider.ascent} > ${provider.height}`);
    assert.ok(Number.isInteger(provider.ascent) && Number.isInteger(provider.height), provider.file);
  }
});

test('gives every glyph its own code point', () => {
  const chars = bitmaps.flatMap(provider => provider.chars).concat(Object.keys(spaceProvider.advances));
  assert.equal(new Set(chars).size, chars.length);
});

test('only places glyphs the font defines', () => {
  const defined = new Set(bitmaps.flatMap(provider => provider.chars));
  const placed = [
    ...layout.panel_a, ...layout.panel_b, ...layout.vs_frames.flat(), ...layout.vs_a, ...layout.vs_b,
    ...Object.values(layout.heads).flatMap(head => [...head.frame, ...head.rows.map(row => [row, 0])]),
    ...Object.values(layout.names.chars).flatMap(chars => Object.values(chars).map(char => [char, 0])),
  ];
  for (const [char] of placed) {
    assert.ok(defined.has(char), `U+${char.codePointAt(0).toString(16)}`);
    assert.ok(char in layout.advances, `no advance for U+${char.codePointAt(0).toString(16)}`);
  }
  assert.deepEqual(layout.spaces, spaceProvider.advances);
});
