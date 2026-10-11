"""Tests for skills/canvas-quizbank (standard library only).

Run from the repository root:  python3 -m unittest discover -s tests
tools/build_zips.py runs them before writing any zip.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "canvas-quizbank"
SCRIPTS = SKILL / "scripts"
EXAMPLES = SKILL / "examples"
BANKS = [EXAMPLES / "advanced-r-function-factories" / "function-factories.yaml",
         EXAMPLES / "smoke-test" / "smoke-test.yaml"]
sys.path.insert(0, str(SCRIPTS))

import bank  # noqa: E402
import build_qti  # noqa: E402
import mdrender  # noqa: E402
import validate_bank  # noqa: E402


def run(script: str, *args, cwd=None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)],
                          capture_output=True, text=True, cwd=cwd)


class RendererTest(unittest.TestCase):
    def test_math_becomes_canvas_equation_image(self):
        html = mdrender.render(r"Let $\lambda^2$ be")
        self.assertIn('class="equation_image"', html)
        self.assertIn("/equation_images/%255Clambda%255E2", html)   # encoded twice
        self.assertNotIn("<math", html)

    def test_dollar_amounts_stay_text(self):
        html = mdrender.render("Costs $5 and $20,000; escaped \\$3.")
        self.assertNotIn("equation_image", html)
        self.assertIn("$5 and $20,000", html)

    def test_list_needs_a_blank_line(self):
        self.assertNotIn("<ol", mdrender.render("differ from\n3. How many?"))
        self.assertIn("<ol", mdrender.render("Steps:\n\n1. one\n2. two"))

    def test_table_is_ruled_and_math_pipes_do_not_split_cells(self):
        html = mdrender.render("| x | $|x|$ |\n|:-:|--:|\n| 1 | 2 |")
        self.assertIn('<table border="1"', html)
        self.assertIn('scope="col"', html)
        self.assertIn("border-collapse: collapse", html)
        self.assertEqual(html.count("<th "), 2)
        self.assertIn('data-equation-content="|x|"', html)

    def test_fences_and_typography(self):
        self.assertIn('<pre class="r"><code>x &lt;- 1</code></pre>',
                      mdrender.render("```{r}\nx <- 1\n```"))
        self.assertIn("”", mdrender.render('("*seeing?*")'))       # closes after </em>
        self.assertIn("it’s", mdrender.render("it's"))

    def test_images_go_through_the_hook(self):
        seen = []
        html = mdrender.render("![A plot](figures/a.png)",
                               lambda src, alt: seen.append((src, alt)) or "NEW")
        self.assertEqual(seen, [("figures/a.png", "A plot")])
        self.assertIn('src="NEW"', html)


class ExampleBankTest(unittest.TestCase):
    def test_examples_are_clean(self):
        for path in BANKS:
            errors, warnings = bank.check_bank(bank.load_bank(path), path,
                                               require_source=True)
            self.assertEqual((errors, warnings), ([], []), path.name)

    def test_packages_match_their_banks(self):
        with tempfile.TemporaryDirectory() as tmp:
            for path in BANKS:
                data = bank.load_bank(path)
                items = bank.active(data)
                for mode, image_mode in (("assessment", "files"), ("objectbank", "files"),
                                         ("assessment", "inline")):
                    out = Path(tmp) / f"{path.stem}-{mode}-{image_mode}.qti.zip"
                    build_qti.write_package(data, items, path.parent, out, mode,
                                            True, image_mode)
                    self.assertEqual(validate_bank.check_package(out, items), [],
                                     f"{out.name}")

    def test_samples_match_their_banks(self):
        samples = ROOT / "samples" / "canvas-quizbank"
        cases = [(BANKS[0], "function-factories.qti.zip", False)] + [
            (BANKS[1], f"smoke-test{s}.qti.zip", False)
            for s in ("", ".objectbank", ".inline-images")]
        for yaml_path, name, reviewed_only in cases:
            items = bank.active(bank.load_bank(yaml_path), reviewed_only)
            self.assertEqual(validate_bank.check_package(samples / name, items), [],
                             f"samples/canvas-quizbank/{name} is stale; see samples/README.md")

    def test_no_zip_inside_the_skill(self):
        self.assertEqual(sorted(SKILL.rglob("*.zip")), [])

    def test_every_type_is_exported(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = BANKS[1]
            out = Path(tmp) / "s.qti.zip"
            data = bank.load_bank(path)
            build_qti.write_package(data, bank.active(data), path.parent, out)
            xml = zipfile.ZipFile(out).read("assessment.xml").decode()
            for t in ("multiple_choice_question", "multiple_answers_question",
                      "numerical_question", "true_false_question"):
                self.assertIn(t, xml)
            self.assertIn("%24IMS-CC-FILEBASE%24/images/histogram.png", xml)
            self.assertIn("images/histogram.png", zipfile.ZipFile(out).namelist())

    def test_a_wrong_key_is_caught(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = BANKS[0]
            data = bank.load_bank(path)
            items = bank.active(data)
            out = Path(tmp) / "f.qti.zip"
            build_qti.write_package(data, items, path.parent, out)
            items[0] = dict(items[0], answer=(items[0]["answer"] + 1) % 4)
            self.assertTrue(validate_bank.check_package(out, items))


class PackageTest(unittest.TestCase):
    def test_two_downloads_and_a_self_contained_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, out = Path(tmp) / "work", Path(tmp) / "out"
            src = BANKS[0].parent
            shutil.copytree(src / "figures", work / "figures")
            for f in ("function-factories.yaml", "function-factories.checks.R"):
                shutil.copy(src / f, work)
            (work / "notes.md").write_text("Coverage: sections 10.2-10.5.")
            r = run("package_bank.py", work / "function-factories.yaml", "--out", out,
                    "--notes", work / "notes.md")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(sorted(p.name for p in out.iterdir()),
                             ["function-factories-source-and-review.zip",
                              "function-factories.qti.zip"])
            names = zipfile.ZipFile(out / "function-factories-source-and-review.zip").namelist()
            self.assertEqual(sorted(names), sorted(
                f"function-factories/{n}" for n in (
                    "function-factories.yaml", "function-factories.review.md",
                    "function-factories.checks.R", "figures/loglik.png", "README.md")))
            unz = Path(tmp) / "unz"
            zipfile.ZipFile(out / "function-factories-source-and-review.zip").extractall(unz)
            readme = (unz / "function-factories" / "README.md").read_text()
            self.assertIn("Coverage: sections 10.2-10.5.", readme)
            r = run("build_qti.py", unz / "function-factories" / "function-factories.yaml",
                    "-o", Path(tmp) / "rebuilt.qti.zip")
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_nothing_is_written_when_the_bank_is_broken(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.yaml"
            bad.write_text(BANKS[1].read_text().replace("answer: 0", "answer: 9", 1))
            shutil.copytree(BANKS[1].parent / "figures", Path(tmp) / "figures")
            r = run("package_bank.py", bad, "--out", Path(tmp) / "out")
            self.assertNotEqual(r.returncode, 0)
            self.assertFalse((Path(tmp) / "out").exists())


class ExampleRunsTest(unittest.TestCase):
    """samples/<skill>/<example>/output/<platform>/ hold what each chat platform handed
    back: <bank>.qti.zip plus <bank>-source-and-review.zip. Both must still pass."""

    def test_every_platform_output_validates(self):
        bundles = sorted((ROOT / "samples").glob("*/*/output/*/*-source-and-review.zip"))
        self.assertTrue(bundles, "no example outputs found")
        for bundle in bundles:
            with self.subTest(bundle=str(bundle.relative_to(ROOT))), \
                    tempfile.TemporaryDirectory() as tmp:
                zipfile.ZipFile(bundle).extractall(tmp)
                yamls = sorted(Path(tmp).glob("*/*.yaml"))
                self.assertEqual(len(yamls), 1)
                data = bank.load_bank(yamls[0])
                errors, _ = bank.check_bank(data, yamls[0], require_source=True)
                self.assertEqual(errors, [])
                qti = bundle.parent / f"{yamls[0].stem}.qti.zip"
                self.assertTrue(qti.is_file(), f"missing {qti.name}")
                self.assertEqual(validate_bank.check_package(qti, bank.active(data)), [])


class ReviewSheetTest(unittest.TestCase):
    def test_unverified_items_come_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = BANKS[1]
            data = bank.load_bank(src)
            data["questions"][2]["verified"] = "no"
            data["questions"][2]["verify_note"] = "R not available"
            out = Path(tmp) / "r.md"
            build_qti.write_review(data, bank.active(data), src, out)
            text = out.read_text()
            self.assertLess(text.index("## Check these first"), text.index("## 1."))
            self.assertIn("st-003", text.split("## 1.")[0])


class SyncTest(unittest.TestCase):
    def test_kept_ids_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            src_dir = BANKS[0].parent
            for f in ("function-factories.yaml", "function-factories.checks.R"):
                shutil.copy(src_dir / f, tmp)
            shutil.copytree(src_dir / "figures", Path(tmp) / "figures")
            yaml_path = Path(tmp) / "function-factories.yaml"
            before = yaml_path.read_text()
            kept = Path(tmp) / "kept.txt"
            kept.write_text("ff-001 · Two functions from one factory\nff-002\n")
            r = run("sync_from_canvas.py", yaml_path, "--kept-ids", kept, "--write")
            self.assertEqual(r.returncode, 0, r.stderr)
            data = bank.load_bank(yaml_path)
            status = {q["id"]: q["status"] for q in data["questions"]}
            self.assertEqual(status["ff-001"], "reviewed")
            self.assertEqual(status["ff-002"], "reviewed")
            self.assertEqual(sum(s == "removed" for s in status.values()), 16)
            changed = [(a, b) for a, b in zip(before.splitlines(),
                                              yaml_path.read_text().splitlines()) if a != b]
            self.assertTrue(all("status:" in a and "status:" in b for a, b in changed))
            self.assertTrue((Path(tmp) / "function-factories.yaml.bak").exists())
            self.assertEqual(len(bank.active(data)), 2)


class ExtractorTest(unittest.TestCase):
    def test_marp_and_notebook(self):
        with tempfile.TemporaryDirectory() as tmp:
            deck = Path(tmp) / "deck.md"
            deck.write_text("---\nmarp: true\n---\n# Title\n<!-- _class: lead -->\n\n---\n\n"
                            "## Closures\n\n```r\nx <- 1\n---\n```\n<!-- say this aloud -->\n")
            nb = Path(tmp) / "nb.ipynb"
            nb.write_text(json.dumps({
                "metadata": {"kernelspec": {"language": "R"}},
                "cells": [{"cell_type": "code", "source": ["mean(1:4)"],
                           "outputs": [{"output_type": "execute_result",
                                        "data": {"text/plain": ["[1] 2.5"]}}]}]}))
            r = run("extract_material.py", deck, nb, "-o", Path(tmp) / "out")
            self.assertEqual(r.returncode, 0, r.stderr)
            text = (Path(tmp) / "out" / "outline.md").read_text()
            self.assertIn("(Marp deck, 2 slides)", text)      # '---' inside code kept
            self.assertIn("## Slide 2 — Closures", text)
            self.assertIn("> say this aloud", text)
            self.assertNotIn("_class", text)
            self.assertIn("```R\nmean(1:4)\n```", text)
            self.assertIn("[1] 2.5", text)


if __name__ == "__main__":
    unittest.main()
