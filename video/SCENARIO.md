# Scenario of the QX-PROBE demonstration video

> The French original of this file is kept unmodified in
> [`docs/SCENARIO.fr.md`](../docs/SCENARIO.fr.md).

**Status:** video **RECORDED** (`media/qx-demo-v1.mp4`, 907 244 bytes, md5
`3558d267dfebc54c275c2c879787b76b`, 44.48 s, 1920x1080, H.264, 25 fps,
1112 frames, **no audio track**).

The recording was re-made after the rules were corrected: the tool now prints
`RESULT:` in English, the on-screen text is entirely English, and every
command shown is a command of **this public repository**, so the jury can
replay them as they are. It was recorded a second time when the test suite
grew from 22 to 27 tests, so that the number on the screen is the number of
the suite that is in this repository today. The first (French) recording, kept
in the frozen snapshot under `docs/`, is not published here.

Shot 5 ("the QNX 8.0 target") is **absent**: it depends on the QNX 8.0 SDK
(non-commercial QNX Everywhere licence, myQNX account), which does not exist
yet. According to the filming rule, this shot was **removed** from the video,
not replaced by a screen capture, and **no compiler output was simulated**.

Format: MP4 H.264, 1920x1080, 25 fps, 44.48 s, no voice-over (the on-screen
text has to be enough).

---

## The shot list

### 1. The problem (8 s)

* Terminal, empty prompt.
* On-screen text: `A QNX 8.0 driver goes wrong in three ways very quickly.`
* Then, one by one, the three mistakes and their consequence:
  * `read()` without `iofunc_read_verify()` -> the client reads what it must not.
  * a message loop that blocks without dispatching -> the client hangs.
  * a reply that returns more parts than the IOV holds -> a corrupted answer.
* Final text: `All three are visible in the code. You need a tool.`

### 2. The tool (10 s)

* Terminal: `python3 -I qx_probe.py examples/blackberry_eventfd_mgr.c`
* BlackBerry's **public reference code** passes: `0 ERROR, 0 WARN`.
* On-screen text: `The QNX 8.0 vendor's reference code passes with no error and no warning.`

### 3. The false positive, acknowledged (12 s) — the most important moment

* Terminal: `python3 -I qx_probe.py examples/qnx80_resmgr_readonly.c`
* Result: `0 ERROR, 0 WARN`.
* On-screen text:
  `Mount point outside /dev/ and read-only resource manager: both are valid in QNX 8.0.`
  `An earlier version of this tool reported these two cases. False positive.`
* Then the source of the rule, shown in full:
  `resmgr_attach() : "puts the path into the general pathname space"`

### 4. The detection (12 s)

* Terminal: `bash scripts/run_tests.sh` (the complete suite).
* Then a targeted demonstration: the file `examples/qnx80_resmgr_relative_path.c`
  produces exactly one `WARN QX005`, with the file line.
* On-screen text: `The rule that bites: a relative path depends on the current directory.`

### 5. The QNX 8.0 target (25 s) — requires the SDK

* Terminal: `bash scripts/build_qcc.sh`
  * real `qcc` output, unedited;
  * the produced binary is run under QEMU if available, otherwise the compile
    output is enough (the contest rationale is "build, test, analyze", not
    "run").
* Terminal: `cat /proc/mount` (or the list of mount points) — the resource
  manager mounted on `/dev/qxprobe-demo` appears.
* A `cat /dev/qxprobe-demo` from the QNX shell shows the character returned
  by the read handler: the demonstration is **real**, not a screenshot of the
  documentation.

### 6. The link with the contest (8 s)

* On-screen text:
  `Zero dependency. Zero hardware. A tool that runs in your CI.`
  `Apache-2.0 licence. Every rule cites its QNX 8.0 documentation page.`

---

## What the video shows exactly (measured, shot by shot)

1. On-screen title: `QX-PROBE — QNX 8.0 resource-manager protocol checker`.
2. `QX-PROBE reads the source of a QNX 8.0 resource manager and reports the
   protocol mistakes the compiler cannot see.  Every rule is backed by an
   official QNX SDP 8.0 documentation page.` — the tool is presented in one
   sentence.
3. `$ head -14 examples/blackberry_eventfd_mgr.c` — an extract of BlackBerry's
   public resource manager (Apache-2.0).
4. "The checker stays green on correct code":
   `python3 -I qx_probe.py examples/blackberry_eventfd_mgr.c`
   -> **5 findings, 0 ERROR, 0 WARN, exit code 0**.
5. "The example of the QNX 8.0 documentation is green too":
   `python3 -I qx_probe.py examples/qnx80_resmgr_official_example.c`
   -> **6 findings, 0 ERROR, 0 WARN, exit code 0**.  This file is the official
   example of `iofunc_func_init()`, reproduced in the repository: it used to
   be reported by mistake.
6. "The same code, with a single access gate removed":
   `python3 -I qx_probe.py tests/fixtures/qnx80_resmgr_qx004_no_gate.c`
   -> **6 findings, 1 ERROR (QX004), 0 WARN, exit code 1**.
7. "The checker is usable as a CI gate: the exit code is not 0":
   `... > /dev/null; echo "exit code = $?"` -> `exit code = 1`.
8. "27 tests: both sides of the contract (no false positive, real defect
   caught)": `python3 -I tests/test_qx_probe.py 2>&1 | tail -3`
   -> `Ran 27 tests ... OK`.
9. "Zero dependency: the standard library only, no QNX SDK":
   `grep -n "^import\|^from" qx_probe.py`
   -> `re`, `sys`, `dataclasses` — the standard library, nothing else.
10. "End of the demonstration".

Every figure above was **re-run** with the current version of the linter; the
numbers are the measured ones, not a transcription.

### The honest reservations about this video

* **Shot 5 (the QNX 8.0 target) is missing, and the compilation is NOT
  MEASURED.** The QNX SDP 8.0 and its non-commercial licence do not exist in
  this environment. `scripts/build_qcc.sh` is written and stops with an
  explicit message when `qcc` is absent; it never simulates a compiler
  output. The examples have therefore **never been compiled for QNX 8.0**,
  and this video does not pretend otherwise.
* **Shot 3 (the acknowledged false positive) is not in this recording** either:
  the two historical false positives (mount point outside `/dev/`, read-only
  resource manager) are fixed and covered by the test suite, but the video
  keeps its runtime short. The proof is in `tests/test_qx_probe.py`, which is
  replayable in one command.
* Everything else was filmed for real: no screen capture, no simulated
  compiler output, no fabricated terminal.

---

## Filming rules

* **No invented output.** Everything filmed was actually executed. If the SDK
  is missing, shot 5 is **removed** from the video, not replaced by a screen
  capture.
* Each shot shows the **code** that produces the result (the file is opened
  next to the terminal when a result has to be believed).
* The quotations of the QNX 8.0 documentation are shown with their URL, so
  that the jury can check them.
* No internal path, no account identifier, no personal data in the shots.

## What remains to be done (video v2, with the SDK)

1. Get the SDP 8.0 (Linux x86_64 host tools) and a non-commercial QNX
   Everywhere licence.
2. Check the target: `qcc -Vgcc_ntoaosdebug` must compile the examples.
3. Re-run `bash scripts/run_tests.sh` and `bash scripts/build_qcc.sh` up to date.
4. Record the **v2**: shots 3 and 5 (the acknowledged false positive, the
   QNX 8.0 target).
5. Upload to YouTube with **public access** (a requirement of the rules) and
   provide the URL.
