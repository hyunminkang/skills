#!/usr/bin/env python3
"""Build a Canvas-importable QTI 1.2 zip (and a review sheet) from a YAML bank.

Usage:
  python3 build_qti.py BANK.yaml -o BANK.qti.zip [--review-md BANK.review.md]
                       [--mode assessment|objectbank] [--reviewed-only]
                       [--no-id-in-title] [--image-mode files|inline]

Standard library only (plus PyYAML, bundled in _vendor/ as a fallback).
The bank is checked with the same rules as validate_bank.py first; the build
stops on any error.

Canvas details that each cost a failed import to learn, kept on purpose:
  - Every XML document has a bare default namespace (xmlns="..."), never a
    generated ns0: prefix. Canvas finds the QTI resource with CSS selectors
    that silently match nothing on prefixed elements, and the import fails as
    "Unsupported content package" with no detail.
  - Math is a Canvas equation image (/equation_images/...), never MathML,
    which New Quizzes renders as "Unexpected text node: '<latex>'".
  - The general-feedback condition (continue="Yes") comes before the scoring
    condition (continue="No"); after it, students who answered correctly
    would never see the explanation.
  - mode "assessment" is the shape New Quizzes' Item Bank > Import Content
    expects (and Classic imports as a quiz); "objectbank" arrives in Classic
    Quizzes as a named question bank.
Images are bundled under images/ and referenced through Canvas's
$IMS-CC-FILEBASE$ token with a webcontent resource each, the layout Canvas
exports use and the text2qti project (BSD-3) has shipped for years.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import os
import re
import sys
import tempfile
import uuid
import zipfile
from pathlib import Path
from urllib.parse import quote
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bank import (IMAGE_TYPES, active, check_bank, load_bank,  # noqa: E402
                  qtype, summarize, tally)
from mdrender import render  # noqa: E402

QTI_NS = "http://www.imsglobal.org/xsd/ims_qtiasiv1p2"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
CP_NS = "http://www.imsglobal.org/xsd/imscp_v1p1"
FILEBASE = "%24IMS-CC-FILEBASE%24"
TITLE_SEP = " · "   # "t9-001 · Restarting the stream"

# ET's namespace registry is global and keyed by prefix as well as URI, so
# registering "" for a second URI deletes the first mapping. Each tree claims
# the default namespace immediately before it is written (see write_package).
# write(default_namespace=...) cannot be used: it rejects the unqualified
# attribute names (ident, title, texttype) that QTI 1.2 requires.
ET.register_namespace("xsi", XSI_NS)

QUESTION_TYPE = {
    "multiple_choice": "multiple_choice_question",
    "multiple_answers": "multiple_answers_question",
    "true_false": "true_false_question",
    "numerical": "numerical_question",
}


def q_(tag: str) -> str:
    return f"{{{QTI_NS}}}{tag}"


def make_ident(prefix: str) -> str:
    return prefix + uuid.uuid4().hex


def fmt_num(x) -> str:
    return f"{float(x):.15g}"


class Images:
    """Collects the figures an item references and rewrites their src."""

    def __init__(self, bank_dir: Path, mode: str):
        self.bank_dir, self.mode = bank_dir, mode
        self.files: dict[str, bytes] = {}      # zip path -> bytes
        self._by_digest: dict[str, str] = {}

    def hook(self, src: str, alt: str) -> str:
        if re.match(r"^[a-z][a-z0-9+.-]*:", src, re.I):
            return src
        path = self.bank_dir / src
        data = path.read_bytes()
        ext = path.suffix.lower()
        if self.mode == "inline":
            return f"data:{IMAGE_TYPES[ext]};base64," + base64.b64encode(data).decode()
        digest = hashlib.sha1(data).hexdigest()
        if digest not in self._by_digest:
            name = re.sub(r"[^A-Za-z0-9._-]", "_", path.name)
            if f"images/{name}" in self.files:
                name = f"{path.stem}_{digest[:8]}{ext}"
            self._by_digest[digest] = f"images/{name}"
            self.files[f"images/{name}"] = data
        return f"{FILEBASE}/{quote(self._by_digest[digest])}"


def add_field(parent, label: str, value: str):
    field = ET.SubElement(parent, q_("qtimetadatafield"))
    ET.SubElement(field, q_("fieldlabel")).text = label
    ET.SubElement(field, q_("fieldentry")).text = value


def add_html(parent, html: str):
    material = ET.SubElement(parent, q_("material"))
    ET.SubElement(material, q_("mattext"), {"texttype": "text/html"}).text = html
    return material


def feedback_markdown(q: dict) -> str:
    text = str(q.get("explanation") or "").rstrip()
    if q.get("source"):
        text += f"\n\n*Source: {q['source']}*"
    return text.strip()


def item_title(q: dict, n: int, id_in_title: bool) -> str:
    title = str(q.get("title") or "").strip()
    if id_in_title:
        title = f"{q['id']}{TITLE_SEP}{title}" if title else str(q["id"])
    return (title or f"Question {n}")[:250]


def build_item(container, q: dict, n: int, images: Images, id_in_title: bool):
    t = qtype(q)
    md = lambda text: render(str(text), images.hook)  # noqa: E731
    item = ET.SubElement(container, q_("item"),
                         {"ident": make_ident("i"),
                          "title": item_title(q, n, id_in_title)})

    if t == "true_false":
        labels = ["True", "False"]
        answer_ids = [str(1000 + n * 100 + j) for j in range(2)]
        correct = [0 if q["answer"] else 1]
    elif t == "numerical":
        labels, answer_ids, correct = [], [str(1000 + n * 100)], []
    else:
        labels = [str(c) for c in q["choices"]]
        answer_ids = [str(1000 + n * 100 + j) for j in range(len(labels))]
        correct = q["answer"] if t == "multiple_answers" else [q["answer"]]

    meta = ET.SubElement(ET.SubElement(item, q_("itemmetadata")), q_("qtimetadata"))
    add_field(meta, "question_type", QUESTION_TYPE[t])
    add_field(meta, "points_possible", f"{float(q.get('points', 1)):g}")
    add_field(meta, "original_answer_ids", ",".join(answer_ids))
    add_field(meta, "assessment_question_identifierref", make_ident("q"))

    presentation = ET.SubElement(item, q_("presentation"))
    add_html(presentation, md(q["question"]))
    if t == "numerical":
        response = ET.SubElement(presentation, q_("response_str"),
                                 {"ident": "response1", "rcardinality": "Single"})
        fib = ET.SubElement(response, q_("render_fib"), {"fibtype": "Decimal"})
        ET.SubElement(fib, q_("response_label"), {"ident": "answer1"})
    else:
        response = ET.SubElement(
            presentation, q_("response_lid"),
            {"ident": "response1",
             "rcardinality": "Multiple" if t == "multiple_answers" else "Single"})
        shuffle = t != "true_false" and q.get("shuffle_answers", True)
        choice = ET.SubElement(response, q_("render_choice"),
                               {"shuffle": "Yes" if shuffle else "No"})
        for aid, label in zip(answer_ids, labels):
            lab = ET.SubElement(choice, q_("response_label"), {"ident": aid})
            add_html(lab, md(label) if t != "true_false" else label)

    res = ET.SubElement(item, q_("resprocessing"))
    outcomes = ET.SubElement(res, q_("outcomes"))
    ET.SubElement(outcomes, q_("decvar"), {"maxvalue": "100", "minvalue": "0",
                                           "varname": "SCORE", "vartype": "Decimal"})
    feedback = feedback_markdown(q)
    if feedback:
        # Must precede the scoring condition: that one is continue="No", so
        # anything after it is reached only by wrong answers.
        fb = ET.SubElement(res, q_("respcondition"), {"continue": "Yes"})
        ET.SubElement(ET.SubElement(fb, q_("conditionvar")), q_("other"))
        ET.SubElement(fb, q_("displayfeedback"),
                      {"feedbacktype": "Response", "linkrefid": "general_fb"})

    cond = ET.SubElement(res, q_("respcondition"), {"continue": "No"})
    var = ET.SubElement(cond, q_("conditionvar"))
    if t == "numerical":
        a = q["answer"]
        if "value" in a:
            tol = float(a.get("tolerance", 0))
            either = ET.SubElement(var, q_("or"))
            ET.SubElement(either, q_("varequal"),
                          {"respident": "response1"}).text = fmt_num(a["value"])
            both = ET.SubElement(either, q_("and"))
            ET.SubElement(both, q_("vargte"),
                          {"respident": "response1"}).text = fmt_num(a["value"] - tol)
            ET.SubElement(both, q_("varlte"),
                          {"respident": "response1"}).text = fmt_num(a["value"] + tol)
        else:
            ET.SubElement(var, q_("vargte"),
                          {"respident": "response1"}).text = fmt_num(a["min"])
            ET.SubElement(var, q_("varlte"),
                          {"respident": "response1"}).text = fmt_num(a["max"])
    elif t == "multiple_answers":
        both = ET.SubElement(var, q_("and"))
        for j, aid in enumerate(answer_ids):
            parent = both if j in correct else ET.SubElement(both, q_("not"))
            ET.SubElement(parent, q_("varequal"), {"respident": "response1"}).text = aid
    else:
        ET.SubElement(var, q_("varequal"),
                      {"respident": "response1"}).text = answer_ids[correct[0]]
    ET.SubElement(cond, q_("setvar"), {"action": "Set", "varname": "SCORE"}).text = "100"

    if feedback:   # the DTD orders item children ..., resprocessing, itemfeedback
        fbk = ET.SubElement(item, q_("itemfeedback"), {"ident": "general_fb"})
        add_html(ET.SubElement(fbk, q_("flow_mat")), md(feedback))


def build_assessment(data: dict, items: list, images: Images, mode: str,
                     id_in_title: bool) -> ET.ElementTree:
    title = str(data.get("title") or "Imported Question Bank").strip()[:250]
    root = ET.Element(q_("questestinterop"), {
        f"{{{XSI_NS}}}schemaLocation":
            f"{QTI_NS} http://www.imsglobal.org/xsd/ims_qtiasiv1p2p1.xsd"})
    if mode == "objectbank":
        # <!ELEMENT objectbank (qticomment?, qtimetadata*, (section | item)+)>
        container = ET.SubElement(root, q_("objectbank"), {"ident": make_ident("bank")})
        add_field(ET.SubElement(container, q_("qtimetadata")), "bank_title", title)
    else:
        assessment = ET.SubElement(root, q_("assessment"),
                                   {"ident": make_ident("a"), "title": title})
        add_field(ET.SubElement(assessment, q_("qtimetadata")), "cc_maxattempts", "1")
        container = ET.SubElement(assessment, q_("section"), {"ident": "root_section"})
    for n, q in enumerate(items, start=1):
        build_item(container, q, n, images, id_in_title)
    return ET.ElementTree(root)


def build_manifest(image_paths: list[str]) -> ET.ElementTree:
    c = lambda tag: f"{{{CP_NS}}}{tag}"  # noqa: E731
    manifest = ET.Element(c("manifest"), {
        "identifier": make_ident("manifest_"),
        f"{{{XSI_NS}}}schemaLocation":
            f"{CP_NS} http://www.imsglobal.org/xsd/imscp_v1p1.xsd"})
    # imscp_v1p1 requires (metadata?, organizations, resources). Canvas's own
    # exports carry this block; it makes identification land on :qti.
    metadata = ET.SubElement(manifest, c("metadata"))
    ET.SubElement(metadata, c("schema")).text = "IMS Content"
    ET.SubElement(metadata, c("schemaversion")).text = "1.1.3"
    ET.SubElement(manifest, c("organizations"))
    resources = ET.SubElement(manifest, c("resources"))
    res = ET.SubElement(resources, c("resource"), {
        "identifier": "assessment_resource", "type": "imsqti_xmlv1p2",
        "href": "assessment.xml"})
    ET.SubElement(res, c("file"), {"href": "assessment.xml"})
    for k, path in enumerate(image_paths, start=1):
        href = quote(path)
        img = ET.SubElement(resources, c("resource"), {
            "identifier": f"image_resource_{k}", "type": "webcontent", "href": href})
        ET.SubElement(img, c("file"), {"href": href})
    return ET.ElementTree(manifest)


def write_package(data: dict, items: list, bank_dir: Path, output: Path,
                  mode: str = "assessment", id_in_title: bool = True,
                  image_mode: str = "files") -> Images:
    images = Images(bank_dir, image_mode)
    assessment = build_assessment(data, items, images, mode, id_in_title)
    manifest = build_manifest(sorted(images.files))
    ET.indent(assessment, space="  ")
    ET.indent(manifest, space="  ")
    with tempfile.TemporaryDirectory() as tmp:
        a_path, m_path = Path(tmp) / "assessment.xml", Path(tmp) / "imsmanifest.xml"
        ET.register_namespace("", QTI_NS)
        assessment.write(a_path, encoding="utf-8", xml_declaration=True)
        ET.register_namespace("", CP_NS)
        manifest.write(m_path, encoding="utf-8", xml_declaration=True)
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(m_path, "imsmanifest.xml")   # manifest at the zip root
            zf.write(a_path, "assessment.xml")
            for path, blob in sorted(images.files.items()):
                zf.writestr(path, blob)
    return images


# ------------------------------------------------------------- review sheet

def _repath_images(md: str, bank_dir: Path, out_dir: Path) -> str:
    def fix(m):
        src = m.group(2)
        if re.match(r"^[a-z][a-z0-9+.-]*:", src, re.I) or os.path.isabs(src):
            return m.group(0)
        rel = os.path.relpath(bank_dir / src, out_dir)
        return f"![{m.group(1)}]({Path(rel).as_posix()}"
    return re.sub(r"!\[([^\]]*)\]\(([^)\s]+)", fix, md)


def _answer_line(q: dict) -> str:
    t, a = qtype(q), q["answer"]
    if t == "true_false":
        return f"**Answer:** {'True' if a else 'False'} ✅"
    if t == "numerical":
        if "value" in a:
            tol = a.get("tolerance", 0)
            return f"**Answer:** {fmt_num(a['value'])}" + (f" ± {fmt_num(tol)}" if tol else "") + " ✅"
        return f"**Answer:** any value in [{fmt_num(a['min'])}, {fmt_num(a['max'])}] ✅"
    return ""


def write_review(data: dict, items: list, bank_path: Path, output: Path,
                 removed: int = 0):
    """Answer-keyed Markdown for human review, from the same items as the zip."""
    bank_dir, out_dir = bank_path.parent, output.parent
    fix = lambda md: _repath_images(str(md), bank_dir, out_dir)  # noqa: E731
    count = lambda key, default: tally(items, key, default)  # noqa: E731
    lines = [f"# {data.get('title', 'Question bank')}", "",
             f"{len(items)} items in the package "
             f"({count('difficulty', '?')}; {count('type', 'multiple_choice')}; "
             f"{count('status', 'draft')}; verified {count('verified', 'not recorded')})"
             + (f"; {removed} removed item(s) left out" if removed else ""), ""]

    attention = []
    for q in items:
        why = []
        if q.get("verified") != "run":
            why.append("not verified by execution"
                       + (f" ({q['verify_note']})" if q.get("verify_note") else ""))
        if not q.get("source"):
            why.append("no source")
        if why:
            attention.append(f"- **{q['id']}**: " + "; ".join(why))
    if attention:
        lines += ["## Check these first", ""] + attention + [""]

    for n, q in enumerate(items, start=1):
        t = qtype(q)
        lines.append(f"## {n}. {q['id']} — {q.get('title', '')}".rstrip(" —"))
        tags = [str(q[k]) for k in ("objective", "difficulty", "status") if k in q]
        tags += [t] if t != "multiple_choice" else []
        tags += [f"verified: {q['verified']}"] if q.get("verified") else []
        lines.append("`" + "` `".join(tags) + "`")
        if q.get("source"):
            lines.append(f"*Source: {q['source']}*")
        lines += ["", fix(q["question"]).rstrip(), ""]
        if t in ("multiple_choice", "multiple_answers"):
            correct = q["answer"] if t == "multiple_answers" else [q["answer"]]
            for j, choice in enumerate(q["choices"]):
                mark = " **✅**" if j in correct else ""
                lines.append(f"- **{chr(65 + j)}.** {fix(choice)}{mark}")
        else:
            lines.append(_answer_line(q))
        if q.get("explanation"):
            lines += ["", "> " + fix(q["explanation"]).strip().replace("\n", "\n> ")]
        lines.append("")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("bank", type=Path, help="YAML question bank")
    ap.add_argument("-o", "--output", type=Path,
                    help="QTI zip to write (default: BANK.qti.zip next to the YAML)")
    ap.add_argument("--review-md", type=Path,
                    help="also write an answer-keyed Markdown review sheet here")
    ap.add_argument("--mode", choices=("assessment", "objectbank"), default="assessment",
                    help="assessment (default): New Quizzes Item Bank > Import Content, "
                         "or a quiz in Classic. objectbank: a named Classic question bank.")
    ap.add_argument("--reviewed-only", action="store_true",
                    help="package only items with status: reviewed")
    ap.add_argument("--no-id-in-title", action="store_true",
                    help="do not prefix Canvas item titles with the item id "
                         "(sync_from_canvas.py then falls back to matching text)")
    ap.add_argument("--image-mode", choices=("files", "inline"), default="files",
                    help="files (default): bundle figures in the zip; inline: embed "
                         "them as data: URIs (fallback if a Canvas instance drops files)")
    ap.add_argument("--verbose", action="store_true", help="list every warning")
    args = ap.parse_args()

    data = load_bank(args.bank)
    errors, warnings = check_bank(data, args.bank)
    for w in (warnings if args.verbose else summarize(warnings)):
        print(f"warning: {w}", file=sys.stderr)
    if errors:
        for e in errors:
            print(f"ERROR {e}", file=sys.stderr)
        print(f"{len(errors)} error(s); nothing written. Fix them and rebuild.",
              file=sys.stderr)
        return 1

    items = active(data, args.reviewed_only)
    if not items:
        print("No items to package (all removed, or none reviewed).", file=sys.stderr)
        return 1
    removed = sum(1 for q in data["questions"] if q.get("status") == "removed")
    output = args.output or args.bank.with_suffix(".qti.zip")
    images = write_package(data, items, args.bank.parent, output, args.mode,
                           not args.no_id_in_title, args.image_mode)
    extra = f", {len(images.files)} image file(s)" if images.files else ""
    print(f"Wrote {output} ({args.mode} mode): {len(items)} items{extra}.")
    if args.review_md:
        write_review(data, items, args.bank, args.review_md, removed)
        print(f"Wrote {args.review_md} (answer-keyed review sheet).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
