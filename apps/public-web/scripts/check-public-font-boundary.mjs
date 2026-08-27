import { execFileSync } from 'node:child_process';

// Audit the Git index, not ignored owner assets. Never print restricted filenames.
const paths = execFileSync('git', ['ls-files', '-z'], { encoding: 'utf8' }).split('\0').filter(Boolean);
const restricted = paths.filter(path => /(^|\/)\.private-fonts\//i.test(path) || /^docs\/licenses\/fonts\//i.test(path) || /\.(woff2?|ttf|otf)$/i.test(path));
if (restricted.length) {
  console.error(`Public Git boundary failed: ${restricted.length} private font/licence paths are tracked.`);
  process.exitCode = 1;
} else {
  console.log('Public Git font boundary passed: no tracked font binaries or private purchase documents.');
}
