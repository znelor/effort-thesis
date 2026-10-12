"""Figure 7a: reported fatigue across the session by task order (LMM).
Figure 7b (new): time-on-task in familiarisation - fatigue reports, ratings and realised intensity across repetitions (LMMs).
Figure 7c (new): timing in the choice phase - higher-demand choices across trial position and block (GLMM)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import effortdata as ed
from effortdata import models as M, style as S, choice as C
from effortdata.run import save_results
S.use_style(); res = {}
def est(m, terms):
    c = M.coefs(m).set_index('term'); e = c.loc[list(terms)].reset_index(); e['term'] = list(terms.values()); return e, c
# ---------------- 7a fatigue by order
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
S.save(fig, '07_fatigue_timing', 'fig07a_fatigue_by_order')
# ---------------- 7b familiarisation: time-on-task
fa = ed.fam_trials(); fs = fa[fa.success].copy()
fs['dev'] = fs.realised - fs.target                    # realised minus displayed target (pp)
m_r = M.fit_lmer('sub_disp ~ G * rep_c + G * tgt10 + period + (1 + G | id)', fa.dropna(subset=['sub_disp']))
m_i = M.fit_lmer('realised ~ G * rep_c + G * tgt10 + period + (1 + G | id)', fs.dropna(subset=['realised']))
m_t = M.fit_lmer('log_time ~ G * rep_c + G * tgt10 + period + (1 + G | id)', fs.assign(log_time=np.log(fs.time)).dropna(subset=['time']))
ff = f[f.phase == 'familiarisation'].copy(); ff['pb_c'] = ff.prompt_block - 2
m_f = M.fit_lmer('fatigue ~ G * pb_c + period_n + (1 + G | id)', ff.assign(period_n=(ff.prompt_all > 11).astype(float)))
rows = []
for nm, mm, t1, t2, unit in [('Rating − target', m_r, 'rep_c', 'G:rep_c', 'points/rep'), ('Realised intensity', m_i, 'rep_c', 'G:rep_c', 'pp/rep'),
                             ('Fatigue', m_f, 'pb_c', 'G:pb_c', 'points/report')]:
    c = M.coefs(mm).set_index('term')
    rows += [dict(term=f'{nm}: tapping', **c.loc[t1, ['est', 'lo', 'hi', 'p']]), dict(term=f'{nm}: grip − tapping', **c.loc[t2, ['est', 'lo', 'hi', 'p']])]
    res[f'fam_{nm}'] = dict(coefs=c.round(4).reset_index().to_dict('records'), singular=M.is_singular(mm))
ct = M.coefs(m_t).set_index('term'); res['fam_log_time'] = dict(coefs=ct.round(4).reset_index().to_dict('records'), singular=M.is_singular(m_t))
eb = pd.DataFrame(rows)
fig, ax = plt.subplots(1, 4, figsize=(8.0, 3.2), gridspec_kw=dict(width_ratios=[1, 1, 1, 1.45], wspace=.85))
a = ax[0]; fp = ff.assign(x=ff.prompt_block)
S.boxes_by(a, fp, 'x', 'fatigue', .28, offsets=dict(tap=-.17, grip=.17)); a.set_xticks([1, 2, 3]); a.set_xlim(.5, 3.5); a.set_ylim(0, 100)
a.set_xlabel('Fatigue report within\nfamiliarisation block'); a.set_ylabel('Reported fatigue (1–100)')
pr = fa.groupby(['id', 'modality', 'rep'], as_index=False).sub_disp.mean()
a = ax[1]; a.axhline(0, ls='--', lw=.5, color='k'); S.boxes_by(a, pr, 'rep', 'sub_disp', .28, offsets=dict(tap=-.17, grip=.17))
a.set_xticks(range(1, 6)); a.set_xlabel('Repetition (7 targets each)'); a.set_ylabel('Rating minus displayed\ntarget (points)')
pi = fs.groupby(['id', 'modality', 'rep'], as_index=False).dev.mean()
a = ax[2]; a.axhline(0, ls='--', lw=.5, color='k'); S.boxes_by(a, pi, 'rep', 'dev', .28, offsets=dict(tap=-.17, grip=.17))
a.set_xticks(range(1, 6)); a.set_xlabel('Repetition (7 targets each)'); a.set_ylabel('Realised intensity minus\ntarget (pp of capacity)')
S.est_panel(ax[3], eb, ylabel='Change per repetition / report\n[95% CI]', title='Linear mixed models')
S.top_legend(fig, ax[1], y=.98)
for x, t in zip(ax, 'ABCD'): S.tag(x, t, -.42)
S.save(fig, '07_fatigue_timing', 'fig07b_familiarisation_time_on_task')
# ---------------- 7c choice phase timing
d = ed.core_trials()
d['P_t'] = d.prog * d.tap; d['P_g'] = d.prog * d.grip; d['EP_t'] = d.E_t * d.prog; d['EP_g'] = d.E_g * d.prog
fo = C.FORMULA.replace('E_g +', 'E_g + P_t + P_g + EP_t + EP_g + period +')
mc = M.fit_glmer(fo, d); cc = M.coefs(mc).set_index('term')
terms = {'P_t': 'Trial position, tapping', 'P_g': 'Trial position, grip', 'EP_t': 'Effort × position, tapping', 'EP_g': 'Effort × position, grip', 'period': 'Second block'}
ec = cc.loc[list(terms)].reset_index(); ec['term'] = list(terms.values())
res['choice_timing'] = dict(coefs=cc.round(4).reset_index().to_dict('records'), singular=M.is_singular(mc), formula=fo,
    note='prog = (trial_index - 38.5)/76, i.e. one unit = start to end of a choice block')
d['bin'] = pd.cut(d.trial_index, [0, 19, 38, 57, 76], labels=[1, 2, 3, 4]).astype(int)
pb = d.groupby(['id', 'modality', 'bin'], as_index=False).y.mean()
d['blk'] = np.where(d.period == 1, 'second', 'first')
pk = d.groupby(['id', 'modality', 'blk'], as_index=False).y.mean(); pk['x'] = (pk.blk == 'second').astype(int) + 1
fig, ax = plt.subplots(1, 3, figsize=(7.2, 3.0), gridspec_kw=dict(width_ratios=[1.4, .9, 1.1], wspace=.5))
S.boxes_by(ax[0], pb, 'bin', 'y', .26, offsets=dict(tap=-.16, grip=.16)); ax[0].set_xticks([1, 2, 3, 4], ['1–19', '20–38', '39–57', '58–76'])
ax[0].set_xlabel('Trial position within choice block'); ax[0].set_ylabel('Higher-demand choices\n(per participant)')
S.boxes_by(ax[1], pk, 'x', 'y', .26, offsets=dict(tap=-.16, grip=.16)); ax[1].set_xticks([1, 2], ['First\nblock', 'Second\nblock']); ax[1].set_xlim(.5, 2.5)
for a in ax[:2]: a.set_ylim(-.02, 1.02); a.set_yticks([0, .25, .5, .75, 1], ['0%', '25%', '50%', '75%', '100%'])
S.est_panel(ax[2], ec, ylabel='Log-odds [95% CI]', title='Binomial GLMM')
S.top_legend(fig, ax[0], y=.98)
for x, t in zip(ax, 'ABC'): S.tag(x, t, -.4)
S.save(fig, '07_fatigue_timing', 'fig07c_choice_timing')
res['choice_by_bin'] = pb.groupby(['modality', 'bin']).y.mean().round(3).unstack().to_dict()
res['choice_by_block'] = pk.groupby(['modality', 'blk']).y.mean().round(3).unstack().to_dict()
save_results(__file__, res)
