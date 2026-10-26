const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const packRoot = path.resolve(__dirname, '..');
const fontPath = path.join(packRoot, 'assets/minecraft/font/default.json');
const iconsPath = path.join(packRoot, 'assets/mcduels/textures/icons');
const registry = JSON.parse(fs.readFileSync(path.join(packRoot, 'tools/icons.json'), 'utf8'));
const allProviders = JSON.parse(fs.readFileSync(fontPath, 'utf8')).providers;
const icons = allProviders.filter(provider => provider.file.startsWith('mcduels:icons/'));

test('maps every icon PNG to exactly one glyph from the registry', () => {
  const pngs = fs.readdirSync(iconsPath).filter(name => name.endsWith('.png')).map(name => name.slice(0, -4)).sort();
  const mapped = icons.map(provider => provider.file.slice('mcduels:icons/'.length, -4)).sort();

  assert.deepEqual(mapped, pngs);
  assert.deepEqual(Object.keys(registry).sort(), pngs);
  for (const provider of icons) {
    const name = provider.file.slice('mcduels:icons/'.length, -4);
    assert.equal(provider.chars.length, 1);
    assert.equal(provider.chars[0].codePointAt(0), parseInt(registry[name], 16), name);
  }
});

test('keeps icon glyphs in the private use area without touching rank glyphs', () => {
  const all = allProviders.flatMap(provider => provider.chars).map(character => character.codePointAt(0));
  assert.equal(new Set(all).size, all.length);
  for (const provider of icons) {
    const code = provider.chars[0].codePointAt(0);
    assert.ok(code >= 0xE900 && code <= 0xF8FF, provider.file);
    assert.equal(provider.height, 8);
    assert.equal(provider.ascent, 7);
  }
});

test('ships the icons.yml list the plugins read', () => {
  const exported = fs.readFileSync(path.join(packRoot, 'icons.yml'), 'utf8');
  for (const [name, code] of Object.entries(registry)) {
    assert.match(exported, new RegExp(`^  ${name}: "\\\\u${code}"$`, 'm'), name);
  }
});

test('ships the lobby scoreboard logo as a large glyph exported as <icon:logo>', () => {
  const logo = allProviders.find(provider => provider.file === 'mcduels:font/logo.png');
  assert.ok(logo, 'logo provider');
  assert.equal(logo.chars[0].codePointAt(0), 0xE880);
  assert.ok(logo.ascent <= logo.height);
  assert.ok(fs.existsSync(path.join(packRoot, 'assets/mcduels/textures/font/logo.png')));
  const exported = fs.readFileSync(path.join(packRoot, 'icons.yml'), 'utf8');
  assert.match(exported, /^  logo: "\\uE880"$/m);
});
