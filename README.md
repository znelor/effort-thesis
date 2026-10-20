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

## R analyses (mixed-effects models)

The `analyses/` directory contains R scripts for random-effects model comparison and covariate tests using `lme4`. These scripts depend on the **effortlib** R package (not included in this public repo).

### Setup

**effortlib dependency:** Set `EFFORT_LIB_DIR` to point to the effortlib package directory:

```bash
export EFFORT_LIB_DIR=/path/to/effort-thesis-analysis/effortlib
```

**Data:** Set `EFFORT_DATA_DIR` as described in the [Data](#data) section above, or place data files in `data/` as shown in the table.

### Scripts

**`analyses/random_effects_tests.R`** — Random-effects structure comparison

Compares three nested random-effects specifications of the binomial choice GLMM:
- **RV1**: Baseline correlated random intercept + reward/effort slopes  
- **RV2**: RV1 + uncorrelated random grip intercept (primary model)  
- **RV6**: Maximal task-specific random slopes (all fixed effects)

Tests likelihood-ratio tests (RV1 vs RV2, RV2 vs RV6), AIC/BIC comparison, singularity checks, and computes the exchange-rate ratio (k_grip / k_tap) with delta-method confidence intervals.

```bash
Rscript analyses/random_effects_tests.R
```

**Output:** `analyses/out/random_effects_models.rds`, `analyses/out/random_effects_comparison.csv`

**`analyses/covariate_tests.R`** — Person-level covariate 'knobs' tests

Tests whether person-level characteristics modulate choice behavior on top of the primary RV2 model:
- Hand span, log grip MVC, hand-use level  
- Tapping calibration, tapping experience level  
- Baseline fatigue, task order (grip-first vs tap-first)  
- Within-person fatigue (trial-level deviations + person means)

For each covariate: adds task-specific intercept shifts and interactions with relevant effort slopes to RV2, then performs likelihood-ratio tests with Holm correction.

```bash
Rscript analyses/covariate_tests.R
```

**Output:** `analyses/out/covariate_models.rds`, `analyses/out/covariate_lrt.csv`, `analyses/out/covariate_terms_*.csv`
