#!/usr/bin/env python3
"""Structural checks. Keeps the repo honest about its own scope rules."""
import io, os, re, sys

fail = []

def check(cond, msg):
    if not cond: fail.append(msg)

# 1 · rubric weights must sum to 100
rub = sorted(f for f in os.listdir("rubric") if re.match(r'v[\d.]+\.md', f))
check(bool(rub), "rubric/ contains no versioned rubric")
LEGACY = {"v1.0.md"}          # 旧格式：支柱权重表 + Credit 列
MODERN = [r for r in rub if r not in LEGACY]
for r in sorted(LEGACY & set(rub)):
    s = io.open(f"rubric/{r}", encoding="utf-8").read()
    weights = [int(x) for x in re.findall(r'^\| \d \| [^|]+ \| \*{0,2}(\d+)\*{0,2} \|', s, re.M)]
    check(sum(weights) == 100, f"rubric/{r}: pillar weights sum to {sum(weights)}, expected 100")
    pts = [int(x) for x in re.findall(r'^\| [^|]+ \| \*{0,2}(\d+)\*{0,2} \| ', s, re.M)]
    check(sum(pts) == 100, f"rubric/{r}: check points sum to {sum(pts)}, expected 100")
    check("**Status:**" in s, f"rubric/{r}: missing status line")

# 2 · scope rule — no fix templates anywhere in the public repo
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in (".git", ".github")]
    for f in files:
        if not f.endswith(".md"): continue
        p = os.path.join(root, f)
        s = io.open(p, encoding="utf-8").read()
        langs = ("typescript", "javascript", "jsonld", "html", "python")
        if not (root.startswith("./rubric") or root.startswith("./schema")):
            langs = langs + ("json",)
        for lang in langs:
            check(f"```{lang}" not in s,
                  f"{p}: contains a ```{lang} block — this repo is measurement-only, "
                  f"fix templates belong in the private repo")

# 3 · required files
for f in ["README.md", "README.zh-CN.md", "LICENSE", "SKILL.md", "CONTRIBUTING.md",
          "CODE_OF_CONDUCT.md", "SECURITY.md", "CHANGELOG.md", "CITATION.cff"]:
    check(os.path.exists(f), f"missing required file: {f}")

# 4 · SKILL.md must declare the rubric version it implements
sk = io.open("SKILL.md", encoding="utf-8").read()
m = re.search(r'rubric: "(v[\d.]+)"', sk)
check(bool(m), "SKILL.md frontmatter does not declare a rubric version")
if m: check(os.path.exists(f"rubric/{m.group(1)}.md"),
            f"SKILL.md declares rubric {m.group(1)} but rubric/{m.group(1)}.md does not exist")

# 5 · licence consistency — the exact failure the previous repo shipped with
check('license: "MIT"' in sk, 'SKILL.md frontmatter must declare license: "MIT" to match LICENSE')

# 6 · 示例报告的加法必须成立（KOL 最容易手加穿帮的地方）
import re as _re
for f in ["README.md", "examples/sample-report.md"]:
    if not os.path.exists(f): continue
    t = io.open(f, encoding="utf-8").read()
    m = _re.search(r'```\n(AIV \d+.*?)\n```', t, _re.S)
    if not m: continue
    rep = m.group(1); lines = rep.split("\n")
    hm = _re.match(r'AIV (\d+) / (\d+)', lines[0])
    check(bool(hm), f"{f}: report header must read 'AIV <score> / <observable max>'")
    tot = omax = 0
    for i, l in enumerate(lines):
        sm = _re.match(r'^  ([A-Z][A-Za-z ]+?)\s{2,}(\d+) / (\d+)', l)
        if not sm: continue
        name, sub, mx = sm.group(1), int(sm.group(2)), int(sm.group(3))
        got = gmax = 0
        for l2 in lines[i+1:]:
            if not l2.startswith("    "): break
            im = _re.search(r'(\d+)/(\d+)\s*$', l2)
            if im: got += int(im.group(1)); gmax += int(im.group(2))
        check(got == sub, f"{f}: '{name}' subtotal {sub} but line items sum to {got}")
        check(gmax == mx, f"{f}: '{name}' max {mx} but line items sum to {gmax}")
        tot += sub; omax += mx
    if hm:
        check(tot == int(hm.group(1)), f"{f}: header score {hm.group(1)} but pillars sum to {tot}")
        check(omax == int(hm.group(2)), f"{f}: header max {hm.group(2)} but pillars sum to {omax}")
        pm = _re.search(r'normalised (\d+)%', rep)
        if pm and omax:
            exp = round(tot / omax * 100)
            check(int(pm.group(1)) == exp, f"{f}: normalised {pm.group(1)}% but {tot}/{omax} = {exp}%")

# 7 · 每个检查项必须标注 credit 类型
for r in sorted(LEGACY & set(rub)):
    s2 = io.open(f"rubric/{r}", encoding="utf-8").read()
    rows = _re.findall(r'^\| [^|]+ \| \d+ \| ([^|]+) \|', s2, _re.M)
    bad = [x.strip() for x in rows if x.strip() not in ("prop.", "all/none")]
    check(not bad, f"rubric/{r}: checks missing a valid Credit value: {bad[:3]}")

