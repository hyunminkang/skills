# Checks for smoke-test.yaml; run with Rscript smoke-test.checks.R (from this folder).
check <- function(id, ok) { if (!isTRUE(ok)) stop("check failed: ", id, call. = FALSE); cat("ok", id, "\n") }
cat(R.version.string, "\n")

# ---- st-001 ----
local({
  x <- c(2, 4, 9)
  check("st-001 mean", mean(x) == 5)
  check("st-001 var", var(x) == 13)
})
# ---- st-002 ----
local({
  x <- c(2, 4, 9)
  check("st-002 sd scales by |a|", isTRUE(all.equal(sd(3 * x + 1), 3 * sd(x))))
  check("st-002 var scales by a^2", isTRUE(all.equal(var(-2 * x), 4 * var(x))))
  check("st-002 mean shifts", mean(x + 10) == mean(x) + 10)
  check("st-002 sd does not shift", sd(x + 10) == sd(x))
})
# ---- st-003 ----
local({
  check("st-003", isTRUE(all.equal(sqrt(13 / 3), 2.081666, tolerance = 1e-6)))
})
# ---- st-004 ----
local({
  check("st-004 P(Z <= 1.96)", round(pnorm(1.96), 3) == 0.975)
})
# ---- st-005 ----
local({
  check("st-005 0.1 + 0.2 == 0.3 is FALSE in doubles", !(0.1 + 0.2 == 0.3))
  check("st-005 gap is about 5.6e-17", round((0.1 + 0.2) - 0.3, 18) == 5.6e-17 ||
          abs((0.1 + 0.2) - 0.3 - 5.55e-17) < 1e-18)
})
# ---- st-006: figure ----
local({
  set.seed(615)
  draws <- rexp(1000, rate = 1)
  check("st-006 right skew: mean > median", mean(draws) > median(draws))
  if (dir.exists("figures")) {
    png("figures/histogram.png", width = 640, height = 400, res = 110)
    par(mar = c(4.2, 4.2, 1, 1))
    hist(draws, breaks = 30, col = "grey80", border = "white", main = "", xlab = "value")
    dev.off()
    cat("redrew figures/histogram.png\n")
  }
})
cat("all checks passed\n")
