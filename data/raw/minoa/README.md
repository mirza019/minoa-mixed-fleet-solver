# MINOA Raw Data

This folder stores professor-provided MINOA challenge data.

The raw input files are treated as source data. The solver and pipeline do not
edit them in place. If an input needs a small compatibility normalization, the
pipeline writes a processed working copy under `data/processed/`, which is
ignored by Git and can be regenerated.

See `data/raw/minoa/senior/README.md` for the senior instance list.
