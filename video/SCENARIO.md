# Scenario of the QX-PROBE demonstration video

> The French original of the **first** scenario is kept unmodified in
> [`docs/SCENARIO.fr.md`](../docs/SCENARIO.fr.md). It describes the first
> recording (the French one, `qx-demo-v0.mp4`), which is **not** published
> here; this file describes the video that is published.

**Status:** video **RECORDED** (`media/qx-demo-v2.mp4`, 1 367 966 bytes, md5
`178e1b58638628a5bc56f11c6fada8e2`, 71.44 s, 1920x1080, H.264, 25 fps,
1 786 frames, **no audio track**, **English subtitles burned into the
picture**).

The video was recorded a second time for three reasons:

* the rules require the video to be **less than three minutes**, the Direction
  asked for **one to two minutes**, and the first English recording was only
  44.48 s long;
* the rules ask for a video that shows the project **functioning**, and the
  most convincing shot — the **false positive of an earlier version of the
  tool**, acknowledged and corrected — was missing from the first recording;
* a video without a sound track must be readable on its own: every scene now
  carries a **burned-in subtitle** (English, one short sentence per scene).

Every command shown is a command of **this public repository**, so the jury can
replay them as they are. Nothing was simulated: the outputs on screen are the
real outputs, produced at recording time, with the real exit code.

The shot that compiles the examples with `qcc` and runs them on a QNX 8.0 guest
under QEMU is **absent**: it depends on the QNX 8.0 SDK (non-commercial QNX
Everywhere licence, myQNX account), which does not exist yet. According to the
filming rule, this shot was **removed** from the video, not replaced by a
screen capture, and **no compiler output was simulated**.

Format: MP4 H.264 (High, yuv420p), 1920x1080, 25 fps, 71.44 s, **no voice-over
and no music at all** — the file has no audio stream — and the on-screen text
plus the burned-in subtitles have to be enough.

---

## The shot list

19 scenes, 1 786 frames, 71.44 s. The timings are the measured ones
(`video/timeline-v3.json`).

| # | from (s) | to (s) | what is on screen | subtitle (burned in) |
|---|---|---|---|---|
| 0 | 0.00 | 3.12 | title card | A linter for QNX 8.0 resource managers. It runs on the host. |
| 1 | 3.12 | 6.24 | the tool in one sentence, marked `(narrative)` | It reports the protocol mistakes the QNX compiler cannot see. |
| 2 | 6.24 | 9.36 | intertitle: the corpus | Every command of this video is a command of the public repository. |
| 3 | 10.24 | 14.48 | `head -14 examples/blackberry_eventfd_mgr.c` | The Apache-2.0 header of BlackBerry's own resource manager. |
| 4 | 14.48 | 17.60 | intertitle: the checker stays green | Correct QNX 8.0 code must produce no error and no warning. |
| 5 | 18.36 | 22.48 | `python3 -I qx_probe.py examples/blackberry_eventfd_mgr.c` | BlackBerry's own resource manager: 0 ERROR, 0 WARN. |
| 6 | 22.48 | 25.60 | intertitle: the false positive, acknowledged | Now the case an earlier version of this tool got wrong. |
| 7 | 26.36 | 30.56 | `python3 -I qx_probe.py examples/qnx80_resmgr_readonly.c` | A read-only manager mounted outside /dev/: 0 ERROR, 0 WARN. |
| 8 | 30.56 | 33.68 | intertitle: the rule behind it | QNX 8.0 documentation: the path joins the general pathname space. / An earlier version of this tool wrongly flagged that case. |
| 9 | 33.68 | 36.80 | the quotation card: `resmgr_attach()` and its official URL | The rule that the earlier version of the tool misread. |
| 10 | 36.80 | 39.92 | intertitle: the same code, one gate removed | A real defect must be reported, not hidden. |
| 11 | 40.84 | 45.08 | `python3 -I qx_probe.py tests/fixtures/qnx80_resmgr_qx004_no_gate.c` | One access gate removed: the checker reports 1 ERROR. |
| 12 | 45.08 | 48.20 | intertitle: the exit code | The exit code tells the build system to stop. |
| 13 | 49.00 | 52.68 | the same command with `> /dev/null` | The exit code is 1, so the checker can gate a CI pipeline. |
| 14 | 52.68 | 55.80 | intertitle: the 27 tests | The suite checks both sides: no false positive, real defects caught. |
| 15 | 56.80 | 60.60 | `python3 -I tests/test_qx_probe.py 2>&1 \| tail -3` | 27 tests pass: no false positive, and real defects caught. |
| 16 | 60.60 | 63.72 | intertitle: zero dependency | No QNX SDK, no board, no licence: Python 3 is enough. |
| 17 | 64.48 | 68.32 | `grep -n "^import\|^from" qx_probe.py` | Only the Python standard library is imported: no QNX SDK, no board. |
| 18 | 68.32 | 71.44 | end card | End of the demonstration. The source is in the public repository. |

