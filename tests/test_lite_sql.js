const { PGlite } = require("@electric-sql/pglite");
const fs = require("fs");
const sql = fs.readFileSync(process.argv[2], "utf8");
let pass = 0, fail = 0;
const check = (name, ok, detail = "") => { ok ? pass++ : fail++; console.log((ok ? "PASS " : "FAIL ") + name + (ok ? "" : "  <- " + detail)); };

(async () => {
  const db = new PGlite();
  await db.exec("create role anon; create role authenticated;");
  await db.exec(sql);
  await db.exec(sql); // running it twice must be safe
  await db.exec("grant usage on schema public to anon; grant select, insert, update, delete on public.ai_versions to anon;");
  await db.exec("set role anon");
  const ins = async (v, level, extra = {}) => {
    try {
      await db.query("insert into ai_versions (version, entry_hash, level, summary, note, reason, restored_from) values ($1,$2,$3,$4,$5,$6,$7)",
        [v, extra.hash || "h" + v, level, extra.summary || "s", extra.note || "", "", extra.from || null]);
      return "ok";
    } catch (e) { return e.message; }
  };
  check("first row must be v1.0.0 start", (await ins("v1.0.1", "patch")).includes("first version"));
  check("v1.0.0 start accepted", (await ins("v1.0.0", "start")) === "ok");
  check("patch -> v1.0.1", (await ins("v1.0.1", "patch")) === "ok");
  check("minor -> v1.1.0", (await ins("v1.1.0", "minor")) === "ok");
  check("major -> v2.0.0", (await ins("v2.0.0", "major")) === "ok");
  check("jumping ahead (v999.0.0) is refused", (await ins("v999.0.0", "major")).includes("not the next version"));
  check("skipping a number is refused", (await ins("v2.0.2", "patch")).includes("not the next version"));
  check("wrong level for the number is refused", (await ins("v2.1.0", "patch")).includes("not the next version"));
  check("restore -> v2.1.0 from an existing version", (await ins("v2.1.0", "restore", { from: "v1.1.0" })) === "ok");
  check("restore from a version that doesn't exist is refused", (await ins("v2.2.0", "restore", { from: "v9.9.9" })).includes("does not exist"));
  check("a second start is refused", (await ins("v2.1.1", "start")).includes("not the next version"));
  check("bad format is refused", (await ins("v2.1.1-hack", "patch")).length > 2 && !(await ins("v2.1.1-hack", "patch")).startsWith("ok"));
  check("long note is refused", !(await ins("v2.1.1", "patch", { note: "x".repeat(501) })).startsWith("ok"));
  check("long summary is refused", !(await ins("v2.1.1", "patch", { summary: "x".repeat(201) })).startsWith("ok"));
  check("duplicate number is refused (two previews)", (await ins("v2.1.0", "minor")).includes("not the next version") || (await ins("v2.1.0", "minor")).includes("duplicate"));
  // update / delete are not allowed (no policies)
  const upd = await db.query("update ai_versions set summary='hacked' where version='v1.0.0'");
  const del = await db.query("delete from ai_versions where version='v1.0.0'");
  const still = await db.query("select summary from ai_versions where version='v1.0.0'");
  check("the app can't change versions", upd.affectedRows === 0 && still.rows[0].summary === "s");
  check("the app can't delete versions", del.affectedRows === 0 && still.rows.length === 1);
  // rate limit: 20 per minute
  let last = "ok", n = 0;
  for (let i = 1; i <= 25 && last === "ok"; i++) { last = await ins(`v2.1.${i}`, "patch"); if (last === "ok") n++; }
  check("at most 20 new versions a minute", last.includes("too many") && n <= 20, `${n} accepted, last: ${last}`);
  const r = await db.query("select count(*)::int c from ai_versions");
  console.log(`rows: ${r.rows[0].c}`);
  console.log(`\n${pass}/${pass + fail} passed`);
  process.exit(fail ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
