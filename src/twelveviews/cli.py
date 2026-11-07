"""Command line: python -m twelveviews.cli {synthetic,analysis,figures,paper,web}."""
from __future__ import annotations

import argparse


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="twelveviews", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("synthetic", help="(re)generate the ten synthetic datasets -> data/raw/synthetic_*.csv")
    sub.add_parser("analysis", help="metrics, LaTeX macros and tables -> data/processed/, paper/tables/")
    f = sub.add_parser("figures", help="the twelve figures -> paper/figures/ (all, or the ones named)")
    f.add_argument("names", nargs="*", help="e.g. sankey chord")
    sub.add_parser("paper", help="typeset paper/paper.pdf (tectonic)")
    sub.add_parser("web", help="web reader -> docs/paper/ (pandoc)")
    args = ap.parse_args(argv)

    if args.cmd == "synthetic":
        from . import data_gen
        data_gen.main()
    elif args.cmd == "analysis":
        from . import analysis
        analysis.main()
    elif args.cmd == "figures":
        from . import figures
        figures.main(args.names)
    elif args.cmd == "paper":
        from . import paper_build
        paper_build.main()
    elif args.cmd == "web":
        from . import paper_web
        paper_web.main()


if __name__ == "__main__":
    main()
