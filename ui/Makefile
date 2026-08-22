.PHONY: venv install setup run design

venv:
	rm -rf venv
	python3 -m venv venv

install: venv
	venv/bin/python -m pip install --upgrade pip
	venv/bin/python -m pip install -r requirements.txt

setup: install

run:
	venv/bin/python main.py

design:
	venv/bin/pyside6-designer