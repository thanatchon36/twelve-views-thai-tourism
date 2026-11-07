"""Reproduce everything: data -> metrics -> figures -> paper.pdf

    python run_all.py
"""
from src import analysis, build_paper, data_gen, figures


def main() -> None:
    data_gen.main()       # 1. ten synthetic datasets       -> data/*.csv
    analysis.main()       # 2. every number in the paper     -> results/, paper/generated/
    figures.main()        # 3. twelve figures                -> figures/*.pdf, *.png
    build_paper.main([])  # 4. pdflatex + bibtex             -> paper.pdf


if __name__ == "__main__":
    main()
