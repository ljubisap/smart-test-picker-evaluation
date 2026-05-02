# Apache Commons Lang — Evaluation Replication Package

Replication package for Smart Test Picker (RAD 1) safety evaluation on Apache Commons Lang 3.21.0-SNAPSHOT.

**Result: 99.87% inclusiveness (771/772 mutations safe), 99.64% test reduction.**

## Documentation

See [`docs/README.md`](docs/README.md) for full details including:
- Methodology and metrics
- Reproduction steps
- Baseline comparison
- Failure mode analysis

## Quick Verification

```bash
# Verify stored results
cat results/aggregated/evaluation_summary.json | python3 -m json.tool

# Re-run evaluation against existing PIT data (requires coverage map)
python3 scripts/03_evaluate.py --project-dir /path/to/commons-lang --results-dir results
```

## Scripts

| Script | Purpose |
|--------|---------|
| `00_sample_classes.py` | Generate `config/sample_classes.json` (deterministic) |
| `01_generate_coverage_map.py` | Run tests + generate per-test coverage map |
| `02_run_pit.py` | Run PIT per-class with fullMutationMatrix |
| `03_evaluate.py` | Evaluate plugin safety vs PIT ground truth |
| `04_baselines.py` | Compare proposed vs baseline selectors |
