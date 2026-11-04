// VersionPill: a small version badge with a timeline dropdown.
// Works in two modes, picked automatically:
//   Pro  (GitHub): reads /ai-versions.json, kept up to date by the "AI Versions" GitHub Action.
//   Lite (no GitHub): if src/lib/ai-versions-store.ts exists, versions live in the
//        project's Cloud database. On each preview load the pill reads src/ai-version.ts
//        (written by the AI on every change) and records a new version when it changed.
// Shows only in preview: the Lovable editor preview and local dev.
// Force it on any page with ?versions=on, hide it again with ?versions=off.
// No dependencies. Do not edit by hand; it is part of ai-versions.

import { useCallback, useEffect, useRef, useState } from "react";

type Level = "major" | "minor" | "patch" | "restore" | "start";
type Version = {
  version: string;
  date: string | null;
  level: Level;
  summary: string;
  note: string;
  reason: string;
  restored_from: string | null;
  built_on?: string | null;
};

const LEVEL_LABEL: Record<Level, string> = {
  major: "Big change",
  minor: "New feature",
  patch: "Small tweak",
  restore: "Went back",
  start: "Start",
};

// ---------- Lite mode (database) ----------
type Entry = { id?: string; bump?: string; summary?: string; reason?: string; prompt?: string };
type Row = {
  version: string;
  entry_hash: string;
  level: string;
  summary: string;
  note: string;
  reason: string;
  restored_from: string | null;
  created_at?: string | null;
};
type Store = {
  listAiVersions: () => Promise<Row[]>;
  addAiVersion: (row: Row) => Promise<"ok" | "duplicate">;
};

// Optional modules: missing files simply give empty objects, so Pro mode needs neither.
const storeModules = import.meta.glob<Store>("../lib/ai-versions-store.ts", { eager: true });
const entryModules = import.meta.glob<{ aiVersion?: Entry }>("../ai-version.ts", { eager: true });
const store: Store | undefined = Object.values(storeModules)[0];
const entry: Entry | undefined = Object.values(entryModules)[0]?.aiVersion;

const VERSION_RE = /^v(\d+)\.(\d+)\.(\d+)$/;
const semver = (v: string) => (VERSION_RE.exec(v)?.slice(1).map(Number) ?? [0, 0, 0]) as number[];
const byVersionDesc = (a: Row, b: Row) => {
  const x = semver(a.version), y = semver(b.version);
  return y[0] - x[0] || y[1] - x[1] || y[2] - x[2];
};
const clip = (s: unknown, n: number) => String(s ?? "").replace(/\s+/g, " ").trim().slice(0, n);

// Stable fingerprint of the AI's entry. Same entry = same code state.
function entryHash(e: Entry): string {
  const s = JSON.stringify([clip(e.id, 40), clip(e.bump, 20).toLowerCase(), clip(e.summary, 200), clip(e.reason, 300), clip(e.prompt, 500)]);
  let h1 = 0xdeadbeef, h2 = 0x41c6ce57;
  for (let i = 0; i < s.length; i++) {
    const c = s.charCodeAt(i);
    h1 = Math.imul(h1 ^ c, 2654435761);
    h2 = Math.imul(h2 ^ c, 1597334677);
  }
  h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507) ^ Math.imul(h2 ^ (h2 >>> 13), 3266489909);
  h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507) ^ Math.imul(h1 ^ (h1 >>> 13), 3266489909);
  return (4294967296 * (2097151 & h2) + (h1 >>> 0)).toString(36);
}

// What (if anything) to record for the current code. Rows may be in any order.
function nextRow(rows: Row[], e: Entry, hash: string): Row | null {
  const sorted = [...rows].sort(byVersionDesc);
  const latest = sorted[0];
  const base = { entry_hash: hash, note: "", reason: "", restored_from: null };
  if (!latest) {
    return { ...base, version: "v1.0.0", level: "start", summary: "Versioning switched on" };
  }
  if (latest.entry_hash === hash) return null; // nothing new
  let [M, m, p] = semver(latest.version);
  const original = sorted.filter((r) => r.entry_hash === hash).pop(); // oldest = the original
  if (original) {
    return {
      ...base, version: `v${M}.${m + 1}.0`, level: "restore", restored_from: original.version,
      summary: `Went back to ${original.version}`,
    };
  }
  const bump = clip(e.bump, 20).toLowerCase();
  const level = bump === "major" || bump === "minor" ? bump : "patch";
  if (level === "major") [M, m, p] = [M + 1, 0, 0];
  else if (level === "minor") [m, p] = [m + 1, 0];
  else p += 1;
  return {
    ...base, version: `v${M}.${m}.${p}`, level,
    summary: clip(e.summary, 200) || "Change",
    note: clip(e.prompt, 500),
    reason: [bump !== level ? `Unknown level "${bump}", saved as a small tweak.` : "", clip(e.reason, 300)]
      .filter(Boolean).join(" "),
  };
}

