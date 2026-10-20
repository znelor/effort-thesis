## Common set-up sourced by every R analysis script:
##   source(file.path(dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])), "setup.R"))
## Loads effortlib (from EFFORT_LIB_DIR env var or an installed copy), the modelling/plotting
## packages, sets the thesis figure theme, and defines `out` (= <analysis folder>/out, tables/fits, git-ignored)
## and `figs` (= <repo>/output/<base|exploratory>/<analysis>, figures, tracked).
##
## EFFORT_LIB_DIR: Path to the private effortlib R package directory.
##   This package contains data loading functions and analysis helpers.
##   Set this environment variable before running analyses:
##     export EFFORT_LIB_DIR=/path/to/effort-thesis-analysis/effortlib
##
local({
  # Check for EFFORT_LIB_DIR environment variable
  effort_lib_dir <- Sys.getenv("EFFORT_LIB_DIR", "")
  
  if (nzchar(effort_lib_dir)) {
    # Load from specified path
    lib <- normalizePath(effort_lib_dir, mustWork = FALSE)
    if (!file.exists(file.path(lib, "DESCRIPTION"))) {
      stop("EFFORT_LIB_DIR is set but effortlib DESCRIPTION not found at: ", lib,
           "\nPlease set EFFORT_LIB_DIR to the effortlib package directory.")
    }
  } else {
    # Fallback: look for effortlib in parent directories (private repo structure)
    here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
    lib <- here
    while (!file.exists(file.path(lib, "effortlib", "DESCRIPTION")) && dirname(lib) != lib) {
      lib <- dirname(lib)
    }
    lib <- file.path(lib, "effortlib")
    
    if (!file.exists(file.path(lib, "DESCRIPTION"))) {
      stop("effortlib not found. Please set EFFORT_LIB_DIR environment variable:\n",
           "  export EFFORT_LIB_DIR=/path/to/effort-thesis-analysis/effortlib\n",
           "Or install effortlib as a regular R package.")
    }
  }
  
  # Load effortlib
  if (requireNamespace("pkgload", quietly = TRUE) && file.exists(file.path(lib, "DESCRIPTION"))) {
    suppressPackageStartupMessages(pkgload::load_all(lib, quiet = TRUE, export_all = FALSE, helpers = FALSE))
  } else {
    suppressPackageStartupMessages(library(effortlib))
  }
})

suppressPackageStartupMessages({library(data.table); library(ggplot2); library(patchwork); library(lme4); library(scales)})
use_effort_style()
out <- out_dir()
figs <- fig_dir()
cols <- mod_cols; labsM <- mod_labels                                # short names used throughout the figure code
save2 <- function(p, name, w, h) save_fig(p, name, w, h, dir = figs)  # PDF + 300-dpi PNG into output/<analysis>/
