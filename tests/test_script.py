import json, os, shutil, subprocess, sys, tempfile, threading, zipfile
from pathlib import Path

# Windows consoles default to a legacy code page; the suite prints and reads UTF-8.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AIV = os.path.abspath(sys.argv[1])
PY = sys.executable
results = []


def run(*args, cwd, env=None, stdin=None, ok=True):
    e = dict(os.environ)
    e.pop("CLAUDE_PROJECT_DIR", None); e.pop("CURSOR_PROJECT_DIR", None)
    if env: e.update(env)
    p = subprocess.run([PY, AIV, *args], cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace", env=e, input=stdin)
    if ok and p.returncode != 0:
        raise AssertionError("command failed: %s\n%s%s" % (args, p.stdout, p.stderr))
    return p


def check(name, cond, detail=""):
    results.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  <- " + str(detail)[:400]))


def versions(root):
    return [e["version"] for e in json.loads(run("list", "--json", "--all", cwd=root).stdout)][::-1]


def entry(root, v):
    return json.loads((root / ".ai-versions/entries" / (v + ".json")).read_text(encoding="utf-8"))


def w(root, rel, text):
    p = root / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text, encoding="utf-8")


base = Path(tempfile.mkdtemp())

# ---------------- A. plain folder (no git)
A = base / "site"; A.mkdir()
w(A, "index.html", "<h1>Hi</h1>\n"); w(A, "css/app.css", "body{}\n")
w(A, "node_modules/x/index.js", "x"); w(A, ".env", "SECRET=1"); w(A, "dist/out.js", "built")
r = run("init", cwd=A)
m = json.loads((A / ".ai-versions/manifests" / (entry(A, "v1.0.0")["manifest"] + ".json")).read_text(encoding="utf-8"))
check("init creates v1.0.0", versions(A) == ["v1.0.0"], r.stdout)
check("init skips node_modules, dist and .env without git", sorted(m) == ["css/app.css", "index.html"], sorted(m))
check("init copies the script into the store", (A / ".ai-versions/aiv.py").is_file())
check("init again is harmless", "Already set up" in run("init", cwd=A).stdout)

w(A, "index.html", "<h1>Hello</h1>\n")
r = run("save", "--bump", "patch", "--summary", "Heading text", "--prompt", "change heading", cwd=A)
check("patch -> v1.0.1", "Saved v1.0.1 (Small tweak)" in r.stdout, r.stdout)
r = run("save", "--bump", "patch", "--summary", "Nothing", cwd=A)
check("save with no changes saves nothing", "No changes since v1.0.1" in r.stdout and versions(A)[-1] == "v1.0.1", r.stdout)

w(A, "pricing.html", "<section>Pricing</section>\n")
r = run("save", "--bump", "minor", "--summary", "Add pricing page", cwd=A)
check("minor -> v1.1.0", "Saved v1.1.0 (New feature)" in r.stdout, r.stdout)
check("changes recorded", entry(A, "v1.1.0")["changes"]["added"] == ["pricing.html"])

os.remove(A / "pricing.html"); w(A, "index.html", "<main>Redesign</main>\n"); w(A, "css/app.css", "body{background:#000}\n")
r = run("save", "--bump", "major", "--summary", "Dark redesign", cwd=A)
check("major -> v2.0.0", "Saved v2.0.0 (Big change)" in r.stdout, r.stdout)

# editing files back to exactly v1.1.0 is detected as going back
w(A, "index.html", "<h1>Hello</h1>\n"); w(A, "css/app.css", "body{}\n"); w(A, "pricing.html", "<section>Pricing</section>\n")
r = run("save", "--bump", "patch", "--summary", "undo redesign by hand", cwd=A)
e = entry(A, "v2.1.0")
check("identical-to-old save becomes 'Went back'", e["level"] == "restore" and e["restored_from"] == "v1.1.0", r.stdout)

