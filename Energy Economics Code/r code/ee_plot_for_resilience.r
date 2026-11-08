# Energy Economics resilience figures
# The script contains four top-level blocks. See readme.txt for prerequisites.

# Required packages
# Install missing packages once, if needed:
# install.packages(c("ggplot2", "readxl", "sysfonts", "showtext"))
# grid is included with R.
library(ggplot2)
library(grid)
library(readxl)
library(sysfonts)
library(showtext)

{
  # Block 1. Three-panel resilience schematic

  # 1. Font setting
  # macOS Times New Roman path
  font_regular <- "/System/Library/Fonts/Supplemental/Times New Roman.ttf"
  font_bold <- "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf"
  font_italic <- "/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf"
  font_bolditalic <- "/System/Library/Fonts/Supplemental/Times New Roman Bold Italic.ttf"

  font_files <- c(font_regular, font_bold, font_italic, font_bolditalic)

  if (!all(file.exists(font_files))) {
    stop("Times New Roman font files not found. Please check the font paths.")
  }

  font_add(family = "Times New Roman", regular = font_regular, bold = font_bold,
    italic = font_italic, bolditalic = font_bolditalic)

  FONT_FAMILY <- "Times New Roman"

  # 2. Output device
  # Find the package root, including when R starts in a code subdirectory.
  PROJECT_DIR <- (function() {
    start_dirs <- c(if (exists("PROJECT_DIR", inherits = TRUE)) PROJECT_DIR, getwd())
    for (start_dir in unique(start_dirs)) {
      if (!dir.exists(start_dir)) next
      root <- normalizePath(start_dir, winslash = "/", mustWork = TRUE)
      repeat {
        if (all(dir.exists(file.path(root,
          c("Energy Economics Code", "Energy Economics Data"))))) return(root)
        parent <- dirname(root)
        if (identical(parent, root)) break
        root <- parent
      }
    }
    stop("Project root not found. Set PROJECT_DIR to the folder containing ",
      "Energy Economics Code and Energy Economics Data.")
  })()
  FIG_DIR <- file.path(PROJECT_DIR, "Fig")
  dir.create(FIG_DIR, recursive = TRUE, showWarnings = FALSE)
  pdf(file.path(FIG_DIR, "r_plot_resilience_abc_vertical_re.pdf"),
    width = 6.2, height = 12.2, useDingbats = FALSE)

  showtext_begin()

  # 3. Global settings
  par(mfrow = c(3, 1), mar = c(2.6, 3.4, 1.1, 1.2), oma = c(0.2, 0.2, 0.2, 0.2), family = FONT_FAMILY
  )

  # 4. Global font and style controls
  BASE_CEX <- 1.55

  CEX_LEVEL <- BASE_CEX
  CEX_AXIS <- BASE_CEX * 0.92
  CEX_TICK_T <- BASE_CEX * 0.95
  CEX_SHOCK <- BASE_CEX * 0.95
  CEX_H <- BASE_CEX * 0.84
  CEX_AREA <- BASE_CEX * 1.02
  CEX_S <- BASE_CEX * 1.10
  CEX_PANEL <- BASE_CEX * 0.78
  CEX_ABCD <- BASE_CEX * 0.78

  DASH_COL <- "#A8CFF0"
  DASH_LTY <- 2
  DASH_LWD <- 1.6

  # 5. Helpers
  beta_shape <- function(u, a, b) {
    out <- rep(0, length(u))
    idx <- (u > 0) & (u < 1)
    out[idx] <- u[idx]^(a - 1) * (1 - u[idx])^(b - 1)
    out
  }

  make_curve <- function(x, t1, t2, S0 = 0.72, A = 0.38, a = 2.2, b = 4.5) {
    y <- rep(S0, length(x))
    idx <- x >= t1 & x <= t2
    u <- (x[idx] - t1) / (t2 - t1)

    grid <- seq(0, 1, length.out = 4001)
    smax <- max(beta_shape(grid, a, b))
    loss <- A * beta_shape(u, a, b) / smax

    y[idx] <- S0 - loss
    y
  }

  fill_between <- function(x, y, S0, from, to, col = gray(0.88)) {
    idx <- x >= from & x <= to
    polygon(c(x[idx], rev(x[idx])), c(rep(S0, sum(idx)), rev(y[idx])), col = col, border = NA)
  }

  curve_area <- function(x, y, S0, from, to) {
    idx <- x >= from & x <= to
    xx <- x[idx]
    ww <- S0 - y[idx]
    sum(diff(xx) * (head(ww, -1) + tail(ww, -1)) / 2)
  }

  match_area_amplitude <- function(target_area, x, t1, t2, S0, a, b, A_lower = 0.05, A_upper = 1.50) {
    f <- function(A) {
      y_tmp <- make_curve(x, t1, t2, S0 = S0, A = A, a = a, b = b)
      curve_area(x, y_tmp, S0, t1, t2) - target_area
    }
    uniroot(f, c(A_lower, A_upper))$root
  }

  match_shape_fixed_peak_and_amplitude <- function(target_area, x, t1, t2, S0, A_fixed, u_peak,
    k_lower = 0.05, k_upper = 200) {
    make_ab <- function(k) {
      c(a = 1 + k * u_peak, b = 1 + k * (1 - u_peak))
    }

    f <- function(k) {
      ab <- make_ab(k)

      y_tmp <- make_curve(x, t1, t2, S0 = S0, A = A_fixed, a = ab["a"], b = ab["b"])

      curve_area(x, y_tmp, S0, t1, t2) - target_area
    }

    while (f(k_lower) < 0) {
      k_lower <- k_lower / 2
    }

    while (f(k_upper) > 0) {
      k_upper <- k_upper * 2
    }

    k_star <- uniroot(f, c(k_lower, k_upper))$root
    ab_star <- make_ab(k_star)

    list(k = k_star, a = ab_star["a"], b = ab_star["b"])
  }

  # Retain both existing helper names with one implementation.
  match_shape_fixed_peak_fixed_amplitude <- match_shape_fixed_peak_and_amplitude

  interp_y <- function(x, y, x0) {
    approx(x = x, y = y, xout = x0)$y
  }

  panel_tag <- function(tag) {
    mtext(tag, side = 1, line = 0.55, cex = CEX_PANEL, family = FONT_FAMILY)
  }

  draw_h_arrow <- function(x_arrow, y_level, label_expr, x_label = NULL, cex_lab = CEX_H) {
    if (is.null(x_label)) x_label <- x_arrow - 0.16

    arrows(x0 = x_arrow, y0 = y_level, x1 = x_arrow, y1 = S0, code = 3, angle = 18, length = 0.08,
      lwd = 1.45, col = "black", xpd = NA)

    text(x = x_label, y = (S0 + y_level) / 2, labels = label_expr, xpd = NA, cex = cex_lab,
      family = FONT_FAMILY)
  }

  draw_axes <- function(xlim, ylim, S0, t1, t2) {
    plot(NA, xlim = xlim, ylim = ylim, type = "n", axes = FALSE, xlab = "", ylab = "")

    # axes with arrows
    arrows(0, 0, xlim[2], 0, length = 0.08, lwd = 2.6, col = "black", xpd = NA)
    arrows(0, 0, 0, ylim[2], length = 0.08, lwd = 2.6, col = "black", xpd = NA)

    # steady-state line
    segments(0, S0, xlim[2] * 0.95, S0, lwd = 1.4, col = "black")

    # t1, t2 dashed vertical lines
    segments(t1, 0, t1, S0, lty = DASH_LTY, lwd = DASH_LWD, col = DASH_COL)
    segments(t2, 0, t2, S0, lty = DASH_LTY, lwd = DASH_LWD, col = DASH_COL)

    # labels
    text(-0.28, S0, expression(S[0]), xpd = NA, cex = CEX_AXIS, family = FONT_FAMILY)
    text(t1, -0.045, expression(t[1]), xpd = NA, cex = CEX_TICK_T, family = FONT_FAMILY)
    text(t2, -0.045, expression(t[2]), xpd = NA, cex = CEX_TICK_T, family = FONT_FAMILY)

    text(xlim[2], -0.02, "Time", xpd = NA, adj = c(1, 1), cex = CEX_AXIS, family = FONT_FAMILY)

    # y-axis label
    text(x = -1.18, y = ylim[2] * 0.88, labels = "State", xpd = NA, cex = CEX_LEVEL, adj = c(0, 0.5),
      family = FONT_FAMILY)

    # Shock arrow
    arrows(t1, S0 + 0.20, t1, S0 + 0.05, length = 0.10, lwd = 2.8, col = "black", xpd = NA)

    text(t1 + 0.78, S0 + 0.14, "Shock", font = 2, cex = CEX_SHOCK, xpd = NA, family = FONT_FAMILY)
  }

  # 6. Shared settings
  x <- seq(0, 9.2, length.out = 1800)
  xlim <- c(0, 9.2)
  ylim <- c(0, 1.10)
  S0 <- 0.72
  t1 <- 1.8
  t2 <- 7.8

  # h positions
  x_h_arrow_main <- t1 - 0.40
  x_h_label_main <- t1 - 0.86

  x_hA_arrow <- t1 - 0.12
  x_hA_label <- t1 - 0.45

  x_hB_arrow <- t1 - 0.71
  x_hB_label <- t1 - 1.05

  x_hC_arrow <- t1 - 0.12
  x_hC_label <- t1 - 0.45

  x_hD_arrow <- t1 - 0.71
  x_hD_label <- t1 - 1.05

  # common label positions
  x_S_pos <- 6.05
  S_offset_above_line <- 0.05

  # Panel (a): Benchmark definition
  draw_axes(xlim, ylim, S0, t1, t2)

  y_a <- make_curve(x, t1, t2, S0 = S0, A = 0.40, a = 2.2, b = 4.5)
  fill_between(x, y_a, S0, t1, t2, col = gray(0.88))
  lines(x, y_a, lwd = 2.2, col = "black")

  y_min_a <- min(y_a)
  S_y_pos <- y_min_a + S_offset_above_line

  segments(0, y_min_a, t2, y_min_a, lty = DASH_LTY, lwd = DASH_LWD, col = DASH_COL)

  draw_h_arrow(x_arrow = x_h_arrow_main, y_level = y_min_a, label_expr = expression(bar(h)),
    x_label = x_h_label_main, cex_lab = CEX_H)

  text(3.95, 0.50, expression(Delta*S), cex = CEX_AREA, family = FONT_FAMILY)

  text(x_S_pos, S_y_pos, expression(S), cex = CEX_S, font = 2, family = FONT_FAMILY)

  panel_tag("(a)")

  # Panel (b): Intensity comparison
  draw_axes(xlim, ylim, S0, t1, t2)

  y_b1 <- make_curve(x, t1, t2, S0 = S0, A = 0.24, a = 2.2, b = 4.5)
  y_b2 <- make_curve(x, t1, t2, S0 = S0, A = 0.42, a = 2.2, b = 4.5)

  fill_between(x, y_b2, S0, t1, t2, col = adjustcolor("gray65", alpha.f = 0.35))
  fill_between(x, y_b1, S0, t1, t2, col = adjustcolor("gray35", alpha.f = 0.18))

  lines(x, y_b1, lwd = 2.1, col = "black")
  lines(x, y_b2, lwd = 2.1, col = "black", lty = 2)

  x_min_b1 <- x[which.min(y_b1)]
  y_min_b1 <- min(y_b1)
  x_min_b2 <- x[which.min(y_b2)]
  y_min_b2 <- min(y_b2)

  segments(0, y_min_b1, x_min_b1, y_min_b1, lty = DASH_LTY, lwd = DASH_LWD, col = DASH_COL)
  segments(0, y_min_b2, x_min_b2, y_min_b2, lty = DASH_LTY, lwd = DASH_LWD, col = DASH_COL)

  draw_h_arrow(x_arrow = x_hA_arrow, y_level = y_min_b1, label_expr = expression(h[A]),
    x_label = x_hA_label, cex_lab = CEX_H)

  draw_h_arrow(x_arrow = x_hB_arrow, y_level = y_min_b2, label_expr = expression(h[B]),
    x_label = x_hB_label, cex_lab = CEX_H)

  text(4.15, 0.60, expression(Delta*S[A]), cex = CEX_AREA * 0.90, family = FONT_FAMILY)
  text(4.35, 0.34, expression(Delta*S[B]), cex = CEX_AREA * 0.90, family = FONT_FAMILY)

  panel_tag("(b)")

  # Panel (c): Same area, different timing profile
  # h_C = h_D; D keeps its original peak-time position;
  # Delta S_C = Delta S_D
  draw_axes(xlim, ylim, S0, t1, t2)

  # Curve C
  a_d1 <- 2.0
  b_d1 <- 4.8
  A_d1 <- 0.40

  y_d1 <- make_curve(x, t1, t2, S0 = S0, A = A_d1, a = a_d1, b = b_d1)

  target_area_d <- curve_area(x, y_d1, S0, t1, t2)

  x_min_d1 <- x[which.min(y_d1)]
  y_min_d1 <- min(y_d1)

  # Curve D
  a_d2_old <- 2.7
  b_d2_old <- 4.0
  u_peak_D_old <- (a_d2_old - 1) / (a_d2_old + b_d2_old - 2)

  A_d2 <- A_d1

  shape_d2 <- match_shape_fixed_peak_fixed_amplitude(target_area = target_area_d, x = x,
    t1 = t1, t2 = t2, S0 = S0, A_fixed = A_d2, u_peak = u_peak_D_old)

  a_d2 <- shape_d2$a
  b_d2 <- shape_d2$b

  y_d2 <- make_curve(x, t1, t2, S0 = S0, A = A_d2, a = a_d2, b = b_d2)

  x_min_d2 <- x[which.min(y_d2)]
  y_min_d2 <- min(y_d2)

  # Fill areas
  fill_between(x, y_d1, S0, t1, t2, col = adjustcolor("gray55", alpha.f = 0.22))

  fill_between(x, y_d2, S0, t1, t2, col = adjustcolor("gray75", alpha.f = 0.22))

  # Draw curves
  lines(x, y_d1, lwd = 2.1, col = "black")
  lines(x, y_d2, lwd = 2.1, col = "black", lty = 2)

  # Dashed horizontal reference lines
  segments(0, y_min_d1, x_min_d1, y_min_d1, lty = DASH_LTY, lwd = DASH_LWD, col = DASH_COL)

  segments(0, y_min_d2, x_min_d2, y_min_d2, lty = DASH_LTY, lwd = DASH_LWD, col = DASH_COL)

  # h_C and h_D arrows
  draw_h_arrow(x_arrow = x_hC_arrow, y_level = y_min_d1, label_expr = expression(h[C]),
    x_label = x_hC_label, cex_lab = CEX_H)

  draw_h_arrow(x_arrow = x_hD_arrow, y_level = y_min_d2, label_expr = expression(h[D]),
    x_label = x_hD_label, cex_lab = CEX_H)

  # Area labels
  text(3.55, 0.51, expression(Delta*S[C]), cex = CEX_AREA * 0.90, family = FONT_FAMILY)

  text(5.65, 0.51, expression(Delta*S[D]), cex = CEX_AREA * 0.90, family = FONT_FAMILY)

  panel_tag("(c)")

  # 7. Finish
  showtext_end()
  dev.off()
} # Three vertical resilience schematic panels used in the final manuscript

