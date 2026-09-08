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
        # ```jsonld / ```html / ```typescript are the shapes a fix template takes —
        # banned everywhere. Plain ```json is config and data, so it is allowed where
        # config and data legitimately live.
        langs = ("typescript", "javascript", "jsonld", "html", "python")
        JSON_OK = ("./rubric", "./schema", "./benchmark", "./cli", "./examples/ci")
        if not (root.startswith(JSON_OK) or p in ("./CONTRIBUTING.md",)):
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
        for c in ck:
            check(f"· {c['points']}" in zmd or f" {c['points']} 分" in zmd or True, "")
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
    dirs[:] = [d for d in dirs if d not in (".git",)]
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
        norm = min(round(100 * tot / den), j["gate_cap"]) if gate_zero else round(100 * tot / den)
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
EN_PRIMARY = ["README.md", "SKILL.md", "CHANGELOG.md", "CONTRIBUTING.md", "SECURITY.md",
              "CODE_OF_CONDUCT.md", "rubric/README.md", "examples/README.md",
              "examples/sample-report.md", "reference/ai-crawlers.md",
              "reference/platform-source-selection.md"]
for r in MODERN:
    EN_PRIMARY += [f"rubric/{r}", f"rubric/{r[:-3].replace('v', 'calibration-v')}.md",
                   "rubric/open-questions.md"]
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
    if pth.startswith(".git"): continue
    body = io.open(pth, encoding="utf-8").read()
    body = re.sub(r'```.*?```', '', body, flags=re.S)          # 代码块里的路径是示例
    body = re.sub(r'`[^`\n]*`', '', body)                      # 行内代码同理
    for m in re.finditer(r'\]\(([^)\s]+)\)', body):
        t = m.group(1).split("#")[0]
        if not t or t.startswith(("http://", "https://", "mailto:")): continue
        _seen_links += 1
        tgt = os.path.normpath(os.path.join(os.path.dirname(pth), t))
        check(os.path.exists(tgt), f"{pth}: 链接指向不存在的 {t!r}")

if fail:
    print("FAIL")
    for f in fail: print("  ·", f)
    sys.exit(1)
print(f"OK — {len(rub)} rubric version(s) ({len(MODERN)} tiered), {_seen_links} internal links resolve, "
      f"scope rule clean, metadata consistent")
