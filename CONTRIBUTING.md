# Contributing

The rubric is the product here. The most valuable contribution is **evidence that a
weight or a pass condition is wrong** — not new features.

## What we most want

1. **Evidence about weights.** If you have data showing a check matters more or less
   than we scored it, open a [rubric proposal](.github/ISSUE_TEMPLATE/rubric_proposal.yml).
   Say what you observed, on how many sites, and over what period. A well-argued
   proposal with a small sample beats an assertion with none.
2. **New checks for engines we don't cover.** Especially non-English engines. Include
   what signal you can actually observe from outside the engine.
3. **False positives and negatives.** If a site scores in a way that is obviously wrong,
   tell us the URL and what you expected. These are the highest-signal bug reports.

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
