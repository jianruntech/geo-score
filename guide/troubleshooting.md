# Troubleshooting

How the tool behaves, and why. This page explains readings, not how to change a site.
中文版：[troubleshooting.zh-CN.md](troubleshooting.zh-CN.md)

## The score moved a few points between two runs

**Cause.** Each run samples up to 8 pages from the sitemap and the homepage's links, and the
sample changes from run to run: a page 404s, a sitemap is reordered, a link rotates. The measured
spread is about ±5 points; see [REPRODUCIBILITY.md](../benchmark/REPRODUCIBILITY.md).

**What to do.** Pin the sample. Save one run with `--json-out before.json`, then re-score with
`--urls-from before.json`. The second run reads exactly the same pages, so a difference comes from
the site. In CI, keep `--fail-under` at least five points below the usual score.

## A check shows `—` instead of a score

**Cause.** `—` means *not measured*, and a check that is not measured leaves the denominator
instead of scoring 0. There are two kinds:

- `p3.listings`, `p3.mentions` and `p4.question-coverage` need off-site search or human judgement.
  The CLI never scores them; a hand audit does.
- `p3.knowledge-graph`, `p3.sameas`, `p1.breadcrumb` and `p4.cn-engines` are `—` when this run could
  not observe them: Wikidata or Wikipedia did not answer, the profile links timed out, no sampled
  page was nested, or the site is not a Chinese-language site.

**What to do.** Nothing, for the first kind. For the second, re-run from a network that can reach
Wikidata and Wikipedia (see *Proxies* below). The report's `reason` field says which case applies.

## The score is capped at 40 (a gate scored zero)

**Cause.** One of the three gate checks (`g.robots`, `g.reachable`, `g.ssr`) scored zero, which
means a retrieval crawler cannot get the content at all. The cap applies only at zero; a middle tier
is an ordinary deduction.

**What to do.** Read the gate's evidence with `--explain`. `g.reachable` is the least stable check:
a firewall or bot-protection service can answer the ten retrieval user-agents differently from one
minute to the next, so re-run before drawing a conclusion. Its probes send each vendor's user-agent
string from your own address, so a firewall that verifies crawlers by IP range may refuse them and
still serve the real crawler ([reference/ai-crawlers.md](../reference/ai-crawlers.md)).

**In CI.** A gate at zero caps the score at exactly 40, so `--fail-under 40` (`fail-under: 40` in the
Action) never fails a capped site; add `--fail-on-gate` (`fail-on-gate: true`). `--assert` holds a
single check to a tier, such as `g.robots=max`. Assertions on heuristic checks carry the same
run-to-run noise as the score, so pin the pages with `--urls-from` when you assert on them.

## `could not fetch …` and exit code 2

**Cause.** Nothing the CLI asked for came back as a page to score. The message names the kind of failure
in parentheses, for example `could not fetch https://example.com (timeout): …`, and links to its section
below. A name that does not resolve, a refused connection and a failed TLS handshake are not retried, so
they fail within a second; a timeout or a dropped connection is tried three times. Exit code 2 also
covers usage errors (including a URL that is not one), refused `--urls` lists and internal errors.

With `--json`, an exit 2 prints a JSON error on stdout instead of a report
([`schema/error.v1.json`](../schema/error.v1.json)): `error.kind` is the same token, so a pipeline can
tell a mistyped host from a site that refused the tool without reading the message.

**What to do.** Read the section for the kind. Check that `curl -I https://the-site/` works from the
same machine. Behind a proxy, set `HTTPS_PROXY`; when a proxy carried the request, the message names it,
because the failure may be the proxy's.

### dns: the name does not resolve

**Cause.** The host name has no address: a typo, a lapsed domain, or a DNS server or VPN that cannot see
it. Without a proxy, the CLI resolves the name once before it fetches anything, so this fails at once.
When a proxy carries the request, the proxy resolves the name, and this check is skipped.

**What to do.** Check the spelling. `nslookup the-host` from the same machine shows what DNS answers. On
a network that resolves names only through a proxy, set `HTTPS_PROXY`.

### refused: the connection was refused

**Cause.** The host has an address, but nothing accepted a connection on that port: the server is down,
the URL names the wrong port, or a firewall rejects the connection.

**What to do.** Check the port in the URL (`https://` means 443 and `http://` means 80 unless the URL
says otherwise) and whether the site is up from another network.

### tls: the HTTPS handshake failed

**Cause.** Python could not complete an HTTPS connection: the certificate is invalid, expired or issued
for another name, the server offers only protocol versions Python refuses, or something between this
machine and the site (a proxy, antivirus or a corporate firewall) interferes with HTTPS. Behind a proxy
a host that does not exist can look like this too, because some proxies accept the connection and then
close it when they cannot reach the host.

