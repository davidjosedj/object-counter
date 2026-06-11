# How to run this project:
# 1. make setup
# 2. make run          - dev mode, no Docker needed
#    make run-local    - real predictions, no Docker needed
# 3. make test
# ----------------------------------------------------------------------
# Production (requires Docker):
# 1. make model then make tfserving then make mongo or make postgres
# 2. make run-prod             - uses MongoDB by default
#    make run-prod-postgres    - uses PostgreSQL

.PHONY: setup model tfserving mongo postgres run run-local run-prod run-prod-postgres test test-verbose test-coverage clean

# ── Setup ──────────────────────────────────────────────────────────────────────
setup:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

# ── Model download (Unix) ──────────────────────────────────────────────────────
model:
	mkdir -p tmp/model/ssd_mobilenet_v2/1
	curl -L -o tmp/model.tar.gz \
	  http://download.tensorflow.org/models/object_detection/ssd_mobilenet_v2_coco_2018_03_29.tar.gz
	tar -xzvf tmp/model.tar.gz -C tmp/model
	mv tmp/model/ssd_mobilenet_v2_coco_2018_03_29/saved_model/saved_model.pb \
	   tmp/model/ssd_mobilenet_v2/1
	chmod -R 777 tmp/model
	rm tmp/model.tar.gz
	rm -rf tmp/model/ssd_mobilenet_v2_coco_2018_03_29

# ── Docker services ────────────────────────────────────────────────────────────
tfserving:
	docker run --rm -d \
	  --name=tfserving \
	  -p 8501:8501 \
	  --mount type=bind,source=$(shell pwd)/tmp/model,target=/models \
	  -e MODEL_NAME=ssd_mobilenet_v2 \
	  tensorflow/serving

mongo:
	docker run --rm --name test-mongo -p 27017:27017 -d mongo:latest

postgres:
	docker run --rm --name test-postgres \
	  -e POSTGRES_PASSWORD=password \
	  -e POSTGRES_DB=prod_counter \
	  -p 5432:5432 -d postgres:15

# ── Run ────────────────────────────────────────────────────────────────────────
run:
	PYTHONPATH=. python -m counter.entrypoints.webapp

run-local:
	PYTHONPATH=. ENV=local python -m counter.entrypoints.webapp

run-prod:
	PYTHONPATH=. ENV=prod python -m counter.entrypoints.webapp

run-prod-postgres:
	PYTHONPATH=. ENV=prod DB_TYPE=postgres POSTGRES_PASSWORD=password python -m counter.entrypoints.webapp

# ── Test ───────────────────────────────────────────────────────────────────────
test:
	PYTHONPATH=. pytest

test-verbose:
	PYTHONPATH=. pytest -v

test-coverage:
	PYTHONPATH=. pytest --cov=counter --cov-report=term-missing --cov-report=html

# ── Clean ──────────────────────────────────────────────────────────────────────
clean:
	rm -rf .venv tmp/debug __pycache__ .pytest_cache
