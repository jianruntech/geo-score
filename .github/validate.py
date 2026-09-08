#!/usr/bin/env python3
"""Structural checks. Keeps the repo honest about its own scope rules."""
import io, os, re, sys

fail = []

def check(cond, msg):
    if not cond: fail.append(msg)

# 1 · rubric weights must sum to 100
rub = sorted(f for f in os.listdir("rubric") if re.match(r'v[\d.]+\.md', f))
check(bool(rub), "rubric/ contains no versioned rubric")
for r in rub:
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
        for lang in ("typescript", "javascript", "json", "jsonld", "html", "python"):
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
for r in rub:
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

if fail:
    print("FAIL")
    for f in fail: print("  ·", f)
    sys.exit(1)
print(f"OK — {len(rub)} rubric version(s), scope rule clean, metadata consistent")
