# Using the skill

Talk to the agent in plain words; it picks one of four starting points.

| you say | what happens |
|---|---|
| "Make a quiz bank from `lecture07.pptx` and `notes07.pdf`." | a new bank, all steps below |
| "Build `week5.yaml` into a Canvas QTI file." | validate, build, check the package |
| "Add 10 numerical items on the bootstrap to `topic09.yaml`." | revise: new ids continue the numbering; existing items are kept |
| "I deleted the weak items in Canvas; here is the export." | sync: kept items become `reviewed`, deleted ones `removed` |

## A new bank, step by step

1. **Profile.** If a `quizbank_profile.yaml` is near the material (or pasted
   in the chat), the agent follows it. See [Course profiles](profiles.md).
2. **Extract.** The agent turns the material into one numbered outline
   (slides, pages, cells), with speaker notes and images in place. PDF
   pages whose diagrams or code exist only as pictures are flagged, so the
   agent looks at them directly.
3. **Questions.** In one message, the agent asks only what it doesn't know:
   - how many items you want to keep (default 50, so it drafts about 65)
   - which code languages items may use
   - who the audience is
   - which sections to include or skip
4. **Coverage plan.** A one-screen table of sections, objectives, item
   counts and difficulty. Reply "OK" or edit it.
5. **Draft** section by section, following the
   [authoring guide](authoring-guide.md).
6. **Verify.** Every snippet runs as printed and every number is
   recomputed. The code is saved as `<bank>.checks.R` / `.py`. Items that
   cannot be run in this environment (for example R in a chat sandbox) are
   marked `verified: no` with the reason.
7. **Validate** the bank.
8. **Package** it as two files: `<bank>.qti.zip` (checked against the
   YAML) and `<bank>-source-and-review.zip` (YAML, review sheet, checks,
   figures and a README).
9. **Hand over** the two downloads, with counts by section, difficulty and
   type, the unverified items, and the import steps.

"Just build it" skips steps 3 and 4 and uses the defaults.

## Downloading in a chat

The agent offers exactly two files:

| product | how the files appear |
|---|---|
| Claude.ai | as download cards under the reply |
| ChatGPT | as links in the reply |
| Gemini | as downloadable files in the reply |

Import the `.qti.zip` into Canvas. Open the other zip for the review sheet,
and keep it: the agent needs its YAML for any later change or sync.

## Reviewing in Canvas

1. Import the `.qti.zip` ([how](import.md)).
2. Read the items in Canvas and delete the ones that don't fit.
   - Each title starts with the item's id, e.g. `ff-004 · Two counters`.
   - Each explanation ends with the item's source, e.g. "Source: slides
     41–43".
   - The `.review.md` sheet has the same items with answers marked, for
     reading offline.
3. Give the agent the `-source-and-review.zip` plus a Canvas export of
   what's left, or a text file of the remaining titles. It shows a dry run,
   updates the YAML, and hands back a fresh pair of downloads. Items you
   edited in Canvas are listed so the edits can be copied into the YAML.

Deleted items stay in the YAML as `status: removed`, so their ids are never
reused and they never come back in a rebuild.

## Tips

- Name the files and the folder you want; otherwise the agent uses
  `quizbank/<bank-name>/`.
- Say "multiple choice only" or "mix in numerical items" to control types.
- Put lasting preferences (languages, audience, notation, things to avoid)
  in a profile once instead of repeating them; the agent offers to save
  them after a first bank.
- Review the "Check these first" list at the top of the review sheet:
  unverified items and items without a source.
