# The files under `docs/`

This directory holds three kinds of documents:

| File | What it is |
|---|---|
| [`CODELAB.md`](CODELAB.md) | **the hands-on tutorial** — a 30-minute codelab that teaches a task on QNX 8.0 (auditing the dispatch table of a resource manager) with nothing but Python 3. Every console output it shows is replayed and checked by [`../scripts/verifier-codelab.py`](../scripts/verifier-codelab.py). |
| [`SUBMISSION-EN.md`](SUBMISSION-EN.md) | **the text of the submission form, field by field** — the exact words to paste into each DevPost field (title, tagline, what it does, why we built it, how we built it, what's next, testing instructions, links), with the character count of each block and the source of every figure. |
| [`YOUTUBE-VIDEO.md`](YOUTUBE-VIDEO.md) | **the YouTube upload package** — the exact title and description to paste, the file to upload with its MD5, size and measured duration, the thumbnail, the five steps, and the two places where the link of the uploaded video has to be pasted. |
| `README.fr.md`, `RULES.fr.md`, `SCENARIO.fr.md` | the **original French versions** of the three documents of the repository, kept **unmodified** so that the English versions can be checked side by side. |

| French file (frozen) | English version (the submission) |
|---|---|
| `docs/README.fr.md` | [`../README.md`](../README.md) |
| `docs/RULES.fr.md` | [`../RULES.md`](../RULES.md) |
| `docs/SCENARIO.fr.md` | [`../video/SCENARIO.md`](../video/SCENARIO.md) |

**The English files are the ones the contest rules require.** The French ones
are the archived v0.1 snapshot: they describe the first version of the tool,
its first set of rules and the first recording of the demonstration video.

> **They are historical documents, not documentation.** They describe a
> linter that reported five false positives and that printed a French summary
> line (`RESULTAT:`). The current tool prints `RESULT:`, reports no false
> positive on the reference code of QNX 8.0, and its rules are listed one by
> one — with their official documentation page — in
> [`../RULES.md`](../RULES.md).

Nothing in this directory is needed to run the tool, to run the tests or to
read the video.

> The frozen snapshot mentions a video `qx-demo-v0.mp4` (the first, French
> recording). It is **not** the one published here: the demonstration video of
> this repository is [`../media/qx-demo-v1.mp4`](../media/qx-demo-v1.mp4) — the
> English re-recording, made after the five rules were corrected.
