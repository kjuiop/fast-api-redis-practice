SHELL := /bin/zsh

VENV := .venv
APP ?= main:app

.PHONY: help enter run exit

help:
	@echo "make enter - open a shell with .venv activated"
	@echo "make run   - run uvicorn using APP=main:app"
	@echo "make exit  - show the command to leave .venv"

enter:
	@. $(VENV)/bin/activate && exec $$SHELL

run:
	@$(VENV)/bin/uvicorn $(APP) --reload

exit:
	@echo "deactivate"