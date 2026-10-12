"""Figure 7 (appendix-type): per-person conditional effort and reward slopes and k from the choice GLMM, grip vs tapping."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import effortdata as ed
from effortdata import models as M, style as S, choice as C
from effortdata.run import save_results
S.use_style()
d = ed.core_trials(); m = C.fit(d); pk = C.person_slopes(m)
pk['k_tap'] = -pk.E_t / pk.R_t; pk['k_grip'] = -pk.E_g / pk.R_g
fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.7), gridspec_kw=dict(wspace=.5))
def sc(a, x, y, xl, yl, log=False):
    v = np.r_[x, y]; lim = [v.min(), v.max()]; pad = .05 * (lim[1] - lim[0]); lim = [lim[0] - pad, lim[1] + pad]
    if log: lim = [v.min() * .85, v.max() * 1.15]; a.set_xscale('log'); a.set_yscale('log')
    a.plot(lim, lim, '--', color='#737373', lw=.6); a.scatter(x, y, s=17, c='#595959', edgecolors='white', linewidths=.4, zorder=3)
    a.set_xlim(lim); a.set_ylim(lim); a.set_aspect('equal')
    if log:
        tk = [t for t in [.1, .2, .5, 1, 2, 5, 10] if lim[0] <= t <= lim[1]]
        for ax_ in (a.xaxis, a.yaxis): ax_.set_major_locator(plt.FixedLocator(tk)); ax_.set_major_formatter(plt.FixedFormatter([f'{t:g}' for t in tk])); ax_.set_minor_formatter(plt.NullFormatter()); a.set_xlabel(xl); a.set_ylabel(yl)
sc(ax[0], pk.E_t, pk.E_g, 'Effort slope, tapping', 'Effort slope, grip')
sc(ax[1], pk.R_t, pk.R_g, 'Reward slope, tapping', 'Reward slope, grip'); ax[1].axhline(0, color='#cccccc', lw=.4); ax[1].axvline(0, color='#cccccc', lw=.4)
ok = (pk.R_t > 0) & (pk.R_g > 0); sc(ax[2], pk.k_tap[ok], pk.k_grip[ok], '$k$ tapping', '$k$ grip', log=True)
ax[2].set_title(f'n = {ok.sum()} with positive reward slopes in both tasks', fontsize=6.5)
for a, t in zip(ax, 'ABC'): S.tag(a, t, -.35)
S.save(fig, '08_per_person_glmm', 'fig08_per_person_glmm')
save_results(__file__, dict(n=len(pk), n_k_defined=int(ok.sum()), nonpos_R=dict(tap=int((pk.R_t <= 0).sum()), grip=int((pk.R_g <= 0).sum())),
    effort_steeper_grip=int((pk.E_g < pk.E_t).sum()), reward_smaller_grip=int((pk.R_g < pk.R_t).sum()),
    k_higher_grip=int((pk.k_grip > pk.k_tap)[ok].sum()), median_k=dict(tap=float(pk.k_tap[ok].median()), grip=float(pk.k_grip[ok].median()))))
