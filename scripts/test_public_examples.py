#!/usr/bin/env python3
"""Check the two public examples in guide/public-examples.md (+ zh) with the CLI's own readers, offline.

    python3 scripts/test_public_examples.py

Measurement is public and remediation is private (AGENTS.md); these two examples are the one exception, because
they are public knowledge. They are held to that here:
- each page carries exactly one robots.txt block and one JSON block, and the English and Chinese pages carry the
  same two blocks byte for byte;
- the robots.txt reaches g.robots' top tier as robots_tier() reads it, names every crawler in RETRIEVAL_UAS in a
  group of its own, and repeats the * group's Disallow lines there (RFC 9309: a named group replaces *);
- the JSON is an Organization and a WebSite and nothing else, and jsonld() finds an Organization with name, url,
  logo and sameAs beside a WebSite: the fields p1.organization's top tier reads.
guide/chatgpt-access.md (+ zh) tells readers to request a page as OpenAI's two retrieval crawlers and as a browser;
the user-agent strings it gives must be the ones the CLI sends, so the two halves of that page agree.
"""
import importlib.util, io, json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PAGES = ("guide/public-examples.md", "guide/public-examples.zh-CN.md")

fails = []


def ok(cond, msg):
    print(("  ok    " if cond else "  FAIL  ") + msg)
    if not cond:
        fails.append(msg)


def rd(p):
    return io.open(os.path.join(ROOT, p), encoding="utf-8").read()


def load_cli():
    spec = importlib.util.spec_from_file_location("geo_score_examples", os.path.join(ROOT, "cli", "geo_score.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def blocks(text):
    """{fence language: [block text]} for every fenced block on the page."""
    out = {}
    for lang, body in re.findall(r"^```(\w*)\n(.*?)^```$", text, re.M | re.S):
        out.setdefault(lang, []).append(body)
    return out


def check_pages():
    print("pages: one robots.txt block and one JSON block each, the same in both languages")
    found = {}
    for p in PAGES:
        b = blocks(rd(p))
        ok(sorted(b) == ["json", "text"] and len(b["json"]) == 1 and len(b["text"]) == 1,
           "%s holds exactly one ```text and one ```json block (found %s)" % (p, {k: len(v) for k, v in b.items()}))
        found[p] = b
    en, zh = found[PAGES[0]], found[PAGES[1]]
    ok(en == zh, "the English and Chinese pages carry the same blocks")
    return en


def check_robots(gs, txt):
    print("\nrobots.txt: g.robots' top tier, every retrieval crawler named, * rules repeated")
    tier, ev = gs.robots_tier(txt, len(txt.encode("utf-8")))
    ok(tier == 5, "robots_tier() reads tier %s of 5: %s" % (tier, ev))
    groups = gs.robots_groups(txt)
    names = [name for name, _ in gs.RETRIEVAL_UAS]
    missing = [n for n in names if n.lower() not in groups]
    ok(not missing, "every crawler in RETRIEVAL_UAS has a group of its own (missing: %s)" % missing)
    star = sorted(v for k, v in groups.get("*", []) if k == "disallow")
    lost = sorted({n for n in names if n.lower() in groups
                   for v in star if ("disallow", v) not in groups[n.lower()]})
    ok(not lost, "the * group's Disallow lines %s are repeated for every named crawler (not for: %s)" % (star, lost))
    ok(not any(t.lower() in groups for t in gs.NOT_SCORED_TOKENS),
       "no training crawler or opt-out token is named: that is the site owner's own decision")


def check_jsonld(gs, raw):
    print("\nJSON-LD: an Organization and a WebSite, with what p1.organization's top tier reads")
    obj = json.loads(raw)
    graph = obj.get("@graph", [obj])
    ok({o.get("@type") for o in graph} == {"Organization", "WebSite"},
       "the example declares an Organization and a WebSite and nothing else")
    page = '<html><head><script type="application/ld+json">%s</script></head><body></body></html>' % raw
    objs = gs.jsonld(page)
    ok({"Organization", "WebSite"} <= gs.types_of(objs), "jsonld() reads both types from the page")
    org = next((o for o in objs if o.get("@type") == "Organization"), {})
    ok(all(org.get(k) for k in ("name", "url", "logo")), "the Organization carries name, url and logo")
    same = org.get("sameAs")
    ok(isinstance(same, list) and same and all(re.match(r"https://", s) for s in same),
       "sameAs is a list of https URLs")
    site = next((o for o in objs if o.get("@type") == "WebSite"), {})
    ok(isinstance(site.get("publisher"), dict) and site["publisher"].get("name") == org.get("name"),
       "the WebSite's publisher resolves to the Organization through its @id")
    urls = [u for u in [org.get("url"), org.get("logo")] + list(same or []) if isinstance(u, str)]
    hosts = {(re.match(r"https?://([^/]+)", u) or re.match(r"()", "")).group(1) for u in urls}
    ok(all(h == "example.com" or h.endswith((".example.com", ".example.org")) or h == "example.org" for h in hosts),
       "every URL in it is on a reserved example domain (%s)" % sorted(hosts))


def check_guide_user_agents(gs):
    print("\nguide/chatgpt-access.md: the user-agent strings are the CLI's")
    want = {"SEARCH": dict(gs.RETRIEVAL_UAS)["OAI-SearchBot"], "USER": dict(gs.RETRIEVAL_UAS)["ChatGPT-User"],
            "BROWSER": gs.UA_BROWSER}
    for p in ("guide/chatgpt-access.md", "guide/chatgpt-access.zh-CN.md"):
        got = dict(re.findall(r"^(SEARCH|USER|BROWSER)='([^']*)'$", rd(p), re.M))
        ok(got == want, "%s sets SEARCH, USER and BROWSER to the CLI's strings%s"
           % (p, "" if got == want else " (differ: %s)" % sorted(k for k in want if got.get(k) != want[k])))


def main():
    gs = load_cli()
    check_guide_user_agents(gs)
    b = check_pages()
    if "text" in b and "json" in b:
        check_robots(gs, b["text"][0])
        check_jsonld(gs, b["json"][0])
    if fails:
        print("\nFAIL: %d public-example check(s)" % len(fails))
        sys.exit(1)
    print("\nOK: the two public examples read as guide/public-examples.md says, and the guide's user-agents are the CLI's")


if __name__ == "__main__":
    main()
