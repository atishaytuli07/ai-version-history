#!/usr/bin/env python3
"""ai-versions: every change gets a version, nothing is ever deleted,
and going back to an old version is saved as a new version.

Run `python3 aiv.py --help` for the commands. Needs Python 3.8+ only.
Git is optional; when the project is a git repo, .gitignore is respected
and the version store is kept out of git so checkouts can't rewrite history.
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import fnmatch
import hashlib
import html
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import threading
import time
import zipfile
import zlib
from pathlib import Path

FORMAT = 1
STORE = ".ai-versions"
IGNORE_FILE = ".aiversionsignore"
# AI tool settings and installed skills are never versioned: going back must not delete
# the skill or the auto-save hook, and a shared backup must not be able to plant them.
TOOL_DIRS = (".claude", ".cursor", ".agents", ".gemini", ".devin", ".windsurf")
ALWAYS_EXCLUDE = [".git/", STORE + "/", "/.github/skills/"] + ["/%s/" % d for d in TOOL_DIRS]
# Without git there's no .gitignore to trust, so skip the usual generated and secret files.
# With git, git decides: tracked files are versioned even if their folder is called "build".
DEFAULT_EXCLUDES = ALWAYS_EXCLUDE + [
    "node_modules/", ".next/", ".nuxt/", ".svelte-kit/", "dist/", "build/", "out/", ".output/",
    ".venv/", "venv/", "__pycache__/", ".cache/", ".turbo/", ".vercel/", ".parcel-cache/",
    "coverage/", ".idea/", ".DS_Store", "Thumbs.db", "*.pyc", "*.swp", ".env", ".env.*",
]
LIMIT_FILES = 5000          # a bigger project almost always means the wrong folder
LIMIT_TOTAL_MB = 500
MAX_FILE_MB = 25            # bigger files are skipped and listed, not silently dropped
DIFF_LINE_LIMIT = 2000
LEVEL_WORDS = {
    "start": "Start", "patch": "Small tweak", "minor": "New feature",
    "major": "Big change", "restore": "Went back",
}
BUMPS = ("patch", "minor", "major")
VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")

try:  # never crash on a console that can't print some characters
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


class Fail(Exception):
    def __init__(self, message: str, code: int = 1):
        super().__init__(message)
        self.code = code


# ---------------------------------------------------------------- helpers

def now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def parse_version(label: str):
    m = VERSION_RE.match(label.strip())
    return tuple(int(x) for x in m.groups()) if m else None


def vkey(entry: dict):
    return parse_version(entry["version"])


def when(iso: str) -> str:
    try:
        t = dt.datetime.fromisoformat(iso)
    except Exception:
        return iso
    mins = int((dt.datetime.now().astimezone() - t).total_seconds() // 60)
    if mins < 1:
        return "just now"
    if mins < 60:
        return "%d min ago" % mins
    if mins < 24 * 60:
        return "%d h ago" % (mins // 60)
    return t.strftime("%d %b %Y, %H:%M").lstrip("0")


def clip(text, n: int) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()[:n]


def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return ("%d %s" % (n, unit)) if unit == "B" else ("%.1f %s" % (n, unit))
        n /= 1024.0
    return str(n)


PROTECTED_TOP = {".git", STORE} | set(TOOL_DIRS)


def plain_rel(path: str) -> bool:
    """A relative path that stays inside the folder."""
    parts = path.replace("\\", "/").split("/")
    return bool(path) and not path.startswith(("/", "\\")) and all(
        part not in ("", ".", "..") and ":" not in part for part in parts)


def safe_rel(path: str) -> bool:
    """A project file we may write: not git internals, the history itself, or AI tool settings
    (checked without regard to case, for Windows and macOS)."""
    if not plain_rel(path):
        return False
    low = path.replace("\\", "/").lower()
    return low.split("/")[0] not in PROTECTED_TOP and not low.startswith(".github/skills/")


def write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(".%s.tmp-%d" % (path.name, os.getpid()))
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def run_git(root: Path, *args: str):
    try:
        p = subprocess.run(["git", *args], cwd=str(root), capture_output=True, timeout=60)
    except Exception:
        return None
    return p.stdout.decode("utf-8", "replace") if p.returncode == 0 else None


# ---------------------------------------------------------------- ignore rules (gitignore-lite)

def compile_rules(lines):
    rules = []
    for raw in lines:
        s = raw.rstrip("\n").rstrip()
        if not s or s.startswith("#"):
            continue
        neg = s.startswith("!")
        if neg:
            s = s[1:]
        dir_only = s.endswith("/")
        s = s.rstrip("/")
        anchored = "/" in s
        s = s.lstrip("/")
        if s:
            rules.append((s, dir_only, anchored, neg))
    return rules


def is_ignored(rel: str, is_dir: bool, rules) -> bool:
    hit = False
    base = rel.rsplit("/", 1)[-1]
    for pat, dir_only, anchored, neg in rules:
        if dir_only and not is_dir:
            continue
        target = rel if anchored else base
        if fnmatch.fnmatchcase(target, pat) or (anchored and fnmatch.fnmatchcase(rel, pat + "/*")):
            hit = not neg
    return hit


def under_ignored_dir(rel: str, rules) -> bool:
    parts = rel.split("/")[:-1]
    for i in range(1, len(parts) + 1):
        if is_ignored("/".join(parts[:i]), True, rules):
            return True
    return False


def matches_only(rel: str, only) -> bool:
    if not only:
        return True
    for p in only:
        p = p.replace("\\", "/").strip("/")
        if rel == p or rel.startswith(p + "/") or fnmatch.fnmatchcase(rel, p):
            return True
    return False


# ---------------------------------------------------------------- the store

class Store:
    def __init__(self, root: Path):
        self.root = root
        self.dir = root / STORE
        cfg_path = self.dir / "config.json"
        if not cfg_path.is_file():
            raise Fail("No version history here. Run `init` in the project folder first.", 2)
        self.config = json.loads(cfg_path.read_text("utf-8"))
        self._entries = None

    # ---- discovery
    @staticmethod
    def find(start: Path) -> "Store":
        start = start.resolve()
        for d in [start, *start.parents]:
            if (d / STORE / "config.json").is_file():
                return Store(d)
        raise Fail("No version history found in %s or its parent folders. Run `init` first." % start, 2)

    # ---- objects
    def obj_path(self, sha: str) -> Path:
        return self.dir / "objects" / sha[:2] / sha[2:]

    def put_blob(self, data: bytes, sha: str) -> None:
        p = self.obj_path(sha)
        if not p.exists():
            write_atomic(p, zlib.compress(data, 6))

    def read_blob(self, sha: str) -> bytes:
        p = self.obj_path(sha)
        if not p.exists():
            raise Fail("Stored content %s is missing. Run `doctor`." % sha[:12])
        return zlib.decompress(p.read_bytes())

    def put_manifest(self, files: dict) -> str:
        body = json.dumps({k: [v["sha"], v["x"], v["size"]] for k, v in sorted(files.items())},
                          separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        mid = hashlib.sha256(body).hexdigest()
        p = self.dir / "manifests" / (mid + ".json")
        if not p.exists():
            write_atomic(p, body)
        return mid

    def manifest(self, mid: str) -> dict:
        p = self.dir / "manifests" / (mid + ".json")
        if not p.exists():
            raise Fail("Stored file list %s is missing. Run `doctor`." % mid[:12])
        raw = json.loads(p.read_text("utf-8"))
        return {k: {"sha": v[0], "x": bool(v[1]), "size": v[2]} for k, v in raw.items()}

    # ---- entries
    def entries(self) -> list:
        if self._entries is None:
            out = []
            for p in (self.dir / "entries").glob("v*.json"):
                try:
                    e = json.loads(p.read_text("utf-8"))
                    if parse_version(e.get("version", "")):
                        out.append(e)
                except Exception:
                    pass
            self._entries = sorted(out, key=vkey)
        return self._entries

    def latest(self):
        es = self.entries()
        return es[-1] if es else None

    def by_label(self, label: str) -> dict:
        label = (label or "").strip()
        es = self.entries()
        if not es:
            raise Fail("There are no versions yet.")
        caret = 0
        while label.endswith("^"):
            caret += 1
            label = label[:-1]
        if label.lower() in ("latest", "current", "now", "head"):
            e = es[-1]
        elif label.lower() in ("prev", "previous", "last"):
            e, caret = es[-1], caret + 1
        else:
            v = parse_version(label)
            if not v:
                raise Fail('"%s" is not a version. Use a number like v1.2.0, or latest, or prev.' % label)
            found = [x for x in es if vkey(x) == v]
            if not found:
                raise Fail("v%d.%d.%d doesn't exist. Run `list` to see all versions." % v)
            e = found[0]
        for _ in range(caret):
            if not e.get("parent"):
                raise Fail("%s is the first version; nothing comes before it." % e["version"])
            e = self.by_label(e["parent"])
        return e

    def next_version(self, level: str) -> str:
        last = self.latest()
        if not last:
            return "v1.0.0"
        M, m, p = vkey(last)
        if level == "major":
            M, m, p = M + 1, 0, 0
        elif level in ("minor", "restore"):
            m, p = m + 1, 0
        else:
            p += 1
        return "v%d.%d.%d" % (M, m, p)

    def add_entry(self, entry: dict) -> dict:
        d = self.dir / "entries"
        d.mkdir(parents=True, exist_ok=True)
        path = d / (entry["version"] + ".json")
        data = json.dumps(entry, indent=2, ensure_ascii=False).encode("utf-8")
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        self._entries = None
        self.write_history()
        return entry

    def write_history(self) -> None:
        lines = ["# Version history", "",
                 "Written by ai-versions. Don't edit: the files in `entries/` are the real history.", "",
                 "| Version | Change | Summary | Saved |", "|---|---|---|---|"]
        for e in reversed(self.entries()):
            lines.append("| %s | %s | %s | %s |" % (
                e["version"], LEVEL_WORDS.get(e["level"], e["level"]),
                clip(e.get("summary"), 120).replace("|", "/"), e.get("date", "")[:16].replace("T", " ")))
        write_atomic(self.dir / "HISTORY.md", ("\n".join(lines) + "\n").encode("utf-8"))

    # ---- locking
    def lock(self):
        store = self

        class _Lock:
            def __enter__(self_inner):
                path = store.dir / ".lock"
                deadline = time.time() + 20
                while True:
                    try:
                        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL)
                        os.write(fd, ("%d %f" % (os.getpid(), time.time())).encode())
                        os.close(fd)
                        return self_inner
                    except FileExistsError:
                        try:
                            if time.time() - path.stat().st_mtime > 120:
                                path.unlink()
                                continue
                        except FileNotFoundError:
                            continue
                        if time.time() > deadline:
                            raise Fail("Another save or restore is running. Try again in a moment.")
                        time.sleep(0.2)

            def __exit__(self_inner, *exc):
                try:
                    (store.dir / ".lock").unlink()
                except FileNotFoundError:
                    pass
                return False

        return _Lock()

    # ---- scanning the working files
    def candidate_paths(self):
        root = self.root
        only = self.config.get("only") or []
        listed = run_git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", ".")
        rules = compile_rules(ALWAYS_EXCLUDE if listed is not None else DEFAULT_EXCLUDES)
        ign = root / IGNORE_FILE
        if ign.is_file():
            rules += compile_rules(ign.read_text("utf-8", "replace").splitlines())
        if listed is not None:
            paths = [p for p in listed.split("\0") if p]
        else:
            gi = root / ".gitignore"
            if gi.is_file():
                rules += compile_rules(gi.read_text("utf-8", "replace").splitlines())
            paths = []
            for dirpath, dirnames, filenames in os.walk(str(root)):
                rel_dir = os.path.relpath(dirpath, str(root)).replace("\\", "/")
                rel_dir = "" if rel_dir == "." else rel_dir
                keep = []
                for d in dirnames:
                    rel = (rel_dir + "/" + d) if rel_dir else d
                    if not is_ignored(rel, True, rules) and not os.path.islink(os.path.join(dirpath, d)):
                        keep.append(d)
                dirnames[:] = sorted(keep)
                for f in filenames:
                    paths.append((rel_dir + "/" + f) if rel_dir else f)
        out = []
        for rel in paths:
            rel = rel.replace("\\", "/")
            if is_ignored(rel, False, rules) or under_ignored_dir(rel, rules) or not matches_only(rel, only):
                continue
            out.append(rel)
        return sorted(set(out))

    def scan(self, check_limits: bool = True):
        """Returns ({path: {sha, x, size}}, skipped[(path, why)])."""
        cache_path = self.dir / "cache.json"
        try:
            cache = json.loads(cache_path.read_text("utf-8"))
        except Exception:
            cache = {}
        max_bytes = int(self.config.get("max_file_mb", MAX_FILE_MB) * 1024 * 1024)
        prev = {}
        last = self.latest()
        if last and os.name == "nt":
            prev = self.manifest(last["manifest"])
        files, skipped, new_cache, total = {}, [], {}, 0
        paths = self.candidate_paths()
        if check_limits and not self.config.get("allow_large") and len(paths) > LIMIT_FILES:
            raise Fail("This folder has %d files, which looks like more than one project. Use "
                       "`init --only <folder or file>` or list folders to skip in %s." % (len(paths), IGNORE_FILE))
        for rel in paths:
            full = self.root / rel
            try:
                st = os.lstat(str(full))
            except FileNotFoundError:
                continue
            if stat.S_ISLNK(st.st_mode):
                skipped.append((rel, "link"))
                continue
            if not stat.S_ISREG(st.st_mode):
                continue
            if st.st_size > max_bytes:
                skipped.append((rel, "larger than %d MB" % (max_bytes // (1024 * 1024))))
                continue
            total += st.st_size
            if os.name == "nt":
                x = bool(prev.get(rel, {}).get("x"))
            else:
                x = bool(st.st_mode & stat.S_IXUSR)
            c = cache.get(rel)
            if c and c[0] == st.st_size and c[1] == st.st_mtime_ns:
                sha = c[2]
            else:
                h = hashlib.sha256()
                with open(str(full), "rb") as f:
                    for chunk in iter(lambda: f.read(1 << 20), b""):
                        h.update(chunk)
                sha = h.hexdigest()
            new_cache[rel] = [st.st_size, st.st_mtime_ns, sha]
            files[rel] = {"sha": sha, "x": x, "size": st.st_size}
        if check_limits and not self.config.get("allow_large") and total > LIMIT_TOTAL_MB * 1024 * 1024:
            raise Fail("This folder holds %s of files, which looks like the wrong folder. Use "
                       "`init --only <folder or file>` or skip big folders in %s." % (human_size(total), IGNORE_FILE))
        try:
            write_atomic(cache_path, json.dumps(new_cache).encode("utf-8"))
        except Exception:
            pass
        return files, skipped

    def store_files(self, files: dict) -> None:
        for rel, meta in files.items():
            if not self.obj_path(meta["sha"]).exists():
                data = (self.root / rel).read_bytes()
                sha = hashlib.sha256(data).hexdigest()
                if sha != meta["sha"]:  # changed while we were working: take what's there now
                    meta["sha"], meta["size"] = sha, len(data)
                self.put_blob(data, sha)


def compare(old: dict, new: dict) -> dict:
    added = sorted(p for p in new if p not in old)
    deleted = sorted(p for p in old if p not in new)
    modified = sorted(p for p in new if p in old and (new[p]["sha"] != old[p]["sha"] or new[p]["x"] != old[p]["x"]))
    return {"added": added, "modified": modified, "deleted": deleted}


def count_changes(ch: dict) -> int:
    return len(ch["added"]) + len(ch["modified"]) + len(ch["deleted"])


def describe_changes(ch: dict) -> str:
    n = count_changes(ch)
    parts = ["%d %s" % (len(ch[k]), k) for k in ("added", "modified", "deleted") if ch[k]]
    return "%d file%s changed (%s)" % (n, "" if n == 1 else "s", ", ".join(parts)) if n else "no file changes"


# ---------------------------------------------------------------- core operations

def record(store: Store, files: dict, skipped, *, level: str, summary: str, reason: str = "",
           prompt: str = "", by: str = "ai", restored_from=None, extra=None) -> dict:
    store.store_files(files)
    mid = store.put_manifest(files)
    last = store.latest()
    old = store.manifest(last["manifest"]) if last else {}
    for _ in range(5):
        version = store.next_version(level)
        entry = {
            "format": FORMAT, "version": version, "level": level,
            "bump": "minor" if level == "restore" else ("baseline" if level == "start" else level),
            "summary": clip(summary, 200) or "Change", "reason": clip(reason, 400), "prompt": clip(prompt, 600),
            "date": now_iso(), "parent": last["version"] if last else None,
            "restored_from": restored_from, "by": by, "manifest": mid,
            "changes": compare(old, files), "skipped": [p for p, _ in skipped],
        }
        if extra:
            entry.update(extra)
        try:
            return store.add_entry(entry)
        except FileExistsError:
            store._entries = None
            last = store.latest()
    raise Fail("Couldn't pick a version number. Run `doctor`.")


def oldest_with_manifest(store: Store, mid: str):
    for e in store.entries():
        if e["manifest"] == mid:
            return e
    return None


def save_now(store: Store, *, level: str, summary: str, reason: str, prompt: str, by: str):
    """Saves the working files. Returns (entry or None, message)."""
    files, skipped = store.scan()
    last = store.latest()
    if last:
        old = store.manifest(last["manifest"])
        if not count_changes(compare(old, files)):
            msg = "No changes since %s. Nothing to save." % last["version"]
            if skipped:
                msg += "\nNot saved: %s" % ", ".join("%s (%s)" % s for s in skipped[:10])
            return None, msg
    store.store_files(files)
    mid = store.put_manifest(files)
    twin = oldest_with_manifest(store, mid)
    if twin:
        e = record(store, files, skipped, level="restore", summary="Went back to %s" % twin["version"],
                   reason="The files are identical to %s. %s" % (twin["version"], clip(summary, 120)),
                   prompt=prompt, by=by, restored_from=twin["version"])
        return e, "Saved %s (Went back): the files match %s exactly, so this is recorded as going back." % (
            e["version"], twin["version"])
    e = record(store, files, skipped, level=level, summary=summary, reason=reason, prompt=prompt, by=by)
    msg = "Saved %s (%s): %s. %s." % (e["version"], LEVEL_WORDS[level], e["summary"], describe_changes(e["changes"]).capitalize())
    if skipped:
        msg += "\nNot saved: %s" % ", ".join("%s (%s)" % s for s in skipped[:10])
    return e, msg


def unsaved(store: Store):
    files, skipped = store.scan()
    last = store.latest()
    old = store.manifest(last["manifest"]) if last else {}
    return files, skipped, compare(old, files)


def auto_summary(ch: dict) -> str:
    names = [p.rsplit("/", 1)[-1] for p in ch["modified"] + ch["added"] + ch["deleted"]]
    head = ", ".join(names[:3]) + (" (+%d more)" % (len(names) - 3) if len(names) > 3 else "")
    return "Unsaved changes in " + head


def write_files(store: Store, target: dict, current: dict):
    """Makes the folder match `target`. Returns (files changed, files kept aside).

    `current` is what the last scan saw, so every file in it is already saved in the history.
    Anything else in the way (an ignored or too-large file, a link, a folder) is moved to
    .ai-versions/displaced/ instead of being overwritten or deleted."""
    root, n, aside = store.root, 0, []
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    # Never write git internals, the history or AI tool settings, whatever a version lists.
    target = {k: v for k, v in target.items() if safe_rel(k)}
    current = {k: v for k, v in current.items() if safe_rel(k)}

    def keep_aside(path: Path) -> None:
        rel = path.relative_to(root).as_posix()
        dest = store.dir / "displaced" / stamp / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        os.replace(str(path), str(dest))
        aside.append(rel)

    try:
        # Delete first: on Windows and macOS "readme.md" and "README.md" are one file, and a file
        # can't become a folder (or the other way) while the old one is still there.
        for rel in sorted(set(current) - set(target)):
            p = root / rel
            if p.is_file() or p.is_symlink():
                p.unlink()
                n += 1
            parent = p.parent
            while parent != root:
                try:
                    parent.rmdir()
                except OSError:
                    break
                parent = parent.parent
        for rel, meta in sorted(target.items()):
            dest = root / rel
            cur = current.get(rel)
            if cur and cur["sha"] == meta["sha"] and cur["x"] == meta["x"] and dest.is_file():
                continue
            # A file or link where this file's folder should be, e.g. "api" when we need "api/x.js".
            for parent in reversed(dest.relative_to(root).parents):
                p = root / parent
                if str(parent) != "." and (p.is_symlink() or (p.exists() and not p.is_dir())):
                    keep_aside(p)
            if dest.is_symlink() or dest.is_dir():
                keep_aside(dest)
            elif dest.exists() and rel not in current:
                keep_aside(dest)  # ignored, too large or otherwise not saved: don't lose it
            write_atomic(dest, store.read_blob(meta["sha"]))
            if os.name != "nt":
                mode = dest.stat().st_mode
                dest.chmod((mode | 0o111) if meta["x"] else (mode & ~0o111))
            n += 1
    except OSError as err:
        raise Fail("Couldn't finish writing the files (%s). Your work from before was saved in the history "
                   "first, so nothing is lost: run `list` and go back to the newest version." % err)
    return n, aside


def displaced_note(store: Store, aside: list) -> str:
    """Tells the user where files that were in the way were moved."""
    if not aside:
        return ""
    where = (store.dir / "displaced").relative_to(store.root).as_posix()
    shown = ", ".join(aside[:5]) + (" (+%d more)" % (len(aside) - 5) if len(aside) > 5 else "")
    return ("Kept a copy of %d file%s that the history doesn't track, instead of overwriting %s: %s. "
            "%s in %s/." % (len(aside), "" if len(aside) == 1 else "s",
                            "it" if len(aside) == 1 else "them", shown,
                            "It's" if len(aside) == 1 else "They're", where))


def built_on(store: Store) -> dict:
    """After going back, later versions are built on the version that was restored."""
    out, base = {}, None
    for e in store.entries():
        if e["level"] == "restore":
            base = e.get("restored_from") or base
        elif base:
            out[e["version"]] = base
    return out


def lineage(store: Store, entry: dict) -> list:
    chain, seen, e = [], set(), entry
    while e and e["version"] not in seen:
        seen.add(e["version"])
        chain.append(e)
        nxt = e.get("restored_from") if e["level"] == "restore" else e.get("parent")
        e = store.by_label(nxt) if nxt else None
    return list(reversed(chain))


# ---------------------------------------------------------------- commands

def cmd_init(args) -> None:
    root = Path(args.root or ".").resolve()
    if not root.is_dir():
        raise Fail("%s is not a folder." % root)
    if (root / STORE / "config.json").is_file():
        store = Store(root)
        last = store.latest()
        print("Already set up. Current version: %s." % (last["version"] if last else "none"))
        return
    if (root / ".github" / "workflows" / "ai-versions.yml").is_file() and not args.force:
        raise Fail("This project uses the GitHub version of ai-versions. Keep using it: update "
                   ".ai-versions/pending.json with each change instead of running `init`.")
    for d in [root, *root.parents]:
        if (d / STORE / "config.json").is_file() and d != root:
            raise Fail("%s already has a version history that includes this folder. Use that one." % d)
    (root / STORE / "entries").mkdir(parents=True, exist_ok=True)
    config = {"format": FORMAT, "created": now_iso(), "only": args.only or [],
              "max_file_mb": MAX_FILE_MB, "allow_large": bool(args.allow_large)}
    write_atomic(root / STORE / "config.json", json.dumps(config, indent=2).encode("utf-8"))
    write_atomic(root / STORE / "README.md", (
        "# Version history (ai-versions)\n\nEvery version of this project lives here. Don't edit or delete "
        "anything in this folder.\nSee HISTORY.md for the list, or run `python3 .ai-versions/aiv.py list`.\n").encode())
    try:
        shutil.copyfile(__file__, str(root / STORE / "aiv.py"))
    except Exception:
        pass
    note = exclude_from_git(root)
    try:
        store = Store(root)
        files, skipped = store.scan()
    except Fail:
        shutil.rmtree(str(root / STORE), ignore_errors=True)
        raise
    e = record(store, files, skipped, level="start", summary=args.summary or "Versioning switched on",
               reason="First version. Earlier changes aren't in the history.", by="start")
    if files:
        print("Set up version history. %s saved with %d file%s." % (e["version"], len(files), "" if len(files) == 1 else "s"))
    else:
        print("Set up version history. %s is the empty starting point; your first change becomes the next version." % e["version"])
    if skipped:
        print("Not saved: %s" % ", ".join("%s (%s)" % s for s in skipped[:10]))
    if note:
        print(note)


def exclude_from_git(root: Path) -> str:
    if run_git(root, "rev-parse", "--is-inside-work-tree") is None:
        return ""
    ex = run_git(root, "rev-parse", "--git-path", "info/exclude")
    prefix = (run_git(root, "rev-parse", "--show-prefix") or "").strip()
    if not ex:
        return ""
    ex_path = Path(ex.strip())
    if not ex_path.is_absolute():
        ex_path = root / ex_path
    line = "/" + prefix + STORE + "/"
    try:
        text = ex_path.read_text("utf-8") if ex_path.exists() else ""
        if line not in text.splitlines():
            ex_path.parent.mkdir(parents=True, exist_ok=True)
            with open(str(ex_path), "a", encoding="utf-8") as f:
                f.write(("" if text.endswith("\n") or not text else "\n") + line + "\n")
        return "Kept %s out of git (in .git/info/exclude) so git checkouts can't change the history." % STORE
    except Exception:
        return ""


def cmd_save(args) -> None:
    store = Store.find(Path(args.root or "."))
    if not clip(args.summary, 200):
        raise Fail("Add --summary with one line about what changed.")
    with store.lock():
        _, msg = save_now(store, level=args.bump, summary=args.summary, reason=args.reason or "",
                          prompt=args.prompt or "", by="ai")
    print(msg)


def read_stdin(timeout: float = 2.0) -> str:
    """Hooks pass JSON on stdin and close it. Never wait forever on a stdin nobody writes to."""
    if sys.stdin is None or sys.stdin.isatty():
        return ""
    box = []
    reader = threading.Thread(target=lambda: box.append(sys.stdin.read()), daemon=True)
    reader.start()
    reader.join(timeout)
    return box[0] if box else ""


def cmd_auto(args) -> None:
    """For hooks: saves anything the AI left unsaved as a Small tweak. Never fails."""
    try:
        root = args.root or os.environ.get("CLAUDE_PROJECT_DIR") or os.environ.get("CURSOR_PROJECT_DIR")
        if not root:
            try:
                data = json.loads(read_stdin() or "{}")
                roots = data.get("workspace_roots") or []
                root = roots[0] if roots else data.get("cwd")
            except Exception:
                root = None
        try:
            store = Store.find(Path(root or "."))
        except Fail:
            return
        with store.lock():
            files, skipped, ch = unsaved(store)
            if not count_changes(ch):
                return
            _, msg = save_now(store, level="patch", summary=auto_summary(ch),
                              reason="Saved automatically: the AI didn't save this change.", prompt="", by="auto")
        if not args.quiet:
            print(msg)
    except Exception as exc:  # a hook must never block the tool
        print("ai-versions auto-save skipped: %s" % exc, file=sys.stderr)


def cmd_status(args) -> None:
    store = Store.find(Path(args.root or "."))
    last = store.latest()
    if not last:
        print("No versions yet.")
        return
    print("Current version: %s (%s) %s, saved %s." % (last["version"], LEVEL_WORDS.get(last["level"]),
                                                     last["summary"], when(last["date"])))
    _, skipped, ch = unsaved(store)
    if not count_changes(ch):
        print("No unsaved changes.")
    else:
        print("Unsaved changes: %s" % describe_changes(ch))
        for k in ("added", "modified", "deleted"):
            for p in ch[k][:30]:
                print("  %-9s %s" % (k, p))
    if skipped:
        print("Not tracked: %s" % ", ".join("%s (%s)" % s for s in skipped[:10]))


def cmd_list(args) -> None:
    store = Store.find(Path(args.root or "."))
    es = list(reversed(store.entries()))
    if args.json:
        print(json.dumps(es if args.all else es[: args.limit], indent=2, ensure_ascii=False))
        return
    if not es:
        print("No versions yet.")
        return
    shown = es if args.all else es[: args.limit or 20]
    on = built_on(store)
    for i, e in enumerate(shown):
        print("%-9s %-12s %-16s %s%s%s" % (e["version"], LEVEL_WORDS.get(e["level"], e["level"]),
                                          when(e["date"]), clip(e["summary"], 70),
                                          "  (built on %s)" % on[e["version"]] if e["version"] in on else "",
                                          "   <- now" if i == 0 else ""))
    if len(shown) < len(es):
        print("... %d older versions. Add --all to see them." % (len(es) - len(shown)))


def cmd_show(args) -> None:
    store = Store.find(Path(args.root or "."))
    e = store.by_label(args.version)
    files = store.manifest(e["manifest"])
    print("%s  %s" % (e["version"], LEVEL_WORDS.get(e["level"], e["level"])))
    print("Summary: %s" % e["summary"])
    if e.get("prompt"):
        print("Prompt:  %s" % e["prompt"])
    if e.get("reason"):
        print("Why:     %s" % e["reason"])
    if e.get("restored_from"):
        print("Same files as: %s" % e["restored_from"])
    if e["version"] in built_on(store):
        print("Built on: %s (the version you went back to before this)" % built_on(store)[e["version"]])
    print("Saved:   %s (%s)" % (e["date"].replace("T", " ")[:16], when(e["date"])))
    print("Before:  %s" % (e.get("parent") or "nothing (first version)"))
    print("Files:   %d (%s)" % (len(files), human_size(sum(f["size"] for f in files.values()))))
    ch = e.get("changes") or {"added": [], "modified": [], "deleted": []}
    if count_changes(ch):
        print("Changed: %s" % describe_changes(ch))
        for k in ("added", "modified", "deleted"):
            for p in ch[k][:40]:
                print("  %-9s %s" % (k, p))


def cmd_diff(args) -> None:
    store = Store.find(Path(args.root or "."))
    if args.a is None:
        a_label, b_label = "latest", None
    elif args.b is None:
        a_label, b_label = args.a, "latest"
    else:
        a_label, b_label = args.a, args.b

    def load(label):
        if label is None:
            files, _ = store.scan()
            return "unsaved", files, (lambda rel, meta: (store.root / rel).read_bytes())
        e = store.by_label(label)
        return e["version"], store.manifest(e["manifest"]), (lambda rel, meta: store.read_blob(meta["sha"]))

    an, af, aget = load(a_label)
    bn, bf, bget = load(b_label)
    ch = compare(af, bf)
    if args.path:
        keep = lambda p: matches_only(p, args.path)
        ch = {k: [p for p in v if keep(p)] for k, v in ch.items()}
    if not count_changes(ch):
        print("No differences between %s and %s." % (an, bn))
        return
    print("%s -> %s: %s" % (an, bn, describe_changes(ch)))
    stats, body = [], []
    for k, mark in (("added", "A"), ("modified", "M"), ("deleted", "D")):
        for rel in ch[k]:
            old = aget(rel, af[rel]) if rel in af else b""
            new = bget(rel, bf[rel]) if rel in bf else b""
            ot, nt = as_text(old), as_text(new)
            if ot is None or nt is None:
                stats.append("  %s %s  (binary, %s -> %s)" % (mark, rel, human_size(len(old)), human_size(len(new))))
                continue
            lines = list(difflib.unified_diff(ot.splitlines(), nt.splitlines(),
                                              "a/%s (%s)" % (rel, an), "b/%s (%s)" % (rel, bn), n=3, lineterm=""))
            plus = sum(1 for l in lines if l.startswith("+") and not l.startswith("+++"))
            minus = sum(1 for l in lines if l.startswith("-") and not l.startswith("---"))
            stats.append("  %s %s  +%d -%d" % (mark, rel, plus, minus))
            body.extend(lines)
    print("\n".join(stats))
    if args.stat or not body:
        return
    print()
    if len(body) > DIFF_LINE_LIMIT:
        print("\n".join(body[:DIFF_LINE_LIMIT]))
        print("... diff cut at %d lines. Add --path <file> to see one file." % DIFF_LINE_LIMIT)
    else:
        print("\n".join(body))


def as_text(data: bytes):
    if b"\0" in data[:8000]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def cmd_restore(args) -> None:
    store = Store.find(Path(args.root or "."))
    with store.lock():
        target = store.by_label(args.version)
        target_files = store.manifest(target["manifest"])
        working, skipped, ch = unsaved(store)
        notes = []
        if count_changes(ch) and working:  # an empty folder (e.g. a fresh chat) has nothing to keep
            e, _ = save_now(store, level="patch", summary=auto_summary(ch),
                            reason="Saved automatically before going back, so nothing is lost.", prompt="", by="auto")
            if e:
                notes.append("Unsaved changes were saved first as %s." % e["version"])
        if args.path:
            return restore_some(store, target, target_files, working, args, notes)
        if not count_changes(compare(working, target_files)):
            print("The project already matches %s. Nothing to do." % target["version"])
            return
        ch_out = compare(working, target_files)
        n, aside = write_files(store, target_files, working)
        if aside:
            notes.append(displaced_note(store, aside))
        if store.latest()["manifest"] == target["manifest"]:
            print("Wrote back the missing files of %s (%d file%s). It's still the current version, so no new "
                  "version was needed." % (target["version"], n, "" if n == 1 else "s"))
            for n_ in notes:
                print(n_)
            return
        after, after_skipped = store.scan()
        summary = "Went back to %s" % target["version"] + (": %s" % clip(args.note, 120) if args.note else "")
        e = record(store, after, after_skipped, level="restore", summary=summary,
                   reason="Restored the files of %s (%s)." % (target["version"], clip(target["summary"], 100)),
                   prompt=args.note or "", by="restore", restored_from=target["version"])
        if store.put_manifest(after) != target["manifest"]:
            notes.append("Some files differ from %s because of ignore rules or large-file limits." % target["version"])
    print("Went back to %s. Saved as %s. %d file%s changed." % (target["version"], e["version"], n, "" if n == 1 else "s"))
    for k in ("modified", "added", "deleted"):
        names = ch_out[k]
        if names:
            label = {"modified": "Changed back", "added": "Brought back", "deleted": "Removed (not in that version)"}[k]
            print("%s: %s" % (label, ", ".join(names[:15]) + (" ..." if len(names) > 15 else "")))
    for n_ in notes:
        print(n_)
    print("Before the next change, read the context for this version: handoff %s" % target["version"])


def restore_some(store: Store, target: dict, target_files: dict, working: dict, args, notes) -> None:
    """Brings back only some files from a version; everything else stays as it is now."""
    want = args.path
    if not any(matches_only(p, want) for p in list(target_files) + list(working)):
        raise Fail("None of %s exists in %s or in the current files." % (", ".join(want), target["version"]))
    new = {p: m for p, m in working.items() if not matches_only(p, want)}
    new.update({p: m for p, m in target_files.items() if matches_only(p, want)})
    ch = compare(working, new)
    if not count_changes(ch):
        print("Those files already match %s. Nothing to do." % target["version"])
        return
    _, aside = write_files(store, new, working)
    if aside:
        notes.append(displaced_note(store, aside))
    after, after_skipped = store.scan()
    names = ch["modified"] + ch["added"] + ch["deleted"]
    shown = ", ".join(p.rsplit("/", 1)[-1] for p in names[:3]) + (" (+%d more)" % (len(names) - 3) if len(names) > 3 else "")
    e = record(store, after, after_skipped, level=args.bump or "patch",
               summary="Brought back %s from %s" % (shown, target["version"]) + (": %s" % clip(args.note, 100) if args.note else ""),
               reason="Only these files were restored; everything else stayed as it was.",
               prompt=args.note or "", by="restore", extra={"files_from": target["version"]})
    print("Brought back %d file%s from %s: %s. Saved as %s; other files weren't touched." % (
        len(names), "" if len(names) == 1 else "s", target["version"], ", ".join(names[:15]), e["version"]))
    for n_ in notes:
        print(n_)


def cmd_handoff(args) -> None:
    store = Store.find(Path(args.root or "."))
    e = store.by_label(args.version)
    chain = lineage(store, e)
    in_chain = {x["version"] for x in chain}
    files = store.manifest(e["manifest"])
    out = ["# Continue from %s" % e["version"], "",
           "Project folder: %s. This version was saved %s." % (store.root.name, e["date"].replace("T", " ")[:16]), "",
           "Treat the files of %s as the current truth. Earlier instructions that aren't in the list below "
           "were dropped; don't bring them back unless the user asks." % e["version"], "",
           "## How this version came together", ""]
    for x in chain:
        if x["level"] == "restore":
            continue
        line = "- %s %s: %s" % (x["version"], LEVEL_WORDS.get(x["level"]), x["summary"])
        if x.get("prompt"):
            line += ' (asked: "%s")' % clip(x["prompt"], 200)
        out.append(line)
    dropped = [x for x in reversed(store.entries()) if x["version"] not in in_chain and x["level"] != "restore"]
    if dropped:
        out += ["", "## Not part of this version", ""]
        for x in dropped[:15]:
            out.append("- %s %s: %s" % (x["version"], LEVEL_WORDS.get(x["level"]), x["summary"]))
        if len(dropped) > 15:
            out.append("- ... and %d more" % (len(dropped) - 15))
    out += ["", "## Files (%d)" % len(files), ""]
    for rel in sorted(files)[:60]:
        out.append("- %s (%s)" % (rel, human_size(files[rel]["size"])))
    if len(files) > 60:
        out.append("- ... and %d more" % (len(files) - 60))
    print("\n".join(out))


def cmd_export(args) -> None:
    store = Store.find(Path(args.root or "."))
    e = store.by_label(args.version)
    files = store.manifest(e["manifest"])
    out = Path(args.out).resolve()
    if out.suffix.lower() == ".zip":
        out.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(str(out), "w", zipfile.ZIP_DEFLATED) as z:
            for rel, meta in sorted(files.items()):
                if safe_rel(rel):
                    z.writestr(rel, store.read_blob(meta["sha"]))
    else:
        if out.exists() and any(out.iterdir()):
            raise Fail("%s isn't empty. Pick a new folder or a .zip file." % out)
        for rel, meta in files.items():
            if safe_rel(rel):
                write_atomic(out / rel, store.read_blob(meta["sha"]))
    print("Exported %s (%d files) to %s" % (e["version"], len(files), out))


def cmd_backup(args) -> None:
    store = Store.find(Path(args.root or "."))
    out = Path(args.out).resolve()
    if store.dir in out.parents:
        raise Fail("Save the backup outside %s." % STORE)
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(str(out), "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(store.dir.rglob("*")):
            # displaced/ holds this computer's own safety copies (maybe secrets like .env): never shared
            if p.relative_to(store.dir).parts[0] == "displaced":
                continue
            if p.is_file() and p.name not in (".lock", "cache.json", "timeline.html") and not p.name.startswith("."):
                z.write(str(p), (STORE + "/" + p.relative_to(store.dir).as_posix()))
    print("Backed up %d versions to %s" % (len(store.entries()), out))


def cmd_import(args) -> None:
    root = Path(args.root or ".").resolve()
    if (root / STORE / "entries").is_dir() and any((root / STORE / "entries").iterdir()):
        raise Fail("This folder already has a version history. Import into an empty folder instead.")
    src = Path(args.backup).resolve()
    with zipfile.ZipFile(str(src)) as z:
        names = z.namelist()
        if not any(n == STORE + "/config.json" for n in names):
            raise Fail("%s isn't an ai-versions backup." % src.name)
        files = [n for n in names if not n.endswith("/")]
        for n in files:
            if not n.startswith(STORE + "/") or not plain_rel(n):
                raise Fail("Unsafe path in backup: %s. Nothing was imported." % n)
        # Every version's file list must be safe too, or a restore could plant files later.
        for n in files:
            if n.startswith(STORE + "/manifests/") and n.endswith(".json"):
                try:
                    paths = list(json.loads(z.read(n).decode("utf-8")))
                except Exception:
                    raise Fail("Broken file list in backup: %s. Nothing was imported." % n)
                bad = [x for x in paths if not safe_rel(x)]
                if bad:
                    raise Fail("This backup would write %s, which isn't allowed. Nothing was imported." % bad[0])
        for n in files:
            write_atomic(root / n, z.read(n))
    store = Store(root)
    last = store.latest()
    files = store.manifest(last["manifest"])
    written = 0
    for rel, meta in files.items():
        dest = root / rel
        if safe_rel(rel) and not dest.exists():
            write_atomic(dest, store.read_blob(meta["sha"]))
            if os.name != "nt" and meta["x"]:
                dest.chmod(dest.stat().st_mode | 0o111)
            written += 1
    exclude_from_git(root)
    try:
        shutil.copyfile(__file__, str(root / STORE / "aiv.py"))
    except Exception:
        pass
    print("Imported %d versions. Current version: %s. Wrote %d missing file%s; existing files were left alone." % (
        len(store.entries()), last["version"], written, "" if written == 1 else "s"))


def cmd_doctor(args) -> None:
    store = Store.find(Path(args.root or "."))
    problems = 0
    for e in store.entries():
        try:
            for rel, meta in store.manifest(e["manifest"]).items():
                if not store.obj_path(meta["sha"]).exists():
                    print("%s: content of %s is missing" % (e["version"], rel))
                    problems += 1
        except Fail as f:
            print("%s: %s" % (e["version"], f))
            problems += 1
    store.write_history()
    try:
        shutil.copyfile(__file__, str(store.dir / "aiv.py"))
    except Exception:
        pass
    print("Checked %d versions: %s." % (len(store.entries()), "all good" if not problems else "%d problems" % problems))


def cmd_view(args) -> None:
    store = Store.find(Path(args.root or "."))
    data, on = [], built_on(store)
    for e in reversed(store.entries()):
        ch = e.get("changes") or {"added": [], "modified": [], "deleted": []}
        data.append({"v": e["version"], "level": e["level"], "word": LEVEL_WORDS.get(e["level"], e["level"]),
                     "summary": e["summary"], "prompt": e.get("prompt", ""), "reason": e.get("reason", ""),
                     "date": e["date"], "from": e.get("restored_from"), "on": on.get(e["version"]), "changes": ch})
    out = Path(args.out).resolve() if args.out else store.dir / "timeline.html"
    page = TIMELINE_HTML.replace("__TITLE__", html.escape(store.root.name)).replace(
        "__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    write_atomic(out, page.encode("utf-8"))
    print("Wrote the timeline page: %s" % out)


def merge_json(path: Path, mutate) -> bool:
    data = {}
    if path.is_file():
        try:
            data = json.loads(path.read_text("utf-8") or "{}")
        except Exception:
            raise Fail("%s isn't valid JSON. Fix it first, then run this again." % path)
    changed = mutate(data)
    if changed:
        write_atomic(path, (json.dumps(data, indent=2) + "\n").encode("utf-8"))
    return changed


def cmd_install_hooks(args) -> None:
    store = Store.find(Path(args.root or "."))
    shutil.copyfile(__file__, str(store.dir / "aiv.py"))
    py = "py" if os.name == "nt" else "python3"  # not this machine's own path: hook files get shared
    if args.tool == "claude-code":
        cmd = '%s "$CLAUDE_PROJECT_DIR/%s/aiv.py" auto --quiet' % (py, STORE)
        path = store.root / ".claude" / "settings.local.json"

        def mutate(d):
            stops = d.setdefault("hooks", {}).setdefault("Stop", [])
            if any("aiv.py" in h.get("command", "") for s in stops for h in s.get("hooks", [])):
                return False
            stops.append({"hooks": [{"type": "command", "command": cmd, "timeout": 60}]})
            return True
    else:
        cmd = '%s %s/aiv.py auto --quiet' % (py, STORE)
        path = store.root / ".cursor" / "hooks.json"

        def mutate(d):
            d.setdefault("version", 1)
            stops = d.setdefault("hooks", {}).setdefault("stop", [])
            if any("aiv.py" in h.get("command", "") for h in stops):
                return False
            stops.append({"command": cmd, "timeout": 60})
            return True
    changed = merge_json(path, mutate)
    print(("Added an auto-save hook to %s." if changed else "The auto-save hook is already in %s.") % path.relative_to(store.root))
    print("From now on, any change the AI forgets to save is saved as a Small tweak when it finishes.")
    if args.tool == "cursor":
        print("Note: .cursor/hooks.json is usually committed. Teammates without ai-versions just see the hook do nothing.")


def cmd_setup_github(args) -> None:
    root = Path(args.root or ".").resolve()
    assets = Path(__file__).resolve().parent.parent / "assets" / "github-layer"
    if not assets.is_dir():
        raise Fail("Run this from the skill's scripts folder; the copy inside %s doesn't include the GitHub files." % STORE)
    if (root / STORE / "config.json").is_file():
        raise Fail("This project already keeps versions locally (files mode). Use one or the other, not both.")
    copied = []
    for src in sorted(assets.rglob("*")):
        if src.is_dir():
            continue
        rel = src.relative_to(assets).as_posix()
        # Stored without leading dots so every skill installer keeps them.
        if rel.startswith("github/"):
            rel = "." + rel
        elif rel.startswith("ai-versions/"):
            rel = "." + rel
        if rel.startswith("pill/"):
            if not args.with_pill:
                continue
            rel = "src/components/" + src.name
        dest = root / rel
        if dest.exists() and dest.read_bytes() == src.read_bytes():
            continue
        if dest.exists() and rel == STORE + "/pending.json":
            continue
        write_atomic(dest, src.read_bytes())
        copied.append(rel)
    print("Added the GitHub version files:" if copied else "The GitHub version files are already here.")
    for c in copied:
        print("  " + c)
    print("Commit and push them. The workflow file runs on the next push and creates v1.0.0.")


# ---------------------------------------------------------------- timeline page

TIMELINE_HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__ versions</title>
<style>
:root{--bg:#fff;--ink:#1c1f24;--muted:#6b717c;--line:#e3e6ea;--hover:#f3f5f7;--major:#b4236b;--minor:#4c51bf;--patch:#8a919c;--restore:#0f8b7f;--start:#1c1f24}
@media (prefers-color-scheme:dark){:root{--bg:#141619;--ink:#eceef1;--muted:#9aa1ab;--line:#2a2e35;--hover:#1d2025;--major:#f06aa8;--minor:#8f93f2;--patch:#7d848f;--restore:#3cc4b6;--start:#eceef1}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:720px;margin:0 auto;padding:40px 16px 64px}
h1{font-size:22px;margin:0 0 4px}p.sub{margin:0 0 28px;color:var(--muted)}
ol{list-style:none;margin:0;padding:0}
li{display:grid;grid-template-columns:24px 1fr;gap:0 14px;padding:12px 10px;border-radius:10px;cursor:pointer}
li:hover,li:focus-visible{background:var(--hover);outline:none}
.rail{position:relative;display:flex;justify-content:center}
.rail:before{content:"";position:absolute;top:-12px;bottom:-12px;left:50%;width:2px;margin-left:-1px;background:var(--line)}
li:first-child .rail:before{top:14px}li:last-child .rail:before{bottom:calc(100% - 14px)}
.dot{position:relative;border-radius:50%;background:var(--c);margin-top:7px;width:8px;height:8px}
.l-major .dot{width:16px;height:16px;margin-top:3px}.l-minor .dot{width:12px;height:12px;margin-top:5px}
.l-restore .dot{width:13px;height:13px;margin-top:5px;background:var(--bg);border:3px solid var(--c)}
.top{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}.v{font-weight:600;font-variant-numeric:tabular-nums}
.w{font-size:13px;color:var(--c)}.now{font-size:12px;font-weight:600;padding:1px 8px;border-radius:999px;background:var(--hover)}
time{margin-left:auto;font-size:13px;color:var(--muted)}.p{color:var(--muted);font-size:14px;margin-top:2px}
.more{display:none;margin-top:8px;font-size:13px;color:var(--muted);border-left:2px solid var(--line);padding-left:10px}
li.open .more{display:block}.more code{font-size:12px}
</style></head><body><main>
<h1>__TITLE__</h1><p class="sub" id="sub"></p><ol id="list"></ol></main>
<script>
const data=__DATA__;
const colors={major:"var(--major)",minor:"var(--minor)",patch:"var(--patch)",restore:"var(--restore)",start:"var(--start)"};
const esc=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const fmt=iso=>{const d=new Date(iso);return isNaN(d)?"":d.toLocaleString(undefined,{day:"numeric",month:"short",year:"numeric",hour:"numeric",minute:"2-digit"})};
document.getElementById("sub").textContent=data.length+" versions. Click one to see details.";
document.getElementById("list").innerHTML=data.map((e,i)=>{const ch=e.changes||{};const files=["added","modified","deleted"].flatMap(k=>(ch[k]||[]).map(p=>k+" <code>"+esc(p)+"</code>"));
return `<li tabindex="0" class="l-${esc(e.level)}" style="--c:${colors[e.level]||colors.patch}"><span class="rail"><span class="dot"></span></span><div>
<div class="top"><span class="v">${esc(e.v)}</span><span class="w">${esc(e.word)}</span>${i===0?'<span class="now">Now</span>':""}<time>${esc(fmt(e.date))}</time></div>
<div>${esc(e.summary)}</div>${e.on?`<div class="p">Built on ${esc(e.on)}</div>`:""}${e.prompt?`<div class="p">“${esc(e.prompt)}”</div>`:""}
<div class="more">${e.from?`<div>Same files as ${esc(e.from)}</div>`:""}${e.reason?`<div>${esc(e.reason)}</div>`:""}${files.length?`<div>${files.slice(0,40).join("<br>")}</div>`:""}</div></div></li>`}).join("");
document.querySelectorAll("li").forEach(li=>{const t=()=>li.classList.toggle("open");li.onclick=t;li.onkeydown=ev=>{if(ev.key==="Enter"||ev.key===" "){ev.preventDefault();t()}}});
</script></body></html>
"""


