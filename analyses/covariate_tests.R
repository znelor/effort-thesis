################################################################################
# Person-level covariate tests on top of RV2 (primary random-effects structure)
#
# Tests whether person-level characteristics ('knobs') modulate choice behavior:
#   - Hand span (cm)
#   - Log grip MVC (maximum voluntary contraction)
#   - Tapping calibration (tap response vigor)
#   - Hand-use level (questionnaire)
#   - Tapping experience level (questionnaire)
#   - Baseline fatigue (pre-task state)
#   - Task order (grip-first vs tap-first, centered)
#   - Within-person fatigue (trial-level deviations + person means)
#
# For each covariate: adds to RV2
#   - Task-specific intercept shifts (covariate:tap, covariate:grip)
#   - Interactions with relevant effort slopes (e.g., hand_span:E_g, tapcal:E_t)
#
# Tests:
#   - Likelihood-ratio test vs RV2 for each covariate model
#   - AIC comparison (delta AIC)
#   - Holm correction across covariate models
#   - Covariate x effort interaction terms with Holm-adjusted p-values
#   - Exchange-rate ratio k_grip/k_tap with delta-method CI per model
#   - FULL model with all covariates
#
# Expected values (verification):
#   - hand_use: LRT chi2(3) = 7.47, p = .058
#   - fat_within: LRT chi2(8) = 84.3
#   - E_t:fat_w: est = -0.163, p_holm = .047
#   - Ratios: 1.51-1.66 across models; FULL = 1.62
#
# Usage:
#   Rscript analyses/covariate_tests.R
#
# Data:
#   Reads via effortlib (core_trials, load_* functions) using EFFORT_DATA_DIR
#   env var or config.yml (see data/README.md for expected data layout).
#
# Output:
#   - analyses/out/covariate_models.rds (fitted models)
#   - analyses/out/covariate_lrt.csv (LRT results vs RV2)
#   - analyses/out/covariate_terms_single.csv (terms from one-at-a-time models)
#   - analyses/out/covariate_terms_full.csv (terms from FULL model)
#   - analyses/out/covariate_fatigue_within_terms.csv (within-person fatigue)
#   - analyses/out/covariate_core_effects.csv (slopes and k ratios per model)
#   - analyses/out/covariate_descriptives.csv (covariate summary statistics)
#   - Printed summary to console
################################################################################

# Load effortlib from this repository, modelling packages, and set up output paths
source(file.path(dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])), "setup.R"))

suppressPackageStartupMessages({
  library(lme4)
  library(data.table)
})

################################################################################
# Load data
################################################################################

cat("Loading data via effortlib...\n")

# Core choice trials
d <- core_trials()
cat(sprintf("  Loaded %d choice trials from %d participants\n", nrow(d), length(unique(d$id))))

# Add grip indicator (needed for covariate interactions)
d[, grip := G]

# Questionnaire data
q <- load_questionnaire(cohort_only = TRUE)
qw <- dcast(q[section == "baseline"], upload_id ~ item, value.var = "value")

# Calibration data
cal <- load_calibration(wide = TRUE, cohort_only = TRUE)

# Run summary (task order)
rs <- load_run_summary(cohort_only = TRUE)[, .(upload_id, task_order)]

# Anthropometrics (hand span)
anth <- load_anthropometrics()

# Merge person-level data
P <- Reduce(function(a, b) merge(a, b, by = "upload_id", all.x = TRUE), list(rs, cal, qw, anth))
stopifnot(nrow(P) == 31)

# Extract and transform covariates
cat("  Processing covariates...\n")
P[, `:=`(
  hand_use = as.numeric(hand_use_level),
  tap_exp = as.numeric(tapping_experience_level),
  fatigue0 = as.numeric(state_fatigue),
  tired0 = as.numeric(state_tired),
  mvc = log(as.numeric(mvc_force_units)),
  tapcal = as.numeric(tap_response_vigor_taps),
  grip_first = as.numeric(task_order == "grip_first")
)]

