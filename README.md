# MT-PrescribeBench Data and Evaluation Package

This directory contains the MT-PrescribeBench benchmark.

## Contents

- `Benchmarks/`: main and targeted benchmark files.
- `Data Source/`: released source tables used by the benchmark.
- `Code/score.py`: field-level scoring utilities.
- `Code/Benchmark_Prompts.py`: public prompt templates.
- `Code/run_benchmarks.ipynb`: provider-agnostic execution template. API credentials and provider-specific adapters must be supplied locally.
- `Code/evaluate_benchmarks.ipynb`: evaluation template.
- `Outputs/`: released example outputs and evaluated results.

## Reproducibility

Use Python 3.10 or newer with `pandas` and `openpyxl`. All paths in the public code are relative to this directory. 

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install pandas openpyxl jupyter
python -m py_compile Code\score.py Code\Benchmark_Prompts.py
```

The benchmark contains 102 main evaluation cases and 435 targeted extension items: 180 critical-slot items, 64 treatment-goal items, 93 clinical-context items, and 98 song-level recommendation items.

## Data use

Please check the source-paper and dataset licenses before redistribution or commercial use. The benchmark is intended for research evaluation and does not provide clinical advice.

## Citation

