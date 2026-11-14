#!/usr/bin/env python3
"""The two controls of the published figures, and their counter-proofs.

scripts/verifier-chiffres-publies.py compares every figure the documents
publish (tests, files, classes, quotations, pages, blocks, rules, lines,
checks, the duration and the size of the video) with the figures measured
on the repository.  scripts/verifier-benchmark-publie.py compares the table
and the console extract of docs/BENCHMARK.md with the real output of the
benchmark.  A control that has never met a false figure is not known to
catch one: these tests write false figures and check that both controls
report them.  No network is needed: the benchmark output is the real output
of 14 November 2026, saved in tests/fixtures/benchmark/.

Run:  python3 -I tests/test_published_figures.py
"""
import importlib.util
import pathlib
import sys
import unittest

sys.dont_write_bytecode = True   # never leave __pycache__ in scripts/

REPO = pathlib.Path(__file__).resolve().parent.parent
SAVED = REPO / "tests" / "fixtures" / "benchmark" / "benchmark-output-20261114.txt"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, str(REPO / path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FIG = load("qx_figures", "scripts/verifier-chiffres-publies.py")
BENCH = load("qx_bench_published", "scripts/verifier-benchmark-publie.py")


def measured():
    n_files, _how = FIG.measure_files()
    per_file, total, classes = FIG.measure_tests()
    pages, quotations = FIG.measure_citations()
    codelab, devpost = FIG.measure_blocks()
    seconds, size = FIG.measure_video()
    return {
        "tests": {str(n) for n in per_file.values()} | {str(total)},
        "files": {str(n_files)}, "classes": {str(classes)},
        "quotations": {str(quotations)}, "pages": {str(pages)},
        "blocks": {str(codelab), str(devpost)},
        "rules": {str(FIG.measure_rules())}, "lines": {str(FIG.measure_lines())},
        "checks": {str(FIG.measure_checks())},
        "seconds": {seconds}, "bytes": {str(size)},
    }


class PublishedFigures(unittest.TestCase):

    def setUp(self):
        self.real = measured()
        self.texts = FIG.read_documents()

    def stale(self, extra):
        texts = dict(self.texts)
        texts["README.md"] = texts["README.md"] + "\n\n" + extra + "\n"
        claims = FIG.collect_claims(texts)
        return FIG.check_claims(claims, self.real)[0]

    def test_an_exemption_applies_in_its_context(self):
        # The same "37 pages", written next to "that guide", is exempted.
        # (Whether the published documents themselves are stale is row 7 of
        # scripts/verify-all.sh: it depends on the tree, not on the code.)
        texts = dict(self.texts)
        texts["RULES.md"] = (texts["RULES.md"]
                             + "\n\nMeasured on the 37 pages of that guide.\n")
        stale = FIG.check_claims(FIG.collect_claims(texts), self.real)[0]
        self.assertFalse([c for c in stale if c[2] == "37 pages"])

    def test_counter_proof_detects_a_false_figure_of_every_kind(self):
        self.assertTrue(FIG.counter_proof(self.texts, self.real, quiet=True))

    def test_each_false_figure_alone_is_stale(self):
        for kind, said in FIG.FALSE_FIGURES:
            with self.subTest(kind=kind):
                found = self.stale("This sentence announces %s." % said)
                self.assertTrue([c for c in found if c[3] == kind],
                                "%s was not reported" % said)

    def test_an_exemption_does_not_apply_out_of_its_context(self):
        # "37 pages" is exempted in RULES.md, next to "that guide" only.
        texts = dict(self.texts)
        texts["RULES.md"] = texts["RULES.md"] + "\n\nThe rules cite 37 pages.\n"
        stale = FIG.check_claims(FIG.collect_claims(texts), self.real)[0]
        self.assertTrue([c for c in stale if c[2] == "37 pages"])

    def test_the_duration_is_read_in_the_mp4_header(self):
        seconds, size = FIG.measure_video()
        self.assertRegex(seconds, r"^\d+\.\d\d$")
        self.assertEqual(size, (REPO / FIG.VIDEO).stat().st_size)


class PublishedBenchmark(unittest.TestCase):

    def setUp(self):
        self.real = BENCH.parse_output(SAVED.read_text(encoding="utf-8"))
        self.texts = {d: (REPO / d).read_text(encoding="utf-8") for d in BENCH.DOCUMENTS}

    def test_the_published_benchmark_is_the_saved_real_output(self):
        for document, text in self.texts.items():
            with self.subTest(document=document):
                self.assertEqual(BENCH.compare(document, text, self.real), [])

    def test_counter_proof_detects_a_false_cell_and_a_false_extract_line(self):
        self.assertTrue(BENCH.counter_proof(self.texts, self.real, quiet=True))

    def test_a_typed_extract_is_not_the_real_output(self):
        # The extract published until 14 November 2026: the right numbers,
        # but not the spacing the script prints.
        document = "docs/BENCHMARK.md"
        typed = self.texts[document].replace(
            [e["line"] for e in self.real["entries"] if e["error"]][0],
            "rpi-thermal/rpi_thermal.c    7 finding(s), 1 ERROR, 0 WARN (exit 1)")
        self.assertTrue(BENCH.compare(document, typed, self.real))

    def test_regenerate_writes_back_the_real_output(self):
        document = "docs/BENCHMARK.md"
        for _what, false in BENCH.falsify(self.texts[document], document):
            fixed = BENCH.regenerate(document, false, self.real)
            self.assertEqual(BENCH.compare(document, fixed, self.real), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