# Z-score covariates (standardize for interpretability)
raw <- c("hand_span_cm", "mvc", "tapcal", "hand_use", "tap_exp", "fatigue0", "grip_first")
z <- function(x) (x - mean(x)) / sd(x)

for (v in setdiff(raw, "grip_first")) {
  P[, paste0(v, "_z") := z(get(v))]
}

# Center task order (0/1 -> centered; + = grip-first)
P[, order_c := grip_first - mean(grip_first)]

# Descriptive statistics
desc <- P[, lapply(.SD, function(x) c(mean(x), sd(x), min(x), max(x))), 
          .SDcols = c(raw, "tired0")]
desc[, stat := c("mean", "sd", "min", "max")]
setcolorder(desc, "stat")

cat(sprintf("  Covariate descriptives (N=%d):\n", nrow(P)))
print(desc[, .(stat, hand_span_cm, mvc, tapcal, hand_use, tap_exp, fatigue0, grip_first)], digits = 2)

################################################################################
# Within-person fatigue
################################################################################

cat("\n  Processing within-person fatigue...\n")

# Fatigue ratings: recurring prompts during the task
fa <- load_fatigue(cohort_only = TRUE)[timing == "recurring"]
setorder(fa, upload_id, recorded_at)
fa[, r := seq_len(.N), by = .(upload_id, modality, top_level_phase)]

# Last familiarization rating per modality (assigned to trials 1-10)
fam <- fa[grepl("Familiarization", top_level_phase), .SD[.N], by = .(upload_id, modality)]
fam[, r := 0L]

# Combine familiarization and task-phase ratings
fr <- rbind(
  fam[, .(upload_id, modality, r, fat = fatigue)],
  fa[grepl("Task", top_level_phase), .(upload_id, modality, r, fat = fatigue)]
)

# Assign each choice trial its most recent rating (trials 1-10: r=0, 11-20: r=1, etc.)
d[, r := as.integer((trial_index - 1) %/% 10)]

# Convert upload_id to factor matching d$id for merge
fr[, upload_id := factor(upload_id, levels = levels(d$id))]

d <- merge(d, fr, by.x = c("id", "modality", "r"), by.y = c("upload_id", "modality", "r"), all.x = TRUE)

if (anyNA(d$fat)) {
  stop("Missing fatigue values after merge")
}

# Within person-task deviations (per 10 points)
d[, fat_w := (fat - mean(fat)) / 10, by = .(id, modality)]

# Between-person means (z-scored)
pm <- d[, .(fat_pm = mean(fat)), by = id]
pm[, fat_b_z := z(fat_pm)]
d <- merge(d, pm, by = "id")

# Merge person-level covariates into trial data
cov_cols <- c("upload_id", paste0(setdiff(raw, "grip_first"), "_z"), "order_c")

# Convert P$upload_id to factor matching d$id for merge
P[, upload_id := factor(upload_id, levels = levels(d$id))]

d <- merge(d, P[, cov_cols, with = FALSE], by.x = "id", by.y = "upload_id")

# Ensure id is a factor
d[, id := factor(id)]

cat(sprintf("  Final data: %d trials with covariates\n", nrow(d)))

################################################################################
# Model machinery
################################################################################

# Control settings
ctrl <- glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 3e5))

# RV2 random effects
RE <- "(1 + R + E | id) + (0 + G | id)"

# Base fixed effects
base_fx <- "y ~ 0 + tap + grip + R_t + R_g + E_t + E_g"

# Fit function with warning capture
fit <- function(f) {
  w <- character()
  m <- withCallingHandlers(
    glmer(as.formula(f), d, binomial, control = ctrl),
    warning = function(x) {
      w <<- c(w, conditionMessage(x))
      invokeRestart("muffleWarning")
    }
  )
  attr(m, "warn") <- w
  m
}

# Extract coefficient table
tab <- function(m) {
  b <- fixef(m)
  se <- sqrt(diag(as.matrix(vcov(m))))
  data.table(
    term = names(b),
    est = b,
    se = se,
    z = b / se,
    lo = b - 1.96 * se,
    hi = b + 1.96 * se,
    p = 2 * pnorm(-abs(b / se))
  )
}

