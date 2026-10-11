#!/usr/bin/env python3
"""Structural checks. Keeps the repo honest about its own scope rules."""
import io, struct, json, os, re, sys

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
# build output (dist/, build/) is gitignored and not part of the repository's documents
SKIP_DIRS = (".git", "node_modules", "dist", "build", "__pycache__", ".venv")
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS + (".github",)]
    for f in files:
        if not f.endswith(".md"): continue
        p = os.path.join(root, f)
        s = io.open(p, encoding="utf-8").read()
        # ```jsonld / ```html / ```typescript are the shapes a fix template takes —
        # banned everywhere. Plain ```json is config and data, so it is allowed where
        # config and data legitimately live.
        langs = ("typescript", "javascript", "jsonld", "html", "python")
        JSON_OK = ("./rubric", "./schema", "./benchmark", "./cli", "./examples/ci")
        if not (root.startswith(JSON_OK) or p in ("./.github/CONTRIBUTING.md",)):
            langs = langs + ("json",)
        for lang in langs:
            check(f"```{lang}" not in s,
                  f"{p}: contains a ```{lang} block — this repo is measurement-only, "
                  f"fix templates belong in the private repo")

# 3 · required files
for f in ["README.md", "README.zh-CN.md", "LICENSE", "SKILL.md", ".github/CONTRIBUTING.md",
          ".github/CODE_OF_CONDUCT.md", ".github/SECURITY.md", "CHANGELOG.md", "CITATION.cff"]:
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
for f in ["examples/sample-report.md", "README.md"]:
    if not os.path.exists(f): continue
    t = io.open(f, encoding="utf-8").read()
    m = _re.search(r'```\n(AIV Readiness .*?)\n```', t, _re.S)
    if f == "examples/sample-report.md":
        check(bool(m), f"{f}: 找不到 ``` 包裹的 AIV Readiness 报告块 —— "
                       f"这是 CI 唯一能验算的格式范例")
    if not m: continue
    rep = m.group(1); lines = rep.split("\n")
    hm = _re.match(r'AIV Readiness (\d+) / (\d+)', lines[0])
    check(bool(hm), f"{f}: 表头须为 'AIV Readiness <score> / <observable max>'，实际是 {lines[0][:60]!r}")
    check(any(l.startswith("Citation performance") for l in lines),
          f"{f}: 报告必须单列「Citation performance」区块——就绪度与引用表现不得合并")
    check(any("Bonus checks" in l for l in lines),
          f"{f}: 报告必须写明加分项状态（即使为 +0），否则读者无法判断分母")
    tot = omax = 0
    for i, l in enumerate(lines):
        sm = _re.match(r'^  ([A-Z][A-Za-z ]+?)\s{2,}(\d+) / (\d+)\s*(?:←.*)?$', l)
        if not sm: continue
        name, sub, mx = sm.group(1), int(sm.group(2)), int(sm.group(3))
        got = gmax = 0
        for l2 in lines[i+1:]:
            if not l2.startswith("    "): break
            if _re.match(r'^\s+(tier |full tier)', l2): continue   # 档位说明续行
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
            exp = min(100, round(tot / omax * 100))
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
    hm = re.search(r'AIV Readiness (\d+) / (\d+)', sr)
    if hm:
        check(bool(hm), "examples/sample-report.md: 封面同步检查找不到表头")
        check(f">{hm.group(1)}<" in cv, f"cover.svg: score {hm.group(1)} not shown")
        check(f"/ {hm.group(2)}" in cv, f"cover.svg: observable max {hm.group(2)} not shown")
    pm = re.search(r'normalised (\d+)%', sr)
    if pm:
        check(f"NORMALISED {pm.group(1)}%" in cv, "cover.svg: normalised % out of sync")
    check("rubric v1.1" in cv, "cover.svg: 封面图上的量表版本已过期——这是分享出去的第一张图")
    check("Critical" not in cv, "cover.svg: 封面仍带判决式档名")
    for stale in ("Infrastructure", "Structured Data", "Platform Visibility", "Brand Authority"):
        check(stale not in cv, f"cover.svg: 仍在用 v1.0 的支柱名 {stale!r}")
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
    # 封顶数字必须在所有语言版本与 JSON 之间完全一致 —— 一处翻错就让整套实现算出不同的分
    gc = j["gate_cap"]
    for f2 in [f"rubric/{r}", f"rubric/{r[:-3]}.zh-CN.md"]:
        if not os.path.exists(f2): continue
        t2 = io.open(f2, encoding="utf-8").read()
        # 排除加分项的「+6」写法：那里数字前带 +，门槛封顶不带
        nums = {int(x) for x in re.findall(r'(?:caps? at|capped at|封顶)\s*\**\s*(?!\+)(\d+)', t2)}
        check(nums == {gc},
              f"{f2}: 门槛封顶数字与 JSON 的 gate_cap={gc} 不一致，文中出现 {sorted(nums)} "
              f"—— 一处写错，照这份规范实现的人算出的分就和官方技能对不上")
    check("This rubric does not tell you how to fix anything" in md
          or "这份量表不告诉你怎么修" in md, f"rubric/{r}: 缺少边界说明章节")
    # 双语版必须存在，且逐条一致——规范只有一种语言，另一种语言的读者就用不了
    zp = f"rubric/{r[:-3]}.zh-CN.md"
    check(os.path.exists(zp), f"{zp} missing — 规范必须双语，否则另一半读者读不了核心口径")
    if os.path.exists(zp):
        zmd = io.open(zp, encoding="utf-8").read()
        for c in ck:
            check(f"`{c['id']}`" in zmd, f"{zp}: 缺少检查项 {c['id']}，与英文版不一致")
        # 逐项比对：每个检查项在中英两份规范的标题里写的分值，必须等于 JSON 的 points。
        # （这里以前是一条带 `or True` 的检查，永远不会失败。）
        for c in ck:
            for lang, text in (("英文", md), ("中文", zmd)):
                if not re.search(r'^### .+? · \d+', text, re.M):
                    continue            # v1.0 的规范没有逐项标题
                m = re.search(r'^### .+? · (\d+)(?: pts?)?\s+`%s`' % re.escape(c["id"]), text, re.M)
                check(m and int(m.group(1)) == c["points"],
                      f"rubric/{r} {lang}版：{c['id']} 的标题分值 {m.group(1) if m else '缺失'} "
                      f"与 JSON 的 {c['points']} 不一致")
        import re as _r
        en_pts = sorted(int(x) for x in _r.findall(r'^### .+? · (\d+)', md, _r.M))
        zh_pts = sorted(int(x) for x in _r.findall(r'^### .+? · (\d+)', zmd, _r.M))
        check(en_pts == zh_pts, f"{zp}: 分值与英文版不一致 — 中 {zh_pts[:6]} vs 英 {en_pts[:6]}")
    # 每个 check 的双语字段都要齐
    for c in ck:
        miss = [k for k in ("name", "name_zh") if not c.get(k)]
        if c["kind"] != "bonus":
            miss += [k for k in ("why", "why_zh") if not c.get(k)]
            for t in c.get("tiers", []):
                if not t.get("condition") or not t.get("condition_zh"):
                    miss.append(f"tier@{t['points']}")
        check(not miss, f"{jp}: {c['id']} 缺少双语字段 {miss}")
    for b in j["bands"]:
        check(b.get("name") and b.get("name_zh") and b.get("meaning") and b.get("meaning_zh"),
              f"{jp}: 档位 {b['min_pct']}+ 缺少双语名称或释义")

# 11 · report schema 必须跟得上量表：档位枚举与 check id 不得漂移
for r in MODERN:
    j = _json.load(io.open(f"rubric/{r[:-3]}.json", encoding="utf-8"))
    sp = "schema/report.v2.json"
    check(os.path.exists(sp), f"{sp} missing — v1.1 的输出形态与 report.v1 不同，必须有新 schema")
    if not os.path.exists(sp): continue
    sc = _json.load(io.open(sp, encoding="utf-8"))
    bands = {b["name"] for b in j["bands"]} | {b["name_zh"] for b in j["bands"]}
    check(set(sc["properties"]["band"]["enum"]) == bands,
          f"{sp}: band 枚举与量表档名不一致 — 少了 {sorted(bands - set(sc['properties']['band']['enum']))}")
    sids = set(sc["properties"]["checks"]["items"]["properties"]["id"]["enum"])
    rids = {c["id"] for c in j["checks"]}
    check(sids == rids, f"{sp}: check id 枚举与量表不一致 — 差 {sorted(rids ^ sids)[:5]}")
    check("failed" not in sc["properties"]["checks"]["items"]["properties"]["state"]["enum"],
          f"{sp}: 阶梯给分下没有 failed 态——未达任何档就是 scored 且 0 分，仍留在分母里")
    for need in ("readiness", "gate_capped", "observable_max", "normalised"):
        check(need in sc["properties"], f"{sp}: 缺少 v1.1 必需字段 {need}")

