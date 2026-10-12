"""Derived trial-level data (same definitions as the thesis analysis repository)."""
import numpy as np, pandas as pd
from .config import cache_dir
from .load import load_table, iter_runs, cohort_ids

def raw_trial_features(refresh=False, dir=None) -> pd.DataFrame:
    """Per trial from the raw uploads: grip held-force/target ratio, execution time, tap timing. Cached in cache/."""
    cf = cache_dir() / 'raw_trial_features.csv'
    if cf.exists() and not refresh: return pd.read_csv(cf)
    rows = []
    for uid, run in iter_runs(dir):
        for i, t in enumerate(run['trials'], start=1):
            tgt = t.get('target_value'); ok = tgt not in (None, 0)
            so = t.get('selected_option') or {}
            r = dict(upload_id=uid, overall_ordinal=i, modality=t['modality'], trial_kind=t['trial_kind'],
                     trial_index=t['trial_index'], raw_effort=so.get('effort_percent'))
            fs = t.get('force_samples') or []
            if fs:   # all stored samples (as in the thesis)
                f = np.array([s.get('measured_force') or 0.0 for s in fs], float)
                h = f[np.array([bool(s.get('holding')) for s in fs])]
                r.update(hold_mean_ratio=(h.mean() / tgt) if len(h) and ok else np.nan, exec_ms=fs[-1]['t_ms'])
            if t['modality'] == 'tap':
                ev = t.get('tap_events') or []
                r.update(n_ev=len(ev), t_first=ev[0]['t_ms'] / 1000 if ev else np.nan, t_last=ev[-1]['t_ms'] / 1000 if ev else np.nan)
            rows.append(r)
    x = pd.DataFrame(rows); x.to_csv(cf, index=False); return x

def prepare_trials(dir=None) -> pd.DataFrame:
    tr = load_table('trials', dir=dir); rs = load_table('run_summary', dir=dir)[['upload_id', 'task_order']]
    raw = raw_trial_features(dir=dir).drop(columns=['modality', 'trial_kind', 'trial_index'])
    tr = tr.merge(raw, on=['upload_id', 'overall_ordinal'], how='left').merge(rs, on='upload_id')
    tr['id'] = tr.upload_id.astype(str)
    tr['G'] = (tr.modality == 'grip').astype(float)
    tr['period'] = ((tr.modality == 'grip') == (tr.task_order == 'tap_first')).astype(float)   # 1 = second block
    tr['order_gf'] = (tr.task_order == 'grip_first').astype(float)
    tr['t_start'] = pd.to_datetime(tr.started_at)
    tr['min_from_start'] = (tr.t_start - tr.groupby('upload_id').t_start.transform('min')).dt.total_seconds() / 60
    return tr

def core_trials(dir=None) -> pd.DataFrame:
    """Core choice trials (60 per task and person) with model variables. R = extra coins, E = extra effort per 10 pp."""
    d = prepare_trials(dir); d = d[d.offer_category == 'core'].copy()
    d['y'] = d.hard_chosen.astype(str).str.lower().isin(['true', '1']).astype(int)
    d['R'] = d.extra_reward; d['E'] = d.extra_effort_pct / 10
    d['prog'] = (d.trial_index - 38.5) / 76; d['tap'] = 1 - d.G
    for v in ['R', 'E']: d[v + '_t'] = d[v] * d.tap; d[v + '_g'] = d[v] * d.G
    d['grip'] = d.G
    assert len(d) == 120 * d.upload_id.nunique()
    return d.reset_index(drop=True)

def fam_trials(dir=None) -> pd.DataFrame:
    """Familiarisation trials (7 targets x 5 repetitions per task) with objective execution measures."""
    tr = prepare_trials(dir); fa = tr[tr.trial_kind == 'familiarization'].copy()
    cal = load_table('calibration', dir=dir).pivot(index='upload_id', columns='measure', values='value').reset_index()
    fa = fa.merge(cal, on='upload_id'); fa['target'] = fa.raw_effort.astype(float)
    grip = fa.modality == 'grip'
    fa['success'] = fa.success.astype(str).str.lower().isin(['true', '1'])
    fa['time'] = np.where(grip, fa.exec_ms / 1000, fa.t_last)                                   # time to criterion (s)
    fa['tap_rate'] = np.where(~grip & (fa.n_ev >= 2), (fa.n_ev - 1) / (fa.t_last - fa.t_first), np.nan)
    fa['cal_rate'] = fa.tap_response_vigor_taps / 10                                             # calibrated taps/s
    fa['realised'] = np.where(grip, fa.hold_mean_ratio * fa.target, 100 * fa.tap_rate / fa.cal_rate)
    fa['rating'] = fa.subjective_effort_rating
    fa['sub_disp'] = fa.rating - fa.target
    fa['rep'] = np.ceil(fa.trial_index / 7).astype(int); fa['rep_c'] = fa.rep - 3
    fa['tgt10'] = (fa.target - 50) / 10
    assert len(fa) == 70 * fa.upload_id.nunique()
    return fa.reset_index(drop=True)

def prepare_fatigue(dir=None) -> pd.DataFrame:
    f = load_table('fatigue', dir=dir); rs = load_table('run_summary', dir=dir)[['upload_id', 'task_order']]
    q = load_table('questionnaire', dir=dir)
    base = q[(q.section == 'baseline') & (q.item == 'state_fatigue')][['upload_id', 'value']].rename(columns={'value': 'base_fatigue'})
    base['base_fatigue'] = base.base_fatigue.astype(float)
    f = f.merge(rs, on='upload_id').merge(base, on='upload_id').sort_values(['upload_id', 'minutes_from_run_start'])
    f['prompt_all'] = f.groupby('upload_id').cumcount() + 1
    f['prompt_block'] = f.groupby(['upload_id', 'modality']).cumcount() + 1
    f['G'] = (f.modality == 'grip').astype(float)
    f['phase'] = np.where(f.top_level_phase.str.contains('Familiarization'), 'familiarisation', 'choice')
    f['id'] = f.upload_id.astype(str)
    return f.reset_index(drop=True)