# Model diagnostics
diag_ <- function(m) {
  list(
    singular = isSingular(m),
    conv_msgs = unlist(m@optinfo$conv$lme4$messages),
    warnings = attr(m, "warn"),
    logLik = as.numeric(logLik(m)),
    AIC = AIC(m),
    BIC = BIC(m),
    npar = attr(logLik(m), "df")
  )
}

# Exchange rate and ratio with delta-method CI
kfun <- function(m) {
  b <- fixef(m)
  V <- as.matrix(vcov(m))
  nm <- c("E_t", "R_t", "E_g", "R_g")
  
  kt <- -b[["E_t"]] / b[["R_t"]]
  kg <- -b[["E_g"]] / b[["R_g"]]
  
  # Gradients of log(k) for delta method
  gt <- c(1 / b[["E_t"]], -1 / b[["R_t"]], 0, 0)
  gg <- c(0, 0, 1 / b[["E_g"]], -1 / b[["R_g"]])
  gd <- gg - gt
  
  sd_ <- sqrt(drop(gd %*% V[nm, nm] %*% gd))
  dl <- log(kg / kt)
  
  list(
    k_tap = kt,
    k_grip = kg,
    ratio = exp(dl),
    ratio_ci = exp(dl + c(-1.96, 1.96) * sd_),
    p_ratio = 2 * pnorm(-abs(dl / sd_))
  )
}

################################################################################
# Covariate model specifications
################################################################################

# Per covariate: task-specific intercept shifts + interaction with relevant effort slope(s)
# Grip-related covariates interact with E_g; tap-related with E_t; fatigue with both
terms_for <- function(v) {
  switch(v,
    hand_span_cm_z = "hand_span_cm_z:tap + hand_span_cm_z:grip + hand_span_cm_z:E_g",
    mvc_z          = "mvc_z:tap + mvc_z:grip + mvc_z:E_g",
    hand_use_z     = "hand_use_z:tap + hand_use_z:grip + hand_use_z:E_g",
    tapcal_z       = "tapcal_z:tap + tapcal_z:grip + tapcal_z:E_t",
    tap_exp_z      = "tap_exp_z:tap + tap_exp_z:grip + tap_exp_z:E_t",
    fatigue0_z     = "fatigue0_z:tap + fatigue0_z:grip + fatigue0_z:E_t + fatigue0_z:E_g",
    order_c        = "order_c:tap + order_c:grip",
    fat_within     = "fat_w:tap + fat_w:grip + fat_w:E_t + fat_w:E_g + fat_b_z:tap + fat_b_z:grip + fat_b_z:E_t + fat_b_z:E_g"
  )
}

# Covariates to test
covs <- c("hand_span_cm_z", "mvc_z", "tapcal_z", "hand_use_z", "tap_exp_z", 
          "fatigue0_z", "order_c", "fat_within")

# Model formulas
formulas <- c(
  list(RV2 = paste(base_fx, "+", RE)),
  setNames(
    lapply(covs, function(v) paste(base_fx, "+", terms_for(v), "+", RE)),
    paste0("plus_", covs)
  ),
  list(FULL = paste(base_fx, "+", paste(sapply(covs, terms_for), collapse = " + "), "+", RE))
)

################################################################################
# Fit models
################################################################################

cat("\n")
cat(paste(rep("=", 80), collapse = ""), "\n")
cat("Fitting covariate models on top of RV2\n")
cat(paste(rep("=", 80), collapse = ""), "\n\n")

cat(sprintf("Baseline (RV2): %s\n\n", formulas$RV2))

# Fit all models (can be parallelized for speed, but sequential for clarity)
M <- list()
for (n in names(formulas)) {
  cat(sprintf("Fitting %s...", n))
  t0 <- Sys.time()
  M[[n]] <- fit(formulas[[n]])
  elapsed <- round(as.numeric(difftime(Sys.time(), t0, units = "secs")), 1)
  cat(sprintf(" %.1f s\n", elapsed))
}

