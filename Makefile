.PHONY: all cov htmlcov test


all: test htmlcov

cov:
	coverage report -m

htmlcov:
	coverage html

test:
	coverage run --source='.' -m unittest
