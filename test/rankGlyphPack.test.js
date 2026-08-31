const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const packRoot = path.resolve(__dirname, '..');
const fontPath = path.join(packRoot, 'assets/minecraft/font/default.json');
const ranksPath = path.join(packRoot, 'assets/minecraft/textures/ranks');
const providers = JSON.parse(fs.readFileSync(fontPath, 'utf8')).providers;

test('maps fifty unique consecutive glyphs from U+E800 through U+E831', () => {
  const codePoints = providers.flatMap(provider => provider.chars)
    .map(character => character.codePointAt(0));
  const expectedCodePoints = Array.from({ length: 50 }, (_, index) => 0xE800 + index);

  assert.equal(providers.length, 50);
  assert.equal(new Set(codePoints).size, 50);
  assert.deepEqual(codePoints, expectedCodePoints);
});

test('uses one eight-pixel bitmap and one distinct file per glyph', () => {
  const referencedFiles = providers.map(provider => provider.file);

  for (const provider of providers) {
    assert.equal(provider.type, 'bitmap');
    assert.equal(provider.ascent, 8);
    assert.equal(provider.height, 8);
    assert.equal(provider.chars.length, 1);
    assert.match(provider.file, /^minecraft:ranks\/[a-z_]+\.png$/);
  }
  assert.equal(new Set(referencedFiles).size, 50);
});

test('contains every referenced PNG and no unreferenced rank PNG', () => {
  const referencedNames = providers.map(provider => path.basename(provider.file)).sort();
  const actualNames = fs.readdirSync(ranksPath).filter(name => name.endsWith('.png')).sort();

  assert.deepEqual(actualNames, referencedNames);
  for (const fileName of referencedNames) {
    const image = fs.readFileSync(path.join(ranksPath, fileName));
    assert.equal(image.subarray(0, 8).toString('hex'), '89504e470d0a1a0a', fileName);
  }
});