const toVersion = (r: Row): Version => ({
  version: r.version,
  date: r.created_at ?? null,
  level: (["major", "minor", "patch", "restore", "start"].includes(r.level) ? r.level : "patch") as Level,
  summary: r.summary,
  note: r.note,
  reason: r.reason,
  restored_from: r.restored_from,
});

// Records the current entry if needed, then returns the full list (newest first).
async function syncDatabase(s: Store, e: Entry | undefined): Promise<Version[]> {
  for (let attempt = 0; attempt < 3; attempt++) {
    const rows = await s.listAiVersions();
    const row = e ? nextRow(rows, e, entryHash(e)) : null;
    if (!row) return rows.sort(byVersionDesc).map(toVersion);
    const result = await s.addAiVersion(row);
    if (result === "ok") {
      return [{ ...row, created_at: new Date().toISOString() }, ...rows].sort(byVersionDesc).map(toVersion);
    }
    // "duplicate": another open preview saved this number first; read again and retry
  }
  return (await s.listAiVersions()).sort(byVersionDesc).map(toVersion);
}

// After going back, later versions are built on the version that was restored.
function withBuiltOn(list: Version[]): Version[] {
  let base: string | null = null;
  const out = [...list].reverse().map((v) => {
    if (v.level === "restore") base = v.restored_from ?? base;
    return { ...v, built_on: v.level === "restore" ? null : base };
  });
  return out.reverse();
}

const ENTRY_KEY = entry ? entryHash(entry) : "";

// Lite: only the Lovable preview and local dev may add versions. The published site
// (even with ?versions=on) only reads, so an older published build can't add wrong rows.
function canRecord(): boolean {
  if (typeof window === "undefined") return false;
  if (Boolean(import.meta.env?.DEV)) return true;
  const h = window.location.hostname;
  return h === "localhost" || h === "127.0.0.1" || h.endsWith(".lovableproject.com") ||
    h.startsWith("id-preview--") || h.startsWith("preview--");
}

function shouldShow(): boolean {
  if (typeof window === "undefined") return false;
  try {
    const q = new URLSearchParams(window.location.search).get("versions");
    if (q === "on" || q === "off") localStorage.setItem("ai-versions-pill", q);
    const saved = localStorage.getItem("ai-versions-pill");
    if (saved === "off") return false;
    if (saved === "on") return true;
  } catch {
    /* storage blocked: fall through to the defaults */
  }
  const h = window.location.hostname;
  return (
    Boolean(import.meta.env?.DEV) ||
    h === "localhost" ||
    h === "127.0.0.1" ||
    h.endsWith(".lovableproject.com") ||
    h.startsWith("id-preview--") ||
    h.startsWith("preview--")
  );
}

function when(iso: string | null): { short: string; full: string } {
  if (!iso) return { short: "", full: "" };
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return { short: "", full: "" };
  const full = d.toLocaleString(undefined, {
    day: "numeric", month: "short", year: "numeric", hour: "numeric", minute: "2-digit",
  });
  const mins = Math.round((Date.now() - d.getTime()) / 60000);
  let short: string;
  if (mins < 1) short = "just now";
  else if (mins < 60) short = `${mins} min ago`;
  else if (mins < 24 * 60) short = `${Math.round(mins / 60)} h ago`;
  else if (mins < 48 * 60) short = "yesterday";
  else short = d.toLocaleDateString(undefined, { day: "numeric", month: "short" });
  return { short, full };
}

