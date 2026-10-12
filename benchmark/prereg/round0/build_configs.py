#!/usr/bin/env python3
"""Round 0, step 2: each candidate's watch entry, the frozen questions, and one watch config per category.

Reads categories.json (step 1) and writes, in this order of decisions:

1. each frame candidate's `watch` entry (name, aliases, domains, URL prefixes), written before the questions
   (PREREGISTRATION.md section 5.2), and whether its name is an ordinary English word (section 5.6: no N for it);
2. the 10 questions of each category (section 4), in watch/<category>/queries.csv;
3. the candidates any frozen question names by watch's own matcher (`Entity.named_in`, the matcher of
   `brand_in_query`), who are out (section 5.2);
4. watch/<category>/geo-score-watch.json with the remaining candidates: the first by name as `brand`, the rest as
   `competitors` (roles do not change the counts, section 5.6).

candidates.json records all of it. Ordinary words are found with two public word lists, recorded by SHA-256:
Webster's Second International (`web2`, as shipped in /usr/share/dict on BSD and macOS) and the 333,333 most frequent
words of the Google Web Trillion Word Corpus as Peter Norvig published them (`count_1w.txt`).

    python3 benchmark/prereg/round0/build_configs.py --web2 /usr/share/dict/web2 --count1w count_1w.txt
    python3 benchmark/prereg/round0/build_configs.py --web2 ... --count1w ... --check

Standard library only. No API is called and no site is fetched.
"""
import argparse, csv, hashlib, importlib.util, io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
WATCH_DIR = os.path.join(HERE, "watch")
OUT = os.path.join(HERE, "candidates.json")
TOP_N = 30000          # a word counts as ordinary within the 30,000 most frequent words of count_1w
DAYS_MONTHS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "january", "february",
               "march", "april", "may", "june", "july", "august", "september", "october", "november", "december")

# The engines of round 0 (amendment of 2026-10-12): an OpenAI model through an OpenAI-compatible endpoint whose
# address and key are given at run time (collect.sh puts OPENAI_COMPAT_BASE_URL in place of the placeholder, and the
# model id is OPENAI_COMPAT_MODEL, recorded in the frozen sample), and Gemini 2.5 Flash through generateContent with
# Google Search. Both search the web on every call.
OPENAI_PLACEHOLDER = "https://openai-compatible.invalid/v1/responses"
ENGINES = [
    {"id": "openai", "provider": "openai", "model": "gpt-5.6-luna", "base_url": OPENAI_PLACEHOLDER,
     "key_env": "OPENAI_COMPAT_API_KEY", "timeout": 300},
    {"id": "gemini", "provider": "gemini", "model": "gemini-2.5-flash", "api": "generate_content",
     "key_env": "GEMINI_API_KEY"},
]
RUNS, COUNTRY = 8, "US"

