# Real audits

Five public sites, audited with nothing but publicly observable data. No client data, no
privileged access, no vendor dashboards. Anyone can re-run these and check the numbers.

## v1.1 — current

| Site | Readiness | | Band | Report |
|---|:-:|:-:|---|---|
| nextjs.org | 85 / 98 | 87% | Leading | [md](v1.1/nextjs.org.md) · [json](v1.1/nextjs.org.json) |
| svelte.dev | 76 / 98 | 78% | Solid | [md](v1.1/svelte.dev.md) · [json](v1.1/svelte.dev.json) |
| stripe.com | 77 / 100 | 77% | Solid | [md](v1.1/stripe.com.md) · [json](v1.1/stripe.com.json) |
| anthropic.com | 69 / 98 | 70% | Solid | [md](v1.1/anthropic.com.md) · [json](v1.1/anthropic.com.json) |
| mingdao.com | 69 / 100 | 69% | Solid | [md](v1.1/mingdao.com.md) · [json](v1.1/mingdao.com.json) |

Every check carries a `tier_reason` — one line saying why the evidence landed on that
tier and not the next one. That line is the part worth reading. The JSON conforms to
[`schema/report.v2.json`](../schema/report.v2.json); emit the same shape and your results
are comparable with these.

**These five are not a representative sample.** They are among the best-built sites in
their categories, and they score like it. A typical business site scores far lower — the
external benchmarks in the [calibration record](../rubric/calibration-v1.1.md) put most of
them between 30 and 55. Do not read 69–87 as "the web is fine".

## v1.0 — superseded, kept as the record

| Site | AIV | | v1.0 band | Report |
|---|:-:|:-:|---|---|
| nextjs.org | — | 49% | Below average | [md](nextjs.org.md) · [json](nextjs.org.json) |
| svelte.dev | — | 40% | Critical | [md](svelte.dev.md) · [json](svelte.dev.json) |
| stripe.com | — | 51% | Below average | [md](stripe.com.md) · [json](stripe.com.json) |
| anthropic.com | — | 36% | Critical | [md](anthropic.com.md) · [json](anthropic.com.json) |
| mingdao.com | — | 34% | Critical | [md](mingdao.com.md) · [json](mingdao.com.json) |

These are the audits that failed v1.0's calibration and became the evidence for v1.1.
They are an archive, and parts of them are written in Chinese — the summaries and the
auditor's caveats. The v1.1 runs above are the current, English reports.
They are kept exactly as run — v1.0 numbers, v1.0 band names — because rewriting them
would destroy the record of what was wrong. Two of them disagreed with each other on the
same criterion, which is how ambiguity #4 in
[open-questions](../rubric/open-questions.md) was found.

## Reading a score

`77 / 100` is not a percentage of the rubric — it is the score over the **observable**
maximum for that site. Checks that do not apply leave the denominator, so two sites are
only comparable after normalising. Every report states both numbers for that reason.

