import { createHash } from 'node:crypto';
import { lstat, readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { create } from 'fontkit';
import { privateFonts } from './private-font-manifest.mjs';

function fail(id, reason) {
  throw new Error(`ARE_FONT_INVALID: ${id}: ${reason}`);
}

// Some original webfonts retain their valid Macintosh full-name record but have
// malformed Windows names. Read only identity records; never expose other metadata.
export function fullNamesFromTable(bytes) {
  const names = [];
  const count = bytes.readUInt16BE(2);
  const strings = bytes.readUInt16BE(4);
  for (let index = 0; index < count; index++) {
    const start = 6 + index * 12;
    const platform = bytes.readUInt16BE(start);
    const nameId = bytes.readUInt16BE(start + 6);
    const length = bytes.readUInt16BE(start + 8);
    const offset = strings + bytes.readUInt16BE(start + 10);
    if (offset + length > bytes.length) throw new Error('Invalid name table');
    if (nameId !== 4) continue;
    const value = bytes.subarray(offset, offset + length);
    if (platform === 1) names.push(value.toString('latin1'));
    else if (platform === 0 || platform === 3) names.push(new TextDecoder('utf-16be', { fatal: true }).decode(value));
  }
  return names;
}

export function validateFontBytes(bytes, spec) {
  if (createHash('sha256').update(bytes).digest('hex') !== spec.sha256) fail(spec.id, 'checksum mismatch');
  try {
    const font = create(bytes);
    let familyMatches = font.familyName === spec.family;
    if (!familyMatches && spec.legacyFullName) {
      // Pinned fontkit adapter: familyName above decompresses WOFF2 first.
      const stream = font._getTableStream('name');
      const table = Buffer.from(stream.readBuffer(font.directory.tables.name.length));
      familyMatches = fullNamesFromTable(table).includes(spec.legacyFullName);
    }
    if (!familyMatches) fail(spec.id, 'family mismatch');
    if (spec.range) {
      const axis = font.variationAxes.wght;
      if (!axis || axis.min !== spec.range[0] || axis.max !== spec.range[1]) fail(spec.id, 'weight range mismatch');
    } else if (font['OS/2'].usWeightClass !== spec.weight || (font.italicAngle !== 0) !== spec.italic) {
      fail(spec.id, 'weight or style mismatch');
    }
    if ([...spec.glyphs].some((char) => !font.hasGlyphForCodePoint(char.codePointAt(0)))) fail(spec.id, 'required glyph missing');
    return { id: spec.id, family: spec.family, weight: spec.range ?? spec.weight };
  } catch (error) {
    if (error instanceof Error && error.message.startsWith('ARE_FONT_INVALID:')) throw error;
    fail(spec.id, 'font decoding or metadata validation failed');
  }
}

export async function readPrivateFont(id, directory = process.env.ARE_PRIVATE_FONT_DIR ?? resolve(process.cwd(), '.private-fonts')) {
  const spec = privateFonts.find((font) => font.id === id);
  if (!spec) fail('unknown', 'asset is not allowlisted');
  let bytes;
  try {
    const path = resolve(directory, spec.id);
    const stat = await lstat(path);
    if (!stat.isFile() || stat.isSymbolicLink() || stat.size > 2 * 1024 * 1024) fail(id, 'invalid asset file');
    bytes = await readFile(path);
  } catch {
    fail(id, 'required private font unavailable');
  }
  validateFontBytes(bytes, spec);
  return bytes;
}

export async function validatePrivateFonts({ mode = 'runtime', env = process.env, directory } = {}) {
  if (mode === 'build' && env.ARE_FONT_BUILD_MODE === 'code-only' && env.CI === 'true') {
    return { status: 'code-only', fonts: 0 };
  }
  if (env.ARE_FONT_BUILD_MODE && env.ARE_FONT_BUILD_MODE !== 'actual') {
    throw new Error('ARE_FONT_MODE: code-only is permitted only for explicitly labelled CI builds, never runtime.');
  }
  for (const font of privateFonts) await readPrivateFont(font.id, directory ?? env.ARE_PRIVATE_FONT_DIR);
  return { status: 'actual', fonts: privateFonts.length };
}
