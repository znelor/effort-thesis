# effort-thesis

Analyses and figures for the master thesis (grip vs. tapping, N = 31). No data in the repo.

## Setup

```bash
# R >= 4.3 with lme4 (used by pymer4)
Rscript -e 'install.packages(c("lme4","lmerTest","emmeans"))'
# Python >= 3.11
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

## Data

Copy these files into `data/` (git-ignored):

| Data file | Copy to |
|---|---|
| `trials.csv` | `data/thesis_data_main/31-participants-2026-09-06/tables/trials.csv` |
| `fatigue.csv` | `data/thesis_data_main/31-participants-2026-09-06/tables/fatigue.csv` |
| `calibration.csv` | `data/thesis_data_main/31-participants-2026-09-06/tables/calibration.csv` |
| `questionnaire.csv` | `data/thesis_data_main/31-participants-2026-09-06/tables/questionnaire.csv` |
| `run_summary.csv` | `data/thesis_data_main/31-participants-2026-09-06/tables/run_summary.csv` |
| `analysis-cohort.json` | `data/thesis_data_main/vps-export-2026-09-28/analysis-cohort.json` |
| `upload-NNNN.json.gz` (raw uploads) | `data/thesis_data_uploads1/` (or `data/thesis_data_uploads2/`) |

Simplest: copy the whole `thesis_data_main/`, `thesis_data_uploads1/` and `thesis_data_uploads2/` folders into `data/`.
Data somewhere else: `export EFFORT_DATA_DIR=/path/to/data`.

## Run

```bash
./run_all.sh                                     # everything (~5 min)
.venv/bin/python figures/03_choices/make_figure.py   # one analysis
```

## Analyses → output

| Analysis | Output |
|---|---|
| `figures/01_effort_ratings` | `output/01_effort_ratings/fig01_effort_ratings.{png,pdf}` |
| `figures/02_familiarisation` | `output/02_familiarisation/fig02_familiarisation.{png,pdf}` |
| `figures/03_choices` | `output/03_choices/fig03_choices.{png,pdf}` |
| `figures/04_choice_matrix` | `output/04_choice_matrix/fig04_choice_matrix.{png,pdf}` |
| `figures/05_choices_glmm` | `output/05_choices_glmm/fig05_choices_glmm.{png,pdf}` |
| `figures/06_exchange_rate` | `output/06_exchange_rate/fig06_exchange_rate.{png,pdf}` |
| `figures/07_fatigue_by_order` | `output/07_fatigue_by_order/fig07_fatigue_by_order.{png,pdf}` |
| `figures/08_per_person_glmm` | `output/08_per_person_glmm/fig08_per_person_glmm.{png,pdf}` |

Model numbers of each analysis: `figures/NN_*/out/results.json` (not tracked).
Shared code (paths, loading, the choice model): `effortdata/`.
