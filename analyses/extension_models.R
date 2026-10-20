################################################################################
# Extension models beyond RV2: does only the effort DIFFERENCE matter, and is
# effort cost linear?
#
# Baseline (RV2, linear difference model):
#   y ~ 0 + tap + grip + R_t + R_g + E_t + E_g + (1 + R + E | id) + (0 + G | id)
#   y = 1 if the hard option was chosen. R = reward difference (hard - easy),
#   E = effort difference (hard - easy) / 10. "_t"/"_g" = slope for tapping/grip.
#   Assumption: only the gap counts (30 vs 10 costs the same as 80 vs 60).
#
# Model A - hard and easy effort level as separate predictors:
#   y ~ 0 + tap + grip + R_t + R_g + Eh_t + Eh_g + El_t + El_g + (1 + R + E | id) + (0 + G | id)
#   Eh = absolute effort level of the hard option / 10, El = of the easy option.
#   RV2 is the special case beta_El = -beta_Eh. If |beta_Eh| > beta_El, the
#   absolute level matters too (high-lying pairs are extra deterrent).
#
# Model B - curved cost function, cost = beta * level^p:
#   C = (Eh^p - El^p) * 7 / (8^p - 1)   (scaled so level 10 -> 80 equals 7 units, as in E)
#   y ~ 0 + tap + grip + R_t + R_g + C_t + C_g + (1 + R + E | id) + (0 + G | id)
#   p = 1 is the straight line of RV2; p > 1 means each further step costs more.
#   p (shared, or separately per task) is found by profiling the likelihood on a grid.
#
# Model C - one free cost per absolute level (no shape assumed):
#   D<L> = 1[Eh == L] - 1[El == L] for L = 20..80 (level 10 = reference, cost 0)
#   y ~ 0 + tap + grip + R_t + R_g + D2_t + ... + D8_t + D2_g + ... + D8_g + (1 + R + E | id) + (0 + G | id)
#   Each level gets its own cost per task; the shape of the cost curve is read off directly.
#
# Grip vs tapping is compared directly in every model via the exchange rate
# k = cost / beta_R (effort cost in coins); ratio = k_grip / k_tap (delta method CI).
#
# Usage:   Rscript analyses/extension_models.R
# Env:     EFFORT_DATA_DIR  folder with the (private) raw data, read by effortlib
#          EFFORT_LIB_DIR   optional path to the effortlib package source
#          EFFORT_CORES     optional number of cores for the p grid (default 4)
# Output:  analyses/out/extensions/*.csv and analyses/out/extensions/fig/*.png
#          (analyses/out is git-ignored; no data or fitted models are committed)
################################################################################

here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
if (Sys.getenv("EFFORT_DATA_DIR") == "") stop("Set EFFORT_DATA_DIR to the data folder (see data/README.md).")
lib_dir <- Sys.getenv("EFFORT_LIB_DIR")
suppressPackageStartupMessages({
  if (nzchar(lib_dir)) pkgload::load_all(lib_dir, quiet = TRUE, export_all = FALSE, helpers = FALSE) else library(effortlib)
  library(lme4); library(data.table); library(ggplot2); library(parallel)
})
OUT <- file.path(here, "out", "extensions"); FIG <- file.path(OUT, "fig")
dir.create(FIG, recursive = TRUE, showWarnings = FALSE)
NC <- as.integer(Sys.getenv("EFFORT_CORES", "4"))
COLD <- c(Tapping = "#0072B2", Grip = "#D55E00")

## ---------- helpers ----------
ctrl <- glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 3e5))
fitg <- function(f, d) { w <- character()
  m <- withCallingHandlers(glmer(as.formula(f), d, binomial, control = ctrl),
    warning = function(x) { w <<- c(w, conditionMessage(x)); invokeRestart("muffleWarning") })
  attr(m, "warn") <- w; m }
tab <- function(m) { b <- fixef(m); se <- sqrt(diag(as.matrix(vcov(m))))
  data.table(term = names(b), est = b, se = se, lo = b - 1.96 * se, hi = b + 1.96 * se, p = 2 * pnorm(-abs(b / se))) }
lc <- function(m, w, nm = "") { b <- fixef(m); V <- as.matrix(vcov(m)); L <- setNames(numeric(length(b)), names(b))
  stopifnot(all(names(w) %in% names(b))); L[names(w)] <- w
  e <- sum(L * b); se <- sqrt(drop(L %*% V %*% L))
  data.table(contrast = nm, est = e, se = se, lo = e - 1.96 * se, hi = e + 1.96 * se, p = 2 * pnorm(-abs(e / se))) }
