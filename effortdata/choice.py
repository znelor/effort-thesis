"""The ONE choice model used for all choice figures (H1-H3).
Binomial GLMM (logit), task-specific intercepts and task-specific reward and effort slopes, no covariates;
random effects per person: intercept, grip offset, and task-specific reward and effort slopes (independent).
(= model RV5 of the thesis analysis repository.)"""
import numpy as np, pandas as pd
from scipy.special import expit
from . import models as M

FORMULA = ('y ~ 0 + tap + grip + R_t + R_g + E_t + E_g + (1 | id) + (0 + G | id) + (0 + R_t | id) + (0 + R_g | id)'
           ' + (0 + E_t | id) + (0 + E_g | id)')
# identical model in interaction (difference) parameterisation: grip effects as differences from tapping
FORMULA_DIFF = ('y ~ 1 + R + E + G + R:G + E:G + (1 | id) + (0 + G | id) + (0 + R_t | id) + (0 + R_g | id)'
                ' + (0 + E_t | id) + (0 + E_g | id)')
FX = ['tap', 'grip', 'R_t', 'R_g', 'E_t', 'E_g']

def fit(d, diff=False): return M.fit_glmer(FORMULA_DIFF if diff else FORMULA, d)

def design(grid):
    g = grid.copy(); g['tap'] = (g.modality == 'tap').astype(float); g['grip'] = 1 - g.tap
    for v in 'RE': g[v + '_t'] = g[v] * g.tap; g[v + '_g'] = g[v] * g.grip
    return g[FX].values

def person_dev(m):
    """Per-person random deviations on the FX scale (intercept terms: tap = (1|id); grip = (1|id) + (0+G|id))."""
    re = M.ranef(m).set_index('id')
    dev = pd.DataFrame({'tap': re['(Intercept)'], 'grip': re['(Intercept)'] + re['G']}, index=re.index)
    for c in FX[2:]: dev[c] = re[c]
    return dev[FX]

def person_slopes(m):
    """Per-person conditional slopes (fixed + random) on the FX scale."""
    return person_dev(m) + M.fixef(m)[FX]

def predict_pop(m, grid, ndraw=1000, seed=20261012):
    """Population-averaged P(hard) over the 31 persons (conditional modes), band = 95% quantiles over draws of the fixed effects."""
    b, V, dev = M.fixef(m)[FX].values, M.vcov(m).loc[FX, FX].values, person_dev(m).values
    X = design(grid); rng = np.random.default_rng(seed); B = rng.multivariate_normal(b, V, ndraw)
    eta_i = X @ dev.T                      # cells x persons
    fit = expit(X @ b[:, None] + eta_i).mean(1)
    sims = np.stack([expit((X @ bb)[:, None] + eta_i).mean(1) for bb in B], 1)
    out = grid.copy(); out['fit'] = fit; out['lo'] = np.quantile(sims, .025, 1); out['hi'] = np.quantile(sims, .975, 1); return out

def predict_person(m, grid):
    b, dev = M.fixef(m)[FX].values, person_dev(m); X = design(grid); rows = []
    for pid, dv in dev.iterrows():
        g = grid.copy(); g['id'] = pid; g['fit'] = expit(X @ (b + dv.values)); rows.append(g)
    return pd.concat(rows)

def exchange_rates(m):
    kt = M.ratio_k(m, 'E_t', 'R_t'); kg = M.ratio_k(m, 'E_g', 'R_g'); r = M.ratio_of_k(m, 'E_t', 'R_t', 'E_g', 'R_g')
    return dict(k_tap=kt[0], k_tap_lo=kt[1], k_tap_hi=kt[2], k_grip=kg[0], k_grip_lo=kg[1], k_grip_hi=kg[2],
                ratio=r[0], ratio_lo=r[1], ratio_hi=r[2], p_ratio=r[3])