## The measured results shown on screen

1. `head -14 examples/blackberry_eventfd_mgr.c` -> the Apache-2.0 header of
   BlackBerry's public resource manager, exit code 0.
2. `python3 -I qx_probe.py examples/blackberry_eventfd_mgr.c`
   -> **5 findings, 0 ERROR, 0 WARN, exit code 0**.
3. `python3 -I qx_probe.py examples/qnx80_resmgr_readonly.c`
   -> **6 findings, 0 ERROR, 0 WARN, exit code 0**. This is the case an
   earlier version of the tool got wrong; it is in the video on purpose.
4. The quotation card: `resmgr_attach() : "puts the path into the general
   pathname space"`, with the official page
   `https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_attach.html`.
   The sentence is **written as text on screen** — the documentation itself is
   never captured.
5. `python3 -I qx_probe.py tests/fixtures/qnx80_resmgr_qx004_no_gate.c`
   -> **6 findings, 1 ERROR (QX004), 0 WARN, exit code 1**.
6. The same command with `> /dev/null` -> **[exit code: 1]** alone, the CI
   gate.
7. `python3 -I tests/test_qx_probe.py 2>&1 | tail -3`
   -> `Ran 27 tests ... OK`.
8. `grep -n "^import\|^from" qx_probe.py`
   -> `re`, `sys`, `dataclasses` — the standard library, nothing else.

Every figure above was **re-run** with the current version of the linter; the
numbers are the measured ones, not a transcription.

## How the subtitles are made

* The subtitle is **drawn in the pixels** of the frames by the recording
  script (`record-sub.py`): there is no separate `.srt` file, and the MP4 has
  no text stream.
* English (the rules require English for all the submitted material), one
  short sentence per scene, **two lines at most**, at most 78 characters per
  line.
* The text is drawn in a band at the bottom of the picture (rows 880 to 1080)
  and the terminal content never reaches that band: a subtitle **never covers
  a line of code or of output**.
* White text on a dark band, font size 38 bold, with a blue accent line: the
  contrast is strong and the text is large.
* The shortest scene lasts **3.12 s**, so every subtitle stays on screen
  longer than the 2.5 s the filming rules ask for.
* The text says **what the viewer sees**, not a marketing claim.

The 19 subtitles are listed with their timings in
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
  (Windows, macOS, or Linux) that builds, tests, analyzes, or otherwise
  supports software targeting QNX 8.0". The argument is written out in
  [`../RULES.md`](../RULES.md) and in [`../docs/RULES.fr.md`](../docs/RULES.fr.md).
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
2. Check the target: `qcc -Vgcc_ntoaosdebug` must compile the examples.
3. Re-run `bash scripts/run_tests.sh` and `bash scripts/build_qcc.sh` up to date.
4. Record a **v3** with the target shot (the QNX 8.0 guest under QEMU), and
   keep the same subtitle rules.
5. Upload to YouTube with **public access** (a requirement of the rules) and
   provide the URL. — *one action by the owner, not by the automation.*
