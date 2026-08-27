import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createRequire } from 'node:module';
import test from 'node:test';
import { create } from 'fontkit';
import { fontVersion, privateFonts } from '../lib/private-font-manifest.mjs';
import { fullNamesFromTable, readPrivateFont, validateFontBytes, validatePrivateFonts } from '../lib/private-fonts.mjs';

// CI exercises real decoding against an OFL asset, never the commercial files.
const require = createRequire(import.meta.url);
const bytes = await readFile(require.resolve('@fontsource/ibm-plex-sans-arabic/files/ibm-plex-sans-arabic-arabic-400-normal.woff2'));
const font = create(bytes);
const spec = { id: 'open-source-fixture', family: font.familyName, weight: 400, italic: false, glyphs: 'العربية', sha256: createHash('sha256').update(bytes).digest('hex') };

test('valid OFL fixture passes checksum, identity, style and Arabic glyph checks', () => {
  assert.equal(validateFontBytes(bytes, spec).weight, 400);
});
test('modified bytes, family, weight, style, variable axis and missing glyph fail closed', () => {
  for (const change of [{ sha256: '0'.repeat(64) }, { family: 'wrong' }, { weight: 700 }, { italic: true }, { range: [100, 900] }, { glyphs: '\u{10FFFF}' }]) {
    assert.throws(() => validateFontBytes(bytes, { ...spec, ...change }), /ARE_FONT_INVALID/);
  }
  const corrupt = Buffer.from('not a font');
  assert.throws(() => validateFontBytes(corrupt, { ...spec, sha256: createHash('sha256').update(corrupt).digest('hex') }), /decoding/);
});
test('legacy identity exception still requires the exact pinned checksum', () => {
  const italic = privateFonts.find(item => item.legacyFullName);
  assert.throws(() => validateFontBytes(bytes, italic), /checksum mismatch/);
  const value = Buffer.from('Hennigar Italic Webfont');
  const table = Buffer.alloc(18 + value.length);
  table.writeUInt16BE(1, 2); table.writeUInt16BE(18, 4);
  table.writeUInt16BE(1, 6); table.writeUInt16BE(4, 12); table.writeUInt16BE(value.length, 14);
  value.copy(table, 18);
  assert.deepEqual(fullNamesFromTable(table), ['Hennigar Italic Webfont']);
  table.writeUInt16BE(65535, 16);
  assert.throws(() => fullNamesFromTable(table));
});
test('code-only requires explicit CI build and cannot start a runtime', async () => {
  assert.deepEqual(await validatePrivateFonts({ mode: 'build', env: { CI: 'true', ARE_FONT_BUILD_MODE: 'code-only' } }), { status: 'code-only', fonts: 0 });
  for (const options of [{ mode: 'runtime', env: { CI: 'true', ARE_FONT_BUILD_MODE: 'code-only' } }, { mode: 'build', env: { ARE_FONT_BUILD_MODE: 'code-only' } }]) {
    await assert.rejects(validatePrivateFonts(options), /never runtime/);
  }
});
test('missing or mismatched private files fail without leaking a private location', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'are-font-test-'));
  try {
    await assert.rejects(validatePrivateFonts({ env: {}, directory }), error => error.message.includes('unavailable') && !error.message.includes(directory));
    await writeFile(join(directory, privateFonts[0].id), bytes);
    await assert.rejects(readPrivateFont(privateFonts[0].id, directory), /checksum mismatch/);
    await assert.rejects(readPrivateFont('../secret', directory), /not allowlisted/);
  } finally { await rm(directory, { recursive: true, force: true }); }
});
test('runtime CSS exposes only versioned allowlisted assets with actual weight ranges', async () => {
  const css = await readFile(new URL('../app/private-fonts.css', import.meta.url), 'utf8');
  const urls = [...css.matchAll(/url\("\/font-assets\/([^/]+)\/([^"/]+)"\)/g)];
  assert.equal(urls.length, privateFonts.length);
  assert.deepEqual(urls.map(match => match[2]).sort(), privateFonts.map(item => item.id).sort());
  assert.ok(urls.every(match => match[1] === fontVersion));
  assert.ok(css.includes('font-weight: 100 800;'));
  assert.ok(css.includes('font-weight: 100 856;'));
  assert.ok(!css.includes('https://'));
});
test('direct runtime instrumentation exits on missing fonts rather than staying half-ready', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'are-font-startup-'));
  try {
    const result = spawnSync(process.execPath, ['--input-type=module', '-e', "import { register } from './instrumentation.ts'; await register();"], {
      cwd: new URL('../', import.meta.url), encoding: 'utf8', timeout: 15000,
      env: { ...process.env, NEXT_RUNTIME: 'nodejs', NEXT_PHASE: 'phase-production-server', ARE_FONT_BUILD_MODE: 'actual', ARE_PRIVATE_FONT_DIR: directory },
    });
    assert.equal(result.status, 1);
    assert.match(result.stderr, /ARE_FONT_INVALID: h1-regular.woff2: required private font unavailable/);
    assert.ok(!result.stderr.includes(directory));
  } finally { await rm(directory, { recursive: true, force: true }); }
});