# 8 · cover 图里的数字必须与示例报告一致（按出现次数比对，重复值不会互相掩盖）
if os.path.exists("assets/cover.svg"):
    cv = io.open("assets/cover.svg", encoding="utf-8").read()
    sr = io.open("examples/sample-report.md", encoding="utf-8").read()
    hm = re.search(r'AIV (\d+) / (\d+)', sr)
    if hm:
        check(f">{hm.group(1)}<" in cv, f"cover.svg: score {hm.group(1)} not shown")
        check(f"/ {hm.group(2)}" in cv, f"cover.svg: observable max {hm.group(2)} not shown")
    pm = re.search(r'normalised (\d+)%', sr)
    if pm:
        check(f"NORMALISED {pm.group(1)}%" in cv, "cover.svg: normalised % out of sync")
    from collections import Counter
    want = Counter(f"{m.group(2)}/{m.group(3)}"
                   for m in re.finditer(r'^  ([A-Z][A-Za-z ]+?)\s{2,}(\d+) / (\d+)', sr, re.M))
    got = Counter(re.findall(r'>(\d+/\d+)<', cv))
    check(want == got,
          f"cover.svg pillar values out of sync with sample report — "
          f"report has {dict(want)}, cover has {dict(got)}")

# 9 · rubric 的 JSON 与 MD 必须逐条一致
import json as _json
for r in sorted(LEGACY & set(rub)):
    jp = f"rubric/{r[:-3]}.json"
    check(os.path.exists(jp), f"{jp} missing — every released rubric needs a machine-readable twin")
    if not os.path.exists(jp): continue
    j = _json.load(io.open(jp, encoding="utf-8"))
    md = io.open(f"rubric/{r}", encoding="utf-8").read()
    md_rows = re.findall(r'^\| (.+?) \| (\d+) \| (prop\.|all/none) \|', md, re.M)
    check(len(j["checks"]) == len(md_rows),
          f"{jp}: {len(j['checks'])} checks but {r} has {len(md_rows)}")
    check(sum(c["points"] for c in j["checks"]) == j["nominal_max"] == 100,
          f"{jp}: points do not sum to nominal_max 100")
    ids = [c["id"] for c in j["checks"]]
    check(len(ids) == len(set(ids)), f"{jp}: duplicate check ids")
    check(all(re.match(r'^p[1-5]\.[a-z0-9-]+$', i) for i in ids),
          f"{jp}: ids must look like p1.some-slug")
    md_pts = [int(x[1]) for x in md_rows]
    check(sorted(md_pts) == sorted(c["points"] for c in j["checks"]),
          f"{jp}: point values differ from {r}")
    for c in j["checks"]:
        check(c["credit"] in ("proportional", "all-or-nothing"),
              f"{jp}: {c['id']} has invalid credit '{c['credit']}'")

# 10 · v1.1 起的新格式：阶梯给分 + 门槛 + 加分项，且实施信息不得进入公开仓
for r in MODERN:
    jp = f"rubric/{r[:-3]}.json"
    check(os.path.exists(jp), f"{jp} missing — every released rubric needs a machine-readable twin")
    if not os.path.exists(jp): continue
    j = _json.load(io.open(jp, encoding="utf-8"))
    ck = j["checks"]
    scored = [c for c in ck if c["kind"] in ("gate", "scored")]
    bonus  = [c for c in ck if c["kind"] == "bonus"]
    check(sum(c["points"] for c in scored) == j["scores"]["readiness"]["total"] == 100,
          f"{jp}: 计分项之和不等于就绪度满分 100")
    check(sum(c["points"] for c in bonus) >= j["bonus_cap"],
          f"{jp}: 加分项总分低于 bonus_cap，封顶值无意义")
    ids = [c["id"] for c in ck]
    check(len(ids) == len(set(ids)), f"{jp}: duplicate check ids")
    check(all(re.match(r'^(g|p[1-4]|b)\.[a-z0-9-]+$', i) for i in ids),
          f"{jp}: ids 必须形如 g.slug / p1.slug / b.slug")
    for c in scored:
        t = [x["points"] for x in c["tiers"]]
        check(t == sorted(t), f"{jp}: {c['id']} 的阶梯分不是递增的")
        check(t[0] == 0 and t[-1] == c["points"],
              f"{jp}: {c['id']} 阶梯须从 0 起、到满分止（现为 {t[0]}..{t[-1]}，满分 {c['points']}）")
        check(len(t) == len(set(t)), f"{jp}: {c['id']} 阶梯有重复分值")
        check(bool(c.get("why_zh")), f"{jp}: {c['id']} 缺少「为什么重要」——老板读的就是这一句")
    gates = [c for c in ck if c["kind"] == "gate"]
    check(gates and all(c.get("gate_note_zh") for c in gates),
          f"{jp}: 门槛项必须写明封顶规则")
    b = j["bands"]
    check([x["min_pct"] for x in b] == sorted((x["min_pct"] for x in b), reverse=True),
          f"{jp}: bands 必须按分数从高到低排列")
    check(b[-1]["min_pct"] == 0, f"{jp}: 最低档必须从 0 起，否则有分数落不进任何档")
    check(not any("危急" in x["name_zh"] or "Critical" in x.get("name", "") for x in b),
          f"{jp}: 档名不得用判决式措辞——这是给决策者看的诊断，不是 CI 的 fail-the-build")
    # 实施信息属于私有仓：公开量表只说测什么与为什么
    leaked = sorted({k for c in ck for k in c if k in ("fix_zh", "effort_days", "owner")})
    check(not leaked, f"{jp}: 公开量表不得携带实施字段 {leaked} —— 修法与工时属于实施层")
    md = io.open(f"rubric/{r}", encoding="utf-8").read()
    for c in ck:
        check(f"`{c['id']}`" in md, f"rubric/{r}: 缺少检查项 {c['id']}，与 JSON 不一致")
    check("## 这份量表不告诉你怎么修" in md, f"rubric/{r}: 缺少边界说明章节")

if fail:
    print("FAIL")
    for f in fail: print("  ·", f)
    sys.exit(1)
print(f"OK — {len(rub)} rubric version(s) ({len(MODERN)} tiered), scope rule clean, metadata consistent")
