# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/). 中文版：[CHANGELOG.zh-CN.md](CHANGELOG.zh-CN.md)。
The **rubric** is versioned separately from the repository — see `rubric/`.

## [Unreleased]

### Added
- **How much of the answer your pages support, beside the cited rate.** Where a provider documents where each
  citation sits, every answer now records it (`spans`: start, end, URLs and kind, character offsets into the
  answer as saved, at most 500), read only from documented fields: the `start_index`/`end_index` of OpenAI's and
  OpenRouter's `url_citation` annotations (where the citation sits), Perplexity's `[n]` marks when its search
  results carry the `id` its documentation maps them to, Gemini's `url_citation` annotations (Interactions API)
  and grounding supports (`generate_content`), both measured in bytes as Google's reference says, and the text
  of Claude's text blocks that carry citations. From them each answer gets `supported_share`: the share of the
  answer a URL the brand owns supports, by characters, by sentences, and by characters weighted by their
  sentence's position, e^(−position / sentences), after the position-adjusted word count of arXiv 2311.09735,
  §2.2.1, Eq. 3 (characters for words; a sentence several sources support counts in full). A mark supports the
  sentence it closes; a segment, its own characters. The report's new "Answer share your pages support" table
  gives, per engine and next to its cited rate, never merged into it, the answers measured, the median of each
  share and how many are above zero; `summary.engines[].supported_share` carries the same. An answer with no
  citation, or with one that came without a usable position (an OpenAI-compatible `base_url` that strips
  annotations looks the same), is not measured, never 0, and so is every Perplexity answer whose results carry
  no id. It is not `mention_share`: that counts sentences naming the brand, this counts text its pages support.
- **Sources listed and sources used.** Perplexity's adapter kept only the sources the text marks with `[n]` and
  dropped the rest; Gemini's `generate_content` lists grounding chunks and ties supports to some of them. Such
  answers now record `sources_listed` and `sources_used`, and a new table, "Sources listed and used in the
  answer", gives per engine the sources listed and used per answer, used over listed, and the answers that list
  and use a URL of yours (`summary.engines[].sources`). `citations`, `cited`, the rank and the headline rate read
  exactly as before for the same responses, which a test holds against 1.7.1's reading. OpenAI, Claude,
  OpenRouter and Gemini's Interactions API return one list, the citations tied to the text, so they are not
  measured.
- A run records what it measured in `recorded`. A run saved before has none, and its report says the answer share
  and the sources were not recorded rather than that the engines gave none; its summary is computed again when it
  is reported, and the file is not rewritten. schema/watch.v1.json registers every new field, closed and capped;
  guide/watch-methodology.md section 9 gives the definitions, which engines give positions and the papers behind
  them; the glossary gains *Answer share* and *Sources listed, sources used*. Measurement only: rubric v1.1, every
  tier and every score are unchanged.

## [1.7.1] — 2026-10-04

### Fixed
- **A run started at one page no longer reads its site navigation as no links.** The server-HTML links
  observation (new in 1.7.0) kept only links inside the path the run was given, so `geo_score.py example.com/product`
  counted 0 links on a page with a full navigation bar and flagged it as navigation that appears only after
  JavaScript runs. Links now count anywhere on the host, the start page itself aside, and the report names that page
  as the page the run started from rather than the homepage ("links to N pages on this host"). Reported from a live
  site the day 1.7.0 shipped. Never part of the score.

## [1.7.0] — 2026-10-04

### Added
- **`engines[].timeout`.** Seconds to wait for one engine's answer, 10 to 600 (default 120), for a slow endpoint
  or a model that searches and reasons at length. A timed-out request is still not retried.
- **"What the engines searched for" counts years and ranking words, and names searches that came back without
  their queries.** A line under the table gives, over every search the answers exposed, how many contain a year
  (a four-digit number from 1900 to 2099 standing alone) and how many contain a ranking or comparison word: `best`,
  `top`, `vs`, `versus`, `review`, `reviews`, `compare`, `comparison`, `alternative`, `alternatives` as whole words
  in any letter case, or `最好`, `最佳`, `推荐`, `排行`, `排名`, `哪家`, `哪个好`, `对比`, `评测` anywhere. A search
  counts once for each, and one that repeats the question's own words counts too: the line describes what was
  searched, not what the engine added. When OpenAI, Gemini or Anthropic answers report a search but expose no query,
  as an OpenAI-compatible `base_url` that returns `web_search_call` items with no `action` does, the section no
  longer disappears: it says how many answers searched with no query text, per engine, and `watch ask` says the same
  under the answer. Perplexity and OpenRouter answers are never counted there, since their adapters record one
  search per answer whatever happened. The summary gains `summary.searches.answers_searched_without_queries`,
  `summary.searches.modifiers` (`total`, `with_year`, `with_ranking_word`) and `searched_without_queries` on each
  row of `summary.engines`, and schema/watch.v1.json now describes `summary.searches`. A run saved before this
  release gets them computed from its saved answers when it is reported; the run file is not rewritten.
- **Pages robots.txt blocks by path, and rules two readings disagree on, outside the score.** `g.robots` reads only a
  Disallow that closes the whole site, so a rule on one path left it green. Each run now holds the homepage, every
  sampled page and the first 200 URLs on the audited host and path of the sitemap `p1.sitemap` read (the first child
  of a sitemap index; when the homepage redirects to another host, that host's too, if robots.txt was answered from
  there) against the rules each of the ten retrieval crawlers obeys, read as RFC 9309 section 2.2.2 says: the longest
  matching pattern decides, an allow wins a tie, `*` and a final `$` are wildcards, and percent-encoding is compared
  in one form. The report names each page a rule closes, the crawlers and the rule, and the pages where the
  first-match reading of Python's `urllib.robotparser` and many older checkers (rules in file order, the first plain
  prefix decides) says otherwise, with the rule each reading chose. Only the first 500 KiB of robots.txt are read, the
  least RFC 9309 section 2.5 asks a crawler to parse, and the readings stop after 1,000,000 rule comparisons, counting
  the URLs left as not checked, so a file of thousands of wildcard rules cannot hold a run up. Nothing is fetched for
  it and it is never scored: rubric v1.1, every tier and the leaderboard are unchanged.
- **Whether pages are linked in the server HTML, outside the score.** From the HTML the run already fetched (the
  homepage, the scored sample and the section indexes sampling read), the report counts the `<a href>` links to pages
  on the audited host and path, or on the host the homepage redirected to (apex to www), that a crawler running no
  JavaScript can follow: links inside comments, scripts, styles and templates do not count, nor do `javascript:`,
  `mailto:` and `tel:` links. It says how many pages the homepage links to and how many of the other sampled pages
  among them, flags a homepage that links to fewer than 3 ("navigation that appears only after JavaScript runs cannot
  be followed by crawlers that do not run it"), and names the checked sitemap URLs no fetched page links to (the
  homepage aside, since a crawl starts there). Only the fetched pages are searched, so a page they do not link to is
  not shown to be orphaned, and the report says so. No request is added, and it is never scored.
- **hreflang annotations on the fetched pages, outside the score.** On the same pages, the report reads each
  `<link rel="alternate" hreflang="…" href="…">` in the server HTML (outside comments, scripts, styles and templates; a
  feed's alternate left out) and each `rel="alternate"` link with an `hreflang` parameter in the page's HTTP `Link`
  header, every `Link` line read (a response's repeated `Link` lines used to keep only the last). It says how many
  pages carry annotations, how many there are and how many came in a `Link` header, and lists, as found: pages that
  carry annotations after the end of the head (after `</head>` or the `<body>` tag), since Google's hreflang
  documentation says the `<link>` tags must be inside a well-formed `<head>` (they are still counted with the others);
  pages whose annotations leave the page itself out; codes outside the subset of BCP 47 that Google's hreflang
  documentation supports (an ISO 639-1 language, optionally an ISO 15924 script and an officially assigned ISO 3166-1
  alpha-2 region, or `x-default`), so `en_US`, `jp`, `en-UK`, `es-419` and the registry's six deprecated two-letter
  language subtags (`iw` and the like) are listed, each with why; a code that names more than one URL on one page; URLs
  named in annotations that are not absolute, as written; and URLs on another host, which hreflang allows and the
  report only notes. A `>` inside a quoted attribute value does not end a `<link>`, a backslash-escaped quote in a
  `Link` header parameter does not end it, and a default port or a trailing dot on a host names the same host. Return
  links are checked only between the pages the run fetched: a pair where one page names the other and is not named
  back is listed, and the other URLs the annotations name are counted as not checked. A site with none gets one line.
  The codes are the 184 two-letter language subtags the IANA Language Subtag Registry (File-Date 2026-09-17) does not
  mark deprecated and the 249 officially assigned ISO 3166-1 alpha-2 codes among its region subtags; the registry and
  Google's page (last updated 2026-09-21) were read on 2026-10-04. Only the first 1,000 annotations of a page are read, and the rest are counted. No request is added, and
  it is never scored: rubric v1.1, every tier and the leaderboard are unchanged.
- **The text report, the MCP `score_site` summary and the Action's job summary show all three under "Outside the
  score".** The JSON report carries them in a new optional `access` field (`access.robots_paths`,
  `access.server_links`, `access.hreflang`), registered in schema/report.v2.json; each lists the first 50 pages, and
  its counts cover them all. The terminal report quotes a page's path, a robots.txt pattern and an hreflang code or
  href as `«site text: …»`, the Markdown views as code. A new e2e fixture, `hidden-pages`, has a path rule that closes
  its pricing page, rules the two readings part on, and a menu only a script writes; another, `hreflang`, has a page
  that is not named back, annotations in two `Link` header lines, and the code and href slips above; the `hostile`
  fixture carries its injection text in an hreflang code and href. Every fixture's `expected.json` pins the new
  counts.
- **The Claude Code skill installs with `npx skills add jianruntech/geo-score`** (the open skills CLI; `-g` for a
  global install). Checked on 2026-10-04: it finds one skill, `geo-score`, and copies the whole repository, about
  9 MB, into `.claude/skills/geo-score`. The README's `git clone` stays as the way without Node.js.

### Changed
- **A ledger with no priced answer says the cost is unknown.** It read `$0 + 4 answers with no price (add prices
  to geo-score-watch.json)`, which looks like a free run; it now reads `cost unknown: 4 answers with no price (add
  prices to geo-score-watch.json)`. When some answers are priced it still reads `$0.07 + 12 answers with no price`.
  The MCP `run` tool's message for a cancelled run uses the same words. The JSON ledger is unchanged.
- **The ledger says what failed.** When calls failed, `watch report` adds a line with how many, and how many HTTP
  requests were sent in all, since a provider may bill a request it timed out on. A path outside the current
  directory is printed absolute instead of as a chain of `../`.

### Fixed
- **OpenAI engines send the question as a one-message list.** The Responses API accepts a string or a list;
  some OpenAI-compatible endpoints that a `base_url` points at accept only the list and refused every call.
  Official OpenAI answers the same either way.
- **The crawler reference no longer says that blocking an opt-out token costs nothing.** `reference/ai-crawlers.md`
  put the cost of blocking an opt-out token at "nothing, in citation terms" and closed by saying that blocking every
  training crawler and both opt-out tokens "costs nothing". Google's common crawlers page (last updated 2026-07-14,
  checked 2026-10-04) says `Google-Extended` governs grounding in Gemini Apps and in Grounding with Google Search on
  Vertex AI as well as the training of Gemini models, and does not affect inclusion or ranking in Google Search. The
  reference now says what each opt-out token and training crawler controls, citing the vendor's page with its date:
  `Applebot-Extended` governs training only, and Apple's AI answers are opted out of with `nosnippet` (About Applebot,
  published 2026-09-04); Meta's crawler page (undated, checked 2026-10-04) describes `Meta-ExternalAgent` as crawling
  for training and also for indexing content to improve Meta's products, so it is no longer implied to be
  training-only; `anthropic-ai` is not in Anthropic's current crawler article, so whether it sends requests is marked
  no data instead of falling under a heading that said opt-out tokens send none. A new table gives the control Google
  documents for each part of its AI features, among them Search Console's Search generative AI control for AI
  Overviews and AI Mode, and eligibility for those features now follows Google's newer guide (last updated
  2026-07-10), which adds inclusion under that control to being indexed and eligible for a snippet. Nothing is scored
  differently: training crawlers and opt-out tokens are still not scored,
  rubric v1.1 is unchanged, and the glossary's opt-out token entry says the same in both languages.
