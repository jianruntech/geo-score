# The v1.1 band cuts, measured against the benchmark

简体中文：[bands-analysis.zh-CN.md](bands-analysis.zh-CN.md)

> **Update for the 2026-10-02 run.** The benchmark was re-run on 2026-10-02 with geo-score 1.5.0, and
> percentiles.json now holds that run, not the one this document analyses; no cut changes. On it, Leading (83) is
> reached by 21 of 324 sites, 6% (21 of the 251 sites no gate capped, 8%), so **Criterion 1 is not met on the
> current run**. Solid (66) is reached by 100 sites (31%), Growing (51) by 183 (56%) and Early (31) by 275 (85%).
> 98 of the 324 sites score within 2.8 points of a cut (SEM 1.41, from the 2026-10-12 same-day retest with
> geo-score 1.8.0, which replaced the 1.1.x retest's SEM 3.09 and its 6.1-point window), and Early, the band the
> gate cap falls in, holds 92 sites, 37 of them capped. The sections below remain the record of the 2026-09-27 run
> (317 sites, geo-score 1.3.0). Moving any cut is a separate v1.2 decision for the maintainer.

**Status:** analysis only. The v1.1 cuts (Early from 31, Growing from 51, Solid from 66, Leading from
83) do not change. Adopting any cut discussed here would be a new rubric version, and that decision
belongs to the maintainer.

**Data:** the 317 scored sites of the 2026-09-27 benchmark run (geo-score 1.3.0), as
[percentiles.py](../benchmark/percentiles.py) writes them to
[percentiles.json](../benchmark/percentiles.json). The measurement noise comes from the only retest on
record: two runs on 2026-09-09 with a 1.1.x build, before the 1.1.2 variance fixes
([REPRODUCIBILITY.md](../benchmark/REPRODUCIBILITY.md)). When the benchmark is re-run, percentiles.json
and the table in the [benchmark README](../benchmark/README.md) move with it; the figures below stay a
record of this run.

## Why this exists

The [calibration record](calibration-v1.1.md#still-unresolved) says the thresholds were borrowed from
GW Content's AEO ladder, and names deriving them from a reference pool as the main v1.2 task. The
benchmark is now that pool. This document states three criteria a cut should meet, checks the v1.1
cuts against each, and lists candidate cuts. It derives nothing on its own authority.

## Criterion 1: achievable, as Core Web Vitals defines it

When Google set the [Core Web Vitals thresholds](https://web.dev/articles/defining-core-web-vitals-thresholds),
a candidate counted as achievable only if at least 10% of origins already met it. The equivalent here is
that the top band, Leading, must be reached by at least 10% of the field.

| Band | From | Sites at or above | Share | Share of the 234 sites no gate capped |
|---|:-:|:-:|:-:|:-:|
| Leading | 83 | 32 of 317 | 10% | 14% |
| Solid | 66 | 109 of 317 | 34% | 47% |
| Growing | 51 | 183 of 317 | 58% | 78% |
| Early | 31 | 271 of 317 | 85% | 95% |

**Assessment: met, with no margin.** Leading is reached by 32 of 317 sites, 10.1%. One point higher,
at 84, only 28 sites (9%) would reach it. A re-run can put Leading on either side of the rule, so it
cannot be the reason the cut sits at 83; it is a check the cut currently passes.

## Criterion 2: bands wider than the measurement noise

The Core Web Vitals method also checks that variability in the data does not misclassify sites that are
consistently good. The equivalent here is that a site's band should not depend on which run measured it.

The retest's standard error of measurement is 3.09 points, so a single score carries a 95% interval of
about ±6.1 points. The three inner bands are 20 (Early), 15 (Growing) and 17 (Solid) points wide:
6.5, 4.9 and 5.5 times the SEM. That is enough for the bands to mean different things, but not for
a site near a cut to be placed with confidence.

- 168 of 317 sites (53%) score within 6.1 points of a cut, so their band is within noise of the next one.
- In the retest itself, 18 of 229 sites (7.9%) changed band between two runs of the same build.
- The weights move bands too: under equal weights 39 sites (12%) change band, while the rank order
  barely moves ([SENSITIVITY.md](../benchmark/SENSITIVITY.md)).

**Assessment: partly met.** The bands are several SEM wide, but more than half the field sits close
enough to a cut that its label is not stable. This SEM predates the 1.1.2 variance fixes, so a retest
with the current tool may shrink the window; until one is recorded, a band label near a cut should be
read as either of the two bands it sits between.

## Criterion 3: each band holds one kind of site

A gate check that scores zero caps the result at 40. 42 sites score exactly 40, and for 38 of them that
is the cap at work: a gate scored zero. The Early band (31 to 50) holds 88 sites, 48 of them capped,
so more than half of Early (55%) is sites whose content a crawler cannot get, which is a different
condition from the "clear gaps in the basics" the band's description names.

Before the cap, the 83 capped sites would spread over every band: 1 Leading, 8 Solid, 18 Growing,
21 Early and 35 Not started. The cap pulls the 27 from Leading, Solid and Growing down to 40, into
Early. It also bends the lower cuts: 85% of all sites reach Early, against 95% of the sites no gate
capped.

**Assessment: not met.** The cap value falls inside a band, so that band mixes two populations. A
v1.2 that keeps the cap needs either a cap value outside the bands' interiors or a band label that
says the result is capped.

## Candidate cuts for v1.2

Each candidate is scored on the same 317 sites. "Within noise" counts the sites whose score lies within
±6.1 points of any cut.

| Candidate | Early | Growing | Solid | Leading | Leading reached by | Within noise |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| v1.1, unchanged | 31 | 51 | 66 | 83 | 32 of 317 (10%) | 168 (53%) |
| Shares of all sites: 75%, 50%, 25% and 10% reach each band | 40 | 56 | 73 | 83 | 32 of 317 (10%) | 219 (69%) |
| The same shares of the 234 uncapped sites | 52 | 63 | 74 | 84 | 28 of 317 (9%) | 187 (59%) |

- **Shares of all sites** puts the Early cut exactly on the cap value, so every site a gate at zero
  holds to 40 lands on a boundary, and more sites sit within noise of a cut than under v1.1.
- **Shares of the uncapped sites** derives the cuts from sites a crawler can read, which keeps the
  pile-up out of the derivation. Its Leading cut, 84, is reached by 28 of the 317 sites (9%) and 28 of
  the 234 uncapped ones (12%): it passes criterion 1 only on the uncapped field.
- **v1.1** passes criterion 1 and has the fewest sites near a cut of the three, but its lower cuts
  are not anchored in anything this data shows.

Per-sector percentiles are in percentiles.json for every sector with at least 10 scored sites, which is
what a report would need to say where a site stands against its own sector.

## What this does not settle

- The pool is a fixed list of prominent sites picked for sector and language coverage, not a sample of
  the web, so a share here is a share of this list.
- The data predates 1.5.0, which changes how `g.robots` reads training crawlers and how a bot-challenge
  page is scored. Both move sites across the gate cap, so the capped counts above will change on the
  re-run.
- Which criterion should win when they disagree is a design choice, not a measurement.
