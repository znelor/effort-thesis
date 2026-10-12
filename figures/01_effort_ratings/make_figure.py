"""Figure 1: effort ratings during familiarisation (whisker boxes by target; per-person rating slopes; LMM estimates)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
import numpy as np, matplotlib.pyplot as plt
import effortdata as ed
from effortdata import models as M, style as S
from effortdata.run import save_results
S.use_style()
fa = ed.fam_trials()
# LMM: rating ~ task * target + task * repetition + second block + (1 + task * target | person)
m = M.fit_lmer('subjective_effort_rating ~ G * tgt10 + G * rep_c + period + (1 + G * tgt10 | id)', fa)
c = M.coefs(m).set_index('term')
terms = {'G': 'Grip vs tapping', 'tgt10': 'Target (+10 pp)', 'G:tgt10': 'Grip × target', 'rep_c': 'Repetition',
         'G:rep_c': 'Grip × repetition', 'period': 'Second block'}
e = c.loc[list(terms)].reset_index(); e['term'] = list(terms.values())
er = fa.dropna(subset=['rating']).groupby(['id', 'modality', 'target'], as_index=False).rating.mean()
sl = er.groupby(['id', 'modality']).apply(lambda g: np.polyfit(g.target, g.rating, 1)[0], include_groups=False).unstack()
fig, ax = plt.subplots(1, 3, figsize=(7.2, 3.1), gridspec_kw=dict(width_ratios=[1.6, 1, .85]))
a = ax[0]; a.plot([0, 100], [0, 100], 'k--', lw=.5); S.boxes_by(a, er, 'target', 'rating', 2.4)
a.set_xlim(15, 85); a.set_ylim(0, 100); a.set_xticks(range(20, 90, 10)); a.set_xlabel('Target level (% of calibrated capacity)'); a.set_ylabel('Effort rating (1–100)')
S.top_legend(fig, ax[0])
a = ax[1]; lim = [sl.values.min() - .05, sl.values.max() + .05]; a.plot(lim, lim, 'k--', lw=.5)
a.scatter(sl.tap, sl.grip, s=16, c='#595959', edgecolors='white', linewidths=.4); a.set_xlim(lim); a.set_ylim(lim); a.set_aspect('equal')
a.set_xlabel('Rating slope, tapping\n(points per pp)'); a.set_ylabel('Rating slope, grip\n(points per pp)')
S.est_panel(ax[2], e, title='Linear mixed model')
for x, t in zip(ax, 'ABC'): S.tag(x, t, -.25)
fig.tight_layout(); S.save(fig, '01_effort_ratings', 'fig01_effort_ratings')
save_results(__file__, dict(n_obs=int(m.r_model.do_slot('frame').nrow) if False else int(fa.rating.notna().sum()),
    coefs=c.round(4).reset_index().to_dict('records'), singular=M.is_singular(m), convergence=M.converged(m),
    varcorr=M.varcorr(m), slope_grip_gt_tap=int((sl.grip > sl.tap).sum()), n=len(sl),
    median_slope=dict(tap=float(sl.tap.median()), grip=float(sl.grip.median()))))
