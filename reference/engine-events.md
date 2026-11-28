# Engine change events

Changes in how an AI engine cites that can move **every** brand's citation rate at the same time. The
machine-readable list is [engine-events.json](engine-events.json); `cli/geo_watch.py` carries the same list
(`ENGINE_EVENTS`, held equal to the JSON by a test), so the one-file CLI needs no download.

This page records **what was observed, not what to do about it**. Remediation is out of scope for this repository
(see [Scope](../README.md#scope--what-this-does-not-do)).

## What goes in

Only an event that anyone can check again:

- **observed**: geo-score measured it itself, with a method and data someone else can repeat (for example two runs of
  a published question set, and what moved between them); or
- **documented**: the engine's operator announced it in a public, dated source that anyone can re-read (a changelog,
  a documentation page, an announcement).

Each entry gives the date, the engine, the providers it concerns, where it was seen (`surface`: the API or an app),
what was observed, and the source to re-check. Figures reported by third parties that cannot be checked are left
out, however often they are repeated.

## The events

None yet.

## How geo-score uses it

- `watch diff` names the events dated between the two runs it compares, for the engines both runs measured
  (`events` in its JSON). Beside them it says when the tracked competitors moved the same way as you, and when an
  engine's pages cited per answer shifted: either way, the change may be the engine's rather than yours
  ([guide/watch-methodology.md, section 12](../guide/watch-methodology.md#12-engine-changes-competitors-that-move-together-and-per-answer-benchmarks)).
  Those two signals come from the runs themselves and work with an empty list.
- `watch report` lists the events of the 30 days before the run, for the engines it measured.
- Nothing here changes a rate, an interval or a verdict.

## Adding or correcting an entry

By pull request, editing both files; the test keeps them and the CLI equal. An entry an app shows may not reach the
API on the same day, or at all, so `surface` says where it was seen.
