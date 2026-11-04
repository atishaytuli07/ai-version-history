import json, os, shutil, stat, subprocess, sys, tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def rmtree(path):
    """Delete a folder, including git's read-only object files on Windows."""
    def writable(func, p, _exc):
        os.chmod(p, stat.S_IWRITE)
        func(p)
    if not os.path.exists(path):
        return
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=writable)
    else:
        shutil.rmtree(path, onerror=writable)

ASSETS = Path(sys.argv[1]).resolve()
T = Path(tempfile.mkdtemp())
env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
results = []


def sh(*a, cwd, ok=True, extra=None):
    p = subprocess.run(list(a), cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace", env={**env, **(extra or {})})
    if ok and p.returncode:
        raise AssertionError("%s\n%s%s" % (a, p.stdout, p.stderr))
    return p


def check(name, cond, detail=""):
    results.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  <- " + str(detail)[:500]))


sh("git", "init", "-q", "--bare", "-b", "main", "remote.git", cwd=T)
hook = T / "remote.git/hooks/pre-receive"
hook.write_text("""#!/bin/sh
# Like GitHub: the workflow token may not change workflow files. A test can also block all bot pushes.
[ -z "$AIV_BOT" ] && exit 0
[ -f "$GIT_DIR/block-bot" ] && { echo "blocked by test" >&2; exit 1; }
while read old new ref; do
  case "$ref" in refs/heads/*) ;; *) continue;; esac
  if git diff --name-only "$old" "$new" 2>/dev/null | grep -q '^.github/workflows/'; then
    echo "refusing to allow a GitHub App to create or update workflow without workflows permission" >&2; exit 1
  fi
done
exit 0
""")
hook.chmod(0o755)
sh("git", "clone", "-q", "remote.git", "lov", cwd=T)
L = T / "lov"
sh("git", "checkout", "-q", "-b", "main", cwd=L)
for f in ASSETS.rglob("*"):
    if f.is_file() and not f.relative_to(ASSETS).as_posix().startswith("pill/"):
        d = L / f.relative_to(ASSETS); d.parent.mkdir(parents=True, exist_ok=True); shutil.copy(f, d)
(L / "index.html").write_text("start\n")
log = []


def action(before, after=None, notes=None):
    """Simulates the AI Versions workflow run (GITHUB_TOKEN pushes are marked as the bot)."""
    run = T / "run"
    rmtree(run)
    sh("git", "clone", "-q", str(T / "remote.git"), "run", cwd=T)
    sh("git", "fetch", "-q", "--tags", "--force", cwd=run)
    if after:
        sh("git", "checkout", "-q", "--detach", after, cwd=run)
    after = sh("git", "rev-parse", "HEAD", cwd=run).stdout.strip()
    extra = {"AFTER": after, "BRANCH": "main", "NO_RELEASE": "1", "AIV_BOT": "1"}
    if notes: extra["PILL_NOTES"] = notes
    p = sh("node", ".github/scripts/ai-version.mjs", cwd=run, ok=False, extra=extra)
    log.append(p.stdout + p.stderr)
    return p


def push(msg):
    before = sh("git", "rev-parse", "-q", "--verify", "origin/main", cwd=L, ok=False).stdout.strip() or "0" * 40
    sh("git", "add", "-A", cwd=L); sh("git", "commit", "-qm", msg, cwd=L); sh("git", "push", "-q", "origin", "main", cwd=L)
    p = action(before)
    sh("git", "pull", "-q", "--ff-only", "origin", "main", cwd=L); sh("git", "fetch", "-q", "--tags", "--force", cwd=L)
    return p


def change(text, bump, summary):
    (L / "index.html").write_text(text + "\n")
    (L / ".ai-versions/pending.json").write_text(json.dumps({"bump": bump, "summary": summary, "reason": "r", "prompt": summary}))
    return push(summary)


def ask_restore(version, also_pending=False, also_code=None):
    (L / ".ai-versions/restore.json").write_text(json.dumps({"version": version, "note": "asked in test"}))
    if also_pending:
        (L / ".ai-versions/pending.json").write_text(json.dumps({"bump": "minor", "summary": "Going back", "reason": "x", "prompt": "go back"}))
    if also_code:
        (L / "index.html").write_text(also_code + "\n")
    return push("Restore request " + version)


tags = lambda: sh("git", "tag", "-l", "v*", "--sort=v:refname", cwd=L).stdout.split()
body = lambda t: json.loads(sh("git", "tag", "-l", "--format=%(contents:body)", t, cwd=L).stdout)
ledger = lambda: json.loads((L / "public/ai-versions.json").read_text())
code = lambda: (L / "index.html").read_text().strip()
code_at = lambda t: sh("git", "show", "%s:index.html" % t, cwd=L).stdout.strip()

push("install")
change("A", "patch", "A")            # v1.0.1
change("B", "minor", "B")            # v1.1.0
change("C", "major", "C")            # v2.0.0
change("D", "minor", "D")            # v2.1.0
check("setup versions", tags() == ["v1.0.0", "v1.0.1", "v1.1.0", "v2.0.0", "v2.1.0"], tags())

# 1. plain chat restore
ask_restore("v1.1.0")
t = tags()[-1]
check("1 chat restore brings back the exact code", code() == "B" and t == "v2.2.0" and body(t)["restored_from"] == "v1.1.0", (code(), t, log[-1]))
check("1 request file is removed afterwards", not (L / ".ai-versions/restore.json").exists())
check("1 the request commit itself made no version", len(tags()) == 6, tags())
check("1 kit files like pending.json are not rolled back", json.loads((L / ".ai-versions/pending.json").read_text())["summary"] == "D")

# 2. changes after going back are 'built on' that version
change("B2", "patch", "B2")
lg = {v["version"]: v for v in ledger()["versions"]}
check("2 next change continues numbering from the top", tags()[-1] == "v2.2.1", tags())
check("2 it is marked built on v1.1.0", lg["v2.2.1"]["built_on"] == "v1.1.0" and lg["v2.2.0"]["built_on"] is None and lg["v2.1.0"]["built_on"] is None, lg)

# 3. AI also rewrote pending.json in the request commit
ask_restore("v2.1.0", also_pending=True)
check("3 request with pending.json is still just a request", code() == "D" and body(tags()[-1])["restored_from"] == "v2.1.0" and len(tags()) == 8, (tags(), log[-1]))
change("D2", "patch", "D2")
check("3 going back to the newest line resets 'built on'", ledger()["versions"][0]["built_on"] == "v2.1.0")

# 4. request + a real code change in the same commit: the change is kept as a version first
ask_restore("v1.0.1", also_code="E")
tg = tags()
check("4 the code change got its own version, then the restore", body(tg[-2])["summary"] != "" and code_at(tg[-2]) == "E" and code() == "A" and body(tg[-1])["restored_from"] == "v1.0.1", (tg[-3:], log[-1]))

# 5. unknown version
n = len(tags())
ask_restore("v9.9.9")
check("5 unknown version: no new version, request removed", len(tags()) == n and not (L / ".ai-versions/restore.json").exists(), log[-1])
check("5 the pill gets a notice", "doesn't exist" in ledger().get("notice", {}).get("text", ""), ledger().get("notice"))
change("F", "patch", "F")
check("5 the notice goes away with the next change", "notice" not in ledger())

# 6. number without the v
ask_restore("1.1.0")
check("6 '1.1.0' works like 'v1.1.0'", code() == "B" and body(tags()[-1])["restored_from"] == "v1.1.0")

# 7. asking for the version you're already on
n = len(tags())
ask_restore(tags()[-1])
check("7 already there: no new version, notice says so", len(tags()) == n and "Already at" in ledger().get("notice", {}).get("text", ""), (log[-1], ledger().get("notice")))

# 8. Lovable pushes another change right after the request, before the workflow runs
(L / ".ai-versions/restore.json").write_text(json.dumps({"version": "v2.0.0"}))
sh("git", "add", "-A", cwd=L); sh("git", "commit", "-qm", "request", cwd=L)
before = sh("git", "rev-parse", "origin/main", cwd=L).stdout.strip()
sh("git", "push", "-q", "origin", "main", cwd=L)
(L / "other.txt").write_text("sneaky\n"); sh("git", "add", "-A", cwd=L); sh("git", "commit", "-qm", "sneaky", cwd=L); sh("git", "push", "-q", "origin", "main", cwd=L)
action(before)
sh("git", "pull", "-q", "--ff-only", "origin", "main", cwd=L); sh("git", "fetch", "-q", "--tags", "--force", cwd=L)
check("8 a request followed by newer work is dropped, not applied", code() != "C" and not (L / ".ai-versions/restore.json").exists() and "dropped" in ledger().get("notice", {}).get("text", ""), (code(), log[-1][-300:]))
vs = tags(); check("8 no duplicate version numbers", len(vs) == len(set(vs)))

# 9. manual AI Restore workflow clears a pending chat request
(L / ".ai-versions/restore.json").write_text(json.dumps({"version": "v1.0.1"}))
sh("git", "add", "-A", cwd=L); sh("git", "commit", "-qm", "request not processed yet", cwd=L); sh("git", "push", "-q", "origin", "main", cwd=L)
run = T / "run2"; rmtree(run); sh("git", "clone", "-q", str(T / "remote.git"), "run2", cwd=T); sh("git", "fetch", "-q", "--tags", cwd=run)
out = run / "out.txt"
sh("node", ".github/scripts/ai-restore.mjs", cwd=run, extra={"VERSION": "v1.1.0", "BRANCH": "main", "GITHUB_OUTPUT": str(out)})
o = dict(l.split("=", 1) for l in out.read_text().split())
sh("node", ".github/scripts/ai-version.mjs", cwd=run, extra={"BEFORE": o["before"], "AFTER": o["after"], "BRANCH": "main", "NO_RELEASE": "1"})
sh("git", "pull", "-q", "--ff-only", "origin", "main", cwd=L); sh("git", "fetch", "-q", "--tags", "--force", cwd=L)
check("9 manual restore wins and clears the old request", code() == "B" and not (L / ".ai-versions/restore.json").exists() and body(tags()[-1])["restored_from"] == "v1.1.0", tags()[-3:])

# 11. a workflow edit after the target version: restore must keep the current kit
wf = L / ".github/workflows/ai-versions.yml"
wf.write_text(wf.read_text().replace("cancel-in-progress: false", "cancel-in-progress: false # edited by user"))
n = len(tags()); push("Change a workflow setting")
check("11 a kit-only change makes no version", len(tags()) == n, tags()[-2:])
ask_restore("v1.0.1")
check("11 restore to a version from before the workflow edit works", code() == "A" and body(tags()[-1])["restored_from"] == "v1.0.1", log[-1][-400:])
check("11 the workflow file keeps its newest content", "# edited by user" in wf.read_text())
(L / "src").mkdir(exist_ok=True); (L / "src/VersionPill.tsx").write_text("// pill v2\n"); push("pill update")
ask_restore("v1.1.0")
check("11 the version button file is never rolled back", (L / "src/VersionPill.tsx").read_text() == "// pill v2\n" and code() == "B")

# 12. GitHub cancels a queued run: the next run catches up
b0 = sh("git", "rev-parse", "origin/main", cwd=L).stdout.strip()
(L / "index.html").write_text("G1\n"); (L / ".ai-versions/pending.json").write_text(json.dumps({"bump": "patch", "summary": "G1", "reason": "r", "prompt": "g1"}))
sh("git", "add", "-A", cwd=L); sh("git", "commit", "-qm", "G1", cwd=L); sh("git", "push", "-q", "origin", "main", cwd=L)
(L / "index.html").write_text("G2\n"); (L / ".ai-versions/pending.json").write_text(json.dumps({"bump": "minor", "summary": "G2", "reason": "r", "prompt": "g2"}))
sh("git", "add", "-A", cwd=L); sh("git", "commit", "-qm", "G2", cwd=L); sh("git", "push", "-q", "origin", "main", cwd=L)
n = len(tags()); action(b0)   # only the second push's run happens
sh("git", "pull", "-q", "--ff-only", "origin", "main", cwd=L); sh("git", "fetch", "-q", "--tags", "--force", cwd=L)
check("12 both pushes got versions although one run was cancelled", len(tags()) == n + 2 and [body(t)["summary"] for t in tags()[-2:]] == ["G1", "G2"], log[-1])

# 13. a go-back request whose run failed is dropped later, never applied over newer work
(T / "remote.git/block-bot").write_text("x")
ask_restore("v1.0.1")
check("13 a failed restore makes the run fail visibly", "Could not apply" in log[-1] and code() != "A", log[-1][-300:])
(T / "remote.git/block-bot").unlink()
change("H", "patch", "H after the failed request")
check("13 the old request is dropped, not applied", code() == "H" and not (L / ".ai-versions/restore.json").exists() and "dropped" in ledger().get("notice", {}).get("text", ""), (code(), ledger().get("notice")))

# 14. prompts stay out of the list unless switched on
check("14 prompts are off by default", all(v["note"] == "" for v in ledger()["versions"]))
change("I", "patch", "I with notes"); action(sh("git", "rev-parse", "HEAD", cwd=L).stdout.strip(), notes="yes")
sh("git", "pull", "-q", "--ff-only", "origin", "main", cwd=L)
check("14 PILL_NOTES=yes shows them", any(v["note"] for v in ledger()["versions"]))

# 10. ledger sanity
lg = ledger()["versions"]
check("10 list has every version, newest first", [v["version"] for v in lg] == tags()[::-1])
# 29. reusing an old pending.json for a NEW edit is not a restore
kit_tags = lambda: [t for t in tags() if "kind" in sh("git", "tag", "-l", "--format=%(contents:body)", t, cwd=L).stdout]
first_with_pending = next(t for t in kit_tags() if sh("git", "cat-file", "-e", "%s:.ai-versions/pending.json" % t, cwd=L, ok=False).returncode == 0)
(L / ".ai-versions/pending.json").write_text(sh("git", "show", "%s:.ai-versions/pending.json" % first_with_pending, cwd=L).stdout)
(L / "index.html").write_text("brand-new content\n")
push("new edit with an old pending.json")
check("29 an old pending.json on a new edit is not called a restore", body(kit_tags()[-1])["kind"] != "restore", body(kit_tags()[-1]))

# 30. a vX.Y.Z tag the kit didn't make (npm version, a release tool) is ignored
before_kit = kit_tags()[-1]
sh("git", "tag", "v50.0.0", cwd=L); sh("git", "push", "-q", "origin", "v50.0.0", cwd=L)
change("after a foreign tag", "patch", "After a foreign tag")
newest = kit_tags()[-1]
check("30 foreign tags don't change the numbering", newest != "v50.0.1" and newest.startswith(before_kit.rsplit(".", 1)[0] + "."), (before_kit, newest))
check("30 foreign tags stay out of the version list", "v50.0.0" not in [v["version"] for v in ledger()["versions"]])

print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