{
  # Block 2. Combined vertical resilience plots: GPR, CPU, and OPU
  # Vertical layout: 6 x 2
  # Rows 1-5: RI/RD plots for the five markets
  # Row 6: compact event labels only
  # One shared plotting function preserves the original three PDF outputs.

  # 1) Font setting
  FONT_FAMILY <- "sans"

  font_regular <- "/System/Library/Fonts/Supplemental/Times New Roman.ttf"
  font_bold <- "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf"
  font_italic <- "/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf"
  font_bolditalic <- "/System/Library/Fonts/Supplemental/Times New Roman Bold Italic.ttf"

  font_files <- c(font_regular, font_bold, font_italic, font_bolditalic)

  if (all(file.exists(font_files))) {
    font_add(family = "Times New Roman", regular = font_regular, bold = font_bold,
      italic = font_italic, bolditalic = font_bolditalic)
    FONT_FAMILY <- "Times New Roman"
  }

  # Shared inputs and outputs
  # Keep all three shocks to reproduce the original three PDF outputs.
  # Use, for example, c("GPR") to generate only one shock figure.
  TARGET_SHOCKS <- c("GPR", "CPU", "OPU")

  # Find the package root, including when R starts in a code subdirectory.
  PROJECT_DIR <- (function() {
    start_dirs <- c(if (exists("PROJECT_DIR", inherits = TRUE)) PROJECT_DIR, getwd())
    for (start_dir in unique(start_dirs)) {
      if (!dir.exists(start_dir)) next
      root <- normalizePath(start_dir, winslash = "/", mustWork = TRUE)
      repeat {
        if (all(dir.exists(file.path(root,
          c("Energy Economics Code", "Energy Economics Data"))))) return(root)
        parent <- dirname(root)
        if (identical(parent, root)) break
        root <- parent
      }
    }
    stop("Project root not found. Set PROJECT_DIR to the folder containing ",
      "Energy Economics Code and Energy Economics Data.")
  })()
  RESILIENCE_FILE <- file.path(
    PROJECT_DIR, "Energy Economics Code", "matlab code", "resilience_metrics.xlsx")
  RESILIENCE_OUTPUT_DIR <- file.path(PROJECT_DIR, "Fig")

  r_data <- read_xlsx(RESILIENCE_FILE)
  # Read the full TVP-VAR calendar and omit its initial, unestimated period.
  VAR_DATA_FILE <- file.path(PROJECT_DIR, "Energy Economics Data", "VAR_100data.xlsx")
  sample_dates <- as.Date(read_xlsx(VAR_DATA_FILE, sheet = "VAR_100data")$date)
  if (length(sample_dates) != 167L || anyNA(sample_dates)) {
    stop("VAR_100data.xlsx must contain 167 valid dates in its date column.")
  }
  x_date <- sample_dates[2:167] # February 2010-November 2023: 166 observations.

  # Shock-specific market mappings
  MARKET_VAR_MAPS <- list(
    GPR = c(OIL = "Var6", NG = "Var7", COAL = "Var8", ERIX = "Var9", EUA = "Var10"),
    CPU = c(OIL = "Var14", NG = "Var15", COAL = "Var16", ERIX = "Var17", EUA = "Var18"),
    OPU = c(OIL = "Var22", NG = "Var23", COAL = "Var24", ERIX = "Var25", EUA = "Var26"))

  # Original event-label adjustments, applied in the listed order
  # measure = "both" applies to RI and RD; "RI" or "RD" changes one column.
  # Append a later row for a single measure to override an earlier "both" row.
  EVENT_LABEL_ADJUSTMENTS <- list(GPR = data.frame(
    event_id = c("E01", "E02", "E03", "E08", "E10", "E12", "E15", "E17", "E22"), measure = "both",
    x_shift_months = c(-15, 0, -8, -24, -14, -27, -18, -23, -17),
    y_pos = c(0.75, 0.26, 0.75, 0.50, 0.75, 0.25, 0.75, 0.24, 0.50), stringsAsFactors = FALSE
    ), CPU = data.frame(event_id = c("E04", "E06", "E09", "E11", "E14", "E18", "E19", "E21"),
    measure = "both", x_shift_months = c(-23, -12, -35, -18, -48, -9, -27, -19),
    y_pos = c(0.76, 0.76, 0.22, 0.76, 0.22, 0.76, 0.22, 0.22), stringsAsFactors = FALSE
    ), OPU = data.frame(event_id = c("E01", "E05", "E07", "E10", "E13", "E17", "E20", "E22"),
    measure = "both", x_shift_months = c(-12, -10, -12, -15, -18, -27, -23, -18),
    y_pos = c(0.75, 0.75, 0.25, 0.75, 0.25, 0.75, 0.75, 0.25), stringsAsFactors = FALSE))

  # Shared generator for the three vertical resilience figures
  plot_vertical_resilience <- function(target_shock, r_data, x_date, target_dir) {
    # 2) Basic settings
    TARGET_SHOCK <- match.arg(target_shock, names(MARKET_VAR_MAPS))

    year_ticks <- seq(from = as.Date(paste0(format(min(x_date), "%Y"), "-01-01")),
      to = as.Date(paste0(format(max(x_date), "%Y"), "-01-01")), by = "1 year")

    # 3) Output file
    dir.create(target_dir, recursive = TRUE, showWarnings = FALSE)

    out_file <- file.path(target_dir,
      paste0(tolower(TARGET_SHOCK), "_resilience_6x2_academic_fine_labels.pdf"))

    # 4) Style controls
    col_ri <- "#2166AC"
    col_rd <- "#B2182B"

    SHADE_COL <- adjustcolor("gray40", alpha.f = 0.12)
    GRID_COL <- adjustcolor("gray70", alpha.f = 0.28)
    AXIS_COL <- "gray25"
    TEXT_COL <- "gray10"

    # User-specified style parameters
    LINE_WIDTH <- 4.4
    CEX_X <- 2
    CEX_Y <- 2.25
    CEX_MAIN <- 2.25
    CEX_EVENT <- if (TARGET_SHOCK == "CPU") 1.15 else 1.75
    CEX_HEADER <- 1.30

    GRID_LWD <- 0.6
    AXIS_LWD <- 0.8
    BOX_LWD <- 0.8

    # Event-label panel settings
    EVENT_SRT <- 0

    # Height of row 6: smaller values make the label panel more compact
    # If labels are clipped or overlap, increase EVENT_PANEL_HEIGHT as needed
    EVENT_PANEL_HEIGHT <- 0.32

    RI_STEP <- 0.1
    RD_STEP <- NULL

    # 5) Market mapping
    market_var_map <- MARKET_VAR_MAPS[[TARGET_SHOCK]]

    market_order <- c("OIL", "NG", "COAL", "ERIX", "EUA")

    # 6) Extract RI / RD from r_data
    get_market_data <- function(market) {
      var_code <- unname(market_var_map[market])
      idx <- r_data$Variable == var_code

      if (sum(idx) == 0) {
        stop("No rows found for ", market, " / ", var_code)
      }

      out <- data.frame(RP = as.numeric(r_data[idx, 3][[1]]), RD = as.numeric(r_data[idx, 4][[1]]))

      if (nrow(out) != length(x_date)) {
        stop(paste0(market, " has a different number of observations from x_date: ",
          "nrow(out) = ", nrow(out), ", length(x_date) = ", length(x_date)))
      }

      out
    }

    # 7) Major-event windows in the revised Supplementary_Appendix.tex.
    # E16 (Indonesia coal ban) is absent from the current eight-event CPU list.
    events <- data.frame(
      event_id = c("E01", "E02", "E03", "E04", "E05", "E06", "E07", "E08", "E09", "E10", "E11", "E12", "E13", "E14", "E15", "E17", "E18", "E19", "E20", "E21", "E22"),
      type = c("GPR_OPU", "GPR", "GPR", "CPU", "OPU", "CPU", "OPU", "GPR", "CPU", "GPR_OPU", "CPU", "GPR", "OPU", "CPU", "GPR", "GPR_OPU", "CPU", "CPU", "OPU", "CPU", "GPR_OPU"),
      start = as.Date(c("2011-02-01", "2012-01-01", "2014-02-01", "2012-11-01", "2014-11-01", "2015-11-01", "2016-01-01", "2017-01-01", "2017-06-01", "2019-09-01", "2019-12-01", "2020-01-01", "2020-03-01", "2021-07-01", "2021-09-01", "2022-02-01", "2022-03-01", "2022-08-01", "2023-04-01", "2023-02-01", "2023-10-01")),
      end = as.Date(c("2011-10-01", "2012-07-01", "2015-02-01", "2013-09-01", "2016-02-01", "2016-01-01", "2017-03-01", "2017-12-01", "2017-12-01", "2019-10-01", "2020-03-01", "2020-02-01", "2020-06-01", "2021-12-01", "2022-03-01", "2022-12-01", "2022-11-01", "2023-04-01", "2023-11-01", "2023-06-01", "2023-11-01")),
      event_short = c("Arab Spring\n& Libya", "Iran\nsanctions", "Crimea\ncrisis", "EU ETS backloading\n& Phase III", "Oil price\ncollapse", "COP21 / Paris\nAgreement", "OPEC+\ncooperation", "Middle East\ntensions", "U.S. Paris exit\nannouncement", "Saudi\nattacks", "EUR\nGreen Deal", "U.S.-Iran\nconfrontation", "COVID-19\noil crash", "Fit for 55 /\nGlasgow Pact", "EUR gas\ncrisis", "Russia-\nUkraine war", "REPowerEU", "IRA", "OPEC+ cuts\n& Mideast", "MSR / EU ETS\nreform", "Israel-\nPalestine"), stringsAsFactors = FALSE)

    events$mid <- events$start + (events$end - events$start) / 2
    if (TARGET_SHOCK == "OPU") {
      events$event_short[events$event_id == "E20"] <- "OPEC+ cuts"
    }

    # 8) Event-label control functions
    get_events_for_type <- function(target_type) {
      events[grep(target_type, events$type),]
    }

    build_label_control <- function(events, target_types = c("GPR", "OPU", "CPU")) {
      out_list <- list()

      for (tt in target_types) {
        ev <- events[grep(tt, events$type),]

        if (nrow(ev) == 0) next

        for (ms in c("RI", "RD")) {
          n <- nrow(ev)

          # Default compact three-row positions: 0.34, 0.25, 0.16
          # Smaller y_pos values move labels downward
          default_y <- rep(c(0.34, 0.25, 0.16), length.out = n)

          tmp <- data.frame(target_type = tt, measure = ms, event_id = ev$event_id,
            event_short = ev$event_short, x_shift_months = 0, y_pos = default_y, srt = EVENT_SRT,
            cex = CEX_EVENT, adj_x = 0, adj_y = 0.5, col_text = "gray30", stringsAsFactors = FALSE)

          out_list[[length(out_list) + 1]] <- tmp
        }
      }

      do.call(rbind, out_list)
    }

    set_event_label_pos <- function(control, target_type, event_id, measure = c("both", "RI", "RD"),
      x_shift_months = NULL, y_pos = NULL, srt = NULL, cex = NULL,
      adj_x = NULL, adj_y = NULL, col_text = NULL, label = NULL) {
      measure <- match.arg(measure)

      idx <- control$target_type == target_type &
      control$event_id == event_id

      if (measure != "both") {
        idx <- idx & control$measure == measure
      }

      if (!any(idx)) {
        warning("No matching label-control row: ", target_type, " / ", event_id, " / ", measure)
        return(control)
      }

      if (!is.null(x_shift_months)) control$x_shift_months[idx] <- x_shift_months
      if (!is.null(y_pos)) control$y_pos[idx] <- y_pos
      if (!is.null(srt)) control$srt[idx] <- srt
      if (!is.null(cex)) control$cex[idx] <- cex
      if (!is.null(adj_x)) control$adj_x[idx] <- adj_x
      if (!is.null(adj_y)) control$adj_y[idx] <- adj_y
      if (!is.null(col_text)) control$col_text[idx] <- col_text
      if (!is.null(label)) control$event_short[idx] <- label

      control
    }

    # 9) Fine-tune event-label positions
    label_control <- build_label_control(events)

    # Display all adjustable event IDs for the current TARGET_SHOCK
    print(label_control[label_control$target_type == TARGET_SHOCK & label_control$measure == "RI",
      c("event_id", "event_short", "x_shift_months", "y_pos")])

    check_x_shift_range <- function(target_type) {
      ev <- get_events_for_type(target_type)

      out <- data.frame(event_id = ev$event_id, event_short = ev$event_short, mid = ev$mid,
        max_left_shift_months = round(as.numeric(min(x_date) - ev$mid) / 30.4375, 2),
        max_right_shift_months = round(as.numeric(max(x_date) - ev$mid) / 30.4375, 2),
        stringsAsFactors = FALSE)

      return(out)
    }

    check_x_shift_range(TARGET_SHOCK)
    # Apply the original label offsets for the selected shock.
    # Negative x_shift_months moves a label left; positive values move it right.
    # Larger y_pos values move a label upward within the event-label row.
    adjustments <- EVENT_LABEL_ADJUSTMENTS[[TARGET_SHOCK]]
    for (i in seq_len(nrow(adjustments))) {
      label_control <- set_event_label_pos(label_control, target_type = TARGET_SHOCK,
        event_id = adjustments$event_id[i], measure = adjustments$measure[i],
        x_shift_months = adjustments$x_shift_months[i], y_pos = adjustments$y_pos[i])
    }

    # 10) General helper functions
    make_axis_spec <- function(series_list, n_ticks = 6, digits = 2, step = NULL) {
      vals <- unlist(series_list)
      vals <- vals[is.finite(vals)]

      if (is.null(step)) {
        ticks <- pretty(range(vals, na.rm = TRUE), n = n_ticks)
      } else {
        lo <- floor(min(vals, na.rm = TRUE) / step) * step
        hi <- ceiling(max(vals, na.rm = TRUE) / step) * step
        ticks <- seq(lo, hi, by = step)
      }

      list(ylim = range(ticks), ticks = ticks,
        labels = formatC(ticks, format = "f", digits = digits))
    }

    add_event_shades <- function(target_type) {
      relevant_events <- get_events_for_type(target_type)

      if (nrow(relevant_events) == 0) {
        return(invisible(NULL))
      }

      usr <- par("usr")

      rect(xleft = relevant_events$start, xright = relevant_events$end, ybottom = usr[3],
        ytop = usr[4], col = SHADE_COL, border = NA)
    }

    plot_with_years_and_shades <- function(yy, x, main = "", col = "black", target_type = "GPR",
      show_x_axis = TRUE, line_width = 4, cex_x = 1.25, cex_y = 1.25, cex_main = 1.5,
      axis_spec = NULL) {
      yy <- as.numeric(yy)

      if (length(yy) != length(x)) {
        stop(paste0("x and y have different lengths: ", "length(x) = ", length(x),
          ", length(y) = ", length(yy)))
      }

      if (is.null(axis_spec)) {
        tmp_ticks <- pretty(range(yy, na.rm = TRUE), n = 6)
        axis_spec <- list(ylim = range(tmp_ticks), ticks = tmp_ticks,
          labels = formatC(tmp_ticks, format = "f", digits = 2))
      }

      plot(x = x, y = yy, type = "n", xlab = "", ylab = "", main = main, xaxt = "n", yaxt = "n",
        ylim = axis_spec$ylim, bty = "n", cex.main = cex_main, font.main = 2, col.main = TEXT_COL,
        family = FONT_FAMILY)

      abline(h = axis_spec$ticks, col = GRID_COL, lwd = GRID_LWD)

      add_event_shades(target_type)

      lines(x = x, y = yy, col = col, lwd = line_width, lend = "round", ljoin = "round")

      if (show_x_axis) {
        axis.Date(side = 1, at = year_ticks, labels = FALSE, col = AXIS_COL, col.axis = AXIS_COL,
          lwd = AXIS_LWD, lwd.ticks = AXIS_LWD)

        usr <- par("usr")
        y_span <- usr[4] - usr[3]

        text(x = year_ticks, y = usr[3] - 0.08 * y_span, labels = format(year_ticks, "%Y"), srt = 60,
          adj = c(1, 0.5), xpd = NA, cex = cex_x, col = AXIS_COL, family = FONT_FAMILY)
      }

      axis(side = 2, at = axis_spec$ticks, labels = axis_spec$labels, las = 1, cex.axis = cex_y,
        col = AXIS_COL, col.axis = AXIS_COL, lwd = AXIS_LWD, lwd.ticks = AXIS_LWD,
        family = FONT_FAMILY)

      box(col = AXIS_COL, lwd = BOX_LWD)
    }

    draw_event_label_panel <- function(target_type, measure = c("RI", "RD"), control) {
      measure <- match.arg(measure)

      relevant_events <- get_events_for_type(target_type)

      plot(x = x_date, y = rep(NA, length(x_date)), type = "n", xlim = range(x_date), ylim = c(0, 1),
        xlab = "", ylab = "", xaxt = "n", yaxt = "n", bty = "n", xaxs = "i", yaxs = "i")

      if (nrow(relevant_events) == 0) {
        return(invisible(NULL))
      }

      relevant_events$.ord <- seq_len(nrow(relevant_events))

      ctrl <- control[control$target_type == target_type &
        control$measure == measure,]

      dat <- merge(relevant_events, ctrl, by = "event_id", all.x = TRUE, sort = FALSE)

      dat <- dat[order(dat$.ord),]

      # Fill missing control values with defaults
      dat$x_shift_months[is.na(dat$x_shift_months)] <- 0
      dat$y_pos[is.na(dat$y_pos)] <- 0.25
      dat$srt[is.na(dat$srt)] <- EVENT_SRT
      dat$cex[is.na(dat$cex)] <- CEX_EVENT
      dat$adj_x[is.na(dat$adj_x)] <- 0
      dat$adj_y[is.na(dat$adj_y)] <- 0.5
      dat$col_text[is.na(dat$col_text)] <- "gray30"

      # The merge creates event_short.x and event_short.y
      # Use the control-table label in event_short.y, falling back to the original label
      if (!"event_short.y" %in% names(dat)) {
        dat$event_short.y <- dat$event_short
      }

      if (!"event_short.x" %in% names(dat)) {
        dat$event_short.x <- dat$event_short
      }

      dat$label_final <- dat$event_short.y
      dat$label_final[is.na(dat$label_final)] <- dat$event_short.x[is.na(dat$label_final)]

      # Convert x_shift_months from months to approximate days
      dat$x_label <- dat$mid + round(dat$x_shift_months * 30.4375)

      # Draw each event label separately:
      # text() requires a scalar srt value for each call
      for (i in seq_len(nrow(dat))) {
        text(x = dat$x_label[i], y = dat$y_pos[i], labels = dat$label_final[i],
          srt = dat$srt[i], cex = dat$cex[i], col = dat$col_text[i],
          adj = c(dat$adj_x[i], dat$adj_y[i]), xpd = NA, family = FONT_FAMILY)
      }
    }
    # 11) Construct common RI / RD y-axis ranges
    ri_series_list <- lapply(market_order, function(m) {
      get_market_data(m)$RP
    })

    rd_series_list <- lapply(market_order, function(m) {
      get_market_data(m)$RD
    })

    ri_axis <- make_axis_spec(series_list = ri_series_list, n_ticks = 6, digits = 2,
      step = RI_STEP)

    rd_axis <- make_axis_spec(series_list = rd_series_list, n_ticks = 6, digits = 2,
      step = RD_STEP)

    # 12) Output PDF: 6 x 2
    pdf(out_file, width = 12, height = 16, useDingbats = FALSE)

    showtext_begin()

    op <- par(no.readonly = TRUE)

    layout(mat = matrix(1:12, nrow = 6, ncol = 2, byrow = TRUE),
      heights = c(1, 1, 1, 1, 1, EVENT_PANEL_HEIGHT), widths = c(1, 1))

    par(oma = c(0.3, 2.0, 2.2, 0.3), family = FONT_FAMILY)

    # Rows 1-5: five markets
    # Use exactly the same mar settings for all market panels
    plot_resilience_measure <- function(market, yy, col, axis_spec) {
      par(mar = c(4.2, 4.0, 2.0, 1.0))
      plot_with_years_and_shades(yy = yy, x = x_date, main = market, col = col,
        target_type = TARGET_SHOCK, show_x_axis = TRUE,
        line_width = LINE_WIDTH, cex_x = CEX_X, cex_y = CEX_Y,
        cex_main = CEX_MAIN, axis_spec = axis_spec)
    }

    for (m in market_order) {
      dat <- get_market_data(m)
      plot_resilience_measure(m, dat$RP, col_ri, ri_axis)
      plot_resilience_measure(m, dat$RD, col_rd, rd_axis)
    }

    # Row 6: compact labels only
    # Draw labels without shading, reference lines, or axes
    par(mar = c(0.02, 4.0, 0.02, 1.0))
    draw_event_label_panel(target_type = TARGET_SHOCK, measure = "RI", control = label_control)

    par(mar = c(0.02, 4.0, 0.02, 1.0))
    draw_event_label_panel(target_type = TARGET_SHOCK, measure = "RD", control = label_control)

    # Column headers
    draw_column_header <- function(label, position) {
      mtext(label, side = 3, outer = TRUE, line = 0.6, at = position,
        cex = CEX_HEADER, font = 2, col = TEXT_COL, family = FONT_FAMILY)
    }
    draw_column_header("Resilience Intensity", 0.25)
    draw_column_header("Resilience Duration", 0.75)

    par(op)

    showtext_end()
    dev.off()

    cat("Saved to:", out_file, "\n")

    invisible(out_file)
  }

  # Generate each selected shock figure using the same plotting function
  vertical_output_files <- setNames(character(length(TARGET_SHOCKS)), TARGET_SHOCKS)

  for (shock in TARGET_SHOCKS) {
    vertical_output_files[[shock]] <- plot_vertical_resilience(target_shock = shock, r_data = r_data,
      x_date = x_date, target_dir = RESILIENCE_OUTPUT_DIR)
  }
} # Vertical GPR, CPU, and OPU resilience plots used in the final manuscript

