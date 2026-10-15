# Can ChatGPT read your website? A check in two halves

The first half is by hand, with a browser and a terminal, and needs nothing from us. The second half runs the same
checks, and a few more, with geo-score. Being readable is a precondition for being cited, not a promise of it.
中文版：[chatgpt-access.zh-CN.md](chatgpt-access.zh-CN.md)

## Which crawlers decide it

ChatGPT reaches a site through two crawlers ([reference/ai-crawlers.md](../reference/ai-crawlers.md)):

| User-agent | What it does |
|---|---|
| `OAI-SearchBot` | Builds the index behind ChatGPT search. OpenAI says a page has to be open to it to be summarised, cited and linked there ([Publishers and developers FAQ](https://help.openai.com/en/articles/12627856-publishers-and-developers-faq)) |
| `ChatGPT-User` | Fetches a page live when a user's prompt needs it |

`GPTBot` is OpenAI's training crawler. OpenAI documents each setting as independent, so a site can refuse `GPTBot`
and still appear in ChatGPT search. This page is about the two above.

## Part 1 · By hand

**1. Read robots.txt.** Open `https://your-site/robots.txt` in a browser. Look for a group that names `OAI-SearchBot`
or `ChatGPT-User` (`User-agent:` lines). If one does, only that group applies to it; if none does, the `User-agent: *`
group applies. A `Disallow: /` in the group that applies shuts the crawler out of the whole site. A `Disallow` on a
path closes only that path, so check the paths you care about.

**2. Request a page as each crawler, and as a browser.** The user-agent strings below are the ones the vendor
documents, and the ones geo-score sends.

```bash
URL=https://www.example.com/
SEARCH='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36; compatible; OAI-SearchBot/1.4; +https://openai.com/searchbot'
USER='Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ChatGPT-User/1.0; +https://openai.com/bot'
BROWSER='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36'
for ua in "$SEARCH" "$USER" "$BROWSER"; do
  curl -s -L -o /dev/null -w '%{http_code} %{size_download} bytes\n' -A "$ua" "$URL"
done
```

Three lines of `200` with similar sizes is what you want. A `403`, a `429` or a much smaller answer for the crawlers
than for the browser means something between them and your pages treats them differently.

These requests come from your own address, not from the vendor's published addresses. A firewall that verifies
crawlers by IP range may refuse your request and still serve the real crawler, or the reverse; read a refusal as
"this server refuses unverified crawler user-agents", not as proof.

**3. Check that the text is in the HTML.** Retrieval crawlers generally read the HTML the server sends, without
running its JavaScript. Pick a sentence you can see on the page in a browser, and look for it in what the crawler
gets:

```bash
curl -s -L -A "$SEARCH" "$URL" | grep -c 'a sentence you can see on the page'
```

`0` means the sentence only appears after JavaScript runs, so a crawler gets an empty shell.

**4. Look at the layer in front of the site.** In your CDN's or host's bot and firewall settings, check that no rule
blocks or challenges `OAI-SearchBot` or `ChatGPT-User`, and look in its logs for their requests and the status codes
they got. A setting that blocks "AI bots" as a group usually covers them.

**5. Look for the result.** Your server logs show whether `OAI-SearchBot` has been fetching pages. Your analytics
show visits from ChatGPT search: OpenAI says the links it sends carry `utm_source=chatgpt.com`. Asking ChatGPT about
one of your pages shows one answer on one day; answers vary from run to run, so one answer is an anecdote.

## Part 2 · With geo-score

Install it as [Ways to run it](../README.md#ways-to-run-it) says, then:

```bash
geo-score www.example.com --explain
```

The three gates answer steps 1 to 3 for all ten retrieval crawlers at once, the two above included:

| Check | What it reads |
|---|---|
| `g.robots` | robots.txt, with each crawler's group chosen as RFC 9309 says |
| `g.reachable` | The sampled pages requested as each crawler and as a browser, compared |
| `g.ssr` | Whether the main content is in the server-rendered HTML |

Under **Outside the score** the report also holds each sampled page against robots.txt, path by path
([cli/README.md](../cli/README.md#outside-the-score)). `--explain` prints the evidence behind every reading, and
[troubleshooting](troubleshooting.md) explains each one. In CI, `--fail-on-gate` fails the build when a gate reaches
zero.

Whether ChatGPT then cites you is a different question. Level 2 asks it through the API with your own key:

```bash
OPENAI_API_KEY=… geo-score www.example.com --ask "a question your buyers ask"
```

That is the API channel, not the ChatGPT app, and one answer is still an anecdote. Level 3 (`watch`) asks a fixed set
of questions every week and reports rates with their intervals; see
[the watch methodology](watch-methodology.md).
