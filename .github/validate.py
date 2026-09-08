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

if fail:
    print("FAIL")
    for f in fail: print("  ·", f)
    sys.exit(1)
print(f"OK — {len(rub)} rubric version(s), scope rule clean, metadata consistent")
