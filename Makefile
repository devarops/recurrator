all: check coverage mutants

.PHONY: \
		all \
		check \
		check_data \
		clean \
		coverage \
		format \
		install \
		linter \
		mutants \
		setup \
		test-shell \
		tests \
		verify

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
	rm --force ${module}/_config.py

coverage: setup
	pytest --cov=${module} --cov-report=xml --verbose && \
	coverage report --show-missing

format:
	black --line-length 100 ${module}
	black --line-length 100 tests

install: recurrator/_config.py
	pip install --editable .

recurrator/_config.py: src/create_config.sh
	src/create_config.sh

linter:
	$(call lint, ${module})
	$(call lint, tests)

mutants:
	mutmut run
	@survivors="$$(mutmut results | grep --count ': survived$$' || true)"; \
	if [ "$${survivors}" -ne 0 ]; then \
		echo "$${survivors} mutants survived; run mutmut results to list them"; \
		exit 1; \
	fi

setup: clean install

tests:
	pytest --ignore=mutants --ignore-glob='*_acceptance_*.py' --verbose

test-shell:
	shellspec

verify:
	qed verify specs
