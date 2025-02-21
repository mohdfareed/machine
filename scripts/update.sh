# Update dependencies

poetry self update
poetry update
poetry lock

poetry run pre-commit install --install-hooks
poetry run pre-commit autoupdate
poetry build