# ---------------------------------------------------------------- CLI

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="aiv.py", description="Every change gets a version. Nothing is ever deleted.")
    ap.add_argument("--root", help="project folder (default: this folder or the nearest parent with a history)")
    sub = ap.add_subparsers(dest="cmd", metavar="<command>")

    def add(name, fn, help_):
        p = sub.add_parser(name, help=help_, description=help_)
        p.add_argument("--root", help=argparse.SUPPRESS, default=argparse.SUPPRESS)
        p.set_defaults(fn=fn)
        return p

    p = add("init", cmd_init, "start a version history here and save v1.0.0")
    p.add_argument("--only", nargs="+", metavar="PATH", help="only version these files or folders")
    p.add_argument("--summary", help="what v1.0.0 is (default: Versioning switched on)")
    p.add_argument("--allow-large", action="store_true", help="allow more than 5000 files or 500 MB")
    p.add_argument("--force", action="store_true", help=argparse.SUPPRESS)

    p = add("save", cmd_save, "save the current files as a new version")
    p.add_argument("--bump", required=True, choices=BUMPS, help="patch = small tweak, minor = new feature, major = big change")
    p.add_argument("--summary", required=True, help="one line: what changed")
    p.add_argument("--reason", help="one line: why this level")
    p.add_argument("--prompt", help="the user's request, shortened")

    p = add("auto", cmd_auto, "for hooks: save unsaved changes as a small tweak; never fails")
    p.add_argument("--quiet", action="store_true")

    add("status", cmd_status, "current version and unsaved changes")

    p = add("list", cmd_list, "list versions, newest first")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--all", action="store_true")
    p.add_argument("--json", action="store_true")

    p = add("show", cmd_show, "details of one version")
    p.add_argument("version")

    p = add("diff", cmd_diff, "compare: diff (unsaved), diff A (A to latest), diff A B; vX^ = the version before vX")
    p.add_argument("a", nargs="?")
    p.add_argument("b", nargs="?")
    p.add_argument("--stat", action="store_true", help="only list changed files")
    p.add_argument("--path", nargs="+", help="only these files or folders")

    p = add("restore", cmd_restore, "go back to a version (saved as a new version; unsaved work is saved first)")
    p.add_argument("version", help="v1.2.0, prev, or vX^")
    p.add_argument("--note", help="why you're going back")
    p.add_argument("--path", nargs="+", metavar="PATH", help="bring back only these files or folders")
    p.add_argument("--bump", choices=BUMPS, help="level for a --path restore (default: patch)")

    p = add("handoff", cmd_handoff, "clean context for continuing from a version (e.g. in a new chat)")
    p.add_argument("version", nargs="?", default="latest")

    p = add("view", cmd_view, "write an HTML timeline of all versions")
    p.add_argument("--out", help="where to write it (default: .ai-versions/timeline.html)")

    p = add("export", cmd_export, "copy the files of a version to a folder or .zip")
    p.add_argument("version")
    p.add_argument("--out", required=True)

    p = add("backup", cmd_backup, "pack the whole history into a .zip (to move it to another tool or chat)")
    p.add_argument("--out", required=True)

    p = add("import", cmd_import, "unpack a backup .zip into an empty project folder")
    p.add_argument("backup")

    p = add("install-hooks", cmd_install_hooks, "auto-save anything the AI forgets (Claude Code or Cursor)")
    p.add_argument("tool", choices=("claude-code", "cursor"))

    p = add("setup-github", cmd_setup_github, "add the GitHub version layer (for Lovable, Bolt, v0 repos)")
    p.add_argument("--with-pill", action="store_true", help="also add src/components/VersionPill.tsx")

    add("doctor", cmd_doctor, "check the history for missing pieces and rebuild HISTORY.md")

    args = ap.parse_args(argv)
    if not getattr(args, "fn", None):
        ap.print_help()
        return 1
    try:
        args.fn(args)
        return 0
    except Fail as f:
        print("Error: %s" % f, file=sys.stderr)
        return f.code
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
