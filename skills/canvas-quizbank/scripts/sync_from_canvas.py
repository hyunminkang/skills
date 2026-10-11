#!/usr/bin/env python3
"""Record a Canvas review in the YAML: kept items -> reviewed, deleted -> removed.

After the instructor imports a bank and deletes the items that do not fit,
export what is left from Canvas and run:

  python3 sync_from_canvas.py BANK.yaml --export EXPORT.zip [--export MORE.zip]
  python3 sync_from_canvas.py BANK.yaml --kept-ids kept.txt    # ids or titles, one per line
  ...add --write to change the file (default: a dry run that prints the plan)

The export can be any zip Canvas produces: a QTI export of a quiz built from
the bank, a Classic question-bank or course export (.imscc), or a New Quizzes
QTI export. Items are matched to the YAML by the id at the start of their
title ("t9-001 · ..."), and by question text when a title has no id.

Removed items stay in the YAML with status: removed, so their ids are never
reused and later builds leave them out. Edits made in Canvas are not copied
back; items whose Canvas text differs from the YAML are listed so the edits
can be ported by hand. With --write, the file is edited line by line (comments
and layout are kept), a backup is saved as BANK.yaml.bak, and the result is
re-read to confirm that only status values changed.
"""
from __future__ import annotations

import argparse
import html
import re
import shutil
import sys
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bank import load_bank, questions  # noqa: E402
from mdrender import render  # noqa: E402

ITEM_TAGS = {"item", "assessmentItem"}


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _visible(fragment: str) -> str:
    """Text of an HTML fragment, equation images replaced by their TeX."""
    fragment = re.sub(r'<img[^>]*\bdata-equation-content="([^"]*)"[^>]*>',
                      lambda m: " " + m.group(1) + " ", fragment)
    fragment = re.sub(r'<img[^>]*\btitle="([^"]*)"[^>]*class="equation_image"[^>]*>',
                      lambda m: " " + m.group(1) + " ", fragment)
    return html.unescape(re.sub(r"<[^>]+>", " ", fragment))


def fingerprint(text: str, n: int = 160) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())[:n]


def export_items(zip_paths: list[Path]) -> list[dict]:
    """Every question in the exports: title and question text."""
    found = []
    for zp in zip_paths:
        with zipfile.ZipFile(zp) as zf:
            for name in zf.namelist():
                if not name.lower().endswith((".xml", ".qti")):
                    continue
                try:
                    root = ET.fromstring(zf.read(name))
                except ET.ParseError:
                    continue
                for node in root.iter():
                    if _local(node.tag) not in ITEM_TAGS:
                        continue
                    text = ""
                    for sub in node.iter():
                        if _local(sub.tag) == "mattext" and sub.text:
                            text = sub.text      # first mattext = the question
                            break
                    if not text:                 # QTI 2.x: itemBody markup
                        for sub in node.iter():
                            if _local(sub.tag) == "itemBody":
                                text = ET.tostring(sub, encoding="unicode")
                                break
                    found.append({"title": node.get("title") or "",
                                  "text": _visible(text), "file": name})
    return found


def match(items: list[dict], bank_qs: list[dict]):
    """Return (kept ids, unmatched export titles, ids whose text differs)."""
    ids = sorted((str(q["id"]) for q in bank_qs), key=len, reverse=True)
    by_print = {}
    for q in bank_qs:
        by_print.setdefault(fingerprint(_visible(render(str(q.get("question", ""))))),
                            str(q["id"]))
    kept, unmatched, edited = set(), [], []
    text_of = {str(q["id"]): fingerprint(_visible(render(str(q.get("question", "")))))
               for q in bank_qs}
    for it in items:
        title = it["title"].strip()
        qid = next((i for i in ids if title == i or re.match(
            re.escape(i) + r"(\s|·|:|-|$)", title)), None)
        fp = fingerprint(it["text"])
        if qid is None and fp:
            qid = by_print.get(fp)
        if qid is None:
            unmatched.append(title or it["text"][:60])
            continue
        kept.add(qid)
        if fp and text_of.get(qid) and fp != text_of[qid]:
            edited.append(qid)
    return kept, unmatched, sorted(set(edited))


_ITEM_START = re.compile(r"^(\s*)-\s+id:\s*['\"]?([^'\"\s#]+)")


