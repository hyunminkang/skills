#!/usr/bin/env python3
"""Turn class material into one numbered outline (and its images) for drafting.

Usage:
  python3 extract_material.py INPUT [INPUT ...] -o OUTDIR [--pages-png] [--dpi 110]
                              [--pdf-images]

Writes OUTDIR/outline.md and OUTDIR/media/<input-stem>/... . The outline
numbers every unit (Slide N, Page N, Cell N, Frame N or a heading) so that
items can cite it as their `source`, and lists each unit's speaker notes and
images in place.

Standard library only. Supported inputs:
  .pptx         slide text (titles, bullets with levels, tables), speaker
                notes, embedded pictures, hidden-slide flags
  .docx         headings, paragraphs, list items, tables, embedded pictures;
                equations become their plain text, marked [math: ...]
  .ipynb        markdown cells, code cells with their language, text outputs
                and PNG/JPEG outputs
  .md .Rmd .qmd Markdown as is; Marp decks (marp: true) split into slides,
                with <!-- speaker notes --> listed as notes
  .html .htm    text with headings, code blocks, lists and tables; KaTeX and
                MathJax v2 math recovered as $TeX$; data: and local images
  .tex          LaTeX as is, split by Beamer frame or by \\section
  .pdf          per-page text with pdftotext (Poppler) or the pypdf module
                when either is installed; otherwise a note to read the PDF
                directly (models read PDFs natively). --pages-png renders
                pages with pdftoppm for cropping figures; --pdf-images also
                pulls embedded pictures with pdfimages.
  .txt          as is
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import shutil
import subprocess
import sys
import zipfile
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
import xml.etree.ElementTree as ET

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}
R_ID = f"{{{NS['r']}}}id"
R_EMBED = f"{{{NS['r']}}}embed"


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


class Out:
    """Collects outline text and copies media for one input file."""

    def __init__(self, outdir: Path, src: Path):
        self.outdir, self.src = outdir, src
        self.media = outdir / "media" / re.sub(r"[^\w.-]", "_", src.stem)
        self.lines: list[str] = []
        self.n_media = 0

    def add(self, *lines: str):
        self.lines.extend(lines)

    def save(self, name: str, data: bytes) -> str:
        self.media.mkdir(parents=True, exist_ok=True)
        name = re.sub(r"[^\w.-]", "_", name)
        (self.media / name).write_bytes(data)
        self.n_media += 1
        return (self.media / name).relative_to(self.outdir).as_posix()


# --------------------------------------------------------------------- OOXML

def _rels(zf: zipfile.ZipFile, part: str) -> dict[str, tuple[str, str]]:
    """rId -> (type suffix, absolute part name) for an OOXML part."""
    p = PurePosixPath(part)
    rel_path = str(p.parent / "_rels" / (p.name + ".rels"))
    if rel_path not in zf.namelist():
        return {}
    out = {}
    for rel in ET.fromstring(zf.read(rel_path)):
        target = rel.get("Target", "")
        if rel.get("TargetMode") == "External":
            continue
        full = PurePosixPath(p.parent, target)
        parts = []
        for seg in full.parts:
            if seg == "..":
                parts.pop()
            elif seg != ".":
                parts.append(seg)
        out[rel.get("Id")] = (rel.get("Type", "").rsplit("/", 1)[-1], "/".join(parts))
    return out


def _para_text(p) -> str:
    bits = []
    for el in p.iter():
        name = local(el.tag)
        if name == "t" and el.text:
            bits.append(el.text)
        elif name == "br":
            bits.append("\n")
        elif name == "tab":
            bits.append("\t")
    return "".join(bits).strip()


def extract_pptx(src: Path, out: Out):
    zf = zipfile.ZipFile(src)
    pres = ET.fromstring(zf.read("ppt/presentation.xml"))
    rels = _rels(zf, "ppt/presentation.xml")
    slides = [rels[s.get(R_ID)][1] for s in pres.iter(f"{{{NS['p']}}}sldId")
              if s.get(R_ID) in rels]
    out.add(f"# Source: {src.name} (PowerPoint, {len(slides)} slides)", "")
    for n, part in enumerate(slides, start=1):
        root = ET.fromstring(zf.read(part))
        title, body = "", []
        for el in root.iter():
            tag = local(el.tag)
            if tag == "sp":
                ph = el.find(".//p:nvPr/p:ph", NS)
                kind = ph.get("type", "body") if ph is not None else ""
                paras = el.findall(".//a:p", NS)
                if kind in ("title", "ctrTitle") and not title:
                    title = " ".join(_para_text(p) for p in paras if _para_text(p))
                    continue
                if kind in ("sldNum", "dt", "ftr", "hdr"):
                    continue
                for p in paras:
                    text = _para_text(p)
                    if not text:
                        continue
                    ppr = p.find("a:pPr", NS)
                    lvl = int(ppr.get("lvl", "0")) if ppr is not None else 0
                    body.append("  " * lvl + "- " + text.replace("\n", " "))
            elif tag == "tbl":
                for tr in el.findall("a:tr", NS):
                    cells = [" ".join(_para_text(p) for p in tc.findall(".//a:p", NS))
                             for tc in tr.findall("a:tc", NS)]
                    body.append("| " + " | ".join(cells) + " |")
        hidden = " (hidden)" if root.get("show") == "0" else ""
        out.add(f"## Slide {n}{' — ' + title if title else ''}{hidden}", "")
        out.add(*(body or ["(no text)"]), "")
        slide_rels = _rels(zf, part)
        notes = [t for k, t in slide_rels.values() if k == "notesSlide"]
        if notes:
            nroot = ET.fromstring(zf.read(notes[0]))
            ntext = []
            for sp in nroot.iter(f"{{{NS['p']}}}sp"):
                ph = sp.find(".//p:nvPr/p:ph", NS)
                if ph is not None and ph.get("type") in ("sldNum", "sldImg", "hdr", "ftr", "dt"):
                    continue
                ntext += [_para_text(p) for p in sp.findall(".//a:p", NS) if _para_text(p)]
            if ntext:
                out.add("Notes:", *("> " + t for t in ntext), "")
        pics = []
        for blip in root.iter(f"{{{NS['a']}}}blip"):
            rid = blip.get(R_EMBED)
            if rid in slide_rels and slide_rels[rid][1] in zf.namelist():
                target = slide_rels[rid][1]
                pics.append(out.save(f"slide{n}_{PurePosixPath(target).name}", zf.read(target)))
        if pics:
            out.add("Images: " + ", ".join(dict.fromkeys(pics)), "")


def extract_docx(src: Path, out: Out):
    zf = zipfile.ZipFile(src)
    root = ET.fromstring(zf.read("word/document.xml"))
    rels = _rels(zf, "word/document.xml")
    out.add(f"# Source: {src.name} (Word)", "")
    body = root.find("w:body", NS)
    pic = 0
    for block in body:
        tag = local(block.tag)
        if tag == "p":
            style = block.find("w:pPr/w:pStyle", NS)
            sval = style.get(f"{{{NS['w']}}}val", "") if style is not None else ""
            text = []
            for el in block.iter():
                name = local(el.tag)
                if name == "oMath":
                    text.append(" [math: " + "".join(t.text or "" for t in el.iter(f"{{{NS['m']}}}t")) + "] ")
                elif name == "t" and el.tag == f"{{{NS['w']}}}t" and el.text:
                    text.append(el.text)
                elif name == "tab":
                    text.append("\t")
                elif name in ("br", "cr"):
                    text.append("\n")
                elif name == "blip" and el.get(R_EMBED) in rels:
                    target = rels[el.get(R_EMBED)][1]
                    if target in zf.namelist():
                        pic += 1
                        rel = out.save(f"figure{pic}_{PurePosixPath(target).name}", zf.read(target))
                        text.append(f" ![figure {pic}]({rel}) ")
            line = "".join(text).strip()   # equations use m:t, so no doubling
            if not line:
                continue
            m = re.match(r"(?i)heading\s*(\d)|title", sval)
            if m:
                level = int(m.group(1)) if m.group(1) else 1
                out.add("", "#" * min(level + 1, 6) + " " + line, "")
            elif (block.find("w:pPr/w:numPr", NS) is not None
                  or sval.lower().startswith("list")):
                out.add("- " + line)
            else:
                out.add(line, "")
        elif tag == "tbl":
            for tr in block.findall("w:tr", NS):
                cells = [" ".join(_para_text(p) for p in tc.findall(".//w:p", NS))
                         for tc in tr.findall("w:tc", NS)]
                out.add("| " + " | ".join(cells) + " |")
            out.add("")


# ------------------------------------------------------------------ notebook

def extract_ipynb(src: Path, out: Out):
    nb = json.loads(src.read_text(encoding="utf-8"))
    meta = nb.get("metadata", {})
    lang = (meta.get("kernelspec", {}).get("language")
            or meta.get("language_info", {}).get("name") or "")
    cells = nb.get("cells", [])
    out.add(f"# Source: {src.name} (notebook, {len(cells)} cells, {lang or 'unknown'} kernel)", "")
    join = lambda v: "".join(v) if isinstance(v, list) else str(v)  # noqa: E731
    for n, cell in enumerate(cells, start=1):
        kind = cell.get("cell_type")
        text = join(cell.get("source", "")).rstrip()
        if not text:
            continue
        out.add(f"## Cell {n} ({kind})", "")
        if kind == "code":
            out.add(f"```{lang}", text, "```", "")
            for k, o in enumerate(cell.get("outputs", []), start=1):
                if o.get("output_type") == "stream":
                    out.add("Output:", "```", join(o.get("text", "")).rstrip(), "```", "")
                data = o.get("data", {})
                for mime, ext in (("image/png", "png"), ("image/jpeg", "jpg")):
                    if mime in data:
                        rel = out.save(f"cell{n}_{k}.{ext}", base64.b64decode(join(data[mime])))
                        out.add(f"Image: {rel}", "")
                if "text/plain" in data and not any(m in data for m in ("image/png", "image/jpeg")):
                    out.add("Output:", "```", join(data["text/plain"]).rstrip(), "```", "")
                if o.get("output_type") == "error":
                    out.add(f"Error: {o.get('ename')}: {o.get('evalue')}", "")
        else:
            out.add(text, "")


# ---------------------------------------------------------- markdown / tex

def extract_markdown(src: Path, out: Out):
    text = src.read_text(encoding="utf-8")
    front = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if front and re.search(r"^marp:\s*true", front.group(1), re.M):
        body = text[front.end():]
        slides, cur, fence = [], [], False
        for line in body.split("\n"):
            if re.match(r"^\s*(```|~~~)", line):
                fence = not fence
            if line.strip() == "---" and not fence:
                slides.append(cur)
                cur = []
            else:
                cur.append(line)
        slides.append(cur)
        out.add(f"# Source: {src.name} (Marp deck, {len(slides)} slides)", "")
        for n, lines in enumerate(slides, start=1):
            chunk = "\n".join(lines)
            notes = [c.strip() for c in re.findall(r"<!--(.*?)-->", chunk, re.S)
                     if not re.match(r"^\s*_?[\w-]+\s*:", c)]
            chunk = re.sub(r"<!--.*?-->", "", chunk, flags=re.S).strip()
            title = next((ln.lstrip("# ").strip() for ln in chunk.split("\n")
                          if ln.startswith("#")), "")
            out.add(f"## Slide {n}{' — ' + title if title else ''}", "", chunk or "(no text)", "")
            if notes:
                out.add("Notes:", *("> " + ln for c in notes for ln in c.split("\n")), "")
        return
    out.add(f"# Source: {src.name} (Markdown)", "", text, "")


def extract_tex(src: Path, out: Out):
    text = src.read_text(encoding="utf-8", errors="replace")
    frames = re.findall(r"\\begin\{frame\}(.*?)\\end\{frame\}", text, re.S)
    if frames:
        out.add(f"# Source: {src.name} (Beamer, {len(frames)} frames)", "")
        for n, body in enumerate(frames, start=1):
            m = re.search(r"\\frametitle\{([^}]*)\}|^\s*\{([^}]*)\}", body)
            title = (m.group(1) or m.group(2)) if m else ""
            out.add(f"## Frame {n}{' — ' + title if title else ''}", "", body.strip(), "")
        return
    out.add(f"# Source: {src.name} (LaTeX)", "", text, "")


# ---------------------------------------------------------------------- html

class _HTML(HTMLParser):
    BLOCK = {"p", "div", "section", "article", "li", "tr", "br", "pre", "h1", "h2",
             "h3", "h4", "h5", "h6", "table", "ul", "ol", "blockquote", "figure"}

    def __init__(self, out: Out, base: Path):
        super().__init__(convert_charrefs=True)
        self.out, self.base = out, base
        self.buf: list[str] = []
        self.skip = 0          # inside script/style
        self.katex = 0         # inside a KaTeX span: only its annotation counts
        self.tex: list[str] = []
        self.in_annotation = False
        self.mathjax = None    # display mode of a MathJax v2 <script type="math/tex">
        self.pre = False
        self.n_img = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class") or ""
        if self.katex:
            if tag == "span":
                self.katex += 1
            if tag == "annotation" and "tex" in (a.get("encoding") or ""):
                self.in_annotation = True
            return
        if tag == "span" and re.search(r"\bkatex\b", cls) and "katex-" not in cls.split()[0]:
            self.katex, self.tex = 1, []
            return
        if tag == "script" and (a.get("type") or "").startswith("math/tex"):
            self.mathjax = "mode=display" in (a.get("type") or "")
            return
        if tag in ("script", "style", "head", "nav"):
            self.skip += 1
            return
        if tag in self.BLOCK:
            self.buf.append("\n")
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.buf.append("#" * int(tag[1]) + " ")
        elif tag == "li":
            self.buf.append("- ")
        elif tag == "pre":
            self.pre = True
            self.buf.append("```\n")
        elif tag in ("td", "th"):
            self.buf.append(" | ")
        elif tag == "img":
            self.buf.append(self._image(a))

    def _image(self, a) -> str:
        src, alt = a.get("src") or "", a.get("alt") or "image"
        m = re.match(r"data:image/(png|jpe?g|gif|svg\+xml);base64,(.*)", src, re.S)
        rel = None
        if m:
            self.n_img += 1
            ext = {"svg+xml": "svg", "jpeg": "jpg"}.get(m.group(1), m.group(1))
            rel = self.out.save(f"img{self.n_img}.{ext}", base64.b64decode(m.group(2)))
        elif src and not re.match(r"^[a-z]+:", src) and (self.base / src).is_file():
            self.n_img += 1
            p = self.base / src
            rel = self.out.save(f"img{self.n_img}_{p.name}", p.read_bytes())
        return f" ![{alt}]({rel or src}) "

    def handle_endtag(self, tag):
        if self.katex:
            if tag == "annotation":
                self.in_annotation = False
            if tag == "span":
                self.katex -= 1
                if not self.katex:
                    self.buf.append(" $" + "".join(self.tex).strip() + "$ ")
            return
        if tag in ("script", "style", "head", "nav"):
            self.skip = max(0, self.skip - 1)
            return
        if tag == "pre":
            self.pre = False
            self.buf.append("\n```\n")
        elif tag in self.BLOCK:
            self.buf.append("\n")

    def handle_data(self, data):
        if self.katex:
            if self.in_annotation:
                self.tex.append(data)
            return
        if self.mathjax is not None:
            d = "$$" if self.mathjax else "$"
            self.buf.append(f" {d}{data.strip()}{d} ")
            self.mathjax = None
            return
        if self.skip:
            return
        self.buf.append(data if self.pre else re.sub(r"\s+", " ", data))


def extract_html(src: Path, out: Out):
    parser = _HTML(out, src.parent)
    parser.feed(src.read_text(encoding="utf-8", errors="replace"))
    text = "".join(parser.buf)
    text = "\n".join(ln.rstrip() for ln in text.split("\n"))
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    out.add(f"# Source: {src.name} (HTML)", "", text, "")


# ----------------------------------------------------------------------- pdf

def _pdf_pictures(src: Path) -> dict[int, int]:
    """Page -> number of real pictures (pdfimages -list), ignoring masks,
    icons and flat fills (under 200x100 px or under 1 KB stored). Empty when
    pdfimages is not installed."""
    if not shutil.which("pdfimages"):
        return {}
    r = subprocess.run(["pdfimages", "-list", str(src)], capture_output=True, text=True)
    scale = {"B": 1, "K": 1024, "M": 1024 ** 2, "G": 1024 ** 3}
    counts: dict[int, int] = {}
    for line in r.stdout.splitlines()[2:]:
        f = line.split()
        if len(f) < 15 or not f[0].isdigit() or f[2] != "image":
            continue
        m = re.match(r"([\d.]+)([BKMG])$", f[14])
        size = float(m.group(1)) * scale[m.group(2)] if m else 0
        if int(f[3]) >= 200 and int(f[4]) >= 100 and size >= 1024:
            counts[int(f[0])] = counts.get(int(f[0]), 0) + 1
    return counts


def extract_pdf(src: Path, out: Out, pages_png: bool, dpi: int, pdf_images: bool):
    pages = None
    if shutil.which("pdftotext"):
        r = subprocess.run(["pdftotext", "-layout", str(src), "-"],
                           capture_output=True, text=True)
        if r.returncode == 0:
            pages = r.stdout.split("\f")
            if pages and not pages[-1].strip():
                pages.pop()
    if pages is None:
        try:
            import pypdf  # type: ignore
            pages = [pg.extract_text() or "" for pg in pypdf.PdfReader(str(src)).pages]
        except Exception:
            pages = None
    if pages is None:
        out.add(f"# Source: {src.name} (PDF)", "",
                "No PDF text extractor here (pdftotext or pypdf). Read the PDF directly; "
                "cite pages as 'p. N'.", "")
    else:
        pictures = _pdf_pictures(src)
        out.add(f"# Source: {src.name} (PDF, {len(pages)} pages)", "")
        if pictures:
            out.add(f"{sum(pictures.values())} picture(s) on {len(pictures)} page(s) are not "
                    f"in this text (diagrams, or code and formulas shown as images). "
                    f"View those pages directly; they are flagged below.", "")
        for n, text in enumerate(pages, start=1):
            text = "\n".join(ln.rstrip() for ln in text.split("\n")).strip()
            flag = (f" [{pictures[n]} picture(s) not in the text: view the page]"
                    if n in pictures else "")
            out.add(f"## Page {n}{flag}", "",
                    text or "(no text layer: a scanned page or a figure)", "")
        if sum(len(p.strip()) for p in pages) < 40 * max(1, len(pages)):
            out.add("Note: little text was found; the PDF may be scanned. Read it directly.", "")
    if pages_png:
        if shutil.which("pdftoppm"):
            out.media.mkdir(parents=True, exist_ok=True)
            subprocess.run(["pdftoppm", "-r", str(dpi), "-png", str(src),
                            str(out.media / "page")], check=False)
            made = sorted(out.media.glob("page-*.png"))
            out.n_media += len(made)
            out.add(f"Page images ({len(made)}): media/{out.media.name}/page-N.png; crop a "
                    f"figure with: pdftoppm -r {dpi} -png -f N -l N -x X -y Y -W W -H H "
                    f"{src.name} out", "")
        else:
            out.add("Page images: pdftoppm not available.", "")
    if pdf_images and shutil.which("pdfimages"):
        out.media.mkdir(parents=True, exist_ok=True)
        subprocess.run(["pdfimages", "-png", "-p", str(src), str(out.media / "img")], check=False)
        made = sorted(out.media.glob("img-*.png"))
        out.n_media += len(made)
        out.add(f"Embedded images ({len(made)}): media/{out.media.name}/img-PAGE-NNN.png", "")


# ---------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("inputs", nargs="+", type=Path)
    ap.add_argument("-o", "--outdir", type=Path, default=Path("extracted"),
                    help="folder for outline.md and media/ (default: extracted)")
    ap.add_argument("--pages-png", action="store_true",
                    help="render PDF pages to PNG (pdftoppm) for cropping figures")
    ap.add_argument("--dpi", type=int, default=110,
                    help="resolution for --pages-png (default: 110)")
    ap.add_argument("--pdf-images", action="store_true",
                    help="also extract pictures embedded in PDFs (pdfimages)")
    a = ap.parse_args()

    a.outdir.mkdir(parents=True, exist_ok=True)
    sections = []
    for src in a.inputs:
        out = Out(a.outdir, src)
        ext = src.suffix.lower()
        try:
            if ext == ".pptx":
                extract_pptx(src, out)
            elif ext == ".docx":
                extract_docx(src, out)
            elif ext == ".ipynb":
                extract_ipynb(src, out)
            elif ext in (".md", ".markdown", ".rmd", ".qmd"):
                extract_markdown(src, out)
            elif ext in (".html", ".htm"):
                extract_html(src, out)
            elif ext == ".tex":
                extract_tex(src, out)
            elif ext == ".pdf":
                extract_pdf(src, out, a.pages_png, a.dpi, a.pdf_images)
            elif ext == ".txt":
                out.add(f"# Source: {src.name}", "", src.read_text(encoding="utf-8"), "")
            else:
                out.add(f"# Source: {src.name}", "",
                        f"Unsupported type {ext}; read it directly "
                        f"(old .ppt/.doc: convert to .pptx/.docx or PDF first).", "")
        except (zipfile.BadZipFile, KeyError, ET.ParseError, json.JSONDecodeError) as exc:
            out.add(f"# Source: {src.name}", "", f"Could not parse ({exc}); read it directly.", "")
        text = "\n".join(out.lines)
        sections.append(text)
        units = len(re.findall(r"^## ", text, re.M))
        print(f"{src.name}: {units} numbered unit(s) (slides, pages, cells or sections), "
              f"{len(text):,} characters, {out.n_media} media file(s)")
    (a.outdir / "outline.md").write_text("\n\n".join(sections).rstrip() + "\n", encoding="utf-8")
    print(f"Wrote {a.outdir / 'outline.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