# Names, written before the questions: the brand as answers usually write it, and other names only where they are
# not ordinary English words (section 5.2). A candidate is its owner's site (categories.json), so a conglomerate's
# entry carries the company's name with the listed product as an alias.
NAMES = {
    "large-language-models": {
        "01.ai": ("01.AI", []), "alibabacloud.com": ("Alibaba Cloud", ["Qwen", "Aliyun"]),
        "bloomberg.com": ("Bloomberg", ["BloombergGPT"]), "huawei.com": ("Huawei", ["Pangu"]),
        "meituan.com": ("Meituan", ["LongCat"]), "meta.com": ("Meta", ["Meta AI", "Meta Platforms"]),
        "mistral.ai": ("Mistral AI", ["Mistral"]), "navercorp.com": ("Naver", ["HyperCLOVA X", "HyperCLOVA"]),
        "openai.com": ("OpenAI", ["ChatGPT"]), "perplexity.ai": ("Perplexity", []),
        "sarvam.ai": ("Sarvam AI", ["Sarvam"]), "stepfun.com": ("StepFun", []),
        "thinkingmachines.ai": ("Thinking Machines Lab", []),
        "tii.ae": ("Technology Innovation Institute", ["TII", "Falcon LLM"]), "x.ai": ("xAI", ["Grok"])},
    "ai-video-generators": {
        "alibabagroup.com": ("Alibaba", ["Alibaba Group"]), "bytedance.com": ("ByteDance", ["Seedance"]),
        "deepmind.google": ("Google", ["Google DeepMind", "Veo"]), "kuaishou.com": ("Kuaishou", ["Kling"]),
        "lightricks.com": ("Lightricks", ["LTX Studio", "LTX Video"]),
        "lumalabs.ai": ("Luma AI", ["Luma", "Luma Labs", "Dream Machine"]), "midjourney.com": ("Midjourney", []),
        "openai.com": ("OpenAI", ["Sora"]), "pika.art": ("Pika", ["Pika Labs"]),
        "runway.com": ("Runway", ["RunwayML", "Runway ML"]), "synthesia.io": ("Synthesia", []),
        "utopaistudios.com": ("Utopai Studios", ["Utopai"])},
    "vector-databases": {
        "aerospike.com": ("Aerospike", []), "allegrograph.com": ("AllegroGraph", []),
        "clickhouse.com": ("ClickHouse", []), "couchbase.com": ("Couchbase", []), "crate.io": ("CrateDB", []),
        "datastax.com": ("DataStax", ["Astra DB"]), "llamaindex.ai": ("LlamaIndex", []),
        "microsoft.com": ("Microsoft", ["Azure Cosmos DB", "Cosmos DB"]), "neo4j.com": ("Neo4j", []),
        "opensearch.org": ("OpenSearch", []), "oracle.com": ("Oracle", ["Oracle Database"]),
        "pingcap.com": ("TiDB", ["PingCAP"]), "scylladb.com": ("ScyllaDB", []), "supabase.com": ("Supabase", []),
        "upstash.com": ("Upstash", [])},
    "cloud-infrastructure": {
        "alibabacloud.com": ("Alibaba Cloud", ["Aliyun"]),
        "amazon.com": ("Amazon Web Services", ["AWS", "Amazon EC2", "Amazon"]),
        "atlantic.net": ("Atlantic.Net", []), "digitalocean.com": ("DigitalOcean", []),
        "godaddy.com": ("GoDaddy", []), "google.com": ("Google", ["Google Cloud", "Google Cloud Platform", "GCP"]),
        "hetzner.com": ("Hetzner", []), "ibm.com": ("IBM", ["IBM Cloud"]),
        "microsoft.com": ("Microsoft", ["Microsoft Azure"]), "oracle.com": ("Oracle", ["Oracle Cloud", "OCI"]),
        "ovhcloud.com": ("OVHcloud", ["OVH"]), "rackspace.com": ("Rackspace", []), "scaleway.com": ("Scaleway", [])},
    "javascript-web-frameworks": {
        "angular.dev": ("Angular", []), "astro.build": ("Astro", []), "backbonejs.org": ("Backbone.js", ["BackboneJS"]),
        "dojo.io": ("Dojo", ["Dojo Toolkit"]), "enyojs.com": ("Enyo", []),
        "gwtproject.org": ("Google Web Toolkit", ["GWT"]), "jquery.com": ("jQuery", []),
        "jqwidgets.com": ("jQWidgets", []), "nuxt.com": ("Nuxt", ["Nuxt.js"]),
        "prototypejs.org": ("Prototype", ["Prototype.js", "Prototype JavaScript Framework"]),
        "qooxdoo.org": ("qooxdoo", []), "sencha.com": ("Ext JS", ["Sencha", "ExtJS"]),
        "tanstack.com": ("TanStack", ["TanStack Start"]), "vuejs.org": ("Vue.js", ["Vue", "VueJS"]),
        "zkoss.org": ("ZK Framework", [])},
    "ecommerce-platforms": {
        "bigcommerce.com": ("BigCommerce", ["Commerce.com"]), "drupalcommerce.org": ("Drupal Commerce", []),
        "nopcommerce.com": ("nopCommerce", []), "opencart.com": ("OpenCart", []), "pimcore.org": ("Pimcore", []),
        "prestashop-project.org": ("PrestaShop", []), "shopify.com": ("Shopify", []),
        "shopline.com": ("SHOPLINE", []), "spreecommerce.org": ("Spree Commerce", []),
        "supadupa.me": ("SupaDupa", []), "ucoz.com": ("uCoz", []), "virtuemart.net": ("VirtueMart", []),
        "webflow.com": ("Webflow", []), "wix.com": ("Wix", []), "zen-cart.com": ("Zen Cart", [])},
    "crm-software": {
        "adempiere.io": ("ADempiere", []), "adobe.com": ("Adobe", ["Adobe Campaign", "Neolane"]),
        "attio.com": ("Attio", []), "booksy.com": ("Booksy", []), "capsulecrm.com": ("Capsule CRM", []),
        "dolibarr.org": ("Dolibarr", []), "getbase.com": ("Base CRM", []), "gnu.org": ("GNU Enterprise", []),
        "hubspot.com": ("HubSpot", []), "onlyoffice.com": ("ONLYOFFICE", []), "pipedrive.com": ("Pipedrive", []),
        "reallysimplesystems.com": ("Really Simple Systems", []), "salesforce.com": ("Salesforce", []),
        "sugarcrm.com": ("SugarCRM", []), "suitecrm.com": ("SuiteCRM", [])},
    "web-analytics": {
        "adobe.com": ("Adobe", ["Adobe Analytics"]), "awstats.org": ("AWStats", []),
        "bing.com": ("Bing", ["Bing Webmaster Tools"]), "goaccess.io": ("GoAccess", []), "ibm.com": ("IBM", ["Tealeaf"]),
        "marfeel.com": ("Marfeel", []), "mixpanel.com": ("Mixpanel", []),
        "plausible.io": ("Plausible", ["Plausible Analytics"]), "splunk.com": ("Splunk", []),
        "statcounter.com": ("StatCounter", []), "w3perl.com": ("W3Perl", []), "webalizer.net": ("Webalizer", []),
        "woopra.com": ("Woopra", []), "yahoo.com": ("Yahoo", ["Yahoo Web Analytics"]),
        "yandex.ru": ("Yandex", ["Yandex Metrica", "Yandex.Metrica", "Yandex Metrika"])},
    "online-payment-providers": {
        "adyen.com": ("Adyen", []), "airwallex.com": ("Airwallex", []), "amazon.com": ("Amazon", ["Amazon Pay"]),
        "apple.com": ("Apple", ["Apple Pay"]), "bitpay.com": ("BitPay", []), "checkout.com": ("Checkout.com", []),
        "creditcall.com": ("Creditcall", []), "heartlandpaymentsystems.com": ("Heartland Payment Systems", []),
        "paymentwall.com": ("Paymentwall", []), "payoneer.com": ("Payoneer", []), "paypal.com": ("PayPal", []),
        "playspan.com": ("PlaySpan", []), "squareup.com": ("Square", []), "stripe.com": ("Stripe", []),
        "wepay.com": ("WePay", [])},
    "buy-now-pay-later": {
        "affirm.com": ("Affirm", []), "apple.com": ("Apple", ["Apple Pay Later", "Apple Pay"]),
        "klarna.com": ("Klarna", []), "paypal.com": ("PayPal", ["PayPal Pay Later", "PayPal Pay in 4"]),
        "sezzle.com": ("Sezzle", []), "zip.co": ("Zip", ["Quadpay", "Zip Co", "Zip Pay"])},
    "online-course-platforms": {
        "alison.com": ("Alison", []), "codecademy.com": ("Codecademy", []), "edx.org": ("edX", []),
        "freecodecamp.org": ("freeCodeCamp", []), "futurelearn.com": ("FutureLearn", []),
        "instructure.com": ("Instructure", ["Canvas Network", "Canvas LMS"]), "iversity.org": ("iversity", []),
        "khanacademy.org": ("Khan Academy", []), "openlearning.com": ("OpenLearning", []),
        "pluralsight.com": ("Pluralsight", []), "shawacademy.com": ("Shaw Academy", []),
        "skillshare.com": ("Skillshare", []), "stanford.edu": ("Stanford", ["Stanford Online", "Stanford University"]),
        "udacity.com": ("Udacity", []), "wikiversity.org": ("Wikiversity", [])},
    "language-learning": {
        "babbel.com": ("Babbel", []), "berlitz.com": ("Berlitz", []),
        "ciil.org": ("Central Institute of Indian Languages", ["CIIL"]),
        "harpercollins.com": ("HarperCollins", []), "langenscheidt.de": ("Langenscheidt", []),
        "languagedrops.com": ("Drops", ["Language Drops"]), "linguaphonegroup.com": ("Linguaphone", []),
        "mangolanguages.com": ("Mango Languages", []), "memrise.com": ("Memrise", []),
        "michelthomas.com": ("Michel Thomas", ["Michel Thomas Method"]), "mondly.com": ("Mondly", []),
        "peacecorps.gov": ("Peace Corps", []), "pimsleur.com": ("Pimsleur", []),
        "rosettastone.com": ("Rosetta Stone", []), "tandem.net": ("Tandem", [])},
    "container-shipping-lines": {
        "cma-cgm.com": ("CMA CGM", []), "evergreen-marine.com": ("Evergreen", ["Evergreen Line", "Evergreen Marine"]),
        "grimaldi.napoli.it": ("Grimaldi", ["Grimaldi Lines", "Grimaldi Group"]), "hapag-lloyd.com": ("Hapag-Lloyd", []),
        "hmm21.com": ("HMM", ["Hyundai Merchant Marine"]),
        "irisl.net": ("IRISL", ["Islamic Republic of Iran Shipping Lines"]), "maersk.com": ("Maersk", []),
        "matson.com": ("Matson", []), "msc.com": ("MSC", ["Mediterranean Shipping Company"]),
        "one-line.com": ("Ocean Network Express", []), "pilship.com": ("Pacific International Lines", ["PIL"]),
        "sinotrans.com": ("Sinotrans", []), "wanhai.com": ("Wan Hai Lines", ["Wan Hai"]),
        "yangming.com": ("Yang Ming", ["Yang Ming Marine Transport"]),
        "zim.com": ("ZIM", ["ZIM Integrated Shipping Services"])},
    "management-consulting": {
        "alixpartners.com": ("AlixPartners", []), "atkearney.com": ("Kearney", ["A.T. Kearney", "AT Kearney"]),
        "bcg.com": ("Boston Consulting Group", ["BCG"]), "deloitte.com": ("Deloitte", []),
        "grantthornton.global": ("Grant Thornton", []), "huronconsultinggroup.com": ("Huron Consulting Group", []),
        "infosys.com": ("Infosys", ["Infosys Consulting"]), "occstrategy.com": ("OC&C Strategy Consultants", ["OC&C"]),
        "protiviti.com": ("Protiviti", []), "publicissapient.com": ("Publicis Sapient", []),
        "pwc.com": ("PwC", ["PricewaterhouseCoopers"]), "rsmus.com": ("RSM", ["RSM US", "McGladrey"]),
        "sia-partners.com": ("Sia Partners", []), "tcs.com": ("Tata Consultancy Services", ["TCS"]),
        "westmonroepartners.com": ("West Monroe", ["West Monroe Partners"])},
    "project-management-software": {
        "24sevenoffice.com": ("24SevenOffice", []), "assembla.com": ("Assembla", []),
        "axosoft.com": ("Axosoft", ["Axosoft OnTime"]), "gforge.com": ("GForge", ["FusionForge"]),
        "group-office.com": ("Group-Office", ["GroupOffice"]), "kidasa.com": ("KIDASA", ["Milestones Professional"]),
        "onlyoffice.com": ("ONLYOFFICE", []), "planisware.com": ("Planisware", []),
        "projectmanager.com": ("ProjectManager", ["ProjectManager.com"]), "rationalplan.com": ("RationalPlan", []),
        "shortcut.com": ("Shortcut", []), "smartsheet.com": ("Smartsheet", []),
        "spiderproject.com": ("Spider Project", []), "thoughtworks.com": ("Thoughtworks", []),
        "visma.fi": ("Visma", ["Severa", "Visma Severa"])},
    "note-taking-apps": {
        "bitsmithsoft.com": ("Personal Knowbase", []), "dayoneapp.com": ("Day One", []),
        "google.com": ("Google", ["Google Keep"]), "icloud.com": ("Apple Notes", ["iCloud"]),
        "notational.net": ("Notational Velocity", []), "obsidian.md": ("Obsidian", []),
        "office.com": ("Microsoft OneNote", ["OneNote"]), "qiqqa.com": ("Qiqqa", []), "qownnotes.org": ("QOwnNotes", []),
        "simplenote.com": ("Simplenote", []), "tagspaces.org": ("TagSpaces", []), "tiddlywiki.com": ("TiddlyWiki", []),
        "tranglos.com": ("KeyNote", ["KeyNote NF"]), "ulyssesapp.com": ("Ulysses", []),
        "zoho.com": ("Zoho", ["Zoho Notebook"])},
    "3d-printers": {
        "3dsystems.com": ("3D Systems", []), "bambulab.com": ("Bambu Lab", ["Bambu"]),
        "cellink.com": ("Cellink", ["BICO"]), "creality.com": ("Creality", []), "kudo3d.com": ("Kudo3D", []),
        "makerbot.com": ("MakerBot", []), "markforged.com": ("Markforged", []), "materialise.com": ("Materialise", []),
        "prusa3d.com": ("Prusa", ["Prusa Research", "Original Prusa"]), "sciaky.com": ("Sciaky", []),
        "somosmaker.com": ("3D makeR Technologies", []),
        "stanleyblackanddecker.com": ("Stanley Black & Decker", []), "stratasys.com": ("Stratasys", []),
        "voxeljet.com": ("voxeljet", []), "zortrax.com": ("Zortrax", [])},
    "us-airlines": {
        "aa.com": ("American", ["American Airlines"]), "alaskaair.com": ("Alaska", ["Alaska Airlines"]),
        "allegiantair.com": ("Allegiant", ["Allegiant Air"]), "delta.com": ("Delta", ["Delta Air Lines"]),
        "flyfrontier.com": ("Frontier", ["Frontier Airlines"]), "hawaiianairlines.com": ("Hawaiian", ["Hawaiian Airlines"]),
        "jetblue.com": ("JetBlue", ["JetBlue Airways"]), "southwest.com": ("Southwest", ["Southwest Airlines"]),
        "suncountry.com": ("Sun Country", ["Sun Country Airlines"]), "united.com": ("United", ["United Airlines"])},
    "accounting-software": {
        "24sevenoffice.com": ("24SevenOffice", []), "acumatica.com": ("Acumatica", []),
        "amesoft.com": ("AME Accounting Software", ["AMESoft"]), "compiere.com": ("Compiere", []),
        "financialforce.com": ("Certinia", ["FinancialForce"]), "freshbooks.com": ("FreshBooks", []),
        "gnucash.org": ("GnuCash", []), "ledgersmb.org": ("LedgerSMB", []),
        "microsoft.com": ("Microsoft", ["Microsoft Dynamics 365", "Dynamics 365", "Dynamics GP", "Business Central"]),
        "newviews.com": ("NewViews", []), "osas.com": ("OSAS", ["Open Systems Accounting Software"]),
        "pass-port.com": ("Passport Software", []), "sybiz.com": ("Sybiz", []),
        "tallysolutions.com": ("Tally", ["TallyPrime", "Tally Solutions"]), "xero.com": ("Xero", [])},
    "online-marketplaces": {
        "aliexpress.com": ("AliExpress", []), "amazon.com": ("Amazon", []), "asseenontv.com": ("As Seen On TV", []),
        "ebay.com": ("eBay", []), "etsy.com": ("Etsy", []), "farmigo.com": ("Farmigo", []),
        "flipkart.com": ("Flipkart", []), "hepsiburada.com": ("Hepsiburada", []), "pinduoduo.com": ("Pinduoduo", []),
        "shein.com": ("Shein", []), "temu.com": ("Temu", []), "trendyol.com": ("Trendyol", []),
        "vinted.com": ("Vinted", []), "walmart.com": ("Walmart", []), "wish.com": ("Wish", [])},
}
# Names the two word lists cannot see as ordinary: everyday phrases of more than one word, places and adjectives that
# answers in a category use, and words newer than web2 or used in a category's own sense. Judged by hand, with the reason.
PHRASES = {
    "Day One": "\"day one\" is an everyday phrase",
    "As Seen On TV": "\"as seen on TV\" is an everyday phrase",
    "Alaska": "also the state, which answers about flights in the US name",
    "Hawaiian": "also the adjective for Hawaii, which answers about flights in the US use",
    "American": "also the adjective for the US, which answers about flights in the US use",
    "Shortcut": "an ordinary word that web2 (1934) predates",
    "Perplexity": "also the measure of a language model that answers about models discuss",
    "HMM": "also the interjection \"hmm\"",
}

