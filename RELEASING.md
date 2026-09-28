# Releasing

For maintainers. Hosted GitHub Actions have not run on this organisation so far, so a release is
cut by hand with `scripts/release.py`, which does the same steps in the same order every time.

## Steps

1. **Everything is in `[Unreleased]`** in both `CHANGELOG.md` and `CHANGELOG.zh-CN.md`, and the gate
   passes: `bash scripts/check.sh`.
2. **Choose the version** by [STABILITY.md](STABILITY.md): a new flag, output or optional field is a
   minor release; a fix is a patch; removing or renaming a contract is a major release.
3. **Bump:** `python3 scripts/release.py X.Y.Z --bump`. It rewrites `__version__` in both CLI files,
   `SKILL.md`, every install line and download pinned to a tag, including the tag and the version in each
   release-wheel URL (README, cli/README, SECURITY,
   STABILITY, the troubleshooting and MCP guides, examples, the issue form, the leaderboard template),
   and the version in the packaging manifests (`server.json` and its `.mcpb` URL, `mcpb/manifest.json`,
   `.claude-plugin/plugin.json`, `gemini-extension.json`). Then it runs `scripts/mcp_docs.py`, which
   regenerates the MCP tool table and install buttons in the READMEs and the MCP guides (a button carries
   the version base64- or URL-encoded, where no pin pattern can see it), and last turns `[Unreleased]`
   into `[X.Y.Z]` with a compare link. If `mcp_docs.py` fails, the changelog is left alone and `--bump`
   can simply be rerun.
4. **By hand:** update the supported-versions table in `SECURITY.md` for a minor or major release,
   rebuild the pages (`python3 benchmark/build_page.py`), run `bash scripts/check.sh`, and commit as
   `chore(release): X.Y.Z`. At a minor or major release, also regenerate the README's AIV badge with
   the new CLI (it scores the leaderboard page):
   `python3 cli/geo_score.py https://www.jianruntech.com/leaderboard --badge docs/aiv-badge.svg --json-out docs/aiv-badge.json`.
5. **Preflight:** `python3 scripts/release.py X.Y.Z` must print `ready`. It refuses while any version,
   pin, manifest, changelog section or compare link is out of step, `scripts/mcp_docs.py --check`
   finds a generated MCP block out of date, the tree is dirty, or the tag exists.
   Then the issue labels, which the forms name: with `gh` logged in as someone with write access,
   `python3 scripts/sync_labels.py` lists each label in `.github/labels.json` that GitHub lacks, and
   `python3 scripts/sync_labels.py --apply` creates it (it never deletes one). Do this the first time
   and whenever `labels.json` has changed: step 7's gate stops while a label is missing.
6. **Try the bundle, and Windows (minor and major releases):** `python3 scripts/release.py X.Y.Z --pack` builds only
   `dist/geo-score-X.Y.Z.mcpb` and `dist/server.json`. Double-click the `.mcpb` in Claude Desktop on
   macOS and on Windows, fill in one key, and run `score_site` and `status`. The bundle runs the user's
   own `python3` (`python` on Windows).
   On the same Windows machine, in a clone at the release commit, run the three CLI suites and the MCP
   conformance check with Python 3.8 and with the newest Python (`check.sh` does not run on Windows):

   ```
   py -3.8 cli/test_geo_score.py
   py -3.8 cli/test_geo_watch.py
   py -3.8 cli/test_geo_score_e2e.py
   py -3.8 scripts/check_mcp.py
   ```

   then the same four with `py -3.14` (the newest stable Python, `PY_NEWEST` in `scripts/check.sh`). Say in
   the release notes that they passed, or what failed.
7. **Publish:** `python3 scripts/release.py X.Y.Z --execute` stops at once unless `gh` is logged in (it
   creates the release, after the pushes), then runs `check.sh --live --strict` (so the tests must run on
   Python 3.8 and 3.14: `uv python install 3.8 3.14` if either is missing; and every label must exist, as
   in step 5), builds the
   wheel and sdist (and stops unless the wheel's file name is the one the install lines download),
   the Claude Desktop bundle `geo-score-X.Y.Z.mcpb` (a zip of `mcpb/manifest.json`,
   both CLI files under `server/` and the licence, byte-for-byte reproducible on the same platform) and `dist/server.json`
   (the template with the bundle's real SHA-256 in `fileSha256`), writes `SHA256SUMS` over all of them
   and the two CLI files, pushes main, creates the tag `vX.Y.Z` and pushes it, moves `v1` to it and
   pushes that, and creates the GitHub release with the changelog section and the files attached. Main
   goes first, so a rejected push leaves no local tag and the step can simply be rerun.
8. **Check it, once the release is published:** the install lines download the wheel attached to the
   release, so they can only be tried after step 7 (`check.sh --live` runs before the release exists).
   Both must print `geo-score X.Y.Z`:

   ```bash
   wheel=https://github.com/jianruntech/geo-score/releases/download/vX.Y.Z/geo_score-X.Y.Z-py3-none-any.whl
   uvx --from "$wheel" geo-score --version
   pipx run --spec "$wheel" geo-score --version
   ```

   Then the one-line `curl` from the README, and the bundle as
   [SECURITY.md](SECURITY.md#verifying-a-download) describes.
9. **MCP Registry:** an Owner of the jianruntech GitHub organisation runs `mcp-publisher login github`
   once, then `cd dist && mcp-publisher validate && mcp-publisher publish`. The listing points clients at
   the `.mcpb` URL on the release and its `fileSha256`, so this comes after step 7. A published
   version is immutable: to correct only the listing, publish a prerelease version such as `X.Y.Z-1`.

## The packaging files

Each client that installs geo-score reads its own manifest. `release.py` keeps their versions in step,
and `scripts/test_packaging.py` (part of `check.sh`) checks each one against the code: the version, the
tool names, the key variables and the entry point.

| File | Read by |
|---|---|
| `mcpb/manifest.json` | Claude Desktop, inside the `.mcpb` bundle; keys go to its keychain fields |
| `server.json` | The MCP Registry; the release attaches it with the real checksum filled in |
| `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | Claude Code (`/plugin marketplace add jianruntech/geo-score`); keys come from the user's exported environment |
| `gemini-extension.json` | Gemini CLI (`gemini extensions install`); one sensitive setting per key, since Gemini CLI does not pass `*KEY*` variables to servers |
| `Dockerfile` | `docker build`; nothing publishes an image yet |

## Who may move `v1`

`v1` is what `uses: jianruntech/geo-score@v1` resolves to, so it only ever moves to a released tag,
and only by step 7. Never point it at an untagged commit.

## The benchmark

`benchmark/results.json` is a dated measurement and states the tool version it was made with. A
release that changes scoring (a tier, a threshold, a check's reading) does not re-run it
automatically: re-running 370 sites is a decision for the owner, and the README says which version
the leaderboard used. `release.py` prints that as a note.