const CSS = `
.aivp{--bg:#fff;--ink:#1c1f24;--muted:#6b717c;--line:#e3e6ea;--hover:#f3f5f7;
--major:#b4236b;--minor:#4c51bf;--patch:#8a919c;--restore:#0f8b7f;--start:#1c1f24;
position:fixed;left:16px;bottom:16px;z-index:2147483000;font:13px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--ink);text-align:left}
.dark .aivp,.aivp.aivp-dark{--bg:#17191d;--ink:#eceef1;--muted:#9aa1ab;--line:#2a2e35;--hover:#20242a;
--major:#f06aa8;--minor:#8f93f2;--patch:#7d848f;--restore:#3cc4b6;--start:#eceef1}
.aivp *{box-sizing:border-box}
.aivp-pill{display:inline-flex;align-items:center;gap:8px;height:30px;padding:0 12px 0 10px;border-radius:999px;
border:1px solid var(--line);background:var(--bg);color:var(--ink);font:inherit;font-weight:600;cursor:pointer;
font-variant-numeric:tabular-nums;box-shadow:0 2px 8px rgba(20,24,31,.08)}
.aivp-pill:hover{background:var(--hover)}
.aivp-panel:focus{outline:none}
.aivp-pill:focus-visible,.aivp-row:focus-visible,.aivp-x:focus-visible{outline:2px solid var(--minor);outline-offset:2px}
.aivp-chev{width:10px;height:10px;transition:transform .15s}
.aivp-open .aivp-chev{transform:rotate(180deg)}
.aivp-panel{position:absolute;left:0;bottom:40px;width:min(360px,calc(100vw - 32px));max-height:min(520px,70vh);
display:flex;flex-direction:column;background:var(--bg);border:1px solid var(--line);border-radius:14px;
box-shadow:0 12px 32px rgba(20,24,31,.16);overflow:hidden}
.aivp-head{display:flex;align-items:baseline;gap:8px;padding:12px 14px 10px;border-bottom:1px solid var(--line)}
.aivp-head b{font-size:14px}
.aivp-count{color:var(--muted)}
.aivp-x{margin-left:auto;border:0;background:none;color:var(--muted);font:inherit;cursor:pointer;padding:2px 4px;border-radius:6px}
.aivp-x:hover{color:var(--ink)}
.aivp-list{overflow-y:auto;padding:6px 0;margin:0;list-style:none}
.aivp-row{position:relative;display:grid;grid-template-columns:22px 1fr;gap:0 10px;padding:8px 14px 8px 12px;cursor:pointer;border-radius:0}
.aivp-row:hover{background:var(--hover)}
.aivp-rail{position:relative;display:flex;justify-content:center}
.aivp-rail:before{content:"";position:absolute;top:-8px;bottom:-8px;left:50%;width:2px;margin-left:-1px;background:var(--line)}
.aivp-row:first-child .aivp-rail:before{top:12px}
.aivp-row:last-child .aivp-rail:before{bottom:calc(100% - 12px)}
.aivp-dot{position:relative;margin-top:6px;border-radius:50%;background:var(--c)}
.aivp-dot.l-major{width:14px;height:14px;margin-top:3px}
.aivp-dot.l-minor{width:10px;height:10px;margin-top:5px}
.aivp-dot.l-patch,.aivp-dot.l-start{width:7px;height:7px;margin-top:6.5px}
.aivp-dot.l-restore{width:11px;height:11px;margin-top:4.5px;background:var(--bg);border:2.5px solid var(--c)}
.aivp-top{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}
.aivp-v{font-weight:600;font-variant-numeric:tabular-nums}
.aivp-lvl{font-size:12px;color:var(--c)}
.aivp-now{font-size:11px;font-weight:600;padding:1px 7px;border-radius:999px;background:var(--hover);color:var(--ink)}
.aivp-time{margin-left:auto;font-size:12px;color:var(--muted);white-space:nowrap}
.aivp-sum{margin-top:1px}
.aivp-note{margin-top:4px;color:var(--muted);font-size:12px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.aivp-row.is-open .aivp-note{display:block}
.aivp-more{margin-top:6px;font-size:12px;color:var(--muted);border-left:2px solid var(--line);padding-left:8px}
.aivp-foot{padding:10px 14px;border-top:1px solid var(--line);color:var(--muted);font-size:12px}
.aivp-msg{padding:18px 14px;color:var(--muted)}
.aivp-on{margin-top:2px;font-size:12px;color:var(--muted)}
.aivp-notice{margin:10px 12px 2px;padding:8px 10px;border-radius:8px;background:var(--hover);font-size:12px}
@media (prefers-reduced-motion:reduce){.aivp-chev{transition:none}}
`;

