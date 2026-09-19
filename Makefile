.PHONY: prepare generate generate-portrait generate-readme check

PYTHON ?= python3
SOURCE ?=
PREPARED := .local/prepared-portrait.png

prepare:
	@test -n "$(SOURCE)" || (echo 'Usage: make SOURCE=/absolute/path/to/portrait.jpg generate' && exit 1)
	mkdir -p .local
	$(PYTHON) scripts/prep_photo.py "$(SOURCE)" "$(PREPARED)"

generate: prepare
	$(PYTHON) scripts/generate_portrait.py "$(PREPARED)" assets/hero
	$(PYTHON) scripts/generate_readme.py
	$(PYTHON) scripts/validate.py

generate-portrait: prepare
	$(PYTHON) scripts/generate_portrait.py "$(PREPARED)" assets/hero

generate-readme:
	$(PYTHON) scripts/generate_readme.py

check:
	$(PYTHON) scripts/validate.py
