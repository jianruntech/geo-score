# Contributing

The rubric is the product here. The most valuable contribution is **evidence that a
weight or a pass condition is wrong** — not new features.

## The easiest useful contribution

**Add a site to the benchmark.** [`benchmark/sites.json`](benchmark/sites.json) is a
plain list. Add an entry, run `python3 benchmark/run.py`, and open a PR with the
regenerated `results.json` and `README.md`:

```json
{"url": "example.com", "sector": "Ecommerce"}
```

We especially want **sectors and languages the list is thin on** — non-English sites,
regulated industries, marketplaces, media. Every site added makes the sector medians
mean more, and the medians are what let a reader place their own score.

Two rules: the site must be publicly reachable without a login, and you should not add
your own employer's site without saying so in the PR. We will still take it — a score is
a score — but a reader deserves to know.

## What we most want

1. **A heuristic that is wrong on your site.** The CLI approximates four checks that the
   rubric describes in prose — answer passages, question intent, sourced statistics and
   authorship. Run `python3 cli/geo_score.py yoursite.com --explain`, and if the evidence
   line does not match what is actually on the page, that is a bug worth reporting. Paste
   the URL and the line. These are the highest-signal reports we get.
2. **Evidence about weights.** If you have data showing a check matters more or less
   than we scored it, open a [rubric proposal](.github/ISSUE_TEMPLATE/rubric_proposal.yml).
   Say what you observed, on how many sites, and over what period. A well-argued
   proposal with a small sample beats an assertion with none.
3. **New checks for engines we don't cover.** Especially non-English engines. Include
   what signal you can actually observe from outside the engine.
4. **An independent implementation.** The rubric is [machine-readable](rubric/v1.1.json)
   and reports have a [schema](schema/report.v2.json). If you build a scorer in another
   language and it disagrees with ours on a real site, that disagreement is the most
   useful thing anyone can send us — it means the specification is ambiguous somewhere,
   and that is exactly what [open-questions.md](rubric/open-questions.md) exists to record.

## What we will decline

- **Fix templates, content rewriting rules, remediation playbooks.** This repository is
  scoped to measurement — see [Scope](README.md#scope--what-this-does-not-do). This is a
  scope decision, not a judgement on the contribution.
- **Checks that cannot be observed from outside the site.** If verifying it requires
  access to an engine's internals or to private analytics, it can't be part of a rubric
  anyone can run.
- **Vendor-specific checks** that only pass if you use a particular product.

## Changing the rubric

Weights and pass conditions are versioned so that scores stay comparable over time.

- Cosmetic edits (typos, clearer wording) — normal PR, no version bump
- Any change to a weight, or to whether a check passes — requires a rubric proposal
  issue first, then a version bump

Never edit a released rubric file in place. Add `rubric/v1.1.md` and mark the previous
version superseded.

## Development

There is no build step. The skill is Markdown. CI validates structure only:

```bash
python3 .github/validate.py
```
