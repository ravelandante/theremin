VENV   := env
PYTHON := python
PIP    := $(VENV)/bin/pip
PY     := $(VENV)/bin/python

.PHONY: install
install:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

.PHONY: clean
clean:
	rm -rf $(VENV)