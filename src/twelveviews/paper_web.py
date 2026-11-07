"""Build the web reader docs/paper/ from paper/paper.tex (same text and numbers as the PDF).

pandoc reads the LaTeX source, with the generated macros and table bodies inlined, and renders it with
paper/reader.html: masthead, abstract, a results strip whose numbers come from data/processed/metrics.json,
contents, numbered sections, references and the appendix. Cross-references and caption numbers are resolved
here, in the order LaTeX numbers them. The TikZ framework diagram (Figure 1) is compiled on its own with
tectonic and rasterised with pdftoppm. The PDF and the figures the page uses are copied next to it; GitHub
Pages serves docs/ at https://thanatchon36.github.io/twelve-views-thai-tourism/.
Requires pandoc, tectonic and pdftoppm (poppler) on PATH.

Run:  python -m twelveviews.cli web
"""
from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from .config import DATA_URL, DOCS, FIGURES, PAPER, PAPER_URL, PROCESSED, REPO_URL, TABLES

OUT = DOCS / "paper"
FRAMEWORK_PNG = "fig01_framework.png"
CONCEPT_DOI = "10.5281/zenodo.24035604"  # Zenodo concept DOI: resolves to the latest release

# (label, style, finding, detail) with {key} placeholders filled from metrics.json.
# style: "ref" = recovered on the synthetic data, "null" = pending.
RESULTS = [
    ("E1 · seasonality", "ref", "Seasonal profile recovered at r = {rec_season_r:.3f}",
     "radial spiral; 12 monthly indices, MAE {rec_season_mae:.3f}; peak in {season_peak_month}"),
    ("E2 · pandemic shock", "ref", "Arrivals fell {drop_pct:.1f}% from {peak_year} to {low_year}",
     "planted drop {rec_drop_planted_pct:.1f}%, recovered {rec_drop_obs_pct:.1f}%; {latest_year} back to {recovery_pct:.1f}% of the peak"),
    ("E4 · length of stay", "ref", "Median stay recovered within {rec_stay_mae:.2f} nights",
     "ridgeline plot; nine markets, largest error {rec_stay_max:.1f} nights"),
    ("E5 · destinations", "ref", "Destination preferences recovered within {rec_dest_mae:.2f} pp",
     "Sankey diagram; 36 shares, largest error {rec_dest_max:.2f} pp"),
    ("E6 · hub", "ref", "Bangkok's share of onward trips: {rec_hub_obs_pct:.1f}% (planted {rec_hub_planted_pct:.1f}%)",
     "chord diagram of onward travel between destination clusters"),
    ("E8 · personas", "ref", "Six personas recovered with ARI {seg_ari:.2f}",
     "t-SNE embedding map and k-means on {seg_n:,} synthetic respondents"),
    ("Revenue", "ref", "{rev_top1} alone takes {rev_top1_share_pct:.1f}% of provincial revenue",
     "circle packing and sunburst; top five provinces {rev_top5_share_pct:.1f}%"),
    ("Thai data", "null", "Real-data results pending",
     "every number here comes from planted synthetic data; drop real files into data/raw/ and run make all"),
]


# --------------------------------------------------------------------------- LaTeX preprocessing
def _inline_inputs(tex: str) -> str:
    tex = tex.replace(r"\input{tables/numbers.tex}", (TABLES / "numbers.tex").read_text(encoding="utf-8"))
    tex = re.sub(r"^\\newcommand\{\\inputrows\}.*$", "", tex, flags=re.M)
    return re.sub(r"\\inputrows\{([^}]+)\}", lambda m: (PAPER / m.group(1)).read_text(encoding="utf-8"), tex)


def _split_minipages(tex: str) -> str:
    """A figure holding side-by-side minipages becomes one figure per minipage."""
    def split(m: re.Match) -> str:
        parts = re.findall(r"\\begin\{minipage\}(?:\[[^\]]*\])?\{[^}]*\}(.*?)\\end\{minipage\}", m.group(0), re.S)
        return "\n".join(f"\\begin{{figure}}\n{p.strip()}\n\\end{{figure}}" for p in parts) if parts else m.group(0)
    return re.sub(r"\\begin\{figure\}(?:\[[^\]]*\])?.*?\\end\{figure\}", split, tex, flags=re.S)


