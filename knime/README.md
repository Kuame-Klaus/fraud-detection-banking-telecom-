# KNIME

KNIME workflows (.knwf) implementing the same process as Python. They run the numbered steps in docs/pipeline_steps.md, including every reconciliation and data quality check, read the same files from data/synthetic/ using the column names in docs/data_dictionary.md, and write the shared tables in docs/output_schema.md.

For about 20 million rows: raise the -Xmx setting in knime.ini, use the columnar table backend, use streaming or chunk loops, read with the Parquet reader, and if needed train on a stratified sample while scoring the full set. Runtime and memory will be measured, not assumed.