# The questions, written after the names and frozen with them. intent_tier labels follow guide/watch-methodology.md.
QUESTIONS = {
    "large-language-models": [
        ("list", "What are the best large language models for building a customer support chatbot?"),
        ("list", "Which AI model APIs are most reliable for production applications right now?"),
        ("list", "Which open-weight language models can a company run on its own servers?"),
        ("problem", "Our support team spends hours answering the same customer emails and I want software that can "
                    "draft the replies automatically. What should I look at?"),
        ("problem", "I need to summarize hundreds of long contracts every week without sending them to a provider that "
                    "trains on our data. What are my options?"),
        ("persona", "What is the best AI model for a small law firm that wants help drafting documents?"),
        ("persona", "Which AI model API should a two-person startup use to add a writing assistant to its app?"),
        ("pricing", "How much does it cost to use a large language model API for about a million requests a month?"),
        ("pricing", "Which AI chat assistants have a good free tier for everyday work?"),
        ("list", "What are the leading AI labs building frontier language models today?")],
    "ai-video-generators": [
        ("list", "What are the best AI video generators right now?"),
        ("list", "Which AI tools can turn a text prompt into a realistic video clip?"),
        ("list", "What are the best tools for generating video from a single image?"),
        ("problem", "I make product videos for a small online store and filming each product takes too long. Can AI "
                    "make these videos for me?"),
        ("problem", "Our training videos are expensive to reshoot whenever a policy changes. Is there a way to generate "
                    "them with AI instead?"),
        ("persona", "Which AI video generator is best for a YouTuber who needs short b-roll clips?"),
        ("persona", "What AI video tool would suit a marketing agency making social media ads for clients?"),
        ("pricing", "How much do AI video generators cost per minute of video?"),
        ("pricing", "Which AI video generators have a free plan?"),
        ("list", "Which AI video models produce the most consistent characters across shots?")],
    "vector-databases": [
        ("list", "What are the best vector databases for retrieval-augmented generation?"),
        ("list", "Which databases support fast similarity search over embeddings?"),
        ("list", "What are the most popular open-source vector databases?"),
        ("problem", "Our semantic search over two million product descriptions has become slow. What database should "
                    "we move the embeddings to?"),
        ("problem", "I want to add vector search without running a separate database next to our main one. What "
                    "options exist?"),
        ("persona", "Which vector database is best for a small startup building an AI chatbot over its documentation?"),
        ("persona", "What vector database should an enterprise with strict compliance requirements choose?"),
        ("pricing", "How much does a managed vector database cost for about 10 million vectors?"),
        ("pricing", "Which vector databases have a free tier for small projects?"),
        ("list", "Which vector databases scale best to billions of embeddings?")],
    "cloud-infrastructure": [
        ("list", "What are the best cloud providers for hosting virtual machines?"),
        ("list", "Which cloud infrastructure providers are the most reliable for a production web application?"),
        ("list", "What are good alternatives to the three biggest cloud providers for a small company?"),
        ("problem", "Our cloud bill keeps growing and most of it is a few always-on virtual servers. Where can we run "
                    "them for less?"),
        ("problem", "We need servers in both the US and Europe with predictable monthly pricing. Which providers "
                    "should we compare?"),
        ("persona", "Which cloud provider is best for a solo developer who wants a simple virtual server?"),
        ("persona", "What cloud platform should a mid-size healthcare company choose for HIPAA-compliant "
                    "infrastructure?"),
        ("pricing", "How much does a cloud virtual machine with 4 CPUs and 16 GB of RAM cost per month?"),
        ("pricing", "Which cloud providers offer a free tier or free credits for new accounts?"),
        ("list", "Which cloud providers offer GPU servers for training machine learning models?")],
    "javascript-web-frameworks": [
        ("list", "What are the best JavaScript frameworks for building a web application?"),
        ("list", "Which front-end frameworks are most popular with web developers today?"),
        ("list", "What are the best frameworks for building a fast content website with JavaScript?"),
        ("problem", "Our single-page app loads slowly and ranks poorly in search. Which framework would help us render "
                    "pages on the server?"),
        ("problem", "We maintain an old web app full of hand-written DOM code and want to move to a modern framework. "
                    "Where should we start?"),
        ("persona", "Which JavaScript framework is easiest for a beginner to learn?"),
        ("persona", "What framework should a large enterprise team choose for a long-lived internal web application?"),
        ("pricing", "Are there JavaScript frameworks with paid enterprise support or licenses?"),
        ("list", "Which JavaScript frameworks have the best TypeScript support?"),
        ("list", "Which full-stack JavaScript frameworks handle routing and data loading out of the box?")],
    "ecommerce-platforms": [
        ("list", "What are the best e-commerce platforms for starting an online store?"),
        ("list", "Which shopping cart software works best for a growing online business?"),
        ("list", "What are the best open-source e-commerce platforms?"),
        ("problem", "I sell handmade candles at local markets and want to start taking orders online. What should I "
                    "use to build my store?"),
        ("problem", "Our online store crashes during holiday sales and the plugins keep conflicting. Which platform "
                    "should we migrate to?"),
        ("persona", "Which e-commerce platform is best for a small clothing brand?"),
        ("persona", "What e-commerce software should a B2B wholesaler with thousands of products use?"),
        ("pricing", "How much does it cost per month to run an online store on a hosted e-commerce platform?"),
        ("pricing", "Which e-commerce platforms charge no transaction fees?"),
        ("list", "Which e-commerce platforms are easiest to set up without a developer?")],
    "crm-software": [
        ("list", "What is the best CRM software for small businesses?"),
        ("list", "Which CRM systems are easiest for a sales team to adopt?"),
        ("list", "What are the best open-source CRM systems?"),
        ("problem", "Our sales reps track leads in spreadsheets and follow-ups keep slipping. What software would fix "
                    "this?"),
        ("problem", "We lose track of which customers we emailed and what they bought. What tool should we use to keep "
                    "it all in one place?"),
        ("persona", "Which CRM is best for a real estate agent?"),
        ("persona", "What CRM should a B2B software startup with five salespeople choose?"),
        ("pricing", "How much does CRM software cost per user per month?"),
        ("pricing", "Which CRM tools have a good free plan?"),
        ("list", "Which CRM platforms are best for large enterprises?")],
    "web-analytics": [
        ("list", "What are the best web analytics tools for tracking website visitors?"),
        ("list", "Which website analytics tools respect visitor privacy and work without cookies?"),
        ("list", "What are the best self-hosted web analytics tools?"),
        ("problem", "I want to know which pages on my blog bring in readers and where they come from. What should I "
                    "install?"),
        ("problem", "Our cookie banner hurts conversions and we still need traffic numbers. How can we measure visits "
                    "without one?"),
        ("persona", "Which web analytics tool is best for a small business website?"),
        ("persona", "What analytics software should a large e-commerce site use to analyze customer journeys?"),
        ("pricing", "How much do web analytics tools cost for a site with 100,000 monthly visits?"),
        ("pricing", "Which website analytics tools are free?"),
        ("list", "Which tools analyze server log files to report website traffic?")],
    "online-payment-providers": [
        ("list", "What are the best payment processors for an online business?"),
        ("list", "Which payment gateways are best for accepting credit cards on a website?"),
        ("list", "Which payment providers support international customers and multiple currencies?"),
        ("problem", "Our online store's payment provider keeps declining legitimate customer cards. Which providers "
                    "should we consider switching to?"),
        ("problem", "I run a subscription business and need recurring billing with automatic card retries. What "
                    "payment provider should I use?"),
        ("persona", "What is the best way for a freelancer to accept card payments from clients online?"),
        ("persona", "Which payment processor is best for a high-volume marketplace that pays out to many sellers?"),
        ("pricing", "How much do online payment processors charge per transaction?"),
        ("pricing", "Which payment processors have the lowest fees for small businesses?"),
        ("list", "Which payment providers let an online store accept digital wallets and cryptocurrency?")],
    "buy-now-pay-later": [
        ("list", "What are the best buy now, pay later services for online shopping?"),
        ("list", "Which buy now, pay later apps are accepted at the most stores?"),
        ("list", "Which buy now, pay later providers can an online store offer at checkout?"),
        ("problem", "I need a new laptop for school but can't pay the full price at once. Which installment payment "
                    "services should I compare?"),
        ("problem", "Customers abandon carts on our furniture site because of the price. How can we let them pay over "
                    "time?"),
        ("persona", "Which buy now, pay later service is best for someone trying to build credit?"),
        ("persona", "What pay-over-time option is best for a small online boutique to offer its customers?"),
        ("pricing", "Do buy now, pay later services charge interest or late fees?"),
        ("pricing", "How much does it cost a merchant to offer buy now, pay later at checkout?"),
        ("list", "Which buy now, pay later companies report payments to credit bureaus?")],
    "online-course-platforms": [
        ("list", "What are the best websites for taking online courses?"),
        ("list", "Which online learning platforms offer certificates that employers recognize?"),
        ("list", "What are the best free online course websites?"),
        ("problem", "I want to switch careers into data analysis but can't go back to college full time. Where can I "
                    "learn online?"),
        ("problem", "Our company needs to train employees in new software skills without sending them to classes. "
                    "Which online course platforms work for teams?"),
        ("persona", "Which online course platform is best for a high school student preparing for college?"),
        ("persona", "What online learning site is best for a working adult who wants university-level courses?"),
        ("pricing", "How much do online course subscriptions cost per month?"),
        ("pricing", "Which online course platforms let you take courses for free and pay only for a certificate?"),
        ("list", "Which websites offer the best online courses for learning to code?")],
    "language-learning": [
        ("list", "What is the best app for learning a new language?"),
        ("list", "Which language learning programs actually get you speaking?"),
        ("list", "What are the best audio courses for learning a language while commuting?"),
        ("problem", "I'm moving to Spain in six months and know no Spanish. What's the fastest way to learn enough to "
                    "get by?"),
        ("problem", "I studied French in school but forgot most of it. What program would help me get it back?"),
        ("persona", "What is the best language learning app for kids?"),
        ("persona", "Which language course is best for a business traveler who needs conversational Japanese?"),
        ("pricing", "How much do language learning apps cost per year?"),
        ("pricing", "Which language learning apps are free?"),
        ("list", "Which language learning programs are best for practicing with a native speaker?")],
    "container-shipping-lines": [
        ("list", "What are the largest container shipping lines?"),
        ("list", "Which ocean carriers are the most reliable for shipping containers from Asia to the US West Coast?"),
        ("list", "Which container shipping companies have the best on-time performance?"),
        ("problem", "We import furniture from Vietnam and our containers keep arriving late. Which carriers should we "
                    "book with instead?"),
        ("problem", "I need to ship a few containers of machinery from Germany to Texas each month. Which shipping "
                    "lines serve that route?"),
        ("persona", "Which container shipping line is best for a small importer shipping a few containers a year?"),
        ("persona", "What ocean carrier should a large retailer use for weekly shipments from China?"),
        ("pricing", "How much does it cost to ship a 40-foot container from China to Los Angeles?"),
        ("pricing", "Which shipping lines offer the best contract rates for importers?"),
        ("list", "Which container lines offer online booking and shipment tracking?")],
    "management-consulting": [
        ("list", "What are the top management consulting firms?"),
        ("list", "Which consulting firms are best for business strategy work?"),
        ("list", "Which consulting firms specialize in digital transformation?"),
        ("problem", "Our company's growth has stalled and the board wants an outside review of our strategy. Which "
                    "consulting firms should we talk to?"),
        ("problem", "We're merging with a competitor and need help integrating the two organizations. Which firms do "
                    "post-merger integration?"),
        ("persona", "Which consulting firms work with mid-size companies rather than only large corporations?"),
        ("persona", "What consulting firm should a hospital system hire to cut operating costs?"),
        ("pricing", "How much do management consulting firms charge for a strategy project?"),
        ("pricing", "What are typical daily rates for management consultants?"),
        ("list", "Which consulting firms are best at restructuring and turnaround work?")],
    "project-management-software": [
        ("list", "What is the best project management software for teams?"),
        ("list", "Which project management tools are easiest to learn?"),
        ("list", "What are the best open-source project management tools?"),
        ("problem", "Our team tracks tasks in email threads and deadlines keep getting missed. What software should we "
                    "use?"),
        ("problem", "We run several client projects at once and can't see who is overloaded. Which tools show resource "
                    "workload?"),
        ("persona", "Which project management software is best for a small marketing agency?"),
        ("persona", "What project management tool should a construction company use for scheduling jobs?"),
        ("pricing", "How much does project management software cost per user?"),
        ("pricing", "Which project management tools have a free plan for small teams?"),
        ("list", "Which project management tools have the best Gantt charts?")],
    "note-taking-apps": [
        ("list", "What is the best note-taking app?"),
        ("list", "Which note-taking apps work well across phone and computer?"),
        ("list", "What are the best note-taking apps that store notes as plain text files?"),
        ("problem", "My notes are scattered across sticky notes, emails and documents and I can never find anything. "
                    "What app should I use?"),
        ("problem", "I want to link my research notes together and see how ideas connect. Which apps do that?"),
        ("persona", "Which note-taking app is best for a college student?"),
        ("persona", "What note-taking app should a writer use to organize a long book project?"),
        ("pricing", "How much do note-taking apps cost per year?"),
        ("pricing", "What are the best free note-taking apps?"),
        ("list", "Which note-taking apps are best for privacy and offline use?")],
    "3d-printers": [
        ("list", "What is the best 3D printer for beginners?"),
        ("list", "Which 3D printers are the most reliable for printing all day?"),
        ("list", "What are the best resin 3D printers?"),
        ("problem", "I keep breaking small plastic parts around the house and want to print replacements. What 3D "
                    "printer should I buy?"),
        ("problem", "Our engineering team waits weeks for test parts from suppliers. Which 3D printers could make them "
                    "in-house?"),
        ("persona", "Which 3D printer is best for a high school classroom?"),
        ("persona", "What industrial 3D printer should a manufacturer use for metal parts?"),
        ("pricing", "How much does a good 3D printer cost?"),
        ("pricing", "What are the best 3D printers under $500?"),
        ("list", "Which 3D printers can print in multiple colors?")],
    "us-airlines": [
        ("list", "What is the best US airline for domestic flights?"),
        ("list", "Which US airlines have the best on-time records?"),
        ("list", "Which airlines in the US have the most comfortable economy seats?"),
        ("problem", "I fly between New York and Los Angeles every month and my flights keep getting delayed. Which "
                    "airline should I switch to?"),
        ("problem", "I'm taking my family of five on vacation and checked bags are adding up. Which airlines let you "
                    "check bags for free?"),
        ("persona", "Which US airline is best for a business traveler who wants elite status?"),
        ("persona", "What airline is best for a student on a tight budget flying home for the holidays?"),
        ("pricing", "Which US airlines have the cheapest fares?"),
        ("pricing", "How much do US airlines charge for a checked bag?"),
        ("list", "Which US airlines have the best frequent flyer programs?")],
    "accounting-software": [
        ("list", "What is the best accounting software for small businesses?"),
        ("list", "Which accounting software is easiest for someone without an accounting background?"),
        ("list", "What are the best open-source accounting programs?"),
        ("problem", "I'm a freelancer and spend hours every month creating invoices and tracking expenses in "
                    "spreadsheets. What software should I use?"),
        ("problem", "Our company has outgrown its basic bookkeeping software and needs multi-entity reporting. What "
                    "should we move to?"),
        ("persona", "Which accounting software is best for a restaurant owner?"),
        ("persona", "What accounting software should a nonprofit use for fund accounting?"),
        ("pricing", "How much does accounting software cost per month?"),
        ("pricing", "Is there free accounting software for small businesses?"),
        ("list", "Which accounting software works best with an outside bookkeeper or accountant?")],
    "online-marketplaces": [
        ("list", "What are the best online marketplaces for shopping?"),
        ("list", "Which shopping sites have the cheapest prices on household goods?"),
        ("list", "Where can I buy secondhand clothes online?"),
        ("problem", "I need a phone case and a charger quickly but don't want to pay full retail price. Which shopping "
                    "sites should I check?"),
        ("problem", "I'm looking for unique handmade gifts that I can't find in stores. Where should I shop online?"),
        ("persona", "Which online marketplace is best for a college student furnishing a dorm room on a budget?"),
        ("persona", "Where should a parent shop online for affordable kids' clothes?"),
        ("pricing", "Which online marketplaces have the best free shipping?"),
        ("pricing", "Are ultra-cheap shopping apps really cheaper than big retail stores?"),
        ("list", "Which online marketplaces are the most trustworthy for buying electronics?")],
}