# 12 · 全仓不得残留上一版的支柱名、已失效的 check id、或「Pillar N」编号
#      —— 只查封面图不够：这批错误当初散落在 README / SKILL.md / rubric/README.md / reference/
CURRENT = set()
for r in MODERN:
    CURRENT |= {c["id"] for c in _json.load(io.open(f"rubric/{r[:-3]}.json", encoding="utf-8"))["checks"]}
LEGACY_IDS = set()
for r in sorted(LEGACY & set(rub)):
    jp0 = f"rubric/{r[:-3]}.json"
    if os.path.exists(jp0):
        LEGACY_IDS |= {c["id"] for c in _json.load(io.open(jp0, encoding="utf-8"))["checks"]}
LEGACY_IDS -= CURRENT
STALE_NAMES = ("Infrastructure", "Structured Data", "Platform Visibility", "Brand Authority")
EXEMPT = ("CHANGELOG", "rubric/v1.0", "rubric/calibration", "rubric/open-questions",
          "examples/audits", "examples/README", "rubric/README")
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for f in files:
        if not f.endswith((".md", ".svg", ".yml")): continue
        pth = os.path.join(root, f)[2:]
        if any(pth.startswith(e) for e in EXEMPT): continue
        t = io.open(pth, encoding="utf-8").read()
        for nm in STALE_NAMES:
            check(nm not in t, f"{pth}: 残留 v1.0 支柱名 {nm!r} —— 当前支柱见 rubric/{MODERN[0]}")
        for bad in sorted(LEGACY_IDS):
            check(bad not in t, f"{pth}: 引用了已失效的 check id {bad!r}")
        m2 = re.search(r'Pillar [1-5]|支柱 [1-5]', t)
        check(not m2, f"{pth}: 用了「{m2.group(0) if m2 else ''}」这种编号 —— v1.1 请用支柱名或 check id 前缀，编号会随版本错位")

# 13 · 发布的审计必须能通过自己发布的 schema，而且分数要能重算出来
try:
    import jsonschema
    have_js = True
except ImportError:
    have_js = False
    print("  · 提示：未安装 jsonschema，跳过 schema 校验（CI 里应装上）")
for r in MODERN:
    j = _json.load(io.open(f"rubric/{r[:-3]}.json", encoding="utf-8"))
    RB = {c["id"]: c for c in j["checks"]}
    d0 = f"examples/audits/{r[:-3]}"
    check(os.path.isdir(d0), f"{d0}/ missing — 当前口径必须有按它跑出来的公开审计，否则没有任何真实参照")
    if not os.path.isdir(d0): continue
    import glob as _g
    files = sorted(_g.glob(f"{d0}/*.json"))
    check(len(files) >= 3, f"{d0}/: 只有 {len(files)} 份审计，太少不足以当参照")
    sc = _json.load(io.open("schema/report.v2.json", encoding="utf-8")) if os.path.exists("schema/report.v2.json") else None
    for fp in files:
        a = _json.load(io.open(fp, encoding="utf-8"))
        if have_js and sc:
            try:
                jsonschema.validate(a, sc)
            except Exception as e:
                check(False, f"{fp}: 不符合 schema/report.v2.json — {str(e)[:160]}")
        got = den = bon = 0
        gate_zero = False
        for c in a["checks"]:
            rr = RB.get(c["id"])
            check(bool(rr), f"{fp}: check id {c['id']!r} 不在 {r[:-3]} 里")
            if not rr or c["state"] != "scored": continue
            tiers = [t["points"] for t in rr.get("tiers", [])] or [0, rr["points"]]
            check(c["points"] in tiers,
                  f"{fp}: {c['id']} 得 {c['points']} 分，但该项档位只有 {tiers}")
            if rr["kind"] == "bonus":
                bon += c["points"]
            else:
                got += c["points"]; den += rr["points"]
                if rr["kind"] == "gate" and c["points"] == 0: gate_zero = True
        tot = got + min(bon, j["bonus_cap"])
        norm = min(100, round(100 * tot / den))            # bonus never takes the percentage past 100
        norm = min(norm, j["gate_cap"]) if gate_zero else norm
        band = next(b["name"] for b in j["bands"] if norm >= b["min_pct"])
        check(a["readiness"] == tot, f"{fp}: readiness {a['readiness']} 但逐项之和是 {tot}")
        check(a["observable_max"] == den, f"{fp}: observable_max {a['observable_max']} 但分母之和是 {den}")
        check(a["normalised"] == norm, f"{fp}: normalised {a['normalised']} 但 {tot}/{den} 应为 {norm}")
        check(a["band"] == band, f"{fp}: band {a['band']!r} 与 {norm}% 对应的 {band!r} 不符")
        check(bool(a.get("gate_capped")) == gate_zero, f"{fp}: gate_capped 与门槛项实际状态不符")
        al = a.get("audience_language")
        check(al is None or re.match(r'^[a-z]{2,3}(-[A-Za-z0-9]{2,8})*$', al),
              f"{fp}: audience_language {al!r} 不是 BCP 47 —— 按语言分流的规则（中文 50–200 字 "
              f"vs 英文 25–120 词、报告语种）会静默用错分支")
        check(len(a["sampled_urls"]) == 8 or a.get("notes"),
              f"{fp}: 抽样 {len(a['sampled_urls'])} 页而非 8 页，且 notes 里没有说明")

# 14 · 英文主文档不得混入中文正文（语言切换链接与公司名除外）
#      —— 仓库主语言是英文，读者点进来撞上整屏读不懂的字，是最刺眼的一种不完整
CJK = re.compile(r'[\u4e00-\u9fff]')
ALLOW = re.compile(r'<a [^>]*>[^<]*简体中文[^<]*</a>'            # HTML 形式的语言切换链接
                   r'|\[[^\]]*简体中文[^\]]*\]\([^)]*\)'      # Markdown 形式
                   r'|(?:简体中文|中文版|同一张表的中文版见)\s*[：:]?\s*\[[^\]]*\]\([^)]*\)'
                   r'|\(见润科技\)')                            # 公司中文名
EN_PRIMARY = ["README.md", "SKILL.md", "CHANGELOG.md", ".github/CONTRIBUTING.md", ".github/SECURITY.md",
              ".github/CODE_OF_CONDUCT.md", "rubric/README.md", "examples/README.md",
              "examples/sample-report.md", "reference/ai-crawlers.md",
              "reference/platform-source-selection.md"]
for r in MODERN:
    EN_PRIMARY += [f"rubric/{r}", f"rubric/{r[:-3].replace('v', 'calibration-v')}.md",
                   "rubric/open-questions.md", f"rubric/evidence-{r[:-3]}.md"]
EN_PRIMARY += ["AGENTS.md", "guide/stability.md", "guide/troubleshooting.md", "benchmark/VALIDITY.md", "benchmark/REPRODUCIBILITY.md",
               "benchmark/SENSITIVITY.md", "rubric/bands-analysis.md", "benchmark/PREREGISTRATION.md"]
import glob as _g2
# 审计的对象若是中文站，报告里必然引用中文原文——那是证据，不是未翻译
for _a in sorted(_g2.glob("examples/audits/v1.1/*.json")):
    if _json.load(io.open(_a, encoding="utf-8")).get("audience_language", "en").startswith("zh"):
        continue
    EN_PRIMARY.append(_a[:-5] + ".md")
for pth in dict.fromkeys(EN_PRIMARY):
    if not os.path.exists(pth): continue
    body = ALLOW.sub("", io.open(pth, encoding="utf-8").read())
    # 引用被审站点的原句可以保留原文，用反引号或引号包起来的不算
    body = re.sub(r'`[^`]*`|「[^」]*」|"[^"]*"', "", body)
    bad = [l.strip()[:70] for l in body.split("\n") if CJK.search(l)]
    check(not bad, f"{pth}: 英文主文档里有 {len(bad)} 行中文正文，第一行是 {bad[0] if bad else ''!r} "
                   f"—— 中文内容应放到对应的 .zh-CN.md")

# 15 · 内部链接必须指向存在的文件 —— 一个 404 的链接比没有链接更伤信任
import glob as _g3
_seen_links = 0
for pth in _g3.glob("**/*.md", recursive=True):
    if pth.startswith(".git") or pth.split(os.sep)[0] in SKIP_DIRS: continue
    body = io.open(pth, encoding="utf-8").read()
    body = re.sub(r'```.*?```', '', body, flags=re.S)          # 代码块里的路径是示例
    body = re.sub(r'`[^`\n]*`', '', body)                      # 行内代码同理
    for m in re.finditer(r'\]\(([^)\s]+)\)', body):
        t = m.group(1).split("#")[0]
        if not t or t.startswith(("http://", "https://", "mailto:")): continue
        _seen_links += 1
        tgt = os.path.normpath(os.path.join(os.path.dirname(pth), t))
        check(os.path.exists(tgt), f"{pth}: 链接指向不存在的 {t!r}")