- **`reference/platform-source-selection.md` gave AI Overviews' grounding control to `Google-Extended`, and offered
  observations this repository has no data for.** Per Google, AI Overviews and AI Mode answer to Googlebot's
  robots.txt rules, the snippet controls (`nosnippet`, `data-nosnippet`, `max-snippet`, `noindex`) and Search
  Console's Search generative AI control; `Google-Extended` governs Gemini's grounding. The page no longer says that a
  retrieval crawler disallowed in robots.txt gets nothing: OpenAI and Perplexity say their user-triggered fetchers
  (`ChatGPT-User`, `Perplexity-User`) may not follow robots.txt. The lines offered as our
  observation (pages with `Organization` or `Article` schema, recently updated pages, Q&A pages and PDFs cited
  disproportionately; `llms.txt` mattering more to Claude; an unindexed Bing site as the most common blind spot) had
  no measurement behind them here, since the benchmark scores sites, not answers, and are gone with the other unsourced
  lines; the passage as the unit of selection is now labelled a hypothesis. Each engine's section now cites its
  vendor's documentation, re-read on 2026-10-04, and says no data where the vendor documents nothing.

## [1.6.0] — 2026-10-03

### Added
- **`watch report` shows who is named for each question.** A new table, "Who is named for each question",
  lists every question with its answers and, out of those, how many cite and name you, how many cite and name
  each competitor, how many name no tracked brand, how many searched the web (yes, no or unknown), and the
  tracked brand cited most often, given only when the question has at least 4 answers and one brand is ahead of
  every other. Every value is a count. Whether an answer searched is derived from what every run already saves
  (a reported search, an exposed search query or a citation); Perplexity and OpenRouter answers are always
  unknown, because their adapters record one search per answer whatever happened. Three lines under the table
  say what the counts cannot: an answer given without a search cannot cite anything, "no tracked brand named"
  covers only the brands in your config, and why some answers are unknown. The summary gains
  `summary.by_question` (`$defs/by_question` in schema/watch.v1.json), the JSON report and the MCP `report` tool
  carry it, and it is an optional property of the tool's output schema, so the MCP contract only grows. A run
  saved before this release gets it computed from its saved answers when it is reported; the run file is not
  rewritten.
- **Suggested question types, and `watch check` counts them.** `intent_tier` stays free text; cli/README.md and
  guide/watch-methodology.md now suggest eight labels, each with one line and an example: `list`, `vs`,
  `alternative`, `pricing`, `problem` (a situation that names no category or brand), `persona` (who it is for),
  `verdict` (is it worth it, can it be trusted) and `channel` (franchise, wholesale, distributor, procurement).
  `watch check` prints how many questions have each type, with a note, never a failure, when every question has
  the same type or none has one. `watch init` writes two more placeholder questions, a `problem` row and a
  `verdict` row.
- **`target_url` is read: `watch report` counts how often the page a question tracks is cited.** The column was
  documented and saved but nothing used it. It is now resolved when the questions load: an absolute `http(s)` URL
  as written (fragment and `utm_*` parameters dropped), or a path starting with `/` joined to the brand's first
  domain. `watch check`, `watch run` and the MCP `run` (its dry run too) and `status` tools warn about any other
  value, which the run ignores, and about a page that is not on the brand's domains or URL prefixes, which is still
  matched. Each answer records `target_cited` (one of its
  citations is that page) and `other_own_cited` (it cites another URL of the brand's, not that page), both null
  when the question tracks no page. The match is the exact page once `www`, letter case, a trailing slash, the
  query string, the fragment and percent-encoding are set aside; `/en/x` is not `/x`, and a citation left as an
  unresolved redirect counts as neither. A new table, "Pages you track", gives per page its questions, their
  answers, how many cite the page, how many cite another of your URLs instead, and the URL of yours those
  answers cite most, exactly as cited. The CSV export gains a last column, `target_cited` (`Y`, `N` or empty).
  Schema: `target_cited` and `other_own_cited` in `$defs/sample`, `summary.tracked_pages` with
  `$defs/tracked_page`, and a description of the saved `target_url`. The MCP `report` tool's output schema gains
  the optional `tracked_pages`, so the MCP contract only grows. A run saved before this release gets the table
  computed from its saved citations when it is reported.
- **`watch report` shows who is named first.** Each answer records, for the brand and each competitor,
  `mention_order` (1 for the brand named before every other brand in the config, by the earliest match of its name,
  aliases or domains with the matcher of `mentioned`; null when it is not named, or when two brands are first named
  at the same place) and `mention_share` (the share of the answer's sentences that name it, every sentence counted
  the same; a sentence ends at a line break, at `。！？`, or at `.` `!` `?` before whitespace). With competitors in the
  config, "By engine" gains a column, "named first (tracked)": the answers that name you first among the brands in
  the config, out of the answers that name at least one of them. "Share of voice" gains "named first (tracked)" and
  "sentence share", the mean `mention_share` over the answers that name each brand, with three lines on how they are
  read. Brands the config does not list are not seen, so first among the brands you track may not be first in the
  answer. Both are read from the answer as saved, which keeps its first 20,000 characters. Schema: `mention_order`
  and `mention_share` in `$defs/sample` and its competitors, and `named_first`, `any_named` and `mention_share` on
  the rows of `summary.engines` and `summary.share_of_voice`. The MCP tools' schemas are unchanged. A run saved
  before this release gets them computed from its saved answers when it is reported.
- **`watch run --dry-run` says what the plan can detect, and `watch report` can pool runs.** The dry run prints the
  plan's resolution: with E engines `watch diff` tests E + 1 rows (one row with one engine), and it can call a
  change only when at least k questions move the same way between two runs, k being the smallest n with rows × 2 /
  2^n < 0.05, the screen diff already applies: 6 questions with one engine, 7 with two, 8 with three to five. A set
  with fewer questions gets "this plan cannot detect a change": more questions help, more engines raise k, and more
  asks per question do not lower it. The MCP `run` tool's dry run prints the same lines. `watch report --since DAYS`
  (or `--runs A..B`) counts the saved runs of a period as one set of answers, when each asked the same questions
  (the same `questions_hash`) as many times each (the same `runs`, so every run weighs the same) on the same engines
  with the same models, from the same `country`, with the same brand domains and URL prefixes as the newest;
  otherwise it exits 1 and names every run that differs and why. It gives the runs, the calendar days they cover,
  the answers, the headline rate and a row per engine, with a 95% interval that resamples questions, each with every
  answer it got in every run, and the run report's notes (the API channel, questions that name the brand, what
  counts as not measured, and that it does not predict traffic, rankings or revenue). There is no pooled diff.
  Schema: `$defs/pooled` in schema/watch.v1.json. MCP: the `report` tool gains an optional `since` argument and its
  output schema the optional `runs` and `days`, so the MCP contract only grows. guide/watch-methodology.md gains
  section 8, "One ask, one day, one month".

### Changed
- **Install from PyPI.** geo-score has been on PyPI since 1.5.0, as the same wheel and sdist the GitHub release
  attaches, and the install lines now lead with it: `uvx geo-score@X.Y.Z example.com`,
  `pipx install geo-score==X.Y.Z`, and `uvx geo-score@X.Y.Z mcp` for MCP clients (the install buttons, the Claude
  Code line, the standard config, every client in guide/mcp.md and the Claude Desktop bundle's watch-init hint). The
  release wheel URL stays as the line for a machine without PyPI, the git tag as the from-source line, and the `curl`
  line as the way to run level 1 with nothing installed. server.json lists the pypi package beside the `.mcpb`, so
  the MCP Registry offers it from this release on, and README.md, the package's description on PyPI, carries the
  registry's `mcp-name` line (1.5.0's description on PyPI has none, so a 1.5.0 listing names only the `.mcpb`).
  `release.py --bump` moves every `geo-score@X.Y.Z` and `geo-score==X.Y.Z`, and `--execute` ends with the PyPI
  upload (`--no-pypi` leaves it out, `--publish-pypi` does it alone): it uploads exactly the wheel and sdist that
  `SHA256SUMS` names, with twine pinned in `TWINE_VERSION`, then checks PyPI's SHA-256 of each (RELEASING.md,
  step 8). Its requests to GitHub and PyPI are tried three times, and a stop that a rerun can get past names the
  command.
  The message `watch`, `mcp` and `--ask` print when `geo_watch.py` is missing (the piped one-line run) names the
  package first too, then the wheel.

### Fixed
- **`watch diff` compares a question only with itself.** It paired questions by `query_id` alone, so a question
  reworded under the same id was compared with its old wording, and the edit could read as a change (and make
  `--fail-on-drop` exit 4). The question text is now compared case-folded, with whitespace collapsed: a question
  whose text changed is left out of every row and named in the notes (at most 10 ids, then "and N more"). The
  6-question minimum and the screen for rows no test could call apply to the questions left, so on runs with
  edited questions a verdict can change, and can become `too few questions to tell`. The notes also say when the
  runs asked from different locations (`country`) and when an engine id moved to another provider. Run files gain
  an optional top-level `questions_hash` (SHA-256 over the sorted pairs of id and normalised text, defined in
  schema/watch.v1.json), and `watch runs` shows its first 8 characters; for older runs it is computed from the
  saved questions.
- **An API that changes its answer format no longer reads, without a word, as an engine that stopped citing.**
  Each adapter reads one format per provider, so a renamed citation field gave answers with no citations at all,
  and `watch diff --fail-on-drop` could exit 4 on what was a format change. `watch report` now warns under "By
  engine" when an engine answered 5 or more questions and none of its answers carried a citation of any domain.
  `watch diff` adds a `warning` to an engine's row, the same words to the notes and to stderr, when the share of
  its answers carrying any citation fell from at least 50% to below 5% with the same model and at least 5
  questions answered in the later run. Both count questions, not answers, because the answers to one question
  move together. The verdict and exit code 4 are unchanged: the warning asks for one answer to be checked with
  `watch ask`. The summary gains `with_citations` and `with_searches` on each row of `summary.engines`, and a
  run saved without them gets them computed from its saved answers when it is reported. Schema: both counts, and
  an optional `warning` in `$defs/diff_row`; the MCP `diff` tool's output schema gains the optional `warning`,
  so the MCP contract only grows.
- **`p3.video`: Douyin, Xigua and Kuaishou channel links count as channels.** A link to a Douyin account page
  (`douyin.com/user/…`, or the `iesdouyin.com/share/user/…` form an expanded share link takes), a Xigua channel
  (`ixigua.com/home/…`, `m.ixigua.com/user/…`) or a Kuaishou profile (`kuaishou.com/profile/…`,
  `live.kuaishou.com/profile/…`) is now read as a channel link, and Douyin's open-platform player
  (`open.douyin.com/player/video`) as an embedded player; through 1.5.0 only YouTube, Bilibili and Vimeo were.
  Short links (`v.douyin.com`, `v.kuaishou.com`) and single-video URLs are never channels. The evidence line now
  says "channel links", not "official channel links", because a link to an account the site does not own counts too.
  Direction: up, on sites that link them. The leaderboard picks this up at its next run.

## [1.5.0] — 2026-09-30

A release about reading sites the way the rubric says, and about failing CI for the right reason. The two
crawler gates now read only the ten retrieval crawlers, choose each crawler's robots.txt group as RFC 9309
does and retry a request that got no answer before they count it; a bot-challenge page is no longer scored
as a page that needs JavaScript; every page is read in its own language; and a figure counts as sourced
only when its source sits beside it. These fixes move scores, and each one below names its check and its
direction. For CI there are `--fail-on-gate` and `--assert` (a gate at zero caps a score at 40, and a site
that would otherwise score 40 or more reads exactly 40, which `--fail-under 40` lets through),
`geo-score diff` and `--baseline` to compare two reports check by check, and a shields.io endpoint badge.
A site that cannot be scored fails fast and says why in one line, in JSON under `--json`, and a scoring
run can no longer hang. Around the CLI: a schema and typo warnings for the watch config, installs from the
release wheel without git, a gate that pins its tools, CI examples beyond GitHub, forms for disputing a
leaderboard row, and a benchmark that can be re-measured and taken apart. The leaderboard itself is still
the 1.3.0 run of 2026-09-27.

**Upgrading from 1.4.0.** Level-1 scores move only where 1.4.0 read a site wrong, and every such fix is
under Fixed with its check and direction: the gates (`g.robots`, `g.reachable`, and `g.ssr` for sites
behind a bot challenge, with Japanese or Korean pages, or with English pages that carry more than 20 Han
characters), the checks that read page text (`p2.answer-passages`, `p2.question-intent`,
`p2.sourced-stats`, `p2.named-author`, `p4.answer-shape`, `p4.cn-engines` and `p3.knowledge-graph`), and
the checks whose file, logo or crawler request is now retried (`p1.llms-txt`, `b.llms-full`, `b.ai-txt`,
`p1.organization` and `p4.cn-engines`). Three invocations exit differently: a site that serves only
bot-challenge pages exits 2 instead of being scored; an unexpected error exits 2 in one line instead of
a traceback that exited 1; and `--sample` below 1 exits 2, where 1.4.0 crashed on 0 and scored fewer
pages on a negative value. `diff` is now a subcommand, so a host named `diff` is written
`https://diff`. `audience_language` can hold languages other than `en` and `zh-CN`, and the report gains
only the optional `elapsed_s`.

