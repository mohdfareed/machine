# Update dependencies

poetry self add poetry-plugin-up
poetry self update
poetry up
poetry lock
poetry run pre-commit autoupdate