def set_statuses(text: str, target: dict[str, str]) -> str:
    """Change (or insert) `status:` for the given ids, touching nothing else."""
    lines = text.splitlines(keepends=True)
    starts = []
    for k, line in enumerate(lines):
        m = _ITEM_START.match(line)
        if m:
            starts.append((k, len(m.group(1)) + 2, m.group(2)))
    inserts = []
    for n, (k, indent, qid) in enumerate(starts):
        if qid not in target:
            continue
        end = starts[n + 1][0] if n + 1 < len(starts) else len(lines)
        field = re.compile(r"^ {%d}status:\s*\S+" % indent)
        for j in range(k + 1, end):
            if field.match(lines[j]):
                nl = "\n" if lines[j].endswith("\n") else ""
                comment = re.search(r"\s+#.*$", lines[j].rstrip("\n"))
                lines[j] = (" " * indent + f"status: {target[qid]}"
                            + (comment.group(0) if comment else "") + nl)
                break
        else:
            inserts.append((k + 1, " " * indent + f"status: {target[qid]}\n"))
    for at, line in sorted(inserts, reverse=True):
        lines.insert(at, line)
    return "".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("bank", type=Path)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--export", type=Path, action="append",
                     help="zip exported from Canvas (repeatable)")
    src.add_argument("--kept-ids", type=Path,
                     help="text file with the ids (or Canvas titles) kept, one per line")
    ap.add_argument("--write", action="store_true", help="apply the changes")
    a = ap.parse_args()

    data = load_bank(a.bank)
    live = [q for q in questions(data) if q.get("status", "draft") != "removed"]
    if a.kept_ids:   # one id, or one Canvas title starting with an id, per line
        lines = [ln.strip() for ln in a.kept_ids.read_text().splitlines() if ln.strip()]
        found = [{"title": ln, "text": ""} for ln in lines]
        kept, unmatched, edited = match(found, live)
    else:
        kept, unmatched, edited = match(export_items(a.export), live)

    if not kept:
        print("No exported item matched this bank. Check that the export is from the "
              "right bank, or use --kept-ids. Nothing changed.", file=sys.stderr)
        return 1
    target = {}
    for q in live:
        qid = str(q["id"])
        new = "reviewed" if qid in kept else "removed"
        if q.get("status", "draft") != new:
            target[qid] = new
    to_rev = sorted(i for i, s in target.items() if s == "reviewed")
    to_rem = sorted(i for i, s in target.items() if s == "removed")
    print(f"{len(kept)} of {len(live)} items kept in Canvas.")
    print(f"  -> reviewed ({len(to_rev)}): {', '.join(to_rev) or '-'}")
    print(f"  -> removed  ({len(to_rem)}): {', '.join(to_rem) or '-'}")
    if unmatched:
        print(f"  in the export but not in the bank ({len(unmatched)}; added in Canvas?):")
        for u in unmatched:
            print(f"     {u}")
    if edited:
        print(f"  text differs in Canvas, port the edits by hand: {', '.join(edited)}")
    if len(kept) < 0.2 * len(live):
        print("  warning: fewer than 20% matched; is this the right export?")
    if not a.write:
        print("Dry run; add --write to apply.")
        return 0
    if not target:
        print("Nothing to change.")
        return 0

    original = a.bank.read_text(encoding="utf-8")
    updated = set_statuses(original, target)
    before, after = load_bank(a.bank), None
    shutil.copyfile(a.bank, a.bank.with_suffix(a.bank.suffix + ".bak"))
    a.bank.write_text(updated, encoding="utf-8")
    after = load_bank(a.bank)
    for q0, q1 in zip(questions(before), questions(after)):
        want = target.get(str(q0["id"]), q0.get("status", "draft"))
        rest0 = {k: v for k, v in q0.items() if k != "status"}
        rest1 = {k: v for k, v in q1.items() if k != "status"}
        if q1.get("status") != want or rest0 != rest1 or len(questions(before)) != len(questions(after)):
            a.bank.write_text(original, encoding="utf-8")
            print(f"Edit check failed at {q0['id']}; the file was restored.", file=sys.stderr)
            return 1
    print(f"Updated {a.bank} (backup: {a.bank.name}.bak).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
