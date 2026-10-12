"""Fig. 7: reported fatigue across the session by task order (LMM)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import effortdata as ed
from effortdata import models as M, style as S
from effortdata.run import save_results
S.use_style(); res = {}
def est(m, terms):
    c = M.coefs(m).set_index('term'); e = c.loc[list(terms)].reset_index(); e['term'] = list(terms.values()); return e, c
f = ed.prepare_fatigue()
f['tap'] = 1 - f.G; f['gf'] = (f.task_order == 'grip_first').astype(float); f['G_gf'] = f.G * f.gf
f['pb_c'] = f.prompt_block - f.prompt_block.mean()
m = M.fit_lmer('fatigue ~ G * gf + pb_c + (1 + G | id)', f)
e, c = est(m, {'G': 'Grip vs tapping (tap-first)', 'gf': 'Grip-first vs tap-first (tapping)', 'pb_c': 'Report in block (+1)', 'G:gf': 'Grip × grip-first'})
res['fatigue_order'] = dict(coefs=c.round(4).reset_index().to_dict('records'), singular=M.is_singular(m), n_order=f.groupby('task_order').id.nunique().to_dict())
no = f.groupby('task_order').id.nunique()
fig = plt.figure(figsize=(7.2, 3.2)); gs = fig.add_gridspec(1, 3, width_ratios=[1.65, 1.65, 1.1], wspace=.3)
axs = []
for j, (to, lab) in enumerate([('tap_first', f'Tap first (n = {no["tap_first"]})'), ('grip_first', f'Grip first (n = {no["grip_first"]})')]):
    a = fig.add_subplot(gs[j], sharey=axs[0] if axs else None); axs.append(a); g = f[f.task_order == to]
    a.axvspan(.5, 3.5, color='#ededed', lw=0); a.axvspan(11.5, 14.5, color='#ededed', lw=0); a.axvline(11.5, color='#666', lw=.4)
    b = g.groupby('id').base_fatigue.first(); S.whiskerbox(a, 0, b, '#808080', .6); a.plot(0, b.mean(), 'o', color='#4d4d4d', ms=3)
    S.boxes_by(a, g.rename(columns={'prompt_all': 'x'}), 'x', 'fatigue', .6, offsets={})
    a.set_title(lab, fontweight='bold'); a.set_ylim(0, 100); a.set_xticks([0, 1, 4, 8, 11, 15, 19, 22], ['B', 1, 4, 8, 11, 15, 19, 22])
    if j: plt.setp(a.get_yticklabels(), visible=False)
axs[0].set_ylabel('Reported fatigue (1–100)'); axs[0].set_xlabel('Fatigue report (B = baseline; shaded = familiarisation)', loc='left')
a = fig.add_subplot(gs[2]); S.est_panel(a, e, ylabel='Estimate [95% CI] (points)', title='Linear mixed model')
S.top_legend(fig, axs[0], y=.98); S.tag(axs[0], 'A', -.2); S.tag(a, 'B', -.35)
S.save(fig, '07_fatigue_by_order', 'fig07_fatigue_by_order')
save_results(__file__, res)