export default function VersionPill() {
  const [visible] = useState(shouldShow);
  const [open, setOpen] = useState(false);
  const [versions, setVersions] = useState<Version[] | null>(null);
  const [error, setError] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [darkOS, setDarkOS] = useState(false);
  const root = useRef<HTMLDivElement>(null);
  const panel = useRef<HTMLDivElement>(null);

  const load = useCallback(async () => {
    try {
      if (store) {
        setVersions(withBuiltOn(await syncDatabase(store, canRecord() ? entry : undefined)));
      } else {
        const base = (import.meta.env?.BASE_URL as string | undefined) ?? "/";
        const res = await fetch(`${base}ai-versions.json?t=${Date.now()}`, { cache: "no-store" });
        if (!res.ok) throw new Error(String(res.status));
        const data = await res.json();
        setVersions(Array.isArray(data?.versions) ? data.versions : []);
        setNotice(typeof data?.notice?.text === "string" ? data.notice.text : null);
      }
      setError(false);
    } catch (err) {
      if (store) console.warn("[ai-versions] Could not reach the versions table:", err);
      setError(true);
    }
  }, []);

  // Lite mode: record a version as soon as the AI's entry changes (hot reload included).
  useEffect(() => {
    if (visible && store) load();
  }, [visible, load, ENTRY_KEY]);

  useEffect(() => {
    if (!visible) return;
    if (!store) load();
    const mq = window.matchMedia?.("(prefers-color-scheme: dark)");
    const sync = () => setDarkOS(Boolean(mq?.matches) && !document.documentElement.classList.contains("light"));
    sync();
    mq?.addEventListener?.("change", sync);
    return () => mq?.removeEventListener?.("change", sync);
  }, [visible, load]);

  useEffect(() => {
    if (!open) return;
    panel.current?.focus();
    load();
    const onDown = (e: MouseEvent) => {
      if (root.current && !root.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open, load]);

  if (!visible) return null;

  const current = versions?.[0];
  const label = current ? current.version : error ? "Versions" : "…";

  return (
    <div ref={root} className={`aivp${open ? " aivp-open" : ""}${darkOS ? " aivp-dark" : ""}`}>
      <style>{CSS}</style>
      {open && (
        <div className="aivp-panel" role="dialog" aria-label="Version history" tabIndex={-1} ref={panel}>
          <div className="aivp-head">
            <b>Version history</b>
            {versions && versions.length > 0 && <span className="aivp-count">{versions.length}</span>}
            <button className="aivp-x" onClick={() => setOpen(false)} aria-label="Close version history">Close</button>
          </div>
          {notice && <div className="aivp-notice" role="status">{notice}</div>}
          {error && !versions && (
            <div className="aivp-msg">
              {store
                ? "Can't reach the versions table. Check that the ai_versions table exists (setup step 2), then reopen this list."
                : "The version list isn't here yet. It appears about a minute after your first change is saved to GitHub."}
            </div>
          )}
          {versions && versions.length === 0 && (
            <div className="aivp-msg">
              {store
                ? "No versions yet. Add src/ai-version.ts (setup step 3) and reload the preview."
                : "No versions yet. Make a change in Lovable and it'll show up here in about a minute."}
            </div>
          )}
          {versions && versions.length > 0 && (
            <ol className="aivp-list">
              {versions.map((v, i) => {
                const t = when(v.date);
                const isOpen = expanded === v.version;
                const color = `var(--${v.level in LEVEL_LABEL ? v.level : "patch"})`;
                const hasMore = Boolean(v.note || v.reason || v.restored_from);
                return (
                  <li
                    key={v.version}
                    className={`aivp-row${isOpen ? " is-open" : ""}`}
                    style={{ ["--c" as string]: color }}
                    tabIndex={0}
                    role="button"
                    aria-expanded={hasMore ? isOpen : undefined}
                    onClick={() => setExpanded(isOpen ? null : v.version)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        setExpanded(isOpen ? null : v.version);
                      }
                    }}
                  >
                    <span className="aivp-rail" aria-hidden="true">
                      <span className={`aivp-dot l-${v.level}`} />
                    </span>
                    <div>
                      <div className="aivp-top">
                        <span className="aivp-v">{v.version}</span>
                        <span className="aivp-lvl">{LEVEL_LABEL[v.level] ?? v.level}</span>
                        {i === 0 && <span className="aivp-now">Now</span>}
                        <time className="aivp-time" dateTime={v.date ?? undefined} title={t.full}>{t.short}</time>
                      </div>
                      <div className="aivp-sum">{v.summary}</div>
                      {v.built_on && <div className="aivp-on">Built on {v.built_on}</div>}
                      {v.note && <div className="aivp-note">“{v.note}”</div>}
                      {isOpen && (v.restored_from || v.reason || t.full) && (
                        <div className="aivp-more">
                          {v.restored_from && <div>Same code as {v.restored_from}</div>}
                          {v.reason && v.level !== "restore" && <div>{v.reason}</div>}
                          {t.full && <div>{t.full}</div>}
                        </div>
                      )}
                    </div>
                  </li>
                );
              })}
            </ol>
          )}
          <div className="aivp-foot">
            {store
              ? "To go back, use History → Restore in Lovable."
              : "To go back, ask in chat, for example: “go back to v1.2.0”."}
          </div>
        </div>
      )}
      <button
        className="aivp-pill"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-label={current ? `Version ${current.version}. Show version history` : "Show version history"}
      >
        <span
          className="aivp-dot l-patch"
          style={{ margin: 0, background: current ? `var(--${current.level})` : "var(--patch)" }}
          aria-hidden="true"
        />
        {label}
        <svg className="aivp-chev" viewBox="0 0 10 10" aria-hidden="true">
          <path d="M2 6.5 5 3.5 8 6.5" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
        </svg>
      </button>
    </div>
  );
}