def load_watch():
    spec = importlib.util.spec_from_file_location("geo_watch", os.path.join(ROOT, "cli", "geo_watch.py"))
    gw = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gw)
    return gw


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


class Words(object):
    """Ordinary English words: a lowercase headword of web2 (or a day or month name) that is also among the TOP_N
    most frequent words of count_1w. A plural is read as its singular too (drops as drop)."""

    def __init__(self, web2, count1w):
        with io.open(web2, encoding="utf-8", errors="replace") as f:
            self.dict = set(w.strip() for w in f if w.strip() and w.strip().islower())
        self.rank = {}
        with io.open(count1w, encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f, 1):
                if i > TOP_N:
                    break
                self.rank[line.split("\t")[0]] = i
        self.sources = {"web2": {"sha256": sha256(web2), "lowercase_headwords": len(self.dict)},
                        "count_1w": {"sha256": sha256(count1w), "top_n": TOP_N,
                                     "source": "https://norvig.com/ngrams/count_1w.txt"}}

    def ordinary(self, term):
        """The reason a single-word name is an ordinary word, or None. Names of more than one word are not read here."""
        t = term.strip()
        if not re.fullmatch(r"[A-Za-z]+", t):
            return None
        w = t.lower()
        forms = [w] + ([w[:-1]] if w.endswith("s") and len(w) > 3 else []) + \
            ([w[:-2]] if w.endswith("es") and len(w) > 4 else [])
        for f in forms:
            if (f in self.dict or f in DAYS_MONTHS) and f in self.rank:
                return "%r is a common English word (web2 headword %r, rank %d in count_1w)" % (t, f, self.rank[f])
        return None


