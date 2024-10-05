# Print a coverage report for the project

poetry run pytest --cov-report=term-missing:skip-covered --cov=app tests/
