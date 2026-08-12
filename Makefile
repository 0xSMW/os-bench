.PHONY: install test validate dataset graph doctor smoke full-selftest payload reference-build reference-boot reference-inventory clean

install:
	python3 -m pip install -e '.[dev]'

test:
	pytest

validate:
	osbench contracts validate
	osbench dataset validate
	osbench results validate results/isolated-smoke-final.json

dataset:
	osbench dataset build --profile public --seed 1 --cases-per-contract 10 --check-determinism

graph:
	osbench graph build

doctor:
	osbench doctor

smoke:
	OSBENCH_REFERENCE_MODE=local osbench smoke

full-selftest:
	OSBENCH_REFERENCE_MODE=local osbench oracle full-selftest --shard-count 16 --jobs 8 --output results/full-local-selftest.json

payload:
	osbench payload build

reference-build:
	osbench reference build

reference-boot:
	osbench reference boot

reference-inventory:
	osbench reference inventory

clean:
	rm -rf .pytest_cache .ruff_cache src/*.egg-info src/osbench/__pycache__ tests/__pycache__
