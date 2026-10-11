"""Load a quiz-bank YAML file and check it against the schema.

Shared by build_qti.py, validate_bank.py and sync_from_canvas.py so that the
builder can never accept a bank the validator would reject. The schema is
documented in references/schema.md.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # sandboxes without PyYAML use the bundled pure-Python copy
    sys.path.insert(0, str(Path(__file__).resolve().parent / "_vendor"))
    import yaml

from mdrender import find_images

TYPES = ("multiple_choice", "multiple_answers", "numerical", "true_false")
DIFFICULTIES = ("easy", "medium", "hard")
STATUSES = ("draft", "reviewed", "removed")
VERIFIED = ("run", "no")
IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg",
               ".jpeg": "image/jpeg", ".gif": "image/gif"}
TEXT_FIELDS = ("question", "explanation")


ORDER = {k: i for i, k in enumerate(DIFFICULTIES + STATUSES + TYPES + VERIFIED)}


def tally(items: list, key: str, default: str) -> str:
    """'6 easy, 8 medium, 4 hard'-style counts in a fixed, readable order."""
    counts: dict[str, int] = {}
    for q in items:
        v = str(q.get(key, default))
        counts[v] = counts.get(v, 0) + 1
    keys = sorted(counts, key=lambda k: (ORDER.get(k, 99), k))
    return ", ".join(f"{counts[k]} {k}" for k in keys)


def load_bank(path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def questions(data: dict) -> list:
    return data.get("questions") or []


def qtype(q: dict) -> str:
    return q.get("type", "multiple_choice")


def active(data: dict, reviewed_only: bool = False) -> list:
    """Items that go into a package: never `removed`; optionally only `reviewed`."""
    keep = []
    for q in questions(data):
        status = q.get("status", "draft")
        if status == "removed" or (reviewed_only and status != "reviewed"):
            continue
        keep.append(q)
    return keep


def text_fields(q: dict) -> list[tuple[str, str]]:
    """(name, markdown) for every rendered field of an item."""
    out = [(f, str(q[f])) for f in TEXT_FIELDS if q.get(f) is not None]
    for j, c in enumerate(q.get("choices") or []):
        out.append((f"choice {j}", str(c)))
    return out


def _norm(text) -> str:
    return " ".join(str(text).split()).lower()


_PARA_LIST = re.compile(r"^ {0,3}(?:[-*+]|\d{1,9}[.)]) \S")


def _list_without_blank_line(md: str) -> str:
    """The first line that looks like a list item but sits right under a text
    line (so it renders as part of the paragraph), or ''."""
    in_fence = False
    prev = ""
    for line in md.split("\n"):
        if re.match(r"^ {0,3}(```|~~~)", line):
            in_fence = not in_fence
        elif (not in_fence and _PARA_LIST.match(line) and prev.strip()
              and not _PARA_LIST.match(prev) and not prev.startswith(" ")):
            return line.strip()
        prev = line
    return ""


def check_item(q: dict, loc: str, bank_dir: Path, require_source: bool):
    """Return (errors, warnings) for one item."""
    errors, warnings = [], []
    t = qtype(q)
    if t not in TYPES:
        return [f"{loc}: type must be one of {', '.join(TYPES)}"], []

    required = ["id", "question", "answer", "explanation", "objective", "difficulty"]
    missing = [f for f in required if q.get(f) is None]
    errors += [f"{loc}: missing field '{f}'" for f in missing]
    if missing:
        return errors, warnings

    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", str(q["id"])):
        errors.append(f"{loc}: id may use only letters, digits, '.', '_' and '-'")
    if q["difficulty"] not in DIFFICULTIES:
        errors.append(f"{loc}: difficulty must be one of {', '.join(DIFFICULTIES)}")
    if q.get("status", "draft") not in STATUSES:
        errors.append(f"{loc}: status must be one of {', '.join(STATUSES)}")
    points = q.get("points", 1)
    if not isinstance(points, (int, float)) or isinstance(points, bool) or points <= 0:
        errors.append(f"{loc}: points must be a positive number")
    if not isinstance(q.get("shuffle_answers", True), bool):
        errors.append(f"{loc}: shuffle_answers must be true or false")

    choices, answer = q.get("choices"), q["answer"]
    if t in ("multiple_choice", "multiple_answers"):
        if not isinstance(choices, list) or len(choices) < 3:
            errors.append(f"{loc}: needs a 'choices' list with at least 3 options")
            choices = None
        else:
            normed = [_norm(c) for c in choices]
            if len(set(normed)) != len(normed):
                errors.append(f"{loc}: duplicate choices")
            if any(not n for n in normed):
                errors.append(f"{loc}: empty choice")
    elif choices is not None:
        errors.append(f"{loc}: a {t} item has no 'choices'")

    if t == "multiple_choice" and choices:
        if not isinstance(answer, int) or isinstance(answer, bool) \
                or not 0 <= answer < len(choices):
            errors.append(f"{loc}: answer must be a zero-based index 0..{len(choices) - 1}")
    elif t == "multiple_answers" and choices:
        ok = (isinstance(answer, list) and answer
              and all(isinstance(a, int) and not isinstance(a, bool)
                      and 0 <= a < len(choices) for a in answer)
              and len(set(answer)) == len(answer))
        if not ok:
            errors.append(f"{loc}: answer must be a list of distinct indexes "
                          f"0..{len(choices) - 1}, at least one")
        elif len(answer) == len(choices):
            warnings.append(f"{loc}: every choice is correct")
    elif t == "true_false":
        if not isinstance(answer, bool):
            errors.append(f"{loc}: answer must be true or false")
    elif t == "numerical":
        errors += _check_numerical(answer, loc)

    if not q.get("source"):
        (errors if require_source else warnings).append(
            f"{loc}: no 'source' (where in the material this item comes from)")
    verified = q.get("verified")
    if verified is None:
        warnings.append(f"{loc}: 'verified' not recorded (run | no)")
    elif verified not in VERIFIED:
        errors.append(f"{loc}: verified must be 'run' or 'no'")
    elif verified == "no" and not q.get("verify_note"):
        errors.append(f"{loc}: verified: no needs a verify_note saying why")

    for name, md in text_fields(q):
        for src, alt in find_images(md):
            if not alt.strip():
                errors.append(f"{loc} ({name}): image {src!r} has no alt text")
            if re.match(r"^[a-z][a-z0-9+.-]*:", src, re.I):
                if src.lower().startswith("data:"):
                    errors.append(f"{loc} ({name}): use an image file, not a data: URI")
                else:
                    warnings.append(f"{loc} ({name}): {src!r} is linked, not bundled; "
                                    f"Canvas will load it from that site")
                continue
            ext = Path(src).suffix.lower()
            if ext not in IMAGE_TYPES:
                errors.append(f"{loc} ({name}): image {src!r} must be "
                              f"{'/'.join(sorted(IMAGE_TYPES))}")
            elif not (bank_dir / src).is_file():
                errors.append(f"{loc} ({name}): image file {src!r} not found "
                              f"(paths are relative to the YAML file)")
        line = _list_without_blank_line(md)
        if line:
            warnings.append(f"{loc} ({name}): the line {line[:40]!r} looks like a list "
                            f"item but follows a text line, so it renders as text; add a "
                            f"blank line before it for a list, or rewrap the paragraph")
    return errors, warnings


def _check_numerical(answer, loc: str) -> list[str]:
    def num(x):
        return isinstance(x, (int, float)) and not isinstance(x, bool)

    if not isinstance(answer, dict):
        return [f"{loc}: numerical answer must be {{value: .., tolerance: ..}} "
                f"or {{min: .., max: ..}}"]
    if "value" in answer:
        extra = set(answer) - {"value", "tolerance"}
        if extra or not num(answer["value"]) or not num(answer.get("tolerance", 0)) \
                or answer.get("tolerance", 0) < 0:
            return [f"{loc}: numerical answer {{value, tolerance}} needs numbers, "
                    f"tolerance >= 0"]
        return []
    if set(answer) == {"min", "max"} and num(answer["min"]) and num(answer["max"]) \
            and answer["min"] <= answer["max"]:
        return []
    return [f"{loc}: numerical answer must be {{value: .., tolerance: ..}} "
            f"or {{min: .., max: ..}} with min <= max"]


def summarize(warnings: list[str], show: int = 6) -> list[str]:
    """Group 'file:id: message' warnings by message: one line per kind."""
    groups: dict[str, list[str]] = {}
    for w in warnings:
        m = re.match(r"^[^:]+:([^: ]+)(?: \(([^)]*)\))?: (.*)$", w)
        if not m:
            groups.setdefault(w, [])
            continue
        groups.setdefault(m.group(3), []).append(m.group(1))
    out = []
    for msg, ids in groups.items():
        if not ids:
            out.append(msg)
            continue
        more = f", ... (+{len(ids) - show})" if len(ids) > show else ""
        out.append(f"{len(ids)} item(s): {msg} [{', '.join(ids[:show])}{more}]")
    return out


def check_bank(data, path, seen_ids=None, require_source=False):
    """Return (errors, warnings) for a whole bank file."""
    path = Path(path)
    if seen_ids is None:
        seen_ids = {}
    if not isinstance(data, dict):
        return [f"{path}: top level must be a mapping with 'title' and 'questions'"], []
    qs = data.get("questions")
    if not isinstance(qs, list) or not qs:
        return [f"{path}: needs a non-empty 'questions:' list"], []
    errors, warnings = [], []
    if not data.get("title"):
        warnings.append(f"{path}: no 'title' (Canvas shows it as the bank or quiz name)")

    stems = {}
    mc_keys = []
    for i, q in enumerate(qs):
        if not isinstance(q, dict):
            errors.append(f"{path}: item #{i + 1} is not a mapping")
            continue
        qid = q.get("id", f"item#{i + 1}")
        loc = f"{path.name}:{qid}"
        if qid in seen_ids:
            errors.append(f"{loc}: duplicate id (also in {seen_ids[qid]})")
        seen_ids[qid] = path.name
        if q.get("status") == "removed":
            continue   # kept only to reserve its id; never built
        e, w = check_item(q, loc, path.parent, require_source)
        errors += e
        warnings += w
        if q.get("question") is not None:
            stem = _norm(q["question"])
            if stem in stems:
                errors.append(f"{loc}: same question text as {stems[stem]}")
            stems[stem] = qid
        if qtype(q) == "multiple_choice" and isinstance(q.get("answer"), int):
            mc_keys.append(q["answer"])
    checks = sorted(path.parent.glob(path.stem + ".checks.*"))
    sections = set()
    for c in checks:
        sections |= set(re.findall(r"^\s*#+\s*-{2,}\s*([A-Za-z0-9._-]+)",
                                   c.read_text(encoding="utf-8", errors="replace"), re.M))
    claimed = [str(q.get("id")) for q in qs if isinstance(q, dict)
               and q.get("verified") == "run" and q.get("status") != "removed"]
    if claimed and not checks:
        warnings.append(f"{path.name}: {len(claimed)} item(s) say verified: run, but there "
                        f"is no {path.stem}.checks.R/.py next to the bank")
    elif checks:
        for qid in claimed:
            if qid not in sections:
                warnings.append(f"{path.name}:{qid}: verified: run, but "
                                f"{' / '.join(c.name for c in checks)} has no "
                                f"'# ---- {qid}' section")
    if len(mc_keys) >= 10 and len(set(mc_keys)) == 1:
        errors.append(f"{path.name}: every multiple-choice key is index {mc_keys[0]}; "
                      f"spread the correct answers across positions")
    return errors, warnings
