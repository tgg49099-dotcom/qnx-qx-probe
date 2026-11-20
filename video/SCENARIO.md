# Scenario of the QX-PROBE demonstration video

> The French original of the **first** scenario is kept unmodified in
> [`docs/SCENARIO.fr.md`](../docs/SCENARIO.fr.md). It describes the first
> recording (the French one, `qx-demo-v0.mp4`), which is **not** published
> here; this file describes the video that is published.

**Status:** video **PUBLISHED** (`media/qx-demo-v3.mp4`, 1 417 251 bytes, md5
`98ec689d13bed874bf2b144538a43d91`, 89.72 s, 1920x1080, H.264, 25 fps,
2 243 frames, **no audio track**, **English subtitles burned into the
picture**).

The video was recorded a third time, on a clean clone of this repository at
commit `3921ffc`, for three reasons:

* the second recording (71.44 s) showed the tool on a single file only: the
  third one shows it on a **program split over several files**, on the
  **SARIF 2.1.0** output that feeds GitHub code scanning, and on the
  **benchmark over 17 real public QNX resource managers**, where it finds a
  real missing access gate;
* the rules ask for a video that shows the project **functioning**, and the
  most convincing shot is the **whole test suite** — 81 tests, not 27;
* a video without a sound track must be readable on its own: every scene
  carries a **burned-in subtitle** (English, one short sentence per scene).

Every command shown is a command of **this public repository**, so the jury can
replay them as they are. Nothing was simulated: the outputs on screen are the
real outputs, produced at recording time, with the real exit code. **This was
checked again on 15 November 2026**: the ten commands of the recording were
re-executed on a fresh clone of the public repository at the commit of the
recording, and **nine of the ten reproduced byte for byte** (same exit code,
same md5 of the output); the tenth is the test suite, whose output differs
only in the decimal of its elapsed time ("Ran 81 tests in 1.788s" on the
recording, "Ran 81 tests in 5.229s" on the replay) — the same 81 tests, the
same "OK", the same exit code 0.

The shot that compiles the examples with `qcc` and runs them on a QNX 8.0 guest
under QEMU is **absent**: it depends on the QNX 8.0 SDK (non-commercial QNX
Everywhere licence, myQNX account), which does not exist yet. According to the
filming rule, this shot was **removed** from the video, not replaced by a
screen capture, and **no compiler output was simulated**.

Format: MP4 H.264 (High, yuv420p), 1920x1080, 25 fps, 89.72 s, **no voice-over
and no music at all** — the file has no audio stream — and the on-screen text
plus the burned-in subtitles have to be enough.

---

## The shot list

18 scenes, 2 243 frames, 89.72 s. The timings are the measured ones
(`video/qx-demo-v3.timeline.json`).

| # | from (s) | to (s) | what is on screen | subtitle (burned in) |
|---|---|---|---|---|
| 0 | 0.00 | 4.00 | title card | A linter for QNX 8.0 resource managers. It runs on the host. |
| 1 | 4.00 | 7.20 | intertitle: every command is real | Every command in this video is a command of the public repository. |
| 2 | 7.20 | 11.32 | `head -14 examples/blackberry_eventfd_mgr.c` | The corpus: BlackBerry's own resource manager, under Apache-2.0. |
| 3 | 11.32 | 16.32 | `python3 -I qx_probe.py examples/blackberry_eventfd_mgr.c` | BlackBerry's own resource manager: 0 ERROR, 0 WARN. |
| 4 | 16.32 | 19.52 | intertitle: a real defect must be reported | A real defect must be reported, not hidden. |
| 5 | 19.52 | 25.68 | `python3 -I qx_probe.py tests/fixtures/qnx80_resmgr_qx004_no_gate.c` | One access gate removed: 1 ERROR, and exit code 1 stops the build. |
| 6 | 25.68 | 31.16 | intertitle: the rule behind it | The rule is the QNX 8.0 documentation's own sentence. |
| 7 | 31.16 | 34.36 | intertitle: a program split over several files | Real QNX programs are split over several files. |
| 8 | 34.36 | 39.72 | `cd tests/fixtures/multifile && python3 -I ../../../qx_probe.py split_main.c` | One file alone: the message loop lives in another file, so a WARN and exit code 1. |
| 9 | 39.72 | 46.08 | `cd tests/fixtures/multifile && python3 -I ../../../qx_probe.py split_main.c split_loop.c split_io_read.c` | The three files read together, as one program: 0 ERROR, 0 WARN. |
| 10 | 46.08 | 49.28 | intertitle: the same findings as code-scanning alerts | The same findings, as alerts in GitHub code scanning. |
| 11 | 49.28 | 59.44 | `python3 -I qx_probe.py --format sarif ...` and the `grep` of the rule link | Each alert carries its rule, its level and a link to the rule and its QNX source. |
| 12 | 59.44 | 62.64 | intertitle: code the tool was never written for | Then on code the tool was never written for. |
| 13 | 62.64 | 72.68 | `python3 -I scripts/benchmark-corpus.py` | 17 public resource managers, each pinned to a commit: one real missing access gate. |
| 14 | 72.68 | 75.88 | intertitle: the suite checks both sides | The suite checks both sides: no false positive, real defects caught. |
| 15 | 75.88 | 80.64 | `python3 -I -m unittest discover -s tests` | 81 tests pass, from a clean clone. |
| 16 | 80.64 | 85.24 | `grep -n "^import\|^from" qx_probe.py` | Only the Python standard library: no QNX SDK, no board, no licence. |
| 17 | 85.24 | 89.72 | end card | End of the demonstration. The source is in the public repository. |

