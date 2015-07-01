.PHONY: html apidoc clean upload

SPHINXAPIDOC=sphinx-apidoc

html: apidoc
	$(MAKE) -C _build html

apidoc:
	$(SPHINXAPIDOC) -F -o _build ../src/catkin_pkg
	sed -i "s/_build/./g" _build/Makefile

clean:
	-rm -rf _build

upload: html
	scp -r _build/html/ rosbot@ros.osuosl.org:/home/rosbot/docs/independent/api/catkin_pkg/
