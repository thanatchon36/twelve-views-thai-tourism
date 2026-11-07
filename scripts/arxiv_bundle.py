"""Build the arXiv source bundle, ``paper/arxiv.tar.gz``, from the paper as last built.

arXiv compiles the paper itself, from the root of the bundle, with XeLaTeX (declared in
``00README.json``). This stages ``paper.tex``, the generated ``tables/``, the figures it uses (PDF), the
bibliography and the ``paper.bbl`` written by ``make paper``, compiles the staged copy once with tectonic to
prove it is self-contained, then tars it. It also prints the title, the plain-text abstract (for the arXiv
form) and a comments line. Run ``make paper`` first.

Usage: ``python scripts/arxiv_bundle.py``.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

from twelveviews.paper_build import plain_abstract

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
STAGE = PAPER / "arxiv"
OUT = PAPER / "arxiv.tar.gz"


def main() -> int:
    tex = (PAPER / "paper.tex").read_text(encoding="utf-8")
    if not (PAPER / "paper.bbl").exists():
        raise SystemExit("paper/paper.bbl missing; run make paper first")
    if STAGE.exists():
        shutil.rmtree(STAGE)
    (STAGE / "figures").mkdir(parents=True)
    (STAGE / "tables").mkdir()
    for name in ("paper.tex", "paper.bbl", "references.bib"):
        shutil.copyfile(PAPER / name, STAGE / name)
    for f in sorted((PAPER / "tables").glob("*.tex")):
        shutil.copyfile(f, STAGE / "tables" / f.name)
    figures = sorted(set(re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([\w.-]+)\}", tex)))
    for name in figures:
        shutil.copyfile(PAPER / "figures" / f"{name}.pdf", STAGE / "figures" / f"{name}.pdf")
    (STAGE / "00README.json").write_text(
        json.dumps(
            {
                "spec_version": 1,
                "process": {"compiler": "xelatex"},
                "sources": [{"filename": "paper.tex", "usage": "toplevel"}],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    # the staged copy must compile on its own
    subprocess.run(
        ["tectonic", "-X", "compile", "--keep-logs", "paper.tex"], cwd=STAGE, check=True, capture_output=True
    )
    log = (STAGE / "paper.log").read_text(encoding="utf-8", errors="replace")
    pages = re.search(r"Output written on paper\.(?:xdv|pdf) \((\d+) pages", log)
    if pages is None:
        raise SystemExit("staged compile left no page count")
    for name in ("paper.log", "paper.pdf"):
        (STAGE / name).unlink(missing_ok=True)
    with tarfile.open(OUT, "w:gz") as tar:
        for p in sorted(STAGE.rglob("*")):
            if p.is_file():
                tar.add(p, arcname=str(p.relative_to(STAGE)))
    files = sorted(str(p.relative_to(STAGE)) for p in STAGE.rglob("*") if p.is_file())
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} kB, {len(files)} files)")
    print("\n".join(f"  {f}" for f in files))

    title = (
        "Twelve Views of Thai Tourism: A Data-Shape-Driven Framework for Visual Analysis, "
        "Evaluated by Planted-Structure Recovery"
    )
    body = plain_abstract()
    n_tables = len(re.findall(r"\\begin\{table\}", tex))
    print(f"\nTitle:\n{title}")
    print(f"\nAbstract ({len(body)} characters; arXiv allows 1,920):\n{body}")
    print(
        f"\nComments:\n{pages.group(1)} pages, {len(figures) + 1} figures, {n_tables} tables. Working paper; all "
        "results are from synthetic data. Code and data: https://github.com/thanatchon36/twelve-views-thai-tourism"
    )
    print("\nPrimary category: cs.HC (Human-Computer Interaction); cross-list: stat.AP")
    return 0


if __name__ == "__main__":
    sys.exit(main())