# restore with unsaved work: work is saved first, then files go back
w(A, "index.html", "<h1>Unsaved idea</h1>\n"); w(A, "new/deep/file.txt", "deep")
r = run("restore", "v1.0.1", "--note", "client liked the first one", cwd=A)
vs = versions(A)
check("restore saves unsaved work first", entry(A, "v2.1.1")["by"] == "auto", vs)
check("restore is a new version", vs[-1] == "v2.2.0" and entry(A, "v2.2.0")["restored_from"] == "v1.0.1", (vs, r.stdout))
check("restore wrote the old files", (A / "index.html").read_text(encoding="utf-8") == "<h1>Hello</h1>\n" and not (A / "pricing.html").exists())
check("restore removed files that didn't exist then, and empty folders", not (A / "new").exists())
check("restore left ignored files alone", (A / "node_modules/x/index.js").exists() and (A / ".env").exists())
check("restore suggests handoff", "handoff v1.0.1" in r.stdout, r.stdout)
r = run("restore", "v1.0.1", cwd=A)
check("restore to the same state does nothing", "already matches" in r.stdout and versions(A)[-1] == "v2.2.0", r.stdout)
r = run("restore", "prev", cwd=A)
check("restore prev works", versions(A)[-1] == "v2.3.0" and entry(A, "v2.3.0")["restored_from"] == "v2.1.1", r.stdout)
check("unsaved work is recoverable", "Unsaved idea" in (A / "index.html").read_text(encoding="utf-8"))
r = run("restore", "v1.1.0^", cwd=A)
check("vX^ means the version before", entry(A, versions(A)[-1])["restored_from"] == "v1.0.1", r.stdout)

# partial restore: only some files come back, the rest stay
w(A, "notes.txt", "new note\n"); w(A, "css/app.css", "body{color:purple}\n")
run("save", "--bump", "patch", "--summary", "purple + note", cwd=A)
v_before = versions(A)[-1]
r = run("restore", "v2.0.0", "--path", "css/app.css", cwd=A)
e = entry(A, versions(A)[-1])
check("restore --path brings back only those files", (A / "css/app.css").read_text(encoding="utf-8") == "body{background:#000}\n" and (A / "notes.txt").read_text(encoding="utf-8") == "new note\n", r.stdout)
check("restore --path is a Small tweak with files_from", e["level"] == "patch" and e.get("files_from") == "v2.0.0" and e["by"] == "restore", e)
p = run("restore", "v2.0.0", "--path", "nope.txt", cwd=A, ok=False)
check("restore --path with an unknown file is a clear error", "None of nope.txt" in p.stderr, p.stderr)
r = run("restore", "v2.0.0", "--path", "css/app.css", cwd=A)
check("restore --path twice does nothing", "already match" in r.stdout, r.stdout)
r = run("restore", v_before, cwd=A)
check("full restore lists the files it changed", "Changed back: css/app.css" in r.stdout, r.stdout)

# built on
r = run("list", "--all", cwd=A)
check("list marks versions built on a restored version", "(built on v1.0.1)" in r.stdout or "(built on" in r.stdout, r.stdout)

# diff
r = run("diff", "v1.0.0", "v2.0.0", "--stat", cwd=A)
check("diff --stat lists files", "M index.html" in r.stdout and "+1 -1" in r.stdout, r.stdout)
r = run("diff", "v1.1.0^", "v1.1.0", cwd=A)
check("diff shows what one version changed", "A pricing.html" in r.stdout and "+<section>Pricing</section>" in r.stdout, r.stdout)
w(A, "index.html", "<h1>Hello there</h1>\n")
r = run("diff", cwd=A)
check("diff with no args shows unsaved changes", "-> unsaved" in r.stdout and "+<h1>Hello there</h1>" in r.stdout, r.stdout)
(A / "logo.png").write_bytes(b"\x89PNG\x00\x01binary")
r = run("diff", cwd=A)
check("binary files are summarized, not dumped", "logo.png  (binary" in r.stdout, r.stdout)
run("save", "--bump", "patch", "--summary", "Logo and greeting", cwd=A)

