"""Figure 4: choice matrix - P(higher-demand choice) per offer cell (additional effort x additional reward), per task, and grip minus tapping."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import effortdata as ed
from effortdata import style as S
from effortdata.run import save_results
S.use_style()
d = ed.core_trials()
pp = d.groupby(['id', 'modality', 'extra_effort_pct', 'extra_reward']).y.mean().reset_index()   # per person and cell (4 offers each)
cell = pp.groupby(['modality', 'extra_effort_pct', 'extra_reward']).y.mean().unstack('extra_reward')
dw = pp.pivot_table(index=['id', 'extra_effort_pct', 'extra_reward'], columns='modality', values='y'); dw['d'] = dw.grip - dw.tap
dc = dw.groupby(['extra_effort_pct', 'extra_reward']).d.agg(lambda v: S.tci(v)).unstack()
E = sorted(d.extra_effort_pct.unique()); R = sorted(d.extra_reward.unique())
fig, ax = plt.subplots(1, 3, figsize=(7.6, 2.9), gridspec_kw=dict(wspace=.5))
for a, mo in zip(ax[:2], ['tap', 'grip']):
    M = cell.loc[mo].loc[E, R].values.T * 100
    im = a.imshow(M, origin='lower', cmap='viridis', vmin=0, vmax=100, aspect='auto')
    for i in range(len(R)):
        for j in range(len(E)): a.text(j, i, f'{M[i, j]:.0f}', ha='center', va='center', fontsize=7, color='white' if M[i, j] < 60 else 'black')
    a.set_title(S.LABS[mo], color=S.COLS[mo], fontweight='bold'); a.set_xticks(range(len(E)), [f'+{int(e)}' for e in E]); a.set_yticks(range(len(R)), [f'+{int(r)}' for r in R])
    a.set_xlabel('Additional effort (pp)')
    if mo == 'tap': a.set_ylabel('Additional reward (coins)')
cb = fig.colorbar(im, ax=ax[1], fraction=.06, pad=.03); cb.set_label('P(higher-demand), %')
Md = np.array([[dc.loc[e, r][0] for e in E] for r in R]) * 100; lim = np.ceil(np.abs(Md).max() / 5) * 5
im2 = ax[2].imshow(Md, origin='lower', cmap='RdBu_r', vmin=-lim, vmax=lim, aspect='auto')
for i, r in enumerate(R):
    for j, e in enumerate(E):
        m, lo, hi = dc.loc[e, r]; sig = (lo > 0) or (hi < 0)
        ax[2].text(j, i, f'{m * 100:+.0f}' + ('†' if sig else ''), ha='center', va='center', fontsize=7)
ax[2].set_title('Grip minus tapping', fontweight='bold'); ax[2].set_xticks(range(len(E)), [f'+{int(e)}' for e in E]); ax[2].set_yticks(range(len(R)), [f'+{int(r)}' for r in R])
ax[2].set_xlabel('Additional effort (pp)')
cb2 = fig.colorbar(im2, ax=ax[2], fraction=.06, pad=.03); cb2.set_label('Difference (pp)')
for a, t in zip(ax, 'ABC'): S.tag(a, t, -.3, 1.08)
S.save(fig, '04_choice_matrix', 'fig04_choice_matrix')
save_results(__file__, dict(cell_tap=cell.loc['tap'].round(3).to_dict(), cell_grip=cell.loc['grip'].round(3).to_dict(),
    diff=dc.map(lambda v: [round(float(x), 3) for x in v]).to_dict(), n_cells_ci_excl_0=int(sum((v[1] > 0) or (v[2] < 0) for v in dc.values.ravel()))))
