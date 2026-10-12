# Round 0: categories and sampling frames

Round 0 of the [preregistered validation plan](../../PREREGISTRATION.md): English questions for a buyer in the
US. This file records what was fixed at each step, in the order the plan sets (section 4): first the categories,
each with its public list at a recorded revision and its candidate sites; then the questions; then the sampling
run. Nothing here has been scored.

## Step 1: categories and sampling frames

[categories.json](categories.json) holds 20 categories. [build_frames.py](build_frames.py) derives it, and
`build_frames.py --cache DIR --check` rebuilds it and compares.

For each category:

- **A one-sentence definition**, written for a buyer in the US.
- **Its public list:** an English Wikipedia list or comparison article, read at the revision id recorded (`frame.revid`;
  `frame.url` opens that revision). The rule that says which rows name the vendors (a table column, or each bullet's
  first link) is recorded with it (`frame.rule`), and so is every row it reads (`frame.rows`).
- **Each listed vendor's own website:** the official website (P856) of the Wikidata item the row links to, with that
  item's revision (`wd_lastrevid`). When the item has several, the English or multilingual one comes first, then an
  unqualified one, then Wikidata's preferred rank, then a generic top-level domain before a country code. A row is
  out, with the reason recorded, when its link has no article or no Wikidata item, when Wikidata records the vendor as
  dissolved (P576) or the product as discontinued (P2669), when no website is recorded, or when the website is a page
  on another site (a code host, `sites.google.com`, a project page). Two values were replaced by hand, each with its
  reason in the row (`website_override`): Rosetta Stone (Wikidata lists only its French site) and OC&C Strategy
  Consultants (only its French office's site).
- **One candidate per owner:** a candidate is the part of a host its owner holds, as `watch` reads it
  (`site_domain` in [cli/geo_watch.py](../../../cli/geo_watch.py): `amazon.com` for `aws.amazon.com`), with
  `napoli.it` added as a public suffix it does not know. Rows that resolve to the same owner are one candidate,
  scored at the first row's website host (`site`), and every domain listed for it counts as its own (`domains`).
- **The benchmark/sites.json sites that sell in it** (`sites_json_in`), matched by hand from the site lists of
  [sites.json](../../sites.json) (its `url` and `sector` only): a site enters when it sells the category's product to
  buyers in the US. A site that is a listed vendor's own site under another domain is merged with that vendor and
  scored at the sites.json site (runway.com for Runway's runwayml.com, bigcommerce.com for Commerce.com, remix.run for
  React Router, cursor.com for Anysphere, ebay.com for ebayinc.com, deepmind.google for Google's video models). Sites
  considered and left out are listed with the reason (`sites_json_out`), most often a China-market site or a
  different kind of product.
- **The size rule** (plan section 5.1): fewer than 6 candidates drops the category before sampling; above 15, 15 are
  drawn with `random.Random(seed).sample` over the candidate ids in sorted order, the seed being the first 16 hex digits
  of SHA-256 of `geo-score prereg round0 frame|<category id>` (`draw`). No category fell below 6.

| Category | Definition | Public list | Candidates | In the frame |
|---|---|---|:-:|:-:|
| `large-language-models` | Large language models that people and businesses in the US use through an app or an API, and the companies that develop them. | [List of large language models](https://en.wikipedia.org/w/index.php?oldid=1378988796) rev. 1378988796 (2026-10-07) | 49 | 15 |
| `ai-video-generators` | AI models and apps that generate video from text or images, offered to creators and businesses in the US. | [Text-to-video model](https://en.wikipedia.org/w/index.php?oldid=1378271382) rev. 1378271382 (2026-10-03) | 12 | 12 |
| `vector-databases` | Databases that store and search vector embeddings, offered to developers and businesses in the US. | [Vector database](https://en.wikipedia.org/w/index.php?oldid=1374243120) rev. 1374243120 (2026-09-10) | 25 | 15 |
| `cloud-infrastructure` | Public cloud infrastructure (virtual machines, storage and networking) that businesses in the US rent. | [Cloud-computing comparison](https://en.wikipedia.org/w/index.php?oldid=1365802661) rev. 1365802661 (2026-07-24) | 13 | 13 |
| `javascript-web-frameworks` | JavaScript and TypeScript frameworks for building websites and web applications, which developers in the US choose for a project. | [Comparison of JavaScript-based web frameworks](https://en.wikipedia.org/w/index.php?oldid=1374992173) rev. 1374992173 (2026-09-15) | 31 | 15 |
| `ecommerce-platforms` | Software and hosted platforms that merchants in the US use to run an online store. | [Comparison of shopping cart software](https://en.wikipedia.org/w/index.php?oldid=1378625961) rev. 1378625961 (2026-10-05) | 22 | 15 |
| `crm-software` | Customer relationship management software that companies in the US use to manage contacts, deals and customer communication. | [Comparison of CRM systems](https://en.wikipedia.org/w/index.php?oldid=1365891310) rev. 1365891310 (2026-07-25) | 27 | 15 |
| `web-analytics` | Software that measures visits to a website, used by site owners and marketers in the US. | [List of web analytics software](https://en.wikipedia.org/w/index.php?oldid=1361857790) rev. 1361857790 (2026-06-30) | 27 | 15 |
| `online-payment-providers` | Services that let businesses in the US accept payments online. | [List of online payment service providers](https://en.wikipedia.org/w/index.php?oldid=1367307700) rev. 1367307700 (2026-08-02) | 27 | 15 |
| `buy-now-pay-later` | Services that let shoppers in the US split a purchase into installments at checkout. | [Buy now, pay later](https://en.wikipedia.org/w/index.php?oldid=1376383699) rev. 1376383699 (2026-09-23) | 6 | 6 |
| `online-course-platforms` | Websites that offer online courses to learners in the US. | [List of MOOC providers](https://en.wikipedia.org/w/index.php?oldid=1363722387) rev. 1363722387 (2026-07-12) | 27 | 15 |
| `language-learning` | Apps, courses and self-study programs that learners in the US use to learn a foreign language. | [List of language self-study programs](https://en.wikipedia.org/w/index.php?oldid=1377422426) rev. 1377422426 (2026-09-29) | 36 | 15 |
| `container-shipping-lines` | Ocean carriers that move shipping containers for importers and exporters in the US. | [List of largest container shipping companies](https://en.wikipedia.org/w/index.php?oldid=1354275764) rev. 1354275764 (2026-05-15) | 17 | 15 |
| `management-consulting` | Firms that companies in the US hire for management consulting. | [List of management consulting firms](https://en.wikipedia.org/w/index.php?oldid=1379170443) rev. 1379170443 (2026-10-08) | 60 | 15 |
| `project-management-software` | Software that teams in the US use to plan, assign and track project work. | [Comparison of project management software](https://en.wikipedia.org/w/index.php?oldid=1364585119) rev. 1364585119 (2026-07-17) | 92 | 15 |
| `note-taking-apps` | Apps that people in the US use to write, organize and search their notes. | [Comparison of note-taking software](https://en.wikipedia.org/w/index.php?oldid=1367074056) rev. 1367074056 (2026-07-31) | 26 | 15 |
| `3d-printers` | 3D printers sold to hobbyists and businesses in the US. | [List of 3D printer manufacturers](https://en.wikipedia.org/w/index.php?oldid=1367768236) rev. 1367768236 (2026-08-05) | 33 | 15 |
| `us-airlines` | Airlines that fly passengers within and from the US. | [List of largest airlines in North America](https://en.wikipedia.org/w/index.php?oldid=1367374301) rev. 1367374301 (2026-08-02) | 10 | 10 |
| `accounting-software` | Accounting software that small and midsize businesses in the US use for bookkeeping, invoicing and financial reports. | [Comparison of accounting software](https://en.wikipedia.org/w/index.php?oldid=1374376033) rev. 1374376033 (2026-09-11) | 41 | 15 |
| `online-marketplaces` | Online marketplaces where shoppers in the US buy consumer goods from many sellers. | [List of online marketplaces](https://en.wikipedia.org/w/index.php?oldid=1373521726) rev. 1373521726 (2026-09-06) | 15 | 15 |

Three lists carry a column that says where a vendor operates or what it sells, and the rule reads it: online payment
providers keep the rows whose Location names the United States or North America or says global or worldwide; US
airlines keep the rows whose Country is the United States; online marketplaces keep the rows whose Industry names
products, fashion or clothing. No other row was screened for the US: a listed vendor that does not sell to buyers in
the US stays a candidate.

**Sectors.** A category's `sectors` are those of its benchmark/sites.json sites, so the 20 categories reach 14 of the
benchmark's 20 sectors (accounting software has no benchmark site). None was found for six: Healthcare (no English
Wikipedia list or comparison of telehealth or health services; "Online doctor" and "Telehealth" list no providers),
Media / Publishing (no list of publications a buyer would ask to have recommended), Manufacturing / Industrial
("Industrial robot" lists no makers; "List of television manufacturers" is mostly defunct brands and conglomerates that
make no televisions), Cross-border services (its sites sell to Chinese exporters, not to buyers in the US), and China
/ cloud and China / no-code, whose sites are China-market sites (the plan reserves a Chinese round). Two more
categories were dropped before any question was written: hotel groups (the table mixes groups that operate only in
China with no column to tell them apart) and online travel agencies (no list).

**What was read.** Only `url` and `sector` of benchmark/sites.json. `benchmark/results.json`, `benchmark/results.csv`
and `benchmark/raw/` were not opened. [benchmark/README.md](../../README.md) was read for its sector list and the
thin-sample rule; it is generated from results.json, and a text search of it for "thin" printed about 60 rows of its
leaderboard table, with those sites' v1.1 scores, before the categories were chosen. No score was used for anything
here. As the plan says (section 4), some candidates' v1.1 scores were public before the questions were written.
