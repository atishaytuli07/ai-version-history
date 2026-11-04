#!/usr/bin/env node
// ai-versions: gives every change on the default branch its own version.
//
// Source of truth = annotated git tags named vMAJOR.MINOR.PATCH. Tags live
// outside the files, so restoring old code in Lovable can never erase them.
//
// Each run versions every commit since the newest tagged one on the branch
// (first-parent), so a run that GitHub cancelled or skipped is caught up next time.
// For each such commit (oldest first):
//   1. Already has a version tag        -> skip (safe to re-run).
//   2. No app-code changes vs parent     -> skip (kit files and our list updates aren't app code).
//   3. App code identical to a version   -> "restore" (bump RESTORE_BUMP).
//   4. Looks like a near-identical restore -> "restore" (about vX).
//   5. AI wrote a fresh pending.json     -> use its bump + summary.
//   6. Anything else                     -> automatic patch.
// Going back from chat: when the branch has .ai-versions/restore.json
// ({"version": "v3.4.5"}), the code of that version is brought back as a new
// commit, versioned as "Restored to v3.4.5", and the request file is removed.
// Finally it rewrites public/ai-versions.json (read by the in-app version pill)
// from the tags and pushes it, so the list heals itself even after a restore.
//
// The kit itself (.github/, .ai-versions/, the VersionPill component, the list) is
// never treated as app code and is never rolled back by a restore.
//
// Env: AFTER (commit to version up to), BRANCH (branch to push the list and restores to),
//      GITHUB_REPOSITORY, GITHUB_SERVER_URL, GH_TOKEN (for releases),
//      NO_RELEASE=1, NO_LEDGER=1, PILL_NOTES=yes (show prompts), GITHUB_STEP_SUMMARY.

import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { writeFileSync, appendFileSync, mkdtempSync, mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';

const PENDING = '.ai-versions/pending.json';
const LEDGER = 'public/ai-versions.json'; // written by this script only; ignored when comparing code
const REQUEST = '.ai-versions/restore.json'; // "go back to vX", written by the builder's AI; not code
// Kit files: versioning machinery, not the user's app. Never versioned, never rolled back.
const isKitFile = (f) => f === LEDGER || f.startsWith('.github/') || f.startsWith('.ai-versions/')
  || /(^|\/)VersionPill\.tsx$/.test(f);
const RESTORE_BUMP = 'minor'; // going back is a visible change, but not a new direction
const FIRST_VERSION = 'v1.0.0';
const MAX_COMMITS = 100; // safety cap for one push
const LEDGER_MAX = 500; // newest versions kept in the in-app list
const BUMPS = ['patch', 'minor', 'major'];
const TAG_RE = /^v(\d+)\.(\d+)\.(\d+)$/;

const git = (...args) =>
  execFileSync('git', args, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], maxBuffer: 64 << 20 }).trim();
const tryGit = (...args) => {
  try { return git(...args); } catch { return null; }
};
const oneLine = (s, max) => String(s ?? '').replace(/\s+/g, ' ').trim().slice(0, max);

// "What the code is" = every file except the kit.
const sigCache = new Map();
const codeSig = (rev) => {
  if (!sigCache.has(rev)) {
    const list = git('ls-tree', '-r', rev).split('\n').filter((l) => !isKitFile(l.split('\t')[1] || '')).join('\n');
    sigCache.set(rev, createHash('sha1').update(list).digest('hex'));
  }
  return sigCache.get(rev);
};
const changedFiles = (parent, commit) =>
  (parent ? git('diff', '--name-only', parent, commit) : git('ls-tree', '-r', '--name-only', commit))
    .split('\n').filter((f) => f && !isKitFile(f));

// ---------- existing versions ----------
const parse = (t) => TAG_RE.exec(t)?.slice(1).map(Number);
const cmp = (a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2];

const tags = (tryGit('tag', '-l', 'v*') || '').split('\n').filter((t) => TAG_RE.test(t));
tags.sort((a, b) => cmp(parse(a), parse(b)));

