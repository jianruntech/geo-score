#!/usr/bin/env python3
"""Render the share card for the leaderboard pages.

Without an og:image and a twitter:card, the leaderboard renders in Slack, X and
LinkedIn as a bare link — which is the one page in this repository people are
most likely to pass around. The card carries the measurement itself, not a logo:
the share of sites that cannot be cited at all, the median, and the real
distribution across the five bands. Regenerate it whenever results.json changes.

    python3 benchmark/build_og.py            # writes docs/og.png, docs/og.zh.png
"""
import io, json, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DOCS = os.path.join(ROOT, "docs")

# Band order and names come from results.json's own `band` field, which run.py
# derived from the rubric. Re-declaring the boundaries here would be exactly the
# drift .github/validate.py exists to catch.
BANDS = [("Not started", "未起步"), ("Early", "起步"), ("Growing", "在建"),
         ("Solid", "扎实"), ("Leading", "领先")]
COL = ["#C4705F", "#C9A227", "#A9854C", "#26714F", "#4FAE80"]

CARD = '''<!doctype html><html><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=IBM+Plex+Mono:wght@400;500&family=Noto+Serif+SC:wght@600;700&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box}  /* 没有这一条，padding 会把 body 顶成 730px，页脚正好落在被裁掉的那 100px 里 */
html,body{margin:0;width:1200px;height:630px;overflow:hidden}
body{background:#0B120E;color:#E7ECE7;
  font-family:"IBM Plex Mono",ui-monospace,monospace;
  display:flex;flex-direction:column;padding:50px 64px;
  background-image:linear-gradient(#1E2A24 1px,transparent 1px);background-size:100%% 42px}
.eyebrow{font-size:15px;letter-spacing:.22em;color:#A9854C;font-weight:500}
h1{margin:22px 0 0;font-family:%(serif)s,Georgia,serif;font-weight:700;
  font-size:%(hsize)spx;line-height:1.12;letter-spacing:-.01em;max-width:19ch;
  text-wrap:balance}
h1 em{font-style:normal;color:#4FAE80}
.sub{margin-top:20px;font-size:18px;line-height:1.6;color:#A7B4AC;max-width:58ch}
.spacer{flex:1}
.dist{display:flex;height:13px;border:1px solid #2C3B33}
.dist i{display:block;height:100%%}
.legend{display:flex;gap:24px;margin-top:14px;font-size:14px;color:#5F6761;
  flex-wrap:wrap;align-items:baseline}
.legend span{display:flex;gap:7px;align-items:baseline}
.legend b{color:#E7ECE7;font-weight:500;font-variant-numeric:tabular-nums}
.legend u{text-decoration:none;width:8px;height:8px;display:inline-block;position:relative;top:-1px}
.foot{display:flex;justify-content:space-between;align-items:flex-end;
  margin-top:26px;padding-top:18px;border-top:1px solid #2C3B33;font-size:16px;color:#5F6761}
.foot b{color:#A7B4AC;font-weight:400}
.big{font-family:%(serif)s,Georgia,serif;font-size:20px;color:#E7ECE7}
</style></head><body>
<p class="eyebrow">JIANRUNTECH / GEO-SCORE</p>
<h1>%(head)s</h1>
<p class="sub">%(sub)s</p>
<div class="spacer"></div>
<div class="dist">%(bars)s</div>
<div class="legend">%(legend)s</div>
<div class="foot"><span class="big">%(median)s</span><b>github.com/jianruntech/geo-score</b></div>
</body></html>'''


def build(stats, results):
    """`readiness` is raw points out of observable_max; the 0-100 figure the bands
    and the published stats use is `normalised`. Count the stored band directly."""
    scored = [r for r in results if isinstance(r.get("normalised"), int)]
    n = len(scored)
    capped = sum(1 for r in scored if r.get("gate_capped"))
    counts = [sum(1 for r in scored if r.get("band") == name) for name, _ in BANDS]
    if sum(counts) != n:
        raise RuntimeError("band names in results.json do not match this script: %r"
                           % sorted(set(r.get("band") for r in scored)))
    return n, capped, counts


def render(lang, n, capped, counts, stats):
    pct = int(round(100.0 * capped / n))
    total = float(sum(counts)) or 1.0
    bars = "".join('<i style="width:%.4f%%;background:%s"></i>' % (100 * c / total, COL[i])
                   for i, c in enumerate(counts))
    if lang == "en":
        legend = "".join(
            '<span><u style="background:%s"></u>%s <b>%d</b></span>' % (COL[i], BANDS[i][0], counts[i])
            for i in range(5))
        v = dict(serif='"Fraunces"', hsize=54,
                 head="%d%% of these sites <em>cannot be cited</em> at all." % pct,
                 sub="%d well-known sites scored on whether an AI answer engine can find, parse, "
                     "trust and cite them. Open rubric, every check reproducible." % n,
                 median="Median %s &nbsp;·&nbsp; range %d&ndash;%d"
                        % (stats["median"], stats["min"], stats["max"]),
                 bars=bars, legend=legend)
    else:
        legend = "".join(
            '<span><u style="background:%s"></u>%s <b>%d</b></span>' % (COL[i], BANDS[i][1], counts[i])
            for i in range(5))
        v = dict(serif='"Noto Serif SC"', hsize=50,
                 head="这些站点里 %d%% <em>根本无法被引用</em>" % pct,
                 sub="%d 个知名网站的实测评分，衡量 AI 回答引擎能不能找到、读懂、信任并引用它们。"
                     "口径公开，每一项都可复算。" % n,
                 median="中位数 %s &nbsp;·&nbsp; 区间 %d&ndash;%d"
                        % (stats["median"], stats["min"], stats["max"]),
                 bars=bars, legend=legend)
    return CARD % v


def shoot(html, out):
    chrome = None
    for c in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "google-chrome", "chromium", "chromium-browser"):
        if os.path.exists(c) or subprocess.call(["which", c],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
            chrome = c
            break
    if not chrome:
        raise RuntimeError("no Chrome found — install Chrome or Chromium to rebuild the card")
    fd, tmp = tempfile.mkstemp(suffix=".html")
    os.close(fd)
    io.open(tmp, "w", encoding="utf-8").write(html)
    # 2x for retina; the declared og:image dimensions must match the real file.
    subprocess.check_call([chrome, "--headless", "--disable-gpu", "--hide-scrollbars",
                           "--force-device-scale-factor=2", "--window-size=1200,630",
                           "--virtual-time-budget=4000",
                           "--screenshot=" + out, "file://" + tmp],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.unlink(tmp)


def main():
    d = json.load(io.open(os.path.join(HERE, "results.json"), encoding="utf-8"))
    n, capped, counts = build(d["stats"], d["results"])
    for lang, name in (("en", "og.png"), ("zh", "og.zh.png")):
        out = os.path.join(DOCS, name)
        shoot(render(lang, n, capped, counts, d["stats"]), out)
        print("%s  %.0f KB" % (name, os.path.getsize(out) / 1024.0))
    print("%d scored, %d gate-capped (%d%%), bands %s"
          % (n, capped, round(100.0 * capped / n), counts))


if __name__ == "__main__":
    main()
