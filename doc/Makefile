.PHONY: html apidoc clean upload

SPHINXAPIDOC=sphinx-apidoc

html: apidoc
	$(MAKE) -C _build html

apidoc:
	$(SPHINXAPIDOC) --extensions sphinx_rtd_theme -F -o _build ../src/catkin_pkg
	sed -i "s/html_theme = .*$$/html_theme = 'sphinx_rtd_theme'/g" _build/conf.py
	sed -i "s/_build/./g" _build/Makefile

clean:
	-rm -rf _build

upload: html
	scp -r _build/html/ rosbot@ros.osuosl.org:/home/rosbot/docs/independent/api/catkin_pkg/