# status, show, list, handoff
check("status clean", "No unsaved changes" in run("status", cwd=A).stdout)
w(A, "css/app.css", "body{color:red}\n")
check("status lists unsaved", "modified  css/app.css" in run("status", cwd=A).stdout)
run("save", "--bump", "patch", "--summary", "Red text", "--reason", "color only", "--prompt", "make text red", cwd=A)
r = run("show", "latest", cwd=A)
check("show has prompt and reason", "make text red" in r.stdout and "color only" in r.stdout, r.stdout)
r = run("list", cwd=A)
check("list newest first with now marker", r.stdout.splitlines()[0].startswith(versions(A)[-1]) and "<- now" in r.stdout, r.stdout)
r = run("handoff", "v2.2.0", cwd=A)
check("handoff follows the real lineage", "v1.0.1 Small tweak: Heading text" in r.stdout and "v2.0.0" in r.stdout.split("## Not part")[1], r.stdout)
check("handoff hides dropped ideas from lineage", "Dark redesign" not in r.stdout.split("## Not part")[0], r.stdout)

# errors
p = run("restore", "v9.9.9", cwd=A, ok=False)
check("unknown version is a clear error", p.returncode == 1 and "doesn't exist" in p.stderr, p.stderr)
p = run("show", "banana", cwd=A, ok=False)
check("bad label is a clear error", "is not a version" in p.stderr, p.stderr)
p = run("restore", "v1.0.0^", cwd=A, ok=False)
check("before the first version is a clear error", "first version" in p.stderr, p.stderr)
p = run("save", "--bump", "huge", "--summary", "x", cwd=A, ok=False)
check("unknown bump is rejected", p.returncode == 2, p.stderr)
p = run("status", cwd=base, ok=False)
check("no history is a clear error (code 2)", p.returncode == 2 and "init" in p.stderr, p.stderr)

# exec bit, unicode
(A / "run.sh").write_text("#!/bin/sh\necho hi\n", encoding="utf-8"); os.chmod(A / "run.sh", 0o755)
w(A, "नमस्ते/हिंदी.md", "नमस्ते दुनिया\n")
run("save", "--bump", "minor", "--summary", "Script and Hindi page", cwd=A)
v_exec = versions(A)[-1]
os.chmod(A / "run.sh", 0o644); os.remove(A / "नमस्ते/हिंदी.md")
run("save", "--bump", "patch", "--summary", "remove", cwd=A)
run("restore", v_exec, cwd=A)
check("exec bit comes back on restore", os.access(A / "run.sh", os.X_OK))
check("unicode paths and content round-trip", (A / "नमस्ते/हिंदी.md").read_text(encoding="utf-8") == "नमस्ते दुनिया\n")

# view, export, backup/import
r = run("view", cwd=A)
html_path = A / ".ai-versions/timeline.html"
check("view writes timeline", html_path.exists() and "Went back" in html_path.read_text(encoding="utf-8"), r.stdout)
run("export", "v1.1.0", "--out", str(base / "v110.zip"), cwd=A)
with zipfile.ZipFile(base / "v110.zip") as z:
    check("export zip has that version's files", sorted(z.namelist()) == ["css/app.css", "index.html", "pricing.html"], z.namelist())
