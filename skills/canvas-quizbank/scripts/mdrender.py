#!/usr/bin/env python3
"""Markdown + TeX math -> HTML for Canvas QTI, using only the standard library.

Supported subset (everything a quiz item needs; see references/schema.md):

  blocks  paragraphs; fenced code (``` or ~~~, optional language such as
          ```r, ```{r} or ```{.python}); indented code; pipe tables with
          alignment; bullet and ordered lists (nested); blockquotes; ATX and
          setext headings; horizontal rules
  inline  `code`, *em*, _em_, **strong**, __strong__, ~~strike~~, ^sup^,
          ~sub~, [links](url), ![alt text](image.png), <https://autolinks>,
          backslash escapes, hard breaks (two trailing spaces or a trailing
          backslash), and a few raw tags (br, sup, sub, kbd, u, mark, small)
  math    $inline$ and $$display$$ TeX, emitted as Canvas equation images
          (/equation_images/...), the representation Canvas's own editor
          produces. Never MathML: New Quizzes walks the <math> subtree and
          renders the literal text "Unexpected text node: '<your latex>'".
  typing  outside code and math, straight quotes become curly quotes and
          -- --- ... become an en dash, an em dash and an ellipsis.

The rules follow Pandoc's Markdown where authors would notice a difference:
a list, table, blockquote or heading must follow a blank line, so a wrapped
line that happens to start with "3." or "- " stays part of its paragraph,
while a fenced code block may follow a paragraph directly. A "$" opens math
only when the next character is not a space, and closes it only when the
previous character is not a space and the next is not a digit, so
"$5 and $20,000" stays text.
"""
from __future__ import annotations

import html as _html
import re
from typing import Callable, Optional
from urllib.parse import quote

__all__ = ["render", "render_inline", "equation_image", "find_images"]

ImageHook = Callable[[str, str], str]   # (src, alt) -> src to emit

_PUNCT = set("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")

_FENCE = re.compile(r"^( {0,3})(`{3,}|~{3,})[ \t]*(.*?)[ \t]*$")
_ATX = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$")
_SETEXT = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")
_HR = re.compile(r"^ {0,3}([-*_])(?:[ \t]*\1){2,}[ \t]*$")
_BQ = re.compile(r"^ {0,3}> ?(.*)$")
_BULLET = re.compile(r"^( {0,3})([-*+])([ \t]+(.*))?$")
_ORDERED = re.compile(r"^( {0,3})(\d{1,9})([.)])([ \t]+(.*))?$")
_TABLE_SEP = re.compile(
    r"^ {0,3}\|?[ \t]*:?-+:?[ \t]*(?:\|[ \t]*:?-+:?[ \t]*)*\|?[ \t]*$")
_RAW_TAG = re.compile(
    r"</?(?:br|sup|sub|kbd|u|mark|small)\b[^<>]*?/?>", re.I)
_AUTOLINK = re.compile(r"<((?:https?|ftp)://[^\s<>]+|mailto:[^\s<>]+)>")
_ENTITY = re.compile(r"&(?:#\d+|#[xX][0-9a-fA-F]+|[A-Za-z][A-Za-z0-9]*);")
_SLOT = re.compile("\x00(\\d+)\x01")


def _esc(text: str) -> str:
    return _html.escape(text, quote=False)


def _attr(text: str) -> str:
    return _html.escape(text, quote=True)


def _encode_uri_component(text: str) -> str:
    """Match JavaScript's encodeURIComponent, which Canvas's editor uses."""
    return quote(text, safe="-_.!~*'()")


def equation_image(latex: str) -> str:
    """Canvas's native equation representation.

    Canvas stores the LaTeX double-escaped in the image path and unescapes it
    once when serving /equation_images/:id, so it is encoded twice here. The
    path is relative, so it resolves on whichever Canvas instance imports it.
    """
    latex = latex.strip()
    src = "/equation_images/" + _encode_uri_component(
        _encode_uri_component(latex))
    esc = _attr(latex)
    return (f'<img class="equation_image" title="{esc}" src="{src}" '
            f'alt="LaTeX: {esc}" data-equation-content="{esc}" />')


# ------------------------------------------------------------------ inline

def _find_code_close(text: str, start: int, run: int) -> int:
    """Index of a closing backtick run of exactly `run` ticks, or -1."""
    j = start
    while True:
        j = text.find("`" * run, j)
        if j == -1:
            return -1
        k = j + run
        if (j == 0 or text[j - 1] != "`") and (k >= len(text) or text[k] != "`"):
            return j
        while k < len(text) and text[k] == "`":
            k += 1
        j = k