def _number(tex: str) -> tuple[str, dict[str, str]]:
    """Number sections, figures, tables and equations as LaTeX does; prefix each caption with its number."""
    token = re.compile(
        r"\\appendix\b|\\setcounter\{table\}\{0\}|\\section\*?\{|\\subsection\*?\{|\\begin\{(figure|table|equation)\}"
        r"|\\end\{(figure|table|equation)\}|\\caption\{|\\label\{([^}]+)\}"
    )
    st = {"sec": 0, "sub": 0, "fig": 0, "tab": 0, "eq": 0, "app": False, "tabp": "", "cur": "", "env": [], "float": ""}
    labels: dict[str, str] = {}

    def visit(m: re.Match) -> str:
        t = m.group(0)
        if t == r"\appendix":
            st["app"] = True
            st["sec"] = 0
        elif t.startswith(r"\setcounter{table}"):
            st["tab"], st["tabp"] = 0, "A"
        elif t.startswith(r"\section"):
            if "*" not in t:
                st["sec"] += 1
                st["sub"] = 0
                st["cur"] = chr(64 + st["sec"]) if st["app"] else str(st["sec"])
        elif t.startswith(r"\subsection"):
            if "*" not in t:
                st["sub"] += 1
                base = chr(64 + st["sec"]) if st["app"] else str(st["sec"])
                st["cur"] = f"{base}.{st['sub']}"
        elif m.group(1):
            st["env"].append(m.group(1))
            if m.group(1) == "equation":
                st["eq"] += 1
        elif m.group(2):
            if st["env"]:
                st["env"].pop()
        elif t == r"\caption{":
            env = next((e for e in reversed(st["env"]) if e in ("figure", "table")), "figure")
            if env == "figure":
                st["fig"] += 1
                st["float"] = str(st["fig"])
                return t + rf"\textbf{{Figure {st['fig']}.}} "
            st["tab"] += 1
            st["float"] = f"{st['tabp']}{st['tab']}"
            return t + rf"\textbf{{Table {st['float']}.}} "
        elif m.group(3):
            env = st["env"][-1] if st["env"] else ""
            labels[m.group(3)] = (
                str(st["eq"]) if env == "equation" else st["float"] if env in ("figure", "table") else st["cur"]
            )
        return t

    body = token.sub(visit, tex)
    return body, labels


def _resolve_refs(tex: str, labels: dict[str, str]) -> str:
    def ref(m: re.Match) -> str:
        if m.group(2) not in labels:
            raise RuntimeError(f"unresolved \\ref{{{m.group(2)}}}")
        n = labels[m.group(2)]
        return f"({n})" if m.group(1) == "eqref" else n
    return re.sub(r"\\(ref|eqref)\{([^}]+)\}", ref, tex)


def _framework_png(tex: str) -> None:
    """Compile the TikZ diagram on its own and rasterise it for the browser."""
    pic = re.search(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}", tex, re.S).group(0)
    colors = "\n".join(re.findall(r"^\\definecolor.*$", tex, re.M))
    doc = (
        "\\documentclass[border=4pt]{standalone}\n\\usepackage{amsmath}\n\\usepackage{libertinus}\n"
        "\\usepackage{xcolor}\n\\usepackage{tikz}\n\\usetikzlibrary{positioning}\n"
        f"{colors}\n\\begin{{document}}\n{pic}\n\\end{{document}}\n"
    )
    with tempfile.TemporaryDirectory() as d:
        Path(d, "fw.tex").write_text(doc, encoding="utf-8")
        subprocess.run(["tectonic", "-X", "compile", "fw.tex"], cwd=d, check=True, capture_output=True)
        subprocess.run(["pdftoppm", "-r", "220", "-png", "-singlefile", "fw.pdf", "fw"], cwd=d, check=True)
        shutil.copyfile(Path(d, "fw.png"), FIGURES / FRAMEWORK_PNG)