run("export", "v1.1.0", "--out", str(base / "v110dir"), cwd=A)
check("export folder", (base / "v110dir/pricing.html").exists())
run("backup", "--out", str(base / "hist.zip"), cwd=A)
B = base / "newchat"; B.mkdir()
r = run("import", str(base / "hist.zip"), cwd=B)
check("import brings all versions", versions(B) == versions(A), r.stdout)
check("import writes the current files", (B / "index.html").read_text(encoding="utf-8") == (A / "index.html").read_text(encoding="utf-8"))
r = run("restore", "v1.1.0", cwd=B)
check("restore works after import", (B / "pricing.html").exists(), r.stdout)
p = run("import", str(base / "hist.zip"), cwd=B, ok=False)
check("import refuses to overwrite a history", "already has a version history" in p.stderr, p.stderr)
C = base / "fresh"; C.mkdir()
(C / ".ai-versions").mkdir()
shutil.copytree(A / ".ai-versions", C / ".ai-versions", dirs_exist_ok=True)
r = run("restore", "latest", cwd=C)
check("empty folder + restore latest rewrites files without a new version", "no new\nversion" in r.stdout.replace(" version was", "\nversion") or "no new version" in r.stdout.replace("\n", " "), r.stdout)

# auto (hooks)
r = run("auto", cwd=base / "v110dir")
check("auto does nothing without a history", r.returncode == 0 and r.stdout == "" and r.stderr == "")
w(A, "index.html", "<h1>Forgot to save</h1>\n")
before = len(versions(A))
r = run("auto", cwd=base, env={"CLAUDE_PROJECT_DIR": str(A)})
check("auto saves forgotten changes as a small tweak (Claude Code env)", len(versions(A)) == before + 1 and entry(A, versions(A)[-1])["level"] == "patch" and entry(A, versions(A)[-1])["by"] == "auto", r.stdout)
w(A, "index.html", "<h1>Forgot again</h1>\n")
r = run("auto", cwd=base, stdin=json.dumps({"workspace_roots": [str(A)], "hook_event_name": "stop"}))
check("auto finds the project from Cursor's stdin", entry(A, versions(A)[-1])["summary"].startswith("Unsaved changes in index.html"), r.stdout)
r = run("auto", cwd=A)
check("auto is quiet when nothing changed", r.stdout == "")
import time as _t
_p = subprocess.Popen([PY, AIV, "auto"], cwd=str(base), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
_s = _t.time()
try:
    _p.wait(timeout=15); _ok = True
except subprocess.TimeoutExpired:
    _p.kill(); _ok = False
check("auto never hangs on an open, silent stdin", _ok and _t.time() - _s < 10, _t.time() - _s)

# install-hooks, then run the exact hook commands
r = run("install-hooks", "claude-code", cwd=A)
cc = json.loads((A / ".claude/settings.local.json").read_text(encoding="utf-8"))
cmd = cc["hooks"]["Stop"][0]["hooks"][0]["command"]
run("install-hooks", "claude-code", cwd=A)
cc2 = json.loads((A / ".claude/settings.local.json").read_text(encoding="utf-8"))
check("claude-code hook added once", len(cc2["hooks"]["Stop"]) == 1, cc2)
w(A, "index.html", "<h1>Via Claude hook</h1>\n")
n = len(versions(A))
# Claude Code runs hook commands through bash (Git Bash on Windows), so run it the same way.
# Use the bash on PATH by full path: a bare "bash" on Windows can start WSL from System32 instead.
hook_shell = [shutil.which("bash"), "-c", cmd] if os.name == "nt" and shutil.which("bash") else cmd
subprocess.run(hook_shell, shell=not isinstance(hook_shell, list), cwd=str(base), env={**os.environ, "CLAUDE_PROJECT_DIR": str(A)})
check("the Claude Code hook command really saves", len(versions(A)) == n + 1, cmd)
(A / ".cursor").mkdir(exist_ok=True); (A / ".cursor/hooks.json").write_text('{"version":1,"hooks":{"afterFileEdit":[{"command":"./fmt.sh"}]}}', encoding="utf-8")
run("install-hooks", "cursor", cwd=A)
cu = json.loads((A / ".cursor/hooks.json").read_text(encoding="utf-8"))
check("cursor hook merged with existing hooks", cu["hooks"]["afterFileEdit"] and len(cu["hooks"]["stop"]) == 1, cu)
w(A, "index.html", "<h1>Via Cursor hook</h1>\n")
n = len(versions(A))
subprocess.run(cu["hooks"]["stop"][0]["command"], shell=True, cwd=str(A), input=json.dumps({"workspace_roots": [str(A)]}), text=True, encoding="utf-8", errors="replace")
check("the Cursor hook command really saves", len(versions(A)) == n + 1)
w(A, ".claude/skills/versioning-ai-work/SKILL.md", "skill")
run("save", "--bump", "patch", "--summary", "after hooks", cwd=A)
m = json.loads((A / ".ai-versions/manifests" / (entry(A, versions(A)[-1])["manifest"] + ".json")).read_text(encoding="utf-8"))
check("hook files and installed skills are never versioned", not any(k.startswith((".claude/", ".cursor/hooks")) for k in m), sorted(m))
run("restore", "v1.0.0", cwd=A)
check("going back to before setup keeps the hooks and the skill", (A / ".claude/settings.local.json").exists() and (A / ".cursor/hooks.json").exists() and (A / ".claude/skills/versioning-ai-work/SKILL.md").exists())
run("restore", "prev", cwd=A)

# concurrency: two saves at once never share a number
w(A, "a.txt", "1")
outs = []
def go(i):
    outs.append(run("save", "--bump", "patch", "--summary", "race %d" % i, cwd=A, ok=False))
ts = [threading.Thread(target=go, args=(i,)) for i in range(2)]
[t.start() for t in ts]; [t.join() for t in ts]
vs = versions(A)
check("parallel saves: no duplicates, one saved", len(vs) == len(set(vs)) and sum("Saved" in o.stdout for o in outs) == 1, [o.stdout + o.stderr for o in outs])

# limits
(A / ".ai-versions/config.json").write_text(json.dumps({**json.loads((A / ".ai-versions/config.json").read_text(encoding="utf-8")), "max_file_mb": 0.001}), encoding="utf-8")
w(A, "big.bin", "x" * 5000)
r = run("save", "--bump", "patch", "--summary", "big", cwd=A)
check("files over the size limit are skipped and named", "big.bin (larger than" in r.stdout, r.stdout)
cfg = json.loads((A / ".ai-versions/config.json").read_text(encoding="utf-8")); cfg["max_file_mb"] = 25
(A / ".ai-versions/config.json").write_text(json.dumps(cfg), encoding="utf-8")
L = base / "huge"; L.mkdir()
for i in range(5005): (L / ("f%d.txt" % i)).write_text("x", encoding="utf-8")
p = run("init", cwd=L, ok=False)
check("init refuses a giant folder and cleans up", "looks like more than one project" in p.stderr and not (L / ".ai-versions").exists(), p.stderr)
r = run("init", "--only", "f1.txt", "f2.txt", cwd=L)
check("--only scopes the history", "2 files" in r.stdout, r.stdout)

# doctor
check("doctor all good", "all good" in run("doctor", cwd=A).stdout)
obj = next((A / ".ai-versions/objects").rglob("*"));
victim = [p for p in (A / ".ai-versions/objects").rglob("*") if p.is_file()][0]
data = victim.read_bytes(); victim.unlink()
check("doctor finds missing content", "problems" in run("doctor", cwd=A).stdout)
victim.write_bytes(data)

# malicious backups are refused before anything is written
import io as _io
def evil_zip(path, manifest_paths=None, extra_name=None):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(".ai-versions/config.json", json.dumps({"format": 1}))
        if manifest_paths is not None:
            z.writestr(".ai-versions/manifests/abc.json", json.dumps({p: ["0" * 64, False, 1] for p in manifest_paths}))
        if extra_name:
            z.writestr(extra_name, "x")
for label, kw in [("a .git/hooks file in a version", {"manifest_paths": [".git/hooks/post-checkout"]}),
                  ("a .GIT/hooks file (other case)", {"manifest_paths": [".GIT/hooks/pre-commit"]}),
                  ("Claude settings in a version", {"manifest_paths": [".claude/settings.local.json"]}),
                  ("a path outside the folder", {"manifest_paths": ["../outside.txt"]}),
                  ("a zip entry outside the store", {"manifest_paths": [], "extra_name": "evil.sh"}),
                  ("a zip entry with ..", {"manifest_paths": [], "extra_name": ".ai-versions/../../evil.sh"})]:
    E = base / ("evil-" + str(abs(hash(label)))); E.mkdir()
    evil_zip(base / "evil.zip", **kw)
    p = run("import", str(base / "evil.zip"), cwd=E, ok=False)
    check("import refuses " + label, p.returncode != 0 and not (E / ".ai-versions").exists() and not (E / ".git").exists(), p.stderr)
U = base / "unicode-out"; U.mkdir(); w(U, "हिंदी.txt", "x")
r = subprocess.run([PY, AIV, "init"], cwd=str(U), capture_output=True, env={**os.environ, "PYTHONIOENCODING": "ascii", "LANG": "C", "LC_ALL": "C"})
r2 = subprocess.run([PY, AIV, "list"], cwd=str(U), capture_output=True, env={**os.environ, "PYTHONIOENCODING": "ascii", "LANG": "C", "LC_ALL": "C"})
check("output works on a console that isn't UTF-8", r.returncode == 0 and r2.returncode == 0, (r.stderr, r2.stderr))
check("hook commands don't contain this machine's Python path", sys.executable not in (A / ".claude/settings.local.json").read_text(encoding="utf-8") and sys.executable not in (A / ".cursor/hooks.json").read_text(encoding="utf-8"))

# ---------------- G. git repo
G = base / "repo"; G.mkdir()
g = lambda *a: subprocess.run(["git", *a], cwd=str(G), capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
g("init", "-q", "-b", "main"); g("config", "user.email", "t@t"); g("config", "user.name", "t")
w(G, ".gitignore", "secret.txt\n"); w(G, "build/script.sh", "tracked build folder\n"); w(G, "app.js", "v1\n"); w(G, "secret.txt", "s")
g("add", "-A"); g("commit", "-qm", "init")
r = run("init", cwd=G)
m = json.loads((G / ".ai-versions/manifests" / (entry(G, "v1.0.0")["manifest"] + ".json")).read_text(encoding="utf-8"))
check("git: gitignored files skipped, tracked build/ kept", sorted(m) == [".gitignore", "app.js", "build/script.sh"], sorted(m))
check("git: store kept out of git", "/.ai-versions/" in (G / ".git/info/exclude").read_text(encoding="utf-8") and g("status", "--porcelain").stdout == "", g("status", "--porcelain").stdout)
w(G, "app.js", "v2\n"); run("save", "--bump", "patch", "--summary", "v2", cwd=G); g("commit", "-qam", "v2")
g("checkout", "-q", "HEAD~1")
check("git: checking out an old commit doesn't touch the history", versions(G) == ["v1.0.0", "v1.0.1"])
g("checkout", "-q", "main")
S = G / "sub"; S.mkdir(); w(S, "page.html", "x")
p = run("init", cwd=S, ok=False)
check("init inside an existing history points to it", "already has a version history" in p.stderr, p.stderr)
H = base / "repo2"; H.mkdir(); subprocess.run(["git", "init", "-q"], cwd=str(H)); w(H, "web/index.html", "x")
run("init", cwd=H / "web")
check("git: init in a subfolder excludes the right path", "/web/.ai-versions/" in (H / ".git/info/exclude").read_text(encoding="utf-8"))

# GitHub layer present -> refuse
K = base / "lovable"; K.mkdir(); w(K, ".github/workflows/ai-versions.yml", "x"); w(K, "a.txt", "a")
p = run("init", cwd=K, ok=False)
check("projects with the GitHub layer are pointed to pending.json", "pending.json" in p.stderr, p.stderr)

failed = [n for n, ok in results if not ok]
print("\n%d/%d passed" % (len(results) - len(failed), len(results)))
sys.exit(1 if failed else 0)
