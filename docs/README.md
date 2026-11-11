# The files under `docs/`

This directory holds three kinds of documents:

| File | What it is |
|---|---|
| [`AI-ASSISTED-RULES.md`](AI-ASSISTED-RULES.md) | **how the eleven rules were written and how each one was proved** — for every rule: the official QNX 8.0 page and the sentence it depends on, the first draft of the rule (with the git commit it comes from), the test that fails on the previous code and passes on the current one, and, for the seven rules that had a defect, the documentation the rule contradicted. The official pages are re-read by [`../scripts/verifier-citations.py`](../scripts/verifier-citations.py). |
| [`BENCHMARK.md`](BENCHMARK.md) | **the benchmark on real code** — QX-PROBE run on 17 QNX resource managers written by other people, seven of them published by QNX or BlackBerry themselves: the corpus pinned to its commits, the measurement, the five defects of the tool it found (nine false positives in five files, and the fixes), the one true positive it confirmed, and the manual verification of every access gate. Replayed by [`../scripts/benchmark-corpus.py`](../scripts/benchmark-corpus.py). |
| [`CODELAB.md`](CODELAB.md) | **the hands-on tutorial** — a 30-minute codelab that teaches a task on QNX 8.0 (auditing the dispatch table of a resource manager) with nothing but Python 3. Every console output it shows is replayed and checked by [`../scripts/verifier-codelab.py`](../scripts/verifier-codelab.py). |
| [`SUBMISSION-EN.md`](SUBMISSION-EN.md) | **the text of the submission form, field by field** — the exact words to paste into each DevPost field (title, tagline, what it does, why we built it, how we built it, what's next, testing instructions, links), with the character count of each block and the source of every figure. |
| [`YOUTUBE-VIDEO.md`](YOUTUBE-VIDEO.md) | **the YouTube upload package** — the exact title and description to paste, the file to upload with its MD5, size and measured duration, the thumbnail, the five steps, and the two places where the link of the uploaded video has to be pasted. |
| [`README.fr.md`](README.fr.md) | the **French counterpart of [`../README.md`](../README.md)**, kept in step with it: it is updated when the English file is updated; the parts that were not retranslated still describe the first version of the tool (see below). |
| [`SCENARIO.fr.md`](SCENARIO.fr.md) | the **original French version** of [`../video/SCENARIO.md`](../video/SCENARIO.md), kept **unmodified** so that the English version can be checked side by side. |
| [`RULES.fr.md`](RULES.fr.md) | the **French counterpart of [`../RULES.md`](../RULES.md)**, kept in step with it: the same eleven rules, the same official QNX 8.0 sources, the same six quotations of the contest rules. |
| [`BENCHMARK.fr.md`](BENCHMARK.fr.md) | the **French counterpart of [`BENCHMARK.md`](BENCHMARK.md)**, kept in step with it: the same corpus, the same measurements, the same conclusions. |

| French file | English version (the submission) |
|---|---|
| `docs/README.fr.md` *(kept in step with it)* | [`../README.md`](../README.md) |
| `docs/SCENARIO.fr.md` *(kept unmodified)* | [`../video/SCENARIO.md`](../video/SCENARIO.md) |
| `docs/RULES.fr.md` *(kept in step with it)* | [`../RULES.md`](../RULES.md) |
| `docs/BENCHMARK.fr.md` *(kept in step with it)* | [`BENCHMARK.md`](BENCHMARK.md) |

**The English files are the ones the contest rules require.** `SCENARIO.fr.md`
is the archived v0.1 snapshot: it describes the first recording of the
demonstration video. `README.fr.md` and `RULES.fr.md` are kept in step with
their English version. The parts of `README.fr.md` that were not retranslated
still describe the first version of the tool, and that is stated here so that
nobody mistakes them for a description of the current one.

> **The parts that were not retranslated are historical, not documentation.**
> They describe a linter that reported five false positives and that printed a
> French summary line (`RESULTAT:`). The current tool prints `RESULT:`, reports
> no false positive on the reference code of QNX 8.0, and its rules are listed
> one by one — with their official documentation page — in
> [`../RULES.md`](../RULES.md). The benchmark on 17 real resource managers
> ([`BENCHMARK.md`](BENCHMARK.md)) is the proof that it does not report them
> by mistake.

Nothing in this directory is needed to run the tool, to run the tests or to
read the video.

> The archived `SCENARIO.fr.md` mentions a video `qx-demo-v0.mp4` (the first,
> French recording). It is **not** the one published here: the demonstration
> video of this repository is [`../media/qx-demo-v2.mp4`](../media/qx-demo-v2.mp4)
> — the English re-recording, made after the five rules that had been
> corrected at that time were corrected, with the English subtitles burned into
> the picture. Two more rules were corrected later, on 11/11/2026, after the
> benchmark on real code; neither of them is shown in the video, so every
> figure it shows is still the measured one.
