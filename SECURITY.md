# Security Policy

## Supported versions

| Version | Security fixes |
|---|---|
| 1.6.x (latest) | Yes |
| 1.5.x and older | No. Upgrade; the report format is compatible (see [STABILITY.md](STABILITY.md)) |

Pin an exact tag in CI (`jianruntech/geo-score@v1.6.0`) if you need a fixed version, and move
the pin when a security release comes out. Every security fix is listed under **Security** in the
[changelog](CHANGELOG.md).

## What geo-score is, and what it touches

A scoring rubric, a skill definition, a stdlib-only CLI, a GitHub Action and a stdio MCP server.
There is no hosted service and nothing is sent to Jianrun: no telemetry, no update checks.

- **Level 1** (the score) fetches the site you name, following its redirects; the URLs that site's own
  markup and robots.txt point to (the `sameAs` profiles, the logo, the declared sitemap), which can be on
  any host; and Wikidata and Wikipedia search. It needs no key and writes only the files you ask for.
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
- **Under MCP, every connection goes to a public address.** The scored URL, each redirect hop and every
  URL the audited site points to (sameAs, logo, sitemap) must resolve to a globally routable address;
  loopback, private, link-local, carrier-grade NAT (where cloud metadata services such as 100.100.100.200
  live) and reserved ranges are refused. A direct connection goes to the address that was checked, so a
  name cannot resolve to something else a moment later. Through an HTTP proxy the proxy resolves names,
  and that last step is the proxy's. NAT64 and 6to4 prefixes, which carry an IPv4 address inside, are
  refused too. This covers `score_site`; `ask` and `run` call only the AI providers configured in
  `geo-score-watch.json`, whose `base_url` is the user's choice. The command-line tool applies none of
  this: it scores whatever its user names, intranet sites included.
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

## The MCP server

`geo_score.py mcp` (installed as `geo-score-mcp`) talks MCP over stdio to the client that started it and
opens no port. stdout carries MCP messages only; diagnostics go to stderr. What each tool touches:

| Tool | Network | Reads | Writes | Spends |
|---|---|---|---|---|
| `score_site` | The named public site, the URLs its markup and robots.txt point to, Wikidata and Wikipedia search | Nothing | Nothing | Nothing |
| `ask` | The AI providers whose keys the server has | `geo-score-watch.json`, if there is one | Nothing | One call per engine |
| `run` | The AI providers in `geo-score-watch.json` | The config and `queries.csv` | A run file in `.geo-score/watch/runs/`, never for a cancelled run | Up to `max_calls`; `budget_usd` plus at most one call per engine |
| `list_runs`, `report`, `diff` | None | The config and saved runs | Nothing | Nothing |
| `status` | None | The config, `queries.csv`, the run directory, and whether each key variable is set (never its value) | Nothing | Nothing |

- **Annotations are hints, not guarantees.** Every tool declares `readOnlyHint`, `destructiveHint`,
  `idempotentHint` and `openWorldHint`, and some clients approve read-only tools without asking. `ask`
  and `run` are marked as not read-only so that clients ask before they spend: keep that confirmation on.
- **A server that cannot spend.** Start it with `--read-only` (or `GEO_SCORE_MCP_READ_ONLY=1`) to drop
  `ask` and `run`, or with `--toolsets score` to serve scoring only. Neither can be undone by an agent.
- **Cancelling stops spending.** On `notifications/cancelled`, `ask` and `run` make no further calls.
  A call already sent completes and is billed (at most one per engine); a cancelled run is not saved,
  and its calls and cost are printed to stderr. Nothing more is sent for a cancelled request. At end of
  input the paid calls stop the same way. One `run` at a time: a second is refused while one is in progress.
- **Where the keys live.** The server reads keys from its environment only. A key written into a
  client's config file (an `env` block) sits there in plain text. The Claude Desktop bundle declares
  its key fields as sensitive, so the host masks them and keeps them as secrets; the Claude Code plugin
  maps no keys and uses the variables exported in your shell.
- **User agents.** `score_site` fetches with a desktop browser's user agent and repeats the
  reachability check with the user agents of the ten retrieval crawlers in
  [reference/ai-crawlers.md](reference/ai-crawlers.md) (OAI-SearchBot, ChatGPT-User, Claude-SearchBot,
  Claude-User, PerplexityBot, Perplexity-User, Googlebot, Bingbot, Applebot and Amazonbot), sent from
  the machine running it. Provider calls send `geo-score-watch/<version>`.
- The address guard, the fencing of site text and the spending caps above apply to every MCP call.

## Verifying a download

Every release attaches `SHA256SUMS` covering `geo_score.py`, `geo_watch.py`, the wheel and the sdist,
and from 1.4.0 the Claude Desktop bundle `geo-score-X.Y.Z.mcpb` and the MCP Registry's `server.json`.
Download it with the files and check them before running anything:

```bash
v=v1.6.0
base=https://github.com/jianruntech/geo-score/releases/download/$v
curl -sSfLO "$base/geo_score.py" -O "$base/geo_watch.py" -O "$base/SHA256SUMS"
grep -E ' geo_(score|watch)\.py$' SHA256SUMS | shasum -a 256 -c
```

The `.mcpb` is a zip of the same two files (under `server/`), its manifest and the licence, built
reproducibly by `scripts/release.py`. Check it before you open it in Claude Desktop, check that
`server.json` names the same checksum (the registry and the clients that install from it rely on
`fileSha256`), and check that its `server/` files are the released ones byte for byte:

```bash
mcpb="geo-score-${v#v}.mcpb"
curl -sSfLO "$base/$mcpb" -O "$base/server.json"
grep -E " ($mcpb|server\.json)\$" SHA256SUMS | shasum -a 256 -c
grep -F "\"fileSha256\": \"$(shasum -a 256 "$mcpb" | cut -d' ' -f1)\"" server.json
for f in geo_score.py geo_watch.py; do unzip -p "$mcpb" "server/$f" | cmp - "$f" && echo "server/$f: same"; done
```

From 1.5.0 the wheel and the sdist are also on PyPI as `geo-score`, and they are the same files:
1.5.0's were checked against its `SHA256SUMS` once uploaded, and from 1.6.0 `scripts/release.py` uploads
the ones `SHA256SUMS` names and stops unless PyPI serves each with that SHA-256. To check the wheel pip
downloads from PyPI against the release:

```bash
python3 -m pip download --no-deps --only-binary :all: -d . "geo-score==${v#v}"
grep -E " geo_score-${v#v}-py3-none-any\.whl\$" SHA256SUMS | shasum -a 256 -c
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
