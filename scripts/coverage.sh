# Print a coverage report for the project

poetry run pytest --junitxml=pytest.xml --cov-report=term-missing:skip-covered --cov=app tests/
