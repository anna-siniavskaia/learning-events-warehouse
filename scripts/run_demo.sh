#!/bin/sh
set -eu

python src/generate_events.py --seed 42 --count 100 --output data/events.jsonl
python src/load_source.py data/events.jsonl
python src/sync_warehouse.py --batch-size 25
python src/build_mart.py --batch-size 25
python src/check_pipeline.py
python src/check_mart.py
python -m unittest discover -s tests -v