# 16 · 公开榜单页必须与 benchmark/results.json 同步 —— 页面是生成的，不该手改
# the pages' default host is defined once, in build_page.py; rules 17 and 30 read it from there
_bp = io.open("benchmark/build_page.py", encoding="utf-8").read() if os.path.exists("benchmark/build_page.py") else ""
_m = re.search(r'^DEFAULT_SITE = "([^"]+)"', _bp, re.M)
SITE_DEFAULT = _m.group(1) if _m else ""
_m = re.search(r'^ZH_PATH = "([^"]+)"', _bp, re.M)
SITE_ZH_PATH = _m.group(1) if _m else ""
if os.path.isdir("docs") and os.path.exists("benchmark/build_page.py"):
    check(bool(SITE_DEFAULT and SITE_ZH_PATH), "benchmark/build_page.py: DEFAULT_SITE or ZH_PATH not found")
    import subprocess
    # llms.txt 和 sitemap.xml 也是生成的。llms.txt 是 AI 爬虫唯一真会读的那个文件，
    # 上面的旧数字就是直接递给每个引擎的错答案 —— 它必须和 results.json 一起动。
    GEN = tuple(f for f in os.listdir("docs")
                if f.endswith(".html") or f in ("llms.txt", "sitemap.xml"))
    before = {f: io.open(os.path.join("docs", f), encoding="utf-8").read() for f in GEN}
    for need in ("llms.txt", "sitemap.xml"):
        check(need in GEN, f"docs/{need} 不存在 —— 跑一遍 python3 benchmark/build_page.py 并提交")
    check(bool(before), "docs/ 里没有生成物 —— 榜单页应由 benchmark/build_page.py 生成")
    r = subprocess.run([sys.executable, "benchmark/build_page.py"],
                       capture_output=True, text=True)
    check(r.returncode == 0, f"benchmark/build_page.py 跑不通：{(r.stderr or '')[-200:]}")
    if r.returncode == 0:
        for f, old in before.items():
            new = io.open(os.path.join("docs", f), encoding="utf-8").read()
            check(old == new,
                  f"docs/{f} 与 results.json 不同步 —— 跑一遍 python3 benchmark/build_page.py 并提交")
    # 检查不许改被检查的东西：把原文件写回去。否则失败一次之后，第二次运行会因为文件已被重新生成而通过，
    # 推上去的提交里却还是旧页面。
    for f, old in before.items():
        io.open(os.path.join("docs", f), "w", encoding="utf-8").write(old)
    # 双语页必须成对存在，且各自声明了 hreflang（中文用 zh-CN，与官网其他页一致），外加 x-default
    for f in ("index.html", "zh.html"):
        pth = os.path.join("docs", f)
        check(os.path.exists(pth), f"{pth} missing —— 榜单页要中英成对")
        if os.path.exists(pth):
            t = io.open(pth, encoding="utf-8").read()
            check('hreflang="en"' in t and 'hreflang="zh-CN"' in t and 'hreflang="x-default"' in t,
                  f"docs/{f}: 缺少 hreflang（en、zh-CN、x-default），另一种语言的读者与搜索引擎都找不到对应版本")
            check("%(" not in t, f"docs/{f}: 有未替换的模板占位符")

    # ── 17. 分享卡：声明的尺寸必须等于 PNG 真实尺寸 ──
    # 榜单页是这个仓库里最可能被转发的一页。og:image 少了、或者宽高写错，
    # Slack / X / LinkedIn 要么不出图，要么裁成一条。这里直接读 PNG 头核对。
    def png_size(path):
        d = io.open(path, "rb").read(24)
        if d[:8] != b"\x89PNG\r\n\x1a\n" or d[12:16] != b"IHDR":
            return None
        return struct.unpack(">II", d[16:24])
    for f, card in (("index.html", "og.png"), ("zh.html", "og.zh.png")):
        pth, cpth = os.path.join("docs", f), os.path.join("docs", card)
        if not os.path.exists(pth):
            continue
        t = io.open(pth, encoding="utf-8").read()
        check(os.path.exists(cpth),
              f"docs/{card} 不存在 —— 跑一遍 python3 benchmark/build_og.py 并提交")
        check('name="twitter:card" content="summary_large_image"' in t,
              f"docs/{f}: 缺 twitter:card，X 上只会显示一条窄链接")
        _base = os.environ.get("GEO_SITE_BASE", SITE_DEFAULT).rstrip("/")
        # 分享卡带内容指纹（?v=）：官网对 PNG 设了一年的 immutable 缓存，卡片原地覆盖时，没有指纹的地址会一直给出旧数字
        _fp = ""
        if os.path.exists(cpth):
            import hashlib
            _fp = "?v=" + hashlib.sha256(io.open(cpth, "rb").read()).hexdigest()[:10]
        for _meta in ('property="og:image"', 'name="twitter:image"'):
            check(f'{_meta} content="{_base}/{card}{_fp}"' in t,
                  f"docs/{f}: {_meta} 没指向 {card}{_fp}（先跑 build_og.py，再跑 build_page.py）")
        check("rel=\"canonical\"" in t, f"docs/{f}: 缺 canonical")
        if os.path.exists(cpth):
            wh = png_size(cpth)
            check(wh is not None, f"docs/{card} 不是有效的 PNG")
            if wh:
                w, h = wh
                dw = re.search(r'og:image:width" content="(\d+)"', t)
                dh = re.search(r'og:image:height" content="(\d+)"', t)
                check(dw and int(dw.group(1)) == w,
                      f"docs/{f}: og:image:width 写的是 {dw and dw.group(1)}，"
                      f"{card} 实际宽 {w}")
                check(dh and int(dh.group(1)) == h,
                      f"docs/{f}: og:image:height 写的是 {dh and dh.group(1)}，"
                      f"{card} 实际高 {h}")
                check(abs(w / float(h) - 1.91) < 0.06,
                      f"docs/{card} 宽高比 {w/float(h):.2f}，社交卡需要接近 1.91:1，否则会被裁")
                check(os.path.getsize(cpth) < 5 * 1024 * 1024,
                      f"docs/{card} 超过 5MB，多数平台不会抓取")

    # ── 19. 每个行业至少 10 站 ──
    # 榜单页会印每个行业的中位数。两个站的「中位数」不是中位数，
    # 但它印出来和真的一样，读者没办法分辨。
    if os.path.exists("benchmark/sites.json"):
        import collections
        sj = json.load(io.open("benchmark/sites.json", encoding="utf-8"))
        cnt = collections.Counter(x["sector"] for x in sj["sites"])
        thin = sorted((k, v) for k, v in cnt.items() if v < 10)
        check(not thin,
              "sites.json 里这些行业不足 10 站，中位数印出去没有意义：%s"
              % ", ".join("%s(%d)" % t for t in thin))
        # 名单上有 10 个不够：抓不到的站不进中位数。按真正评上分的站数算，不足的行业不许印中位数。
        if os.path.exists("benchmark/results.json"):
            rj = json.load(io.open("benchmark/results.json", encoding="utf-8"))
            scored = collections.Counter(r["sector"] for r in rj["results"] if r.get("normalised") is not None)
            brd = io.open("benchmark/README.md", encoding="utf-8").read()
            for k, n in sorted(scored.items()):
                if n < 10:
                    row = next((ln for ln in brd.splitlines() if ln.startswith("| %s |" % k)), "")
                    check(row and "| — |" in row,
                          f"benchmark/README.md prints a median for {k}, which has only {n} scored sites "
                          f"(python3 benchmark/run.py --readme-only)")
        near = [k for k in cnt if k.replace(" ", "") in
                {x.replace(" ", "") for x in cnt if x != k}]
        check(not near,
              "sites.json 里有只差空格的行业名，会把同一行业劈成两个：%s" % sorted(near))

    # ── 18. llms.txt 里的样本量必须等于 results.json 的 ──
    # 这条和上面的字节比对重叠，但失败信息可读得多：
    # 「llms.txt 写着 105 站，results.json 是 229」比「字节不一致」有用得多。
    # 必须读 before 里那份「提交进仓库的」内容 —— 上面的字节比对已经把磁盘上的文件
    # 重新生成成正确的了，再去读文件这条检查就永远不会响。
    if before.get("llms.txt") and os.path.exists("benchmark/results.json"):
        lt = before["llms.txt"]
        n = json.load(io.open("benchmark/results.json", encoding="utf-8"))["stats"]["n"]
        # llms.txt 是折行的 Markdown 引用块，数字和「well-known sites」之间可能隔着
        # 换行和「> 」。只认单个空格会漏掉第一处，那条检查就成了摆设。
        found = set(int(x) for x in re.findall(r"(\d{2,4})[\s>]+well-known sites", lt))
        check(found == {n},
              "docs/llms.txt 写着 %s 站，results.json 是 %d 站 —— 这是 AI 爬虫唯一会读的"
              "文件，数字错了就是递给每个引擎一个错答案" % (sorted(found) or "没写", n))

