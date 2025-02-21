# Print coverage report of the tests

poetry run pytest --cov-report=term-missing:skip-covered --cov=app tests/
