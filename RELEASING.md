# Releasing

For maintainers. Hosted GitHub Actions have not run on this organisation so far, so a release is
cut by hand with `scripts/release.py`, which does the same steps in the same order every time.

## Steps

1. **Everything is in `[Unreleased]`** in both `CHANGELOG.md` and `CHANGELOG.zh-CN.md`, and the gate
   passes: `bash scripts/check.sh`.
2. **Choose the version** by [STABILITY.md](STABILITY.md): a new flag, output or optional field is a
   minor release; a fix is a patch; removing or renaming a contract is a major release.
3. **Bump:** `python3 scripts/release.py X.Y.Z --bump`. It rewrites `__version__` in both CLI files,
   `SKILL.md`, every install line and download pinned to a tag (README, cli/README, SECURITY,
   STABILITY, the troubleshooting guides, examples, the issue form, the leaderboard template), and turns `[Unreleased]` into
   `[X.Y.Z]` with a compare link.
4. **By hand:** update the supported-versions table in `SECURITY.md` for a minor or major release,
   rebuild the pages (`python3 benchmark/build_page.py`), run `bash scripts/check.sh`, and commit as
   `chore(release): X.Y.Z`.
5. **Preflight:** `python3 scripts/release.py X.Y.Z` must print `ready`. It refuses while any version,
   pin, changelog section or compare link is out of step, the tree is dirty, or the tag exists.
6. **Publish:** `python3 scripts/release.py X.Y.Z --execute` runs `check.sh --live`, builds the
   wheel and sdist, writes `SHA256SUMS` over them and the two CLI files, pushes main, creates the tag
   `vX.Y.Z` and pushes it, moves `v1` to it and pushes that, and creates the GitHub release with the
   changelog section and the files attached. Main goes first, so a rejected push leaves no local tag
   and the step can simply be rerun.
7. **Check it:** `uvx --from git+https://github.com/jianruntech/geo-score@vX.Y.Z geo-score --version`,
   and the one-line `curl` from the README.

## Who may move `v1`

`v1` is what `uses: jianruntech/geo-score@v1` resolves to, so it only ever moves to a released tag,
and only by step 6. Never point it at an untagged commit.

## The benchmark

`benchmark/results.json` is a dated measurement and states the tool version it was made with. A
release that changes scoring (a tier, a threshold, a check's reading) does not re-run it
automatically: re-running 370 sites is a decision for the owner, and the README says which version
the leaderboard used. `release.py` prints that as a note.
