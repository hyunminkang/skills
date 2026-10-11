#!/usr/bin/env python3
"""Validate quiz-bank YAML files, and optionally the QTI zip built from one.

Usage:
  python3 validate_bank.py BANK.yaml [MORE.yaml ...] [--report] [--require-source]
  python3 validate_bank.py BANK.yaml --qti BANK.qti.zip [--reviewed-only]
  add --strict to treat warnings as errors

Bank checks (schema in references/schema.md): required fields; ids unique
across all files given; question text unique within a file; at least three
distinct choices and a valid key for choice items; numerical and true/false
answers well formed; every image has alt text and an existing png/jpg/gif
file; verified: no carries a verify_note; source present (an error with
--require-source, used for newly drafted items); multiple-choice keys not all
at one position.

Package checks with --qti (the ones Canvas actually enforces): imsmanifest.xml
at the zip root with a bare default namespace (a prefixed <ns0:manifest> makes
Canvas report "Unsupported content package"); an imsqti resource pointing at
a file in the zip; an <assessment> or a titled <objectbank>; no MathML (New
Quizzes renders it as "Unexpected text node"); every bundled image declared
in the manifest and present; and, item by item, the question type and the
scored answer in the package match the YAML.

Exit code 1 on any error, so an AI agent can use it as its feedback loop.
"""
from __future__ import annotations

import argparse
import collections
import html
import re
import sys
import zipfile
from pathlib import Path
from urllib.parse import unquote
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bank import active, check_bank, load_bank, qtype, summarize, tally  # noqa: E402
from build_qti import QUESTION_TYPE, TITLE_SEP  # noqa: E402

QTI_NS = "http://www.imsglobal.org/xsd/ims_qtiasiv1p2"
CP_NS = "http://www.imsglobal.org/xsd/imscp_v1p1"
Q = f"{{{QTI_NS}}}"


def _visible(mattext) -> str:
    """Visible text with equations collapsed back to their TeX."""
    raw = (mattext.text if mattext is not None else "") or ""
    raw = re.sub(r'<img[^>]*\bdata-equation-content="([^"]*)"[^>]*/?>',
                 lambda m: m.group(1), raw)
    return html.unescape(re.sub(r"<[^>]+>", "", raw))


