# Scenario of the QX-PROBE demonstration video

> The French original of this file is kept unmodified in
> [`docs/SCENARIO.fr.md`](../docs/SCENARIO.fr.md).

**Status:** video **v0 RECORDED** (`media/qx-demo-v0.mp4`, 543 516 bytes, md5
`381f7aa6af21ae209e3bbccb1d4bfac0`, 35.92 s, 1920x1080, H.264, 25 fps,
898 frames, **no audio track**).

Shot 5 ("the QNX 8.0 target") is **absent**: it depends on the QNX 8.0 SDK
(non-commercial QNX Everywhere licence, myQNX account), which does not exist
yet. According to the filming rule, this shot was **removed** from the video,
not replaced by a screen capture, and **no compiler output was simulated**.

The v0 video therefore covers shots **1 (partly), 2, 4 and 6**. Shots **3**
(the acknowledged false positive) and **5** (the QNX 8.0 target) are not in it.

Format: MP4 H.264, 1920x1080, 25 fps, 35.92 s, no voice-over (the on-screen
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

## What the v0 video shows exactly (measured, shot by shot)

1. On-screen title: `QX — QNX 8.0 resource-manager protocol checker`.
2. `QX-PROBE analyses the source code of a QNX resource manager and reports
   (the error)` — the tool is presented in one sentence.
3. `$ head -12 research/shim-demo/eventfd-mgr.c` — an extract of BlackBerry's
   public resource manager (Apache-2.0).
4. "The probe passes green on correct code":
   `python3 -I probe/qx_probe.py research/shim-demo/eventfd-mgr.c`
   -> **5 findings, 0 ERROR, 0 WARN, exit code 0**.
5. "The same code, with a single access gate removed":
   `python3 -I probe/qx_probe.py proofs/contre-epreuve/eventfd-mgr-qx004.c`
   -> **6 findings, 1 ERROR (QX004), 0 WARN, exit code 1**.
6. "The probe is usable as a CI gate: a non-zero exit code":
   `... > /dev/null; echo "exit code = $?"` -> `exit code = 1`.
7. "Zero dependency, zero QNX SDK, runs everywhere":
   `python3 -c "import importlib.util as u; print(...)"` ->
   `external dependencies: ['pycparser']`.
8. "End of the demonstration".

The figures 4 and 5 were **re-run** with the current version of the linter:
they are identical.

### Two honest reservations about the v0 video

* **Shot 7 (dependencies) is misleading as it stands.** The command shown lists
  the modules **present on the machine where the video was recorded**, not the
  ones QX-PROBE uses. `qx_probe.py` imports only the Python standard library
  (`re`, `sys`, `dataclasses`); `pycparser` was installed on that machine and
  is **not** used by the tool. The v1 video must show the real imports.
* **The filmed commands show internal paths** (`research/…`, `proofs/…`) that
  do not exist in this public repository. The public equivalents are:
  `python3 -I qx_probe.py examples/blackberry_eventfd_mgr.c` (healthy file:
  5 findings, 0 ERROR, 0 WARN, exit code 0) and
  `bash scripts/run_tests.sh` (the complete suite, 11 tests, including the
  detection case `examples/qnx80_resmgr_relative_path.c`: exactly one
  WARN QX005, exit code 1).
* The video itself **is in French**; the contest rules require every
  material to be in English, or to have an English translation provided. The
  shot-by-shot English translation of the v0 video is provided with the
  submission text.

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

## What remains to be done (video v1, with the SDK)

The **v0** video is recorded (see above). What remains:

1. Get the SDP 8.0 (Linux x86_64 host tools) and a non-commercial QNX
   Everywhere licence.
2. Check the target: `qcc -Vgcc_ntoaosdebug` must compile the two examples.
3. Re-run `bash scripts/run_tests.sh` and `bash scripts/build_qcc.sh` up to date.
4. Record the **v1**: shots 3 and 5 (the acknowledged false positive, the
   QNX 8.0 target), an English version or subtitles, and a "zero dependency"
   shot that shows the real imports of `qx_probe.py` instead of the modules
   present on the recording machine.
5. Upload to YouTube with **public access** (a requirement of the rules) and
   provide the URL.