dfun <- function(m, fun) { b <- fixef(m); V <- as.matrix(vcov(m))
  g <- sapply(seq_along(b), function(i) { h <- 1e-6 * max(1, abs(b[i])); bp <- b; bm <- b; bp[i] <- b[i] + h; bm[i] <- b[i] - h
    (fun(bp) - fun(bm)) / (2 * h) })
  e <- fun(b); se <- sqrt(drop(t(g) %*% V %*% g)); c(est = e, se = se, lo = e - 1.96 * se, hi = e + 1.96 * se, p = 2 * pnorm(-abs(e / se))) }
ratio_ci <- function(m, f) { r <- dfun(m, function(b) log(f(b))); data.table(ratio = exp(r[["est"]]), lo = exp(r[["lo"]]), hi = exp(r[["hi"]]), p = r[["p"]]) }
ll <- function(m) as.numeric(logLik(m))

## ---------- data ----------
d <- core_trials(); d[, grip := G]
d[, `:=`(Eh = E0 + E, El = E0)]                                   # absolute levels / 10 (1..8)
d[, `:=`(Eh_t = Eh * tap, Eh_g = Eh * G, El_t = El * tap, El_g = El * G)]
for (L in 2:8) { v <- (d$Eh == L) - (d$El == L); d[, paste0("D", L, "_t") := v * tap]; d[, paste0("D", L, "_g") := v * G] }
n <- nrow(d)
RE <- "(1 + R + E | id) + (0 + G | id)"                           # RV2 random effects, identical in all models

## ---------- RV2 ----------
rv2 <- fitg(paste("y ~ 0 + tap + grip + R_t + R_g + E_t + E_g +", RE), d)
k_rv2 <- ratio_ci(rv2, function(b) (b[["E_g"]] / b[["R_g"]]) / (b[["E_t"]] / b[["R_t"]]))

## ---------- A ----------
mA <- fitg(paste("y ~ 0 + tap + grip + R_t + R_g + Eh_t + Eh_g + El_t + El_g +", RE), d)
cA <- rbind(lc(mA, c(Eh_t = 1, El_t = 1), "Eh_t + El_t (0 = difference model holds, tap)"),
            lc(mA, c(Eh_g = 1, El_g = 1), "Eh_g + El_g (0 = difference model holds, grip)"),
            lc(mA, c(Eh_t = -1, El_t = -1, Eh_g = 1, El_g = 1), "level effect grip - tap"))
k_A <- ratio_ci(mA, function(b) (b[["Eh_g"]] / b[["R_g"]]) / (b[["Eh_t"]] / b[["R_t"]]))
fwrite(tab(mA), file.path(OUT, "A_coef.csv")); fwrite(cA, file.path(OUT, "A_contrasts.csv"))

## ---------- B ----------
addC <- function(pt, pg) { x <- copy(d)
  x[, C := ifelse(tap == 1, (Eh^pt - El^pt) * 7 / (8^pt - 1), (Eh^pg - El^pg) * 7 / (8^pg - 1))]
  x[, `:=`(C_t = C * tap, C_g = C * G)]; x }
fitB <- function(pt, pg) fitg(paste("y ~ 0 + tap + grip + R_t + R_g + C_t + C_g +", RE), addC(pt, pg))
prof <- function(G) rbindlist(mclapply(seq_len(nrow(G)), function(i)
  data.table(pt = G$pt[i], pg = G$pg[i], ll = ll(fitB(G$pt[i], G$pg[i]))), mc.cores = NC))
sh <- prof(data.table(pt = seq(0.5, 6, 0.25), pg = seq(0.5, 6, 0.25)))        # shared p
g2 <- prof(CJ(pt = seq(1, 5.5, 0.5), pg = seq(1, 5.5, 0.5)))                   # per task, coarse
b0 <- g2[which.max(ll)]
g3 <- prof(CJ(pt = seq(b0$pt - 0.4, b0$pt + 0.4, 0.1), pg = seq(b0$pg - 0.4, b0$pg + 0.4, 0.1)))  # fine
p2 <- unique(rbind(g2, g3)[, `:=`(pt = round(pt, 2), pg = round(pg, 2))], by = c("pt", "pg"))
fwrite(sh, file.path(OUT, "B_profile_shared.csv")); fwrite(p2, file.path(OUT, "B_profile_2d.csv"))
bs <- sh[which.max(ll)]; bt <- p2[which.max(ll)]
mBs <- fitB(bs$pt, bs$pt); mBt <- fitB(bt$pt, bt$pg)
fwrite(tab(mBt), file.path(OUT, "B_coef_pertask.csv"))
Es <- mean(c(d$Eh, d$El))                                          # ratio of marginal cost at the mean level
k_B <- ratio_ci(mBt, function(b) (b[["C_g"]] * bt$pg * Es^(bt$pg - 1) / (8^bt$pg - 1) / b[["R_g"]]) /
                                 (b[["C_t"]] * bt$pt * Es^(bt$pt - 1) / (8^bt$pt - 1) / b[["R_t"]]))