# ── 20. 门槛封顶只在得 0 分时触发 —— 每一处文档都得这么说 ──
# v1.1 初稿写的是「门槛项没拿满就封顶」，这个 bug 修了，但 rubric/README、中文校准记录、
# SKILL.md、示例报告里还留着旧说法。规格里写着已修掉的 bug，是挑刺的读者最先会抓的矛盾。
# 提到「封顶 40」的句子必须同时说明是得 0 分时；讲历史的句子（当时 / at the time）放行。
CAP_RE = re.compile(r"\bcap(?:s|ped)?\b[^.。;；]{0,40}?\bat 40|封顶 ?40", re.I)
ZERO_MARK = ("zero", " 0 ", "得 0 分", "0 分", "为零", "零分", "at the time", "当时", "first draft", "初稿")
def cap_sentences(text):
    flat = re.sub(r"\*\*|`", "", re.sub(r"\s+", " ", text))
    return [x for x in re.split(r"(?<=[.。!?！？；;])\s*", flat) if CAP_RE.search(x)]
_cap_files = (["README.md", "README.zh-CN.md", "SKILL.md", "cli/README.md", ".github/CONTRIBUTING.md"]
              + [os.path.join("rubric", f) for f in sorted(os.listdir("rubric"))
                 if f.endswith(".md") and not f.startswith("v1.0")]
              + [os.path.join("examples", f) for f in sorted(os.listdir("examples")) if f.endswith(".md")]
              # the schemas' descriptions are documentation too: the retired rule survived there once
              + [os.path.join("schema", f) for f in sorted(os.listdir("schema")) if f.endswith(".json")]
              + [os.path.join("guide", f) for f in sorted(os.listdir("guide")) if f.endswith(".md")])
for f in _cap_files:
    if not os.path.exists(f): continue
    for x in cap_sentences(io.open(f, encoding="utf-8").read()):
        check(any(m in x.lower() for m in ZERO_MARK),
              "%s 说门槛封顶 40，但没说只在得 0 分时触发（v1.1 修掉的规则）：%s" % (f, x[:160]))

# 封顶是上限（min(norm, 40)），不是把分数定在 40：被封顶的站可以低于 40（js-shell 样例站 15 分），--fail-under 40 照样
# 拦得住。1.5.0 的草稿在 help、action.yml、两份 README、CI 示例和排障指南里写成「正好封顶在 40，所以 --fail-under 40 永远
# 拦不住被封顶的站」。这条扫所有文档、CI 示例、action.yml 和 CLI 的 help 文字。
EXACT_CAP_RE = re.compile(r"\bcaps? (?:a |the |its )?(?:score |result )?at exactly 40|正好封顶"
                          r"|never fails? a capped site|never failed a capped site|拦不住被封顶", re.I)
_exact_cap_files = ["action.yml", "cli/geo_score.py", "cli/geo_watch.py"]
for root_, dirs_, files_ in os.walk("."):
    dirs_[:] = [d for d in dirs_ if d not in SKIP_DIRS + (".github", "raw")]
    _exact_cap_files += [os.path.join(root_, f)[2:] for f in files_ if f.endswith((".md", ".yml", ".html"))]
for f in sorted(set(_exact_cap_files)):
    if not os.path.exists(f): continue
    flat = re.sub(r"\*\*|`", "", re.sub(r"\s+", " ", io.open(f, encoding="utf-8").read()))
    for m in EXACT_CAP_RE.finditer(flat):
        check(False, "%s 说门槛封顶把分数定在 40、--fail-under 40 拦不住被封顶的站；封顶是上限，被封顶的站可以低于 40：…%s…"
              % (f, flat[max(0, m.start() - 60):m.end() + 60]))

# ── 21. 校准记录中英两份：同样多的章节，同一组数字 ──
# 中文版曾漏掉「60 KB 服务端渲染正文」和 Foglift 的上四分位。比集合不比次数：
# 同一个数字中文多提一遍是行文习惯，少了一个数字才是少了一条事实。
def _cal_facts(p):
    t = re.sub(r"\]\([^)]*\)", "]", io.open(p, encoding="utf-8").read())
    return (len(re.findall(r"^## ", t, re.M)),
            {int(x) for x in re.findall(r"(?<![\w.])(\d{2,})(?![\w])", t) if int(x) >= 10})
for base in ("rubric/calibration-v1.1", "rubric/bands-analysis"):
    if not os.path.exists(base + ".md"):
        continue
    (se, ne), (sz, nz) = _cal_facts(base + ".md"), _cal_facts(base + ".zh-CN.md")
    check(se == sz, "%s 中英章节数不同：%d vs %d" % (base, se, sz))
    check(ne == nz, "%s 中英数字不一致 —— 只在英文：%s；只在中文：%s"
          % (base, sorted(ne - nz), sorted(nz - ne)))

# ── 22. 每项检查都要声明证据依据，且 JSON 与中英两份证据表逐行一致 ──
# README 承诺「凡是依据我们自己的观察而非公开研究的检查项，口径里都会注明」。这条让承诺可验证。
EVIDENCE_BASES = ("research", "vendor-doc", "field-observation", "convention")
REPO_URL = "https://github.com/jianruntech/geo-score/blob/main/"
for r in MODERN:
    stem = r[:-3]
    jp = f"rubric/{stem}.json"
    if not os.path.exists(jp): continue
    j = json.load(io.open(jp, encoding="utf-8"))
    tables = {}
    for tp in (f"rubric/evidence-{stem}.md", f"rubric/evidence-{stem}.zh-CN.md"):
        check(os.path.exists(tp), f"{tp} missing — every check's evidence basis must be published in both languages")
        if not os.path.exists(tp): continue
        rows = {}
        for line in io.open(tp, encoding="utf-8").read().splitlines():
            m = re.match(r'^\| `((?:g|p[1-4]|b)\.[a-z0-9-]+)` \|', line)
            if m:
                check(m.group(1) not in rows, f"{tp}: {m.group(1)} has more than one row")
                rows[m.group(1)] = line
        tables[tp] = rows
    ids = [c["id"] for c in j["checks"]]
    for tp, rows in tables.items():
        extra = sorted(set(rows) - set(ids))
        check(not extra, f"{tp}: rows for checks that are not in {jp}: {extra}")
    for c in j["checks"]:
        e = c.get("evidence")
        check(isinstance(e, dict), f"{jp}: {c['id']} has no evidence object")
        if not isinstance(e, dict): continue
        basis, src = e.get("basis"), e.get("sources") or []
        check(basis in EVIDENCE_BASES, f"{jp}: {c['id']} evidence basis {basis!r} is not one of {EVIDENCE_BASES}")
        if basis in ("research", "vendor-doc"):
            check(len(src) >= 1, f"{jp}: {c['id']} claims {basis} but lists no source")
        check(all(isinstance(u, str) and u.startswith("https://") for u in src),
              f"{jp}: {c['id']} has a source that is not an https URL")
        check(bool(re.match(r'^\d{4}-\d{2}-\d{2}$', str(e.get("last_verified", "")))),
              f"{jp}: {c['id']} evidence has no last_verified date (YYYY-MM-DD)")
        for tp, rows in tables.items():
            row = rows.get(c["id"])
            check(row is not None, f"{tp}: no row for {c['id']}")
            if row is None: continue
            check(f"| `{basis}` |" in row, f"{tp}: {c['id']} basis differs from {jp} ({basis})")
            check(f"| {c['points']} |" in row, f"{tp}: {c['id']} points differ from {jp} ({c['points']})")
            check(f"| {e.get('last_verified')} |" in row, f"{tp}: {c['id']} verified date differs from {jp}")
            # 英文表的最后一格就是 evidence.note 原文；只改了表、没改 JSON 的说明会在这里被拦下
            if tp == f"rubric/evidence-{stem}.md" and isinstance(e.get("note"), str):
                check(row.rstrip().endswith(f"| {e['note']} |"),
                      f"{tp}: {c['id']} note differs from evidence.note in {jp} — the English row's last cell is that note, verbatim")
            for u in src:
                if u.startswith(REPO_URL):
                    # 仓库内文件在表里用相对链接；中文表可以指向对应的 .zh-CN.md
                    rel = os.path.relpath(u[len(REPO_URL):].split("#")[0], "rubric")
                    ok_link = any(f"]({x}" in row for x in (rel, rel.replace(".md", ".zh-CN.md")))
                else:
                    ok_link = f"]({u})" in row
                check(ok_link, f"{tp}: {c['id']} row does not link source {u}")

