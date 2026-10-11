# Course profile

A course profile records one course's conventions, so every bank for that
course follows them without the instructor repeating themselves. It is an
optional YAML file, usually `quizbank_profile.yaml` next to the course
material or the banks. The instructor may also paste it into the chat.

**Precedence:** the instructor's request, then the profile, then the
defaults in `authoring-guide.md`. A profile rule that conflicts with a
default replaces it; everything else adds to it.

```yaml
course: "STAT 101: Introduction to Statistics"
audience: "first-year undergraduates; no programming before this course"
languages: [R]               # languages items may show code in; [] = no code
types: [multiple_choice]     # allowed types (default: multiple_choice only)
bank:
  target_items: 50           # items wanted after the instructor trims
  overdraft: 1.3             # draft target × overdraft (default 1.3)
  difficulty_mix: {easy: 0.33, medium: 0.5, hard: 0.17}
  id_prefix: "w05-"          # ids are prefix + 3 digits: w05-001, w05-002, ...
  points: 1
notation:                    # how to write things
  - "Write sample means as \\overline{x}, never \\bar{x}."
avoid:                       # never include
  - "Questions about the textbook's chapter numbering."
rules:                       # extra rules, in the instructor's words
  - "Every item about a test names the null hypothesis."
```

Every field is optional. Unknown fields are allowed: read them as
instructions.

## When there is no profile

Ask only what the request does not answer (see SKILL.md, intake). At the
end, offer to save the answers as `quizbank_profile.yaml` for next time,
and write it only if the instructor agrees.

## Examples

- `examples/profiles/template.yaml`: every field, commented
- `examples/profiles/bios615.yaml`: a graduate statistical computing
  course with R and Python, showing many real conventions
