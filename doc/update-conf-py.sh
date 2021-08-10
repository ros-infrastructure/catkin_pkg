#!/bin/sh

CONFIG_FILE='_build/conf.py'
TMP_FILE="${CONFIG_FILE}.tmp"

sed -i "s/html_theme =.*\$/html_theme = 'sphinx_rtd_theme'/" $CONFIG_FILE
awk "
	start && finish && !done { done = 1; print \"extensions.append('sphinx_rtd_theme')\" }
	/extensions = \[/ { start = 1 }
	/^\]$/ && start { finish = 1 }
	{ print \$0 }

" < $CONFIG_FILE > $TMP_FILE
mv $TMP_FILE $CONFIG_FILE