# ── 23. README 引用的 CLI 与人工审计一致度，必须等于 benchmark/validity.json ──
# 「通常低 5 到 15 分」曾是一句没有数据的话；换成实测数字之后，不能让它再悄悄过期。
if os.path.exists("benchmark/validity.json"):
    vj = json.load(io.open("benchmark/validity.json", encoding="utf-8"))
    nd, bm = vj["normalised_difference"], vj["by_method"]
    want = {"%d%%" % round(100 * vj["exact_tier_agreement"]), "%.1f" % -nd["mean"],
            "%d check pairs" % vj["n_check_pairs"],
            "%d%%" % round(100 * bm["rule"]["exact_agreement"]), "%d%%" % round(100 * bm["heuristic"]["exact_agreement"])}
    for f in ("README.md", "cli/README.md"):
        t = " ".join(io.open(f, encoding="utf-8").read().split())
        want_f = set(want) | ({"from %d lower to %d %s" % (-nd["min"], abs(nd["max"]), "higher" if nd["max"] > 0 else "lower")}
                              if f == "README.md" else set())
        missing = [w for w in want_f if w not in t]
        check(not missing, f"{f}: CLI-vs-hand-audit figures must match benchmark/validity.json; missing {missing}")
    tz = " ".join(io.open("README.zh-CN.md", encoding="utf-8").read().split())
    wz = {"%d%%" % round(100 * vj["exact_tier_agreement"]), "%.1f" % -vj["normalised_difference"]["mean"],
          "%d 对" % vj["n_check_pairs"]}
    check(all(w in tz for w in wz), f"README.zh-CN.md: 与人工审计一致度的数字必须等于 benchmark/validity.json：{sorted(wz)}")
    # the like-for-like headline (checks both scored) must be the arithmetic of the per-site rows it summarises
    cc = vj.get("common_checks")
    check(bool(cc), "benchmark/validity.json: no common_checks block (python3 benchmark/validity.py)")
    if cc:
        dd = [s["common_checks_cli_pct"] - s["common_checks_human_pct"] for s in vj["sites"]
              if s.get("common_checks_cli_pct") is not None and s.get("common_checks_human_pct") is not None]
        got = {"n": len(dd), "mean": round(sum(dd) / len(dd), 1) if dd else None, "min": min(dd, default=None),
               "max": max(dd, default=None), "mean_abs": round(sum(abs(x) for x in dd) / len(dd), 1) if dd else None}
        check(all(cc.get(k) == v for k, v in got.items()),
              f"benchmark/validity.json: common_checks {({k: cc.get(k) for k in got})} is not what its sites give {got}")
        # both root READMEs and cli/README.md lead with that like-for-like figure
        en_cc = ["%.1f points %s on average" % (abs(cc["mean"]), "lower" if cc["mean"] < 0 else "higher"),
                 "per site from %d lower to %d %s" % (-cc["min"], abs(cc["max"]), "higher" if cc["max"] > 0 else "lower"),
                 "mean absolute difference %.1f" % cc["mean_abs"]]
        zh_cc = ["平均%s %.1f 分" % ("低" if cc["mean"] < 0 else "高", abs(cc["mean"])),
                 "逐站从低 %d 分到%s %d 分" % (-cc["min"], "高" if cc["max"] > 0 else "低", abs(cc["max"])),
                 "平均绝对差 %.1f 分" % cc["mean_abs"]]
        te = " ".join(io.open("README.md", encoding="utf-8").read().split())
        tc = " ".join(io.open("cli/README.md", encoding="utf-8").read().split())
        miss = ([w for w in en_cc if w not in te] + [w for w in zh_cc if w not in tz]
                + ["cli/README.md: " + w for w in en_cc if w not in tc])
        check(not miss, f"README.md / README.zh-CN.md / cli/README.md: the checks-both-scored figures must be validity.json's "
                        f"common_checks; missing {miss}")
    for f in (f for f in ("README.md", "README.zh-CN.md", "cli/README.md") if os.path.exists(f)):
        t = io.open(f, encoding="utf-8").read()
        check("5 to 15 points" not in t and "低 5 到 15 分" not in t,
              f"{f}: the unmeasured '5 to 15 points' claim is back; quote benchmark/validity.json instead")

# ── 24. AGENTS.md 必须指向真正在执行的检查 ──
# 贡献者和写代码的 agent 从这里读规矩；它提到的入口一旦改名或删掉，这份说明就会悄悄失效。
if os.path.exists("AGENTS.md"):
    ag = io.open("AGENTS.md", encoding="utf-8").read()
    for need in ("scripts/check.sh", "rubric/v1.1.json", "schema/report.v2.json", "schema/watch.v1.json", "guide/stability.md"):
        check(need in ag, f"AGENTS.md must mention {need}")
        check(os.path.exists(need), f"AGENTS.md points at {need}, which does not exist")
    vsrc = io.open(".github/validate.py", encoding="utf-8").read()
    cited = {int(n) for grp in re.findall(r"rules? ([\d, and]+)", ag) for n in re.findall(r"\d+", grp)}
    have = {int(n) for n in re.findall(r"^\s*# (?:── )?(\d+)[ .·]", vsrc, re.M)}
    check(cited <= have, f"AGENTS.md cites validate.py rules that do not exist: {sorted(cited - have)}")
    # the request budget it quotes is the one the e2e test holds the good fixture to
    _gr = re.search(r"^GOOD_REQUESTS = \((\d+), (\d+)\)", io.open("cli/test_geo_score_e2e.py", encoding="utf-8").read(), re.M)
    check(bool(_gr), "cli/test_geo_score_e2e.py no longer defines GOOD_REQUESTS = (site, elsewhere)")
    if _gr:
        want24 = "`GOOD_REQUESTS` (%s to the site, %s elsewhere" % _gr.groups()
        check(want24 in ag, f"AGENTS.md must quote the e2e request budget as {want24!r}")
else:
    check(False, "AGENTS.md missing: contributors and coding agents need the invariants and the gate")

# ── 25. issue 表单：每份都要有名字、说明和 body，报错类的必须要工具版本 ──
# 不带版本号和 JSON 的报错没法复现；表单是唯一能强制要这两样东西的地方。不引入 yaml 依赖，只做形状检查。
for f in sorted(os.listdir(".github/ISSUE_TEMPLATE")) if os.path.isdir(".github/ISSUE_TEMPLATE") else []:
    if not f.endswith(".yml") or f == "config.yml":
        continue
    t = io.open(os.path.join(".github/ISSUE_TEMPLATE", f), encoding="utf-8").read()
    for key in ("name:", "description:", "body:"):
        check(re.search(r"^" + key, t, re.M), f".github/ISSUE_TEMPLATE/{f}: missing top-level {key}")
    ids = re.findall(r"^\s+id: ([a-z_]+)\s*$", t, re.M)
    check(len(ids) == len(set(ids)), f".github/ISSUE_TEMPLATE/{f}: duplicate field ids {ids}")
    check("\t" not in t, f".github/ISSUE_TEMPLATE/{f}: tabs are not valid YAML indentation")
    if f in ("bug_report.yml", "engine_bug.yml"):
        check("id: tool_version" in t, f".github/ISSUE_TEMPLATE/{f}: must ask for the tool version")

# ── 26. README 引用的榜单中位数区间必须等于 benchmark/stats.json ──
if os.path.exists("benchmark/stats.json"):
    sj2 = json.load(io.open("benchmark/stats.json", encoding="utf-8"))
    lo, hi = sj2["overall"]["ci"]
    for f in ("README.md", "README.zh-CN.md", "benchmark/README.md"):
        t = io.open(f, encoding="utf-8").read()
        check("%d–%d" % (lo, hi) in t, f"{f}: the median's 95% interval must read {lo}–{hi} (benchmark/stats.json)")
    # the root READMEs also quote how many rows are thin samples and the median without them
    th2 = sj2.get("thin_sample")
    if th2:
        for f, want in (("README.md", ["%d sites were scored on fewer than" % th2["n_thin"],
                                       "without them the median is %d" % th2["without_thin"]["median"]]),
                        ("README.zh-CN.md", ["其中 %d 个站实际评分的页面不足 %d 个，去掉它们后中位数是 %d"
                                             % (th2["n_thin"], th2["threshold"], th2["without_thin"]["median"])])):
            t = " ".join(io.open(f, encoding="utf-8").read().split())
            missing = [w for w in want if w not in t]
            check(not missing, f"{f}: the thin-sample figures must be benchmark/stats.json's; missing {missing}")