### Added
- **A glossary and a Chinese CLI reference.** `guide/glossary.md` (and `guide/glossary.zh-CN.md`) defines the 49
  terms the README, the reports and the guides use, each with where it appears and which page goes deeper;
  `cli/README.zh-CN.md` is the CLI reference in Simplified Chinese, with a language switch at the top of both.
- **`--fail-on-gate` and `--assert EXPR`**, in the CLI and as the Action inputs `fail-on-gate` and
  `assert`. A gate at zero caps the score at 40: a site that would otherwise score 40 or more reads
  exactly 40 and passes `--fail-under 40` (`fail-under: 40`). `--fail-on-gate` fails any capped site: it
  exits 1 when any `g.*` check scores 0, and names the gate and its evidence; it is the same as
  `--assert 'g.*>0'`. `--assert` holds one check, or an fnmatch glob of checks, to a value, e.g.
  `g.robots=max` or `p1.llms-txt>=4`, and is repeatable. A check the run could not observe is skipped,
  never failed. A malformed expression, or a glob that names no check, exits 2.
  Both are opt-in and change no score, and their results go to stderr, never into the report.
- **`geo-score diff BEFORE AFTER [--format text|md|json] [--fail-on-drop]`** compares two level-1 reports
  check by check. Each check shows its points before and after, its max, and a state: `up`, `down`,
  `same`, `became unobservable`, `became observable`, or `unobservable` when neither report observed it.
  The comparison also shows the score, band and gate cap before and after, names each gate that reached
  or left 0, and lists the pages added to or removed from the sample. When the two samples differ, it
  says so, reads the totals as ±5 (benchmark/REPRODUCIBILITY.md) and names `g.reachable` as the least
  stable check. A check that became unobservable is never shown as a drop to 0. `--format json` follows
  the new `schema/diff.v1.json`. Two reports of different rubric versions exit 2, and reports from
  different releases, or of two different targets, are compared with a warning on stderr. `diff` needs
  only `geo_score.py`.
- **`--baseline REPORT`** on a scoring run scores the baseline's pages again (as `--urls-from` does) and
  prints the same comparison after the report. It cannot be combined with `--urls` or `--urls-from`.
  Under `--json`, stdout carries only the report and the comparison is not printed: write the report
  with `--json-out` and run `geo-score diff` on the two files to see it. `--fail-on-drop` still exits 4
  and names each drop on stderr.
- **`--fail-on-drop`** (with `--baseline`, or on `diff`) exits 4 when a check lost points, a gate reached
  0 or the band fell, and prints one stderr line per reason. It is opt-in, as `watch diff --fail-on-drop`
  is, so no existing invocation changes its exit code. A failed `--fail-under`, `--fail-on-gate` or
  `--assert` still exits 1.
- **Action:** a `baseline` input, `delta` and `dropped-checks` outputs, and a "Changes since baseline"
  section in the job summary, with the check ids read from the baseline escaped. The baseline may be the
  same file as `json-out`.
- **A badge that stays current.** `--badge-json FILE` writes the badge as [shields.io
  endpoint](https://shields.io/badges/endpoint-badge) JSON:
  `{"schemaVersion": 1, "label": "AIV readiness", "message": "71/100 Solid", "color": "#2f8f52", "cacheSeconds": 86400}`.
  The SVG and the JSON take their message and colour from one helper, so the two cannot disagree. Host
  the file anywhere and `https://img.shields.io/endpoint?url=<its URL>` draws the badge. The Action gets
  a `badge` input: a path ending in `.json` gets the endpoint JSON, and any other path gets the SVG. A
  `badge-path` output says where the file went.
- **A JSON error instead of nothing.** Under `--json`, every exit 2, usage errors included, prints
  `{"error": {"kind", "message", "target"}, "tool": "geo-score-cli/X.Y.Z"}` on stdout, where stdout used
  to be empty; `diff --format json` does the same. The new `schema/error.v1.json` names the kinds: `dns`,
  `refused`, `tls`, `timeout`, `dropped` and `no_response` when nothing answered; `http_<code>`,
  `no_content`, `slow` and `bot_challenge` when the site answered; `deadline` when the run ran out of
  time; `not_public` under the MCP server's address guard; and `usage`, `rubric_mismatch` (reports of two
  rubric versions given to `diff` or `--baseline`), `error` and `internal`. A minor release may add
  kinds; read an unknown one as `error`.
- **`--timeout SECONDS`** (default 15, as before; up to 300): how long each request may wait for the
  server before it counts as unanswered.
- **`elapsed_s` in the JSON report** (optional, `schema/report.v2.json`): how many seconds the run took
  on the machine that ran it. The footer prints it too (`· took 23.4 s`). It describes the run, not the
  site, and `diff` ignores it.
- **A schema for `geo-score-watch.json`, and a warning for every key nothing reads.**
  `schema/watch-config.v1.json` (JSON Schema draft 2020-12) describes the file, and `watch init` now
  writes `"$schema"` as its first key, so an editor checks and completes it. A mistyped key used to
  vanish without a word: `budget` for `budget_usd` meant no budget, and `max_call` for `max_calls` the
  default cap of 120. `watch check` names every unknown key at every level (top, `brand`,
  `competitors[i]`, `engines[i]`, `prices.<id>`), with the nearest known key when one is close, as in
  `unknown key 'budget' (did you mean 'budget_usd'?); it is ignored`, and flags a `prices` entry that
  names no engine. `watch run` and the other commands that read the config print the same warnings on
  stderr; the MCP `status` tool lists them, and `run` shows them with its plan and after a saved run. A
  key named like a credential (`api_key`, `OPENAI_KEY`, `api_token`, `client_secret`, `credentials` …)
  is pointed at environment variables instead, and its value is never printed. Warnings only: no exit
  code changes.
- **CI beyond GitHub.** `examples/ci/gitlab-ci.yml` is a GitLab job on `python:3.12-slim`: it downloads
  `geo_score.py` from a pinned release, checks it against `SHA256SUMS`, scores once, keeps
  `geo-score.json` as an artifact and hands `geo-score.xml` to GitLab as a JUnit report, so a check at
  zero shows as a failed test. `examples/ci/README.md` gives the one directive that Bitbucket Pipelines,
  Azure Pipelines, Jenkins and CircleCI each need to show the `--junit` file.
- **Where to report what.** A *Benchmark correction* form disputes a leaderboard row's score, gate
  reason, label or not-scored reason, with a fresh `--json-out` report and the tool version; a *Tool
  problem* form covers the CLI, the Action, the MCP server, pip/pipx/uvx, the MCPB bundle, the Claude
  Code plugin, the Gemini CLI extension and Docker. The issue chooser links the troubleshooting guide and
  the MCP troubleshooting section, and a new `SUPPORT.md` says which form takes what. The forms applied
  `benchmark`, `engine` and `rubric`, labels the repository did not have, so those issues arrived
  unlabelled: `.github/labels.json` now lists every label, and `scripts/sync_labels.py` carries the list
  to GitHub (a dry run by default; `--apply` creates and updates, `--check` exits 1 when a label is
  missing, and it never deletes one). It prints a proxy's host and port, never the credentials in
  `HTTPS_PROXY`.