def _alnum(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", re.sub(r"[`$*_]", "", str(text)).lower())


def _num(text) -> float | None:
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def _close(a: float, b: float) -> bool:
    return abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b))


def check_package(zip_path: Path, items: list[dict]) -> list[str]:
    errors: list[str] = []
    try:
        zf = zipfile.ZipFile(zip_path)
    except (OSError, zipfile.BadZipFile) as exc:
        return [f"{zip_path}: cannot open ({exc})"]
    names = set(zf.namelist())
    if "imsmanifest.xml" not in names:
        return [f"{zip_path}: no imsmanifest.xml at the zip root"]

    manifest_raw = zf.read("imsmanifest.xml").decode("utf-8")
    if re.search(r"<\w+:manifest[\s>]", manifest_raw):
        errors.append(f"{zip_path}: <manifest> has a namespace prefix; Canvas will "
                      f"report 'Unsupported content package'")
    try:
        manifest = ET.fromstring(manifest_raw)
    except ET.ParseError as exc:
        return errors + [f"{zip_path}: imsmanifest.xml is not well-formed ({exc})"]
    resources = manifest.findall(f"{{{CP_NS}}}resources/{{{CP_NS}}}resource")
    qti_res = [r for r in resources if (r.get("type") or "").startswith("imsqti")]
    if not qti_res:
        return errors + [f"{zip_path}: no imsqti resource in the manifest"]
    href = qti_res[0].get("href")
    if href not in names:
        return errors + [f"{zip_path}: manifest points at {href!r}, not in the zip"]
    declared = {unquote(r.get("href") or "") for r in resources
                if r.get("type") == "webcontent"}

    qti_raw = zf.read(href).decode("utf-8")
    if re.search(r"<\w+:questestinterop[\s>]", qti_raw):
        errors.append(f"{zip_path}: <questestinterop> has a namespace prefix")
    if "<math" in qti_raw or "MathML" in qti_raw:
        errors.append(f"{zip_path}: contains MathML; New Quizzes shows it as "
                      f"'Unexpected text node'. Math must be equation images.")
    try:
        root = ET.fromstring(qti_raw)
    except ET.ParseError as exc:
        return errors + [f"{zip_path}: {href} is not well-formed ({exc})"]
    bank = root.find(f"{Q}objectbank")
    if bank is None and root.find(f"{Q}assessment") is None:
        errors.append(f"{zip_path}: neither <assessment> nor <objectbank>")
    if bank is not None and "bank_title" not in [
            f.text for f in root.iter(f"{Q}fieldlabel")]:
        errors.append(f"{zip_path}: <objectbank> without bank_title (unnamed bank)")

    for src in re.findall(r'src="([^"]+)"', html.unescape(qti_raw)):
        if src.startswith("/equation_images/") or src.startswith("data:"):
            continue
        m = re.match(r"(?:%24|\$)IMS-CC-FILEBASE(?:%24|\$)/(.+)", src)
        if not m:
            errors.append(f"{zip_path}: image src {src!r} is neither bundled nor "
                          f"an equation")
            continue
        path = unquote(m.group(1))
        if path not in names:
            errors.append(f"{zip_path}: image {path!r} is referenced but not in the zip")
        if path not in declared:
            errors.append(f"{zip_path}: image {path!r} has no webcontent resource "
                          f"in the manifest")
    for tag in re.findall(r"<img\b[^>]*>", html.unescape(qti_raw)):
        if "equation_image" not in tag and not re.search(r'alt="[^"]+', tag):
            errors.append(f"{zip_path}: an image has no alt text: {tag[:80]}")

    qti_items = root.findall(f".//{Q}item")
    if len(qti_items) != len(items):
        return errors + [f"{zip_path}: {len(qti_items)} items in the package, "
                         f"{len(items)} expected from the YAML"]
    by_id = {str(q["id"]): q for q in items}
    for k, node in enumerate(qti_items):
        title = node.get("title") or ""
        qid = title.split(TITLE_SEP)[0].strip()
        src = by_id.get(qid, items[k])
        errors += [f"{src['id']}: {e}" for e in _check_item(node, src)]
    return errors


def _check_item(node, q: dict) -> list[str]:
    t = qtype(q)
    fields = {f.findtext(f"{Q}fieldlabel"): f.findtext(f"{Q}fieldentry")
              for f in node.iter(f"{Q}qtimetadatafield")}
    if fields.get("question_type") != QUESTION_TYPE[t]:
        return [f"package type {fields.get('question_type')!r}, YAML type {t!r}"]
    scored = node.find(f'.//{Q}respcondition[@continue="No"]')
    if scored is None:
        return ["no scoring condition in the package"]
    conds = scored.find(f"{Q}conditionvar")
    if t == "numerical":
        a = q["answer"]
        lo = _num(conds.findtext(f".//{Q}vargte"))
        hi = _num(conds.findtext(f".//{Q}varlte"))
        want = ((a["value"] - a.get("tolerance", 0), a["value"] + a.get("tolerance", 0))
                if "value" in a else (a["min"], a["max"]))
        if lo is None or hi is None or not (_close(lo, want[0]) and _close(hi, want[1])):
            return [f"package accepts [{lo}, {hi}], YAML wants [{want[0]}, {want[1]}]"]
        return []

    labels = node.findall(f".//{Q}response_label")
    ids = [lab.get("ident") for lab in labels]
    if t == "multiple_answers":
        wrong = {v.text for v in conds.findall(f".//{Q}not/{Q}varequal")}
        right = {v.text for v in conds.iter(f"{Q}varequal")} - wrong
        got = sorted(ids.index(x) for x in right if x in ids)
        if got != sorted(q["answer"]):
            return [f"package scores choices {got}, YAML answer is {sorted(q['answer'])}"]
        return []
    eq = conds.find(f"{Q}varequal")
    if eq is None or eq.text not in ids:
        return ["scored ident is not one of the choices"]
    pos = ids.index(eq.text)
    if t == "true_false":
        if pos != (0 if q["answer"] else 1):
            return [f"package scores {'True' if pos == 0 else 'False'}, "
                    f"YAML answer is {q['answer']}"]
        return []
    if pos != q["answer"]:
        return [f"package scores choice #{pos}, YAML key is #{q['answer']}"]
    want = _alnum(q["choices"][q["answer"]])
    got = _alnum(_visible(labels[pos].find(f".//{Q}mattext")))
    if want and want not in got:
        return ["scored choice text does not match the YAML key"]
    return []


def report(items: list[dict], warnings: list[str]):
    print("\n=== coverage report ===")
    print(f"{len(items)} items (not counting removed)")
    for key, default in (("difficulty", "?"), ("type", "multiple_choice"),
                         ("status", "draft"), ("verified", "not recorded")):
        print(f"  {key:10s} " + tally(items, key, default))
    mc = [q for q in items if qtype(q) == "multiple_choice"
          and isinstance(q.get("answer"), int) and q.get("choices")]
    if mc:
        keys = collections.Counter(q["answer"] for q in mc)
        print("  MC key positions: " + ", ".join(f"{chr(65 + k)} {v}" for k, v in sorted(keys.items())))
        longest = [q["id"] for q in mc if len(str(q["choices"][q["answer"]])) >= 20
                   and len(str(q["choices"][q["answer"]])) > 1.25 * max(
                       len(str(c)) for j, c in enumerate(q["choices"]) if j != q["answer"])]
        print(f"  key clearly the longest option (informational): {len(longest)} of {len(mc)}"
              + (f" ({', '.join(longest[:12])}{' ...' if len(longest) > 12 else ''})"
                 if longest else ""))
    no_source = [q["id"] for q in items if not q.get("source")]
    if no_source:
        print(f"  no source: {len(no_source)}")
    print("  objectives:")
    objectives = collections.Counter(str(q.get("objective", "?")) for q in items)
    for obj, c in sorted(objectives.items()):
        print(f"    {c:3d}  {obj}")
    if warnings:
        print(f"  warnings: {len(warnings)}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--report", action="store_true", help="print a coverage summary")
    ap.add_argument("--require-source", action="store_true",
                    help="a missing 'source' is an error (use for new drafts)")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    ap.add_argument("--verbose", action="store_true",
                    help="list every warning (default: grouped by kind)")
    ap.add_argument("--qti", type=Path, metavar="ZIP",
                    help="also check the package built from the (single) bank")
    ap.add_argument("--reviewed-only", action="store_true",
                    help="with --qti: the package was built with --reviewed-only")
    a = ap.parse_args()

    errors, warnings, items, seen = [], [], [], {}
    banks = []
    for path in a.files:
        try:
            data = load_bank(path)
        except Exception as exc:   # YAML syntax errors carry line numbers
            errors.append(f"{path}: cannot parse YAML: {exc}")
            continue
        e, w = check_bank(data, path, seen, a.require_source)
        errors += e
        warnings += w
        if isinstance(data, dict):
            banks.append((path, data))
            items += [q for q in active(data) if isinstance(q, dict)]

    if a.qti:
        if len(banks) != 1:
            errors.append("--qti checks one bank at a time")
        elif not errors:
            expected = active(banks[0][1], a.reviewed_only)
            pkg_errors = check_package(a.qti, expected)
            errors += pkg_errors
            if not pkg_errors:
                print(f"package {a.qti.name}: opened; manifest, namespaces, images and "
                      f"all {len(expected)} items' types and answer keys match the YAML")

    for w in (warnings if a.verbose else summarize(warnings)):
        print(f"warning: {w}")
    for e in errors:
        print(f"ERROR {e}")
    if a.report:
        report(items, warnings)
    bad = len(errors) + (len(warnings) if a.strict else 0)
    print(f"\n{len(items)} items checked: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
