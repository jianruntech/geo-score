# geo-score CLI

Score a site against the [AIV rubric v1.1](../rubric/v1.1.md). Python 3.8+, standard
library only, nothing to install.

```bash
curl -sL https://raw.githubusercontent.com/jianruntech/geo-score/main/cli/geo_score.py \
  | python3 - yoursite.com
```

## Options

| Flag | What it does |
|---|---|
| `--explain`, `-e` | Print the evidence behind every check, not just the score |
| `--json` | Machine-readable output conforming to [`schema/report.v2.json`](../schema/report.v2.json) |
| `--sample N` | How many pages to sample (default 8, which is what the rubric specifies) |
| `--fail-under N` | Exit 1 when the score is below N — for CI |
| `--quiet`, `-q` | Suppress progress lines on stderr |

`NO_COLOR=1` turns off colour, as does piping to a file.

## What it measures, and what it does not

The CLI scores the **17 checks a static fetch can honestly observe**. It fetches your
sample pages once with a browser user-agent, then re-fetches three of them with each of
the ten retrieval user-agents to see whether any of them is served something different.
It parses JSON-LD, `robots.txt`, `llms.txt` and your sitemap, and it queries the public
Wikidata and Wikipedia APIs to check whether your brand has a knowledge-graph entity.

Four checks are **left out of the denominator** rather than guessed:

| Check | Why the CLI cannot see it |
|---|---|
| `p3.listings` | Needs to know your industry and search its directories |
| `p3.mentions` | Needs off-site search for independent coverage |
| `p4.question-coverage` | Needs the ten questions people actually ask in your market |
| `p4.cn-engines` | Skipped unless the site addresses the Chinese market |

Because those four are excluded, the CLI reads **lower than a full audit on an
established brand** — typically by 5 to 15 points, since listings and mentions are
usually the checks such a brand already passes. The
[Claude Code skill](../SKILL.md) scores all 21.

## Heuristics, stated plainly

Some checks are judgements the rubric describes in prose, and the CLI approximates them:

- **Answer passages** — takes the first six paragraphs of the main content and looks for
  one of 25–120 words (50–200 characters on a Chinese-language site) that ends in
  sentence punctuation. A human reader judges whether it truly stands alone.
- **Question intent** — pattern-matches headings for questions, task verbs and
  explanatory forms, excluding navigation labels and brand strings.
- **Sourced statistics** — counts figures per page against citation elements, source
  phrases and outbound references near them.
- **Named authorship** — reads the `author` field from JSON-LD, then falls back to
  `rel="author"` and byline patterns, and rejects team and brand names.

Where the CLI and a careful human disagree, the human is right and the rubric is the
arbiter. Run `--explain` to see exactly what the CLI observed, and
[open an issue](https://github.com/jianruntech/geo-score/issues) if a heuristic is wrong
on your site — those reports are how these get better.

## As a GitHub Action

```yaml
- uses: jianruntech/geo-score@v1
  with:
    url: https://example.com
    fail-under: 40
    json-out: geo-score.json
```

Outputs `score`, `band` and `report`, and writes a scored table to the job summary.
