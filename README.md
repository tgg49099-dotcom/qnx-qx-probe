# QX-PROBE — a static checker for the QNX 8.0 resource-manager protocol

QX-PROBE reads C code and reports the **resource-manager bugs you cannot
afford** in a QNX 8.0 driver: a read handler that never calls
`iofunc_read_verify()`, a message loop that blocks without dispatching, a
reply that returns more parts than the IOV holds.

It is a **host** tool: it runs on Linux, macOS or Windows, it has **no
dependency** and it asks for **neither a QNX SDK nor a QNX board**. That is
what makes it usable in a continuous-integration chain, or for a jury that
has no hardware.

```console
$ python3 -I qx_probe.py tests/fixtures/qnx80_resmgr_qx004_no_gate.c
ERROR QX004  tests/fixtures/qnx80_resmgr_qx004_no_gate.c:52: qx_read() never calls iofunc_read_verify(): the access gate is missing
...
RESULT: 6 finding(s), 1 ERROR, 0 WARN
```

Every finding points at a line (`file:line:`, the gcc format), so a click in
VS Code, in the Eclipse-based QNX Momentics IDE or in a CI log opens the
source line. On the official QNX example, the same command reports nothing
actionable (`0 ERROR, 0 WARN`, exit code 0).

## The golden rule: zero false positives

QNX 8.0 is a real-time operating system. The reference code of resource
managers is public and written by the vendor itself. **A rule that reports
canonical code by mistake is worse than a missing rule**: it would lose the
contest at the judge's first look.

Concretely, the linter **never** reports:

* a mount point outside `/dev/` — `resmgr_attach()` "puts the path into the
  general pathname space";
* a read-only resource manager (no `io_funcs.write`) — every slot of
  `resmgr_io_funcs_t` has a documented POSIX default;
* the `resmgr_block()` / `resmgr_handler()` idiom — it is the canonical
  example in the QNX 8.0 documentation;
* an `iofunc_func_init()` called with the `_RESMGR_IO_NFUNCS` /
  `_RESMGR_CONNECT_NFUNCS` macros — that is the normal case;
* **the official example of the documentation** — `examples/qnx80_resmgr_official_example.c`
  reproduces the `iofunc_func_init()` example of QNX SDP 8.0 (including its
  `my_io_functions.io_read = my_io_read;` spelling) and produces no
  actionable finding;
* a handler defined in another translation unit — a single file cannot prove
  that a symbol is missing.

Every rule is backed by an official **BlackBerry QNX SDP 8.0** documentation
page (the 12 cited pages were re-read on 12 November 2026; each one carries
the update date QNX put on it, and `scripts/verifier-citations.py` prints
that date). The detail, rule by rule, with the quotation and the URL, is in
**[RULES.md](RULES.md)**.

## The eleven rules

| Code | What the linter reports | Level | Official QNX 8.0 source |
|---|---|---|---|
| QX001 | the file uses the resmgr API but wires no dispatch table (or attaches a NULL one) | ERROR | `resmgr_attach()` |
| QX002 | `iofunc_func_init()` is asked to fill more entries than the table holds | ERROR | `iofunc_func_init()` |
| QX003 | a slot points at a function not found in the analysed files | INFO | `resmgr_io_funcs_t()` |
| QX004 | a `read`/`write` handler does not call `iofunc_*_verify()` | ERROR | `iofunc_read_verify()` |
| QX005 | the path mounted by `resmgr_attach()` is **relative** | WARN | `resmgr_attach()` |
| QX006 | no message loop **in this file** (`dispatch_block()`/`resmgr_block()`) | WARN | `resmgr_block()` |
| QX007 | the loop blocks but no handler is called **in this file** | WARN | `resmgr_handler()` |
| QX008 | an `io_funcs` slot is not wired (the POSIX default applies) | INFO | `resmgr_io_funcs_t()` |
| QX009 | the reply returns more parts than `attr.nparts_max` allows | ERROR | `_RESMGR_NPARTS()` |
| QX010 | the number of slots of `iofunc_func_init()` is a macro | INFO | `iofunc_func_init()` |
| QX011 | an **automatic** dispatch table is never initialised | WARN | `iofunc_func_init()` |

Exit code: `0` if there is no actionable finding, `1` if there is at least
one `ERROR` or `WARN`, `2` if the call is malformed. `INFO` findings never
change the exit code: they describe the state of the resource manager, they
do not condemn it.

