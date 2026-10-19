#!/usr/bin/env python3
"""Exit non-zero when a source failed, so the GitHub Action turns red and emails the owner."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(ROOT, "data.json"), encoding="utf-8"))
bad = {k: v for k, v in d.get("status", {}).items() if v != "ok"}
print(open(os.path.join(ROOT, "report.md"), encoding="utf-8").read())
if bad:
    print("SOURCE PROBLEM:", json.dumps(bad))
    sys.exit(1)
