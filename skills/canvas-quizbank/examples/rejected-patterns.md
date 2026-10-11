# Rejected patterns, with fixes

Each pair shows an item an instructor rejected in review and the version
that replaced it. All are on the Advanced R function-factories material, so
they can be compared with `advanced-r-function-factories/`.

## 1. Trivia instead of the idea

Rejected: it tests where a helper lives, not what a closure does.

```yaml
question: |
  Which package provides `env_print()`, used to inspect a function's
  enclosing environment?
choices: ['rlang', 'base', 'pryr', 'lobstr']
```

Fixed: ask what the idea predicts for concrete code (see ff-001).

~~~yaml
question: |
  ```r
  power <- function(exp) {
    function(x) x^exp
  }
  square <- power(2)
  cube <- power(3)
  c(square(4), cube(2))
  ```

  What does the last line print?
choices: ['`64 8`', '`16 8`', '`16 16`', '`Error: object ''exp'' not found`']
~~~

## 2. Names that only the lecture uses

Rejected: "the promise trap" and "the slide-12 factory" mean nothing to
someone who learned the topic elsewhere.

```yaml
question: |
  Why does the slide-12 factory fall into the promise trap?
```

Fixed: show the code and ask what it prints (see ff-002). Use standard
terms such as "lazy evaluation", and define any symbol in the stem.

## 3. Arithmetic instead of understanding

Rejected: computing ℓ(3) to three decimals takes a calculator and tests
arithmetic, not likelihood.

```yaml
question: |
  For x = (2, 4, 3, 7) and a Poisson model, compute ℓ(3) to three decimals.
type: numerical
```

Fixed: ask for the maximizer, one or two mental steps once the idea is known
(see ff-010: $\hat\lambda = \bar{x} = 16/4$).

## 4. Options that give the key away

Rejected: only the key carries a justification, and it is by far the
longest option.

```yaml
choices:
  - '`8`, because the promise is evaluated when `square()` is first called and `e` is 3 by then'
  - '`4`'
  - '`9`'
  - 'an error'
```

Fixed: options are values of the same form, and the reasoning moves to
`explanation`.

```yaml
choices: ['`4`', '`9`', '`8`', '`Error: object ''e'' not found`']
```

## 5. Two questions in one stem

Rejected: "and" asks two things, so a partly right answer has no option.

```yaml
question: |
  What does `c(a(), a(), b(), a())` print, and how many environments
  does the code create?
```

Fixed: one question ("What does the last line print?", ff-004). If the
second part matters, it gets its own item.

## 6. A fragment instead of complete code

Rejected: the factory is not shown, so the answer depends on a guess.

```yaml
question: |
  After `a <- new_counter()`, what does `c(a(), a(), a())` print?
```

Fixed: show the complete, runnable code (ff-004 and ff-005 each show the
whole factory), and run it as printed before shipping.

## 7. "Why" with prose options

Rejected: prose explanations as options invite arguments about wording, and
several can be partly right.

```yaml
question: Why does the counter made with `<-` not count?
choices:
  - 'Because `<-` creates a local variable that is discarded'
  - 'Because R copies the environment on every call'
  - 'Because the factory returns before the counter runs'
  - 'Because `i` is a promise'
```

Fixed: ask what happens instead ("What does the last line print?",
ff-005), and put the reason in `explanation`.

## 8. One question answering another

Rejected: an item whose code fixes the bug with `force(exp)` and prints
`4`, in the same bank as ff-002, which asks what the unfixed code prints.
Drawn into one quiz, the first gives away the second.

Fixed: test each example once; when two items share code, neither may show
the other's answer.
