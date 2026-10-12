"""Figure style shared by all figures: Okabe-Ito colours, Open Sans, Tukey whisker boxes, estimate panels."""
import numpy as np, matplotlib as mpl, matplotlib.pyplot as plt
from scipy import stats
from .config import fig_dir

COLS = dict(tap='#0072B2', grip='#D55E00'); LABS = dict(tap='Tapping', grip='Grip')
TERM_COLS = ['#4D4D4D', '#009E73', '#CC79A7', '#E69F00', '#56B4E9', '#882255', '#999933', '#117733']
OFF = dict(tap=1.6, grip=-1.6)

def use_style():
    mpl.rcParams.update({'font.family': ['Open Sans', 'DejaVu Sans'], 'font.size': 8, 'axes.titlesize': 8.5,
        'axes.labelsize': 8, 'xtick.labelsize': 7.2, 'ytick.labelsize': 7.2, 'legend.fontsize': 7.2,
        'axes.spines.top': False, 'axes.spines.right': False, 'axes.linewidth': .6, 'xtick.major.width': .6,
        'ytick.major.width': .6, 'legend.frameon': False, 'pdf.fonttype': 42, 'savefig.dpi': 300, 'figure.dpi': 110})

def tag(ax, s, x=-0.2, y=1.06): ax.text(x, y, s, transform=ax.transAxes, fontsize=12, fontweight='bold', va='bottom')

def bstats(v):
    v = np.asarray(v, float); v = v[np.isfinite(v)]; q1, med, q3 = np.percentile(v, [25, 50, 75]); i = q3 - q1
    inl = v[(v >= q1 - 1.5 * i) & (v <= q3 + 1.5 * i)]
    return dict(q1=q1, med=med, q3=q3, wlo=inl.min(), whi=inl.max(), mean=v.mean(), out=v[(v < q1 - 1.5 * i) | (v > q3 + 1.5 * i)])

def whiskerbox(ax, x, v, colour, w):
    """Tukey box (alpha fill), thin black whiskers with caps, dark median line, outliers as small dots. Returns stats."""
    s = bstats(v); c = w * .5
    ax.vlines(x, s['wlo'], s['q1'], color='k', lw=.45); ax.vlines(x, s['q3'], s['whi'], color='k', lw=.45)
    ax.hlines([s['wlo'], s['whi']], x - c / 2, x + c / 2, color='k', lw=.45)
    ax.add_patch(mpl.patches.Rectangle((x - w / 2, s['q1']), w, s['q3'] - s['q1'], fc=colour, alpha=.35, ec='none'))
    ax.hlines(s['med'], x - w / 2, x + w / 2, color='#1a1a1a', lw=1.3)
    if len(s['out']): ax.plot(np.full(len(s['out']), x), s['out'], 'o', ms=2, color=colour, mec='none')
    return s

def boxes_by(ax, df, xcol, ycol, w, offsets=OFF, mods=('tap', 'grip'), line=True):
    """Per-participant values in df (one row per person x cell) -> whisker boxes per task and x, mean line + points."""
    for mo in mods:
        sub = df[df.modality == mo]; xs, ms = [], []
        for xv, g in sub.groupby(xcol):
            s = whiskerbox(ax, xv + offsets.get(mo, 0), g[ycol], COLS[mo], w); xs.append(xv + offsets.get(mo, 0)); ms.append(s['mean'])
        if line: ax.plot(xs, ms, '-', color=COLS[mo], lw=1)
        ax.plot(xs, ms, 'o', color=COLS[mo], ms=3.2, label=LABS[mo])

def tci(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]; n = len(x); m = x.mean(); h = stats.t.ppf(.975, n - 1) * x.std(ddof=1) / np.sqrt(n)
    return m, m - h, m + h

def est_panel(ax, e, ylabel='Model estimate [95% CI]', title=None):
    """e: DataFrame term/est/lo/hi/p; colour per term, '*' for p < .05, legend below."""
    lo, hi = e.lo.min(), e.hi.max(); rg = max(hi, 0) - min(lo, 0); top = max(hi, 0) + .08 * rg
    ax.axhline(0, ls='--', lw=.5, color='k')
    for i, r in enumerate(e.itertuples()):
        c = TERM_COLS[i % len(TERM_COLS)]
        ax.vlines(i + 1, r.lo, r.hi, color=c, lw=2); ax.plot(i + 1, r.est, 'o', color=c, ms=4.5, label=r.term)
        if r.p < .05: ax.text(i + 1, top, '*', ha='center', va='center', fontsize=11)
    ax.set_xlim(.5, len(e) + .5); ax.set_ylim(min(lo, 0) - (.18 * len(e)) * rg, top + .07 * rg)
    ax.set_xticks([]); ax.spines['bottom'].set_visible(False); ax.set_ylabel(ylabel)
    if title: ax.set_title(title)
    ax.legend(loc='lower center', fontsize=6, handlelength=.8, borderaxespad=.1, labelspacing=.15, ncol=1)

def save(fig, folder, name):
    d = fig_dir(folder)
    fig.savefig(d / f'{name}.pdf', bbox_inches='tight'); fig.savefig(d / f'{name}.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig); print('saved', d / name)

def top_legend(fig, ax, ncol=2, y=1.02):
    h, l = ax.get_legend_handles_labels(); fig.legend(h, l, loc='lower center', bbox_to_anchor=(.5, y), ncol=ncol, frameon=False)
