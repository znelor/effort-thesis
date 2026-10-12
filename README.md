# Effort valuation in gripping and tapping – supervisor figures

Core figures of the master thesis (N = 31; effort-based choices, grip vs tapping), with the code that makes them.
**No participant data are included.** The overview with explanations (German) is [`docs/supervisor_figures.pdf`](docs/supervisor_figures.pdf).

Hypotheses: larger rewards increase (H1) and larger efforts decrease (H2) choices of the higher-demand option;
the effort-to-reward exchange rate k = −β_E/β_R is higher for gripping than for tapping (H3).

## Layout

```
effortdata/     Python package: data paths (config.py), loaders (load.py), derived variables (derive.py),
                the one choice model (choice.py), pymer4/lme4 helpers (models.py), figure style (style.py)
figures/NN_*/   one folder per figure: make_figure.py (+ out/results.json with model output, git-ignored)
output/NN_*/    the figures (PNG 300 dpi + vector PDF), tracked
docs/           supervisor_figures.pdf and build_pdf.py
data/           put the data here (git-ignored except data/README.md)
config.yml      data folder and data layout
run_all.sh      makes all figures and the PDF
```

| Folder | Figure |
|---|---|
| `01_effort_ratings` | Effort ratings in familiarisation; LMM |
| `02_familiarisation` | Success, time to criterion, execution, realised intensity, rating − target |
| `03_choices` | Higher-demand choices; choice curves of the choice GLMM |
| `04_choice_matrix` | P(higher-demand) per offer cell (effort × reward), per task and grip − tap |
| `05_choices_glmm` | Choices by effort and reward level; GLMM fixed effects; ceiling check |
| `06_exchange_rate` | Exchange rate k per task and k_grip/k_tap (one model) |
| `07_fatigue_timing` | 7a fatigue by task order; 7b time-on-task in familiarisation; 7c timing effects in choices |
| `08_per_person_glmm` | Per-person conditional slopes and k |

All choice figures use **one** model (`effortdata/choice.py`): binomial GLMM with task-specific intercepts and reward/effort
slopes, no covariates, independent per-person random intercept, grip offset and task-specific reward and effort slopes.

## Setup

1. **R ≥ 4.3** with `lme4`, `lmerTest`, `emmeans`, `broom`, `broom.mixed`, `report`, `performance`
   (`Rscript -e 'install.packages(c("lme4","lmerTest","emmeans","broom","broom.mixed","report","performance"))'`).
2. **Python ≥ 3.11**: `python -m venv .venv && .venv/bin/pip install -r requirements.txt`
   (pymer4 calls lme4 through rpy2; on Linux rpy2 may need `python3-dev`).
3. **Data**: copy the study data into `data/`, layout in [`data/README.md`](data/README.md).
   Data elsewhere: set `data_dir` in `config.yml` or `export EFFORT_DATA_DIR=/path/to/data`.
4. Font: Open Sans (falls back to DejaVu Sans). The PDF builder needs static Open Sans TTFs in `~/.local/share/fonts` or `docs/fonts/`
   (`OpenSans-400.ttf`, `OpenSans-700.ttf`).

## Running

```
./run_all.sh                     # all figures + docs/supervisor_figures.pdf (≈ 5 min)
.venv/bin/python figures/06_exchange_rate/make_figure.py   # a single figure, from any folder
```

The first run parses the raw uploads once and caches per-trial features in `cache/` (git-ignored).
