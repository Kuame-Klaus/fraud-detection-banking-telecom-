# Klaus Konsults fraud detection, Python stack. All data is SYNTHETIC.
PY ?= python

.PHONY: install sample full full-export pipeline pipeline-full pipeline-committed-full charts test

install:
	$(PY) -m pip install -r requirements.txt

sample:          ## generate sample data (50k rows for B1, T1, T4) and refresh data/sample CSVs
	$(PY) -m python.synthetic.generate --mode sample --export-csv data/sample

pipeline:        ## run the six steps on the committed sample CSVs
	$(PY) -m python.pipeline.run --data data/sample --out outputs/sample --run-id python_sample

charts:
	$(PY) -m python.viz.charts --results outputs/sample/results_python_sample.parquet --out outputs/sample/charts

full:            ## full size (about 20M rows for B1, T1, T4); needs several GB of disk
	$(PY) -m python.synthetic.generate --mode full

pipeline-full:
	$(PY) -m python.pipeline.run --data data/synthetic/full --out outputs/full --run-id python_full

full-export:     ## rewrite full data as zstd parts of 90 MB or less plus data/full/manifest.json (committed)
	$(PY) -m python.synthetic.generate --mode full --reuse --export-full data/full

pipeline-committed-full:  ## run on the committed full parts
	$(PY) -m python.pipeline.run --data data/full --out outputs/full --run-id python_full

test:
	$(PY) -m pytest -q tests

all: sample pipeline charts test