## ---------- C ----------
fC <- paste("y ~ 0 + tap + grip + R_t + R_g +", paste(c(paste0("D", 2:8, "_t"), paste0("D", 2:8, "_g")), collapse = " + "), "+", RE)
mC <- fitg(fC, d)
fwrite(tab(mC), file.path(OUT, "C_coef.csv"))
KC <- rbindlist(lapply(2:8, function(Lv) rbind(
  data.table(level = Lv * 10, task = "Tapping", t(dfun(mC, function(b) -b[[paste0("D", Lv, "_t")]] / b[["R_t"]])))
  , data.table(level = Lv * 10, task = "Grip", t(dfun(mC, function(b) -b[[paste0("D", Lv, "_g")]] / b[["R_g"]]))))))
fwrite(KC, file.path(OUT, "C_cost_per_level_in_coins.csv"))
k_C <- ratio_ci(mC, function(b) (b[["D8_g"]] / b[["R_g"]]) / (b[["D8_t"]] / b[["R_t"]]))
jump <- rbindlist(lapply(c("t", "g"), function(s) { nm <- paste0("D", 2:8, "_", s); w <- setNames(numeric(7), nm)
  w[nm[7]] <- -1; w[nm[6]] <- 1 + 1/6; cbind(task = s, lc(mC, w, "step 70->80 minus average step 10->70")) }))
jump <- rbind(jump, cbind(task = "g-t", lc(mC, c(D8_g = -1, D7_g = 1 + 1/6, D8_t = 1, D7_t = -(1 + 1/6)), "jump grip - tap")))
fwrite(jump, file.path(OUT, "C_jump_test.csv"))

## ---------- comparison ----------
ic <- function(name, m, k) data.table(model = name, logLik = ll(m), npar = k, AIC = -2 * ll(m) + 2 * k, BIC = -2 * ll(m) + log(n) * k)
cmp <- rbind(ic("RV2 (linear difference)", rv2, 13), ic("A (hard/easy separate)", mA, 15),
             ic(sprintf("B shared p=%.2f", bs$pt), mBs, 14), ic(sprintf("B p_tap=%.2f p_grip=%.2f", bt$pt, bt$pg), mBt, 15),
             ic("C (one cost per level)", mC, 25))
lrt <- function(a, ma, b, mb, df) data.table(test = paste(a, "vs", b), chisq = 2 * (ll(mb) - ll(ma)), df = df,
                                             p = pchisq(2 * (ll(mb) - ll(ma)), df, lower.tail = FALSE))
L <- rbind(lrt("RV2", rv2, "A", mA, 2), lrt("RV2", rv2, "B shared", mBs, 1), lrt("RV2", rv2, "B per task", mBt, 2),
           lrt("RV2", rv2, "C", mC, 12))
K <- rbind(cbind(model = "RV2", k_rv2), cbind(model = "A (hard level)", k_A),
           cbind(model = "B (marginal cost at mean level)", k_B), cbind(model = "C (cost of level 80)", k_C))
fwrite(cmp, file.path(OUT, "model_comparison.csv")); fwrite(L, file.path(OUT, "lrts.csv")); fwrite(K, file.path(OUT, "ratio_grip_tap.csv"))
print(cmp); print(L); print(K)

## ---------- figures ----------
th <- theme_bw(base_size = 12) + theme(legend.position = "top", plot.caption = element_text(hjust = 0, size = 8.5), plot.caption.position = "plot")
tA <- tab(mA)[term %in% c("Eh_t", "Eh_g", "El_t", "El_g")]
tA[, task := factor(ifelse(grepl("_t$", term), "Tapping", "Grip"), c("Tapping", "Grip"))]
tA[, opt := ifelse(grepl("^Eh", term), "Effort of hard option", "Effort of easy option")]
gA <- ggplot(tA, aes(opt, est, colour = task)) + geom_hline(yintercept = 0, linetype = 2) +
  geom_pointrange(aes(ymin = lo, ymax = hi), position = position_dodge(0.4)) + scale_colour_manual(values = COLD, name = "Task") +
  labs(x = NULL, y = "Weight beta (log-odds per +10 effort)", title = "Model A: hard and easy effort level separate",
       caption = paste0("Points = fixed effects, bars = 95% CI; tapping and grip side by side. Dashed line = 0 (no effect).\n",
                        "If only the difference mattered (RV2), both points of a task would be equally far from 0.\n",
                        sprintf("LRT vs RV2: chi2(2) = %.1f.", L$chisq[1]))) + th