**What to do.** Check the spelling first when the message names a proxy. Then open the site in a
browser on the same machine. The CLI checks certificates against Python's own certificate store, which
can differ from the browser's.

### timeout: no answer in time

**Cause.** The server did not answer within `--timeout` seconds (15 by default) on any of three tries.
A timeout is retried at once, because the wait has already passed.

**What to do.** Re-run. A site that is slow but up may need a longer wait, such as `--timeout 40`.
If every run times out, check the site from the same network with `curl -I`.

### dropped, no_response: no answer came back

**Cause.** The connection closed before an HTTP answer arrived (`dropped`), or what came back was not
HTTP (`no_response`). Firewalls and bot protection do this to clients they do not trust, and so do
overloaded servers. Each is tried three times.

**What to do.** Re-run later, and compare with `curl -I` from the same machine. A proxy that cannot
reach the site can also close the connection; the message names the proxy when one was used.

### http_NNN: the pages answered with an HTTP error

**Cause.** Every page the CLI asked for answered with an HTTP error. The kind carries the first page's
code, such as `http_403` (often a firewall or bot protection turning away a non-browser client),
`http_404` (the path does not exist), `http_429` (a rate limit) or `http_503`, and the message lists every
code it saw.

**What to do.** Check the URL, including its path. If a browser gets the page and the CLI gets a 403,
the site refuses the tool; that difference is what `g.reachable` measures once any page loads.

### no_content: the page came back empty

**Cause.** The server answered with a success code and an empty body.

**What to do.** Check the URL, then compare with `curl -i` from the same machine.

## Proxies

The CLI uses Python's standard proxy settings: `HTTPS_PROXY`, `HTTP_PROXY` and `NO_PROXY` (and the
system proxy on macOS and Windows). From networks that cannot reach Wikidata, Wikipedia or some
social profiles directly, `p3.knowledge-graph` and `p3.sameas` come back as not measured rather than
zero. Set a proxy and re-run to measure them.

## The report scored a different domain than I typed

**Cause.** The site redirected: to `www.`, to a locale path, or to another domain. The report says
where it landed.

**What to do.** Score the address you meant to measure directly. If the site lives under a path
(`example.com/docs`), give that path; sampling stays inside it, while `robots.txt` and `llms.txt`
are read at the origin because that is where the specifications put them.

## My score differs from the public leaderboard

**Cause.** The leaderboard is a dated measurement: the current run scored 317 sites on 2026-09-27
with tool 1.3.0. A site's page can change after that date, the sample differs between runs, and
reports made with an older tool read some checks differently (see the changelog). Every report
states the tool version (`tool`), and each site's full report from the run is in `benchmark/raw/`.

**What to do.** Compare scores made with the same tool version, and remember the ±5 band. To see
exactly what the leaderboard read, open the site's file in `benchmark/raw/` and re-score the same
pages with `--urls-from` on it.

## `watch` or `--ask` says it needs `geo_watch.py`

**Cause.** Levels 2 and 3 live in `cli/geo_watch.py`. The one-line `curl … | python3 -` install runs
level 1 only, and never loads a `geo_watch.py` from the current directory.

**What to do.** Install the tool from the release wheel
(`pipx install https://github.com/jianruntech/geo-score/releases/download/v1.4.0/geo_score-1.4.0-py3-none-any.whl`;
from source, which needs git: `pipx install git+https://github.com/jianruntech/geo-score@v1.4.0`), or
clone the repository, or download `cli/geo_score.py` and `cli/geo_watch.py` from the same release into
one folder. The two files must carry the same version.

## `watch run` exits 3

**Cause.** No engine could be measured. Either no API key is set, in which case nothing runs and
nothing is recorded, or every call failed (a refused key, a quota, a network error), in which case
the run is saved with each engine's error and the exit code says that none of it was measured.

**What to do.** Run `geo-score watch check` to see which engines have a key set. For failed calls,
the printed report and the saved run name each engine's error. Keys are read from environment
variables only.

## The GitHub Action shows fewer annotations than checks at zero

**Cause.** GitHub shows at most 10 annotations of each level per step. The action lists the rest in
the job summary.

**What to do.** Read the job summary, or upload the SARIF file to code scanning, which has no such
limit. `upload-sarif` needs `security-events: write` in the job's permissions.

## A Chinese site is judged by characters, an English one by words

**Cause.** If any sampled page's visible text is mostly Chinese, the whole run switches its length
thresholds from words to characters (for example 50–200 characters for an answer passage instead of
25–120 words), and `p4.cn-engines` becomes observable. One Chinese page is enough, so a bilingual site
whose sample includes a single Chinese page is judged by the Chinese thresholds on every page. The
report's `audience_language` says which branch was used.

**What to do.** Check which pages were sampled (`sampled_urls`). To score the English edition of a
bilingual site by the English thresholds, pin English pages only with `--urls`; to score the Chinese
edition, pin Chinese pages.