def _find_inline_math_close(text: str, start: int) -> int:
    """Closing '$' for inline math opened just before `start`, or -1.

    Pandoc's rule: the first unescaped '$' closes the math, provided it is
    preceded by a non-space and not followed by a digit; otherwise the
    opening '$' is literal text.
    """
    k = start
    while k < len(text):
        ch = text[k]
        if ch == "\\":
            k += 2
            continue
        if ch == "\n" and text.startswith("\n\n", k):
            return -1
        if ch == "$":
            if text[k - 1].isspace() or (k + 1 < len(text) and text[k + 1].isdigit()):
                return -1
            return k
        k += 1
    return -1


def _match_bracket(text: str, i: int, open_ch: str, close_ch: str) -> int:
    depth = 0
    j = i
    while j < len(text):
        ch = text[j]
        if ch == "\\":
            j += 2
            continue
        if ch == "`":
            run = len(text[j:]) - len(text[j:].lstrip("`"))
            close = _find_code_close(text, j + run, run)
            j = (close + run) if close != -1 else j + run
            continue
        if ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return j
        j += 1
    return -1


_LINK_DEST = re.compile(r'\s*<?([^\s<>]*)>?(?:\s+"([^"]*)")?\s*$', re.S)


def _parse_link(text: str, i: int):
    """Parse [label](dest "title") starting at text[i] == '['."""
    close = _match_bracket(text, i, "[", "]")
    if close == -1 or not text.startswith("(", close + 1):
        return None
    end = _match_bracket(text, close + 1, "(", ")")
    if end == -1:
        return None
    m = _LINK_DEST.match(text[close + 2:end])
    if not m:
        return None
    return text[i + 1:close], m.group(1), m.group(2), end + 1


def _plain_alt(label: str) -> str:
    """Alt text: the label with Markdown escapes and markers removed."""
    label = re.sub(r"\\(.)", r"\1", label)
    return re.sub(r"[*_`]", "", label).strip()


def _smart_quotes(s: str) -> str:
    out = []
    for idx, ch in enumerate(s):
        if ch not in "'\"":
            out.append(ch)
            continue
        prev = s[idx - 1] if idx else " "
        nxt = s[idx + 1] if idx + 1 < len(s) else " "
        if prev == ">":   # after <em> the quote opens; after </em> it closes
            prev = " " if s[s.rfind("<", 0, idx) + 1] != "/" else "x"
        opening = (prev.isspace() or prev in "([{—–\x00\"'“‘")
        opening = opening and not nxt.isspace()
        if ch == "'":
            out.append("‘" if opening and not prev.isalnum() else "’")
        else:
            out.append("“" if opening else "”")
    return "".join(out)


