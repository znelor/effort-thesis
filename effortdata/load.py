"""Loaders: exported tables (analysis cohort only, pilots excluded) and raw run uploads."""
import json, gzip, glob, re
import pandas as pd
from .config import tables_dir, export_dir, data_dir, config

def cohort_ids(dir=None) -> list:
    j = json.load(open(export_dir(dir) / 'analysis-cohort.json'))
    r = pd.DataFrame(j['runs']); r = r[r.include_in_main_trial_analysis & ~r.upload_id.isin(j['pilot_upload_ids'])]
    return sorted(r.upload_id.astype(int).tolist())

def load_table(name, cohort_only=True, dir=None) -> pd.DataFrame:
    """name: trials, fatigue, calibration, questionnaire, run_summary"""
    x = pd.read_csv(tables_dir(dir) / f'{name}.csv')
    return x[x.upload_id.isin(cohort_ids(dir))].copy() if cohort_only and 'upload_id' in x else x

def upload_files(dir=None) -> dict:
    fs = glob.glob(str(data_dir(dir) / config()['uploads_glob']))
    if not fs: raise FileNotFoundError(f"No raw uploads matching {config()['uploads_glob']} in {data_dir(dir)}")
    return {int(re.search(r'upload-0*(\d+)\.json\.gz$', f).group(1)): f for f in fs}

def upload_run(upload_id, dir=None) -> dict:
    u = json.load(gzip.open(upload_files(dir)[int(upload_id)]))
    return list(u['payload']['participants'].values())[0]['study_runs'][0]

def iter_runs(dir=None):
    for uid in cohort_ids(dir): yield uid, upload_run(uid, dir)
