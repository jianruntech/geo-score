## Summary

<!-- What this changes and why. For a heuristic or a benchmark change, name the check ids or the sites. -->

## Type

- [ ] A site added to the benchmark
- [ ] Heuristic fix: a fixture tier that moves updates `expected.json` and says why in its `_notes`
- [ ] Rubric change (a weight, a tier or a pass condition): needs a [rubric proposal](https://github.com/jianruntech/geo-score/issues/new?template=rubric_proposal.yml) first, and adds a new version file; a released rubric is never edited in place
- [ ] Engine, MCP server or Action
- [ ] Docs or cosmetic (typo, wording): no rubric version bump

Rubric proposal issue: #
New version files: `rubric/v___.md` and `rubric/v___.json`

## Test plan

The last lines of `bash scripts/check.sh` (hosted CI does not run here, so this is the gate):

```
paste here
```

## Checklist

- [ ] `CHANGELOG.md` and `CHANGELOG.zh-CN.md` updated under `[Unreleased]`, for a change a user can see
- [ ] English and Chinese kept in step: a document with a `.zh-CN.md` twin changed in both
- [ ] For a benchmark change: outputs regenerated with `benchmark/run.py`, `benchmark/build_page.py` and `benchmark/build_og.py`, or "no Chrome, cards left alone" noted in the summary ([how](https://github.com/jianruntech/geo-score/blob/main/CONTRIBUTING.md#the-easiest-useful-contribution))
- [ ] No fix templates, remediation steps or content-rewriting rules added (see [Scope](https://github.com/jianruntech/geo-score/blob/main/README.md#scope--what-this-does-not-do))
- [ ] If I added my employer's site to the benchmark, the summary says so
- [ ] Claims that rest on observation rather than published research say so
