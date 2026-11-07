"""Typeset paper/paper.tex into paper/paper.pdf with tectonic (XeLaTeX + BibTeX).

Every number and table body in the paper is \\input from paper/tables/, written by twelveviews.analysis,
and every figure comes from paper/figures/, written by twelveviews.figures, so `make all` regenerates the
whole document from the data. Requires tectonic on PATH.

Run:  python -m twelveviews.cli paper
"""
from __future__ import annotations

import re
import shutil
import subprocess

from .config import PAPER, TABLES

TECTONIC = ["tectonic", "-X", "compile", "--keep-logs", "--keep-intermediates", "paper.tex"]


def macros() -> dict[str, str]:
    """The \\newcommand values in paper/tables/numbers.tex, LaTeX escapes undone."""
    vals = {}
    for line in (TABLES / "numbers.tex").read_text(encoding="utf-8").splitlines():
        m = re.match(r"\\newcommand\{\\(\w+)\}\{(.*)\}$", line)
        if m:
            vals[m.group(1)] = m.group(2).replace(r"\&", "&").replace(r"\%", "%")
    return vals


def expand_macros(text: str) -> str:
    for name, value in sorted(macros().items(), key=lambda kv: -len(kv[0])):
        text = re.sub(r"\\" + name + r"(\{\})?(?![A-Za-z])", lambda _m, v=value: v, text)
    return text


def plain_abstract() -> str:
    """The abstract as plain text with every macro expanded, for the arXiv submission form."""
    tex = (PAPER / "paper.tex").read_text(encoding="utf-8")
    text = tex[tex.index(r"\begin{abstract}") + len(r"\begin{abstract}"):tex.index(r"\end{abstract}")]
    text = expand_macros(text)
    for a, b in (("---", "\u2014"), ("--", "\u2013"), (r"\%", "%"), ("~", " "), ("$", ""), ("{}", "")):
        text = text.replace(a, b)
    return re.sub(r"\s+", " ", text).strip()


def build_pdf() -> None:
    if shutil.which("tectonic") is None:
        raise SystemExit("tectonic not found; install it (brew install tectonic) to build the paper")
    res = subprocess.run(TECTONIC, cwd=PAPER, capture_output=True, text=True)
    if res.returncode != 0:
        print(res.stdout[-4000:], res.stderr[-4000:])
        raise SystemExit("tectonic failed; see paper/paper.log")
    log = (PAPER / "paper.log").read_text(encoding="utf-8", errors="replace")
    pages = re.search(r"Output written on paper\.(?:xdv|pdf) \((\d+) pages", log)
    print(f"wrote paper/paper.pdf ({pages.group(1) if pages else '?'} pages)")


def main(argv=None) -> None:
    build_pdf()


if __name__ == "__main__":
    main()