const commitToTag = new Map();
const sigToTag = new Map(); // oldest version wins = the original, not a later restore
const seenPendingBlobs = new Set();
const pendingBlobToTag = new Map(); // which version first carried this pending.json
for (const t of tags) {
  const c = git('rev-list', '-n', '1', t);
  commitToTag.set(c, t);
  const sig = codeSig(c);
  if (!sigToTag.has(sig)) sigToTag.set(sig, t);
  const blob = tryGit('rev-parse', `${c}:${PENDING}`);
  if (blob) {
    seenPendingBlobs.add(blob);
    if (!pendingBlobToTag.has(blob)) pendingBlobToTag.set(blob, t);
  }
}
let latest = tags.at(-1) || null;
const warnings = [];
const created = [];

// ---------- commits to process ----------
// Everything since the newest tagged commit on the first-parent line, not just this
// push: GitHub may cancel a queued run, and the next run must catch up.
const after = process.env.AFTER || git('rev-parse', 'HEAD');
function untaggedSince(tip) {
  const line = (tryGit('rev-list', '--first-parent', `--max-count=${MAX_COMMITS + 1}`, tip) || '')
    .split('\n').filter(Boolean);
  const out = [];
  for (const c of line) {
    if (commitToTag.has(c)) return out.reverse();
    out.push(c);
  }
  return null; // no tagged commit within reach (history rewritten, or very long gap)
}
let commits = latest ? untaggedSince(after) : [];
if (latest && commits === null) {
  warnings.push(`No versioned commit found in the last ${MAX_COMMITS} commits; versioning only the newest one.`);
  commits = [after];
}

// ---------- helpers ----------
const nextVersion = (bump) => {
  let [M, m, p] = parse(latest);
  if (bump === 'major') [M, m, p] = [M + 1, 0, 0];
  else if (bump === 'minor') [m, p] = [m + 1, 0];
  else p += 1;
  let v = `v${M}.${m}.${p}`;
  while (tryGit('rev-parse', '-q', '--verify', `refs/tags/${v}`)) v = `v${M}.${m}.${++p}`;
  return v;
};

const repoUrl = process.env.GITHUB_REPOSITORY
  ? `${process.env.GITHUB_SERVER_URL || 'https://github.com'}/${process.env.GITHUB_REPOSITORY}`
  : null;


function publish(version, commit, info) {
  const prev = latest;
  const meta = {
    version, previous: prev, commit, kind: info.kind, bump: info.bump,
    summary: info.summary, reason: info.reason, prompt: info.prompt,
    restored_from: info.restoredFrom || null,
  };
  git('tag', '-a', version, commit, '-m', `${version}: ${info.summary}\n\n${JSON.stringify(meta, null, 2)}`);
  try {
    git('push', 'origin', `refs/tags/${version}`);
  } catch (e) {
    console.error(`Could not save ${version} to GitHub.\n${String(e.stderr || e.message).trim()}\n` +
      'Fix: Settings -> Actions -> General -> Workflow permissions -> "Read and write", then Re-run this job.\n' +
      'If you added a tag ruleset, make sure "Restrict creations" is NOT ticked.');
    process.exit(1);
  }
  latest = version;
  commitToTag.set(commit, version);
  const sig = codeSig(commit);
  if (!sigToTag.has(sig)) sigToTag.set(sig, version);
  created.push(meta);
  console.log(`${version}  ${info.bump.padEnd(5)}  ${info.summary}`);

  if (process.env.NO_RELEASE === '1') return;
  const lines = [
    `**Change:** ${info.summary}`,
    `**Level:** ${info.bump}${info.kind === 'ai' ? ' (chosen by the AI)' : ''}`,
    info.reason ? `**Why this level:** ${info.reason}` : null,
    info.prompt ? `**Prompt:** ${info.prompt}` : null,
    info.restoredFrom ? `**Restored from:** ${info.restoredFrom}${info.exact ? ' (code is identical)' : ' (most files match)'}` : null,
    `**Commit:** ${commit.slice(0, 7)}`,
    prev && repoUrl ? `**Compare with ${prev}:** ${repoUrl}/compare/${prev}...${version}` : null,
  ].filter(Boolean);
  const dir = mkdtempSync(join(tmpdir(), 'aiv-'));
  const notes = join(dir, 'notes.md');
  writeFileSync(notes, lines.join('\n\n') + '\n');
  try {
    execFileSync('gh', ['release', 'create', version, '--verify-tag',
      '--title', `${version} — ${oneLine(info.summary, 80)}`, '--notes-file', notes],
      { stdio: ['ignore', 'pipe', 'pipe'] });
  } catch (e) {
    warnings.push(`Release page for ${version} failed (the version itself is saved): ${String(e.stderr || e.message).trim()}`);
  }
}

