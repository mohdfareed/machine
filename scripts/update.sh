# Update dependencies

poetry self update
poetry update
poetry lock
poetry run pre-commit autoupdate
