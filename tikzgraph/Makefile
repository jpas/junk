demo.pdf: demo.tex star.tex

clean:
	rm -rf demo.pdf star.tex __pycache__

%.pdf: %.tex
	tectonic $<

%.tex: %.tex.py
	python $< > $@