- **Benchmark: a re-runnable retest study.** `benchmark/retest.py` takes two or more run directories
  (results.json plus raw/) and records each run's tool, date, Python, declared vantage and pinning. For
  each pair it reports the shares identical, within ±2 and within ±5, ICC(A,1) and SEM, band changes and
  gate-cap flips, and per check the tier flips and the unobservable rate in each run. It keeps one record
  per site per run, so every figure can be recomputed; `--check` verifies the committed files
  (`validate.py` rule 32). `benchmark/run.py` gains `--out DIR` (a run for the study that leaves the
  published files alone), `--urls-from-dir DIR` (each site re-reads an earlier run's pages, through the
  CLI's `--urls-from` reader) and `--vantage LABEL`, recorded in results.json as `measured_from` beside
  `python` and `pinned_from`. The operator declares the label; nothing looks an address up.
- **Benchmark: the Chinese-market gap, taken apart.** `benchmark/stats.json` gains `china_gap_detail`,
  drawn after the existing bootstraps from the same seed, so no published interval moves: the gap by
  audience language beside the sector-label gap, with their cross-tab (37/27/13/240); four matched sector
  families, with no figure below 10 sites; the raw-point gap split into rule-read and heuristic checks
  (68% heuristic, an upper bound on what a heuristic misreading could explain); `p3.knowledge-graph`
  unobservable on 33 of 50 Chinese-language sites against 76 of 267 others; and the gap with that check
  imputed as 0 (20 points) or as 4 (19 points).
- **Benchmark: flat downloads.** `benchmark/results.csv` has one row per listed site (its fields,
  `sample_n`, `sample_source`, the not-scored reason and the error, then one column per check holding its
  points, blank where the check was not observable); `benchmark/checks.csv` has one row per scored site
  and check. `run.py` writes both, `--readme-only` included; the leaderboard's Dataset markup and
  llms.txt link them; `validate.py` rule 35 checks every cell against results.json and raw/. There is no
  robots.csv yet: raw/ does not record the status each user-agent got.
- **Benchmark: what each row rests on.** Every row's real sample size (`sample_n`, `sample_source`) is
  published, read from raw/ for the committed rows. The 69 rows scored on fewer than 4 pages are marked
  *thin sample* in the benchmark README and on both pages, which can filter on them, and stats.json puts
  the median without them (62) beside the headline 56 (`validate.py` rule 33). A table computed from
  raw/ shows how common each practice is: `llms.txt` served on 137 of 317 sites, complete Organization
  and WebSite markup on 98, BreadcrumbList on a nested page on 82 of 251, a sitemap with `lastmod` on
  161, a personal byline on at least half the pages on 67. The Web Almanac 2025 `llms.txt` figure sits
  beside it, with a line saying the populations differ.
- **Benchmark: how it fetches, and how to correct a row.** "How the benchmark fetches" states the
  per-site request budget, computed from the CLI's own user-agent lists and constants (at most 67
  requests to the site and 20 elsewhere, counted before redirects and retries), and says that crawler
  user-agents are sent from the operator's address, not the vendors'. "Corrections" links the correction
  form: a confirmed tool error ships as a patch release, and published scores change only when a site is
  measured again. `run.py` files a CLI error that starts with
  `bot challenge served to a browser user-agent` under a not-scored reason of its own, and the Not
  scored list is grouped by reason. A row measured with 1.5.0 or later keeps the CLI's error kind
  (`error_kind` in results.json) and is filed by it: `http_*` as refused, `timeout`, `slow` and `deadline`
  as timed out, and `dns`, `refused`, `tls`, `dropped` and `no_response` as connection failed. Rows
  measured with 1.3.0 are still filed by their message. When a site and its `www` host both fail, the row
  keeps the error of the attempt that got further (it kept the `www` host's), and an IP address is not
  retried on `www`.
- **Weight sensitivity** (`benchmark/sensitivity.py`, `SENSITIVITY.md` + zh). It first recomputes all 317
  scores from raw/ (0 mismatches), then re-scores them under equal weights, an illustrative
  evidence-basis weighting, each check left out, and 300 seeded draws. The rank order holds (Spearman
  ρ ≥ 0.988 under every weighting); the bands move more: equal weights change 39 sites' bands, the
  evidence-basis weighting 24, the draws a median of 26. Per-check tier spreads and item-rest
  correlations follow, and it ends with input for v1.2. It adds with `math.fsum`, so every Python writes
  the same files. No v1.1 weight changes. `validate.py` rule 36.
- **Where the band cuts fall** (`benchmark/percentiles.py`, `percentiles.json`, a table in the benchmark
  README, `rubric/bands-analysis.md` + zh). Of the 317 sites, 85%, 58%, 34% and 10% reach Early,
  Growing, Solid and Leading. The analysis sets the v1.1 cuts against three criteria (achievable as Core
  Web Vitals defines it: Leading is reached by 10%, with no margin; 168 of 317 sites sit within the
  retest SEM's noise of a cut; 48 of Early's 88 sites are gate-capped) and lists candidates for v1.2. The
  v1.1 cuts are unchanged. `validate.py` rule 37.
- **The gate on every Python.** `scripts/check.sh --all` runs the three CLI suites and the MCP
  conformance check on every Python from 3.8 to 3.14, and on 3.15 when it is installed; `--strict` fails
  with `uv python install X` when a needed Python is missing instead of skipping it. Both combine with
  `--live`, and an unknown argument exits 2. The gate runs every `scripts/test_*.py` and
  `benchmark/test_*.py` on `python3`, so a new suite joins it by its name, and under `--live` it runs
  `scripts/sync_labels.py --check` when `gh` is installed and logged in.
- **New tests.** `scripts/test_ci_examples.py` runs the copyable CI examples with bash against fixture
  sites. `scripts/test_repo_meta.py` checks the forms against the labels, the README badge against its
  recorded run, and the links in the chooser, the forms, `SUPPORT.md` and the PR template.
  `benchmark/test_benchmark.py` tests retest.py, the qualifiers, the canonical URLs, the China-gap
  suppression, the sample sizes, the fetch budget, the CSVs, the sensitivity and percentile arithmetic
  and the validity figures, offline. `scripts/test_packaging.py` now checks that every tracked file
  naming a release is one `release.py --bump` rewrites (the changelogs, benchmark/raw/, dist/,
  docs/*.html and .github/validate.py are exempt), that every release-wheel URL's tag and file name
  equal `__version__`, that validate.yml installs the ruff and jsonschema versions check.sh pins and
  pins its actions by commit, that the Dockerfile's base is pinned by digest, and that the pyproject
  classifiers cover 3.8 to 3.14 while validate.yml and RELEASING.md name the same two ends.
  `cli/test_geo_score.py` adds seven inputs that crashed 1.4.0's parsers and a seeded property test that
  sends 200 random pages and robots.txt files through the parsers and `run()`, and it runs the MCP
  address guard's connect-time pinning, its refusal of a name that rebinds to a private address and its
  CONNECT branch for HTTPS through a proxy, code no test had run before. `cli/test_geo_score_e2e.py`
  injects faults (dropped connections, 429, fixed statuses, answers that trickle in), counts every
  request the good fixture makes, and holds `diff` to golden files.

### Changed
- **Docs: what an API run cannot see, and the OpenRouter example.** The README and the watch methodology (a
  new §7) list the surfaces these APIs cannot reach and say that a citation is presence, not merit. The
  OpenRouter example engine is now `deepseek-via-openrouter`, and the docs say an OpenRouter engine measures
  the model answering over OpenRouter's search, not the vendor's own; `country` is applied by OpenAI, Claude and
  Perplexity and ignored by Gemini and OpenRouter.
- **The headline names the gate.** Each gate at zero is named with the first sentence of its evidence, in
  the default view and in `--brief`:
  `GATE AT ZERO — g.ssr: 0 of 8 sampled pages carry substantive body text …; the score cannot exceed 40 while a gate is at zero`.
  It used to say only `GATE CAPPED — a gate check scored zero`.
- **One order of gaps in every view.** The default view, `--brief` and `--share` rank gaps the same way:
  gates at zero first, then the points the next tier adds, then rubric order. Each row prints the number
  that belongs to the condition beside it, for example
  `+4 next tier (+9 to full)  Self-contained answer passages  needs: …`. Before, it printed the full
  headroom next to the next tier's condition. `--share` now names the gate: "robots.txt disallows AI
  retrieval crawlers", "AI retrieval crawlers are refused" or "crawlers get no server-rendered body
  text". Before, it said a crawler "cannot reach the content at all", whichever gate it was. A content
  gap now reads `(+N at the next tier)`. The MCP `score_site` summary follows too: it opens with the same
  headline when a gate is at zero and lists up to six gaps in the same order, each with what the next
  tier adds. It used to list the six checks with the lowest share of their points, bonus checks among
  them.
- **The report footer.** `Needs judgement:` is split in two. `Needs off-site search or judgement:` lists
  p3.listings, p3.mentions and p4.question-coverage. `Not observable this run:` lists the rest, each with
  a short reason, for example `p4.cn-engines (not a Chinese-language site)`. The report and `--brief`
  print a legend for ✓ ◐ ✗ ⊘. The rubric and troubleshooting links point at this release's tag
  (`blob/v1.5.0/…`), as each check's `doc_url` already did. The terminal layout is not a contract.
- **One fetch wave after the sample.** Once the sampled pages are in, every request whose URL is known
  goes out at once and the checks read the answers from the run's memo: the sitemaps, `llms.txt`,
  `llms-full.txt`, `ai.txt` and `/.well-known/ai.txt` (and the same files under a given path), the
  Organization logo, up to 8 `sameAs` profiles, the Chinese crawlers and the 30 retrieval probes. The
  Wikidata and Wikipedia lookups run beside them, one brand candidate at a time as before, so they get
  the same lookups. Requests to the site still share 8 connections; other hosts get their own. On the
  test fixtures, with 0.2 s added to every answer, a run went from 18–29 rounds of requests one after
  another to 11–12. The wave itself moves no score and asks for the same URLs as 1.4.0, except
  `/.well-known/ai.txt`, which is now requested even when `/ai.txt` exists. The retries it adds for the
  site's files, the logo and the Chinese crawlers do move scores, and are under Fixed.
- **`--help` stands alone.** It names the command you ran (`geo_score.py` or `geo-score`), lists `diff`,
  `watch` and `mcp` in the usage line, and explains the URL argument and `-q`. It ends with five
  examples, the exit codes (watch's too) and links to the rubric and the troubleshooting guide for this
  release. Without `geo_watch.py`, `mcp`, `watch` and `--ask` say which of them needs it, and show the
  release wheel's `uvx` and `pipx` commands before the clone option.
- The SVG badge of a gate-capped score reads `40/100 Early (gate capped)`, as the endpoint JSON does.
- `diff` is now a subcommand, like `watch` and `mcp`. To score a host literally named `diff`, write
  `https://diff`.
- **The scorer's documents.** guide/troubleshooting.md (EN and zh) has a section for each error kind,
  which the CLI's messages link to at the release tag, a "Why did my score move" section, and "Each page
  is read in its own language" in place of the section on Chinese characters and English words.
  rubric/v1.1.md (EN and zh) says under `g.robots` and `g.reachable` which ten crawlers are read and how,
  and under `g.ssr` that a bot-challenge page is not a sampled page and never reads as tier 0; these are
  clarifications, and no tier or points change. reference/ai-crawlers.md (verified 2026-09-28) says that
  `RETRIEVAL_UAS` is tested against its retrieval table, that the probes are unverified vendor strings
  sent from the auditor's address, that the Claude-SearchBot and Claude-User strings are built from
  Anthropic's documented product token, and that Amazonbot stays a retrieval crawler until Amazon's new
  description of it is reviewed. rubric/open-questions.md (EN and zh) opens two questions for v1.2: #10,
  whether a robots.txt that answers 5xx on every try is a full disallow, and #11, whether a sample with
  no page carrying three figures should leave `p2.sourced-stats` out rather than score 3.
- **Install from the release wheel.** The uvx, pipx and MCP install lines download
  `https://github.com/jianruntech/geo-score/releases/download/vX.Y.Z/geo_score-X.Y.Z-py3-none-any.whl`,
  so they need neither git nor a build step: the README install bullet, the Cursor, VS Code, VS Code
  Insiders and LM Studio buttons, the Claude Code line, the standard `mcpServers` config, every
  per-client block in guide/mcp.md and the MCPB watch-init hint. The git install
  (`git+https://github.com/jianruntech/geo-score@vX.Y.Z`) stays on a line labelled "From source (needs
  git)". `release.py --bump` rewrites the version in the wheel's file name as well as the tag.
- **The gate and the release.** By default the gate looks for Python 3.8, 3.12 and 3.14 (it used to look
  for 3.8, 3.12 and 3.13, never 3.14) and skips one uv cannot find, with its install hint; `--strict`
  requires 3.8 and 3.14. It pins ruff 0.15.15 and jsonschema 4.23.0 (the newest jsonschema that installs
  on Python 3.8): the PATH ruff runs only when it is the pinned version, otherwise `uvx ruff@0.15.15`,
  from uv's cache before the network, and python3's own jsonschema is used when it is the pinned
  version. Offline with a cold cache it falls back to the PATH ruff and python3's jsonschema, as before
  the pin. Under `--all`, the Python after the newest supported one is reported as optional, and `--all`
  without uv says that only python3 runs.
  `release.py --execute` stops at once unless `gh` is logged in, runs `check.sh --live --strict` (it ran
  `--live` before), and stops when the built wheel's file name differs from the one the install lines
  download.
- **validate.yml** sets `permissions: {contents: read}`, pins actions/checkout v7.0.1 and
  actions/setup-python v7.0.0 by commit SHA, sets `persist-credentials: false`, installs the pinned ruff
  and jsonschema, tests 3.8 and 3.14, and runs on `ubuntu-24.04`, the newest image setup-python still
  builds 3.8 for. The Dockerfile's base image is `python:3.12-slim` pinned by its image-index digest
  (3.12.14-slim-trixie, 2026-09-28). pyproject.toml has classifiers for Python 3.8 to 3.14 and
  "3 :: Only".
- **Copyable CI.** `examples/ci/github-actions.yml` pins `actions/checkout`, `actions/upload-artifact` and
  `github/codeql-action/upload-sarif` to commit SHAs with the release as a comment, sets
  `persist-credentials: false`, passes step outputs through `env:`, and says how to hold the Action
  still between runs (a release tag, or that release's commit). `examples/ci/watch-weekly.yml` pins
  `actions/checkout` and `actions/setup-python` the same way and keeps its credentials, because it
  pushes the run file.
- **The README badge is a recorded run.** It is regenerated from one run on the leaderboard page, kept
  in `docs/aiv-badge.json` (2026-09-28, geo-score 1.4.0): 93/100 Leading, and its alt text names that
  date and version. The old badge read 87 and was committed by hand. The scorer did not change.
- **Contributing.** The pull request template asks for the last lines of `bash scripts/check.sh`, both
  changelogs, English and Chinese kept in step, the benchmark regeneration and disclosure of an
  employer's site, and uses only absolute links. It and CONTRIBUTING.md name every file a new rubric
  version needs: the next version's rubric in both languages and as JSON, both evidence tables and a
  public audit scored with it. CONTRIBUTING.md also lists the two new test suites.
- **The leaderboard has one address.** Its canonical, og:url, og:image, hreflang, llms.txt and sitemap
  URLs point at the maintained mirror, https://www.jianruntech.com/leaderboard and /leaderboard/zh,
  instead of the GitHub Pages copy frozen at 229 sites; `GEO_SITE_BASE` still overrides.
  `scripts/check_live.py` defaults to the mirror and reads the site count, median and date from the page
  itself. `validate.py` rule 30.
- **The CLI-vs-hand-audit headline compares like with like.** On the checks both scored, the CLI reads
  0.4 points lower on average (per site from 6 lower to 9 higher, mean absolute difference 5.2;
  Bland-Altman bias −0.4, 95% limits −12.8 to +12.0, n=5), kept in `benchmark/validity.json` as
  `common_checks` beside a `validation_set` block. The full-score figure, 3.6 points lower, comes second:
  the hand audits also score `p3.listings`, `p3.mentions` and `p4.question-coverage`, which the CLI
  leaves out. VALIDITY.md (EN + zh) adds three caveats: the five sites are the v1.0→v1.1 calibration
  sites, so this is development data; they score 69–87, with one Chinese site and none capped; and the
  audit files do not record the rater. Both READMEs lead with the like-for-like figure, and
  `validate.py` rule 23 holds it and `common_checks` to the per-site rows. The 1.3.0 entry stays as
  released.
- **The Chinese-market gap is decomposed** rather than quoted whole, in benchmark/README.md, on the
  leaderboard pages and in both READMEs: the 20-point gap states its definition (the five China
  sectors), the language gap (20 points, 95% CI 13–25), the range within matched sector families (6 to
  30 points) and the heuristic upper bound (68%). `validate.py` rules 31 and 38.
- **REPRODUCIBILITY.md says what the ±5 / 96% was measured with:** 229 sites on 2026-09-09, with a 1.1.x
  build before the 1.1.2 variance fixes. It adds ICC(A,1) 0.974, SEM 3.09 and 18 band changes, and its
  tables are generated by retest.py. `reproducibility.json` moves to format 2 and keeps those runs under
  `legacy`. The pages' footer and both READMEs name the date and the build.
- **Evidence notes, metadata only** (no weight or tier changes): `p2.question-intent` records that
  through 1.4.x the CLI's Chinese heading lexicon lacked the task and explanation forms its English
  lexicon matches, and `p3.knowledge-graph` that the CLI queries Wikidata and Wikipedia but not Baidu
  Baike. The rubric README and the evidence table link the sensitivity study, and the calibration record
  the bands analysis.

### Fixed
- **The sample is documents.** A file that a sitemap or a link lists (Markdown such as `agents.md`, feeds,
  JSON, PDFs, media) is never a sampled page, and listing pages (pagination, category, tag, author, series
  and archive pages) are drawn only after every content page. Direction: either way, toward what the site's
  content reads. On the 1.3.0 leaderboard, 5 sites had a file in their sample and 39 had two or more
  listing pages; baseus.com had been scored on `agents.md` alone.
- **`p1.llms-txt`: no answer is not observed.** An `/llms.txt` that gets no answer after its retries now
  leaves the denominator instead of scoring 0. Direction: 0 to not observed (38 sites on the first 1.5.0
  pass read 0 from a request that never got an answer).
- **A handshake cut off in the middle is a dropped connection.** An SSL EOF during the handshake is now kind
  `dropped` and is retried, not `tls`, which is not. A `tls` error on a Python whose TLS library cannot speak
  TLS 1.3 says so: macOS's `/usr/bin/python3` is built on LibreSSL 2.8, and many sites require TLS 1.3.
- **The leaderboard tries network failures again.** `benchmark/run.py` tries a site whose failure was a network
  fault (a dropped connection, a timeout, a TLS error, a 429 or a 5xx) once more at the end of the run. The
  1.5.0 leaderboard is run on Python 3.12: a first pass on the system Python lost 68 sites to TLS errors.
- **`g.robots` and `g.reachable` score the 10 retrieval crawlers of `reference/ai-crawlers.md`, and only
  those.** Claude-User, Googlebot and Amazonbot are added. GPTBot, ClaudeBot and a made-up
  Google-Extended probe are removed. Each crawler is sent with its vendor-documented user-agent string.
  `g.robots` now chooses each crawler's rules as RFC 9309 2.2.1 says: a crawler's own group replaces `*`.
  A leading byte-order mark no longer hides the first group. Scores move in three ways:
  - **Up** for sites that block only training crawlers or opt-out tokens. On the leaderboard, measured
    2026-09-28: together.ai, lonelyplanet.com, loom.com, stackoverflow.blog, webmd.com, airbnb.com and
    khanacademy.org leave `g.robots` 0. airbnb.com stays capped by `g.reachable`, because it returns 403
    to every crawler user-agent.
  - **Up** for a `*` Disallow alongside named Allows for the retrieval crawlers.
  - **Down** where a site blocks Claude-User, Googlebot or Amazonbot, or where a byte-order mark hid a
    blocking group. healthline.com stays at 0, now for Amazonbot.

  Evidence now names the blocked crawlers and their group. Training crawlers and opt-out tokens
  disallowed by name are listed as "not scored". `g.reachable` evidence lists the agents it did not
  reach.
- **A transient fault is retried before it moves a gate.** robots.txt, the homepage and the sitemap are
  fetched once per run, with retries. `g.reachable` probes retry once on no answer, 429 or 5xx, and honour
  Retry-After up to 5 s. A crawler that gets no answer on any page (a timeout or a dropped connection on
  every try) is not counted: from one address that is mostly the network, or a firewall dropping a crawler
  user-agent sent from an address its vendor does not use, which the real crawler never meets. The tier is
  read over the crawlers that answered; tier 0 ("most retrieval user-agents are blocked") needs HTTP
  refusals from more than half of all ten; with fewer than half answering, the check is not observed. A crawler answered
  on some pages counts as reached. This rule came from 1.5.0's first leaderboard run, which read silence as
  refusal and gate-capped 31 sites that a browser and most crawlers reached (pulumi.com went from 99 to 40);
  on the five hand audits it takes `g.reachable`'s exact agreement from 0.4 to 0.8.
- **A homepage that cannot be fetched is not a missing entity.** When the homepage is in the sample but
  fails, `p1.organization`, `p3.sameas` and `p3.knowledge-graph` read not observed instead of 0 if the
  other pages lack the entity: it usually sits on the homepage. Direction: 0 to not observed, on runs
  where the homepage failed (nextjs.org's hand-audit comparison had read all three as 0 after one failed
  fetch). A robots.txt that cannot be read after 3 tries is now not observed and leaves the
  denominator, instead of reading as "No robots.txt". One that answers 429 or 5xx on every try keeps tier
  3 and says so. The direction is either way: down where a dropped robots.txt fetch hid a Disallow, up
  where a transient 429 or reset on a crawler probe read as a block. Five rows of the 1.3.0 leaderboard
  took their `g.robots` from a failed fetch ("No robots.txt (HTTP 0)"): clickpaas.com, codecademy.com,
  continue.dev, helium10.com and xcmg.com.
- **The site's files, the Organization logo and the Chinese crawlers are retried.** 1.4.0 asked once for
  `llms.txt`, `llms-full.txt`, `ai.txt`, the logo and the home page as each Chinese crawler, so one
  timeout, reset, 429 or 5xx read as a file that is not there, a logo that does not resolve or a crawler
  that was not reached. The files and the logo are now retried like the sitemaps (up to 3 tries) and the
  Chinese crawlers like the retrieval probes (one retry); a request still unanswered after its tries reads
  as before, and a definite answer is asked once, so a healthy site gets no extra request. Direction: up,
  where a transient fault used to read as absent, in `p1.llms-txt`, `b.llms-full`, `b.ai-txt`, the logo
  part of `p1.organization` and `p4.cn-engines`. Two of seven live runs through a proxy had lost
  `p1.llms-txt` to a single timeout.
- **A bot-challenge page is not scored.** When a bot-protection service (AWS WAF, Akamai, Cloudflare,
  Fastly, PerimeterX, DataDome or Imperva) sends the CLI's browser user-agent a challenge page instead of
  the page, that page is dropped from the sample like a failed fetch. A site that serves nothing but
  challenges used to be scored `g.ssr` 0 and capped at 40, and the leaderboard published that as "content
  needs JavaScript". It is now not scored: it exits 2 with
  `bot challenge served to a browser user-agent (<vendor>): a static fetch cannot measure this site`, and
  under `--json` it gives the error kind `bot_challenge`. Direction: `g.ssr` goes from 0 to not scored
  for such sites: live on 2026-09-30, ups.com (Akamai), which the 1.3.0 leaderboard shows at 16, capped,
  got the bot-challenge error. A site that serves challenges on only some pages is scored on the real
  pages left, and its notes count the challenges: booking.com (AWS WAF, 20 and capped on the 1.3.0
  leaderboard) got the bot-challenge error on one run on 2026-09-30, and on two others that day was
  scored on the pages left. openai.com, which the 1.3.0 leaderboard lists as "all requests returned
  403", answers with a Cloudflare challenge and now gets the bot-challenge error. A JavaScript shell that
  only loads a vendor's sensor script still scores `g.ssr` 0. HTTP error pages are now decompressed when
  gzipped, so a gzipped challenge is recognised.
- **A report scored on fewer pages says so.** `notes` gains
  `Scored on N of M sampled pages; K returned errors, J were bot challenges` when pages were dropped.
  When discovery found fewer pages than asked for, it gains
  `Sampled N of the 8 pages asked for: no more were found (sample source: …)`. `schema/report.v2.json`
  (`sampled_urls`) has always asked for this. The terminal report prints the same lines. No score
  changes.
- **`p2.sourced-stats` counts a source only beside its figure.** A figure is attributed only when its own
  block of the content (a paragraph, list item, table cell, definition, caption or quotation), or the next
  block, holds a link to a source off the site, a `<cite>`, a source phrase, or a footnote reference whose
  note links to a source. The content is the first `<main>` or `<article>`, or else the page without its
  header, navigation, footer and asides. Links to the site's own hosts, to its own `sameAs` profiles and
  to social profiles or share buttons are not sources. 1.4.0 took any two outbound links, `<cite>` or
  `<blockquote>` elements or source words anywhere in a page's main HTML as the source of all its figures,
  so a social icon, a partner logo or a "Research" menu item did it. Fewer things are figures: a year, a
  version number, a dotted date, a day of the month, a `#` reference, an identifier (seven or more digits
  in a row, or a number that `ICP备`, `ICP证`, `公安备`, `网安备` or `号` introduces, or that `号` follows: filing,
  account and phone numbers), and a price (a sum written the way only a price is, such as `$29/mo`,
  `68元/月`, `$15 per user` or `¥68起`, one after a price word such as `每月`, `售价`, `起价` or `低至`, or one that
  is all its block says, such as a pricing card's `$29`). Any other sum of money is still a figure, and so
  is one with a magnitude after it (`$4.5 billion`, `3000亿元`). The tiers keep their page-fraction
  structure: 7 needs three quarters of the pages that carry three or more figures to attribute most of
  them with a link, 5 needs half with any attribution, 3 any attributed figure; a sample with no such page
  keeps 3. The evidence gives the counts. The direction is down. Re-scored with 1.5.0 on 2026-09-30 on the
  pages their 1.3.0 leaderboard reports sampled, sentry.io and seeyon.com read 3 (7 on the 1.3.0
  leaderboard) and mingdao.com 0 (7); mistral.ai, whose pages are French, is not measured (5; see page
  language below). On the five hand-audited sites, re-scored on their audited pages the same day, the CLI
  now matches the auditor's tier on 4 of 5, against 1 of 5 in VALIDITY.md (measured with 1.3.0, when it
  read higher on the other four); on mingdao.com it reads 0 against the auditor's 3.
- **Each page is read in its own language.** A sampled page's language comes from its `<html lang>`, or
  else its `Content-Language` header, unless the visible text contradicts it. With neither, it comes from
  the script (kana is Japanese, hangul Korean, Han alone Chinese) and, for Latin-script text, from a few
  common words (English, German, French, Spanish, Portuguese). Code samples (`<pre>`, `<code>`) are not
  read for this, and a page declared Chinese, Japanese or Korean keeps its declaration while it carries
  30 or more such characters. Through 1.4.x one Chinese page switched every page of a run to the Chinese
  thresholds, a Japanese site was labelled `zh-CN`, and German or French headings were read with the
  English lexicon. The checks that move, and which way:
  - `p2.answer-passages` goes up. Each page is counted in its own unit: characters (50–200) on Chinese,
    Japanese and Korean pages, words (25–120) everywhere else. English pages in a sample whose homepage
    is Chinese are now counted in words (airwallex.com's had scored 0 of 8), and kana and hangul now
    count as characters. The evidence says which unit applied to how many pages.
  - `g.ssr` goes up on Japanese and Korean pages, whose kana and hangul now count toward the 120 floor (a
    Japanese fixture went from 0, which capped its score at 40, to 5). It also goes up on English pages
    whose main text carries more than 20 Han characters, such as a language menu. The "content needs
    JavaScript" reading moves the same way.
  - `p2.question-intent`: pages in a language without a heading lexicon (the CLI has English and Chinese)
    leave the count. A site with no page left is not measured ("no question-intent lexicon for ja")
    instead of being read with the English lexicon. It goes up for Chinese task, explanation and
    comparison headings (`创建你的第一个应用`, `工作流的工作原理`, `价格与版本对比`), with noun compounds
    such as `管理团队` and `处理器` and the product specs `对比度` (contrast ratio) and `原理图`
    (schematic) left out, and for English comparison headings (compare, vs, versus, compared).
  - `p2.sourced-stats` and `p2.named-author` move toward not measured. Source phrases and written "By …"
    bylines are read only on English and Chinese pages. A link, a `<cite>`, a footnote, and an author in
    structured data or `rel="author"` are read in any language. The check leaves the denominator instead
    of scoring 0 in two cases: no page carrying figures could be read for a source phrase and the reading
    is below 5, or no page could be read for a byline.
  - `p4.cn-engines` leaves the denominator on Japanese and Korean sites. It is observed when a sampled
    page is Chinese or the host name ends in `.cn`, no longer on any page heavy with Han characters. It
    also leaves the denominator on a site with no Chinese page whose address merely contains `.cn`, such
    as `www.cnn.com` or `www.cnbc.com`: 1.4.0 tested for `.cn` anywhere in the address. No leaderboard
    site is one of these.
  - `p4.answer-shape` goes down on some pages because the paragraph-length limit is now set per page.
    English pages in a sample with a Chinese homepage are held to 90 words again, and Japanese paragraphs
    count their kana.
  - `p3.knowledge-graph`: Wikidata and Wikipedia are searched in English and in the most common page
    language other than English, when Wikipedia has a large edition in it. Japanese sites are no longer
    searched in Chinese. A brand name is still searched in two languages at most.
- **`audience_language` is the most common page language**, as a BCP 47 primary tag (`en`, `ja`, `de`, …).
  Chinese stays `zh-CN`, and `und` means no page's language could be told. A sample with a Chinese
  homepage and English pages is now `en`. The field was already a BCP 47 string. The description in
  schema/report.v2.json now says what it holds.
- **An unreachable site fails fast and says why.** A typo or a dead host took from 20 seconds to 4
  minutes and ended in raw urllib text. The CLI now resolves the host once before a run (not when a proxy
  carries the request, since the proxy resolves it), and a name that does not exist fails at once with
  `cannot resolve <host>: check the spelling, or your DNS/proxy settings (HTTPS_PROXY)`. A name that does
  not resolve, a refused connection and a failed TLS handshake are not retried. The final error is one
  sentence that names the kind of failure, the proxy when one carried the request (host and port, never
  credentials) and the troubleshooting section for it, pinned to the release tag. Input that is not an
  http or https URL with a host (whitespace, another scheme, a port outside 1–65535) is a usage error,
  exit 2; localhost, IP literals and dotless intranet names are still scored. A site that answers is
  scored exactly as before.
- **A slow server can no longer hold a run.** `--timeout` limits each read, not their sum: a server that
  sent one byte every few seconds held a fetch, and a CI job or an MCP worker with it, for hours. One
  request, redirects included, now takes at most 30 s or twice `--timeout`, whichever is longer, and then
  counts as kind `slow`, without a retry. One scoring run takes at most 300 s: after that no request
  starts, one in flight stops as kind `deadline`, and the checks that needed it are not observed, a gate
  included, rather than scored 0. The HTML scanners that retried every unclosed tag to the end of the
  page (80 KB of `<script>x ` took 1.8 s, and a 4 MB page would have taken hours) read a page in one
  pass, with the same results. A site that answers within these limits scores as before.
- **Malformed markup can no longer crash a run.** `{"@type": {"@id": …}}`, a link, Sitemap line or logo
  URL such as `http://[::1`, a lone surrogate escape in a JSON-LD name, or JSON-LD nested 2000 deep ended
  a run with a traceback and exit 1, which CI reads as "below `--fail-under`". Only a string names a type
  now, a malformed link reads as no link, a lone surrogate becomes `?` (an emoji still comes through
  whole), and JSON-LD is flattened without recursion. Any other unexpected error prints
  `geo-score internal error (<Type>) while scoring <url>; please report it at …/issues` and exits 2;
  `GEO_SCORE_DEBUG=1` shows the traceback. No score changes.
- `--sample` below 1 is now a usage error (exit 2). Before, 0 crashed and a negative value silently
  scored fewer pages. The Action's `sample` input takes a whole number of 1 or more.
- cli/README.md said the GitHub Action regenerates the badge "if you point `json-out` at a path". It
  never did. The section now describes only what exists: `--badge`, `--badge-json`, the Action's `badge`
  input and the shields.io recipe.
- The distance to the next band reads `1 point to Solid`, not `1 points to Solid`, in the report and in
  `--brief`.
- **Saving a paid run is all or nothing.** An answer holding half a surrogate pair (half an emoji, which
  a provider can send) stopped the save half way and left a truncated run file: the paid run was lost,
  and `watch report`, `watch diff` and the MCP tools failed on the latest run until the file was deleted
  by hand. A run is now written in full to a hidden temporary file, synced to disk and only then linked
  into place under a run id no other file has (`<id>-2` and on when the id is taken), so a failed save
  leaves no partial file and the earlier runs as they were. Text UTF-8 cannot carry is stored as `\u`
  escapes, which load back as the same text.
- **Half a surrogate pair no longer crashes `watch run`, `watch report`, `watch ask` or `watch diff`.**
  Text output shows it as a `\u` escape, on stdout and in an `-o` file alike, and
  `watch report --format json` and `watch ask --format json` print such answers.
- **The engines' tuning keys are checked.** `max_tokens`, `max_searches` and `max_results` must be
  positive integers and `tool` a string; `watch check`, and every command that reads the config, now
  refuses anything else, including a string such as `"2048"`, which 1.4.0 accepted. A value pasted into
  `max_tokens` used to reach `int()`, and the error saved in the run file quoted it; the new error never
  shows the value. `runs`, `max_calls` and the tuning keys accept `2.0`, as JSON Schema does.
- **MCP `score_site` says why it refuses a host.** A name that does not resolve gets
  `cannot resolve <host>: check the spelling, or your DNS/proxy settings`, with a note, when a proxy
  applies, that `score_site` resolves every host on the machine running the server to check it is
  public; such a host used to be called private. A host that resolves to a private, loopback or reserved
  address gets `url must be on a public host: <host> resolves to a private, loopback or reserved address`.
- The MCP rubric resource's `source` links to the rubric at the release tag instead of `main`, and the
  `mcp` entry in `geo_score.py watch --help` names the installed command, `geo-score-mcp`.
- **Installing needs no git.** The documented `uvx` and `pipx` routes and the one-click MCP buttons no
  longer fail on a machine that has uv but no git ("Git operation failed"), and no longer build from
  source on first start. guide/mcp.md (EN + zh) no longer says `score_site` takes about 20 seconds, a
  figure that was never measured, and neither do the leaderboard pages ("about twenty seconds"), the
  README cover image or the demo image's description. How long a run takes depends on the site and the
  network, and the report's `elapsed_s` records it.
- **The 'Anything else' CI snippet** ran the CLI twice, so the report you kept could differ from the run
  that set the exit code, and it did not verify the download. It now downloads `geo_score.py` and
  `SHA256SUMS` from a pinned release and scores once with `--json-out`, `--junit` and `--fail-under`.
  The checksum and the run are chained with `&&`, so a file that does not match stops the step before
  scoring even in a shell without `set -e` (Azure Pipelines script steps) or `pipefail`. The GitLab job
  and the weekly watch workflow check each file against its own `SHA256SUMS` line, and the weekly
  compare step no longer runs after a failed checksum.
- The pull request template's Scope link was relative, which gives a 404 in a PR body. CONTRIBUTING.md
  told rubric contributors to add `rubric/v1.1.md`, the version already released; it now names the next
  one.
- **The leaderboard's groups claim only what the 1.3.0 data supports.** While results.json was measured
  with a tool older than 1.5.0, the robots.txt group carries a qualifier: the 1.3.0 reading counted
  GPTBot, ClaudeBot and Google-Extended as retrieval crawlers, so the 23 include sites that block only
  training crawlers or an opt-out token. The JavaScript group carries one too: that reading could not
  tell a bot-challenge page from a JavaScript shell. Both appear in benchmark/README.md, on both pages
  and in llms.txt, and drop out by themselves once the leaderboard is re-run with 1.5.0 or later. The
  403 group now reads "the server refuses crawler user-agents (unverified probes from the auditor's
  address)", and the pages no longer say the China gap "is not content quality. It is llms.txt,
  Organization schema…": its two largest per-check differences are heuristics.
- The benchmark README no longer claims "the same eight-page sample": it says up to eight pages per
  site, and that 69 sites were scored on fewer than 4 pages (55 of them on a single page).
- **Leaderboard Dataset markup.** `readiness` was described as the "0-100 normalised score"; it is raw
  points, and `normalised` is the percentage. `variableMeasured` lists normalised, readiness,
  observable_max, band and gate_capped, and the download, which pointed at a blob/main page, is
  raw.githubusercontent.com pinned to `v<version>`, with the two CSVs beside it. The licence stays MIT
  for now. `validate.py` rule 34.
- None of the benchmark entries above re-scores a site: results.json is still the 1.3.0 run of
  2026-09-27, and no check id or check reading changes with them.

## [1.4.0] — 2026-09-28

The MCP server becomes a first-class way to use geo-score: its own README section with install
buttons, a guide for every client, one-click packages, both protocol eras, and a surface that says
what costs money and lets you turn that off.

### Added
- **MCP server, both protocol eras.** 2026-07-28 (`server/discover`, per-request `_meta`, cache hints)
  alongside 2025-11-25, 2025-06-18, 2025-03-26 and 2024-11-05 over `initialize`. An unknown legacy
  version gets 2025-11-25; an unsupported modern one gets `-32022` with the supported list. Batches are
  accepted only on 2025-03-26, and a `cursor` is an error because the server never issues one.
- **MCP tools say what they cost.** `score_site` is listed first. Every tool has a title and all four
  annotation hints, descriptions open with the cost ("Free, no API key." / "Paid: …"), input schemas
  reject unknown keys, and nullable fields use `anyOf`, which strict clients accept. `ask` and `run`
  now return structured results, and a `run` dry run returns its plan as data.
- **Cancelling stops spending.** `notifications/cancelled` stops `ask` and `run` before their next
  call; a cancelled run is not saved, and its calls and cost go to stderr. Tool calls run on worker
  threads (up to 4), so the server still answers `ping` during a long run. At end of input it stops the
  paid calls at once and lets free ones answer. One `run` at a time: a second is refused while one is in
  progress, so parallel calls cannot double the spend of one approval.
- **Robustness.** A malformed run file or config is an error answer, never the end of the server;
  arguments that are not an object are refused rather than read as `{}`; stdio is UTF-8 on every
  platform, and a stream that cannot carry a character gets it escaped instead of losing the answer;
  `status` never shows a value pasted into `key_env` and reports `run` as ready only when it could start;
  `GEO_SCORE_MCP_EXCLUDE_TOOLS` and `--exclude-tools` add up.
- **Choose the tools.** `--toolsets score,ask,watch`, `--tools`, `--exclude-tools` and `--read-only`,
  each with a `GEO_SCORE_MCP_*` environment twin. `--read-only` gives a server that cannot spend. A new
  read-only `status` tool reports the version, the config it found, which engines have keys (never the
  keys) and the caps.
- **Prompts and completions.** `audit_site`, `check_citations`, `weekly_watch`, `compare_runs` and
  `explain_check`, with completion for check ids and run ids, and a `geo-score://runs/{run_id}` resource.
  None of them contains fix instructions: measurement is public, remediation is not.
- **Packages.** Every release attaches a Claude Desktop bundle (`geo-score-X.Y.Z.mcpb`) and a
  `server.json` for the MCP Registry, both covered by `SHA256SUMS`. The repository is also a Claude Code
  plugin marketplace (`/plugin marketplace add jianruntech/geo-score`) and a Gemini CLI extension, and
  has a Dockerfile for the stdio server. Nothing is published to a registry, PyPI or a container
  registry yet.
- **Docs.** A `## MCP server` section in both READMEs with install buttons (Cursor, VS Code, VS Code
  Insiders, LM Studio), a standard config, the tool table and example prompts; `guide/mcp.md` with the
  exact setup for Claude Code, Claude Desktop, Codex, Cursor, VS Code, Gemini CLI, Devin Desktop and
  Zed, plus timeouts, security and troubleshooting. `scripts/mcp_docs.py` generates the tables and
  buttons from the server, and `check.sh` fails when they are stale.
- **Checks.** `scripts/check_mcp.py` drives the server over raw stdio in both eras on every tested
  Python; `check.sh --live` repeats it through the official MCP Inspector (2.8.0, `--strict`) and calls
  `score_site`. `scripts/test_packaging.py` checks every manifest against the code. A snapshot and a
  1.3.0 contract baseline stop a tool or a required argument from changing by accident.
- SECURITY.md has a per-tool table of network access, files and spending for the MCP server.

### Changed
- **The leaderboard is re-run with 1.3.0** (2026-09-27): 317 of 370 sites scored, median 56 (95% CI
  52–58), range 11–99; 83 sites (26%) have a gate at zero (47 need JavaScript, 23 block AI crawlers,
  13 serve an error). Across the 312 sites scored in both runs the mean change is −0.4 points; 72% move
  by 5 points or less, which mixes the 1.3.0 scoring fixes with 18 days of site changes and is not a
  reproducibility figure (that study is `benchmark/REPRODUCIBILITY.md`, same tool, two runs).
- Every site's full report from the run is in `benchmark/raw/`, and `validate.py` checks it against
  `results.json` (rule 29).
- The benchmark README's findings are computed rather than written by hand: the headline share,
  the top gaps, and which checks drive the Chinese-market gap. That gap is 20 points (95% CI 16–28),
  and its two largest per-check drivers are heuristics the CLI also read lower than a human on the
  Chinese site in the hand-audit comparison; the README says so.
- The READMEs link the leaderboard on www.jianruntech.com/leaderboard, which is kept current; the
  GitHub Pages copy cannot be rebuilt while Actions and Pages are disabled for the organisation.

## [1.3.0] — 2026-09-27

A release about trust in the measurement: outputs CI systems read natively, a pinned sample for
before/after comparisons, change detection that no longer calls noise a change, offline end-to-end
tests on twelve fixture sites, a measured CLI-vs-hand-audit agreement, and an evidence basis for every
check. The fixtures also found places where the CLI read sites against the rubric (grouped
robots.txt rules, single-page apps' catch-all pages, empty markup, stale `dateModified`, bylines,
Chinese dates and figures); those are fixed and listed below with their direction. The percentage can
no longer pass 100, and the MCP server now keeps every connection on public addresses.

**Upgrading from 1.2.0.** Level 1 scores move only where a check read a site wrongly; each fix and
its direction is listed under *Fixed*, and the public leaderboard (measured with 1.1.0) is not
re-scored. In `watch`, the headline rate leaves out questions that name the brand, intervals widen
when a question has several answers, and some `diff` verdicts that said `change` now say
`within noise` or `too few questions to tell`; the 1.2.0 fields keep their meaning. Evidence strings
now quote site text inside `«site text: …»`. The CSV report has an eleventh column, `branded`.

### Added
- **One run, several outputs:** `--json-out FILE`, `--sarif FILE` (SARIF 2.1.0: one rule per check,
  one result per check below full marks) and `--junit FILE` (one test per check; a check at zero
  fails, an unobservable one is skipped). All are written from the same fetch as the report on
  screen, so they cannot disagree with it. Single site only.
- **Install as a command:** `pyproject.toml`, so `pipx install git+https://github.com/jianruntech/geo-score`
  and `uvx --from git+… geo-score` work. Installs `geo-score` and `geo-score-mcp` (the MCP server over
  stdio). Still no dependencies.
- `STABILITY.md`: what is a public contract (check ids, score arithmetic, the JSON schemas, CLI
  flags, exit codes, Action inputs and outputs, MCP tool names, SARIF rule ids), what semver means
  here, and that nothing is sent anywhere (no telemetry).
- Action inputs `sarif`, `junit` and `annotations`; outputs `gate-capped` and `report-path`.
- **Pin the sample:** `--urls FILE` scores exactly the given pages (up to 8, all on the scored site);
  `--urls-from REPORT.json` re-reads the pages an earlier report sampled. Sampling is the main source
  of run-to-run variance, so a before/after comparison on pinned pages shows what changed on the
  site. The report says `sample_source: "pinned"`. Action input `urls-from`.
- **Per-check documentation links:** every check in the JSON report carries `doc_url`, its definition
  in the rubric pinned to the release tag, so the link never drifts from the scorer. SARIF rules link
  there too, and `--explain` prints it under each check below full marks. Optional field in
  `schema/report.v2.json`.
- [Troubleshooting](guide/troubleshooting.md), in English and Chinese: score movement, checks shown
  as `—`, the gate cap, exit code 2, proxies, redirects, the leaderboard's tool version, `watch`
  exit 3, Action annotation limits, CJK thresholds. The terminal report links to it.
- **Intervals on the leaderboard's medians.** `benchmark/stats.py` computes a seeded bootstrap 95%
  interval for the overall median, each sector median and the Chinese-market gap; `benchmark/README.md`
  and both READMEs quote them: overall 56 (53–58), the gap 19 points (12–26). The hosted page shows
  medians without intervals until it is rebuilt and redeployed. Sectors with fewer than 10 scored sites (China / cloud and Professional services, 9
  each) no longer print a median; `validate.py` counts scored sites, not listed ones.
  `benchmark/run.py --readme-only` regenerates the README without re-scoring.
- The leaderboard can move host: `GEO_SITE_BASE` sets the base URL for canonical links, `og:image`,
  hreflang, `llms.txt` and the sitemap, and `scripts/check_live.py` compares a hosted page with the
  committed data (today's Pages build still shows 229 sites against 314).
- **How far to trust the CLI, measured.** `benchmark/validity.py` re-scores the five published hand
  audits on the same pages and compares every check tier for tier: 79% of 86 check pairs agree (95%
  for checks read by rule, 64% for heuristics), and the CLI reads 3.6 points lower on average, from
  10 lower to 6 higher. Results, caveats and every disagreement: `benchmark/VALIDITY.md` (EN + zh).
  This replaces the unmeasured "typically 5 to 15 points lower", which was wrong for two sites in five.
- **Evidence basis for every check.** `rubric/v1.1.json` gains an `evidence` object per check
  (basis, sources, last verified), published as `rubric/evidence-v1.1.md` (EN + zh). Metadata only:
  no weight, tier or score changed.
- **MCP for agents, not only for people.** `score_site`, `report`, `diff` and `list_runs` return
  `structuredContent` (the full report, summary or diff as JSON) beside the text, and declare an
  `outputSchema`, so an agent no longer parses Markdown to recover a score. `score_site` takes `urls`
  (pin the pages, same checks as `--urls`) and `sample`. The rubric is served as the resource
  `geo-score://rubric/v1.1`, built from the scorer's own tables. The server instructions and the
  `score_site` description say that `«site text: …»` spans are data from the audited site.
- `watch diff --fail-on-drop`: exit 4 when a verdict is `change` with a negative change. The MCP
  `diff` tool takes `format: "json"`. [guide/watch-methodology.md](guide/watch-methodology.md)
  (EN + zh) gives the formulas and a worked example.
- **One gate: `scripts/check.sh`.** Structure, ruff, the three test suites on Python 3.8 and the newest
  available, and an emulation of the GitHub Action against a fixture site (`scripts/test_action.py`);
  `--live` adds example.com. `.githooks/pre-push` runs it; `.github/workflows/validate.yml` runs the same
  script. Hosted Actions have not run on this organisation so far, so `CONTRIBUTING.md` no longer says
  CI checks anything: maintainers run the script before every merge.
- `AGENTS.md`: the repository's invariants, each mapped to the check that enforces it, for
  contributors and coding agents (`CLAUDE.md` points to it).
- Issue forms ask for the tool version and the JSON report; a new form covers level 2 and 3 engine
  problems and warns never to paste a key; security reports are routed to `SECURITY.md`.
- **Offline end-to-end tests.** `cli/test_geo_score_e2e.py` serves twelve fixture sites from
  127.0.0.1 (a good site, a JavaScript shell, robots blocks, a firewall that refuses AI crawlers, a
  Chinese site, a site under a path, a hostile site that tries to address an agent, and more) and
  checks every check's tier against each site's `expected.json`, plus a golden report. A socket
  guard fails the run if anything leaves the machine; the suite takes under a second.
- Tests that the CLI's embedded rubric (check ids, points, every tier's points and wording, bands,
  caps, bonus) equals `rubric/v1.1.json`.

### Changed
- **`watch diff` is paired, clustered and corrected for multiple comparisons.** It compares the
  questions both runs answered, with an exact paired test per row (McNemar when every question has
  one answer per run, otherwise an exact sign-flip test on each question's net change) and Holm's
  correction across the engine rows and the all-engines row. The verdict is `change` only when the
  adjusted p < 0.05, and `too few questions to tell` below 6 shared questions. 1.2.0 used an unpaired
  two-proportion test on answers that are not independent, which called changes too readily. New
  row fields: `p_paired`, `p_adjusted`, `n_pairs`, `n_questions`, `n_asks`, `before_paired`,
  `after_paired`, `delta_pp`, `delta_ci`. `before`, `after`, `delta` and `p_value` keep their 1.2.0
  unpaired meaning; no verdict uses them.
- **Intervals account for repeated asks.** Every rate block gains `cited_ci_clustered` (a bootstrap
  over questions, 2,000 seeded resamples, never narrower than Wilson) and `n_questions`; reports quote
  it whenever a question has more than one answer. `cited_ci` (Wilson) is unchanged.
- **Headline rates leave out questions that name the brand.** Questions are flagged at run time
  (`brand_in_query`, `competitor_in_query`) with the matcher used on answers; the headline covers the
  other questions and branded ones get their own line and n. An optional `branded` column in
  `queries.csv` (`auto`, `yes`, `no`) overrides the flag, `watch check` warns when more than 30% of the
  questions name the brand, and the CSV report gains a trailing `branded` column.
- **The Action scores the site once.** It used to fetch and score twice (once for JSON, once for
  the log), which doubled the time and could print two different scores. The job summary, the
  annotations and every file now come from one run.
- The Action annotates checks at zero: gates as errors, other checks as warnings (GitHub shows up
  to 10 of each; the rest are in the job summary).
- `geo-score watch --help` names the command you typed (`geo-score` after an install).
- `--compare` with three or more sites no longer says "Both scored".
- When a site redirects to another domain, the full report says so and the JSON carries `landed`
  (optional), the URL that was scored.

### Fixed
- **Scoring fixes the offline fixtures found.** Each moves a score only where the old reading
  contradicted the rubric:
  - `g.robots`: several `User-agent` lines share the rules that follow them (RFC 9309 2.1). The rules
    were attached to the last line only, so a group listing GPTBot, ClaudeBot and CCBot over
    `Disallow: /` read as blocking only CCBot. Down, to 0 and the gate cap, where grouped rules block
    retrieval crawlers; up (3 to 5) where a grouped `Allow` now counts as an explicit permission.
  - `p1.llms-txt`, `b.llms-full`, `b.ai-txt`, `p1.sitemap`: a single-page app that answers every path
    with its HTML shell no longer counts as serving these files; a sitemap must be XML with a
    `<urlset>` or `<sitemapindex>`. Down. A relative `Sitemap:` line in robots.txt is resolved against the
    origin (up where it now loads).
  - `p1.organization`: Organization and WebSite without name, url and logo score 3, as the rubric
    says, not 5 (down); a relative logo resolves against the page it sits on (up where it now loads);
    Organization subtypes (EducationalOrganization, NewsMediaOrganization, LocalBusiness and others) are
    read for logo and sameAs, which lifts `p1.organization` and `p3.sameas` for sites typed that way (up).
    `sameAs` values that are not http(s) URLs are no longer fetched.
  - `p1.page-type`: the top tier needs real field values; a bare `{"@type": "Product"}` scores 2. Down.
  - `p2.freshness`: dates flush against Chinese text and dates with English month names are read
    (up); the top tier requires `dateModified` not to be older than the page's own date (its
    datePublished, article time or the first date in its content) on at least three quarters of the
    pages that declare it (down where it is).
  - `p2.sourced-stats`: "resources" no longer counts as "source" (down); figures flush against Chinese
    text count as figures (either way).
  - `p2.named-author`: "Editor", the organisation's own name and "Powered by Hugo" in a footer are not
    personal bylines. Down.
  - Sampling: for a site under a path, a sibling folder (`/docs-legacy` for `/docs`) is no longer
    sampled, and the path's own sitemap is used when the origin has none.
- **SARIF uploads to GitHub code scanning.** Results were located at the scored URL, which code
  scanning rejects; each now points at its check's line in the JSON report (the Action writes one into
  the workspace when `sarif` is set) and names the site in its message.
- `watch diff` no longer says `within noise` when the question set is too small for the number of
  rows compared: before Holm's correction, a row with m × 2 / 2^n ≥ 0.05 (m rows, n questions;
  Tarone's screen) is `too few questions to tell` and leaves the family. The screen is conservative. An unknown MCP tool is a JSON-RPC error (-32602), as the protocol says.
- **A score could exceed 100.** Bonus points sit outside the denominator, so a site at or near full
  marks plus bonus read above 100 (the good fixture read 107), which also broke the report schema (`normalised` ≤ 100). The
  percentage is now capped at 100, and rubric rule 5 says so. No published score changes: the
  benchmark's highest is 98 and the hand audits' 87. The offline fixtures found it.
- `--json-out`, `--sarif` and `--junit` report a path that cannot be written as a clear error (exit
  2) instead of a traceback.
- A Latin brand name written directly next to Chinese, Japanese or Korean text ("用Lumo做视频") now
  counts as a mention; it never matched before. New runs can therefore show a higher `mentioned` rate
  on such answers than earlier runs.
- Run files saved by 1.2.0 still load; reports recompute their summary and the branded flag from the
  saved question text, and say so in a note.
- Documentation that still described the superseded gate rule: `rubric/README.md`, the Chinese
  calibration record, `SKILL.md` and the sample report said a gate short of full marks caps the score.
  The rule since v1.1 is that only a gate at **zero** caps it. The scores were always computed with the
  correct rule; `validate.py` now fails on any sentence that states the cap without the zero condition.
- The calibration record credited the structured-data adoption figures (BreadcrumbList 5.66%,
  Product 0.77%, FAQPage 0.34%) to the 2025 Web Almanac; they are from the 2024 edition. Only the
  llms.txt figure (2.13%) is from 2025.
- The Chinese calibration record was missing two facts the English one has (the 60 KB of
  server-rendered prose, Foglift's upper quartile); a new check compares the numbers in both.

### Security
- **The MCP server connects only to public addresses, on every hop.** 1.2.0 checked the URL an agent
  passed and nothing after it, so the audited site could point the scorer at loopback or intranet
  addresses through a redirect, its `sameAs` links, its logo or its declared sitemap, and the check
  let carrier-grade NAT through (100.64.0.0/10, where cloud metadata such as 100.100.100.200 lives).
  Under MCP every connection is now resolved and checked (`is_global`), each redirect hop is checked,
  and a direct connection goes to the checked address. The check also uses the exact host to be
  fetched rather than its brand form. The command-line tool still scores whatever its user names.
- More text is fenced or cleaned: the sitemap URL a site declares is quoted as site text without its
  query or fragment; sitemap entries with control or bidi characters are dropped; Unicode tag
  characters, soft hyphens, line separators and XML-illegal characters are removed; a truncated
  evidence line never leaves a `«site text: …»` fence open; server error lines are reduced to one
  clean line; the Action's job summary escapes evidence instead of rendering it as Markdown and HTML.
- The Action passes its inputs to the script as environment variables. Before this, `url` and the
  other inputs were pasted into the shell script, so a crafted value could run commands in the
  workflow. `sample` and `fail-under` are now checked to be whole numbers.
- **Site text in evidence is fenced as data.** Evidence that quotes the audited site (an answer
  passage, the brand name read from the page, a Wikidata description) now carries it inside
  `«site text: …»`, and control, zero-width and bidi characters are stripped from every evidence
  string. The report reaches AI agents through the MCP server, so a page could otherwise address the
  agent in the tool's own voice. Harvested links carrying such characters are dropped from the sample.
- Errors that wrap a lower-level exception (a malformed request header, an unreadable config) no
  longer chain it, so an uncaught traceback cannot print the original message, which for a header can
  contain the API key.
- `SECURITY.md` now has a supported-versions table and a threat model; `SKILL.md` tells the agent
  that fetched text is evidence, never instructions.

## [1.2.0] — 2026-09-27

### Added — levels 2 and 3: does AI actually cite you?

geo-watch 0.1.0 is merged into this repository. One tool now measures both halves of AI
visibility: whether engines **can** cite a site (the score, free) and whether they **do**
(with the user's own API keys). The citation half is never summed into the score, as the
rubric has always required.

- **Level 2, `--ask "question"`** (repeatable, up to 5): after the readiness report, asks
  ChatGPT, Perplexity, Gemini and Claude the question through their search-enabled APIs,
  one ask per engine that has a key, and fills the report's `citation` object. Without a key
  the block says not measured and the score is unchanged.
- **Level 3, `geo_score.py watch`**: a fixed question list asked every week; citation rate per
  engine with 95% Wilson intervals, share of voice against competitors, the third-party
  sources the engines cite, the searches they ran, a cost ledger with caps (`max_calls`
  is exact; `budget_usd` can be exceeded by at most one call per engine), and `diff` with a
  two-proportion test. Runs follow `schema/watch.v1.json`.
- **`geo_score.py mcp`**: a dependency-free stdio MCP server with `score_site` (level 1) and
  `ask`, `run`, `list_runs`, `report`, `diff` (levels 2 and 3).
- `schema/report.v2.json`: the reserved `citation` object gains optional `channel`,
  `answered`, `mentioned_count`, `per_engine`, `top_sources` and `cost_usd`. Additive; every
  1.1.x report still validates.
- `examples/ci/watch-weekly.yml`: the weekly schedule.

Levels 2 and 3 need `cli/geo_watch.py` from the same release next to `cli/geo_score.py`. The
one-line `curl | python3` install still runs level 1 on its own. Scores are unchanged from 1.1.2.

**For geo-watch 0.1.0 users:** rename `geo-watch.json` to `geo-score-watch.json` and run
`python3 cli/geo_score.py watch …` instead of `geo_watch.py …`. Runs now live in
`.geo-score/watch/runs/` with format `geo-score/watch.v1`; 0.1.0 run files are not read. The CSV
export renames `competitors_cited` to `other_domains_cited` and drops the always-empty
`wrong_fact` column.

## [1.1.2] — 2026-09-25

### Changed — scores move

A site scored 88 and then 95 on two consecutive runs from one machine, and another
scored 71, 40, 71 — both outside the ±5 this repository promises. Three causes, one
principle: **a network that cannot reach something is not evidence that it is missing.**

- **p3.sameas** counted every non-200 as a dead profile. Timeouts, resets and 451 (LinkedIn,
  X, YouTube, GitHub and Wikipedia are unreachable from mainland China) and bot walls
  (401 / 403 / 429 / 999 from Crunchbase, Zhihu, Facebook, LinkedIn) are now left out;
  only 404 / 410 count as gone. When no link can be checked, the check leaves the
  denominator instead of scoring 0. The same 12 profiles resolved 1 of 12 from a
  mainland network and 9 of 12 from overseas.
- **p3.knowledge-graph** scored 0 when *some* Wikidata / Wikipedia lookups timed out and
  the rest found nothing. Absence now needs every lookup to answer; a partial answer is
  unobservable. (All lookups failing was already unobservable.)
- **Sampling** fetched the sitemap once. One dropped request sent discovery to homepage
  links, a different eight pages were scored, and the middle run fell under the g.ssr
  gate (capped at 40). The homepage, robots.txt, sitemap, section indexes and sampled
  pages are now retried on timeouts, 429 and 5xx. Reports carry `sample_source`.

After the change, three runs each: jianruntech.com 95 / 95 / 95 (direct) and 93 / 93 / 95
(overseas); stripe.com 75 / 75 / 75 (direct) and 70 / 72 / 70 (overseas, concurrent).
**The published benchmark was measured on 2026-09-09 with the earlier logic and has not been
re-run.** A site whose sameAs or knowledge-graph lookups hit an unreachable host can score a
few points higher today than its leaderboard row. Reports now say `geo-score-cli/1.1.2`, so the
two can be told apart.

### Fixed
- **gzip bomb.** The 4 MB read cap applied to the compressed stream, and `gzip.decompress`
  has no output limit, so a few MB of crafted gzip could inflate to gigabytes and kill the
  process — on a GitHub Action runner, an out-of-memory crash instead of a score. Inflation
  is now capped at 16 MB; real pages never get near it. **No score changes.**

## [1.1.1] — 2026-09-09

The rubric became something you can run. Backfilled from the tag's history; this release shipped
without a changelog section.

### Added
- **The CLI** (`cli/geo_score.py`): standard library only, one command, no install; scores the 17
  checks a static fetch can observe and leaves the rest out of the denominator. Every check says what
  the next tier needs and what it is worth, and the report lists the largest gaps.
- **The GitHub Action** (`uses: jianruntech/geo-score@v1`) with `--fail-under` for CI, and the moving
  `v1` tag.
- `--compare URL` to score a competitor side by side; `--badge` for an embeddable SVG; `--share` for a
  one-line summary.
- **The public benchmark**: 229 of 266 well-known sites scored with the same rubric, with the gate
  failures split into deliberate and accidental, and a generated leaderboard page in English and
  Chinese with share cards.

### Fixed
- Sites that live under a path (a project page, a docs subtree) are sampled inside that path.
- Author references through `@graph` `@id` are resolved; pages with an author were read as having none.
- Non-ASCII domains crashed before the first request.
- 22 broken links in the examples index; CI now guards internal links.

## [1.1.0] — 2026-09-08

Rubric **v1.1**. v1.0 was tagged a few hours earlier but never announced: running it
against five real sites before release labelled anthropic.com *Critical* — a site
returning 200 to all ten retrieval crawlers, byte-identical to a browser, with 60 KB of
server-rendered prose. That is a failed calibration check, so v1.1 shipped instead.
Full reasoning: [rubric/calibration-v1.1.md](rubric/calibration-v1.1.md).

**Scores from v1.0 and v1.1 are not comparable.** v1.0 and its five audits stay published,
unaltered — they are the evidence that found the problem.

### Changed
- **Two scores, never one.** *Readiness* (what the site owner can change, observable from
  outside) is what the rubric scores. *Citation performance* is reported separately and
  never folded in. Merging them is what produced the *Critical* verdict above.
- **Tiers replace pass/fail.** All 21 scored checks now carry 2–4 tiers, and every tier
  states a count out of the 8 sampled pages rather than "most" or "a few".
- **Substance over format.** Headings match question intent whether or not they carry a
  question mark — tasks ("Accept a payment") and explanations ("How Connect works") count.
  A freshness signal is a visible date *or* a schema date. Answer passages widened to
  25–120 words (50–200 characters for Chinese) and no longer have to be the first paragraph.
- **Unobservable checks left the base.** Search Console and Bing verification state and
  multi-engine query tests are gone from the 100 — no external auditor can see them, and
  scoring them zero silently penalised every site. They are reported as an unscored block.
- **Emerging conventions moved to bonus.** `ai.txt`, `speakable`, GEO `<link>` tags and
  `llms-full.txt` were 9 points inside the denominator; they are now bonus checks worth up
  to +6 outside it.
- **Gates.** `g.robots`, `g.reachable` and `g.ssr` score normally and cap the normalised
  percentage at 40 — but only when one of them scores **zero**.
- **Five bands with stage names.** "Critical" is gone; CI now rejects verdict-style band
  names. Thresholds are taken from a published AEO ladder its own distribution backs.
- **Rubric is bilingual.** [`rubric/v1.1.md`](rubric/v1.1.md) (English) and
  [`rubric/v1.1.zh-CN.md`](rubric/v1.1.zh-CN.md), with both languages in the JSON.

### Added
- [`rubric/calibration-v1.1.md`](rubric/calibration-v1.1.md) — how the recalibration was
  reasoned, against four external benchmarks
- [`schema/report.v2.json`](schema/report.v2.json) — v1.1 changed the output shape
  (`score` became `readiness`, `gate_capped` and `tier_reason` are new, the `failed` state
  is gone). `report.v1.json` stays for v1.0 reports.
- [`examples/audits/v1.1/`](examples/audits/v1.1/) — the five sites re-audited under v1.1
- CI now validates published audits against the schema and recomputes every score,
  checks that gate-cap figures agree across both languages and the JSON, rejects
  implementation fields (`fix_zh`, `effort_days`, `owner`) in the public rubric, and
  rejects stale pillar names and retired check ids anywhere in the repo

### Fixed
- A first draft of v1.1 capped any site whose gate checks fell short of full marks. That
  showed stripe.com (77/100) and nextjs.org (85/98) as **40%, Early** — v1.0's mistake in a
  new place, treating *not ideal* as *not working*. Gates now cap only at tier zero.
- The eight ambiguities in [`rubric/open-questions.md`](rubric/open-questions.md) all have
  decisions, recorded inline.

## [1.0.0] — 2026-09-08

Tagged but never announced; superseded within hours by 1.1.0 after it failed its own
calibration check. Kept published so the correction stays auditable.
The repository was pushed a few hours earlier without a tag;
the rubric was corrected before this tag, so v1.0 as released here is the only v1.0.
Corrections made in that window are listed under *Fixed before first tag*.

### Added
- Rubric v1.0: **29 checks** across 5 pillars, 100 nominal points, with pass conditions,
  an explicit Credit type per check, three-state scoring, and score bands
- `SKILL.md` — Claude Code skill that runs the rubric
- `reference/ai-crawlers.md` — the AI user-agent list the crawler checks run against
- `reference/platform-source-selection.md` — how each engine selects sources
- `examples/sample-report.md`

### Fixed before first tag
- **Crawler classification was wrong.** `Google-Extended` and `Applebot-Extended` were
  listed as retrieval crawlers. They are opt-out tokens — they send no requests, and
  blocking them costs no citations. The real retrieval crawler `Applebot` was missing
  entirely. Net effect was inverted: blocking a harmless token lost points, blocking a
  real crawler did not.
- **Anthropic's retrieval agents were missing.** `Claude-SearchBot` and `Claude-User`
  were absent; only the training crawler `ClaudeBot` was listed. A site blocking both
  retrieval agents could still score full marks.
- **Added a reachability check.** `robots.txt` states an intention; the edge decides.
  A WAF returning 403 to `OAI-SearchBot` while `robots.txt` says `Allow` was previously
  a perfect score.
- **Pillar 5 scored procedure, not outcome.** "A query test was performed" is now
  "cited in N of 3 engines" — being cited nowhere scores zero.
- **No rule for inapplicable or unobservable checks.** A brand site with no articles lost
  points for having no `Article` schema. Scores now report `score / observable max` and
  band on the normalised percentage.
- **Partial-credit rule contradicted the sample report.** Every check now carries an
  explicit `prop.` or `all/none` Credit value, with `floor()` rounding stated.
- **The sample report did not add up** — a pillar subtotal was 2 points above its line
  items. CI now validates the arithmetic of every report block in the repo.

### Scope note
Remediation (fix templates, content rewriting, per-engine tactics) is deliberately
out of scope. See [Scope](README.md#scope--what-this-does-not-do).

[Unreleased]: https://github.com/jianruntech/geo-score/compare/v1.7.1...HEAD
[1.7.1]: https://github.com/jianruntech/geo-score/compare/v1.7.0...v1.7.1
[1.7.0]: https://github.com/jianruntech/geo-score/compare/v1.6.0...v1.7.0
[1.6.0]: https://github.com/jianruntech/geo-score/compare/v1.5.0...v1.6.0
[1.5.0]: https://github.com/jianruntech/geo-score/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/jianruntech/geo-score/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/jianruntech/geo-score/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/jianruntech/geo-score/compare/v1.1.2...v1.2.0
[1.1.2]: https://github.com/jianruntech/geo-score/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/jianruntech/geo-score/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/jianruntech/geo-score/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/jianruntech/geo-score/releases/tag/v1.0.0