def render_inline(text: str, image_hook: Optional[ImageHook] = None) -> str:
    """Render one paragraph's (or cell's) inline Markdown to HTML."""
    slots: list[str] = []

    def slot(fragment: str) -> str:
        slots.append(fragment)
        return f"\x00{len(slots) - 1}\x01"

    text = re.sub(r" {2,}\n", "\x02", text)
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch == "\x02":
            out.append(slot("<br />\n"))
            i += 1
            continue
        if ch == "\\" and i + 1 < n:
            nxt = text[i + 1]
            if nxt == "\n":
                out.append(slot("<br />\n"))
                i += 2
                continue
            if nxt in _PUNCT:
                out.append(slot(_esc(nxt)))
                i += 2
                continue
        if ch == "`":
            run = len(text[i:]) - len(text[i:].lstrip("`"))
            close = _find_code_close(text, i + run, run)
            if close == -1:
                out.append(slot(_esc("`" * run)))
                i += run
                continue
            code = text[i + run:close].replace("\n", " ").strip()
            out.append(slot(f"<code>{_esc(code)}</code>"))
            i = close + run
            continue
        if ch == "$":
            if text.startswith("$$", i):
                close = text.find("$$", i + 2)
                if close != -1 and text[i + 2:close].strip():
                    out.append(slot(equation_image(text[i + 2:close])))
                    i = close + 2
                    continue
                out.append(slot("$$"))
                i += 2
                continue
            if i + 1 < n and not text[i + 1].isspace():
                close = _find_inline_math_close(text, i + 1)
                if close != -1:
                    out.append(slot(equation_image(text[i + 1:close])))
                    i = close + 1
                    continue
            out.append(slot("$"))
            i += 1
            continue
        if ch == "!" and text.startswith("![", i):
            link = _parse_link(text, i + 1)
            if link:
                label, src, title, end = link
                alt = _plain_alt(label)
                if image_hook is not None:
                    src = image_hook(src, alt)
                t = f' title="{_attr(title)}"' if title else ""
                out.append(slot(f'<img src="{_attr(src)}" alt="{_attr(alt)}"{t} />'))
                i = end
                continue
        if ch == "[":
            link = _parse_link(text, i)
            if link:
                label, href, title, end = link
                t = f' title="{_attr(title)}"' if title else ""
                inner = render_inline(label, image_hook)
                out.append(slot(f'<a href="{_attr(href)}"{t}>{inner}</a>'))
                i = end
                continue
        if ch == "<":
            m = _AUTOLINK.match(text, i)
            if m:
                href = m.group(1)
                shown = href[7:] if href.startswith("mailto:") else href
                out.append(slot(f'<a href="{_attr(href)}">{_esc(shown)}</a>'))
                i = m.end()
                continue
            m = _RAW_TAG.match(text, i)
            if m:
                out.append(slot(m.group(0)))
                i = m.end()
                continue
        if ch == "&":
            m = _ENTITY.match(text, i)
            if m:
                out.append(slot(m.group(0)))
                i = m.end()
                continue
        out.append(ch)
        i += 1

    s = _esc("".join(out))
    s = re.sub(r"\*\*(?=\S)(.+?)(?<=\S)\*\*", r"<strong>\1</strong>", s, flags=re.S)
    s = re.sub(r"(?<![\w_])__(?=\S)(.+?)(?<=\S)__(?![\w_])",
               r"<strong>\1</strong>", s, flags=re.S)
    s = re.sub(r"(?<!\*)\*(?=[^\s*])(.+?)(?<=[^\s*])\*(?!\*)",
               r"<em>\1</em>", s, flags=re.S)
    s = re.sub(r"(?<![\w_])_(?=[^\s_])(.+?)(?<=[^\s_])_(?![\w_])",
               r"<em>\1</em>", s, flags=re.S)
    s = re.sub(r"~~(?=\S)(.+?)(?<=\S)~~", r"<del>\1</del>", s, flags=re.S)
    s = re.sub(r"\^([^\s^]+)\^", r"<sup>\1</sup>", s)
    s = re.sub(r"(?<!~)~([^\s~]+)~(?!~)", r"<sub>\1</sub>", s)
    s = s.replace("---", "—").replace("--", "–").replace("...", "…")
    s = _smart_quotes(s)
    s = s.replace("\n", " ")
    while _SLOT.search(s):
        s = _SLOT.sub(lambda m: slots[int(m.group(1))], s)
    return s.strip()


# ------------------------------------------------------------------- blocks