cat("\nAll models fitted.\n")

################################################################################
# Extract results
################################################################################

cat("\n")
cat(paste(rep("=", 80), collapse = ""), "\n")
cat("Extracting results\n")
cat(paste(rep("=", 80), collapse = ""), "\n\n")

# Store results per model
res <- list()
for (n in names(M)) {
  m <- M[[n]]
  res[[n]] <- list(
    formula = formulas[[n]],
    coefs = tab(m),
    diag = diag_(m),
    k = kfun(m)
  )
}

################################################################################
# Likelihood-ratio tests vs RV2
################################################################################

cat("Likelihood-ratio tests (vs RV2):\n\n")

lrt_list <- list()
for (n in names(M)[-1]) {  # Skip RV2 itself
  x <- anova(M$RV2, M[[n]])
  lrt_list[[n]] <- data.table(
    model = n,
    chisq = x$Chisq[2],
    df = x$Df[2],
    p = x$`Pr(>Chisq)`[2],
    dAIC = AIC(M[[n]]) - AIC(M$RV2),
    logLik_RV2 = as.numeric(logLik(M$RV2)),
    logLik_model = as.numeric(logLik(M[[n]])),
    singular = isSingular(M[[n]]),
    conv_warn = length(res[[n]]$diag$conv_msgs) > 0
  )
}

lrt_dt <- rbindlist(lrt_list)

# Holm correction for covariate models (exclude FULL from correction)
lrt_dt[!model %in% c("FULL"), p_holm := p.adjust(p, "holm")]

print(lrt_dt[, .(model, chisq, df, p, p_holm, dAIC, singular)], digits = 3)

################################################################################
# Covariate interaction terms
################################################################################

cat("\n")
cat(paste(rep("=", 80), collapse = ""), "\n")
cat("Covariate x effort interaction terms\n")
cat(paste(rep("=", 80), collapse = ""), "\n\n")

# Extract covariate terms from one-at-a-time models (excluding fat_within)
cov_models_single <- paste0("plus_", setdiff(covs, "fat_within"))
C1 <- rbindlist(lapply(cov_models_single, function(n) {
  res[[n]]$coefs[grepl(":", term)][, model := n]
}))

# Extract within-person fatigue terms
CW <- res$plus_fat_within$coefs[grepl(":", term)]
CW[, model := "plus_fat_within"]

# Combine all covariate x effort terms for Holm correction
# (This is the reported family: 11 terms from single models + within-fatigue)
C_all <- rbind(C1, CW, fill = TRUE)
C_all[, p_holm := p.adjust(p, "holm")]

# Split back for display
C1 <- C_all[model %in% cov_models_single]
CW <- C_all[model == "plus_fat_within"]

cat("One-at-a-time covariate models:\n\n")
print(C1[, .(model, term, est, se, z, p, p_holm)], digits = 3)

################################################################################
# Within-person fatigue terms
################################################################################

cat("\n")
cat(paste(rep("=", 80), collapse = ""), "\n")
cat("Within-person fatigue model terms\n")
cat(paste(rep("=", 80), collapse = ""), "\n\n")

cat("(Holm correction applied jointly with single-covariate terms above)\n\n")
print(CW[, .(term, est, se, z, p, p_holm)], digits = 3)

################################################################################
# FULL model terms
################################################################################

cat("\n")
cat(paste(rep("=", 80), collapse = ""), "\n")
cat("FULL model covariate terms\n")
cat(paste(rep("=", 80), collapse = ""), "\n\n")

CF <- res$FULL$coefs[grepl(":", term)]
CF[, model := "FULL"]
CF[, p_holm := p.adjust(p, "holm")]

print(CF[, .(term, est, se, z, p, p_holm)], digits = 3)

################################################################################
# Core effects and exchange rates per model
################################################################################

cat("\n")
cat(paste(rep("=", 80), collapse = ""), "\n")
cat("Core effects and exchange-rate ratios per model\n")
cat(paste(rep("=", 80), collapse = ""), "\n\n")