def _prepare(tex: str) -> tuple[str, str]:
    """paper.tex -> LaTeX that pandoc reads well, plus the plain keywords line."""
    tex = _inline_inputs(tex)
    tex = _split_minipages(tex)
    tex = re.sub(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}",
                 lambda _m: rf"\includegraphics{{{FRAMEWORK_PNG}}}", tex, flags=re.S)
    tex = re.sub(r"\\includegraphics(\[[^\]]*\])?\{([\w.-]+?)(\.png)?\}",
                 lambda m: rf"\includegraphics{{figures/{m.group(2)}.png}}", tex)
    tex, labels = _number(tex)
    tex = _resolve_refs(tex, labels)
    # front matter goes to pandoc metadata; drop it from the body
    tex = re.sub(r"\\title\{.*?\n\\date\{[^}]*\}\n", "", tex, flags=re.S)
    tex = tex.replace(r"\maketitle", "")
    kw = re.search(r"\\noindent\\textbf\{Keywords:\}(.*?)\n\n", tex, re.S)
    tex = tex.replace(kw.group(0), "")
    keywords = " ".join(kw.group(1).split()).rstrip(".")
    # the bibliography goes where \bibliography stands (before the appendix), as in the PDF
    tex = re.sub(r"\\bibliographystyle\{[^}]*\}\s*\\bibliography\{[^}]*\}", r"\\section*{References}\nREFSHERE\n", tex)
    tex = tex.replace(r"\clearpage", "")
    tex = tex.replace(r"\paragraph{", r"\paragraph*{")  # unnumbered in the PDF too
    tex = _plain_lists(tex)
    return tex, keywords


def _plain_lists(tex: str) -> str:
    """pandoc drops lists that carry enumitem options: strip them, and turn a labelled enumerate such as
    label=(C\\arabic*) into a description list with the labels written out."""
    tex = re.sub(r"\\begin\{description\}\[[^\]]*\]", r"\\begin{description}", tex)

    def labelled(m: re.Match) -> str:
        fmt, body = m.group(1), m.group(2)
        items = re.split(r"\\item\s+", body)[1:]
        rows = "".join(rf"\item[{fmt.replace(r'\arabic*', str(i))}] {it.strip()}" + "\n"
                       for i, it in enumerate(items, 1))
        return "\\begin{description}\n" + rows + "\\end{description}"

    return re.sub(r"\\begin\{enumerate\}\[label=([^,\]]+)[^\]]*\](.*?)\\end\{enumerate\}", labelled, tex, flags=re.S)


# --------------------------------------------------------------------------- HTML post-processing
def _postprocess(page: str) -> str:
    # move citeproc's reference list to where \bibliography stood
    refs = re.search(r'<div id="refs".*?</div>\s*</div>\s*(?=</article>)', page, re.S)
    if refs:
        page = page.replace(refs.group(0), "")
        page = re.sub(r"<p>REFSHERE</p>", lambda _m: refs.group(0), page)
    # appendix sections are lettered in the PDF
    page = re.sub(r'(<h1 data-number="(\d+)" id="app:[^"]*"><span class="header-section-number">)\d+',
                  lambda m: m.group(1) + "A", page)
    page = re.sub(r'(<a href="#app:[^"]*"[^>]*><span class="toc-section-number">)\d+', r"\1A", page)
    # figures: drop the PDF sizing and load lazily
    page = re.sub(r"<img\b[^>]*>",
                  lambda m: re.sub(r'\s(?:style|width|height)="[^"]*"', "", m.group(0)).replace("<img ", '<img loading="lazy" ', 1),
                  page)
    # tables: caption above, outside the sideways scroll; content-sized columns
    page = re.sub(r"<table\b[^>]*>\s*<caption>(.*?)</caption>(.*?)</table>",
                  r'<div class="tbl"><p class="tcap">\1</p><div class="tscroll"><table>\2</table></div></div>',
                  page, flags=re.S)
    page = re.sub(r"<colgroup>.*?</colgroup>\s*", "", page, flags=re.S)
    return page


def _results(metrics: dict) -> str:
    m = dict(metrics)
    for k in ("drop", "recovery", "rec_drop_planted", "rec_drop_obs", "rec_hub_obs", "rec_hub_planted",
              "rev_top1_share", "rev_top5_share"):
        m[f"{k}_pct"] = 100 * m[k]
    items = []
    for label, style, finding, detail in RESULTS:
        f, d = finding.format(**m), detail.format(**m)
        items.append(f'<li class="r r-{style}"><span class="r-id">{html.escape(label)}</span>'
                     f'<span class="r-text">{html.escape(f)}<small>{html.escape(d)}</small></span></li>')
    return "\n".join(items)


