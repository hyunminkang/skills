# Checks for function-factories.yaml: every snippet run as printed, every
# number in a stem, key or explanation recomputed. Each item runs in its own
# local() so no state leaks between items. Run with
#   Rscript function-factories.checks.R          (from this folder)
# It stops at the first failed check; on success it prints "all checks passed"
# and redraws figures/loglik.png.

check <- function(id, ok) {
  if (!isTRUE(ok)) stop("check failed: ", id, call. = FALSE)
  cat("ok", id, "\n")
}
cat(R.version.string, "\n")

# ---- ff-001: two closures from one factory ----------------------------------
local({
  power <- function(exp) {
    function(x) x^exp
  }
  square <- power(2)
  cube <- power(3)
  check("ff-001", identical(c(square(4), cube(2)), c(16, 8)))
})

# ---- ff-002: lazy evaluation of the factory argument ------------------------
local({
  power <- function(exp) {
    function(x) x^exp
  }
  e <- 2
  square <- power(e)
  e <- 3
  check("ff-002", square(2) == 8)
})

# ---- ff-003: closures made in a for loop share the loop variable ------------
local({
  adders <- list()
  for (i in 1:3) {
    adders[[i]] <- function(x) x + i
  }
  check("ff-003", adders[[1]](10) == 13)
  rm(i)
  check("ff-003 explanation: after rm(i) the call fails",
        inherits(try(adders[[1]](10), silent = TRUE), "try-error"))
})

# ---- ff-004: independent counters -------------------------------------------
local({
  new_counter <- function() {
    i <- 0
    function() {
      i <<- i + 1
      i
    }
  }
  a <- new_counter()
  b <- new_counter()
  check("ff-004", identical(c(a(), a(), b(), a()), c(1, 2, 1, 3)))
})

# ---- ff-005: <- instead of <<- ----------------------------------------------
local({
  new_counter <- function() {
    i <- 0
    function() {
      i <- i + 1
      i
    }
  }
  a <- new_counter()
  check("ff-005", identical(c(a(), a(), a()), c(1, 1, 1)))
})

# ---- ff-006: Box-Cox values at x = 4 -----------------------------------------
local({
  bc <- function(x, lambda) if (lambda == 0) log(x) else (x^lambda - 1) / lambda
  check("ff-006 lambda = 1", bc(4, 1) == 3)
  check("ff-006 lambda = 0.5 is 2, so the table's 1 is wrong", bc(4, 0.5) == 2)
  check("ff-006 lambda = 0", bc(4, 0) == log(4))
  check("ff-006 lambda = -1", isTRUE(all.equal(bc(4, -1), 0.75)))
  check("ff-006 lambda = 2", bc(4, 2) == 7.5)
})

# ---- ff-007: the formula at lambda = 0 ---------------------------------------
local({
  boxcox <- function(lambda) {
    function(x) (x^lambda - 1) / lambda
  }
  check("ff-007", is.nan(boxcox(0)(5)))
  check("ff-007 explanation: the limit is log(5) = 1.609",
        abs(boxcox(1e-8)(5) - log(5)) < 1e-6 && round(log(5), 3) == 1.609)
})

# ---- ff-009: what a closure keeps alive --------------------------------------
local({
  f1 <- function(n) {
    x <- runif(n)
    m <- mean(x)
    function() m
  }
  f2 <- function(n) {
    x <- runif(n)
    m <- mean(x)
    rm(x)
    function() m
  }
  g1 <- f1(1e6)
  g2 <- f2(1e6)
  check("ff-009 g1 keeps x", length(environment(g1)$x) == 1e6)
  check("ff-009 g2 does not",
        !exists("x", envir = environment(g2), inherits = FALSE))
  check("ff-009 explanation: about 8 MB",
        round(as.numeric(object.size(environment(g1)$x)) / 1e6) == 8)
})

# ---- ff-010: Poisson MLE ------------------------------------------------------
local({
  x <- c(2, 4, 3, 7)
  ll <- function(lambda) log(lambda) * sum(x) - length(x) * lambda - sum(lfactorial(x))
  opt <- optimize(ll, c(0.01, 50), maximum = TRUE)
  check("ff-010", abs(opt$maximum - 4) < 1e-4 && mean(x) == 4)
})

# ---- ff-011: dropping the constant term ---------------------------------------
local({
  x <- c(5, 1, 6, 2)
  ll_full <- function(lambda) log(lambda) * sum(x) - length(x) * lambda - sum(lfactorial(x))
  ll_drop <- function(lambda) log(lambda) * sum(x) - length(x) * lambda
  ll_bad <- function(lambda) log(lambda) * sum(x) - sum(lfactorial(x))
  m1 <- optimize(ll_full, c(0.01, 50), maximum = TRUE)$maximum
  m2 <- optimize(ll_drop, c(0.01, 50), maximum = TRUE)$maximum
  m3 <- optimize(ll_bad, c(0.01, 50), maximum = TRUE)$maximum
  check("ff-011 same maximizer without sum(log(x!))", abs(m1 - m2) < 1e-4)
  check("ff-011 dropping n*lambda moves it to the upper bound", m3 > 49)
})

