all: check coverage mutants

.PHONY: \
		all \
		check \
		check_data \
		clean \
		coverage \
		format \
		init \
		install \
		linter \
		mutants \
		setup \
		tests

module = recurrator
codecov_token = 39e783f6-020b-4e84-b333-2f8a40f9df2b

define lint
	pylint \
        --disable=bad-continuation \
        --disable=missing-class-docstring \
        --disable=missing-function-docstring \
        --disable=missing-module-docstring \
        ${1}
endef

check: check_test_data
	black --check --line-length 100 ${module}
	black --check --line-length 100 tests
	flake8 --max-line-length 100 ${module}
	flake8 --max-line-length 100 tests
	mypy ${module}
	mypy tests

check_data: check_test_data check_production_data

check_test_data:
	frictionless validate tests/data/datapackage.json

check_production_data:
	cd /root/.config/recurrator && frictionless validate ./datapackage.json

clean:
	rm --force --recursive .*_cache
	rm --force --recursive ${module}.egg-info
	rm --force --recursive ${module}/__pycache__
	rm --force --recursive tests/__pycache__
	rm --force --recursive mutants
	rm --force coverage.xml
	rm --force ${module}/_contexts.py

coverage: setup
	pytest --cov=${module} --cov-report=xml --verbose && \
	coverage report --show-missing

format:
	black --line-length 100 ${module}
	black --line-length 100 tests

init: check_production_data setup tests

install: recurrator/_contexts.py
	pip install --editable .

recurrator/_contexts.py: src/create_contexts.sh
	src/create_contexts.sh

linter:
	$(call lint, ${module})
	$(call lint, tests)

mutants: setup
	mutmut run

setup: clean install

tests:
	pytest --verbose tests

red: format
	pytest --verbose \
	&& git restore tests/*.py \
	|| (git add tests/*.py && git commit -m "🛑🧪 Fail tests")
	chmod g+w -R .

green: format
	pytest --verbose \
	&& (git add ${module}/*.py tests/*.py && git commit -m "✅ Pass tests") \
	|| git restore ${module}/*.py
	chmod g+w -R .

refactor: format
	pytest --verbose \
	&& (git add ${module}/*.py tests/*.py && git commit -m "♻️  Refactor ${message}") \
	|| git restore ${module}/*.py tests/*.py
	chmod g+w -R .