test('approved Arabic family covers mixed-script copy at every loaded weight', async () => {
  const sample = 'العربية الإمارات أسئلة خياراتك ونظّم ALIYAS Real Estate EN 0123456789 + / : . , — · © ()';
  for (const weight of [400, 500, 600, 700]) {
    const faces = await Promise.all(['arabic', 'latin'].map(async subset => {
      const face = create(await readFile(require.resolve(`@fontsource/ibm-plex-sans-arabic/files/ibm-plex-sans-arabic-${subset}-${weight}-normal.woff2`)));
      const expectedFamily = weight === 500 ? 'IBM Plex Sans Arabic Medium' : weight === 600 ? 'IBM Plex Sans Arabic SemiBold' : 'IBM Plex Sans Arabic';
      assert.equal(face.familyName, expectedFamily);
      assert.equal(face['OS/2'].usWeightClass, weight);
      return face;
    }));
    for (const character of sample) {
      assert.ok(faces.some(face => face.hasGlyphForCodePoint(character.codePointAt(0))), `Missing glyph ${character} at ${weight}`);
    }
  }
});

test('same-family Latin subset precedes system fallback and language labels retain Arabic typography', async () => {
  const [source, css] = await Promise.all([
    readFile(new URL('../app/fonts.ts', import.meta.url), 'utf8'),
    readFile(new URL('../app/globals.css', import.meta.url), 'utf8'),
  ]);
  assert.match(source, /const ibmPlexSansArabicLatin = localFont\(\{[\s\S]*?adjustFontFallback: false/);
  assert.match(source, /publicFontVariables = [^;]*ibmPlexSansArabicLatin\.variable/);
  for (const weight of [400, 500, 600, 700]) {
    assert.ok(source.includes(`ibm-plex-sans-arabic-latin-${weight}-normal.woff2`));
  }
  assert.match(css, /--are-font-arabic: var\(--font-arabic-latin\), var\(--font-arabic\)/);
  assert.match(css, /html\[lang="en"\] body\.are-site a\[hreflang="ar"\] \{\s*font-family: var\(--are-font-arabic\);\s*letter-spacing: normal;/);
});

test('shared heading roles and private font gates remain independent of route content', async () => {
  const css = await readFile(new URL('../app/globals.css', import.meta.url), 'utf8');
  assert.match(css, /html\[lang="en"\] body\.are-site h1 \{\s*font-family: var\(--are-font-h1\);\s*font-style: normal;\s*font-weight: 400;/);
  assert.match(css, /html\[lang="en"\] body\.are-site h2,\s*html\[lang="en"\] body\.are-site h3 \{\s*font-family: var\(--are-font-display\);\s*font-weight: 600;/);
  assert.match(css, /html\[lang="ar"\] body\.are-site h1 \{\s*font-family: var\(--are-font-arabic-h1\);\s*font-weight: 700;/);
  assert.match(css, /--are-heading-tracking: normal;/);
  assert.match(css, /html\[lang="en"\] body\.are-site h1 \{[^}]*letter-spacing: var\(--are-heading-tracking\);/);
  assert.match(css, /html\[lang="en"\] body\.are-site :is\(h2, h3\):not\(:where\(\.premium-home \*\)\) \{\s*letter-spacing: var\(--are-heading-tracking\);/);
  const layout = await readFile(new URL('../app/(localized)/[locale]/layout.tsx', import.meta.url), 'utf8');
  assert.match(layout, /<html className=\{publicFontVariables\} lang=\{locale\}/);
  assert.match(layout, /href="\/font-assets\/v1\/h1-regular\.woff2" as="font"/);
  assert.match(layout, /href="\/font-assets\/v1\/arabic-h1\.woff2" as="font"/);
});
