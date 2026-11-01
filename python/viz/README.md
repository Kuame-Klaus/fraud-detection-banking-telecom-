# Python charts

Builds charts from the shared results file (`--results`), reading only the columns each chart needs. Run `python -m python.viz.charts --results outputs/sample/results_python_sample.parquet --out outputs/sample/charts`.

Charts produced (11): 01 to 11 as in docs/charts.md, including 05_risk_leaderboards.png (top entities by alerts, red when the entity has a planted case), 06_networks.png (mule account and agent to wallet hubs), 09_threshold_sensitivity.png and the interactive 09_threshold_slider.html. Chart 12 (route map) is not built. All values come from SYNTHETIC data. Alteryx and KNIME results are shown only once those tools have produced results files.
