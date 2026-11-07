"""Typeset the manuscript and, optionally, package an arXiv submission.

Run:  python -m src.build_paper           -> paper/main.pdf and ./paper.pdf
      python -m src.build_paper --arxiv   -> also arxiv/arxiv-submission.zip and arxiv/metadata.txt
"""
import re
import shutil
import subprocess
import sys
import zipfile

from .config import FIGURES, PAPER, ROOT

PDFLATEX = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"]


def _run(cmd, cwd=PAPER, ok=(0,)) -> str:
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if res.returncode not in ok:
        print(res.stdout[-4000:])
        raise SystemExit(f"{cmd[0]} failed (exit {res.returncode}) in {cwd}")
    return res.stdout


def typeset() -> None:
    _run(PDFLATEX)
    _run(["bibtex", "main"], ok=(0, 1))      # bibtex exits 1 on mere warnings
    _run(PDFLATEX)
    _run(PDFLATEX)
    shutil.copy(PAPER / "main.pdf", ROOT / "paper.pdf")
    print("wrote paper.pdf")


def _macros() -> dict:
    vals = {}
    for line in (PAPER / "generated" / "numbers.tex").read_text(encoding="utf-8").splitlines():
        m = re.match(r"\\newcommand\{\\(\w+)\}\{(.*)\}$", line)
        if m:
            vals[m.group(1)] = m.group(2).replace(r"\&", "&").replace(r"\%", "%")
    return vals


def plain_abstract() -> str:
    """The abstract as plain text with every macro expanded, for the arXiv submission form."""
    tex = (PAPER / "main.tex").read_text(encoding="utf-8")
    text = tex[tex.index(r"\begin{abstract}") + len(r"\begin{abstract}"):tex.index(r"\end{abstract}")]
    for name, value in sorted(_macros().items(), key=lambda kv: -len(kv[0])):
        text = re.sub(r"\\" + name + r"(\{\})?(?![A-Za-z])", lambda _m, v=value: v, text)
    for a, b in (("---", "\u2014"), ("--", "\u2013"), (r"\%", "%"), ("~", " "), ("$", ""), ("{}", "")):
        text = text.replace(a, b)
    return re.sub(r"\s+", " ", text).strip()


def arxiv_bundle() -> None:
    """Self-contained source bundle: arXiv runs pdflatex on it and uses the supplied main.bbl."""
    out = ROOT / "build" / "arxiv"
    shutil.rmtree(out, ignore_errors=True)
    (out / "figures").mkdir(parents=True)
    (out / "generated").mkdir()
    tex = (PAPER / "main.tex").read_text(encoding="utf-8")
    tex = tex.replace(r"\graphicspath{{../figures/}}", r"\graphicspath{{figures/}}")
    (out / "main.tex").write_text(tex, encoding="utf-8")
    for name in ("preprint.sty", "main.bbl", "references.bib"):
        shutil.copy(PAPER / name, out / name)
    for f in (PAPER / "generated").glob("*.tex"):
        shutil.copy(f, out / "generated" / f.name)
    figures = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", tex)
    for name in figures:
        shutil.copy(FIGURES / f"{name}.pdf", out / "figures" / f"{name}.pdf")
    _run(PDFLATEX, cwd=out)
    log = _run(PDFLATEX, cwd=out)                     # second pass resolves references
    pages = re.search(r"Output written on main\.pdf \((\d+) pages", log).group(1)
    for f in out.glob("main.*"):
        if f.suffix not in (".tex", ".bbl"):
            f.unlink()
    dest = ROOT / "arxiv"
    dest.mkdir(exist_ok=True)
    with zipfile.ZipFile(dest / "arxiv-submission.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(out.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(out))
    title = re.sub(r"\s+", " ", re.search(r"\\title\{(.*?)\}\n", tex, re.S).group(1))
    abstract = plain_abstract()
    n_tables = len(re.findall(r"\\begin\{table\}", tex))
    meta = (f"Title: {title}\n"
            f"Authors: Thanatchon Chongmankhong\n\n"
            f"Abstract ({len(abstract)} characters; the arXiv limit is 1,920):\n{abstract}\n\n"
            f"Comments: {pages} pages, {len(figures) + 1} figures, {n_tables} tables. Code and synthetic data: "
            f"https://github.com/[username]/twelve-views-thai-tourism\n\n"
            f"Primary category: cs.HC (Human-Computer Interaction)\n"
            f"Cross-list: stat.AP (Statistics - Applications)\n"
            f"Licence (suggested): CC BY 4.0\n")
    (dest / "metadata.txt").write_text(meta, encoding="utf-8")
    print(f"wrote arxiv/arxiv-submission.zip ({pages} pages) and arxiv/metadata.txt")


def main(argv=None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    typeset()
    if "--arxiv" in argv:
        arxiv_bundle()


if __name__ == "__main__":
    main()
