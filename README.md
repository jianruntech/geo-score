<p align="right"><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a></p>

<p align="center"><img src="assets/cover.svg" alt="geo-score — an open rubric for AI answer-engine visibility" width="100%"></p>

# geo-score

**Can AI engines cite your site? A free 0–100 score from one command. Do they? Check through their APIs with your own keys.**

[![License: MIT](https://img.shields.io/badge/License-MIT-1E5C46.svg)](LICENSE)
[![Rubric v1.1](https://img.shields.io/badge/rubric-v1.1-A9854C.svg)](rubric/v1.1.md)
[![No dependencies](https://img.shields.io/badge/dependencies-none-1E5C46.svg)](cli/geo_score.py)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-skill-blue.svg)](SKILL.md)
[![MCP server](https://img.shields.io/badge/MCP-server-A9854C.svg)](#mcp-server)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![AIV readiness of the leaderboard page, measured 2026-10-03 with geo-score 1.5.0](docs/aiv-badge.svg)](https://www.jianruntech.com/leaderboard)

> **Score** (free, no key) → **Ask** one question (your API keys) → **Watch** a question set every week (your API keys).
> [Three levels, one tool](#three-levels-one-tool) · the citation half is never added to the score.

```bash
curl -sL https://raw.githubusercontent.com/jianruntech/geo-score/v1.5.0/cli/geo_score.py \
  | python3 - stripe.com --brief
```

<p align="center"><img src="assets/demo.svg" alt="geo-score scoring stripe.com from the command line — 71 out of 100, band Solid" width="100%"></p>
<p align="center"><sub>Recorded with geo-score 1.1.0 on 2026-09-09. A run with 1.2.0 on 2026-09-27 read 72.</sub></p>

<sub>One command. Every check, and what the next tier needs. The report says how long its run took.</sub>


<details>
<summary>Full output — every check, and what the next tier asks for (<code>--explain</code> adds the evidence)</summary>

```
  AIV READINESS  https://stripe.com
──────────────────────────────────────────────────────────────────────────
  72 / 100   Solid
  11 points to Leading

  Reachable 13/15
   ◐ Crawlers allowed in robots.txt   ███████████░░░░░░░  3/5
   ✓ Reachable to retrieval agents    ██████████████████  5/5
   ✓ Main content server-rendered     ██████████████████  5/5
  Understandable 17/22
   ◐ Sitemap discoverable and fresh   █████████░░░░░░░░░  2/4
   ✓ llms.txt present and structured  ██████████████████  5/5
   ✓ Organization + WebSite schema    ██████████████████  6/6
   ✗ BreadcrumbList on nested pages   ░░░░░░░░░░░░░░░░░░  0/3
   ✓ Page-type schema (Product, FAQ…) ██████████████████  4/4
  Content Citability 21/35
   ✓ Self-contained answer passages   ██████████████████  9/9
   ◐ Headings match how people ask    ████████░░░░░░░░░░  3/7
   ◐ Freshness signal present         █████████░░░░░░░░░  3/6
   ◐ Statistics carry a source        ████████░░░░░░░░░░  3/7
   ◐ Named, verifiable authorship     █████████░░░░░░░░░  3/6
  Brand Credibility 9/10
   ⊘ Third-party listings             ··················   —
   ⊘ Independent mentions             ··················   —
   ✓ Knowledge-graph entity           ██████████████████  4/4
   ✓ sameAs links resolve             ██████████████████  3/3
   ◐ Video and multimodal presence    ████████████░░░░░░  2/3
  Answer Fit 2/4
   ◐ Content shaped for extraction    █████████░░░░░░░░░  2/4
   ⊘ Covers the questions people ask  ··················   —
   ⊘ Chinese engine readiness         ··················   —
  ✓ full · ◐ partial · ✗ zero · ⊘ not measured (left the denominator)

  Biggest gaps
   +3 next tier (+3 to full)  Freshness signal present          needs: most pages do, and dateModified agrees with the visible date
   +3 next tier (+3 to full)  Named, verifiable authorship      needs: and the name links to a verifiable identity page
   +2 next tier (+2 to full)  Crawlers allowed in robots.txt    needs: mainstream retrieval user-agents explicitly allowed

  Scored 62 / 86 observable · 4 checks left the denominator · rubric v1.1 · took 91.5 s
  Needs off-site search or judgement: p3.listings, p3.mentions, p4.question-coverage
  Not observable this run: p4.cn-engines (not a Chinese-language site)

  Full rubric and what each tier means:
  https://github.com/jianruntech/geo-score/blob/v1.5.0/rubric/v1.1.md
  Score moved, or a check shows —? https://github.com/jianruntech/geo-score/blob/v1.5.0/guide/troubleshooting.md
```

<sub>`geo_score.py stripe.com`, recorded with geo-score 1.5.0 on 2026-10-03 through an HTTPS proxy (the footer's time includes it). The image above is an earlier run, with 1.1.0.</sub>

</details>

Python 3.8+, standard library only, nothing to install. It reads public URLs and prints
a score against a **published, versioned rubric** — not a black box.

**[See how 324 well-known sites score →](https://www.jianruntech.com/leaderboard)**  ·  a quarter of them are unreadable to AI crawlers.

> **GEO means Generative Engine Optimization** — getting cited by ChatGPT, Perplexity,
> Google AI Overviews, Gemini and Copilot. Nothing to do with geography or maps.

---

## MCP server

`geo-score-mcp` is a local MCP server (stdio, Python standard library only). It gives an agent the
same three levels as the CLI: score a site for free, ask the AI engines one question, and track a
question set week over week.

<!-- BEGIN MCP:install -->
<!-- Generated by scripts/mcp_docs.py for version 1.5.0; edit the script, not this block. -->

[![Add geo-score to Cursor](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en/install-mcp?name=geo-score&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyItLWZyb20iLCJodHRwczovL2dpdGh1Yi5jb20vamlhbnJ1bnRlY2gvZ2VvLXNjb3JlL3JlbGVhc2VzL2Rvd25sb2FkL3YxLjUuMC9nZW9fc2NvcmUtMS41LjAtcHkzLW5vbmUtYW55LndobCIsImdlby1zY29yZS1tY3AiXX0%3D)
[![Install geo-score in VS Code](https://img.shields.io/badge/VS_Code-Install_Server-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect?url=vscode%3Amcp%2Finstall%3F%257B%2522name%2522%253A%2522geo-score%2522%252C%2522command%2522%253A%2522uvx%2522%252C%2522args%2522%253A%255B%2522--from%2522%252C%2522https%253A%252F%252Fgithub.com%252Fjianruntech%252Fgeo-score%252Freleases%252Fdownload%252Fv1.5.0%252Fgeo_score-1.5.0-py3-none-any.whl%2522%252C%2522geo-score-mcp%2522%255D%257D)
[![Install geo-score in VS Code Insiders](https://img.shields.io/badge/VS_Code_Insiders-Install_Server-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect?url=vscode-insiders%3Amcp%2Finstall%3F%257B%2522name%2522%253A%2522geo-score%2522%252C%2522command%2522%253A%2522uvx%2522%252C%2522args%2522%253A%255B%2522--from%2522%252C%2522https%253A%252F%252Fgithub.com%252Fjianruntech%252Fgeo-score%252Freleases%252Fdownload%252Fv1.5.0%252Fgeo_score-1.5.0-py3-none-any.whl%2522%252C%2522geo-score-mcp%2522%255D%257D)
[![Add geo-score to LM Studio](https://img.shields.io/badge/LM_Studio-Install_Server-4338CA?style=flat-square)](https://lmstudio.ai/install-mcp?name=geo-score&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyItLWZyb20iLCJodHRwczovL2dpdGh1Yi5jb20vamlhbnJ1bnRlY2gvZ2VvLXNjb3JlL3JlbGVhc2VzL2Rvd25sb2FkL3YxLjUuMC9nZW9fc2NvcmUtMS41LjAtcHkzLW5vbmUtYW55LndobCIsImdlby1zY29yZS1tY3AiXX0%3D)

The buttons and the lines below install the geo-score **1.5.0** release wheel with `uvx`, which needs only [uv](https://docs.astral.sh/uv/): no git and no build step. They add no keys of their own, but a server started from a shell that exports a provider key (Claude Code passes its environment on) can use it. For a server that cannot spend, add `--read-only` after `geo-score-mcp`.

**Claude Code**

```bash
claude mcp add --scope user geo-score -- uvx --from https://github.com/jianruntech/geo-score/releases/download/v1.5.0/geo_score-1.5.0-py3-none-any.whl geo-score-mcp
```

**Standard config** (no keys in the file) for any client that reads an `mcpServers` file:

```
{
  "mcpServers": {
    "geo-score": {
      "command": "uvx",
      "args": ["--from", "https://github.com/jianruntech/geo-score/releases/download/v1.5.0/geo_score-1.5.0-py3-none-any.whl", "geo-score-mcp"]
    }
  }
}
```

Claude Desktop does not read your shell's `PATH`: put the full path that `which uvx` prints in `command`.

From source (needs git): `uvx --from git+https://github.com/jianruntech/geo-score@v1.5.0 geo-score-mcp`
<!-- END MCP:install -->

<!-- BEGIN MCP:tools -->
<!-- Generated by scripts/mcp_docs.py from MCPServer.tools(); edit the server or the script, not this table. -->

| Tool | Level | Cost | Writes | Hints | Args |
|---|:-:|---|---|---|---|
| `score_site` | 1 | Free | No | read-only, open-world | **`url`**, `urls`, `sample` |
| `ask` | 2 | Paid (your keys) | No | non-destructive, open-world | **`question`**, `engines`, `brand`, `domains` |
| `run` | 3 | Paid (your keys); `dry_run` is free | A run file under `.geo-score/watch/runs/`, next to the config | non-destructive, open-world | `dry_run`, `engines`, `limit`, `max_calls`, `budget_usd` |
| `list_runs` | 3 | Free | No | read-only, idempotent | — |
| `report` | 3 | Free | No | read-only, idempotent | `run`, `since`, `format` |
| `diff` | 3 | Free | No | read-only, idempotent | `from`, `to`, `format` |
| `status` | — | Free | No | read-only, idempotent | — |

Resources: `geo-score://rubric/v1.1`.

Prompts: `audit_site` (**`url`**), `check_citations` (**`question`**, `brand`), `weekly_watch`, `compare_runs` (`from`, `to`), `explain_check` (**`check_id`**).

Bold arguments are required. Hints are the tools' MCP annotations: clients may use them to decide what to confirm, and they are hints, not guarantees. **Only `ask` and `run` can spend money**, and only with the provider keys you give the server.
<!-- END MCP:tools -->

**Things to ask your agent:**

| Prompt | What it calls |
|---|---|
| Score https://acme.com for AI-search readiness and list the 3 checks with the most points to gain. | `score_site` with `url` |
| Dry-run my tracked questions and tell me the planned calls and caps. | `run` with `dry_run: true` (level 3, needs a config) |
| Compare my last two watch runs: which engines changed, and is any change outside the noise? | `diff` (defaults to the latest two runs) |

**Keys and config.** `score_site` needs no key. `ask` and `run` read the provider keys
(`OPENAI_API_KEY`, `PERPLEXITY_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`)
from the server's environment, which is not your terminal's: a desktop app does not see what you
exported in a shell. The level 3 tools also need a `geo-score-watch.json`. Pass it as
`-c /absolute/path/geo-score-watch.json`, because a GUI client does not start the server in your
project. From 1.4.0, `--read-only` gives a server that cannot spend anything.

Setup for each client (Claude Code, Claude Desktop, Codex, Cursor, VS Code, Gemini CLI, Devin
Desktop, Zed), the Claude Code plugin, timeouts, security and troubleshooting:
**[guide/mcp.md](guide/mcp.md)**.

## Three levels, one tool

| Level | What it answers | Needs | Command |
|---|---|---|---|
| **1 · Score** | Can AI engines reach, parse, trust and cite the site? 0–100 against the open rubric | Nothing: no key, no install | `geo_score.py stripe.com` |
| **2 · Ask** | Right now, for a question you care about, do they cite it? | An API key for any of OpenAI, Perplexity, Gemini, Anthropic, OpenRouter | `geo_score.py stripe.com --ask "best payments API for marketplaces"` |
| **3 · Watch** | How often are you cited, against which competitors and sources, week over week? | Your API keys and a fixed question list | `geo_score.py watch run` |

Level 1 is the score. Levels 2 and 3 measure the outcome the rubric keeps out of the score on
purpose ([two scores, never one](rubric/v1.1.md#two-scores-never-one)): they are reported next to
the 100 and never summed into it. A site can score 90 and still lose every answer to a competitor
with more third-party coverage, and the reverse also happens, which is why you want both.

Levels 2 and 3 need `cli/geo_watch.py` next to `cli/geo_score.py`: clone the repo or download both
files. The one-line `curl | python3` above runs level 1.

## Why this is a different question from SEO

Classic SEO asks *where do I rank*. Answer engines don't rank — they retrieve passages,
decide whether a source is worth quoting, and cite it. Different question, different
failure modes: a site can sit at position 3 on Google and never be quoted, while a page
nobody links to gets cited daily because its passages are clean.

Most of what determines this is **mechanical and cheap to fix** — a `robots.txt` line, a
JSON-LD block, a date in a template, a paragraph rewritten so it stands on its own. The
hard part is knowing which of them you are missing, and what each one is worth.

## What it checks

21 tiered checks totalling 100 points, plus 4 bonus checks worth up to +6 outside the
denominator. Full specification: **[rubric/v1.1.md](rubric/v1.1.md)** · [简体中文](rubric/v1.1.zh-CN.md)

| Pillar | Pts | Asks |
|---|:-:|---|
| **Reachable** — *gates* | 15 | Can a retrieval crawler get the page at all? `robots.txt`, live reachability across 10 AI user-agents, server-rendered content |
| **Understandable** | 22 | Can it tell what the page and the company are? `Organization` + `WebSite`, `llms.txt`, sitemap, breadcrumbs, page-type schema |
| **Content Citability** | **35** | Is there anything here worth quoting? Self-contained answer passages, headings that match how people ask, sourced figures, real bylines, freshness |
| **Brand Credibility** | 18 | Why should an engine trust it? Knowledge-graph entity, third-party listings, `sameAs` that resolves, video presence |
| **Answer Fit** | 10 | Is the content shaped to be lifted into an answer? |

Content Citability carries the most weight on purpose: answer engines retrieve
**passages**, not domains. Passage shape beats domain authority more often than classic
SEO intuition expects.

**Every scored check is tiered** — 2 to 4 tiers, each naming a count out of the 8 sampled
pages, so two people scoring the same site agree on the arithmetic. **Three checks are
gates**: score zero on crawler access, live reachability or server-rendered content and
the result caps at 40, because until a crawler can reach the content nothing else you
change has any effect.

### Bands

| 0–30 | 31–50 | 51–65 | 66–82 | 83–100 |
|:-:|:-:|:-:|:-:|:-:|
| Not started | Early | Growing | Solid | Leading |

Band names describe a **stage, not a verdict**. External benchmarks put most business
sites in the 30–55 range, so a score in the forties is ordinary, not alarming. In this repository's
own benchmark, 85% of 324 sites reach Early and 6% reach Leading
([where the cuts fall](benchmark/README.md#where-the-band-cuts-fall)).

## 324 sites, scored in public

**A quarter of them are unreadable to AI crawlers.** 73 sites have a gate check at zero — an
AI retrieval crawler cannot get the content, so it has nothing of theirs to quote. 20 block AI crawlers by name in
`robots.txt`, which is an editorial choice and reported as such — amazon.com lands at 17
for exactly this reason. **41 serve a page whose body only exists after JavaScript runs.**
Their content is there, a browser sees it, and a crawler gets an empty shell. That group
almost certainly did not choose it. At a further 12 the server refuses crawler user-agents (unverified
probes from the auditor's address).

Median **55** (95% CI 51–58, [stats.py](benchmark/stats.py)). Range 11 to 96. 66 sites were scored on
fewer than four pages; without them the median is 59.

| Site | Score | Band |
|---|:-:|---|
| resend.com | **96** | Leading |
| pulumi.com | **94** | Leading |
| supabase.com | **93** | Leading |
| elevenlabs.io | **91** | Leading |
| lumalabs.ai | **90** | Leading |
| … | | |
| qcloud.com | 12 | Not started |
| mercadolibre.com | 12 | Not started |
| keepa.com | 11 | Not started |

**[The full table, by sector →](https://www.jianruntech.com/leaderboard)** · [markdown](benchmark/README.md) · [raw data](benchmark/results.json) · [CSV](benchmark/results.csv) · [every site's full report](benchmark/raw/) · [re-run it](benchmark/run.py)

Two more findings worth the click. Sites in the five China sectors score **22 points
lower** than everyone else (95% CI 16–30; median 36 against 58; earlier samples measured with 1.1.0
put the gap between 16 and 23 points). Grouped by the language a site serves instead, the 54
Chinese-language sites score 26 points lower than the 270 others (95% CI 22–32), and within matched
sector families the gap runs from -8 to 27 points. Counted check by check in raw points, 69% of the gap
sits in checks the CLI reads with a heuristic, so at most that share could be the tool misreading
Chinese pages ([the breakdown](benchmark/README.md#what-the-spread-shows)). The two largest per-check
differences, question-shaped headings and self-contained answer passages, are heuristics the CLI also
read lower than a human on the one Chinese site in the [hand-audit comparison](benchmark/VALIDITY.md),
so part of the gap may be the tool reading Chinese pages conservatively. From 1.5.0 the CLI reads each
page in its own language and counts Chinese task, explanation and comparison headings; the leaderboard
above was measured with 1.5.0, so its figures include that change. And statistics that carry a source
and a named, verifiable byline are among the three largest gaps on more than half the sites.

Every number here is reproducible with the command at the top of this page (the benchmark
was run with 1.5.0 on 2026-10-02) — and we measured how reproducible, though with an older tool.
Running the whole benchmark twice on 2026-09-09 with a 1.1.x build, before the 1.1.2 variance fixes,
and comparing every site: **96% landed within ±5, 45% identically** (ICC 0.97, SEM 3.1). It has not
been re-measured with the current tool yet; [benchmark/retest.py](benchmark/retest.py) is the committed
study that will. Read one site's score as ±5 rather than as exact; medians are stable. The unstable
part is the gate checks, where five sites flipped
between runs because their bot protection answered a crawler differently.
The band, the control experiment and the per-site pairs are in
[benchmark/REPRODUCIBILITY.md](benchmark/REPRODUCIBILITY.md).

For five reference sites we also publish **hand-scored audits** covering all 21 checks,
with the evidence behind each one: [examples/audits/v1.1/](examples/audits/v1.1/).

## Ways to run it

**CLI** — level 1 is one file with no dependencies, and every report records how long its run took
(`elapsed_s`). Levels 2 and 3 add `cli/geo_watch.py` from the same release.

```bash
python3 cli/geo_score.py example.com            # human-readable
python3 cli/geo_score.py example.com --explain  # with the evidence behind every check
python3 cli/geo_score.py example.com --json     # conforms to schema/report.v2.json
python3 cli/geo_score.py example.com --compare competitor.com   # side by side
python3 cli/geo_score.py example.com --badge aiv-badge.svg      # embeddable SVG
python3 cli/geo_score.py example.com --badge-json aiv-badge.json  # the same badge as shields.io endpoint JSON
python3 cli/geo_score.py example.com --share                    # one line to paste somewhere
python3 cli/geo_score.py diff before.json after.json             # what changed between two reports, check by check
python3 cli/geo_score.py example.com --baseline before.json --fail-on-drop   # CI: re-score the same pages, fail only on a drop
```

**GitHub Action** (level 1) — score on every push, fail the build when it regresses. For level 3 on a
schedule, see [examples/ci/watch-weekly.yml](examples/ci/watch-weekly.yml).

```yaml
- uses: jianruntech/geo-score@v1
  with:
    url: https://example.com
    fail-under: 40
    fail-on-gate: true
```

A gate at zero caps the score at 40: a site that would otherwise score 40 or more reads exactly 40 and passes `fail-under: 40`. `fail-on-gate: true` fails any capped site.

**Claude Code skill** — the CLI measures what a static fetch can see. Four checks need
off-site search or human judgement, and the skill does those too.

```bash
git clone https://github.com/jianruntech/geo-score ~/.claude/skills/geo-score
# then: /geo-score audit https://example.com
```

The CLI leaves those four checks out of the denominator rather than guessing. Re-scoring
the five published hand audits on the same pages, it matched the auditor's tier on 80% of
84 check pairs (92% where it reads a rule, 69% where it approximates a judgement). On the checks
both scored it read 2.4 points lower on average (per site from 12 lower to 10 higher; mean absolute
difference 8.8). Its full normalised score read 5.2 points lower on average, from 16 lower to 7
higher, because the hand audits also score `p3.listings`, `p3.mentions` and `p4.question-coverage`,
which the CLI leaves out. n=5, all of them calibration sites:
[VALIDITY.md](benchmark/VALIDITY.md) lists every disagreement.

**MCP server** (all three levels) — `geo-score-mcp`, or `python3 cli/geo_score.py mcp` from a clone,
for Claude Code, Cursor and other agents: see [MCP server](#mcp-server).

## Levels 2 and 3 · does AI actually cite you?

`--ask` and `watch` put the questions your buyers ask to ChatGPT, Perplexity, Gemini and Claude,
through each provider's search-enabled API with your own keys, and record who the answers cite:
you, your competitors, or the third-party pages (forums, review sites) the engines lean on
instead. Keys are read from the environment; geo-score never writes them anywhere.

```bash
git clone https://github.com/jianruntech/geo-score && cd geo-score/cli
export OPENAI_API_KEY=… PERPLEXITY_API_KEY=…         # any subset of engines works
python3 geo_score.py acme.com --ask "best invoicing app for freelancers"   # level 2
python3 geo_score.py watch init --brand Acme --domain acme.com --competitor "Rival=rival.com"
# put the questions your buyers ask an AI assistant into queries.csv, then:
python3 geo_score.py watch run --dry-run            # the plan, the caps and what a diff could detect; no calls, no cost
python3 geo_score.py watch run                      # level 3: every question on every engine, saved
python3 geo_score.py watch diff                     # this run against the last, with a significance test
python3 geo_score.py watch report --since 30        # the last 30 days pooled, one interval over questions
```

<details>
<summary>What a watch run prints (illustrative: made-up brands and canned answers, not a real measurement)</summary>

```
geo-score watch · Lumo · run 20260926T083000Z · api channel

6 questions × 2 engines × 2 = 24 planned · 23 answered · 1 failed · 0 skipped

Cited in 38% of answers to questions that do not name Lumo (6 of 16, 4 questions, 95% CI 12–62%) · mentioned in 38%
Questions that name Lumo (2, kept out of the headline): cited in 100% (7 of 7, 95% CI 65–100%) · mentioned in 100%
Your site was cited somewhere for 5 of 6 questions.

By engine
  engine          model             cited         95% CI   mentioned  named first (tracked)  avg rank
  chatgpt-api     gpt-6-luna        9/12 75%      42–100%  75%        9/12                   1.0
  perplexity-api  sonar             4/11 36%      8–75%    36%        0/11                   2.0       1 failed
  gemini-api      gemini-3.8-flash  not measured                                                       no_key: set GEMINI_API_KEY or GOOGLE_API_KEY

These rows, and the tables below, count every question, the 2 that name Lumo included.

Share of voice
              cited  95% CI  mentioned  named first (tracked)  sentence share
  Lumo (you)  57%    26–86%  57%        9/23                   100%
  Pixa        52%    33–71%  100%       14/23                  100%

- Named first (tracked): answers that name that brand before any other brand in your config, out of the answers that name at least one of them. Brands your config does not list are not seen, so first among the brands you track may not be first in the answer. Two brands first named at the same place, one name inside the other, are neither first.
- Sentence share: in the answers that name a brand, the mean share of their sentences that name it, every sentence counted the same. A sentence ends at a line break, at 。！？, or at . ! ? before a space.
- Both read the answer as saved, which keeps its first 20,000 characters; a name that first appears after that is not seen.

Sources the engines cite most (not yours)
  domain        answers  share  owner
  pixa.example  12       52%    Pixa
  reddit.com    11       48%

Questions where a competitor is cited and you are not (1)
  id   question                    cited instead
  q03  cheapest text to video app  Pixa

Who is named for each question
  id   question                         answers  Lumo (you)             Pixa               no tracked brand named  searched yes/no/unknown  most cited
  q01  best free ai video generator     4        cited 3/4 · named 3/4  cited 2 · named 4  0/4                     2/0/2                    Lumo (you)
  q02  ai video tool with no watermark  4        cited 1/4 · named 1/4  cited 2 · named 4  0/4                     2/0/2                    Pixa
  q03  cheapest text to video app       4        cited 0/4 · named 0/4  cited 2 · named 4  0/4                     2/0/2                    Pixa
  q04  lumo vs pixa                     4        cited 4/4 · named 4/4  cited 2 · named 4  0/4                     2/0/2                    Lumo (you)
  q05  pixa alternatives                4        cited 2/4 · named 2/4  cited 2 · named 4  0/4                     2/0/2                    —
  q06  鹿末视频免费吗                   3        cited 3/3 · named 3/3  cited 2 · named 3  0/3                     2/0/1                    —

- An answer given without a web search cannot cite anything.
- "No tracked brand named" counts answers that name none of the brands in your config; they may name others.
- Perplexity and OpenRouter search on every call or do not say, so their answers count as unknown under searched.

By question type
  type         cited     95% CI   mentioned
  alternative  2/4 50%   15–85%   50%
  list         4/8 50%   22–78%   50%
  pricing      3/7 43%   0–100%   43%
  vs           4/4 100%  51–100%  100%

What the engines searched for (from 12 answers that show it)
  times  search
  2      best free ai video generator
  2      ai video tool with no watermark
  2      cheapest text to video app
  2      lumo vs pixa
  2      pixa alternatives
  2      鹿末视频免费吗

Ledger
24 questions asked · 23 API requests · 14,620 in / 4,860 out tokens · 23 searches · $0.07 + 12 answers with no price (add prices to geo-score-watch.json)
Caps: at most 100 questions.

Read this before quoting the numbers
- API channel. Answers come from each provider's search-enabled API, which is not the consumer app. Compare runs with runs; never pool them with answers sampled by hand in the apps.
- The same question gets different answers from one ask to the next, and answers to one question move together. Rates carry a 95% interval: Wilson when each question was answered once, a bootstrap over questions when a question has several answers. diff pairs the questions both runs answered and calls a change a change only when an exact paired test (McNemar, or a sign-flip test when a question has several answers), Holm-corrected across engines, says so (p < 0.05).
- A question that names the brand invites an answer that cites it. Those questions are kept out of the headline rate and reported on a line of their own.
- Engines without a key, calls that failed and calls skipped by a cap count as not measured, never as zero.
- This measures citations. It does not predict traffic, rankings or revenue.
```
</details>

**Level 2** asks each engine each question once and prints the result under the readiness
report (and into the report's `citation` object with `--json`). One ask is an anecdote: use it to
see what the engines say today, not to measure a rate.

**Level 3** keeps a fixed question list, saves every answer under `.geo-score/watch/runs/`
([schema](schema/watch.v1.json)), and reports:

| | Meaning |
|---|---|
| **cited** | The answer links to a URL you own: one of your `domains` (subdomains included), or a `url_prefixes` entry such as your Amazon store or GitHub org |
| **rank** | Your position among the distinct domains the answer cites. Rank 1 means you were the first source |
| **mentioned** | The answer names you, one of your `aliases` or your domain. Chinese, Japanese and Korean names match anywhere; all other names match whole words only |
| **share of voice** | The same two rates for each competitor, over the same answers |
| **sources** | The third-party domains cited most often: the pages the engines trust in your category |
| **gaps** | Questions where a competitor is cited and you are not, in any answer |
| **searches** | The searches the engine actually ran before answering, where the API exposes them (OpenAI, Gemini, Claude). This is the query fan-out, observed rather than guessed |
| **ledger** | Questions asked, API requests, tokens, searches and cost. Every run keeps its own ledger |

**What it will not tell you.**

- **It is not the ChatGPT app.** Answers come from each provider's API with web search switched
  on. The consumer apps use other models, prompts and personalisation. Compare API runs with API
  runs; never pool them with answers sampled by hand in the apps.
- **Some surfaces are out of reach.** Google AI Overviews and AI Mode, the AI summaries inside apps such
  as TikTok, Reddit or Xiaohongshu, an assistant's memory and account settings, location finer than the
  country hint, and which library a coding agent picks cannot be reached through these APIs.
- **A citation is presence, not merit.** A citation rate says an engine named and linked you, not that what
  it said is true or that the page deserved it; engines also cite misleading and self-promotional pages.
- **One answer is an anecdote.** Every rate carries a 95% interval (a bootstrap over questions
  when a question has several answers, since those answers move together), and `diff` calls
  something a change only when an exact paired test on the questions both runs answered,
  Holm-corrected across engines, says so (p < 0.05). Too few shared questions (under 6, or too few
  for the number of engines compared) is reported as too few to tell. The method: [guide/watch-methodology.md](guide/watch-methodology.md).
- **Questions that name you are kept apart.** "acme vs rival" or "is acme worth it" put your name
  in the engine's search and are cited almost every time. `watch` flags them when it runs, keeps
  them out of the headline rate, and reports them on their own line with their own count. An
  optional `branded` column in `queries.csv` corrects the flag by hand.
- **Not measured is not zero.** An engine without a key, a failed call and a capped call are all
  reported as not measured, and none of them lowers your rate.
- **Citations are not traffic.** Nothing here predicts visits, rankings or revenue.

**Engines.** Pin the model you mean in the config and keep it fixed between runs; `diff` flags a
run where the model changed. OpenRouter covers hundreds of models with one key.

| Engine id (default) | Provider | Key | Default model | What counts as cited | Searches shown | Cost reported |
|---|---|---|---|---|---|---|
| `chatgpt-api` | OpenAI Responses API + `web_search` | `OPENAI_API_KEY` | `gpt-6-luna` | `url_citation` annotations | yes | no, set prices |
| `perplexity-api` | Perplexity Sonar | `PERPLEXITY_API_KEY` | `sonar` | numbered sources the answer uses | no | yes |
| `gemini-api` | Gemini Interactions API + `google_search` | `GEMINI_API_KEY` or `GOOGLE_API_KEY` | `gemini-3.8-flash` | `url_citation` annotations | yes | no, set prices |
| `claude-api` | Anthropic Messages + `web_search` tool | `ANTHROPIC_API_KEY` | `claude-sonnet-5` | citations on the answer text | yes | no, set prices |
| any id you choose | OpenRouter + `web` plugin (the model answering over OpenRouter's search, not the vendor's own) | `OPENROUTER_API_KEY` | `openai/gpt-6-luna` | `url_citation` annotations | no | yes |

**Caps and cost.** `max_calls` is an exact cap on questions asked in a run, and a plan that
exceeds it refuses to start. `budget_usd` is checked before every call against the spend so far
plus the most expensive call seen on that engine, so it can be exceeded by at most one call per
engine; with a budget set, engines whose cost cannot be known are left out unless you pass
`--allow-unpriced`. Every run keeps a ledger of requests, tokens, searches
and cost. Configuration, prices and all commands: [cli/README.md](cli/README.md#watch).

**From an agent.** Levels 2 and 3 are also MCP tools, and an agent can only tighten your caps,
never loosen them: see [MCP server](#mcp-server).

**Every week.** Citation rates move slowly and noisily: run on the same weekday with the same
questions and models, and read `diff`, not single runs.
[examples/ci/watch-weekly.yml](examples/ci/watch-weekly.yml) does it on a schedule with keys from
repository secrets and commits each run, so the history lives in git. Run files contain your
questions and the full answers: use a private repository if they are confidential.

**Run it yourself, or have it run for you.** Everything here is MIT; the tool has no paid edition.
You pay your model providers directly and the ledger shows what each run used. What needs people
rather than an API, [Jianrun](https://www.jianruntech.com/en/) does as a service:

| | Run it yourself (free) | Run by Jianrun |
|---|---|---|
| Channel | Provider APIs with search | APIs and the consumer apps, sampled by hand each week |
| Engines | OpenAI, Perplexity, Gemini, Anthropic, anything on OpenRouter | ChatGPT with search, Perplexity, Gemini, Google AI Overviews, Copilot; Chinese engines when you sell into China |
| Report | Text, Markdown, CSV, JSON | A weekly report with the AIV dashboard: citation trend, per-engine rates, facts AI gets wrong about you, readiness history |
| When citations drop | Out of scope | We do the fixing |
| Price | Your API bill | AEO delivery system, from US$5,780 per 3 months, AIV dashboard included. [See pricing](https://www.jianruntech.com/en/#pricing) |

## Why a rubric, not just a tool

A score you cannot audit is a number someone made up. So the specification is the
product, and the tools are implementations of it:

- **Versioned.** Every score reports the rubric version. `71 (v1.1)` is a claim; `71` is not.
- **Tiered, with counts.** Each tier names a page count out of 8, not "most".
- **Evidence-bound.** Every check requires an observation someone else can reproduce.
- **Calibrated against public benchmarks**, with [the record published](rubric/calibration-v1.1.md) — including the four external sources the thresholds were checked against, and the [eight specification ambiguities](rubric/open-questions.md) that real audits surfaced and v1.1 settled.
- **Machine-readable.** [`rubric/v1.1.json`](rubric/v1.1.json) with stable check ids, and [`schema/report.v2.json`](schema/report.v2.json) so results from different implementations are comparable.

Implement it in your own stack, disagree with a weight, [open a rubric proposal](.github/ISSUE_TEMPLATE/rubric_proposal.yml). That is the main thing we want contributions on.

## Scope — what this does *not* do

This is the part most tools leave out, so it's stated plainly.

**AIV Score measures. It does not fix.**

| Not included | Why |
|---|---|
| Fix templates — `robots.txt`, JSON-LD blocks, `llms.txt` boilerplate | Remediation is where the actual work and judgement live. It is a separate, non-open project |
| Content rewriting — how to shape a passage so it gets quoted | Same |
| Per-engine tactics — what to do differently for Perplexity vs Gemini | Same |
| A remediation roadmap | Same |

**Other honest limits:**

- **It measures input-side readiness, not outcomes.** A high readiness score means
  engines *can* cite you. Whether they *do* depends on competition, query intent and
  factors no external audit can observe. Citation performance is reported as a separate,
  unscored block and never folded into the 100 — see
  [Two scores](rubric/v1.1.md#two-scores-never-one). Measure it with levels 2 and 3 above.
- **Brand Credibility and the named-author check need human judgement.** "Is this a real
  identifiable person" and "is this mention independent" are not fully automatable.
  Treat those ~24 points as assisted, not automatic.
- **Tiers reduce disagreement, they do not remove it.** Every tier names a count out of
  the 8 sampled pages, so two auditors agree on the arithmetic. They can still disagree
  on whether a given paragraph is a self-contained answer. The
  [settled ambiguities](rubric/open-questions.md) are the ones we found; there will be more.
- **Heavily client-rendered sites score low, sometimes unfairly.** If your content only
  appears after hydration, most checks will read the pre-hydration HTML — which is also
  roughly what a crawler sees, so the low score is usually right, but verify by hand.
- **Engine behaviour moves.** The rubric is versioned for exactly this reason. A score
  from an older rubric version is not comparable to a current one.

## Research behind the weights

The weights are opinionated but not invented. The two findings that most shaped them:

- **[Aggarwal et al., *GEO: Generative Engine Optimization*, KDD 2024](https://arxiv.org/abs/2311.09735)** —
  citing sources, adding statistics and quoting experts raise visibility by
  **up to 40%** (measured as Position-Adjusted Word Count, not citation count).
  Notably, the paper found an *authoritative tone* produced **no significant improvement** —
  which is why this rubric scores structure and attribution, not voice.
- **[llms.txt proposal, Answer.AI](https://llmstxt.org/)** — the convention this rubric
  checks for in the Understandable pillar (`p1.llms-txt`).

Every check declares what its weight rests on (published research, a vendor's own
documentation, our field observation, or a convention no engine has confirmed using), with
sources and the date they were last verified: [rubric/evidence-v1.1.md](rubric/evidence-v1.1.md).
Where the evidence is thin (`p2.answer-passages`, `p2.question-intent`, `p1.llms-txt`), the table
says so. If you have evidence that a weight is wrong,
[open a rubric proposal](.github/ISSUE_TEMPLATE/rubric_proposal.yml) — that is the
main thing we want contributions on.

## Related tools

Deliberately naming what this is *not*, so you can pick correctly:

| Project | What it does | Relationship |
|---|---|---|
| [llms-txt](https://github.com/AnswerDotAI/llms-txt) | The `llms.txt` specification itself | AIV checks for compliance with it |
| [yao-geo-skills](https://github.com/yaojingang/yao-geo-skills) | 21 categorized GEO skills, execution-oriented | Complementary — they do production, this does measurement |
| [GEOFlow](https://github.com/yaojingang/GEOFlow) | Full GEO operations system for company sites | Much larger scope; AGPL |

If you need remediation and not just a score, those projects overlap with the part
this repo deliberately excludes.

## Stability, privacy and install options

- **Install:** nothing to install for level 1 (the `curl` line above, pinned to a release). For
  a `geo-score` command with all three levels, install the release wheel:
  `pipx install https://github.com/jianruntech/geo-score/releases/download/v1.5.0/geo_score-1.5.0-py3-none-any.whl`.
  To run it without installing:
  `pipx run --spec https://github.com/jianruntech/geo-score/releases/download/v1.5.0/geo_score-1.5.0-py3-none-any.whl geo-score example.com`
  or `uvx --from https://github.com/jianruntech/geo-score/releases/download/v1.5.0/geo_score-1.5.0-py3-none-any.whl geo-score example.com`.
  None of these needs git or a build step.
  From source (needs git): `pipx install git+https://github.com/jianruntech/geo-score@v1.5.0`.
  Standard library only, whichever you pick. Release downloads carry a `SHA256SUMS` file ([how to check](SECURITY.md#verifying-a-download)).
- **Stability:** the rubric and the tool are versioned separately, and the report schema, check
  ids, CLI flags, exit codes, Action inputs and MCP tools are public contracts. What may change in
  which release: [STABILITY.md](STABILITY.md).
- **No telemetry.** geo-score sends nothing to us or anyone else. Level 1 fetches the site you
  name (following its redirects), the URLs its markup and robots.txt point to (`sameAs` profiles, logo,
  sitemap), and Wikidata and Wikipedia search; levels 2 and 3
  call only the AI providers whose keys you set.
- **Security:** text quoted from the audited site is fenced as data in every report, the MCP
  server's `score_site` connects only to public addresses, and keys never reach a file. Threat model and reporting:
  [SECURITY.md](SECURITY.md).

**Why did my score move 4 points?** Each run samples up to 8 pages, and the sample changes; the
spread measured with a 1.1.x build is ±5 ([REPRODUCIBILITY.md](benchmark/REPRODUCIBILITY.md)). To compare before and
after a change, re-score the same pages with `--baseline last.json`, which also prints what changed,
check by check (`--urls-from last.json` re-scores them without the comparison).
**Why does a check show `—`?** It was not measured, so it left the denominator instead of scoring 0.
More answers: [troubleshooting](guide/troubleshooting.md). Every term the README, the reports and the guides
use is defined in the [glossary](guide/glossary.md); every flag, exit code and watch command is in the
[CLI reference](cli/README.md) ([简体中文](cli/README.zh-CN.md)).

## Who maintains this

Built and maintained by **[Jianrun Tech](https://www.jianruntech.com)** (见润科技), Shenzhen —
we run GEO and AI-adoption programs for cross-border commerce companies. The rubric came
out of client work and out of optimizing our own products; publishing it is how we'd like
AI visibility to be measured consistently, including by people who never become our clients.

Commercial use of this repository is unrestricted under MIT — including inside paid
consulting work. You do not need our permission, and there is no separate commercial licence.

## Contributing

The most valuable contribution is evidence about the weights.
See [CONTRIBUTING.md](CONTRIBUTING.md). Which issue form takes a wrong score, a disputed leaderboard
row or a tool that does not work: [SUPPORT.md](SUPPORT.md).

## Citation

If you reference the rubric in research or a report, see [CITATION.cff](CITATION.cff).

## License

[MIT](LICENSE)