function readPending(commit, parent) {
  const changed = parent
    ? git('diff', '--name-only', parent, commit).split('\n')
    : git('ls-tree', '-r', '--name-only', commit).split('\n');
  if (!changed.includes(PENDING)) return { why: 'AI did not update pending.json' };
  const blob = tryGit('rev-parse', `${commit}:${PENDING}`);
  if (!blob) return { why: 'pending.json was deleted' };
  if (seenPendingBlobs.has(blob)) {
    return { why: 'pending.json reused an old entry', hintTag: pendingBlobToTag.get(blob) };
  }
  let data;
  try { data = JSON.parse(git('cat-file', 'blob', blob)); } catch { return { why: 'pending.json is not valid JSON' }; }
  const bump = String(data.bump || '').toLowerCase().trim();
  if (!BUMPS.includes(bump)) return { why: `pending.json has unknown bump "${data.bump}"`, data };
  seenPendingBlobs.add(blob);
  return { ok: true, bump, data };
}

// A restore that is not byte-identical (e.g. the tool left one file alone):
// pending.json went back to an old version's entry AND the code now differs
// from that version in only a few files (at most 2, or under 20% of what changed).
function looksLikeRestore(commit, parent, tag) {
  if (!parent) return false;
  const changed = changedFiles(parent, commit).filter((f) => f !== PENDING);
  const offFromTag = git('diff', '--name-only', `${tag}^{commit}`, commit).split('\n')
    .filter((f) => f && !isKitFile(f));
  return offFromTag.length <= 2 || offFromTag.length < 0.2 * changed.length;
}

// ---------- baseline ----------
if (!latest) {
  const c = after;
  publish(FIRST_VERSION, c, {
    kind: 'baseline', bump: 'baseline', summary: 'Baseline: versioning switched on',
    reason: 'First version. Everything before this commit is not versioned.', prompt: '',
  });
  commits = [];
}

// ---------- main loop ----------
function versionCommit(c) {
  if (commitToTag.has(c)) return;
  const parent = tryGit('rev-parse', `${c}^`);
  if (parent && codeSig(parent) === codeSig(c)) {
    console.log(`skip ${c.slice(0, 7)}: no code changes`);
    return;
  }
  const subject = oneLine(git('log', '-1', '--format=%s', c), 100) || 'Change';

  const match = sigToTag.get(codeSig(c));
  if (match) {
    publish(nextVersion(RESTORE_BUMP), c, {
      kind: 'restore', bump: RESTORE_BUMP, restoredFrom: match, exact: true,
      summary: `Restored to ${match}`,
      reason: 'Code is identical to an earlier version, so this was a restore.', prompt: '',
    });
    return;
  }

  const p = readPending(c, parent);
  if (!p.ok && p.hintTag && looksLikeRestore(c, parent, p.hintTag)) {
    publish(nextVersion(RESTORE_BUMP), c, {
      kind: 'restore', bump: RESTORE_BUMP, restoredFrom: p.hintTag, exact: false,
      summary: `Restored to about ${p.hintTag}`,
      reason: `pending.json and most changed files went back to ${p.hintTag}, so this looks like a restore.`,
      prompt: '',
    });
    return;
  }
  if (p.ok) {
    publish(nextVersion(p.bump), c, {
      kind: 'ai', bump: p.bump,
      summary: oneLine(p.data.summary, 100) || subject,
      reason: oneLine(p.data.reason, 200),
      prompt: oneLine(p.data.prompt, 300),
    });
  } else {
    publish(nextVersion('patch'), c, {
      kind: 'auto', bump: 'patch', summary: subject,
      reason: `Automatic patch: ${p.why}.`, prompt: '',
    });
  }
}

