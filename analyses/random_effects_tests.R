################################################################################
# Random-effects structure comparison for the main choice model
#
# Fits three nested random-effects specifications of the binomial choice GLMM:
#   RV1: baseline correlated random intercept + reward/effort slopes
#   RV2: RV1 + uncorrelated random grip intercept (primary model)
#   RV6: maximal task-specific random slopes (all fixed effects)
#
# Tests:
#   - Likelihood-ratio test: RV1 vs RV2 (tests random grip intercept G)
#   - Likelihood-ratio test: RV2 vs RV6 (tests task-specific random slopes)
#   - AIC/BIC comparison
#   - Singularity check (isSingular)
#   - Exchange-rate ratio k_grip/k_tap with delta-method CI (per model)
#
# Expected values (verification):
#   - RV2 ratio: 1.571 [1.117, 2.210]
#   - logLik: RV1 = -1472.53, RV2 = -1414.35, RV6 = -1408.51 (singular)
#
# Usage:
#   Rscript analyses/random_effects_tests.R
#
# Data:
#   Reads via effortlib::core_trials() using EFFORT_DATA_DIR env var or
#   config.yml (see data/README.md for the expected data layout).
#
# Output:
#   - analyses/out/random_effects_models.rds (fitted models)
#   - analyses/out/random_effects_comparison.csv (summary table)
#   - Printed summary to console
################################################################################

# Load effortlib from this repository, modelling packages, and set up output paths
source(file.path(dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])), "setup.R"))

suppressPackageStartupMessages({
  library(lme4)
  library(data.table)
})

# Load core choice trials with model variables
cat("Loading data via effortlib::core_trials()...\n")
d <- core_trials()

# Verify data structure
cat(sprintf("  Loaded %d trials from %d participants\n", nrow(d), length(unique(d$id))))
if (nrow(d) != 60 * 2 * length(unique(d$id))) {
  warning("Unexpected number of trials (expected 120 per participant)")
}

# Prepare task indicator for RV2 random effects
d[, grip := G]

# Control settings for optimizer (matches the main analysis)
ctrl <- glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 3e5))

# Fixed effects (same for all models)
# y ~ 0 + tap + grip + R_t + R_g + E_t + E_g
#   where: y = hard option chosen (0/1)
#          tap, grip = task-specific intercepts
#          R_t, R_g = extra reward (coins) × task indicator
#          E_t, E_g = extra effort (per 10 pp) × task indicator
fx <- "y ~ 0 + tap + grip + R_t + R_g + E_t + E_g"

# Model specifications
specs <- list(
  RV1 = list(
    name = "RV1: (1 + R + E | id)",
    formula_suffix = "+ (1 + R + E | id)",
    description = "Baseline: correlated random intercept, reward, and effort slopes"
  ),
  RV2 = list(
    name = "RV2: (1 + R + E | id) + (0 + G | id)",
    formula_suffix = "+ (1 + R + E | id) + (0 + G | id)",
    description = "Primary: RV1 + uncorrelated random grip intercept"
  ),
  RV6 = list(
    name = "RV6: (0 + tap + grip + R_t + R_g + E_t + E_g | id)",
    formula_suffix = "+ (0 + tap + grip + R_t + R_g + E_t + E_g | id)",
    description = "Maximal: task-specific random slopes for all fixed effects"
  )
)

################################################################################
# Exchange-rate calculation with delta-method CI
################################################################################
# Exchange rate k = -beta_E / beta_R (coins per 10 pp effort increase)
# Ratio: k_grip / k_tap
# Delta-method CI on log scale (transforms to multiplicative CI)

