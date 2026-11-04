# Fraud detection Power BI project (PBIP)

A Klaus Konsults project. All data in this project is SYNTHETIC. Banking and telecom are separate entities and are never joined. SIM swap uses telecom data only.

This folder is a Power BI Project (PBIP): a semantic model in TMDL (FraudDetection.SemanticModel) and a report in the PBIR folder format (FraudDetection.Report). It has 12 pages as set out in docs/powerbi_design.md, Klaus Konsults theme D, Arial throughout, a star schema and DAX measures. The default model is logistic regression; XGBoost is optional.

## What is inside

1. FraudDetection.pbip: open this file.
2. data/sample/results_latest.csv: the 50k sample results from the Python pipeline (run python_sample), bundled so the report works offline. SYNTHETIC.
3. data/sample/model_drivers.md: plain English list of the top logistic regression drivers for the sample run.

## Open steps

1. You need Power BI Desktop (a recent release) on Windows.
2. Unzip or copy this folder to C:\FraudDetection so that C:\FraudDetection\FraudDetection.pbip exists. If you use another folder, see step 5.
3. In Power BI Desktop, go to File, Options and settings, Options, Preview features, and turn on Power BI Project (.pbip) save option and Store reports using enhanced metadata format (PBIR) if they are not already on. Restart if asked.
4. Open FraudDetection.pbip. The report opens with no data yet.
5. If the folder is not C:\FraudDetection, go to Home, Transform data, Edit parameters, and set pLocalFolder to your folder, ending with a backslash, for example D:\Work\FraudDetection\.
6. Click Refresh. Power BI loads the bundled sample. If asked about privacy levels, choose Public for the GitHub source and Organizational or Public for the local file; the data is synthetic.
7. Page 12 uses the built in Map visual. If it shows a message, go to File, Options and settings, Options, Security, and allow Map and Filled Map visuals.

## Switch to full data

1. Home, Transform data, Edit parameters.
2. Set pDataSource to github_full. The other values are local_sample (the default, bundled file) and github_sample (the same sample read from GitHub).
3. Click Refresh. Power BI reads outputs/full/results_parts/manifest.json from the repo and combines the three Parquet parts (about 170 MB in total, 7,472,706 rows). This needs internet access and a few minutes and plenty of memory.

The base address is the parameter pBaseUrl, set to https://raw.githubusercontent.com/Kuame-Klaus/fraud-detection-banking-telecom-/main/

Full results folder: https://github.com/Kuame-Klaus/fraud-detection-banking-telecom-/tree/main/outputs/full/results_parts
Repo data folder (SYNTHETIC input data): https://github.com/Kuame-Klaus/fraud-detection-banking-telecom-/tree/main/data

## Model choice

Score pages (1, 3, 5, 7) carry a page filter on DimModel set to logistic_regression. To show XGBoost, run the pipeline with --model xgboost, refresh, and change that filter to xgboost in the filter pane. The bundled sample only holds logistic regression and rule rows.

## Data model

One staging query, Results, reads the shared results file (docs/output_schema.md) and is not loaded. Each fact table is one record_type: FactScore, FactMetric, FactDQ, FactCoverage, FactThreshold, FactDrift, FactAgreement, FactEdge, FactBenford, FactGeo, FactRun, FactPRCurve, FactCoefficient. Dimensions: DimDomain, DimScenario (keyed on domain and scenario), DimDataset (keyed on domain and dataset), DimStack, DimModel, DimMonth, DimDate and the Threshold change table. DimDomain filters DimScenario and DimDataset, so picking banking never shows a telecom scenario or dataset. FactAgreement has no rows yet, because only the Python stack has run.

## Known limits

1. This project was generated as files and checked for JSON schema and TMDL syntax. It has not yet been opened in Power BI Desktop, so expect small fixes on first open.
2. Page 6 needs a custom network visual (spec in docs/powerbi_design.md). Installing it needs approval on the tenant, so the page holds a placeholder note, a top senders bar chart and the full link table for now.
3. Cell site locations on page 12 are SYNTHETIC, not real sites, and must be replaced with the client's site list.
4. Thresholds were tuned on synthetic data and must be retuned on real data.
5. On the Power BI Service, refresh from the local file needs a gateway; use github_sample or github_full there, with Anonymous access and privacy level Public.
