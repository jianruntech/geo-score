# Contributing

The rubric is the product here. The most valuable contribution is **evidence that a
weight or a pass condition is wrong** — not new features.

## The easiest useful contribution

**Add a site to the benchmark.** The quickest way is the
[Add a site](https://github.com/jianruntech/geo-score/issues/new?template=add_site.yml) form: the site,
its sector and the line `--share` prints. Or open a PR with two things:

1. the entry in [`benchmark/sites.json`](../benchmark/sites.json), reusing an existing sector where one fits:

   ```json
   {"url": "example.com", "sector": "Ecommerce"}
   ```

2. that site's own report, from `python3 cli/geo_score.py example.com --json > example.com.json`,
   attached to the PR or pasted into it.

Please do not re-run the leaderboard or regenerate its files. Maintainers re-run it, so every row on
the board comes from one run, with one release of the tool and from one place; a PR that regenerates
`results.json` elsewhere would mix two runs. Your report is what we check the entry against before that run.

We especially want **sectors and languages the list is thin on** — non-English sites,
regulated industries, marketplaces, media. Every site added makes the sector medians
mean more, and the medians are what let a reader place their own score.

Two rules: the site must be publicly reachable without a login, and you should not add
your own employer's site without saying so in the PR or the issue. We will still take it — a score is
a score — but a reader deserves to know.

### Regenerating the board (maintainers)

Everything below is generated from `results.json` and `benchmark/raw/`, and all of it is
regenerated together; `validate.py` re-runs the generators and fails on any drift:

```
python3 benchmark/run.py            # scores the sites: results.json, raw/, then the files --readme-only writes
python3 benchmark/run.py --readme-only   # benchmark/README.md, results.csv, checks.csv (no re-scoring)
python3 benchmark/stats.py          # stats.json: the intervals and the China-gap breakdown
python3 benchmark/percentiles.py    # percentiles.json: where the band cuts fall
python3 benchmark/sensitivity.py    # sensitivity.json, SENSITIVITY.md, SENSITIVITY.zh-CN.md
python3 benchmark/build_og.py       # docs/og.png + docs/og.zh.png  (needs Chrome)
python3 benchmark/build_page.py     # docs/index.html, docs/zh.html, docs/llms.txt, docs/sitemap.xml
```

The pages name each share card with a fingerprint of the PNG (`og.png?v=…`), so build the cards first and the
pages after them.

A PR that changes a generator regenerates what that generator writes, without re-scoring the sites; if you
have no Chrome, say so in the PR and leave the two cards alone — we will regenerate them. Do not hand-edit a
generated file: the next generator run overwrites it.

## What we most want

1. **A heuristic that is wrong on your site.** The CLI approximates four checks that the
   rubric describes in prose — answer passages, question intent, sourced statistics and
   authorship. Run `python3 cli/geo_score.py yoursite.com --explain`, and if the evidence
   line does not match what is actually on the page, that is a bug worth reporting. Paste
   the URL and the line. These are the highest-signal reports we get.
2. **Evidence about weights.** If you have data showing a check matters more or less
   than we scored it, open a [rubric proposal](ISSUE_TEMPLATE/rubric_proposal.yml).
   Say what you observed, on how many sites, and over what period. A well-argued
   proposal with a small sample beats an assertion with none.
3. **New checks for engines we don't cover.** Especially non-English engines. Include
   what signal you can actually observe from outside the engine.
4. **An independent implementation.** The rubric is [machine-readable](../rubric/v1.1.json)
   and reports have a [schema](../schema/report.v2.json). If you build a scorer in another
   language and it disagrees with ours on a real site, that disagreement is the most
   useful thing anyone can send us — it means the specification is ambiguous somewhere,
   and that is exactly what [open-questions.md](../rubric/open-questions.md) exists to record.

## What we will decline

- **Fix templates, content rewriting rules, remediation playbooks.** This repository is
  scoped to measurement — see [Scope](../README.md#scope--what-this-does-not-do). This is a
  scope decision, not a judgement on the contribution. The two public-knowledge examples in
  [guide/public-examples.md](../guide/public-examples.md) are the one exception, and it will not grow.
- **Checks that cannot be observed from outside the site.** If verifying it requires
  access to an engine's internals or to private analytics, it can't be part of a rubric
  anyone can run.
- **Vendor-specific checks** that only pass if you use a particular product.

## Changing the rubric

Weights and pass conditions are versioned so that scores stay comparable over time.

- Cosmetic edits (typos, clearer wording) — normal PR, no version bump
- Any change to a weight, or to whether a check passes — requires a rubric proposal
  issue first, then a version bump

The steps in between (the draft, at least 30 days of public comment, an independent review, the announcement)
are in [rubric/governance.md](../rubric/governance.md).

Never edit a released rubric file in place. Add the next version (`rubric/v1.2.md`, its Chinese twin
`rubric/v1.2.zh-CN.md` and `rubric/v1.2.json`) and mark the previous one superseded. `.github/validate.py`
also requires, for every rubric version, its evidence table in both languages (`rubric/evidence-v1.2.md` and
`rubric/evidence-v1.2.zh-CN.md`) and a public audit scored with it (`examples/audits/v1.2/`).

## Development

There is no build step. One script is the gate for every change:

```bash
bash scripts/check.sh           # structure, lint, unit and end-to-end tests, the Action; offline, about 1-1.5 min
bash scripts/check.sh --all     # the CLI suites on every Python uv finds, 3.8 to 3.14
bash scripts/check.sh --strict  # fail, instead of skip, when 3.8 or the newest Python is missing
bash scripts/check.sh --live    # also scores example.com (run before a release)
git config core.hooksPath .githooks   # once per clone: run the gate before every push
```

Hosted GitHub Actions have not run on this organisation so far, so maintainers run `scripts/check.sh`
before every merge and `--live` before every release; `.github/workflows/validate.yml` runs the same
script and will take over if Actions is enabled. The suites need nothing beyond the standard library;
`ruff` and `jsonschema` are used when installed.

- `cli/test_geo_score.py` and `cli/test_geo_watch.py`: unit tests, offline, every provider faked.
- `cli/test_geo_score_e2e.py`: twelve fixture sites in `cli/fixtures/sites/`, each with an
  `expected.json` naming every check's tier. A change to a heuristic that moves a tier fails here with
  a per-check diff; if the move is intended, update `expected.json` and say why in its `_notes`.
  `UPDATE_GOLDEN=1` rewrites the golden report.
- `scripts/test_action.py`: runs `action.yml` as a runner would, against a fixture site.
- `scripts/test_ci_examples.py`: runs the copyable CI examples in `examples/ci/` with bash against fixture
  sites, and checks that the workflow examples pin their actions.
- `scripts/test_repo_meta.py`: checks the issue forms, `.github/labels.json`, the PR template, `SUPPORT.md`
  and the README badge against each other.

See [AGENTS.md](../AGENTS.md) for the invariants each check enforces.

## Adding an engine to watch (levels 2 and 3)

`cli/geo_watch.py` keeps one small function per provider: `call_<provider>(eng, key, question, country)`
returns `_result(...)` with the answer text, the cited sources as `(url, title)` pairs in the order the
engine lists them, any searches the API exposes, and token and search counts. Register it in `PROVIDERS`
and `CALLERS`, add a row to the engine tables in both READMEs, and add a parsing test with a response
fixture taken from the provider's documentation. `python3 cli/test_geo_watch.py` must pass with no
network access. Anything that could not be observed (a missing key, a failed call, a hidden field) is
reported as not measured, never as zero.