for (const c of commits) versionCommit(c);

// ---------- going back from chat (.ai-versions/restore.json) ----------
let notice = null;

// After bringing back old files, put the kit back as it is now: old workflow files
// would be refused by GitHub, and old scripts or settings would quietly downgrade the kit.
function keepKitFrom(tip) {
  const tipKit = git('ls-tree', '-r', '--name-only', tip).split('\n').filter((f) => f && isKitFile(f));
  for (const f of git('ls-files').split('\n').filter((x) => x && isKitFile(x) && !tipKit.includes(x))) {
    tryGit('rm', '-q', '--cached', '--', f);
    tryGit('clean', '-q', '-f', '--', f);
  }
  if (tipKit.length) git('checkout', tip, '--', ...tipKit);
  tryGit('rm', '-q', '--cached', '--ignore-unmatch', '--', REQUEST);
  tryGit('clean', '-q', '-f', '--', REQUEST);
}

// A request counts only if the app code hasn't changed since it was made. If the user
// kept working after asking (or a failed run left it behind), it's dropped: an old
// request must never roll back newer work.
function requestIsFresh(tip, blob) {
  const line = (tryGit('rev-list', '--first-parent', `--max-count=${MAX_COMMITS}`, tip) || '')
    .split('\n').filter(Boolean);
  for (const c of line) {
    if (tryGit('rev-parse', `${c}:${REQUEST}`) === blob && tryGit('rev-parse', `${c}^:${REQUEST}`) !== blob) {
      return codeSig(c) === codeSig(tip);
    }
  }
  return false;
}

function handleRestoreRequest() {
  const branch = process.env.BRANCH || 'main';
  for (let attempt = 1; attempt <= 3; attempt++) {
    if (tryGit('fetch', '-q', 'origin', branch) === null) return;
    const tip = git('rev-parse', 'FETCH_HEAD');
    const blob = tryGit('rev-parse', `${tip}:${REQUEST}`);
    if (!blob) return; // nothing requested
    let req = {};
    try { req = JSON.parse(git('cat-file', 'blob', blob)); } catch {}
    let v = oneLine(req.version, 40).toLowerCase();
    if (v && !v.startsWith('v')) v = `v${v}`;
    const exists = TAG_RE.test(v) && tryGit('rev-parse', '-q', '--verify', `refs/tags/${v}`) !== null;
    const fresh = requestIsFresh(tip, blob);

    git('checkout', '-q', '-B', 'ai-versions-restore', tip);
    let message;
    let restoring = false;
    if (!fresh) {
      git('rm', '-q', '--ignore-unmatch', REQUEST);
      message = `Drop an old go-back request (${v || 'no version'})`;
      notice = `An old request to go back to ${v || 'a version'} was dropped, because newer changes came after it. Ask again if you still want it.`;
    } else if (!exists) {
      git('rm', '-q', '--ignore-unmatch', REQUEST);
      message = `Restore request: ${v || 'no version given'} doesn't exist`;
      notice = `Couldn't go back to ${v || '(no version given)'}: that version doesn't exist. Check the number in the version list and ask again.`;
    } else {
      git('read-tree', '-u', '--reset', `${v}^{tree}`); // app files become exactly that version
      keepKitFrom(tip);
      const note = oneLine(req.note, 100);
      message = `Restore ${v} (asked in chat)${note ? `: ${note}` : ''}`;
      restoring = true;
    }
    if (tryGit('diff', '--cached', '--quiet', tip) !== null) return; // nothing to change
    git('commit', '-q', '-m', message);
    const head = git('rev-parse', 'HEAD');
    const pushed = (() => {
      try { git('push', '-q', 'origin', `HEAD:refs/heads/${branch}`); return null; } catch (e) { return String(e.stderr || e.message).trim(); }
    })();
    if (pushed !== null) {
      console.log(`Restore push was rejected (attempt ${attempt}): ${pushed}`);
      notice = null;
      if (attempt === 3) {
        console.log(`::error::Could not apply the go-back request: ${pushed}`);
        process.exitCode = 1;
      }
      continue;
    }
    console.log(message);
    if (restoring) {
      if (codeSig(head) === codeSig(tip)) notice = `Already at ${v}: the code didn't change.`;
      versionCommit(head);
    }
    return;
  }
  warnings.push('Could not apply the go-back request after 3 tries. It will be dropped on the next run; ask again then.');
}

