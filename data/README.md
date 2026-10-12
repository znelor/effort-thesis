# Data (not in git)

Copy the study data here (everything in this folder except this README is git-ignored):

```
data/thesis_data_main/31-participants-2026-09-06/tables/{trials,fatigue,calibration,questionnaire,run_summary}.csv
data/thesis_data_main/vps-export-2026-09-28/analysis-cohort.json      (cohort definition, pilots excluded)
data/thesis_data_uploads1/upload-NNNN.json.gz                          (raw run uploads; also thesis_data_uploads2/)
```

The raw uploads are needed for grip force / target, time to criterion and tap timing (familiarisation, Fig. 2 and 7b).
Same layout as the main analysis repository, so the same `data/` folder can be copied or symlinked.
To use data elsewhere: `data_dir:` in `config.yml` or the environment variable `EFFORT_DATA_DIR`.
