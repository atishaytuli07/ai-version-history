#!/usr/bin/env node
// ai-versions restore: makes a NEW commit whose files exactly match an old
// version, then pushes it. Nothing is deleted from history. The versioning
// script then records it as "Restored to vX.Y.Z".
// Kit files (.github/, .ai-versions/, the version button, the list) are kept as they are now.
//
// Env: VERSION (e.g. v1.2.0 or 1.2.0), NOTE (optional), BRANCH (default: main),
//      GITHUB_OUTPUT (receives before= / after= for the next step).

import { execFileSync } from 'node:child_process';
import { appendFileSync } from 'node:fs';

const LEDGER = 'public/ai-versions.json';
const REQUEST = '.ai-versions/restore.json';
// Kit files (workflows, scripts, the version button, the list) stay as they are now.
const isKitFile = (f) => f === LEDGER || f.startsWith('.github/') || f.startsWith('.ai-versions/')
  || /(^|\/)VersionPill\.tsx$/.test(f);
const git = (...args) =>
  execFileSync('git', args, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim();
const tryGit = (...args) => { try { return git(...args); } catch { return null; } };
const fail = (msg) => { console.error(msg); process.exit(1); };

let version = String(process.env.VERSION || '').trim();
if (!version) fail('Give a version, for example v1.2.0');
if (!version.startsWith('v')) version = `v${version}`;
if (!/^v\d+\.\d+\.\d+$/.test(version)) fail(`"${version}" is not a version like v1.2.0`);
if (tryGit('rev-parse', '-q', '--verify', `refs/tags/${version}`) === null) {
  fail(`${version} does not exist. Open the version pill or the Releases page to see all versions.`);
}

const branch = process.env.BRANCH || 'main';
const before = git('rev-parse', 'HEAD');
const out = (k, v) => process.env.GITHUB_OUTPUT && appendFileSync(process.env.GITHUB_OUTPUT, `${k}=${v}\n`);

git('read-tree', '-u', '--reset', `${version}^{tree}`); // app files become exactly the old version
const tipKit = git('ls-tree', '-r', '--name-only', before).split('\n').filter((f) => f && isKitFile(f));
for (const f of git('ls-files').split('\n').filter((x) => x && isKitFile(x) && !tipKit.includes(x))) {
  tryGit('--literal-pathspecs', 'rm', '-q', '--cached', '--', f);
  tryGit('--literal-pathspecs', 'clean', '-q', '-f', '--', f);
}
if (tipKit.length) git('--literal-pathspecs', 'checkout', before, '--', ...tipKit);
git('--literal-pathspecs', 'rm', '-q', '--cached', '--ignore-unmatch', REQUEST); // a pending chat request is replaced by this one
tryGit('--literal-pathspecs', 'clean', '-q', '-f', '--', REQUEST);

if (tryGit('diff', '--cached', '--quiet', 'HEAD') !== null) {
  console.log(`The project is already identical to ${version}. Nothing to do.`);
  out('before', before); out('after', before);
  process.exit(0);
}

const note = String(process.env.NOTE || '').trim();
git('commit', '-q', '-m', `Restore ${version}${note ? `: ${note}` : ''}`);
const after = git('rev-parse', 'HEAD');
try {
  git('push', 'origin', `HEAD:refs/heads/${branch}`);
} catch (e) {
  const why = String(e.stderr || e.message).trim();
  const hint = /rejected|fetch first|non-fast-forward/i.test(why)
    ? 'A new change reached GitHub at the same moment. Wait a minute and run AI Restore again.'
    : /403|permission/i.test(why)
      ? 'Give the workflow permission: Settings -> Actions -> General -> Workflow permissions -> "Read and write".'
      : 'See the message above.';
  fail(`Could not push the restore.\nGitHub said: ${why}\n${hint}`);
}
console.log(`Pushed ${after.slice(0, 7)} with the files of ${version}. Your builder will sync it.`);
out('before', before); out('after', after);