# ---- ff-012: precomputing in the factory --------------------------------------
local({
  ll1 <- function(x) {
    function(lambda) {
      log(lambda) * sum(x) - length(x) * lambda - sum(lfactorial(x))
    }
  }
  ll2 <- function(x) {
    s <- sum(x)
    n <- length(x)
    lf <- sum(lfactorial(x))
    function(lambda) log(lambda) * s - n * lambda - lf
  }
  x <- rpois(1e5, 30)
  check("ff-012 same function", isTRUE(all.equal(ll1(x)(25), ll2(x)(25))))
  calls <- 0
  traced <- function(f) function(lambda) { calls <<- calls + 1; f(lambda) }
  invisible(optimize(traced(ll2(x)), c(1, 100), maximum = TRUE))
  check("ff-012 optimize() makes k > 1 calls", calls > 5)
})

# ---- ff-013: which generators can change between calls -------------------------
local({
  fa <- function() { i <- 0; function() { i <<- i + 1; i } }
  fb <- function(x) { force(x); function() mean(sample(x, replace = TRUE)) }
  fc <- function(x) { m <- mean(x); function() m }
  fd <- function(x) function() max(x)
  set.seed(1)
  ga <- fa(); gb <- fb(1:10); gc <- fc(1:10); gd <- fd(1:10)
  check("ff-013 A changes", ga() != ga())
  check("ff-013 B can change", length(unique(replicate(20, gb()))) > 1)
  check("ff-013 C fixed", length(unique(replicate(20, gc()))) == 1)
  check("ff-013 D fixed", length(unique(replicate(20, gd()))) == 1)
})

# ---- ff-014: possible bootstrap means --------------------------------------------
local({
  boot_mean <- function(x) {
    force(x)
    function() mean(sample(x, length(x), replace = TRUE))
  }
  b <- boot_mean(c(1, 2, 3))
  draws <- expand.grid(1:3, 1:3, 1:3)
  possible <- sort(unique(round(rowMeans(draws), 6)))
  check("ff-014 2.5 impossible; 1, 2, 3 possible",
        !(2.5 %in% possible) && all(c(1, 2, 3) %in% possible))
  set.seed(2)
  check("ff-014 b() returns one of them", all(round(replicate(200, b()), 6) %in% possible))
})

# ---- ff-015: lm() runs once ---------------------------------------------------------
local({
  boot_resid <- function(df, formula) {
    fit <- lm(formula, data = df)
    fitted <- unname(fitted(fit))
    resid <- unname(resid(fit))
    function() fitted + sample(resid)
  }
  n_lm <<- 0   # global: trace() evaluates the counter inside lm()
  trace(lm, quote(n_lm <<- n_lm + 1), print = FALSE, where = globalenv())
  gen <- boot_resid(mtcars, mpg ~ wt)
  sims <- replicate(1000, gen())
  untrace(lm, where = globalenv())
  check("ff-015", n_lm == 1 && identical(dim(sims), c(32L, 1000L)))
})

# ---- ff-016: the figure: Poisson log-likelihood peaks at the mean ------------------
local({
  x <- c(28, 35, 31, 40, 26, 33, 30, 29, 36, 32)
  ll <- function(lambda) log(lambda) * sum(x) - length(x) * lambda - sum(lfactorial(x))
  peak <- optimize(ll, c(20, 45), maximum = TRUE)$maximum
  check("ff-016 peak at the mean 32", abs(peak - 32) < 1e-4 && mean(x) == 32)
  check("ff-016 distractors are false",
        median(x) == 31.5 && max(x) == 40 && sum(x) == 320)
  if (dir.exists("figures")) {
    png("figures/loglik.png", width = 640, height = 400, res = 110)
    par(mar = c(4.2, 4.6, 1, 1))
    lam <- seq(20, 45, by = 0.05)
    plot(lam, sapply(lam, ll), type = "l", lwd = 2, xaxt = "n",
         xlab = expression(lambda), ylab = "log-likelihood")
    axis(1, at = c(20, 26, 32, 38, 44))
    abline(v = peak, lty = 2)
    dev.off()
    cat("redrew figures/loglik.png\n")
  }
})

# ---- ff-017: a closure reads its factory's argument later ---------------------------
local({
  make_greeting <- function(name) {
    force(name)
    function() paste("hello", name)
  }
  hi <- make_greeting("Ada")
  check("ff-017", hi() == "hello Ada")
})

# ---- ff-018: ecdf() returns a function -------------------------------------------------
local({
  Fn <- ecdf(c(3, 1, 4, 1, 5))
  check("ff-018", is.function(Fn) && Fn(2) == 0.4)
})

# ---- ff-019: a named list of closures ----------------------------------------------------
local({
  power <- function(exp) {
    force(exp)
    function(x) x^exp
  }
  funs <- lapply(c(square = 2, cube = 3, root = 0.5), power)
  check("ff-019", funs$root(64) + funs$cube(2) == 16 &&
          identical(names(funs), c("square", "cube", "root")))
})

cat("all checks passed\n")
