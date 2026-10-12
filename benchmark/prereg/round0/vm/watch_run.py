#!/usr/bin/env python3
"""`geo_score.py watch` with patient retries, for round 0's collection (amendment of 2026-10-12).

    python3 watch_run.py --cli PATH/cli/geo_watch.py -- run -c CONFIG --quiet

The frozen CLI is used unchanged: this wrapper loads its geo_watch.py and wraps the one function that sends a request
(`TRANSPORT`), so that an answer of HTTP 429, 500, 502, 503 or 504 is retried after 15, 30, 60, 120 and 120 seconds
before the CLI's own retries see it. Gemini's free tier answered 503 ("high demand") to 2 of 3 test requests, and the
CLI's own policy (three tries a few seconds apart; an engine stops after three answers in a row fail) would stop the
engine for most categories. A 429 whose body says a daily quota is used up is not retried. Nothing the CLI counts or
saves changes: an answer that still fails is saved as an error, as the CLI saves it, and reported. A request that timed
out is not retried, as the CLI does not retry one (it may have been billed).

Keys stay in the environment and are never printed. Standard library only.
"""
import argparse, importlib.util, sys, time

WAITS = (15, 30, 60, 120, 120)
RETRY = (429, 500, 502, 503, 504)
DAILY = ("per day", "perday", "requests per day", "daily")


def load(path):
    spec = importlib.util.spec_from_file_location("geo_watch", path)
    gw = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gw)
    return gw


def patient(transport, sleep=time.sleep, log=sys.stderr):
    """TRANSPORT with retries on transient HTTP answers; same signature and return value."""
    def call(url, headers, body, timeout=None):
        for i, wait in enumerate((0,) + WAITS):
            if wait:
                sleep(wait)
            st, hdrs, raw = transport(url, headers, body) if timeout is None else transport(url, headers, body,
                                                                                               timeout=timeout)
            if st not in RETRY:
                return st, hdrs, raw
            text = (raw or b"")[:2000].decode("utf-8", "replace").lower()
            if st == 429 and "quota" in text and any(w in text for w in DAILY):
                print("watch_run: HTTP 429, daily quota used up; not retried", file=log)
                return st, hdrs, raw
            if i < len(WAITS):
                print("watch_run: HTTP %d, retry %d of %d in %d s" % (st, i + 1, len(WAITS), WAITS[i]), file=log)
        return st, hdrs, raw
    return call


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--cli", required=True, help="the frozen CLI's cli/geo_watch.py")
    ap.add_argument("args", nargs=argparse.REMAINDER, help="-- then the watch command, as geo_score.py watch takes it")
    a = ap.parse_args(argv)
    args = a.args[1:] if a.args[:1] == ["--"] else a.args
    gw = load(a.cli)
    gw.TRANSPORT = patient(gw.TRANSPORT)
    return gw.main(args, prog="geo_score.py watch")


if __name__ == "__main__":
    sys.exit(main())
