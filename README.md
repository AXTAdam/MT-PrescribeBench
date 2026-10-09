<h1 align="center">MT-PrescribeBench</h1>

<p align="center">A benchmark for personalized, evidence-linked music-based intervention planning and song selection.</p>

<p align="center">
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-green" alt="License: MIT"></a>
  <img src="https://img.shields.io/badge/Main%20cases-102-2f6f9f" alt="102 main cases">
  <img src="https://img.shields.io/badge/Extended%20items-435-e07a45" alt="435 extended items">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776ab" alt="Python 3.10 or newer">
</p>

- <div align="center">
  <img src="./figures/MT-PrescribeBench_overview.png" alt="MT-PrescribeBench overview" width="100%">
</div>

---

## <img src="./figures/icon-overview.svg" width="30" alt=""> Overview

Music-based interventions must be adapted to a person's clinical context, therapeutic goals, treatment setting, intervention procedures, musical characteristics, and treatment schedule. These requirements make structured prescription planning and evidence-linked song selection difficult to evaluate with generic language-model tests.

MT-PrescribeBench is a case-based benchmark for evaluating these capabilities. It connects literature-derived intervention records with structured reference answers and targeted reasoning tasks. The release is intended for reproducible research evaluation and supports field-level error analysis.

The benchmark contains:

- **102 main evaluation cases** for structured prescription generation;
- **180 Critical Slot Selection items** for prescription completion;
- **64 treatment-goal matching items**;
- **93 clinical-context matching items**;
- **98 Song-Level Recommendation items** for selecting evidence-linked songs from candidate lists.

The main task covers 13 prescription fields across music features, therapy configuration, dose and delivery, setting, and combination therapy. Scoring includes categorical accuracy, multi-label F1, temporal-structure F1, and symmetric BPM/tempo mean absolute error. Extension tasks use task-specific accuracy or exact-match rules.

## <img src="./figures/icon-resources.svg" width="30" alt=""> Resources

- `Benchmarks/Main evaluation task/`: the 102 case questions and their structured gold cards.
- `Benchmarks/Targeted extended tasks/`: gold cards and question files for the four targeted tasks.
- `Data Source/MTDP1.0.xlsx`: literature-level music-based intervention records.
- `Data Source/MCUD1.0.xlsx`: song-level clinical-use records and musical metadata.
- `Code/score.py`: field-level scoring utilities.
- `Code/Benchmark_Prompts.py`: public prompt templates.
- `Outputs/`: released raw and evaluated example results with neutral model labels.

## <img src="./figures/icon-reproduce.svg" width="30" alt=""> Reproducibility

The public package uses repository-relative paths. Provider-specific runtime adapters, credentials, endpoints, and private execution configuration are excluded from the release.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install pandas openpyxl jupyter
python -m py_compile Code\score.py Code\Benchmark_Prompts.py
```

The notebooks in `Code/` document the public execution and evaluation workflow. To run a model locally, supply a compatible provider adapter through your own environment and keep all credentials outside the repository.

## <img src="./figures/icon-evaluation.svg" width="30" alt=""> Evaluation Tasks

### Main evaluation task

Each case presents a patient or clinical context, therapeutic goals, and scenario constraints. The system produces a structured intervention prescription. The scorer evaluates fixed-value categorical fields, multi-label fields, duration/frequency/study-period components, and BPM/tempo using symmetric nearest-neighbor MAE.

### Targeted extended tasks

1. **Prescription completion:** select missing fields from controlled options.
2. **Treatment-goal matching:** distinguish prescriptions associated with different goals in a shared context.
3. **Clinical-context matching:** distinguish prescriptions associated with different clinical contexts under a shared goal.
4. **Song-Level Recommendation:** select three evidence-linked songs from eight visible candidates.

## <img src="./figures/icon-use.svg" width="30" alt=""> How to Use

1. Open the relevant workbook in `Benchmarks/`.
2. Use the question columns as model inputs.
3. Save model responses in the corresponding output schema.
4. Apply the functions in `Code/score.py` or use `evaluate_benchmarks.ipynb`.
5. Report field-level and task-level metrics together with the benchmark version.

The benchmark is designed for research evaluation. It does not provide clinical advice and should not be used to make unsupervised treatment decisions.

## <img src="./figures/icon-citation.svg" width="30" alt=""> Citation

If you use MT-PrescribeBench, please cite the accompanying article and this repository. The final article citation will be added after publication.

```text
MT-PrescribeBench. Data and evaluation package.
https://github.com/AXTAdam/MT-PrescribeBench
```

## <img src="./figures/icon-contact.svg" width="30" alt=""> Contact

For questions about the benchmark, please open a GitHub issue. Do not include API credentials, private patient information, or unpublished model outputs in an issue.

## License

The public code and release materials are distributed under the MIT License where applicable. Please check the original source-paper and dataset terms before redistributing source-derived data.