def build(words, gw):
    with io.open(os.path.join(HERE, "categories.json"), encoding="utf-8") as f:
        cats = json.load(f)["categories"]
    out_cats, files = [], {}
    for c in cats:
        cid = c["id"]
        names = NAMES[cid]
        drawn = [x for x in c["candidates"] if x["drawn"]]
        if sorted(names) != sorted(x["id"] for x in drawn):
            raise SystemExit("%s: NAMES does not list exactly the frame's candidates" % cid)
        qs = QUESTIONS[cid]
        tiers = sorted(set(t for t, _ in qs))
        if len(qs) != 10 or len([t for t in tiers if t in ("list", "problem", "persona", "pricing")]) < 3 \
                or any(t not in ("list", "problem", "persona", "pricing") for t in tiers):
            raise SystemExit("%s: 10 questions with at least three of the unbranded tiers" % cid)
        rows = [{"query_id": "q%02d" % i, "query": q, "intent_tier": t} for i, (t, q) in enumerate(qs, 1)]
        entries = []
        for x in sorted(drawn, key=lambda v: v["id"]):
            name, aliases = names[x["id"]]
            ent = {"name": name, "domains": x["domains"], "url_prefixes": [], "aliases": aliases}
            reasons = [r for r in (words.ordinary(t) for t in [name] + aliases) if r]
            reasons += ["%r: %s" % (t, PHRASES[t]) for t in [name] + aliases if t in PHRASES]
            bad_alias = [a for a in aliases if words.ordinary(a) or a in PHRASES]
            if bad_alias:
                raise SystemExit("%s/%s: alias %s is an ordinary word" % (cid, x["id"], bad_alias))
            e = gw.Entity(ent)
            named = [r["query_id"] for r in rows if e.named_in(r["query"])]
            entries.append({"id": x["id"], "site": x["site"], "entry": ent,
                            "ordinary_word": bool(reasons), "ordinary_word_reasons": reasons,
                            "named_by_questions": named,
                            "status": "out: named by %s" % ", ".join(named) if named else "remaining"})
        keep = sorted([v for v in entries if not v["named_by_questions"]], key=lambda v: v["entry"]["name"].casefold())
        cfg = {"$schema": gw.CONFIG_SCHEMA_URL, "brand": keep[0]["entry"], "competitors": [v["entry"] for v in keep[1:]],
               "queries": "queries.csv", "engines": ENGINES, "country": COUNTRY, "runs": RUNS,
               "max_calls": len(rows) * len(ENGINES) * RUNS, "budget_usd": None, "prices": {}}
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerow(["query_id", "query", "intent_tier"])
        for r in rows:
            w.writerow([r["query_id"], r["query"], r["intent_tier"]])
        files[os.path.join(WATCH_DIR, cid, "queries.csv")] = buf.getvalue()
        files[os.path.join(WATCH_DIR, cid, "geo-score-watch.json")] = json.dumps(cfg, ensure_ascii=False, indent=2) + "\n"
        out_cats.append({"id": cid, "questions": rows, "tiers": tiers, "candidates": entries,
                         "remaining": [v["id"] for v in keep], "brand": keep[0]["id"],
                         "config": "watch/%s/geo-score-watch.json" % cid,
                         "questions_hash": gw.questions_hash(rows)})
    doc = {"format": "geo-score/prereg-round0-candidates.v1",
           "plan": "benchmark/PREREGISTRATION.md, sections 4, 5.2 and 5.6",
           "built_by": "benchmark/prereg/round0/build_configs.py", "order": [
               "each candidate's watch entry (name, aliases, domains, url_prefixes) written first",
               "then the 10 questions of each category, frozen",
               "then the candidates a frozen question names (watch's brand_in_query matcher) are out",
               "then the configs, with the remaining candidates"],
           "ordinary_words": dict(words.sources, rule="a single-word name or alias is ordinary when its lowercase form, "
                                  "or its singular, is a lowercase headword of web2 (or a day or month name) and among "
                                  "the %d most frequent words of count_1w; names of more than one word are judged by "
                                  "hand (phrases)" % TOP_N, phrases=PHRASES),
           "engines": ENGINES, "runs": RUNS, "country": COUNTRY,
           "openai_endpoint": "an OpenAI-compatible endpoint given at run time (OPENAI_COMPAT_BASE_URL in place of "
                              "%s; key in OPENAI_COMPAT_API_KEY); the model id is OPENAI_COMPAT_MODEL, recorded in the "
                              "frozen sample" % OPENAI_PLACEHOLDER,
           "results_not_read": "benchmark/results.json, benchmark/results.csv and benchmark/raw/ were not opened before "
                               "these questions were committed",
           "categories": out_cats}
    files[OUT] = json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
    return files


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--web2", default="/usr/share/dict/web2")
    ap.add_argument("--count1w", required=True, help="Norvig's count_1w.txt")
    ap.add_argument("--check", action="store_true", help="rebuild and compare with the committed files")
    a = ap.parse_args(argv)
    gw = load_watch()
    files = build(Words(a.web2, a.count1w), gw)
    if a.check:
        bad = []
        for path, text in sorted(files.items()):
            try:
                with io.open(path, encoding="utf-8") as f:
                    if f.read() != text:
                        bad.append(path)
            except OSError:
                bad.append(path)
        print("%d files; %s" % (len(files), "all are what build_configs.py derives" if not bad else
                                 "differ: %s" % ", ".join(os.path.relpath(p, ROOT) for p in bad)))
        return 1 if bad else 0
    for path, text in sorted(files.items()):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with io.open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text)
    with io.open(OUT, encoding="utf-8") as f:
        doc = json.load(f)
    for c in doc["categories"]:
        out = [v for v in c["candidates"] if v["named_by_questions"]]
        flagged = [v["entry"]["name"] for v in c["candidates"] if v["ordinary_word"]]
        print("%-28s remaining %2d  out %d %s  ordinary words: %s" % (
            c["id"], len(c["remaining"]), len(out), [v["id"] for v in out], ", ".join(flagged) or "-"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
