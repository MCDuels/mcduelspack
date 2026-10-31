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

function placedGlyphs(node, found = []) {
  if (typeof node === 'string') {
    const code = node.codePointAt(0);
    if (node.length === 1 && code >= 0xe000 && code <= 0xf8ff) found.push(node);
  } else if (Array.isArray(node)) {
    node.forEach(child => placedGlyphs(child, found));
  } else if (node && typeof node === 'object') {
    Object.values(node).forEach(child => placedGlyphs(child, found));
  }
  return found;
}

test('only places glyphs the font defines', () => {
  const defined = new Set(bitmaps.flatMap(provider => provider.chars));
  const { spaces, advances, ...placements } = layout;
  const placed = placedGlyphs(placements);
  assert.ok(placed.length > 0);
  for (const char of placed) {
    assert.ok(defined.has(char), `U+${char.codePointAt(0).toString(16)}`);
    assert.ok(char in advances, `no advance for U+${char.codePointAt(0).toString(16)}`);
  }
  assert.deepEqual(spaces, spaceProvider.advances);
});

test('cuts the card into strips that cover the screen top to bottom without gaps', () => {
  const tops = layout.strips.map(strip => strip.top);
  assert.deepEqual(tops, [...tops].sort((a, b) => a - b));
  for (const strip of layout.strips) {
    assert.ok(strip.direction === 1 || strip.direction === -1);
    assert.ok(strip.left < -120 && strip.right > 120, `strip at ${strip.top} is too narrow`);
  }
});

function provider(char) {
  return bitmaps.find(entry => entry.chars.includes(char));
}

test('closes the letterbox one unit at a time, each bar reaching the screen edge', () => {
  const { steps, left, piece } = layout.cinema.letterbox;
  assert.ok(steps.length > 1);
  steps.forEach((step, index) => {
    if (index > 0) assert.equal(step.edge, steps[index - 1].edge - 1);
    const top = provider(step.top);
    const bottom = provider(step.bottom);
    assert.equal(-3 - top.ascent, -136, 'top bar starts at the top of the cover');
    assert.equal(-3 - bottom.ascent, step.edge, 'bottom bar starts at the edge');
    assert.equal(-3 - bottom.ascent + bottom.height, 136, 'bottom bar reaches the bottom of the cover');
    assert.equal(layout.advances[step.top], piece + 1);
  });
  assert.ok(left <= -160 && left + 2 * piece >= 160, 'two pieces span the widest screen');
});

test('fades the cover in even steps, lightest first', () => {
  const fade = layout.cinema.fade;
  assert.equal(fade.length, 15);
  fade.forEach(([char, x], index) => {
    assert.equal(x, layout.cover.solid[1]);
    assert.ok(provider(char).file.endsWith(`fade_${String(index + 1).padStart(2, '0')}.png`));
  });
});
