# Alteryx

Alteryx workflows (.yxmd) implementing the same six stages as Python (docs/pipeline_steps.md): load and control totals, data quality checks, features, scenario rules, model using Alteryx built in learners, and shared results output. They run the numbered steps in docs/pipeline_steps.md, including every reconciliation and data quality check, read the same files from data/synthetic/ using the column names in docs/data_dictionary.md, and write the shared results file in docs/output_schema.md.

For about 20 million rows: use the AMP engine, raise the sort and join memory setting, give temp files ample disk space, use chunked inputs or the In Database tools, and expect long runtimes on a desktop. Runtime and memory will be measured, not assumed.