# ── 27. 一行安装从发布的 tag 下载，不从 main ──
# main 上的代码随时在变：README 教的那行命令，今天和明天可能跑的不是同一个 CLI。schema 的 $id 是标识符，不算下载。
for root_, dirs_, files_ in os.walk("."):
    dirs_[:] = [d for d in dirs_ if d not in SKIP_DIRS]
    for f in files_:
        if not f.endswith((".md", ".yml", ".yaml", ".py", ".html", ".txt")) or f == "validate.py":
            continue
        pth = os.path.join(root_, f)
        t = io.open(pth, encoding="utf-8", errors="replace").read()
        check("raw.githubusercontent.com/jianruntech/geo-score/main/cli" not in t,
              f"{pth}: downloads the CLI from main; pin it to a release tag (python3 scripts/release.py X.Y.Z --bump)")
        # an install from the git URL without @vX.Y.Z installs whatever main is today; the changelogs may
        # describe the feature without pinning
        if not f.startswith("CHANGELOG"):
            check(not re.search(r"git\+https://github\.com/jianruntech/geo-score(?!@v)(?![\w.-])", t),
                  f"{pth}: installs from the git URL without a release tag (@vX.Y.Z)")
            # a git clone in a document checks out the release, as release.py --bump pins it, never main
            check(not re.search(r"git clone (?!--branch v\d+\.\d+\.\d+ --depth 1 )[^\n`]*github\.com/jianruntech/geo-score", t),
                  f"{pth}: clones main; use git clone --branch vX.Y.Z --depth 1 https://github.com/jianruntech/geo-score")

# ── 28. 每个发布过的 tag 在中英两份更新日志里都有自己的一节 ──
import subprocess as _sp
try:
    _tags = [t[1:] for t in _sp.run(["git", "tag", "-l", "v*.*.*"], capture_output=True, text=True).stdout.split()]
except OSError:
    _tags = []
for c in ("CHANGELOG.md", "CHANGELOG.zh-CN.md"):
    t = io.open(c, encoding="utf-8").read()
    for v in _tags:
        check(re.search(r"^## \[%s\]" % re.escape(v), t, re.M), f"{c}: tag v{v} has no '## [{v}]' section")
        check(re.search(r"^\[%s\]: https://github\.com/jianruntech/geo-score/" % re.escape(v), t, re.M),
              f"{c}: no compare link for [{v}]")
    check(len(re.findall(r"^## \[Unreleased\]", t, re.M)) <= 1, f"{c}: more than one [Unreleased] section")

# ── 29. 榜单每个有分的站，都要有它的完整报告，分数一致 ──
# results.json 只存汇总；benchmark/raw/ 让别人能逐项复核。两边对不上，就是有一边不是这一轮的。
if os.path.isdir("benchmark/raw") and os.path.exists("benchmark/results.json"):
    rj2 = json.load(io.open("benchmark/results.json", encoding="utf-8"))
    names = set(os.listdir("benchmark/raw"))
    scored = [r for r in rj2["results"] if r.get("normalised") is not None]
    for r in scored:
        fn = re.sub(r"[^A-Za-z0-9.\-]+", "__", r["site"].strip("/")) + ".json"
        if fn not in names:
            check(False, f"benchmark/raw/{fn} missing for {r['site']}")
            continue
        raw = json.load(io.open(os.path.join("benchmark/raw", fn), encoding="utf-8"))
        check(raw.get("normalised") == r["normalised"],
              f"benchmark/raw/{fn} scores {raw.get('normalised')}, results.json says {r['normalised']}")
    check(len(names) == len(scored), f"benchmark/raw has {len(names)} files for {len(scored)} scored sites")

# ── 30. The leaderboard's canonical URLs are the ones the READMEs link ──
# The Pages copy kept declaring itself canonical long after it stopped updating, so engines were told
# the stale page was the real one. Each page's canonical must be the leaderboard link its README gives,
# and every leaderboard link in that README must be that canonical.
for page, readme in (("docs/index.html", "README.md"), ("docs/zh.html", "README.zh-CN.md")):
    if not (os.path.exists(page) and os.path.exists(readme)):
        continue
    m = re.search(r'<link rel="canonical" href="([^"]+)">', io.open(page, encoding="utf-8").read())
    canon = m.group(1) if m else None
    links = set(re.findall(r'\]\((https?://[^)\s]*/leaderboard[^)\s]*)\)', io.open(readme, encoding="utf-8").read()))
    check(canon in links, f"{page}: canonical {canon} is not the leaderboard URL {readme} links ({sorted(links)})")
    check(links <= {canon}, f"{readme}: links the leaderboard as {sorted(links - {canon})}, but {page} declares {canon}")
    want = os.environ.get("GEO_SITE_BASE", SITE_DEFAULT).rstrip("/") + (SITE_ZH_PATH if page.endswith("zh.html") else "")
    check(canon == want, f"{page}: canonical {canon} is not {want}, the base build_page.py builds for "
                         f"(python3 benchmark/build_page.py)")

# ── 31. The China-gap block in benchmark/README.md quotes stats.json ──
# "Sites built for the Chinese market score 20 points lower" was one sentence over a sector label. The block that
# replaced it states the definition, the language gap, the matched families and the heuristic bound; each of its
# figures has to be the one stats.json holds (python3 benchmark/run.py --readme-only rewrites both).
if os.path.exists("benchmark/stats.json") and os.path.exists("benchmark/README.md"):
    sj3 = json.load(io.open("benchmark/stats.json", encoding="utf-8"))
    m = re.search(r"<!-- china-gap:.*?-->(.*?)<!-- /china-gap -->", io.open("benchmark/README.md", encoding="utf-8").read(), re.S)
    check(bool(m), "benchmark/README.md: no generated China-gap block (python3 benchmark/run.py --readme-only)")
    g, d = sj3["china_gap"], sj3.get("china_gap_detail")
    if m:
        blk = " ".join(m.group(1).split())
        want = ["score %d points lower** (95%% CI %d–%d): median %d against %d for the other %d scored sites"
                % (g["gap"], g["ci"][0], g["ci"][1], g["median_china"], g["median_rest"], g["n_rest"])]
        if d:
            lg, x, f, mt, kg = d["by_language"], d["crosstab"], d["families"], d["by_method"], d["knowledge_graph"]["by_language"]
            want += ["the %d Chinese-language sites score %d points lower than the %d others (95%% CI %d–%d)"
                     % (lg["n_group"], lg["gap"], lg["n_vs"], lg["ci"][0], lg["ci"][1]),
                     "%d of the %d China-sector sites" % (x["china"]["other"], x["china"]["zh"] + x["china"]["other"]),
                     "%d sites in other sectors serve Chinese" % x["rest"]["zh"],
                     "on %d of %d Chinese-language sites against %d of %d others"
                     % (kg["zh"]["unobservable"], kg["zh"]["n"], kg["other"]["unobservable"], kg["other"]["n"]),
                     "the gap would be %s points" % " or ".join(str(d["kg_imputed"][k]["gap"])
                                                                for k in sorted(d["kg_imputed"], key=int))]
            if f["range"]:
                want += ["gap runs from %d points (" % f["range"][0], ") to %d (" % f["range"][1]]
            if mt["heuristic_share_pct"] is not None:
                want += ["the gap is %.1f points, and %.1f of them" % (mt["total"], mt["heuristic"]),
                         "at most %d%% of the gap" % mt["heuristic_share_pct"]]
        missing = [w for w in want if w not in blk]
        check(not missing, f"benchmark/README.md: the China-gap block does not match benchmark/stats.json; missing {missing} "
                           f"(python3 benchmark/run.py --readme-only)")

# ── 32. The reproducibility tables are what retest.py derives from the committed records ──
# The ±5 figure was once compared by a `python3 -c "..."` step nobody committed. retest.py now derives every
# figure in reproducibility.json and every table in REPRODUCIBILITY.md from the records in that file.
if os.path.exists("benchmark/retest.py") and os.path.exists("benchmark/reproducibility.json"):
    import subprocess
    r = subprocess.run([sys.executable, "benchmark/retest.py", "--check"], capture_output=True, text=True)
    check(r.returncode == 0, "benchmark/reproducibility.json or REPRODUCIBILITY.md is not what retest.py derives: "
                             + ((r.stderr or r.stdout).strip()[-300:] or "exit %d" % r.returncode))

