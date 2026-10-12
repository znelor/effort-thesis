"""Figure 5: participant choice proportions by effort and by reward level; fixed effects of the choice GLMM in difference
parameterisation (tapping = reference). Also: ceiling check for tapping."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import effortdata as ed
from effortdata import models as M, style as S, choice as C
from effortdata.run import save_results
S.use_style()
d = ed.core_trials(); m = C.fit(d, diff=True)
c = M.coefs(m).set_index('term')
terms = {'R': 'Reward (+1 coin)', 'E': 'Effort (+10 pp)', 'G': 'Grip vs tapping', 'R:G': 'Reward × grip', 'E:G': 'Effort × grip'}
e = c.loc[list(terms)].reset_index(); e['term'] = list(terms.values())
pe = d.groupby(['id', 'modality', 'extra_effort_pct']).y.mean().reset_index()
pr = d.groupby(['id', 'modality', 'extra_reward']).y.mean().reset_index()
fig, ax = plt.subplots(1, 3, figsize=(7.2, 3.2), gridspec_kw=dict(width_ratios=[1.5, 1, .85], wspace=.35))
for a, df, x, w, off in [(ax[0], pe, 'extra_effort_pct', 2.6, S.OFF), (ax[1], pr, 'extra_reward', .14, dict(tap=.09, grip=-.09))]:
    for (pid, mo), g in df.groupby(['id', 'modality']): a.plot(g[x], g.y, color=S.COLS[mo], alpha=.12, lw=.4)
    S.boxes_by(a, df, x, 'y', w, offsets=off); a.set_ylim(-.02, 1.02); a.set_yticks([0, .25, .5, .75, 1], ['0%', '25%', '50%', '75%', '100%'])
ax[0].set_xticks(range(20, 61, 10)); ax[0].set_xlabel('Additional effort of the higher-demand option (pp)'); ax[0].set_ylabel('Higher-demand choices\n(per participant, all reward levels)')
ax[1].set_xticks([1, 2, 3]); ax[1].set_xlabel('Additional reward (coins)')
S.est_panel(ax[2], e, ylabel='Log-odds [95% CI]', title='Binomial GLMM')
S.top_legend(fig, ax[0], y=.97)
for a, t in zip(ax, 'ABC'): S.tag(a, t, -.25)
S.save(fig, '05_choices_glmm', 'fig05_choices_glmm')
# ---- ceiling check: how many participants (almost) always choose the higher-demand option, per task
pp = d.groupby(['id', 'modality']).y.mean().unstack()
cell = d.groupby(['id', 'modality', 'extra_effort_pct', 'extra_reward']).y.mean().reset_index()
at_ceiling = cell.assign(c=cell.y == 1).groupby('modality').c.mean()
low = pe[pe.extra_effort_pct == 20].pivot(index='id', columns='modality', values='y')
save_results(__file__, dict(coefs=c.round(4).reset_index().to_dict('records'), singular=M.is_singular(m),
    n_ge95=dict(tap=int((pp.tap >= .95).sum()), grip=int((pp.grip >= .95).sum())),
    n_eq100=dict(tap=int((pp.tap == 1).sum()), grip=int((pp.grip == 1).sum())),
    n_ge90=dict(tap=int((pp.tap >= .9).sum()), grip=int((pp.grip >= .9).sum())),
    n_le10=dict(tap=int((pp.tap <= .1).sum()), grip=int((pp.grip <= .1).sum())),
    share_person_cells_at_100=at_ceiling.round(3).to_dict(),
    median_p=pp.median().to_dict(),
    p_at_plus20_median=low.median().to_dict(), p_at_plus20_n100=dict(tap=int((low.tap == 1).sum()), grip=int((low.grip == 1).sum())),
    mean_by_effort=pe.groupby(['modality', 'extra_effort_pct']).y.mean().round(3).unstack().to_dict(),
    mean_by_reward=pr.groupby(['modality', 'extra_reward']).y.mean().round(3).unstack().to_dict()))
