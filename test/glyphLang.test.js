const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const packRoot = path.resolve(__dirname, '..');
const providers = JSON.parse(fs.readFileSync(path.join(packRoot, 'assets/minecraft/font/default.json'), 'utf8')).providers;
const lang = JSON.parse(fs.readFileSync(path.join(packRoot, 'assets/mcduels/lang/en_us.json'), 'utf8'));

test('translates every default-font glyph key back to its glyph', () => {
  const codes = providers.flatMap(provider => provider.chars || []).flatMap(row => [...row])
    .map(character => character.codePointAt(0)).filter(code => code >= 0xE000 && code <= 0xF8FF);
  assert.ok(codes.length > 0);
  for (const code of codes) {
    const key = 'mcduels.glyph.' + code.toString(16).padStart(4, '0');
    assert.equal(lang[key], String.fromCodePoint(code), key);
    assert.equal(lang['mcduels.nopack.' + code.toString(16).padStart(4, '0')], '', key);
  }
  assert.equal(Object.keys(lang).length, 2 * new Set(codes).size);
});

test('covers the logo and rank glyphs the plugins send', () => {
  for (const key of ['mcduels.glyph.e880', 'mcduels.glyph.e800', 'mcduels.glyph.e831', 'mcduels.glyph.e900']) {
    assert.ok(lang[key], key);
  }
});
