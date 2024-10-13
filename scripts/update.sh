# Update dependencies

poetry self add poetry-plugin-up
poetry up
poetry lock
poetry run pre-commit autoupdate
