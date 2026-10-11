#!/usr/bin/env python3
"""Build a bank and package it as two downloads: the Canvas file and the rest.

Usage:
  python3 package_bank.py BANK.yaml --out OUTDIR [--notes NOTES.md]
                          [--mode assessment|objectbank] [--image-mode files|inline]
                          [--reviewed-only]

Writes, in OUTDIR:
  <bank>.qti.zip                  import this into Canvas
  <bank>-source-and-review.zip    everything else, in a folder <bank>/:
                                  the YAML (source of truth), the answer-keyed
                                  review sheet, the checks files, the figures
                                  the items use, and a README
and also <bank>.review.md next to the YAML.

The bank is validated first and the package is checked against the YAML
after the build; any error stops before anything is delivered. The bundle
unzips into a folder whose YAML rebuilds as is (figure paths are kept), and
holds no copy of the skill's scripts. --notes adds the agent's hand-over notes
(coverage table, judgment calls) to the README.
"""
from __future__ import annotations

import argparse
import datetime
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bank import active, check_bank, find_images, load_bank, qtype, summarize, tally, text_fields  # noqa: E402
from build_qti import write_package, write_review  # noqa: E402
from validate_bank import check_package  # noqa: E402


def bank_files(data: dict, bank_path: Path, review: Path) -> list[tuple[Path, str]]:
    """(file, path inside the bundle folder) for everything but the QTI."""
    out = [(bank_path, bank_path.name), (review, review.name)]
    for checks in sorted(bank_path.parent.glob(bank_path.stem + ".checks.*")):
        out.append((checks, checks.name))
    seen = set()
    for q in data.get("questions") or []:
        for _, md in text_fields(q):
            for src, _ in find_images(md):
                if ":" in src.split("/")[0] or src in seen:
                    continue
                seen.add(src)
                out.append((bank_path.parent / src, Path(src).as_posix()))
    return out


def readme(data: dict, items: list, stem: str, files: list[str], notes: str) -> str:
    unverified = [q for q in items if q.get("verified") != "run"]
    lines = [
        f"# {data.get('title', stem)}",
        "",
        f"Built {datetime.date.today().isoformat()} by the canvas-quizbank skill.",
        "",
        "## The two downloads",
        "",
        f"- `{stem}.qti.zip`: import this into Canvas (see below).",
        f"- `{stem}-source-and-review.zip`: this folder. Keep it: the YAML is the "
        f"source for every later change, rebuild and sync.",
        "",
        "## Files in this folder",
        "",
    ]
    describe = {
        f"{stem}.yaml": "the bank; edit this, never the QTI file",
        f"{stem}.review.md": "every item with its answer marked; unverified items first",
        "README.md": "this file",
    }
    for f in files:
        if f.startswith("figures/") or "/" in f:
            continue
        what = describe.get(f, "the code that verified the items (one section per item)"
                            if ".checks." in f else "")
        lines.append(f"- `{f}`" + (f": {what}" if what else ""))
    if any("/" in f for f in files):
        lines.append("- `figures/`: images used by the items")
    lines += [
        "",
        "## Summary",
        "",
        f"- {len(items)} items: {tally(items, 'difficulty', '?')}",
        f"- types: {tally(items, 'type', 'multiple_choice')}",
        f"- verified by running code: {sum(q.get('verified') == 'run' for q in items)} "
        f"of {len(items)}",
    ]
    if unverified:
        lines += ["", "Not verified by execution (check these first):", ""]
        lines += [f"- {q['id']}: {q.get('verify_note', 'no reason recorded')}"
                  for q in unverified]
    if notes.strip():
        lines += ["", "## Notes", "", notes.strip()]
    lines += [
        "",
        "## Import into Canvas",
        "",
        "- New Quizzes: open **Item Banks**, choose **+ Bank** to create a new bank, "
        "open it, then **⋮ → Import Content** and upload the `.qti.zip`.",
        "- Classic Quizzes: **Settings → Import Course Content → QTI .zip file**.",
        "- Each item's title starts with its id; its feedback ends with its source.",
        "",
        "## After you review it in Canvas",
        "",
        "Delete the items that do not fit, then give the agent (with the canvas-quizbank "
        "skill) this folder's YAML plus a Canvas export of what is left, or a text file of "
        "the remaining titles. It marks kept items `reviewed` and deleted ones `removed`, "
        "so they never come back in a rebuild.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("bank", type=Path)
    ap.add_argument("--out", type=Path, required=True,
                    help="folder for the two downloads (e.g. the chat's download folder)")
    ap.add_argument("--notes", type=Path, help="Markdown notes to add to the README")
    ap.add_argument("--mode", choices=("assessment", "objectbank"), default="assessment")
    ap.add_argument("--image-mode", choices=("files", "inline"), default="files")
    ap.add_argument("--reviewed-only", action="store_true")
    a = ap.parse_args()

    data = load_bank(a.bank)
    errors, warnings = check_bank(data, a.bank)
    for w in summarize(warnings):
        print(f"warning: {w}", file=sys.stderr)
    if errors:
        for e in errors:
            print(f"ERROR {e}", file=sys.stderr)
        print("Nothing packaged. Fix the errors and run again.", file=sys.stderr)
        return 1
    items = active(data, a.reviewed_only)
    if not items:
        print("No items to package.", file=sys.stderr)
        return 1

    stem = a.bank.stem
    a.out.mkdir(parents=True, exist_ok=True)
    qti = a.out / f"{stem}.qti.zip"
    write_package(data, items, a.bank.parent, qti, a.mode, True, a.image_mode)
    problems = check_package(qti, items)
    if problems:
        qti.unlink()
        for p in problems:
            print(f"ERROR {p}", file=sys.stderr)
        return 1
    review = a.bank.with_suffix(".review.md")
    removed = sum(1 for q in data["questions"] if q.get("status") == "removed")
    write_review(data, items, a.bank, review, removed)

    files = bank_files(data, a.bank, review)
    names = [inner for _, inner in files] + ["README.md"]
    notes = a.notes.read_text(encoding="utf-8") if a.notes else ""
    bundle = a.out / f"{stem}-source-and-review.zip"
    with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path, inner in files:
            zf.write(path, f"{stem}/{inner}")
        zf.writestr(f"{stem}/README.md", readme(data, items, stem, names, notes))

    types = ", ".join(sorted({qtype(q) for q in items}))
    print(f"{qti}  <- import into Canvas ({len(items)} items: {types}; package checked)")
    print(f"{bundle}  <- source and review ({len(files) + 1} files: YAML, review sheet, "
          f"checks, figures, README)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
