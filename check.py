#!/usr/bin/env python3
# Universal auditor for factory products: syntax + contract counts + empty fields + encoding hygiene
import sys, re, ast, os
path = sys.argv[1] if len(sys.argv) > 1 else "content.py"
src = open(path, encoding="utf-8").read()
try:
    ast.parse(src)
except SyntaxError as e:
    print("SYNTAX FAIL line", e.lineno, (e.text or "")[:90].strip())
    raise SystemExit(1)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or ".")
import content as C

# garbage: CJK/Cyrillic/Hebrew/wide-forms — 【】 allowed as beat markers
garbage = re.compile(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef\u0400-\u04ff\u0590-\u05ff\u2e80-\u2eff]")
bracket_ok = re.compile(r"[\u3010\u3011]")
latin_in_arabic = re.compile(r"[\u0600-\u06FF][A-Za-z]{2,}|[A-Za-z]{2,}[\u0600-\u06FF]")

def rows(tab):
    return {"cards": tab.get("items", []), "roadmap": tab.get("days", []), "kanban": tab.get("items", []),
            "table": tab.get("rows", []), "calc": tab.get("fields", []), "checklist": tab.get("items", [])}[tab["type"]]

bad = 0
for tk, want in C.CONTRACT.items():
    tab = next((x for x in C.CONTENT["tabs"] if x["key"] == tk), None)
    if not tab:
        print(f"{tk}: TAB MISSING"); bad += 1; continue
    rs = rows(tab)
    if len(rs) != want["n"]:
        print(f"{tk}: COUNT FAIL want {want['n']} got {len(rs)}"); bad += 1; continue
    probs = []
    for r in rs:
        for k, v in r.items():
            s = str(v)
            dirty = [g for g in garbage.findall(s) if not bracket_ok.match(g)]
            if dirty: probs.append(f"{r.get('id','?')}: dirty {''.join(map(str,dirty[:4]))} :: {s[:50]}")
            if isinstance(v, str) and not v.strip(): probs.append(f"{r.get('id','?')}: empty {k}")
            if isinstance(v, list) and not v: probs.append(f"{r.get('id','?')}: empty list {k}")
    if probs:
        for p in probs[:10]: print("  ", p)
        bad += 1
    print(f"{tk}: {len(rs)}/{want['n']} — " + ("OK" if not probs else "FAIL"))
print("== content.py:", "CLEAN" if bad == 0 else f"{bad} FAILURES")
raise SystemExit(1 if bad else 0)