ggsave(file.path(FIG, "A_hard_easy_effort.png"), gA, width = 8, height = 6, dpi = 150)

lev <- seq(1, 8, 0.05); bB <- fixef(mBt); bR <- fixef(rv2)
cB <- rbind(
  data.table(E = lev * 10, task = "Tapping", cost = -bB[["C_t"]] * 7 / (8^bt$pt - 1) * (lev^bt$pt - 1) / bB[["R_t"]], mod = "Model B (curved)"),
  data.table(E = lev * 10, task = "Grip", cost = -bB[["C_g"]] * 7 / (8^bt$pg - 1) * (lev^bt$pg - 1) / bB[["R_g"]], mod = "Model B (curved)"),
  data.table(E = lev * 10, task = "Tapping", cost = -bR[["E_t"]] * (lev - 1) / bR[["R_t"]], mod = "RV2 (linear, p = 1)"),
  data.table(E = lev * 10, task = "Grip", cost = -bR[["E_g"]] * (lev - 1) / bR[["R_g"]], mod = "RV2 (linear, p = 1)"))
pts <- rbind(data.table(level = 10, task = c("Tapping", "Grip"), est = 0, lo = 0, hi = 0), KC[, .(level, task, est, lo, hi)])
cB[, task := factor(task, c("Tapping", "Grip"))]; pts[, task := factor(task, c("Tapping", "Grip"))]
gB <- ggplot() + geom_line(data = cB, aes(E, cost, linetype = mod), colour = "grey20") +
  geom_pointrange(data = pts, aes(level, est, ymin = lo, ymax = hi, colour = task), size = 0.3) + facet_wrap(~task) +
  scale_colour_manual(values = COLD, guide = "none") + scale_linetype_manual(values = c(1, 2), name = NULL) +
  scale_x_continuous(breaks = seq(10, 80, 10)) +
  labs(x = "Absolute effort level", y = "Cost in coins (relative to level 10)", title = "Model B: curved cost = beta * effort^p",
       caption = sprintf("Solid = model B (p_tap = %.2f, p_grip = %.2f), dashed = linear RV2. Points = free per-level estimates from model C (95%% CI).",
                         bt$pt, bt$pg)) + th
ggsave(file.path(FIG, "B_curved_cost.png"), gB, width = 10, height = 6, dpi = 150)

pr <- rbind(p2[, .(ll = max(ll)), by = .(p = pt)][, task := "Tapping"], p2[, .(ll = max(ll)), by = .(p = pg)][, task := "Grip"])
pr[, `:=`(dll = ll - max(p2$ll), task = factor(task, c("Tapping", "Grip")))]
gP <- ggplot(pr[order(p)], aes(p, dll, colour = task)) + geom_line() + geom_point(size = 1) + geom_hline(yintercept = -1.92, linetype = 2) +
  geom_vline(xintercept = 1, linetype = 3) + scale_colour_manual(values = COLD, name = "Task") + coord_cartesian(ylim = c(-30, 0)) +
  labs(x = "Exponent p", y = "Log-likelihood relative to best", title = "Model B: profile likelihood for p",
       caption = "Dashed = approx. 95% CI threshold (-1.92). Dotted = p = 1 (linear RV2).") + th
ggsave(file.path(FIG, "B_profile_p.png"), gP, width = 8, height = 5.5, dpi = 150)

gC <- ggplot(pts, aes(level, est, colour = task)) + geom_line(position = position_dodge(3)) +
  geom_pointrange(aes(ymin = lo, ymax = hi), position = position_dodge(3)) + scale_colour_manual(values = COLD, name = "Task") +
  scale_x_continuous(breaks = seq(10, 80, 10)) +
  labs(x = "Absolute effort level", y = "Cost in coins (relative to level 10)", title = "Model C: one cost per effort level",
       caption = paste0("Points = cost of each level in coins (-beta_level / beta_R), bars = 95% CI (delta method). Level 10 = reference.\n",
                        sprintf("Linear costs would lie on a straight line. LRT C vs RV2: chi2(12) = %.1f.", L$chisq[4]))) + th
ggsave(file.path(FIG, "C_cost_per_level.png"), gC, width = 9, height = 6, dpi = 150)
cat("done; outputs in", OUT, "\n")
