import { validatePrivateFonts } from '../lib/private-fonts.mjs';
try {
  const result = await validatePrivateFonts({ mode: process.argv.includes('--build') ? 'build' : 'runtime' });
  console.log(result.status === 'actual'
    ? `ARE fonts: ${result.fonts} original assets verified (checksum, family, weight, glyphs).`
    : 'ARE CI CODE-ONLY: no commercial fonts accessed. Final typography is NOT verified.');
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
