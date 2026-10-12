"""Figure 3: higher-demand choices per task (participant proportions) and choice curves of the choice GLMM."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
import numpy as np, pandas as pd, matplotlib.pyplot as plt
from scipy import stats
import effortdata as ed
from effortdata import models as M, style as S, choice as C
from effortdata.run import save_results
S.use_style(); rng = np.random.default_rng(20261009)
d = ed.core_trials(); m = C.fit(d)
pp = d.groupby(['id', 'modality']).y.mean().unstack()
diff = (pp.grip - pp.tap) * 100; bt = [rng.choice(diff.values, len(diff)).mean() for _ in range(5000)]
fig = plt.figure(figsize=(7.2, 3.0)); gs = fig.add_gridspec(1, 4, width_ratios=[1, .87, .87, .87], wspace=.35)
a = fig.add_subplot(gs[0])
for i, mo in enumerate(['tap', 'grip']):
    v = pp[mo].values; kde = stats.gaussian_kde(v, .35); yy = np.linspace(0, 1, 200); w = kde(yy); w = w / w.max() * .42
    xs = i + 1; side = -1 if mo == 'tap' else 1
    a.fill_betweenx(yy, xs + side * .05, xs + side * (.05 + w), color=S.COLS[mo], alpha=.5, lw=0)
for pid in pp.index: a.plot([1.12, 1.88], [pp.tap[pid], pp.grip[pid]], color='#b3b3b3', lw=.35, zorder=1)
jit = rng.uniform(-.03, .03, len(pp))
a.scatter(1.12 + jit, pp.tap, s=7, color=S.COLS['tap'], alpha=.8, zorder=2, lw=0); a.scatter(1.88 + jit, pp.grip, s=7, color=S.COLS['grip'], alpha=.8, zorder=2, lw=0)
for xs, mo in [(1.42, 'tap'), (1.58, 'grip')]:
    mm, lo, hi = S.tci(pp[mo]); a.vlines(xs, lo, hi, color='k', lw=1.1); a.plot(xs, mm, 'o', color='k', ms=3.5)
a.set_xticks([1, 2], ['Tapping', 'Grip']); a.set_xlim(.4, 2.6); a.set_ylim(0, 1.02); a.set_yticks([0, .25, .5, .75, 1], ['0%', '25%', '50%', '75%', '100%'])
a.set_ylabel('Higher-demand choices\n(proportion per participant)'); S.tag(a, 'A', -.42)
grid = pd.DataFrame([(mo, R, E) for mo in ['tap', 'grip'] for R in (1, 2, 3) for E in np.arange(2, 6.01, .1)], columns=['modality', 'R', 'E'])
pop = C.predict_pop(m, grid); per = C.predict_person(m, grid[np.isclose((grid.E * 10) % 5, 0) | np.isclose((grid.E * 10) % 5, 5)])
obs = d.groupby(['id', 'modality', 'R', 'E']).y.mean().reset_index()
axs = []
for j, R in enumerate((1, 2, 3)):
    a = fig.add_subplot(gs[j + 1], sharey=axs[0] if axs else None); axs.append(a)
    for mo in ['tap', 'grip']:
        for pid, g in per[(per.R == R) & (per.modality == mo)].groupby('id'): a.plot(g.E * 10, g.fit, color=S.COLS[mo], alpha=.12, lw=.4)
        g = pop[(pop.R == R) & (pop.modality == mo)]
        a.fill_between(g.E * 10, g.lo, g.hi, color=S.COLS[mo], alpha=.22, lw=0); a.plot(g.E * 10, g.fit, color=S.COLS[mo], lw=1.3, label=S.LABS[mo])
        o = obs[(obs.R == R) & (obs.modality == mo)].groupby('E').y.apply(S.tci); x = o.index.values * 10 + (-1.5 if mo == 'tap' else 1.5)
        a.vlines(x, [v[1] for v in o], [v[2] for v in o], color=S.COLS[mo], lw=.8)
        a.plot(x, [v[0] for v in o], 'o', mfc='white', mec=S.COLS[mo], ms=3.2, mew=.9)
    a.set_title(f'+{R} coin' + ('s' if R > 1 else '')); a.set_xticks(range(20, 61, 10)); a.set_ylim(0, 1.02)
    if j: plt.setp(a.get_yticklabels(), visible=False)
    else: a.set_yticks([0, .25, .5, .75, 1], ['0%', '25%', '50%', '75%', '100%']); a.set_ylabel('P(higher-demand choice)'); S.tag(a, 'B', -.42)
axs[1].set_xlabel('Additional effort of the higher-demand option (pp of capacity)')
S.top_legend(fig, axs[1], y=.98)
S.save(fig, '03_choices', 'fig03_choices')
save_results(__file__, dict(mean_p=pp.mean().to_dict(), diff_pp=float(diff.mean()), diff_boot_ci=[float(np.quantile(bt, .025)), float(np.quantile(bt, .975))],
    fewer_in_grip=int((diff < 0).sum()), more_in_grip=int((diff > 0).sum()), equal=int((diff == 0).sum()),
    coefs=M.coefs(m).round(4).to_dict('records'), singular=M.is_singular(m), varcorr=M.varcorr(m), convergence=M.converged(m)))