# ── 33. The sample the benchmark README describes is the one raw/ records ──
# "The same eight-page sample" was printed over 55 rows scored on a single page. The opening sentence counts the rows
# scored on fewer than stats.py's THIN_N pages, and the Every-site table marks each of them with its page count.
if os.path.isdir("benchmark/raw") and os.path.exists("benchmark/results.json") and os.path.exists("benchmark/stats.py"):
    _m = re.search(r"^THIN_N = (\d+)", io.open("benchmark/stats.py", encoding="utf-8").read(), re.M)
    check(bool(_m), "benchmark/stats.py: THIN_N not found")
    brd_raw = io.open("benchmark/README.md", encoding="utf-8").read()
    if _m:
        thin_n, sn = int(_m.group(1)), {}
        for r in json.load(io.open("benchmark/results.json", encoding="utf-8"))["results"]:
            if r.get("normalised") is None:
                continue
            fn = os.path.join("benchmark/raw", re.sub(r"[^A-Za-z0-9.\-]+", "__", r["site"].strip("/")) + ".json")
            if r.get("sample_n") is not None:
                sn[r["site"]] = r["sample_n"]
            elif os.path.exists(fn):
                sn[r["site"]] = len(json.load(io.open(fn, encoding="utf-8")).get("sampled_urls") or [])
        thin_sites = {x for x, k in sn.items() if k < thin_n}
        want = ("on up to eight pages per site; %d sites were scored on fewer than %d pages (%d of them on a single page)"
                % (len(thin_sites), thin_n, sum(1 for k in sn.values() if k == 1)))
        check(want in " ".join(brd_raw.split()),
              f"benchmark/README.md: the sample sentence must read '{want}', as raw/ gives (python3 benchmark/run.py --readme-only)")
        check("eight-page sample" not in brd_raw, "benchmark/README.md: 'the same eight-page sample' is back; raw/ says otherwise")
        marked = dict(re.findall(r"^\| \d+ \| (\S+) \*\(thin sample: (\d+) pages?\)\* \|", brd_raw, re.M))
        check(set(marked) == thin_sites,
              "benchmark/README.md: the rows marked thin sample are not the ones raw/ gives; unmarked %s, marked in error %s"
              % (sorted(thin_sites - set(marked))[:5], sorted(set(marked) - thin_sites)[:5]))
        check(all(int(k) == sn.get(x) for x, k in marked.items()),
              "benchmark/README.md: a thin-sample page count differs from raw/: %s"
              % sorted(x for x, k in marked.items() if int(k) != sn.get(x))[:5])

# ── 34. The leaderboard's Dataset markup describes the data it links ──
# It once called `readiness` the 0-100 score (that is `normalised`; readiness is raw points) and pointed its download
# at a blob/main page that moves with every run. Every variableMeasured name must be a key of every scored row, and
# every download must be a file in benchmark/ at the tag of the CLI version the page was built with.
if os.path.exists("benchmark/results.json") and os.path.exists("cli/geo_score.py"):
    _rows = [r for r in json.load(io.open("benchmark/results.json", encoding="utf-8"))["results"]
             if r.get("normalised") is not None]
    _ver = re.search(r'^__version__ = "([^"]+)"', io.open("cli/geo_score.py", encoding="utf-8").read(), re.M).group(1)
    for page in ("docs/index.html", "docs/zh.html"):
        if not os.path.exists(page):
            continue
        _m = re.search(r'<script type="application/ld\+json">(.*?)</script>', io.open(page, encoding="utf-8").read(), re.S)
        try:
            _ld = json.loads(_m.group(1)) if _m else None
        except ValueError as e:
            _ld = None
            check(False, f"{page}: the JSON-LD block does not parse ({e})")
        _ds = [x for x in (_ld or {}).get("@graph", []) if x.get("@type") == "Dataset"]
        check(len(_ds) == 1, f"{page}: expected one Dataset in the JSON-LD, found {len(_ds)}")
        if not _ds:
            continue
        names = [v.get("name") for v in _ds[0].get("variableMeasured", [])]
        bad = sorted({n for n in names if any(n not in r for r in _rows)})
        check(names and not bad, f"{page}: variableMeasured names {bad or names} are not keys of every scored row "
                                 f"in benchmark/results.json")
        for d in _ds[0].get("distribution", []):
            u = d.get("contentUrl", "")
            m2 = re.match(r"^https://raw\.githubusercontent\.com/jianruntech/geo-score/v([\d.]+)/(benchmark/[\w.-]+)$", u)
            check(bool(m2) and m2.group(1) == _ver,
                  f"{page}: download {u} is not pinned to v{_ver}/benchmark/ (python3 benchmark/build_page.py)")
            if m2:
                check(os.path.exists(m2.group(2)), f"{page}: download {u} names {m2.group(2)}, which does not exist")

# ── 35. results.csv and checks.csv are results.json and raw/, flattened ──
# The per-check points used to exist only in 317 nested reports. The flat files are generated with the README
# (python3 benchmark/run.py --readme-only); each cell has to be what results.json and raw/ hold for that site.
if os.path.exists("benchmark/results.json") and os.path.isdir("benchmark/raw"):
    import csv as _csv
    for f in ("benchmark/results.csv", "benchmark/checks.csv"):
        check(os.path.exists(f), f"{f} missing (python3 benchmark/run.py --readme-only)")
    if os.path.exists("benchmark/results.csv") and os.path.exists("benchmark/checks.csv"):
        rj5 = json.load(io.open("benchmark/results.json", encoding="utf-8"))
        ids5 = [c["id"] for c in json.load(io.open("rubric/v1.1.json", encoding="utf-8"))["checks"]]

        def _cell(v):
            return "" if v is None else ("true" if v is True else "false" if v is False else str(v))
        with io.open("benchmark/results.csv", encoding="utf-8", newline="") as f:
            rows5 = list(_csv.DictReader(f))
        with io.open("benchmark/checks.csv", encoding="utf-8", newline="") as f:
            long5 = list(_csv.reader(f))
        check([r["site"] for r in rows5] == sorted(r["site"] for r in rj5["results"]),
              "benchmark/results.csv: not one row per site in results.json, sorted by site (python3 benchmark/run.py --readme-only)")
        by5, bad5, want_long = {r["site"]: r for r in rj5["results"]}, [], []
        for row in rows5:
            r = by5.get(row["site"])
            if r is None:
                continue
            if r.get("normalised") is None:
                exp = {"sector": r["sector"], "error": r.get("error"), "normalised": None}
                exp.update({c: None for c in ids5})
            else:
                fn = os.path.join("benchmark/raw", re.sub(r"[^A-Za-z0-9.\-]+", "__", r["site"].strip("/")) + ".json")
                if not os.path.exists(fn):
                    continue                                   # rule 29 reports the missing report
                rep = json.load(io.open(fn, encoding="utf-8"))
                st5 = {c["id"]: c for c in rep["checks"]}
                exp = {k: r.get(k) for k in ("sector", "normalised", "readiness", "observable_max", "band",
                                             "gate_reason", "resolved_to", "tool_version")}
                exp.update(gate_capped=bool(r.get("gate_capped")), measured_at=rep.get("audited_at"),
                           sample_n=len(rep.get("sampled_urls") or []), sample_source=rep.get("sample_source"), error=None)
                exp.update({c: st5[c].get("points") if c in st5 and st5[c].get("state") == "scored" else None for c in ids5})
                for c in ids5:
                    if c in st5:
                        sc = st5[c].get("state") == "scored"
                        want_long.append([r["site"], c, st5[c].get("state"), _cell(st5[c].get("points") if sc else None),
                                          _cell(st5[c].get("max") if sc else None)])
            diff5 = [k for k, v in exp.items() if row.get(k) != _cell(v)]
            if diff5:
                bad5.append("%s (%s)" % (row["site"], ", ".join(diff5[:3])))
        check(not bad5, f"benchmark/results.csv differs from results.json and raw/ for {len(bad5)} sites: {bad5[:3]} "
                        f"(python3 benchmark/run.py --readme-only)")
        check(long5[:1] == [["site", "check_id", "state", "points", "max"]] and long5[1:] == want_long,
              "benchmark/checks.csv is not the checks in raw/, one row per scored site and check "
              "(python3 benchmark/run.py --readme-only)")

# ── 36. The weight-sensitivity study is what sensitivity.py derives from results.json and raw/ ──
# It first recomputes every published score from the per-check points and stops on any mismatch, so this rule also
# fails when a raw report and results.json disagree on the arithmetic.
if os.path.exists("benchmark/sensitivity.py"):
    import subprocess
    r = subprocess.run([sys.executable, "benchmark/sensitivity.py", "--check"], capture_output=True, text=True)
    check(r.returncode == 0, "benchmark/sensitivity.json or SENSITIVITY*.md is not what sensitivity.py derives: "
                             + ((r.stderr or r.stdout).strip()[-300:] or "exit %d" % r.returncode))