compute_exchange_rates <- function(m, level = 0.95) {
  z <- qnorm(1 - (1 - level) / 2)
  b <- fixef(m)
  V <- as.matrix(vcov(m))
  
  # Exchange rates per task
  k_tap  <- -b["E_t"] / b["R_t"]
  k_grip <- -b["E_g"] / b["R_g"]
  
  # Gradients of log(k) with respect to (E_t, R_t, E_g, R_g)
  g_tap  <- c(1 / b["E_t"], -1 / b["R_t"], 0, 0)
  g_grip <- c(0, 0, 1 / b["E_g"], -1 / b["R_g"])
  
  # Variance-covariance submatrix
  nm <- c("E_t", "R_t", "E_g", "R_g")
  Vs <- V[nm, nm]
  
  # Standard errors on log scale
  se_tap  <- sqrt(drop(t(g_tap) %*% Vs %*% g_tap))
  se_grip <- sqrt(drop(t(g_grip) %*% Vs %*% g_grip))
  
  # Log ratio and its SE
  g_diff <- g_grip - g_tap
  se_diff <- sqrt(drop(t(g_diff) %*% Vs %*% g_diff))
  log_ratio <- log(k_grip) - log(k_tap)
  
  # Slope differences (for supplementary info)
  bEG <- b["E_g"] - b["E_t"]
  seEG <- sqrt(V["E_g", "E_g"] + V["E_t", "E_t"] - 2 * V["E_g", "E_t"])
  bRG <- b["R_g"] - b["R_t"]
  seRG <- sqrt(V["R_g", "R_g"] + V["R_t", "R_t"] - 2 * V["R_g", "R_t"])
  
  data.table(
    k_tap = k_tap,
    k_tap_lo = exp(log(k_tap) - z * se_tap),
    k_tap_hi = exp(log(k_tap) + z * se_tap),
    k_grip = k_grip,
    k_grip_lo = exp(log(k_grip) - z * se_grip),
    k_grip_hi = exp(log(k_grip) + z * se_grip),
    ratio_grip_tap = exp(log_ratio),
    ratio_lo = exp(log_ratio - z * se_diff),
    ratio_hi = exp(log_ratio + z * se_diff),
    p_wald_logratio = 2 * pnorm(-abs(log_ratio / se_diff)),
    bE_tap = b["E_t"],
    bE_grip = b["E_g"],
    bR_tap = b["R_t"],
    bR_grip = b["R_g"],
    EG = bEG,
    p_EG = 2 * pnorm(-abs(bEG / seEG)),
    RG = bRG,
    p_RG = 2 * pnorm(-abs(bRG / seRG))
  )
}

################################################################################
# Fit models
################################################################################

fits <- list()
results <- list()

cat("\n")
cat(paste(rep("=", 80), collapse = ""), "\n")
cat("Fitting models...\n")
cat(paste(rep("=", 80), collapse = ""), "\n\n")

for (model_name in names(specs)) {
  spec <- specs[[model_name]]
  
  cat(sprintf("Fitting %s\n", spec$name))
  cat(sprintf("  %s\n", spec$description))
  
  t0 <- Sys.time()
  
  # Construct and fit the model
  formula_str <- paste(fx, spec$formula_suffix)
  m <- glmer(as.formula(formula_str), data = d, family = binomial, control = ctrl)
  
  # Store fitted model
  fits[[model_name]] <- m
  
  # Extract results
  r <- compute_exchange_rates(m)
  r[, model := model_name]
  
  # Add fit statistics
  r[, logLik := as.numeric(logLik(m))]
  r[, AIC := AIC(m)]
  r[, BIC := BIC(m)]
  r[, df := attr(logLik(m), "df")]
  r[, singular := isSingular(m)]
  
  # Convergence info
  conv_messages <- unlist(m@optinfo$conv$lme4$messages)
  r[, convergence := if (is.null(conv_messages)) "OK" else paste(conv_messages, collapse = "; ")]
  
  results[[model_name]] <- r
  
  elapsed <- round(as.numeric(difftime(Sys.time(), t0, units = "secs")), 1)
  cat(sprintf("  Completed in %.1f seconds\n", elapsed))
  cat(sprintf("  logLik = %.2f, AIC = %.1f, BIC = %.1f, singular = %s\n\n",
              r$logLik, r$AIC, r$BIC, r$singular))
}

# Combine results
results_dt <- rbindlist(results)
setcolorder(results_dt, "model")

################################################################################
# Likelihood-ratio tests
################################################################################

cat(paste(rep("=", 80), collapse = ""), "\n")
cat("Likelihood-ratio tests\n")
cat(paste(rep("=", 80), collapse = ""), "\n\n")

# Test 1: RV1 vs RV2 (tests random grip intercept)
lrt_rv1_rv2 <- anova(fits$RV1, fits$RV2)
cat("Test 1: RV1 vs RV2 (tests random grip intercept G)\n")
cat(sprintf("  Chi-squared = %.3f, df = %d, p = %.4f\n",
            lrt_rv1_rv2$Chisq[2], lrt_rv1_rv2$Df[2], lrt_rv1_rv2$`Pr(>Chisq)`[2]))
cat(sprintf("  logLik(RV1) = %.2f, logLik(RV2) = %.2f\n",
            results_dt[model == "RV1", logLik], results_dt[model == "RV2", logLik]))
cat(sprintf("  Delta AIC = %.1f (negative favors RV2)\n\n",
            results_dt[model == "RV2", AIC] - results_dt[model == "RV1", AIC]))

# Test 2: RV2 vs RV6 (tests task-specific random slopes)
lrt_rv2_rv6 <- anova(fits$RV2, fits$RV6)
cat("Test 2: RV2 vs RV6 (tests task-specific random slopes)\n")
cat(sprintf("  Chi-squared = %.3f, df = %d, p = %.4f\n",
            lrt_rv2_rv6$Chisq[2], lrt_rv2_rv6$Df[2], lrt_rv2_rv6$`Pr(>Chisq)`[2]))
