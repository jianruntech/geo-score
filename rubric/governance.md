# Rubric governance

*简体中文：[governance.zh-CN.md](governance.zh-CN.md)*

> Adopted 2026-10-16. How the AIV rubric changes, who can ask for a change, how one version keeps
> giving the same score whoever runs it, and how the rubric relates to standards bodies. This page
> changes the way the rubric does: in public, with a changelog entry.

## Who maintains it, and what we sell

Jianrun Tech maintains the rubric, the tool and the leaderboard. We also sell GEO services:
diagnosing sites and fixing them so that they score better. That is a conflict of interest, and the
rules on this page exist because of it.

- The rubric, the tool and the leaderboard are free. We do not sell certification, a seal, a
  "compliant" label or a place on the leaderboard. A badge or a link back never moves a score
  ([README](../README.md)).
- Sites are on the leaderboard for sector and language coverage and public prominence, never because
  they are anyone's client or competitor.
- Our client work uses the published release, unmodified. A client's baseline and the follow-up it is
  compared with are scored with the same rubric version and the same tool release, so a rubric change
  can never be what makes a client's number go up.
- Our own proposals go through the same public process as anyone else's, and say that they are ours.

## Who can propose a change

Anyone. You do not need to be a client, a contributor or a company. Open a
[rubric proposal](../.github/ISSUE_TEMPLATE/rubric_proposal.yml); the form asks for:

- **the change**, stated precisely enough that someone could implement it;
- **the evidence**: what you observed, on how many sites, over what period, against which engines.
  Published research and your own field data are both welcome; say which it is;
- **how anyone could verify it from outside the site.** A check that needs an engine's internals or
  private analytics cannot be in a rubric anyone can run.

A proposal with no observation is closed. A small, well-described sample is enough to start.
If you have a commercial interest in the outcome, for example you sell a product the change would
favour, say so in the proposal. It does not disqualify the proposal; it lets readers weigh it.

Ambiguities found by running the rubric, such as two implementations scoring the same page
differently, go in as issues with the `rubric` label and are recorded in
[open-questions.md](open-questions.md).

## How a change is made

The version rules are the ones in [the rubric README](README.md#what-bumps-the-version):

| Change | Version | Process |
|---|---|---|
| A typo, clearer wording, a better example | none | a normal pull request |
| Adding or removing a check, changing a weight, changing whether a check passes | minor (v1.1 to v1.2) | the five steps below, with at least 30 days of comment |
| Restructuring the pillars | major (v1 to v2) | the five steps below, with at least 60 days of comment |

The maintainers decide whether a proposal goes into a version, and give their reasons in the issue; a proposal
that is declined is closed with the reason.

1. **Proposal.** An issue with the `rubric` label. The discussion happens there, in public.
2. **Draft.** When the maintainers judge a proposal ready, they open a pull request with the next
   version's files: the rubric in English and Chinese, its JSON, the evidence table in both languages,
   a calibration record showing how the draft scores the public benchmark and what moves, and a public
   audit scored with it ([CONTRIBUTING](../.github/CONTRIBUTING.md#changing-the-rubric) lists the
   files, and `validate.py` checks that they exist). Several accepted proposals can share one version.
3. **Comment.** The pull request states when the comment period ends: at least 30 days after it opens
   for a minor version, 60 for a major one. Every objection gets an answer in the pull request, and the
   answer stays on record when we disagree.
4. **Independent review.** Before release, we ask at least one reviewer with no commercial tie to
   Jianrun Tech, an academic or an independent practitioner, to read the draft and its calibration
   record. Their comments are published with the release, with their consent. If no one was available,
   the release notes say so.
5. **Release and announcement.** The new files are merged and the previous version is marked
   superseded; a released rubric file is never edited in place. The tool release that implements the
   new version says so in both changelogs and in its GitHub release notes: what changed, why, the
   evidence, and how the benchmark moved. The version table in [the rubric README](README.md) gains
   a row.

A bug in the tool is not a rubric change. When the tool misreads a site, the fix ships as a patch
release under [the stability policy](../guide/stability.md#what-a-minor-or-patch-release-may-do), and
the changelog names the check and the direction. A patch never changes a weight, a tier or a band.

## When a score changes

A published score changes in four ways, and only these:

- **A new rubric version.** Old scores are never recomputed or relabelled: `AIV 62 (v1.1)` stays a
  v1.1 score. Scores from different versions are not compared or averaged; re-score with the current
  version instead.
- **A tool fix.** A patch that corrects a wrong result can move a site's score, as above.
- **The site changed.** That is what the score is for.
- **A leaderboard re-run.** Each run uses one tool release from one place, and says which release and
  which day. A row that looks wrong goes through the
  [benchmark correction](../.github/ISSUE_TEMPLATE/benchmark_correction.yml) form and is checked
  against the stored report in `benchmark/raw/`.

A score never changes because someone paid, because a site is or is not a client, or because of a
complaint without evidence.

## Same version, same score

The aim is that anyone who runs the same version on the same site gets the same score. What holds it:

- A released rubric file is never edited. The JSON is canonical for machines, and check ids are
  permanent: an id may be retired, never reused.
- Every report names the rubric version, the tool release, the date and the eight sampled URLs, so it
  can be run again as it was.
- Every tool release stays installable and pinned (`uvx geo-score@X.Y.Z`), so an old version can still
  be run after a new one ships.
- The tool is tested against the rubric: check ids, points, tiers, bands and the gate cap must equal the
  JSON, and fixture sites pin the expected tier of every check. `scripts/check.sh` runs these before
  every merge.
- Anyone may implement the rubric. An implementation that changes the weights should not call its
  number an AIV score. When two implementations disagree on a real page, we treat it as a gap in the
  specification and record it.

What can still differ: a site serves different pages or content from one run to the next; a request
fails, and the check it fed is reported as not observed rather than scored zero; and four checks are
read by heuristics. How much this moves a score is measured in public and re-measured with new tool
releases ([REPRODUCIBILITY.md](../benchmark/REPRODUCIBILITY.md)). Read one site's score as ±5 rather
than as exact.

## Standards bodies

We run the rubric as an open specification: free to read, implement, cite and criticise, under the MIT
licence, with its history kept. That is the form we intend to keep.

- We do not pay for a seat as a founding or sponsoring organisation of any standard. Ordinary
  membership dues, or a disclosed share of drafting costs, are not a seat, and we would state either in
  public.
- We take part in drafting a standard only when a properly registered body invites us through its
  published procedure, the standard's text will be free for anyone to read, and the rubric stays open
  and in step with it.
- Before taking part, we ask a lawyer to read the rules that govern that kind of standard (for an
  association standard in China, the national rules on association standards) and the body's own
  articles.
- A standard built on this rubric should score readiness only. Outcomes such as citations, mentions
  and rankings belong in a separate report, as they do here, and we would not support folding them
  into the score.
- We do not describe the rubric as a national standard, an industry standard or a certification, and
  we do not describe ourselves as a standard-setting body.

## Changing this page

By pull request, with an entry in both changelogs. A change that loosens any rule above on conflicts of
interest or standards bodies gets the same 30 days of comment as a minor rubric version.