# ── 37. Where the band cuts fall: percentiles.json, the README table and the dated bands analysis agree ──
# The cuts were borrowed from a vendor ladder and never set against the benchmark. percentiles.py places them in the
# field; the README table between the markers must quote it, and rubric/bands-analysis.md (+zh), a record of the run
# it names, must quote the same shares while percentiles.json still describes that run.
if os.path.exists("benchmark/percentiles.py"):
    import subprocess
    r = subprocess.run([sys.executable, "benchmark/percentiles.py", "--check"], capture_output=True, text=True)
    check(r.returncode == 0, "benchmark/percentiles.json is not what percentiles.py derives: "
                             + ((r.stderr or r.stdout).strip()[-300:] or "exit %d" % r.returncode))
if os.path.exists("benchmark/percentiles.json"):
    pj = json.load(io.open("benchmark/percentiles.json", encoding="utf-8"))
    o7, f7, g7 = pj["overall"], pj["uncapped"], pj["gate_cap"]

    def _pc(n, of):
        return "%d%%" % round(100.0 * n / of)
    m = re.search(r"<!-- bands:.*?-->(.*?)<!-- /bands -->", io.open("benchmark/README.md", encoding="utf-8").read(), re.S)
    check(bool(m), "benchmark/README.md: no generated band-cut block (python3 benchmark/run.py --readme-only)")
    rows7 = ["| %s | %s | %d of %d | %s | %s |" % (pj["cuts"][c], c, o7["at_or_above"][c]["n"], o7["n"],
                                                  _pc(o7["at_or_above"][c]["n"], o7["n"]),
                                                  _pc(f7["at_or_above"][c]["n"], f7["n"])) for c in pj["cuts"]]
    if m:
        blk = " ".join(m.group(1).split())
        want = rows7 + ["%d sites score exactly %d, %d of them" % (g7["at_cap"], g7["score"], g7["at_cap_capped"]),
                        "band holds %d sites, %d of them capped" % (g7["band_n"], g7["band_capped"])]
        missing = [w for w in want if w not in blk]
        check(not missing, f"benchmark/README.md: the band-cut block does not match benchmark/percentiles.json; missing "
                           f"{missing[:3]} (python3 benchmark/run.py --readme-only)")
    for f in ("rubric/bands-analysis.md", "rubric/bands-analysis.zh-CN.md"):
        if not os.path.exists(f):
            continue
        t = " ".join(io.open(f, encoding="utf-8").read().split())
        if pj["source"]["measured_at"] not in t:
            continue                          # a record of an earlier run: its figures describe that run
        want = ["| %s |" % c for c in pj["cuts"]] + ["%d" % o7["n"], "%d" % f7["n"]]
        want += ["%d" % o7["at_or_above"][c]["n"] for c in pj["cuts"]] + [_pc(o7["at_or_above"][c]["n"], o7["n"])
                                                                         for c in pj["cuts"]]
        want += ["%d" % pj["noise"]["near_any_cut"], "%s" % pj["noise"]["sem"], "%d" % g7["band_capped"]]
        missing = [w for w in want if w not in t]
        check(not missing, f"{f}: quotes the {pj['source']['measured_at']} run, but not these benchmark/percentiles.json "
                           f"figures: {missing[:5]}")
    # the root READMEs quote the share of sites that reach the lowest band and the highest
    c7 = sorted(pj["cuts"], key=int)
    lo7, hi7 = (_pc(o7["at_or_above"][c]["n"], o7["n"]) for c in (c7[0], c7[-1]))
    for f, w in (("README.md", "%s of %d sites reach %s and %s reach %s" % (lo7, o7["n"], pj["cuts"][c7[0]], hi7,
                                                                             pj["cuts"][c7[-1]])),
                 ("README.zh-CN.md", "%d 个站中 %s 达到起步期，%s 达到领先" % (o7["n"], lo7, hi7))):
        t = " ".join(io.open(f, encoding="utf-8").read().split())
        check(w in t, f"{f}: the band shares must be benchmark/percentiles.json's; missing '{w}'")

# ── 38. The root READMEs quote the China-gap decomposition from benchmark/stats.json ──
# They once quoted the sector-label gap alone. Now they give its definition, the gap by the language a site serves,
# the range within matched sector families and the heuristic share, and each figure must be the one stats.json holds.
if os.path.exists("benchmark/stats.json"):
    d8 = json.load(io.open("benchmark/stats.json", encoding="utf-8"))
    g8, x8 = d8["china_gap"], d8.get("china_gap_detail")
    en8 = ["five China sectors score **%d points lower** than everyone else (95%% CI %d–%d; median %d against %d"
           % (g8["gap"], g8["ci"][0], g8["ci"][1], g8["median_china"], g8["median_rest"])]
    zh8 = ["五个中国行业的站比其余站**低 %d 分**（95%% 置信区间 %d–%d；中位 %d 对 %d"
           % (g8["gap"], g8["ci"][0], g8["ci"][1], g8["median_china"], g8["median_rest"])]
    if x8:
        lg8, fr8, hs8 = x8["by_language"], x8["families"]["range"], x8["by_method"]["heuristic_share_pct"]
        en8.append("the %d Chinese-language sites score %d points lower than the %d others (95%% CI %d–%d)"
                   % (lg8["n_group"], lg8["gap"], lg8["n_vs"], lg8["ci"][0], lg8["ci"][1]))
        zh8.append("%d 个中文站比其余 %d 个站低 %d 分（95%% 置信区间 %d–%d）"
                   % (lg8["n_group"], lg8["n_vs"], lg8["gap"], lg8["ci"][0], lg8["ci"][1]))
        if fr8:
            en8.append("the gap runs from %d to %d points" % tuple(fr8))
            zh8.append("差距在 %d 到 %d 分之间" % tuple(fr8))
        if hs8 is not None:
            en8.append("%d%% of the gap sits in checks the CLI reads with a heuristic, so at most that share" % hs8)
            zh8.append("差距的 %d%% 落在 CLI 靠启发式判断的检查项上，所以最多" % hs8)
    for f, want in (("README.md", en8), ("README.zh-CN.md", zh8)):
        t8 = " ".join(io.open(f, encoding="utf-8").read().split())
        missing = [w for w in want if w not in t8]
        check(not missing, f"{f}: the China-gap figures must be benchmark/stats.json's; missing {missing}")

# ── 39. Where a README or the troubleshooting guide says which tool and day measured the leaderboard, it is results.json's ──
# "the leaderboard above was measured with 1.3.0" is true until the leaderboard is re-run; a sentence that names the
# tool must then change with it, not be found stale by a reader.
if os.path.exists("benchmark/results.json"):
    rj9 = json.load(io.open("benchmark/results.json", encoding="utf-8"))
    tool9 = (rj9.get("tool") or "").rsplit("/", 1)[-1]
    day9, n9 = rj9.get("measured_at"), sum(1 for r in rj9["results"] if "error" not in r)
    V9, D9 = r"(?P<v>\d+\.\d+\.\d+)", r"(?P<d>\d{4}-\d\d-\d\d)"
    said9 = {"README.md": [r"leaderboard above was measured with " + V9, r"benchmark was run with %s on %s" % (V9, D9)],
             "README.zh-CN.md": [r"上面的榜单是用 ?%s ?测的" % V9, r"榜单是 ?%s ?用 ?%s ?跑的" % (D9, V9)],
             "guide/troubleshooting.md": [r"the current run scored (?P<n>\d+) sites on %s with tool %s" % (D9, V9)],
             "guide/troubleshooting.zh-CN.md": [r"当前这一轮是 ?%s ?用 ?%s ?跑的，(?P<n>\d+) ?站有分" % (D9, V9)]}
    for f, pats in said9.items():
        if not os.path.exists(f): continue
        t9 = " ".join(io.open(f, encoding="utf-8").read().split())
        for pat in pats:
            for m in re.finditer(pat, t9):
                g = m.groupdict()
                check(g["v"] == tool9, f"{f}: says the leaderboard was measured with {g['v']}; results.json's tool is {tool9}")
                check(g.get("d") in (None, day9), f"{f}: dates the leaderboard {g.get('d')}; results.json says {day9}")
                check(g.get("n") in (None, str(n9)), f"{f}: says {g.get('n')} sites were scored; results.json has {n9}")

if fail:
    print("FAIL")
    for f in fail: print("  ·", f)
    sys.exit(1)
print(f"OK — {len(rub)} rubric version(s) ({len(MODERN)} tiered), {_seen_links} internal links resolve, "
      f"scope rule clean, metadata consistent")
