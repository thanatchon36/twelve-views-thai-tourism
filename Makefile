.PHONY: all data analysis figures paper arxiv test fonts clean

all: data analysis figures paper

fonts:    ; bash scripts/get_fonts.sh
data:     ; python -m src.data_gen
analysis: ; python -m src.analysis
figures:  ; python -m src.figures
paper:    ; python -m src.build_paper
arxiv:    ; python -m src.build_paper --arxiv
test:     ; python -m pytest -q
clean:    ; rm -rf build; rm -f paper/*.aux paper/*.bbl paper/*.blg paper/*.log paper/*.out paper/main.pdf