if (latest) handleRestoreRequest();

// ---------- in-app version list ----------
// The list is served by the live site too (anything in public/ is), so prompts and
// reasons are left out unless PILL_NOTES=yes. Versions, dates and summaries stay.
const HIDE_NOTES = String(process.env.PILL_NOTES || 'no').toLowerCase() !== 'yes';
function buildLedger() {
  const all = (tryGit('tag', '-l', 'v*') || '').split('\n').filter((t) => TAG_RE.test(t));
  all.sort((a, b) => cmp(parse(b), parse(a))); // newest first
  const builtOn = new Map(); // after going back, later versions are built on that version
  let base = null;
  for (const t of [...all].reverse()) {
    let m = {};
    try { m = JSON.parse(tryGit('tag', '-l', '--format=%(contents:body)', t) || '{}'); } catch {}
    if (m.kind === 'restore') base = m.restored_from || base;
    else if (base) builtOn.set(t, base);
  }
  const versions = all.slice(0, LEDGER_MAX).map((t) => {
    const date = tryGit('for-each-ref', '--format=%(taggerdate:iso-strict)', `refs/tags/${t}`) || null;
    let m = {};
    try { m = JSON.parse(tryGit('tag', '-l', '--format=%(contents:body)', t) || '{}'); } catch {}
    return {
      version: t,
      date,
      level: m.kind === 'restore' ? 'restore' : m.kind === 'baseline' ? 'start' : (m.bump || 'patch'),
      summary: m.summary || '',
      note: HIDE_NOTES ? '' : m.prompt || '',
      reason: HIDE_NOTES ? '' : m.reason || '',
      restored_from: m.restored_from || null,
      built_on: builtOn.get(t) || null,
    };
  });
  const out = { versions };
  if (notice) out.notice = { text: notice, date: new Date().toISOString() };
  return JSON.stringify(out, null, 2) + '\n';
}

function pushLedger() {
  const branch = process.env.BRANCH || 'main';
  const content = buildLedger();
  for (let attempt = 1; attempt <= 3; attempt++) {
    if (tryGit('fetch', '-q', 'origin', branch) === null) return warnings.push(`Could not fetch ${branch} to update the version list.`);
    git('checkout', '-q', '-B', 'ai-versions-list', 'FETCH_HEAD');
    mkdirSync(dirname(LEDGER), { recursive: true });
    writeFileSync(LEDGER, content);
    git('add', LEDGER);
    if (tryGit('diff', '--cached', '--quiet') !== null) return console.log('Version list already up to date.');
    git('commit', '-q', '-m', `Update version list (${latest})`);
    if (tryGit('push', '-q', 'origin', `HEAD:refs/heads/${branch}`) !== null) {
      return console.log(`Version list updated (${latest}).`);
    }
    console.log(`List push was rejected (attempt ${attempt}), retrying...`);
  }
  warnings.push('Could not push the version list after 3 tries. Versions are safe; the next change will update the list.');
}

if (process.env.NO_LEDGER !== '1' && latest) pushLedger();

// ---------- report ----------
if (process.env.GITHUB_STEP_SUMMARY && created.length) {
  const rows = created.map((v) =>
    `| ${v.version} | ${v.bump} | ${v.summary.replace(/\|/g, '/')} | ${v.commit.slice(0, 7)} |`);
  appendFileSync(process.env.GITHUB_STEP_SUMMARY,
    ['### New versions', '| Version | Level | Change | Commit |', '|---|---|---|---|', ...rows, ''].join('\n'));
}
if (!created.length) console.log('No new versions.');
for (const w of warnings) console.log(`::warning::${w}`);