def _indent_width(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _fence_open(line: str):
    m = _FENCE.match(line)
    if not m:
        return None
    fence, info = m.group(2), m.group(3)
    if fence[0] == "`" and "`" in info:
        return None
    return m


def _fence_lang(info: str) -> str:
    info = info.strip().strip("{}").strip()
    word = info.split()[0] if info.split() else ""
    word = word.split(",")[0].lstrip(".")
    return re.sub(r"[^\w+#.-]", "", word)


def _fenced(lines: list[str], i: int, m) -> tuple[int, str]:
    indent, fence, info = len(m.group(1)), m.group(2), m.group(3)
    close = re.compile(r"^ {0,3}" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}[ \t]*$")
    body = []
    i += 1
    while i < len(lines) and not close.match(lines[i]):
        line = lines[i]
        strip = min(indent, _indent_width(line))
        body.append(line[strip:])
        i += 1
    i += 1  # skip the closing fence (or run off the end)
    lang = _fence_lang(info)
    cls = f' class="{_attr(lang)}"' if lang else ""
    return i, f"<pre{cls}><code>{_esc(chr(10).join(body))}</code></pre>"


def _is_table_start(lines: list[str], i: int) -> bool:
    return (i + 1 < len(lines) and "|" in lines[i] and "|" in lines[i + 1]
            and bool(_TABLE_SEP.match(lines[i + 1])))


def _split_row(line: str) -> list[str]:
    """Cells of a pipe-table row; a '|' inside `code` or $math$ does not split."""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    cells, cur, i, in_math = [], [], 0, False
    while i < len(s):
        ch = s[i]
        if ch == "\\" and i + 1 < len(s):
            cur.append(s[i:i + 2])
            i += 2
            continue
        if ch == "`" and not in_math:
            run = len(s[i:]) - len(s[i:].lstrip("`"))
            close = _find_code_close(s, i + run, run)
            if close != -1:
                cur.append(s[i:close + run])
                i = close + run
                continue
        if ch == "$":
            in_math = not in_math
        if ch == "|" and not in_math:
            cells.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
        i += 1
    cells.append("".join(cur).strip())
    return cells


# Canvas adds no table styling, so a bare <table> renders as unruled, cramped
# text. Inline styles survive Canvas's sanitizer (as text-align does); the
# border="1" attribute keeps the grid visible if a sanitizer drops them.
_TABLE_STYLE = "border-collapse: collapse; margin: 0.5em 0;"
_TD_STYLE = "border: 1px solid #8c8c8c; padding: 0.3em 0.9em;"
_TH_STYLE = _TD_STYLE + " background-color: #eeeeee; font-weight: bold;"


def _table(lines: list[str], i: int, hook) -> tuple[int, str]:
    header = _split_row(lines[i])
    aligns = []
    for spec in _split_row(lines[i + 1]):
        left, right = spec.startswith(":"), spec.endswith(":")
        aligns.append("center" if left and right else
                      "right" if right else "left" if left else "")
    i += 2
    rows = []
    while i < len(lines) and lines[i].strip() and "|" in lines[i]:
        rows.append(_split_row(lines[i]))
        i += 1
    ncol = len(header)

    def cells(row, tag):
        row = (row + [""] * ncol)[:ncol]
        parts = []
        for k, cell in enumerate(row):
            a = aligns[k] if k < len(aligns) else ""
            style = (_TH_STYLE if tag == "th" else _TD_STYLE) + (f" text-align: {a};" if a else "")
            scope = ' scope="col"' if tag == "th" else ""
            parts.append(f'<{tag}{scope} style="{style}">{render_inline(cell, hook)}</{tag}>')
        return "<tr>\n" + "\n".join(parts) + "\n</tr>"

    html = [f'<table border="1" style="{_TABLE_STYLE}">', "<thead>", cells(header, "th"),
            "</thead>", "<tbody>"]
    html += [cells(r, "td") for r in rows]
    html += ["</tbody>", "</table>"]
    return i, "\n".join(html)


def _list_marker(line: str, ordered: Optional[bool] = None):
    """(ordered, match) if the line starts a list item."""
    if ordered in (None, False):
        m = _BULLET.match(line)
        if m and not _HR.match(line):
            return False, m
    if ordered in (None, True):
        m = _ORDERED.match(line)
        if m:
            return True, m
    return None


def _starts_block(line: str) -> bool:
    return bool(_fence_open(line) or _ATX.match(line) or _BQ.match(line)
                or _HR.match(line) or _list_marker(line))


def _list(lines: list[str], i: int, ordered: bool, hook) -> tuple[int, str]:
    items: list[list[str]] = []
    loose = False
    start = None
    n = len(lines)
    while i < n:
        found = _list_marker(lines[i], ordered)
        if not found:
            break
        _, m = found
        marker_end = len(m.group(1)) + len(m.group(2)) + (1 if ordered else 0)
        gap = m.group(3) if not ordered else m.group(4)
        gap = gap[:len(gap) - len(gap.lstrip(" \t"))] if gap else ""
        content_col = marker_end + (len(gap) if 0 < len(gap) <= 4 else 1)
        first = (m.group(4) if not ordered else m.group(5)) or ""
        if ordered and start is None:
            start = int(m.group(2))
        body = [first]
        i += 1
        pending_blank = False
        while i < n:
            line = lines[i]
            if not line.strip():
                body.append("")
                pending_blank = True
                i += 1
                continue
            if _indent_width(line) >= content_col:
                if pending_blank and any(b.strip() for b in body):
                    loose = True
                body.append(line[content_col:])
                pending_blank = False
                i += 1
                continue
            if pending_blank or _list_marker(line) or _starts_block(line):
                break
            body.append(line.strip())   # lazy paragraph continuation
            i += 1
        while body and not body[-1].strip():
            body.pop()
        items.append(body)
        if pending_blank and i < n and _list_marker(lines[i], ordered):
            loose = True
        if pending_blank and not (i < n and _list_marker(lines[i], ordered)):
            break
    parts = []
    for body in items:
        blocks = _blocks(body, hook, in_list=True)
        if not loose:
            blocks = [(k, h[3:-4] if k == "p" else h) for k, h in blocks]
        parts.append("<li>" + "\n".join(h for _, h in blocks) + "</li>")
    tag = "ol" if ordered else "ul"
    attr = f' start="{start}"' if ordered and start not in (None, 1) else ""
    return i, f"<{tag}{attr}>\n" + "\n".join(parts) + f"\n</{tag}>"


def _display_math_open(text: str) -> bool:
    return text.replace("\\$", "").count("$$") % 2 == 1


def _blocks(lines: list[str], hook, in_list: bool = False) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        m = _fence_open(line)
        if m:
            i, h = _fenced(lines, i, m)
            out.append(("code", h))
            continue
        if line.startswith("    ") or line.startswith("\t"):
            body = []
            while i < n and (not lines[i].strip() or lines[i].startswith("    ")
                             or lines[i].startswith("\t")):
                body.append(lines[i][4:] if lines[i].startswith("    ") else lines[i][1:])
                i += 1
            while body and not body[-1].strip():
                body.pop()
            out.append(("code", f"<pre><code>{_esc(chr(10).join(body))}</code></pre>"))
            continue
        m = _ATX.match(line)
        if m:
            level = len(m.group(1))
            out.append(("h", f"<h{level}>{render_inline(m.group(2) or '', hook)}</h{level}>"))
            i += 1
            continue
        if _HR.match(line):
            out.append(("hr", "<hr />"))
            i += 1
            continue
        if _BQ.match(line):
            quoted = []
            while i < n:
                m = _BQ.match(lines[i])
                if m:
                    quoted.append(m.group(1))
                elif (lines[i].strip() and quoted and quoted[-1].strip()
                      and not _starts_block(lines[i])):
                    quoted.append(lines[i])
                else:
                    break
                i += 1
            inner = "\n".join(h for _, h in _blocks(quoted, hook))
            out.append(("bq", f"<blockquote>\n{inner}\n</blockquote>"))
            continue
        if _is_table_start(lines, i):
            i, h = _table(lines, i, hook)
            out.append(("table", h))
            continue
        found = _list_marker(line)
        if found:
            i, h = _list(lines, i, found[0], hook)
            out.append(("list", h))
            continue
        # paragraph: runs to a blank line or a fence; inside an open $$ it
        # runs regardless; in a list item a nested list may interrupt it.
        para = [line]
        i += 1
        while i < n and lines[i].strip():
            text = "\n".join(para)
            if not _display_math_open(text):
                if _fence_open(lines[i]):
                    break
                if in_list and _list_marker(lines[i]):
                    break
                if len(para) == 1 and _SETEXT.match(lines[i]):
                    break
            para.append(lines[i])
            i += 1
        if (len(para) == 1 and i < n and _SETEXT.match(lines[i])
                and not _display_math_open(para[0])):
            level = 1 if lines[i].strip().startswith("=") else 2
            out.append(("h", f"<h{level}>{render_inline(para[0].strip(), hook)}</h{level}>"))
            i += 1
            continue
        text = "\n".join(p.lstrip() for p in para)
        out.append(("p", f"<p>{render_inline(text, hook)}</p>"))
    return out


def render(markdown_text: str, image_hook: Optional[ImageHook] = None) -> str:
    """Render Markdown + $TeX$ to an HTML fragment for a QTI <mattext>.

    image_hook(src, alt) is called for every ![alt](src) and returns the src
    to emit; the QTI builder uses it to collect and repath bundled figures.
    """
    text = str(markdown_text).replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.expandtabs(4).rstrip("\n") for ln in text.split("\n")]
    return "\n".join(h for _, h in _blocks(lines, image_hook)).strip()


def find_images(markdown_text: str) -> list[tuple[str, str]]:
    """Every (src, alt) pair referenced by ![alt](src) in the text."""
    found: list[tuple[str, str]] = []

    def hook(src: str, alt: str) -> str:
        found.append((src, alt))
        return src

    render(markdown_text, hook)
    return found


if __name__ == "__main__":
    import sys
    print(render(sys.stdin.read()))
