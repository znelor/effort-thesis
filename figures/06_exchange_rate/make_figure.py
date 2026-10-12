"""Figure 6: exchange rate k = -b_E / b_R (coins needed to compensate +10 pp) per task from the ONE choice GLMM."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import effortdata as ed
from effortdata import models as M, style as S, choice as C
from effortdata.run import save_results
S.use_style()
d = ed.core_trials(); m = C.fit(d); k = C.exchange_rates(m); c = M.coefs(m).set_index('term')
fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.9), gridspec_kw=dict(width_ratios=[1, 1, 1], wspace=.6))
for a, (lab, terms) in zip(ax[:2], [('Reward slope $\\beta_R$\n(log-odds per +1 coin)', ['R_t', 'R_g']), ('Effort slope $\\beta_E$\n(log-odds per +10 pp)', ['E_t', 'E_g'])]):
    for i, (t, mo) in enumerate(zip(terms, ['tap', 'grip'])):
        a.vlines(i, c.lo[t], c.hi[t], color=S.COLS[mo], lw=2); a.plot(i, c.est[t], 'o', color=S.COLS[mo], ms=5)
        a.text(i + .12, c.est[t], f'{c.est[t]:.2f}', va='center', fontsize=6.5)
    a.axhline(0, ls='--', lw=.5, color='k'); a.set_xticks([0, 1], ['Tapping', 'Grip']); a.set_xlim(-.5, 1.6); a.set_ylabel(lab)
a = ax[2]
for i, mo in enumerate(['tap', 'grip']):
    a.vlines(i, k[f'k_{mo}_lo'], k[f'k_{mo}_hi'], color=S.COLS[mo], lw=2); a.plot(i, k[f'k_{mo}'], 'o', color=S.COLS[mo], ms=5)
    a.text(i + .12, k[f'k_{mo}'], f"{k[f'k_{mo}']:.2f}", va='center', fontsize=6.5)
a.set_xticks([0, 1], ['Tapping', 'Grip']); a.set_xlim(-.5, 1.6); a.set_ylim(0, max(k['k_grip_hi'], k['k_tap_hi']) * 1.25)
a.set_ylabel('Exchange rate $k = -\\beta_E/\\beta_R$\n(coins per +10 pp, 95% CI)')
a.text(.5, .97, f"$k_{{grip}}/k_{{tap}}$ = {k['ratio']:.2f} [{k['ratio_lo']:.2f}, {k['ratio_hi']:.2f}]\np = {k['p_ratio']:.3f}", transform=a.transAxes, ha='center', va='top', fontsize=6.8)
for x, t in zip(ax, 'ABC'): S.tag(x, t, -.45)
S.save(fig, '06_exchange_rate', 'fig06_exchange_rate')
save_results(__file__, dict(k, coefs=c.round(4).reset_index().to_dict('records'), singular=M.is_singular(m), varcorr=M.varcorr(m), formula=C.FORMULA))
