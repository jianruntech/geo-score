"""Remove Gemini's grounded results from round 0's published run files.

The Gemini API terms for Grounding with Google Search do not allow caching, syndicating or analysing
Grounded Results or Search Suggestions (https://ai.google.dev/gemini-api/terms). Round 0's Gemini runs
all stopped on the free tier's quota, so none of their answers entered the analysis; this script keeps
only what describes the request (question, run, status, usage, timing, error) and drops the answer
text, the links, the search queries and everything computed from them. A run's summary that pooled
Gemini answers is dropped too; the OpenAI answers it was computed from are still in the file.

Usage: python3 benchmark/prereg/round0/redact_gemini.py benchmark/prereg/round0/runs/wave0
"""
import glob
import json
import os
import sys

KEEP = {"query_id", "engine", "run", "status", "error", "usage", "cost_usd", "seconds", "ask"}
NOTE = ("Gemini grounded results removed: the Gemini API terms (Grounding with Google Search) do not allow "
        "storing or republishing them. Counts per status are kept.")


def redact(path):
    with open(path, encoding="utf-8") as f:
        run = json.load(f)
    changed = False
    gemini_ok = 0
    for i, s in enumerate(run.get("samples", [])):
        if s.get("engine") != "gemini":
            continue
        gemini_ok += s.get("status") == "ok"
        kept = {k: v for k, v in s.items() if k in KEEP}
        if kept != s:
            kept["redacted"] = True
            run["samples"][i] = kept
            changed = True
    if gemini_ok and "summary" in run:
        run["summary"] = {"redacted": NOTE}
        changed = True
    if changed:
        notes = run.setdefault("notes", [])
        if NOTE not in notes:
            notes.append(NOTE)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(run, f, ensure_ascii=False, indent=1)
            f.write("\n")
    return changed, gemini_ok


def main(root):
    files = sorted(glob.glob(os.path.join(root, "*", "*.json")))
    touched = sum(redact(p)[0] for p in files)
    print(f"{touched} of {len(files)} run files changed")


if __name__ == "__main__":
    main(sys.argv[1])