### Reading the output

Each finding is one line: `LEVEL  CODE  file:line: message`. The messages
themselves are in English, and so is the summary line:

```console
RESULT: 5 finding(s), 0 ERROR, 0 WARN
```

For a CI chain, `--format json` and `--format sarif` (SARIF 2.1.0, read by
GitHub code scanning, GitLab and the SARIF viewers of the IDEs) give the
same findings with the same exit code, each with the line of the source file
it is about. See **[docs/CI.md](docs/CI.md)**.

### What was corrected in this version

Seven rules (QX001, QX002, QX003, QX004, QX006, QX007, QX011) had a known
defect that contradicted the official documentation. They are now corrected,
and each correction is covered by a test that **fails on the previous code**
and **passes on the current one** — a rule that was simply deleted would
prove nothing. The rule-by-rule description is in
**[RULES.md](RULES.md)**, section "What was corrected in this version, and
how it is proved".

The last three of them were found by running the tool on **17 real resource
managers written by other people** — seven of them published by QNX or
BlackBerry themselves — and by reading every finding by hand. The corpus,
the measurement and the five defects of the tool it exposed — nine false
positives in five files — are in
**[docs/BENCHMARK.md](docs/BENCHMARK.md)**.

## What is in the repository

```
.gitignore                                   what git ignores (build artefacts, Python caches)
LICENSE                                      Apache-2.0, the full text
NOTICE                                       attribution of the third-party code and the AI notice
README.md                                    this file
RULES.md                                     each rule + its official QNX 8.0 source
qx_probe.py                                  the linter (one file, no dependency)
docs/AI-ASSISTED-RULES.md                    how the eleven rules were written, and how each one was proved
docs/BENCHMARK.md                            the benchmark: QX-PROBE on 17 real QNX resource managers
docs/BENCHMARK.fr.md                         the French counterpart of docs/BENCHMARK.md, updated with it
docs/CI.md                                   JSON and SARIF output, and a GitHub Actions example
docs/CODELAB.md                              the hands-on tutorial (30 minutes, no SDK needed)
docs/README.fr.md                            the French counterpart of this file, updated with it: the parts that were not retranslated still describe the first version of the tool
docs/README.md                               what the files under docs/ are
docs/RULES.fr.md                             the French counterpart of RULES.md, updated with it: the same eleven rules, the same official QNX 8.0 sources
docs/SCENARIO.fr.md                          the French original of video/SCENARIO.md
docs/SUBMISSION-EN.md                        the DevPost submission text, field by field
docs/YOUTUBE-VIDEO.md                        the YouTube upload package (title, description, file, thumbnail, steps)
examples/blackberry_eventfd_mgr.c            BlackBerry's public resource manager (Apache-2.0)
examples/qnx80_resmgr_minimal.c              canonical resource manager (written for this repository)
examples/qnx80_resmgr_official_example.c     the official example of the QNX 8.0 documentation
examples/qnx80_resmgr_readonly.c             read-only, mounted outside /dev/
examples/qnx80_resmgr_relative_path.c        triggers exactly one QX005 warning
examples/sys/eventfd.h                       the header of the example above (Apache-2.0)
media/qx-demo-thumbnail.png                  the thumbnail of the video (PNG, 1280x720)
media/qx-demo-v2.mp4                         the demonstration video itself (MP4, H.264, 1920x1080, 71.44 s)
scripts/audit-sous-titres-pixels.py          proves that the published subtitles ARE the pixels of the video
scripts/benchmark-corpus.py                  runs the linter on a pinned corpus of 17 real QNX resource managers
scripts/build_qcc.sh                         QNX 8.0 build (requires the SDP 8.0)
scripts/run_tests.sh                         runs the test suite
scripts/verifier-citations.py                re-reads the 12 cited QNX 8.0 pages and checks the 33 quotations
scripts/verifier-codelab.py                  replays every command of docs/CODELAB.md and checks its output
scripts/verifier-soumission-devpost.py       checks the submission text: lengths, English, links
scripts/verify-all.sh                        replays every published proof in one command
tests/fixtures/qnx80_resmgr_qx004_no_gate.c  the sabotaged file used by the tests and the video
tests/test_qx_probe.py                       27 tests: 10 anti-false-positive, 15 detection, 2 output format
tests/test_output_formats.py                 9 tests: line numbers, JSON and SARIF output, no QX003 on NULL
tests/test_build_qcc.py                      4 tests: the qcc variant and target of scripts/build_qcc.sh (fake qcc)
video/SCENARIO.md                            the video demonstration scenario
```