cat(sprintf("  logLik(RV2) = %.2f, logLik(RV6) = %.2f\n",
            results_dt[model == "RV2", logLik], results_dt[model == "RV6", logLik]))
cat(sprintf("  Delta AIC = %.1f (negative favors RV6)\n",
            results_dt[model == "RV6", AIC] - results_dt[model == "RV2", AIC]))
cat(sprintf("  Note: RV6 is %s\n\n", ifelse(results_dt[model == "RV6", singular], "SINGULAR", "not singular")))

# Add LRT results to the table
results_dt[model == "RV2", `:=`(
  LRT_vs_RV1_chisq = lrt_rv1_rv2$Chisq[2],
  LRT_vs_RV1_df = lrt_rv1_rv2$Df[2],
  LRT_vs_RV1_p = lrt_rv1_rv2$`Pr(>Chisq)`[2]
)]
results_dt[model == "RV6", `:=`(
  LRT_vs_RV2_chisq = lrt_rv2_rv6$Chisq[2],
  LRT_vs_RV2_df = lrt_rv2_rv6$Df[2],
  LRT_vs_RV2_p = lrt_rv2_rv6$`Pr(>Chisq)`[2]
)]

################################################################################
# Summary table
################################################################################

cat(paste(rep("=", 80), collapse = ""), "\n")
cat("Summary: Exchange rates and model fit\n")
cat(paste(rep("=", 80), collapse = ""), "\n\n")

# Key columns for display
summary_cols <- c("model", "k_tap", "k_tap_lo", "k_tap_hi", 
                  "k_grip", "k_grip_lo", "k_grip_hi",
                  "ratio_grip_tap", "ratio_lo", "ratio_hi", "p_wald_logratio")
cat("Exchange rates (coins per 10 pp effort):\n\n")
print(results_dt[, ..summary_cols], digits = 3)

cat("\n\nModel fit statistics:\n\n")
fit_cols <- c("model", "logLik", "AIC", "BIC", "df", "singular", "convergence")
print(results_dt[, ..fit_cols], digits = 2)

cat("\n\nSlope estimates:\n\n")
slope_cols <- c("model", "bE_tap", "bE_grip", "EG", "p_EG", "bR_tap", "bR_grip", "RG", "p_RG")
print(results_dt[, ..slope_cols], digits = 3)

################################################################################
# Verification against expected values
################################################################################

cat("\n")
cat(paste(rep("=", 80), collapse = ""), "\n")
cat("Verification against expected values\n")
cat(paste(rep("=", 80), collapse = ""), "\n\n")

expected <- list(
  RV2_ratio = 1.571,
  RV2_ratio_lo = 1.117,
  RV2_ratio_hi = 2.210,
  RV1_logLik = -1472.53,
  RV2_logLik = -1414.35,
  RV6_logLik = -1408.51
)

rv2 <- results_dt[model == "RV2"]
cat(sprintf("RV2 ratio: %.3f [%.3f, %.3f] (expected: %.3f [%.3f, %.3f])\n",
            rv2$ratio_grip_tap, rv2$ratio_lo, rv2$ratio_hi,
            expected$RV2_ratio, expected$RV2_ratio_lo, expected$RV2_ratio_hi))

cat("\nLog-likelihoods:\n")
for (m in c("RV1", "RV2", "RV6")) {
  obs <- results_dt[model == m, logLik]
  exp <- expected[[paste0(m, "_logLik")]]
  diff <- obs - exp
  cat(sprintf("  %s: %.2f (expected: %.2f, diff: %+.2f)\n", m, obs, exp, diff))
}

cat("\nSingularity:\n")
for (m in c("RV1", "RV2", "RV6")) {
  sing <- results_dt[model == m, singular]
  cat(sprintf("  %s: %s", m, ifelse(sing, "SINGULAR", "not singular")))
  if (m == "RV6" && sing) cat(" (expected)")
  cat("\n")
}

################################################################################
# Save outputs
################################################################################

cat("\n")
cat(paste(rep("=", 80), collapse = ""), "\n")
cat("Saving outputs\n")
cat(paste(rep("=", 80), collapse = ""), "\n\n")

# Save fitted models
models_file <- file.path(out, "random_effects_models.rds")
saveRDS(fits, models_file)
cat(sprintf("Saved fitted models to: %s\n", models_file))

# Save summary table
table_file <- file.path(out, "random_effects_comparison.csv")
fwrite(results_dt, table_file)
cat(sprintf("Saved summary table to: %s\n", table_file))

cat("\nDone.\n")

