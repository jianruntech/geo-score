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

## Why did my score move

**Cause.** A score moves for four reasons, and a comparison of the two reports tells them apart:

- **Different pages.** The two runs sampled different pages. Every content check counts out of the
  sampled pages, so movement mixes change on the site with sampling. Read a total that moved by 5 or
  less as noise: that is the measured run-to-run spread
  ([REPRODUCIBILITY.md](../benchmark/REPRODUCIBILITY.md)).
- **A gate answered differently.** `g.reachable` is the least stable check: it records how the site
  answered retrieval crawlers at that moment, and some sites' bot protection answers differently from
  one minute to the next. A gate at 0 caps the score at 40, so a gate that flips moves the score a
  long way.
- **A check was observed in one run and not the other.** A check the run could not observe (an
  off-site lookup that did not answer, a page in a language the lexicon does not read) leaves the
  denominator. The same points then weigh more or less, and the score moves though no check lost a
  point. That is not a drop to 0.
- **A different release.** A release can read some checks differently; the changelog names them, and
  every report states its `tool`.

**What to do.** Compare the reports check by check. `geo_score.py diff before.json after.json` shows
each check's points before and after with a state (`up`, `down`, `same`, `became unobservable`,
`became observable`), the score, band and gate cap before and after, and the pages added to or
removed from the sample, and it says which of the causes above apply. To take sampling out, re-score
the same pages: `geo_score.py yoursite.com --baseline before.json` scores the pages `before.json`
sampled and prints the same comparison. In CI, `--fail-on-drop` exits 4 only when a check lost
points, a gate reached 0 or the band fell, so a site that already exists can gate on regressions
rather than on an absolute score.

## A check shows `—` instead of a score

**Cause.** `—` means *not measured*, and a check that is not measured leaves the denominator
instead of scoring 0. There are two kinds:

- `p3.listings`, `p3.mentions` and `p4.question-coverage` need off-site search or human judgement.
  The CLI never scores them; a hand audit does.
- `p3.knowledge-graph`, `p3.sameas`, `p1.breadcrumb` and `p4.cn-engines` are `—` when this run could
  not observe them: Wikidata or Wikipedia did not answer, the profile links timed out, no sampled
  page was nested, or the site is not a Chinese-language site.
- `p2.question-intent`, `p2.sourced-stats` and `p2.named-author` are `—` when the sampled pages are in a
  language the CLI has no heading, source-phrase or byline lexicon for (it has English and Chinese; see
  *Each page is read in its own language* below).

**What to do.** Nothing, for the first kind. For the second, re-run from a network that can reach
Wikidata and Wikipedia (see *Proxies* below). The report's `reason` field says which case applies, and the
terminal report's footer lists the two kinds on separate lines: `Needs off-site search or judgement:` and
`Not observable this run:`, each check there with a short reason.

## The score is capped at 40 (a gate scored zero)

**Cause.** One of the three gate checks (`g.robots`, `g.reachable`, `g.ssr`) scored zero, which
means a retrieval crawler cannot get the content at all. The cap applies only at zero; a middle tier
is an ordinary deduction.

The report's first lines name each gate at zero with the first sentence of its evidence
(`GATE AT ZERO — g.ssr: …`), and the gate leads the *Biggest gaps*.

**What to do.** Read the gate's evidence with `--explain`. `g.reachable` is the least stable check:
a firewall or bot-protection service can answer the ten retrieval user-agents differently from one
minute to the next, so re-run before drawing a conclusion. Its probes send each vendor's user-agent
string from your own address, so a firewall that verifies crawlers by IP range may refuse them and
still serve the real crawler ([reference/ai-crawlers.md](../reference/ai-crawlers.md)).

**In CI.** A gate at zero caps the score at 40: a site that would otherwise score 40 or more reads
exactly 40 and passes `--fail-under 40` (`fail-under: 40` in the Action). `--fail-on-gate`
(`fail-on-gate: true`) fails any capped site. `--assert` holds a
single check to a tier, such as `g.robots=max`. Assertions on heuristic checks carry the same
run-to-run noise as the score, so pin the pages with `--urls-from` when you assert on them.

## `could not fetch …` and exit code 2

**Cause.** Nothing the CLI asked for came back as a page to score. The message names the kind of failure
in parentheses, for example `could not fetch https://example.com (timeout): …`, and links to its section
below. A name that does not resolve, a refused connection and a failed TLS handshake are not retried, so
they fail within a second; a timeout or a dropped connection is tried three times. A site that answered
every page with a bot-challenge page exits 2 as well, with `bot challenge served to a browser user-agent (…)`
(kind `bot_challenge`, below). Exit code 2 also covers usage errors (including a URL that is not one), refused
`--urls` lists and internal errors.

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
can differ from the browser's. If the message says this Python's TLS library cannot speak TLS 1.3, run
the CLI with a newer Python: macOS's `/usr/bin/python3` is built on LibreSSL 2.8, which cannot, and a
Python from python.org, Homebrew or `uv` can. A handshake cut off in the middle is not this error: it is
`dropped`, and it is retried.

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