{
  # Block 3. Resilience comparison across H
  # Five market rows: RI on the left, RD on the right; compact bottom legend.
  # Compare H = 6, 8, and 10 without event shading or labels.

  # 1) Font setting
  FONT_FAMILY <- "sans"

  font_regular <- "/System/Library/Fonts/Supplemental/Times New Roman.ttf"
  font_bold <- "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf"
  font_italic <- "/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf"
  font_bolditalic <- "/System/Library/Fonts/Supplemental/Times New Roman Bold Italic.ttf"

  font_files <- c(font_regular, font_bold, font_italic, font_bolditalic)

  if (all(file.exists(font_files))) {
    font_add(family = "Times New Roman", regular = font_regular, bold = font_bold,
      italic = font_italic, bolditalic = font_bolditalic)
    FONT_FAMILY <- "Times New Roman"
  }

  # 2) Basic settings
  TARGET_SHOCK <- "GPR" # Used only to name the output file

  # Find the package root, including when R starts in a code subdirectory.
  PROJECT_DIR <- (function() {
    start_dirs <- c(if (exists("PROJECT_DIR", inherits = TRUE)) PROJECT_DIR, getwd())
    for (start_dir in unique(start_dirs)) {
      if (!dir.exists(start_dir)) next
      root <- normalizePath(start_dir, winslash = "/", mustWork = TRUE)
      repeat {
        if (all(dir.exists(file.path(root,
          c("Energy Economics Code", "Energy Economics Data"))))) return(root)
        parent <- dirname(root)
        if (identical(parent, root)) break
        root <- parent
      }
    }
    stop("Project root not found. Set PROJECT_DIR to the folder containing ",
      "Energy Economics Code and Energy Economics Data.")
  })()
  # Read the full TVP-VAR calendar and omit its initial, unestimated period.
  VAR_DATA_FILE <- file.path(PROJECT_DIR, "Energy Economics Data", "VAR_100data.xlsx")
  sample_dates <- as.Date(read_xlsx(VAR_DATA_FILE, sheet = "VAR_100data")$date)
  if (length(sample_dates) != 167L || anyNA(sample_dates)) {
    stop("VAR_100data.xlsx must contain 167 valid dates in its date column.")
  }
  x_date <- sample_dates[2:167] # February 2010-November 2023: 166 observations.

  year_ticks <- seq(from = as.Date(paste0(format(min(x_date), "%Y"), "-01-01")),
    to = as.Date(paste0(format(max(x_date), "%Y"), "-01-01")), by = "1 year")

  # 3) Output file
  target_dir <- file.path(PROJECT_DIR, "Fig")

  dir.create(target_dir, recursive = TRUE, showWarnings = FALSE)

  out_file <- file.path(target_dir,
    paste0(tolower(TARGET_SHOCK), "_resilience_H_comparison_academic_no_shades.pdf"))

  # 4) Read resilience data for different H
  HORIZON_DATA_DIR <- file.path(PROJECT_DIR, "Energy Economics Data", "horizon_resilience")
  r_data_6 <- read_xlsx(file.path(HORIZON_DATA_DIR, "resilience_metrics_median6.xlsx"))
  r_data_8 <- read_xlsx(file.path(HORIZON_DATA_DIR, "resilience_metrics_median.xlsx"))
  r_data_10 <- read_xlsx(file.path(HORIZON_DATA_DIR, "resilience_metrics_median10.xlsx"))

  H_DATA <- list("H = 6" = r_data_6, "H = 8" = r_data_8, "H = 10" = r_data_10)

  # 5) Style controls
  H_COLS <- c("H = 6" = "#2166AC", "H = 8" = "#B2182B", "H = 10" = "gray25")

  H_LTYS <- c("H = 6" = 1, "H = 8" = 1, "H = 10" = 1)

  GRID_COL <- adjustcolor("gray70", alpha.f = 0.28)
  AXIS_COL <- "gray25"
  TEXT_COL <- "gray10"

  # Match the style of the main resilience figures
  LINE_WIDTH <- 4.4
  CEX_X <- 2.00
  CEX_Y <- 2.25
  CEX_MAIN <- 2.25
  CEX_HEADER <- 1.30
  CEX_LEGEND <- 2.25

  GRID_LWD <- 0.6
  AXIS_LWD <- 0.8
  BOX_LWD <- 0.8

  # RI y-axis tick interval
  RI_STEP <- 0.10

  # Choose RD y-axis ticks automatically
  RD_STEP <- NULL

  # 6) Market mapping
  market_var_map <- c("OIL" = "Var6", "NG" = "Var7", "COAL" = "Var8", "ERIX" = "Var9",
    "EUA" = "Var10")

  market_order <- c("OIL", "NG", "COAL", "ERIX", "EUA")

  # 7) Helper functions
  get_h_series <- function(h_name, market, measure = c("RI", "RD")) {
    measure <- match.arg(measure)

    dat <- H_DATA[[h_name]]
    var_code <- unname(market_var_map[market])

    idx <- dat$Variable == var_code

    if (sum(idx) == 0) {
      stop("No rows found for ", h_name, " / ", market, " / ", var_code)
    }

    col_id <- if (measure == "RI") 3 else 4

    yy <- as.numeric(dat[idx, col_id][[1]])

    if (length(yy) != length(x_date)) {
      stop(paste0(h_name, " / ", market, " / ", measure,
        " has a different number of observations from x_date: ", "length(y) = ", length(yy),
        ", length(x_date) = ", length(x_date)))
    }

    yy
  }

  get_panel_series <- function(market, measure = c("RI", "RD")) {
    measure <- match.arg(measure)

    out <- lapply(names(H_DATA), function(h) {
      get_h_series(h, market, measure)
    })

    names(out) <- names(H_DATA)
    out
  }

  make_axis_spec <- function(series_list, n_ticks = 6, digits = 2, step = NULL) {
    vals <- unlist(series_list)
    vals <- vals[is.finite(vals)]

    if (is.null(step)) {
      ticks <- pretty(range(vals, na.rm = TRUE), n = n_ticks)
    } else {
      lo <- floor(min(vals, na.rm = TRUE) / step) * step
      hi <- ceiling(max(vals, na.rm = TRUE) / step) * step
      ticks <- seq(lo, hi, by = step)
    }

    list(ylim = range(ticks), ticks = ticks,
      labels = formatC(ticks, format = "f", digits = digits))
  }

  draw_year_axis_60 <- function(cex_x = 2.00) {
    axis.Date(side = 1, at = year_ticks, labels = FALSE, col = AXIS_COL, col.axis = AXIS_COL,
      lwd = AXIS_LWD, lwd.ticks = AXIS_LWD)

    usr <- par("usr")
    y_span <- usr[4] - usr[3]

    text(x = year_ticks, y = usr[3] - 0.08 * y_span, labels = format(year_ticks, "%Y"), srt = 60,
      adj = c(1, 0.5), xpd = NA, cex = cex_x, col = AXIS_COL, family = FONT_FAMILY)
  }

  plot_h_comparison_panel <- function(series_list, main = "", axis_spec, show_x_axis = TRUE) {
    plot(x = x_date, y = series_list[[1]], type = "n", xlab = "", ylab = "", main = main, xaxt = "n",
      yaxt = "n", ylim = axis_spec$ylim, bty = "n", cex.main = CEX_MAIN, font.main = 2,
      col.main = TEXT_COL, family = FONT_FAMILY)

    abline(h = axis_spec$ticks, col = GRID_COL, lwd = GRID_LWD)

    for (h in names(series_list)) {
      lines(x = x_date, y = series_list[[h]], col = H_COLS[h], lty = H_LTYS[h], lwd = LINE_WIDTH,
        lend = "round", ljoin = "round")
    }

    if (show_x_axis) {
      draw_year_axis_60(cex_x = CEX_X)
    }

    axis(side = 2, at = axis_spec$ticks, labels = axis_spec$labels, las = 1, cex.axis = CEX_Y,
      col = AXIS_COL, col.axis = AXIS_COL, lwd = AXIS_LWD, lwd.ticks = AXIS_LWD, family = FONT_FAMILY
    )

    box(col = AXIS_COL, lwd = BOX_LWD)
  }

  # 8) Construct common RI / RD y-axis ranges
  all_ri_series <- list()
  all_rd_series <- list()

  for (m in market_order) {
    all_ri_series <- c(all_ri_series, get_panel_series(m, "RI"))
    all_rd_series <- c(all_rd_series, get_panel_series(m, "RD"))
  }

  ri_axis <- make_axis_spec(series_list = all_ri_series, n_ticks = 6, digits = 2, step = RI_STEP)

  rd_axis <- make_axis_spec(series_list = all_rd_series, n_ticks = 6, digits = 2, step = RD_STEP)

  # 9) Output PDF
  pdf(out_file, width = 12, height = 16, useDingbats = FALSE)

  showtext_begin()

  op <- par(no.readonly = TRUE)

  layout_matrix <- matrix(c(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 11), nrow = 6, byrow = TRUE)

  layout(mat = layout_matrix, heights = c(1, 1, 1, 1, 1, 0.22), widths = c(1, 1))

  par(oma = c(0.4, 2.0, 2.2, 0.3), family = FONT_FAMILY)

  # Rows 1-5: market panels
  plot_h_measure <- function(market, measure, axis_spec) {
    par(mar = c(4.2, 4.0, 2.0, 1.0))
    plot_h_comparison_panel(series_list = get_panel_series(market, measure), main = market,
      axis_spec = axis_spec, show_x_axis = TRUE)
  }

  for (m in market_order) {
    plot_h_measure(m, "RI", ri_axis)
    plot_h_measure(m, "RD", rd_axis)
  }

  # Bottom legend
  par(mar = c(0, 0, 0, 0))
  plot.new()

  legend("center", horiz = TRUE, bty = "n", lwd = LINE_WIDTH, lty = H_LTYS, col = H_COLS,
    legend = names(H_DATA), cex = CEX_LEGEND, seg.len = 3.2, x.intersp = 1.1, text.col = TEXT_COL)

  # Column headers
  draw_column_header <- function(label, position) {
    mtext(label, side = 3, outer = TRUE, line = 0.6, at = position,
      cex = CEX_HEADER, font = 2, col = TEXT_COL, family = FONT_FAMILY)
  }
  draw_column_header("Resilience Intensity", 0.25)
  draw_column_header("Resilience Duration", 0.75)

  par(op)

  showtext_end()
  dev.off()

  cat("Saved to:", out_file, "\n")
} # Vertical resilience comparison across H used in the final manuscript

