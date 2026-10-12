"""Mixed models via pymer4 (R lme4/lmerTest called from Python). Helpers return plain pandas/numpy objects."""
import warnings, numpy as np, pandas as pd, polars as pl
from scipy import stats
from pymer4.models import lmer as _lmer, glmer as _glmer
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri
from rpy2.robjects.conversion import localconverter

def _with_control(cls, ctrl):
    class M(cls):
        def _initialize(self):
            kw = {}
            if self.family is not None: kw['family'] = self._r_family_link
            self.r_model = self._r_func(self.formula, self.data, control=ro.r(ctrl), **kw)
    return M

def fit_lmer(formula, data: pd.DataFrame):
    """lme4::lmer with lmerTest (Satterthwaite df), REML, bobyqa."""
    m = _with_control(_lmer, 'lme4::lmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5))')(formula, data=pl.from_pandas(data))
    m.fit(); return m

def fit_glmer(formula, data: pd.DataFrame):
    """lme4::glmer binomial (logit), Laplace, bobyqa; Wald CIs."""
    m = _with_control(_glmer, 'lme4::glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 3e5))')(formula, data=pl.from_pandas(data), family='binomial')
    m.fit(conf_method='wald'); return m

def coefs(m) -> pd.DataFrame:
    """Fixed effects table: term, est, se, lo, hi, p (Satterthwaite for lmer, Wald z for glmer)."""
    x = m.result_fit.to_pandas()
    ren = {'estimate': 'est', 'std_error': 'se', 'conf_low': 'lo', 'conf_high': 'hi', 'p_value': 'p'}
    x = x.rename(columns=ren); return x[['term', 'est', 'se', 'lo', 'hi', 'p'] + [c for c in ['df'] if c in x]].reset_index(drop=True)

def fixef(m) -> pd.Series:
    b = ro.r['fixef'](m.r_model); return pd.Series(np.array(b), index=list(b.names))

def vcov(m) -> pd.DataFrame:
    V = np.array(ro.r('function(m) as.matrix(vcov(m))')(m.r_model)); n = list(fixef(m).index)
    return pd.DataFrame(V, index=n, columns=n)

def person_coefs(m, group='id') -> pd.DataFrame:
    """Per-person conditional coefficients (fixed effect + BLUP), lme4::coef()."""
    f = ro.r(f'function(m) {{ x <- as.data.frame(coef(m)${group}); x$id <- rownames(x); x }}')
    with localconverter(ro.default_converter + pandas2ri.converter): return ro.conversion.get_conversion().rpy2py(f(m.r_model))

def is_singular(m) -> bool: return bool(ro.r('lme4::isSingular')(m.r_model)[0])

def converged(m) -> str: return str(m.convergence_status)

def varcorr(m) -> str: return '\n'.join(ro.r('function(m) capture.output(print(lme4::VarCorr(m), comp = "Std.Dev."))')(m.r_model))

def ratio_k(m, e, r):
    """k = -b_e / b_r with delta-method 95% CI on the log scale."""
    b, V = fixef(m), vcov(m); k = -b[e] / b[r]
    g = np.array([1 / b[e], -1 / b[r]]); se = float(np.sqrt(g @ V.loc[[e, r], [e, r]].values @ g))
    return k, k * np.exp(-1.96 * se), k * np.exp(1.96 * se), se

def ratio_of_k(m, et, rt, eg, rg):
    """k_grip / k_tap with delta-method CI on the log scale and Wald p."""
    b, V = fixef(m), vcov(m); n = [et, rt, eg, rg]
    g = np.array([-1 / b[et], 1 / b[rt], 1 / b[eg], -1 / b[rg]])
    se = float(np.sqrt(g @ V.loc[n, n].values @ g)); l = np.log((b[eg] / b[rg]) / (b[et] / b[rt]))
    return np.exp(l), np.exp(l - 1.96 * se), np.exp(l + 1.96 * se), 2 * stats.norm.sf(abs(l / se))

def task_contrasts_by_level(m, data: pd.DataFrame, level='tf', task='mod'):
    """emmeans grip - tap contrast at each level of `level`, Holm-corrected over levels."""
    f = ro.r(f'''function(m) {{ suppressMessages(library(emmeans)); emm_options(lmer.df = "satterthwaite", lmerTest.limit = 5000)
      ct <- contrast(emmeans(m, ~ {task} | {level}), list(grip_minus_tap = c(-1, 1)), by = "{level}")
      x <- as.data.frame(summary(ct, infer = TRUE, adjust = "none")); x$p_holm <- p.adjust(x$p.value, "holm"); x$level <- as.character(x${level}); x[, c("level","estimate","lower.CL","upper.CL","p.value","p_holm")] }}''')
    with localconverter(ro.default_converter + pandas2ri.converter): return ro.conversion.get_conversion().rpy2py(f(m.r_model))

def ranef(m, group='id') -> pd.DataFrame:
    """Conditional modes (BLUPs) of all random terms of `group`, merged into one table (lme4::ranef)."""
    f = ro.r(f'''function(m) {{ r <- lme4::ranef(m); nm <- grep("^{group}(\\\\.|$)", names(r), value = TRUE)
      x <- do.call(cbind, lapply(nm, function(n) r[[n]])); x$id <- rownames(r[[nm[1]]]); x }}''')
    with localconverter(ro.default_converter + pandas2ri.converter): return ro.conversion.get_conversion().rpy2py(f(m.r_model))
