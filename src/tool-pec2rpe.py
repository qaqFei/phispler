import json
from sys import argv

from light_utils import pec2rpe

if len(argv) < 3:
    print("Usage: tool-pec2rpe <input> <output>")
    raise SystemExit

with open(argv[1], "r", encoding="utf-8") as f:
    pec = f.read()

result, errs = pec2rpe(pec)

for e in errs:
    print(f"warning: {repr(e)}")

json.dump(result, open(argv[2], "w", encoding="utf-8"), ensure_ascii=False)