The French files under `docs/` are the **French counterparts of their English
version, updated with it**: `docs/README.fr.md` is the French counterpart of
this file, `docs/RULES.fr.md` is the **French counterpart of `RULES.md`,
updated with it** — it carries the same eleven rules, the same official
QNX 8.0 sources and the same six quotations of the contest rules — and
`docs/BENCHMARK.fr.md` is the French counterpart of `docs/BENCHMARK.md`,
updated with it: the same corpus, the same measurements, the same
conclusions. The parts of them that were not retranslated still describe the
first version of the tool. The last one, `docs/SCENARIO.fr.md`, is the
**original French version**, kept unmodified so the translation can be
checked side by side. The English files are the ones the contest rules
require; the French ones are the reference.
`docs/CODELAB.md` is not a translation but a document written directly in
English, because the contest rules require the submitted material to be in
English. `docs/SUBMISSION-EN.md` is the text of the submission form, field by
field: everything to paste into DevPost is between its markers.

## The hands-on codelab

**[docs/CODELAB.md](docs/CODELAB.md)** — a 30-minute tutorial that teaches a task on
QNX 8.0 (auditing the dispatch table of a resource manager) without needing
an SDK, a board or a licence: it works on a plain Python 3.

It is not a promise, it is a checked transcript:

* every console block of the tutorial is replayed by
  `scripts/verifier-codelab.py`, which runs the commands in a throw-away copy
  of the repository and compares the real output with the output written in
  the tutorial;
* the tutorial also states the **known limits of the tool**, with the
  measured results, instead of hiding them.

```console
$ python3 -I scripts/verifier-codelab.py
...
blocks replayed and matching : 12
blocks replayed and differing : 0
VERDICT : EVERY OUTPUT OF THE CODELAB IS THE REAL ONE (RC 0)
```

## Run the tests

```console
$ bash scripts/run_tests.sh
```

The suite checks both sides of the contract: valid cases must produce **no**
actionable finding, and broken cases must produce the expected finding. A
rule that was simply deleted proves nothing.

## Replay every claim in one command

Every proof of this repository is replayed by one command, from the root of
the repository:

```console
$ bash scripts/verify-all.sh
```

It runs the test suite, the codelab replay, the pixel audit of the video, the
re-reading of the 12 cited QNX 8.0 pages, the check of the submission text
and the benchmark on 17 real QNX resource managers, then prints one table:
one line per verification, its result and its exit code. It exits 0 only when
every row is OK; a check that could not run is reported as NOT CHECKED, never
as OK.

## Build for QNX 8.0

```console
$ bash scripts/build_qcc.sh
```

This script uses `qcc` from the SDP 8.0, so it is **not runnable without the
SDK**. It stops with an explicit message if `qcc` is absent, and it never
invents a compiler output.

**The compilation is NOT MEASURED.** The SDP 8.0 and its non-commercial
licence do not exist in this environment: the examples have never been
compiled for QNX 8.0, and nothing in this repository pretends otherwise.

## Why this tool counts as QNX 8.0 evidence

The contest rules say exactly what a host tool may offer. Line 149 of the
copy of the rules that we saved and compared word by word on 12 November 2026
(the local copy is `/work/qnx/proofs/rules-live-20261112.txt`; the rules
themselves are public and were fetched from <https://qnx.devpost.com/rules>,
HTTP 200) reads:

> Evidence of QNX use: Your submission must explain how the project uses or
> supports QNX. Evidence may include QNX-specific source code or APIs; QNX
> libraries, headers, buildfiles, toolchains, system images, or configuration
> files in the repository; a demonstration running on QNX 8.0; or, for
> host-based developer tools, output or functionality specifically intended to
> build, analyze, test, deploy, debug, or manage software for QNX 8.0. This
> list is illustrative, not exhaustive. POSIX-compatible code, interpreted
> languages, ports of existing software, and tools that run on another
> operating system remain eligible when the submission clearly demonstrates a
> meaningful connection to QNX. Entrants should identify the relevant files,
> functions, output, or demonstration in their submission description so that
> reviewers can verify the QNX connection.

This repository answers that passage with four things, each of them named
where a reviewer can open it, and each of them re-playable:

* **the eleven rules** — one line each in the table above, every one of them
  backed by an official BlackBerry QNX SDP 8.0 documentation page, with the
  quotation and the URL in **[RULES.md](RULES.md)**;
* **the 33 quotations** taken from the **12** cited pages, checked word for
  word by `scripts/verifier-citations.py`, which re-reads the pages and
  prints the update date QNX put on each of them;
* **the benchmark on public QNX 8.0 code** — the linter is run on **17 real
  resource managers**, **seven of them published by QNX or BlackBerry
  themselves**, every file pinned to the exact commit that was read, with
  **one true positive and no false positive** on the current version (see
  **[docs/BENCHMARK.md](docs/BENCHMARK.md)**);
* **the QNX connection in the rules themselves** — they are not about generic
  C, they are about the QNX 8.0 resource-manager protocol
  (`resmgr_attach()`, `iofunc_read_verify()`, `iofunc_func_init()`,
  `_RESMGR_NPARTS()`), and the code they analyse is QNX 8.0 resource-manager
  code (`examples/`, and the seventeen files of the benchmark).

What this repository does **not** claim: the QNX 8.0 compilation of the
examples is **NOT MEASURED** (the QNX SDP 8.0 is not installed in the
environment where the project was written, and no QNX licence key has been
used there). `scripts/build_qcc.sh` stops with an explicit
message and the exit code 2 when `qcc` is absent, and **no compiler output is
simulated anywhere in this repository**.

## The demonstration video

`media/qx-demo-v2.mp4` — 1 367 966 bytes, MP4 / H.264, 1920x1080, 25 fps,
71.44 s, no audio track (md5 `178e1b58638628a5bc56f11c6fada8e2`).
Its thumbnail is `media/qx-demo-thumbnail.png` (PNG, 1280x720), and the exact
title, description and steps for the mandatory YouTube upload are in
**[docs/YOUTUBE-VIDEO.md](docs/YOUTUBE-VIDEO.md)**.

Every sentence of the video is **burned into the picture** (English
subtitles, one per scene, no subtitle file): the video has no audio track at
all, so there is no music and no voice-over.

That claim is **machine-checkable, and checked here**: the script
**[scripts/audit-sous-titres-pixels.py](scripts/audit-sous-titres-pixels.py)**
re-renders each of the 19 published subtitles (the table of
`docs/YOUTUBE-VIDEO.md` §8) with the same font, size and position, and
compares the result with the pixels of the published file. It needs only
`ffmpeg` and `pillow`:

```
$ python3 scripts/audit-sous-titres-pixels.py
...
   IoU moyen (texte attendu)  : 0.998  (min 0.997)
   IoU moyen (mauvais texte)  : 0.464  (max 0.547)
VERDICT : PREUVE ETABLIE
```

The last line is the **contre-épreuve**: the same comparison made against the
*wrong* subtitle (the next scene's) scores at most 0.547, so the check really
separates the right text from a wrong one — it is not a test that passes
anyway.

Every command shown in the video is a command of this repository, so the
jury can replay them as they are: the checker passes on BlackBerry's own
public resource manager and on the official example of the QNX 8.0
documentation, it catches the missing access gate in a deliberately broken
fixture, and it returns a non-zero exit code — the CI gate. The video also
shows the **false positive of an earlier version of the tool**, acknowledged
and corrected: a read-only manager mounted outside `/dev/` gives 0 ERROR and
0 WARN, and the rule behind it is quoted from the QNX 8.0 documentation. The
shot that compiles the examples with `qcc` and runs them on a QNX 8.0 guest
under QEMU is **absent**: it needs the QNX SDP 8.0 licence, which we do not
have. It was **removed** from the video rather than replaced with a screen
capture, and **no compiler output was simulated**. The shot list and the
honest reservations about it are in **[video/SCENARIO.md](video/SCENARIO.md)**.

## Licence

QX-PROBE code: Apache-2.0 (see `LICENSE`).
The example `examples/blackberry_eventfd_mgr.c` and the header
`examples/sys/eventfd.h` come from BlackBerry's public `shim-demo`
repository and are under Apache-2.0; the full licence header is kept at the
top of each file and the notice is in `NOTICE`.

AI assistance: this project was written with the assistance of a language
model. The official QNX 8.0 documentation and BlackBerry's public reference
code are the only factual sources cited.