def build_web() -> Path:
    for tool in ("pandoc", "tectonic", "pdftoppm"):
        if shutil.which(tool) is None:
            raise RuntimeError(f"{tool} not found; the web reader needs pandoc, tectonic and pdftoppm")
    src = (PAPER / "paper.tex").read_text(encoding="utf-8")
    _framework_png(src)
    tex, keywords = _prepare(src)
    title = "Twelve Views of Thai Tourism"
    subtitle = "A Data-Shape-Driven Framework for Visual Analysis, Evaluated by Planted-Structure Recovery"
    thanks = re.search(r"\\thanks\{(.*?)\}\}\n", src, re.S).group(1)
    thanks = re.sub(r"\\url\{([^}]+)\}", r'<a href="\1">\1</a>', " ".join(thanks.split()))
    page = subprocess.run(
        ["pandoc", "--from=latex", "--to=html5", "--mathml", "--wrap=none", "--standalone",
         "--template=reader.html", "--number-sections", "--toc", "--toc-depth=1",
         "--citeproc", "--bibliography=references.bib",
         f"--metadata=title:{title}", f"--metadata=subtitle:{subtitle}",
         "--metadata=author:Thanatchon Chongmankhong", "--metadata=date:November 2026",
         f"--metadata=keywords:{keywords}", f"--metadata=thanks:{thanks}",
         f"--metadata=pagetitle:{title}",
         "--metadata=description:Working paper: a data-shape-driven framework of twelve coordinated views for "
         "analysing inbound tourism to Thailand, evaluated by planted-structure recovery on synthetic data."],
        input=tex, capture_output=True, text=True, check=True, cwd=str(PAPER),
    ).stdout
    page = _postprocess(page)

    metrics = json.loads((PROCESSED / "metrics.json").read_text(encoding="utf-8"))
    actions = (
        '<li><a href="paper.pdf">Download PDF</a></li>'
        f'<li><a href="{REPO_URL}">Code and replication</a></li>'
        f'<li><a href="{DATA_URL}">Data (Hugging Face)</a></li>'
        + (f'<li><a href="https://doi.org/{CONCEPT_DOI}">Zenodo archive</a></li>' if CONCEPT_DOI else "")
    )
    bib = (
        "@techreport{chongmankhong2026twelveviews,\n"
        "  author      = {Chongmankhong, Thanatchon},\n"
        f"  title       = {{{title}: {subtitle}}},\n"
        "  year        = {2026},\n"
        "  type        = {Working paper},\n"
        + (f"  doi         = {{{CONCEPT_DOI}}},\n" if CONCEPT_DOI else "")
        + f"  url         = {{{PAPER_URL}}}\n"
        "}"
    )
    colophon = (
        "<p>Rendered from <code>paper/paper.tex</code> by <code>twelveviews.paper_web</code> "
        "(<code>make web</code>). Every number is resolved from the same generated macros and tables as the PDF, "
        "which is authoritative. This run uses synthetic data throughout.</p>"
    )
    for marker, value in (
        ("<!--ACTIONS-->", actions),
        ("<!--RESULTS-NOTE-->", (
            "Recovery of the structure planted in the synthetic data, generated from the result files. "
            "They validate the method, not Thai tourism. Amber: results on synthetic data; grey: pending."
        )),
        ("<!--RESULTS-->", _results(metrics)),
        ("<!--CITE-->", f"<h2>How to cite</h2><pre><code>{html.escape(bib)}</code></pre>"),
        ("<!--COLOPHON-->", colophon),
    ):
        if marker not in page:
            raise RuntimeError(f"reader.html lacks {marker}")
        page = page.replace(marker, value)
    visible = re.sub(r"<annotation\b.*?</annotation>", "", page, flags=re.S)  # MathML keeps its TeX source there
    leftovers = re.findall(r"REFSHERE|\\[A-Za-z]+\{|\{\w+(?::[^}]*)?\}(?=</)", visible)
    if leftovers:
        raise RuntimeError(f"unresolved LaTeX in the web page: {sorted(set(leftovers))[:10]}")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "index.html").write_text(page, encoding="utf-8")
    if (PAPER / "paper.pdf").exists():
        shutil.copyfile(PAPER / "paper.pdf", OUT / "paper.pdf")
    if (OUT / "figures").exists():
        shutil.rmtree(OUT / "figures")
    (OUT / "figures").mkdir()
    for name in sorted(set(re.findall(r'src="figures/([\w.-]+)"', page))):
        shutil.copyfile(FIGURES / name, OUT / "figures" / name)
    print(f"wrote {(OUT / 'index.html').relative_to(DOCS.parent)}")
    return OUT / "index.html"


def main() -> None:
    build_web()


if __name__ == "__main__":
    main()