## The measured results shown on screen

1. `head -14 examples/blackberry_eventfd_mgr.c` -> the Apache-2.0 header of
   BlackBerry's public resource manager, exit code 0.
2. `python3 -I qx_probe.py examples/blackberry_eventfd_mgr.c`
   -> **5 findings, 0 ERROR, 0 WARN, exit code 0**.
3. `python3 -I qx_probe.py tests/fixtures/qnx80_resmgr_qx004_no_gate.c`
   -> **6 findings, 1 ERROR (QX004), 0 WARN, exit code 1**.
4. `cd tests/fixtures/multifile && python3 -I ../../../qx_probe.py split_main.c`
   -> **8 findings, 0 ERROR, 1 WARN (QX006: no message loop in this file),
   exit code 1** — the loop lives in another translation unit.
5. The same command with the three files of the program
   (`split_main.c split_loop.c split_io_read.c`)
   -> **6 findings, 0 ERROR, 0 WARN, exit code 0**: read as one program.
6. `python3 -I qx_probe.py --format sarif tests/fixtures/qnx80_resmgr_qx004_no_gate.c`
   -> the SARIF 2.1.0 alert of the rule **QX004**, with its level and its
   `helpUri` (the link to the rule in the repository's `RULES.md`), which the
   second command prints with `grep`, exit code 0 for both.
7. `python3 -I scripts/benchmark-corpus.py` -> **17/17 files analysed, 1 ERROR
   in total**: the real missing access gate of
   `rpi_thermal/rpi_thermal.c:465`, the only one found in 17 real public QNX
   resource managers, each pinned to a commit.
8. `python3 -I -m unittest discover -s tests` -> `Ran 81 tests ... OK`, exit
   code 0.
9. `grep -n "^import\|^from" qx_probe.py` -> `re`, `sys`, `dataclasses` and
   `from __future__ import annotations` — the standard library, nothing else.

Every figure above was **re-run** with the current version of the linter on a
fresh clone of this repository; the numbers are the measured ones, not a
transcription.

## How the subtitles are made

* The subtitle is **drawn in the pixels** of the frames by the recording
  script: there is no separate `.srt` file, and the MP4 has no text stream.
* English (the rules require English for all the submitted material), one
  short sentence per scene, **two lines at most**, at most 70 characters per
  line.
* The text is drawn in a band at the bottom of the picture (rows 880 to 1080)
  and the terminal content never reaches that band: a subtitle **never covers
  a line of code or of output**.
* White text on a dark band, font size 40 bold, with a blue accent line: the
  contrast is strong and the text is large.
* The shortest scene lasts **3.20 s**, so every subtitle stays on screen
  longer than the 2.5 s the filming rules ask for.
* The text says **what the viewer sees**, not a marketing claim.

The 18 subtitles are listed with their timings in
[`../docs/YOUTUBE-VIDEO.md`](../docs/YOUTUBE-VIDEO.md) (§ 8), and one frame
per subtitle was extracted and read to check that the sentence matches the
scene.

### The honest reservations about this video

* **The QNX 8.0 target shot is missing, and the compilation is NOT
  MEASURED.** The QNX SDP 8.0 and its non-commercial licence do not exist in
  this environment. `scripts/build_qcc.sh` is written and stops with an
  explicit message when `qcc` is absent; it never simulates a compiler
  output. The examples have therefore **never been compiled for QNX 8.0**,
  and this video does not pretend otherwise.
* **The video shows the tool running on the host machine**, which is the
  platform the tool is built for: QX-PROBE is a host tool (it reads C source
  code and needs neither the SDK nor a board). The rules define the
  eligible category "Developer Tooling & Host Tools" as "a host-based tool
  running on Windows, macOS, or Linux that builds, tests, analyzes, or
  otherwise supports software targeting QNX 8.0". The argument is written out
  in [`../RULES.md`](../RULES.md) and in
  [`../docs/RULES.fr.md`](../docs/RULES.fr.md).
* Everything else was filmed for real: no screen capture, no simulated
  compiler output, no fabricated terminal, no filler image.

---

## Filming rules

* **No invented output.** Everything filmed was actually executed. If the SDK
  is missing, the target shot is **removed** from the video, not replaced by a
  screen capture.
* Each shot shows the **code** that produces the result (the file is opened
  next to the terminal when a result has to be believed).
* The quotation of the QNX 8.0 documentation is shown with its URL, so that
  the jury can check it.
* No internal path, no account identifier, no personal data in the shots.
* No music, no voice-over: the file has **no audio stream at all**.
* Every scene carries a burned-in subtitle that describes what is on screen.

## What remains to be done

1. Get the SDP 8.0 (Linux x86_64 host tools) and a non-commercial QNX
   Everywhere licence.
2. Check the target: `qcc -Vgcc_ntox86_64` must compile the examples.
3. Re-run `bash scripts/run_tests.sh` and `bash scripts/build_qcc.sh` up to date.
4. Record a **v4** with the target shot (the QNX 8.0 guest under QEMU), and
   keep the same subtitle rules.
5. Upload to YouTube with **public access** (a requirement of the rules) and
   provide the URL. — *one action by the owner, not by the automation.*
