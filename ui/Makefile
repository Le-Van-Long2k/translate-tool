.PHONY: venv install setup run design

venv:
	rm -rf venv
	python3.14 -m venv venv

install: venv
	venv/bin/python -m pip install --upgrade pip
	venv/bin/python -m pip install -r requirements.txt

setup: install

run:
	QT_QPA_PLATFORM=xcb venv/bin/python main.py

design:
	venv/bin/pyside6-designer

convert_resource:
	venv/bin/pyside6-rcc resources.qrc -o resources_rc.py