### slow: the answer never finished

**Cause.** The server sent its answer so slowly that one request, redirects included, ran past the most
a request may take: 30 seconds, or twice `--timeout` when that is longer. Some sites do this to crawlers on
purpose. A slow answer is not retried.

**What to do.** Re-run later. If a browser on the same network loads the page quickly, the site is slowing
this client down, and a real crawler may meet the same. A longer `--timeout` raises the per-request limit.

### deadline: the run ran out of time

**Cause.** One run takes at most 300 seconds. Once it reaches that, no new request starts and the one in
flight stops. This error means no page to score had come back by then; when some had, the run finishes and
the checks that needed the missing answers show as not observed.

**What to do.** Re-run later, or ask for fewer pages with `--sample` or a shorter `--urls` list.

### bot_challenge: a challenge page came back instead of the site

**Cause.** Bot protection (AWS WAF, Akamai, Cloudflare, Fastly, PerimeterX, DataDome or Imperva) answered the
CLI's browser user-agent with a challenge page, which only a browser that runs its script can pass. The message
names the vendor whose page it recognised. A challenge page is not the site's content, so it is never scored: read
as content, it would put `g.ssr` at zero and cap the site for a JavaScript problem it may not have. When only some
sampled pages were challenges, the run scores the rest, and the report's notes say `Scored on N of M sampled
pages; …`. A page that carries substantive text is scored whatever bot-protection script it also loads.

**What to do.** Nothing in the tool gets past a challenge: what a static fetch observes is what it measures. The
same protection may answer a real retrieval crawler differently from this machine (by its address, its reputation
or a list of verified bots), so this says nothing either way about what AI crawlers receive. A run from another
network can get a different answer.

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

**Cause.** The leaderboard is a dated measurement: the current run scored 324 sites on 2026-10-02
with tool 1.5.0. A site's page can change after that date, the sample differs between runs, and
reports made with an older tool read some checks differently (see the changelog). Every report
states the tool version (`tool`), and each site's full report from the run is in `benchmark/raw/`.

**What to do.** Compare scores made with the same tool version, and remember the ±5 band. To see
exactly what the leaderboard read, open the site's file in `benchmark/raw/` and re-score the same
pages with `--urls-from` on it.

## `watch` or `--ask` says it needs `geo_watch.py`

**Cause.** Levels 2 and 3 live in `cli/geo_watch.py`. The one-line `curl … | python3 -` install runs
level 1 only, and never loads a `geo_watch.py` from the current directory.

**What to do.** Install the package from PyPI, which carries both files: `pipx install geo-score==1.8.1`,
or run it without installing, `uvx geo-score@1.8.1 watch …`. Without access to PyPI, install the release
wheel (`pipx install https://github.com/jianruntech/geo-score/releases/download/v1.8.1/geo_score-1.8.1-py3-none-any.whl`;
from source, which needs git: `pipx install git+https://github.com/jianruntech/geo-score@v1.8.1`). Or
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

## Each page is read in its own language

**Cause.** Since 1.5.0 the CLI tells each sampled page's language apart: from its `<html lang>`, else
its `Content-Language` header, unless the visible text contradicts it (a page declared English whose
text is Chinese is read as Chinese). With no declaration the script decides (kana means Japanese,
hangul Korean, Han alone Chinese), and Latin-script text is told apart by a few common words (English,
German, French, Spanish, Portuguese). Then:

- **Answer passages** are counted in each page's own unit: 50–200 characters on Chinese, Japanese and
  Korean pages, 25–120 words on every other page. A bilingual site whose homepage is Chinese has its
  English pages read in words. The evidence says which unit applied to how many pages.
- **The heading, source-phrase and byline lexicons are English and Chinese.** `p2.question-intent`
  reads only pages in those languages and scores over them. Source phrases and written bylines are
  read only there too; a linked source, a `<cite>`, a footnote, and an author in structured data or
  `rel="author"` are read in any language. A check with no page left to read shows `—` with
  "no … lexicon for ja" (or de, fr, …), because not measured is never zero.
- **`p4.cn-engines`** is observed when a sampled page is Chinese or the host is under `.cn`: a Japanese
  site is not a Chinese-language site.
- **Knowledge-graph lookups** go to Wikidata and Wikipedia in the most common page language other than
  English, when Wikipedia has a large edition in it, and in English.

The report's `audience_language` is the most common page language; Chinese is written `zh-CN`, as it
was when the field could only be that or `en`. Before 1.5.0, one Chinese page switched every page of
the run to characters, a Japanese site was labelled `zh-CN`, and German or French headings were read
with the English lexicon.

**What to do.** Check which pages were sampled (`sampled_urls`) and read the evidence of the checks
above. To score one language edition of a multilingual site on its own, pin its pages with `--urls`.
