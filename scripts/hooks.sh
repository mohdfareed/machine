# Run the pre-commit hooks

poetry run pre-commit install --install-hooks
poetry run pre-commit run --all-files
poetry build