{
  # Block 4. Markov smoothed probability
  # Python exports; five market rows plus a bottom legend.
  # Left axis: smoothed probability; right axis: RI or RD.

  # 1) Font setting
  FONT_FAMILY <- "sans"

  font_regular <- "/System/Library/Fonts/Supplemental/Times New Roman.ttf"
  font_bold <- "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf"
  font_italic <- "/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf"
  font_bolditalic <- "/System/Library/Fonts/Supplemental/Times New Roman Bold Italic.ttf"

  font_files <- c(font_regular, font_bold, font_italic, font_bolditalic)

  if (all(file.exists(font_files))) {
    font_add(family = "Times New Roman", regular = font_regular, bold = font_bold,
      italic = font_italic, bolditalic = font_bolditalic)
    FONT_FAMILY <- "Times New Roman"
  }

  # 2) Basic settings
  SHOCK_LABEL <- "OPU" # Choose "GPR", "CPU", or "OPU"
  STATE_TO_PLOT <- 1 # 1 or 2

  # Find the package root, including when R starts in a code subdirectory.
  PROJECT_DIR <- (function() {
    start_dirs <- c(if (exists("PROJECT_DIR", inherits = TRUE)) PROJECT_DIR, getwd())
    for (start_dir in unique(start_dirs)) {
      if (!dir.exists(start_dir)) next
      root <- normalizePath(start_dir, winslash = "/", mustWork = TRUE)
      repeat {
        if (all(dir.exists(file.path(root,
          c("Energy Economics Code", "Energy Economics Data"))))) return(root)
        parent <- dirname(root)
        if (identical(parent, root)) break
        root <- parent
      }
    }
    stop("Project root not found. Set PROJECT_DIR to the folder containing ",
      "Energy Economics Code and Energy Economics Data.")
  })()
  PYTHON_OUTPUT_DIR <- file.path(PROJECT_DIR, "Energy Economics Code", "python code", "output")
  input_xlsx <- file.path(PYTHON_OUTPUT_DIR, paste0(tolower(SHOCK_LABEL),
    "_ms_state_probabilities_state", STATE_TO_PLOT, ".xlsx"))
  target_dir <- file.path(PROJECT_DIR, "Fig")

  dir.create(target_dir, recursive = TRUE, showWarnings = FALSE)

  out_file <- file.path(target_dir, paste0(tolower(SHOCK_LABEL),
    "_ms_smoothed_probability_5x2_state", STATE_TO_PLOT, "_prob_left_metric_right.pdf"))

  prob_data <- read_xlsx(input_xlsx, sheet = "probabilities_long")

  state_mapping <- read_xlsx(input_xlsx, sheet = "state_mapping")

  prob_data$date <- as.Date(prob_data$date)

  market_order <- c("OIL", "NG", "COAL", "ERIX", "EUA")

  # 3) Style controls
  col_ri <- "#2166AC"
  col_rd <- "#B2182B"

  PROB_SHADE_COL <- adjustcolor("gray45", alpha.f = 0.16)
  PROB_LINE_COL <- adjustcolor("black", alpha.f = 0.70)
  PROB_REF_COL <- adjustcolor("gray40", alpha.f = 0.60)

  GRID_COL <- adjustcolor("gray70", alpha.f = 0.28)
  AXIS_COL <- "gray25"
  TEXT_COL <- "gray10"

  # Match the current figure style
  LINE_WIDTH <- 3.2
  PROB_LINE_WIDTH <- 2.5

  CEX_X <- 2.00
  CEX_Y <- 2.00 # Right-hand resilience-axis label size
  CEX_PY <- 2.25 # Left-hand probability-axis label size
  CEX_MAIN <- 2.25
  CEX_HEADER <- 1.30
  CEX_LEGEND <- 2.25

  GRID_LWD <- 0.6
  AXIS_LWD <- 0.8
  BOX_LWD <- 0.8

  RI_STEP <- 0.10
  RD_STEP <- NULL

  # 4) Axis helper functions
  make_axis_spec <- function(vals, n_ticks = 6, digits = 2, step = NULL) {
    vals <- vals[is.finite(vals)]

    if (is.null(step)) {
      ticks <- pretty(range(vals, na.rm = TRUE), n = n_ticks)
    } else {
      lo <- floor(min(vals, na.rm = TRUE) / step) * step
      hi <- ceiling(max(vals, na.rm = TRUE) / step) * step
      ticks <- seq(lo, hi, by = step)
    }

    list(ylim = range(ticks), ticks = ticks,
      labels = formatC(ticks, format = "f", digits = digits))
  }

  ri_axis <- make_axis_spec(vals = prob_data$metric_value[prob_data$measure == "RI"], n_ticks = 6,
    digits = 2, step = RI_STEP)

  rd_axis <- make_axis_spec(vals = prob_data$metric_value[prob_data$measure == "RD"], n_ticks = 6,
    digits = 2, step = RD_STEP)

  x_date <- sort(unique(prob_data$date))

  year_ticks <- seq(from = as.Date(paste0(format(min(x_date), "%Y"), "-01-01")),
    to = as.Date(paste0(format(max(x_date), "%Y"), "-01-01")), by = "1 year")

  draw_year_axis_60 <- function(cex_x = 2.00) {
    axis.Date(side = 1, at = year_ticks, labels = FALSE, col = AXIS_COL, col.axis = AXIS_COL,
      lwd = AXIS_LWD, lwd.ticks = AXIS_LWD)

    usr <- par("usr")
    y_span <- usr[4] - usr[3]

    text(x = year_ticks, y = usr[3] - 0.08 * y_span, labels = format(year_ticks, "%Y"), srt = 60,
      adj = c(1, 0.5), xpd = NA, cex = cex_x, col = AXIS_COL, family = FONT_FAMILY)
  }

  # 5) Panel plotting function
  # Left y-axis  = smoothed probability
  # Right y-axis = resilience metric
  plot_ms_probability_panel <- function(dat, measure = c("RI", "RD"), main = "", axis_spec,
    metric_col, show_x_axis = TRUE) {
    measure <- match.arg(measure)

    dat <- dat[order(dat$date),]
    dat <- dat[is.finite(dat$metric_value) & is.finite(dat$prob_selected),]

    metric_min <- axis_spec$ylim[1]
    metric_max <- axis_spec$ylim[2]

    metric_to_prob <- function(v) {
      (v - metric_min) / (metric_max - metric_min)
    }

    y_metric_scaled <- metric_to_prob(dat$metric_value)
    y_metric_ticks_scaled <- metric_to_prob(axis_spec$ticks)

    plot(x = dat$date, y = dat$prob_selected, type = "n", xlab = "", ylab = "", main = main,
      xlim = range(x_date), ylim = c(0, 1), xaxt = "n", yaxt = "n", bty = "n", cex.main = CEX_MAIN,
      font.main = 2, col.main = TEXT_COL, family = FONT_FAMILY)

    # probability grid
    abline(h = c(0, 0.5, 1), col = GRID_COL, lwd = GRID_LWD)

    # probability shade
    polygon(x = c(dat$date, rev(dat$date)), y = c(rep(0, nrow(dat)), rev(dat$prob_selected)),
      col = PROB_SHADE_COL, border = NA)

    # 0.5 probability reference line
    abline(h = 0.5, col = PROB_REF_COL, lwd = 0.8, lty = 3)

    # probability dashed line
    lines(x = dat$date, y = dat$prob_selected, col = PROB_LINE_COL, lwd = PROB_LINE_WIDTH, lty = 2
    )

    # resilience metric line, mapped onto probability coordinate system
    lines(x = dat$date, y = y_metric_scaled, col = metric_col, lwd = LINE_WIDTH, lend = "round",
      ljoin = "round")

    if (show_x_axis) {
      draw_year_axis_60(cex_x = CEX_X)
    }

    # left axis: smoothed probability
    axis(side = 2, at = c(0, 0.5, 1), labels = c("0.0", "0.5", "1.0"), las = 1, cex.axis = CEX_PY,
      col = AXIS_COL, col.axis = "gray35", lwd = AXIS_LWD, lwd.ticks = AXIS_LWD, family = FONT_FAMILY
    )

    # right axis: resilience metric
    axis(side = 4, at = y_metric_ticks_scaled, labels = axis_spec$labels, las = 1, cex.axis = CEX_Y,
      col = AXIS_COL, col.axis = AXIS_COL, lwd = AXIS_LWD, lwd.ticks = AXIS_LWD, family = FONT_FAMILY
    )

    box(col = AXIS_COL, lwd = BOX_LWD)
  }

  # 6) Output PDF
  pdf(out_file, width = 12, height = 16, useDingbats = FALSE)

  showtext_begin()

  op <- par(no.readonly = TRUE)

  layout_matrix <- matrix(c(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 11), nrow = 6, byrow = TRUE)

  layout(mat = layout_matrix, heights = c(1, 1, 1, 1, 1, 0.22), widths = c(1, 1))

  par(oma = c(0.4, 2.0, 2.2, 0.3), family = FONT_FAMILY)

  # Rows 1-5: market panels
  plot_ms_measure <- function(market, dat, measure, axis_spec, metric_col) {
    par(mar = c(4.2, 3.8, 2.0, 4.2))
    plot_ms_probability_panel(dat = dat, measure = measure, main = market,
      axis_spec = axis_spec, metric_col = metric_col, show_x_axis = TRUE)
  }

  for (m in market_order) {
    dat_ri <- prob_data[prob_data$market == m & prob_data$measure == "RI",]
    dat_rd <- prob_data[prob_data$market == m & prob_data$measure == "RD",]
    plot_ms_measure(m, dat_ri, "RI", ri_axis, col_ri)
    plot_ms_measure(m, dat_rd, "RD", rd_axis, col_rd)
  }

  # Bottom legend
  par(mar = c(0, 0, 0, 0))
  plot.new()

  legend("center", horiz = TRUE, bty = "n", lwd = c(3.0, 3.0, PROB_LINE_WIDTH), lty = c(1, 1, 2),
    col = c(col_ri, col_rd, PROB_LINE_COL), legend = c("Resilience Intensity", "Resilience Duration",
    "State 1 Strong Resilience"
    ), cex = CEX_LEGEND, seg.len = 1.8, x.intersp = 0.55, y.intersp = 0.75, text.col = TEXT_COL)

  # Column headers
  draw_column_header <- function(label, position) {
    mtext(label, side = 3, outer = TRUE, line = 0.6, at = position,
      cex = CEX_HEADER, font = 2, col = TEXT_COL, family = FONT_FAMILY)
  }
  draw_column_header("Resilience Intensity", 0.25)
  draw_column_header("Resilience Duration", 0.75)

  par(op)

  showtext_end()
  dev.off()

  cat("Saved to:", out_file, "\n")
} # Plot Markov smoothed probabilities from the Python export
