# Troubleshooting

How the tool behaves, and why. This page explains readings, not how to change a site.
中文版：[troubleshooting.zh-CN.md](troubleshooting.zh-CN.md)

## The score moved a few points between two runs

**Cause.** Each run samples up to 8 pages from the sitemap and the homepage's links, and the
sample changes from run to run: a page 404s, a sitemap is reordered, a link rotates. The measured
spread is about ±5 points; see [REPRODUCIBILITY.md](../benchmark/REPRODUCIBILITY.md).

**What to do.** Pin the sample. Save one run with `--json-out before.json`, then re-score with
`--urls-from before.json`. The second run reads exactly the same pages, so a difference comes from
the site. In CI, keep `--fail-under` at least five points below the usual score.

## A check shows `—` instead of a score

**Cause.** `—` means *not measured*, and a check that is not measured leaves the denominator
instead of scoring 0. There are two kinds:

- `p3.listings`, `p3.mentions` and `p4.question-coverage` need off-site search or human judgement.
  The CLI never scores them; a hand audit does.
- `p3.knowledge-graph`, `p3.sameas`, `p1.breadcrumb` and `p4.cn-engines` are `—` when this run could
  not observe them: Wikidata or Wikipedia did not answer, the profile links timed out, no sampled
  page was nested, or the site is not a Chinese-language site.

**What to do.** Nothing, for the first kind. For the second, re-run from a network that can reach
Wikidata and Wikipedia (see *Proxies* below). The report's `reason` field says which case applies.

## The score is capped at 40 (a gate scored zero)

**Cause.** One of the three gate checks (`g.robots`, `g.reachable`, `g.ssr`) scored zero, which
means a retrieval crawler cannot get the content at all. The cap applies only at zero; a middle tier
is an ordinary deduction.

**What to do.** Read the gate's evidence with `--explain`. `g.reachable` is the least stable check:
a firewall or bot-protection service can answer the ten retrieval user-agents differently from one
minute to the next, so re-run before drawing a conclusion.

## `could not fetch …` and exit code 2

**Cause.** No sampled page answered with content: DNS failed, TLS failed, every request timed out,
or the server refused a non-browser client. Exit code 2 also covers usage errors and refused
`--urls` lists.

**What to do.** Check that `curl -I https://the-site/` works from the same machine. Behind a proxy,
set `HTTPS_PROXY`. If the site answers a browser but not the CLI, that difference is itself what
`g.reachable` measures once the page loads.

## Proxies

The CLI uses Python's standard proxy settings: `HTTPS_PROXY`, `HTTP_PROXY` and `NO_PROXY` (and the
system proxy on macOS and Windows). From networks that cannot reach Wikidata, Wikipedia or some
social profiles directly, `p3.knowledge-graph` and `p3.sameas` come back as not measured rather than
zero. Set a proxy and re-run to measure them.

## The report scored a different domain than I typed

**Cause.** The site redirected: to `www.`, to a locale path, or to another domain. The report says
where it landed.

**What to do.** Score the address you meant to measure directly. If the site lives under a path
(`example.com/docs`), give that path; sampling stays inside it, while `robots.txt` and `llms.txt`
are read at the origin because that is where the specifications put them.

## My score differs from the public leaderboard

**Cause.** The leaderboard is a dated measurement: the 314-site run was made on 2026-09-09 with
tool 1.1.0. Since 1.1.2, a third-party site that cannot be reached counts as not measured instead
of zero, which raises some scores by a few points. Every report states the tool version (`tool`).

**What to do.** Compare scores made with the same tool version, and remember the ±5 band.

## `watch` or `--ask` says it needs `geo_watch.py`

**Cause.** Levels 2 and 3 live in `cli/geo_watch.py`. The one-line `curl … | python3 -` install runs
level 1 only, and never loads a `geo_watch.py` from the current directory.

**What to do.** Install the tool (`pipx install git+https://github.com/jianruntech/geo-score@v1.3.0`), or
clone the repository, or download `cli/geo_score.py` and `cli/geo_watch.py` from the same release
into one folder. The two files must carry the same version.

## `watch run` exits 3

**Cause.** No engine could be measured. Either no API key is set, in which case nothing runs and
nothing is recorded, or every call failed (a refused key, a quota, a network error), in which case
the run is saved with each engine's error and the exit code says that none of it was measured.

**What to do.** Run `geo-score watch check` to see which engines have a key set. For failed calls,
the printed report and the saved run name each engine's error. Keys are read from environment
variables only.

## The GitHub Action shows fewer annotations than checks at zero

**Cause.** GitHub shows at most 10 annotations of each level per step. The action lists the rest in
the job summary.

**What to do.** Read the job summary, or upload the SARIF file to code scanning, which has no such
limit. `upload-sarif` needs `security-events: write` in the job's permissions.

## A Chinese site is judged by characters, an English one by words

**Cause.** If any sampled page's visible text is mostly Chinese, the whole run switches its length
thresholds from words to characters (for example 50–200 characters for an answer passage instead of
25–120 words), and `p4.cn-engines` becomes observable. One Chinese page is enough, so a bilingual site
whose sample includes a single Chinese page is judged by the Chinese thresholds on every page. The
report's `audience_language` says which branch was used.

**What to do.** Check which pages were sampled (`sampled_urls`). To score the English edition of a
bilingual site by the English thresholds, pin English pages only with `--urls`; to score the Chinese
edition, pin Chinese pages.