core <- rbindlist(lapply(names(M), function(n) {
  b <- res[[n]]$coefs
  k <- res[[n]]$k
  data.table(
    model = n,
    E_t = b[term == "E_t", est],
    E_g = b[term == "E_g", est],
    R_t = b[term == "R_t", est],
    R_g = b[term == "R_g", est],
    k_tap = k$k_tap,
    k_grip = k$k_grip,
    ratio = k$ratio,
    ratio_lo = k$ratio_ci[1],
    ratio_hi = k$ratio_ci[2],
    p_ratio = k$p_ratio
  )
}))

print(core[, .(model, k_tap, k_grip, ratio, ratio_lo, ratio_hi, p_ratio)], digits = 3)

################################################################################
# Verification against expected values
################################################################################

cat("\n")
cat(paste(rep("=", 80), collapse = ""), "\n")
cat("Verification against expected values\n")
cat(paste(rep("=", 80), collapse = ""), "\n\n")

# hand_use: LRT chi2(3) = 7.47, p = .058
hu <- lrt_dt[model == "plus_hand_use_z"]
cat(sprintf("hand_use: LRT chi2(%d) = %.2f, p = %.3f (expected: chi2(3) = 7.47, p = .058)\n",
            hu$df, hu$chisq, hu$p))

# fat_within: LRT chi2(8) = 84.3
fw <- lrt_dt[model == "plus_fat_within"]
cat(sprintf("fat_within: LRT chi2(%d) = %.1f (expected: chi2(8) = 84.3)\n",
            fw$df, fw$chisq))

# E_t:fat_w: est = -0.163, p_holm = .047
ew <- CW[grepl("E_t:fat_w", term)]
cat(sprintf("E_t:fat_w: est = %.3f, p_holm = %.3f (expected: est = -0.163, p_holm = .047)\n",
            ew$est, ew$p_holm))

# Ratios: 1.51-1.66 across models; FULL = 1.62
cat("\nExchange-rate ratios (expected range: 1.51-1.66; FULL = 1.62):\n")
print(core[, .(model, ratio)], digits = 3)

cat(sprintf("\nFULL ratio: %.2f (expected: 1.62)\n", core[model == "FULL", ratio]))

################################################################################
# Save outputs
################################################################################

cat("\n")
cat(paste(rep("=", 80), collapse = ""), "\n")
cat("Saving outputs\n")
cat(paste(rep("=", 80), collapse = ""), "\n\n")

# Create output directory if needed
dir.create(out, showWarnings = FALSE, recursive = TRUE)

# Save fitted models
models_file <- file.path(out, "covariate_models.rds")
saveRDS(M, models_file)
cat(sprintf("Saved fitted models to: %s\n", models_file))

# Save LRT results
lrt_file <- file.path(out, "covariate_lrt.csv")
fwrite(lrt_dt, lrt_file)
cat(sprintf("Saved LRT results to: %s\n", lrt_file))

# Save covariate terms (single models)
c1_file <- file.path(out, "covariate_terms_single.csv")
fwrite(C1, c1_file)
cat(sprintf("Saved single-model covariate terms to: %s\n", c1_file))

# Save within-person fatigue terms
cw_file <- file.path(out, "covariate_fatigue_within_terms.csv")
fwrite(CW, cw_file)
cat(sprintf("Saved within-person fatigue terms to: %s\n", cw_file))

# Save FULL model terms
cf_file <- file.path(out, "covariate_terms_full.csv")
fwrite(CF, cf_file)
cat(sprintf("Saved FULL model covariate terms to: %s\n", cf_file))

# Save core effects
core_file <- file.path(out, "covariate_core_effects.csv")
fwrite(core, core_file)
cat(sprintf("Saved core effects and k ratios to: %s\n", core_file))

# Save descriptive statistics
desc_file <- file.path(out, "covariate_descriptives.csv")
fwrite(desc, desc_file)
cat(sprintf("Saved covariate descriptives to: %s\n", desc_file))

cat("\nDone.\n")

