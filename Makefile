# Variables
VENV = ./env
MANAGE = $(VENV)/bin/python manage.py

# Run Django server on port 8080
.PHONY: run
run:
	$(MANAGE) runserver 8080

# Make Django migrations
.PHONY: makemigrations
makemigrations:
	$(MANAGE) makemigrations

# Apply Django migrations
.PHONY: migrate
migrate:
	$(MANAGE) migrate
