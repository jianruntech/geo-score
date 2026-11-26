# Engine change events

Changes in how an AI engine cites that were reported in public and can move **every** brand's citation rate at
the same time. The machine-readable list is [engine-events.json](engine-events.json); `cli/geo_watch.py` carries
the same list (`ENGINE_EVENTS`, held equal to the JSON by a test), so the one-file CLI needs no download.

This page records **what was observed, not what to do about it**. Remediation is out of scope for this repository
(see [Scope](../README.md#scope--what-this-does-not-do)).

## How geo-score uses it

- `watch diff` names the events dated between the two runs it compares, for the engines both runs measured
  (`events` in its JSON). Beside them it says when the tracked competitors moved the same way as you, and when an
  engine's pages cited per answer or brands named per answer shifted: either way, the change may be the engine's
  rather than yours ([guide/watch-methodology.md, section 12](../guide/watch-methodology.md#12-engine-changes-competitors-that-move-together-and-per-answer-benchmarks)).
- `watch report` lists the events of the 30 days before the run, for the engines it measured.
- Nothing here changes a rate, an interval or a verdict.

## The events

| Date | Engine | What was observed | Status |
|---|---|---|---|
| 2026-10-09 | ChatGPT | Pages cited per answer fell from about 27 to about 20, and the share of citations pointing to a brand's own website from about 33% to about 24% | Reported, not verified |
| 2026-10-20 to 10-31 | ChatGPT | Citations of reddit.com fell by about 84% in the second half of October | Reported, not verified |

## What the entries are and are not

- **Reported, not verified.** Both entries come from a third-party monitoring dataset of several hundred million
  answers, presented in public in November 2026. The figures are as reported; geo-score has not reproduced them.
- **Consumer products unless stated.** `surface` says where an event was seen. These two do not say, and
  monitoring datasets usually sample the consumer apps. geo-score measures the providers' APIs (the `api` channel),
  which may not change on the same day, or at all.
- **Written in our own words**, with the date, the engine and what moved. An entry is added when a change was
  observed in public with a date and an engine; one without a date is left out, since nothing can be placed
  against it.
- **Corrections** go through an ordinary pull request that edits both files; the test keeps them and the CLI
  equal.
