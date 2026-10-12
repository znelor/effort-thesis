"""Figure 2: familiarisation - success, time to criterion, execution (grip force/target, taps per second),
realised intensity, rating minus displayed target. Asterisks: grip-tap contrasts per target level from an LMM, Holm-corrected."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import effortdata as ed
from effortdata import models as M, style as S
from effortdata.run import save_results
S.use_style()
fa = ed.fam_trials()
cap = fa.groupby('upload_id')[['sustained_grip_force_units', 'tap_response_vigor_taps']].first()
z = lambda v: (np.log(v) - np.log(v).mean()) / np.log(v).std(ddof=1)
fa = fa.merge(pd.DataFrame({'z_gcap': z(cap.sustained_grip_force_units), 'z_tcap': z(cap.tap_response_vigor_taps)}), left_on='upload_id', right_index=True)
fa['mod'] = pd.Categorical(fa.modality, ['tap', 'grip']); fa['tf'] = pd.Categorical(fa.target.astype(int).astype(str), [str(i) for i in range(20, 90, 10)])
fa['log_time'] = np.log(fa.time)
fs = fa[fa.success]
rhs = ' ~ mod * tf + mod * (z_gcap + z_tcap) + rep_c + period + (1 + mod | id)'
res, ct = {}, {}
for key, y, dat in [('time', 'log_time', fs.dropna(subset=['log_time'])), ('realised', 'realised', fs.dropna(subset=['realised'])),
                    ('sub_disp', 'sub_disp', fa.dropna(subset=['sub_disp']))]:
    m = M.fit_lmer(y + rhs, dat); c = M.task_contrasts_by_level(m, dat); ct[key] = c
    res[key] = dict(singular=M.is_singular(m), contrasts=c.round(4).to_dict('records'))
def stars(a, key):
    c = ct[key]; lv = c.level[c.p_holm < .05].astype(int); top = a.get_ylim()[1]
    for x in lv: a.text(x, top, '*', ha='center', va='top', fontsize=11)
pm = lambda d, v: d.groupby(['id', 'modality', 'target'], as_index=False)[v].mean().dropna()
fig = plt.figure(figsize=(7.4, 5.6)); gs = fig.add_gridspec(2, 3, hspace=.45, wspace=.42)
# A: success, full 0-100 % scale + count of failed trials (the old zoomed axis made a few failures look dramatic)
a = fig.add_subplot(gs[0, 0])
su = fa.groupby(['id', 'modality', 'target'], as_index=False).success.mean(); su['success'] *= 100
fails = fa.assign(f=~fa.success).groupby(['modality', 'target']).f.sum()
for mo in ['tap', 'grip']:
    r = su[su.modality == mo].groupby('target').success.apply(S.tci); x = r.index.values + S.OFF[mo]
    mm = np.array([v[0] for v in r]); lo = np.array([v[1] for v in r]); hi = np.minimum(100, [v[2] for v in r])
    a.vlines(x, lo, hi, color=S.COLS[mo], lw=1.2); a.plot(x, mm, 'o-', color=S.COLS[mo], ms=3.2, lw=1, label=S.LABS[mo])
for i, t in enumerate(range(20, 90, 10)):
    a.text(t, 8, f"{fails['tap', t]}\n{fails['grip', t]}", ha='center', va='bottom', fontsize=5.8, color='#444')
a.text(14.5, 20, 'failed trials\n(tap / grip,\nof 155 each)', fontsize=5.5, color='#444', va='bottom')
a.set_ylim(0, 105); a.set_xlim(12, 85); a.set_xticks(range(20, 90, 10)); a.set_xlabel('Target level (%)'); a.set_ylabel('Success (% of trials, mean ± 95% CI)')
# B: time to criterion
a = fig.add_subplot(gs[0, 1]); S.boxes_by(a, pm(fs, 'time'), 'target', 'time', 2.4)
a.set_xlim(15, 85); a.set_xticks(range(20, 90, 10)); a.set_ylim(0, a.get_ylim()[1] * 1.08); a.set_xlabel('Target level (%)'); a.set_ylabel('Time to criterion (s)'); stars(a, 'time')
# C: raw execution measure per task (two stacked axes)
sg = gs[0, 2].subgridspec(2, 1, hspace=.9)
a1 = fig.add_subplot(sg[0]); g = pm(fs[fs.modality == 'grip'], 'hold_mean_ratio'); a1.axhline(1, ls='--', lw=.5, color='k')
S.boxes_by(a1, g, 'target', 'hold_mean_ratio', 4, offsets={}, mods=('grip',)); a1.set_title('Grip: held force / target', fontsize=7.5, fontweight='bold')
a2 = fig.add_subplot(sg[1]); t = pm(fs[fs.modality == 'tap'], 'tap_rate')
S.boxes_by(a2, t, 'target', 'tap_rate', 4, offsets={}, mods=('tap',)); a2.set_title('Tapping: taps per second', fontsize=7.5, fontweight='bold')
for x in (a1, a2): x.set_xticks(range(20, 90, 20)); x.set_xlim(14, 86)
a2.set_xlabel('Target level (%)')
# D: realised intensity
a = fig.add_subplot(gs[1, 0]); a.plot([0, 100], [0, 100], 'k--', lw=.5); a.axhline(100, ls='--', lw=.5, color='k')
S.boxes_by(a, pm(fs, 'realised'), 'target', 'realised', 2.4); a.set_xlim(15, 85); a.set_xticks(range(20, 90, 10))
a.set_ylim(0, a.get_ylim()[1] * 1.06); a.set_xlabel('Target level (%)'); a.set_ylabel('Realised intensity\n(% of calibrated capacity)'); stars(a, 'realised')
# E: rating minus displayed target
a = fig.add_subplot(gs[1, 1]); a.axhline(0, ls='--', lw=.5, color='k'); S.boxes_by(a, pm(fa, 'sub_disp'), 'target', 'sub_disp', 2.4)
a.set_xlim(15, 85); a.set_xticks(range(20, 90, 10)); lo, hi = a.get_ylim(); a.set_ylim(lo, hi + .1 * (hi - lo))
a.set_xlabel('Target level (%)'); a.set_ylabel('Rating minus\ndisplayed target (points)'); stars(a, 'sub_disp')
for x, l in zip([fig.axes[0], fig.axes[1], a1, fig.axes[4], a], 'ABCDE'): S.tag(x, l, -.3, 1.04 if l != 'C' else 1.12)
S.top_legend(fig, fig.axes[1], y=.93)
nt = fig.add_subplot(gs[1, 2]); nt.axis('off')
nt.text(0, .95, 'Reading guide', fontweight='bold', fontsize=7.5, va='top')
nt.text(0, .83, 'C shows each task\'s own raw execution\nmeasure (not comparable across tasks).\nGrip: held force / target (1 = exactly on\ntarget). Tapping: taps per second\n(calibrated max. ~ 7/s). D puts both on\none scale (% of calibrated capacity).\n\nAll panels: successful trials, except A\n(all trials) and E (all rated trials).\nBoxes: person means; * = grip vs\ntapping, LMM, Holm-corrected p < .05.', fontsize=6.4, va='top', linespacing=1.35)
S.save(fig, '02_familiarisation', 'fig02_familiarisation')
tab = fs.groupby(['modality', 'target'])[['time', 'realised', 'tap_rate', 'hold_mean_ratio']].mean().round(3)
res['cell_means_successful'] = tab.reset_index().to_dict('records'); res['failed_trials'] = {f'{k[0]}_{k[1]}': int(v) for k, v in fails.items()}
res['success_rate'] = fa.groupby('modality').success.mean().to_dict()
save_results(__file__, res)
