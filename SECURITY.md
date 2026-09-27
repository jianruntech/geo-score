# Security Policy

## Supported versions

| Version | Security fixes |
|---|---|
| 1.3.x (latest) | Yes |
| 1.2.x and older | No. Upgrade; the report format is compatible (see [STABILITY.md](STABILITY.md)) |

Pin an exact tag in CI (`jianruntech/geo-score@v1.3.0`) if you need a fixed version, and move
the pin when a security release comes out. Every security fix is listed under **Security** in the
[changelog](CHANGELOG.md).

## What geo-score is, and what it touches

A scoring rubric, a skill definition, a stdlib-only CLI, a GitHub Action and a stdio MCP server.
There is no hosted service and nothing is sent to Jianrun: no telemetry, no update checks.

- **Level 1** (the score) fetches the site you name, the profile links its own `sameAs` markup
  lists, and Wikidata and Wikipedia search. It needs no key and writes only the files you ask for.
- **Levels 2 and 3** (`--ask`, `watch`) call the AI providers whose keys you set, and write
  `geo-score-watch.json`, `queries.csv` and `.geo-score/` in a directory you pick.

## Threat model

Two inputs are treated as adversarial, because neither is under the user's control:

1. **The audited site.** Its pages, robots.txt, sitemap, llms.txt and JSON-LD can say anything,
   including text written to steer an AI agent that reads the report.
2. **AI answers.** An engine's answer can quote hostile pages it found while searching.

What the code does about it:

- **Quoted text is fenced.** Evidence that quotes the site (an answer passage, the brand name read
  from the page, a Wikidata description) carries it inside `«site text: …»`. Control characters,
  zero-width characters and bidi overrides are removed from every evidence string and from quoted
  AI answers, and a site cannot close the fence early. The MCP tools say that fenced text is data.
- **Nothing a page says changes what the tool does.** Caps, keys, output paths and the question set
  come from the user's command line and config, never from fetched content.
- **The MCP server fetches only public hosts.** `score_site` resolves the host and refuses
  loopback, private, link-local and reserved addresses before fetching, so an agent cannot be talked
  into probing an internal network.
- **Keys stay out of reach.** Keys are read from environment variables only. They are never written
  to the config, run files or reports; a key that appears in a provider's error message is replaced
  with `[redacted]` (including escaped and split forms) before it is stored or printed; a malformed
  key is refused without being echoed.
- **Provider calls never follow redirects.** A redirecting endpoint is reported as an error rather
  than handed the key. A custom `base_url` must be `https://` (or `http://localhost`).
- **An agent can only lower spending.** Over MCP, `max_calls` and `budget_usd` can be lowered, never
  raised, and run ids are validated before any file is read.
- **The GitHub Action passes inputs as environment variables**, never pasted into the script, so a
  crafted URL or path cannot run shell commands in your workflow.
- **CSV output escapes** cells a spreadsheet would treat as formulas.
- **Piped installs load nothing extra.** `curl … | python3 -` runs level 1 only and never imports a
  `geo_watch.py` from the current directory.

## Verifying a download

Every release attaches `SHA256SUMS` covering `geo_score.py`, `geo_watch.py`, the wheel and the sdist.
Download it with the files and check them before running anything:

```bash
v=v1.3.0
base=https://github.com/jianruntech/geo-score/releases/download/$v
curl -sSfLO "$base/geo_score.py" -O "$base/geo_watch.py" -O "$base/SHA256SUMS"
grep -E ' geo_(score|watch)\.py$' SHA256SUMS | shasum -a 256 -c
```

The one-line install in the README downloads from a release tag, never from `main`, so the code you
run is the code that was released.

## Your data

Run files hold your questions and the full text of the AI answers, and `queries.csv` holds the
question list. If either is confidential, keep `.geo-score/` and `queries.csv` out of public
repositories (the included `.gitignore` covers `.geo-score/`), and note that the weekly workflow in
`examples/ci/` commits run files on purpose: use it in a private repository.

Other realistic risks:

- **You choose what gets fetched.** Only audit sites you are authorised to audit. Auditing at volume
  can look like scraping to the target.
- **Reports contain data from the target site.** Treat a report as you would any document about a
  client.

## Reporting a vulnerability

Email **hello@jianruntech.com** rather than opening a public issue. Include the version
(`geo-score --version`), what an attacker controls, and what they gain. We acknowledge within five
working days, agree a disclosure date with you, and credit you in the changelog unless you prefer
not to be named.
