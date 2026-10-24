#!/usr/bin/env python3
"""Aodı Akdıro product factory — renders the OS engine for any product.

Reads content.py (CONTENT dict + CONTRACT counts), validates contracts, then:
  app/index.html (engine + payload) · export/<slug>.json · export/<table>.csv · library/*.md
Fails loudly on any contract deviation.
"""
import json, csv, os, sys, importlib
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
FACTORY = os.environ.get("AOD_FACTORY", os.path.join(os.path.dirname(ROOT), "factory"))

import content as C

META_BASE = {
    "version": "1.0.0", "author": "Baran Avisat",
    "email": "baranavisat@gmail.com", "phone": "+90 531 326 37 22",
    "whatsapp": "https://wa.me/905313263722",
    "github": "https://github.com/aoodiakdiro0001-ops",
    "btc": "bc1q8dhtdrndxsl70e97t8grydfe6pjue37zrhzf6c",
    "usdt": "TLWdTjqqogkXNEXGiPWsGdjFP6ioycxeWW",
    "license": "MIT © 2026 Baran Avisat",
}


def iter_rows(tab):
    t = tab["type"]
    if t == "cards":
        return tab.get("items", [])
    if t == "roadmap":
        return tab.get("days", [])
    if t == "kanban":
        return tab.get("items", [])
    if t == "table":
        return tab.get("rows", [])
    if t == "calc":
        return tab.get("fields", [])
    if t == "checklist":
        return tab.get("items", [])
    return []


def validate():
    slug = C.CONTENT["slug"]
    tabs = C.CONTENT["tabs"]
    for tk, want in C.CONTRACT.items():
        tab = next((x for x in tabs if x["key"] == tk), None)
        if tab is None:
            raise SystemExit(f"[FAIL] contract tab missing: {tk}")
        n = len(iter_rows(tab))
        want_n = want["n"]
        if n != want_n:
            raise SystemExit(f"[FAIL] {tk}: want {want_n}, got {n}")
        # empty-field + gate
        for r in iter_rows(tab):
            for k, v in r.items():
                if isinstance(v, str) and not v.strip():
                    raise SystemExit(f"[FAIL] {tk}: empty {k} in {r.get('id','?')}")
                if isinstance(v, list) and not v:
                    raise SystemExit(f"[FAIL] {tk}: empty list {k} in {r.get('id','?')}")
    ids = []
    for tab in tabs:
        for r in iter_rows(tab):
            if "id" in r:
                ids.append(r["id"])
    if len(set(ids)) != len(ids):
        dupes = sorted({x for x in ids if ids.count(x) > 1})
        raise SystemExit(f"[FAIL] duplicate ids: {dupes}")
    return slug, tabs


def write_exports(slug, tabs, payload):
    os.makedirs(os.path.join(ROOT, "export"), exist_ok=True)
    with open(os.path.join(ROOT, "export", slug + ".json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    for tab in tabs:
        rows = iter_rows(tab)
        if not rows:
            continue
        cols = []
        for r in rows:
            for k, v in r.items():
                if k not in cols:
                    cols.append(k)
        with open(os.path.join(ROOT, "export", tab["key"] + ".csv"), "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(cols)
            w.writerows([[", ".join(x) if isinstance(x, list) else str(x) for x in [r.get(c, "") for c in cols]] for r in rows])


def write_library(slug, tabs):
    lib = os.path.join(ROOT, "library")
    os.makedirs(lib, exist_ok=True)
    for tab in tabs:
        rows = iter_rows(tab)
        if not rows:
            continue
        out = [f"# {tab['label_ar']} — {len(rows)} سجلاً", ""] + ["> بيانات افتراضية للتوضيح؛ استبدلها بما يناسب حالتك.", ""]
        t = tab["type"]
        if t == "cards":
            for it in rows:
                out += [f"## {it['id']} — {it['title']}", "", f"- التصنيف: {it.get('tag','—')}"]
                out += [f"- {b}" for b in it.get("bullets", [])]
                out += ["", "> " + it.get("pointer", ""), ""] + [it.get("body", ""), ""]
        elif t == "roadmap":
            for r in rows:
                out += [f"**اليوم {r['day']}** · {r['focus']}", "", f"- الفعل: {r['action']}", f"- المؤشر: {r['kpi']}", ""]
        elif t == "kanban":
            for r in rows:
                meta = ", ".join(f"{k}: {v}" for k, v in r.get("fields", {}).items())
                out += [f"**{r['id']}** — {r['title']}", "", f"- {meta}", f"- {r.get('note','')}", ""]
        elif t == "table":
            keys = [k for r in rows for k in r if k != "id"]
            keys = list(dict.fromkeys(keys))
            out += ["| المعرف | " + " | ".join(keys) + " |", "|---" * (len(keys) + 1) + "|"]
            for r in rows:
                out.append("| " + " | ".join(str(r.get(k, " — ")) for k in ["id"] + keys) + " |")
            out.append("")
        elif t == "checklist":
            for r in rows:
                out += [f"- [ ] {r['id']}: {r.get('text','')} (خطر: {r.get('risk','—')}) "]
            out.append("")
        elif t == "calc":
            out += ["الحقول:"]
            for r in rows:
                 out.append(f"- {r['key']}: {r.get('label_ar','')} (افتراضي {r.get('def', 0)})")
            out += ["", f"> الصيغة: {tab.get('note','')}", ""]
        with open(os.path.join(lib, tab["key"] + ".md"), "w", encoding="utf-8") as f:
            f.write("\n".join(out))


def main():
    slug, tabs = validate()
    meta = dict(META_BASE)
    meta.update({k: v for k, v in C.CONTENT.get("meta", {}).items()})
    meta["build_date"] = date.today().isoformat()
    payload = {"meta": meta, "tabs": tabs}

    with open(os.path.join(FACTORY, "os_engine.html"), encoding="utf-8") as f:
        tpl = f.read()
    if "__AOD_JSON__" not in tpl or "__AOD_SLUG__" not in tpl:
        raise SystemExit("[FAIL] engine template markers missing")
    html = tpl.replace("__AOD_SLUG__", slug).replace("__AOD_JSON__", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    os.makedirs(os.path.join(ROOT, "app"), exist_ok=True)
    with open(os.path.join(ROOT, "app", "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

    write_exports(slug, tabs, payload)
    write_library(slug, tabs)
    total = sum(len(iter_rows(t)) for t in tabs)
    print(f"[OK] contract holds — {', '.join(t['key'] + ':' + str(len(iter_rows(t))) for t in tabs)} | {total} records | app/index.html {len(html)//1024} KB")


if __name__ == "__main__":
    main()
