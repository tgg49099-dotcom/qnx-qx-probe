# DevPost submission text — QX-PROBE (QNX Global Hackathon)

**Everything between a `<!-- DEBUT:… -->` and a `<!-- FIN:… -->` marker is the
text to paste into the submission form, as it is, in English.** Nothing else in
this file has to be pasted: the text outside the markers tells the entrant
where each block goes, how long it is, and where every figure comes from.

Three rules this file obeys:

1. **No figure is invented.** Every number is measured on the public
   repository (§ 12 lists them with the command that produced them), or the
   words `NOT MEASURED` are written.
2. **No promise of conformity.** QX-PROBE is a *linter*: it reports what its
   rules can prove and stays silent about the rest. The word "compliant" never
   appears about the tool.
3. **Nothing is hidden.** What the QNX 8.0 compilation has not been measured,
   the video does not show and the tool does not do, is written as it is.

---

## 0. Where each block goes

| § | Block | Field of the submission form | Limit |
|---|---|---|---|
| 1 | `TITRE` | Project title | 60 characters |
| 2 | `TAGLINE` | Short description / tagline | 300 characters |
| 3 | `CATEGORIE` | Category — **one** choice | — |
| 4 | `BUILTWITH` | Built with + tags | — |
| 5 | `WHATITDOES` | "About the project" / "What it does" | 1 200 characters |
| 6 | `WHY` | "Why we built it" | — |
| 7 | `HOW` | "How we built it" | — |
| 8 | `WHATSNEXT` | "What's next" | — |
| 9 | `TESTING` | "Testing instructions" | — |
| 10 | `BUILD` | "Build and run instructions" | — |
| 11 | `QXUSE` | "Evidence of QNX use" | — |
| 12 | `LIENS` | "Try it out" (URL), video URL, codelab URL | — |
| 13 | `REGLES11` | the eleven rules, one sentence each | — |
| 14 | `RESUME5` | five sentences for the repository README | — |

> If the form shows a **single long description field** instead of the four
> rubrics of § 5 to § 8, paste them in this order: `WHATITDOES`, then `WHY`,
> then `HOW`, then `WHATSNEXT`. `WHATITDOES` alone already fills the
> 1 200-character field, so put it in the dedicated field.

---

## 1. Title

<!-- DEBUT:TITRE -->
QX-PROBE: a linter for QNX 8.0 resource managers
<!-- FIN:TITRE -->

_Measured: 48 characters (DevPost limit: 60)._

## 2. Tagline

<!-- DEBUT:TAGLINE -->
QX-PROBE reads your QNX 8.0 resource-manager C code and reports the protocol
mistakes the compiler cannot see. Zero dependencies, no QNX SDK, no hardware.
Every rule cites the official QNX 8.0 page it comes from.
<!-- FIN:TAGLINE -->

_Measured: 212 characters (DevPost limit: 300)._

## 3. Category

**Tick exactly one: `Developer Tooling & Host Tools`.**

The rules say: *"Each Entrant must select one (1) of the following categories"*
and describe this one as *"a host-based tool (Windows, macOS, or Linux) that
builds, tests, analyzes, or otherwise supports software targeting QNX 8.0"*.
QX-PROBE is exactly that: a host tool, with no QNX board, no SDK and no cost.

The other four categories — Robotics & Medical, Automotive & Mobility,
Low-level Software, Open-Source Contribution & Ports — do not describe this
project: it is not a robot, not a vehicle, not a low-level driver, and it is
not a port of an upstream project.

## 4. Built with / tags / try it out

<!-- DEBUT:BUILTWITH -->
Built with: C, Python  (the project is a Python 3 linter that reads C source)

Technologies: QNX 8.0, QNX SDP 8.0 (host tools, qcc), Python 3 (standard
library only), static analysis, CI

Tags: QNX, QNX 8.0, static analysis, linter, developer tooling,
resource manager, CI

Try it out: https://github.com/tgg49099-dotcom/qnx-qx-probe
<!-- FIN:BUILTWITH -->

_Measured: 333 characters._

> If the form offers a limited number of tags, keep this order: `QNX`,
> `static analysis`, `developer tooling`, `linter`, `CI`.

## 5. "What it does" — the description field

<!-- DEBUT:WHATITDOES -->
A QNX 8.0 resource manager is where the expensive bugs live. Drop the iofunc_read_verify() call and a client can read what it should not. Block in the dispatch loop without dispatching and the client hangs. Return more parts in a reply than the IOV holds and the answer is corrupted. The compiler sees none of it.

QX-PROBE is a single-file, dependency-free linter for QNX 8.0 resource-manager C code. It runs on Linux, macOS or Windows, needs no QNX SDK or hardware, so it fits in CI. It has 11 rules, and each rule cites the official BlackBerry QNX SDP 8.0 documentation page it comes from.

Five rules had a defect that contradicted the documentation; they are corrected, and each correction is covered by a test that fails on the previous code and passes on the current one.

It is a linter, not a certifier: it reports what its rules can prove and stays silent about the rest.

Install: clone, then run python3 -I qx_probe.py your_resmgr.c. Nothing to build.

Evaluate it in a minute: bash scripts/run_tests.sh runs 27 tests and exits 0. python3 -I qx_probe.py examples/blackberry_eventfd_mgr.c runs it on BlackBerry's own published resource manager: 5 findings, 0 errors, 0 warnings.
<!-- FIN:WHATITDOES -->

_Measured: 1189 characters (DevPost limit: 1 200)._

## 6. "Why we built it"

<!-- DEBUT:WHY -->
A QNX 8.0 resource manager is the part of a system that owns a device: the automotive ECU, the train controller, the medical ventilator. Its protocol is written in prose, and the mistakes that matter most are invisible to the compiler.

Forget the access gate and a client reads what it must not. Block in the dispatch loop without dispatching and the client waits forever. Return more parts than the IOV holds and the reply is corrupted. In each case the code compiles, links, boots and passes review: iofunc_read_verify() is an ordinary function call that returns an int, so the compiler has nothing to say.

The teams who write these drivers are usually small teams whose expertise is the product, not the QNX resource-manager protocol. Nothing in the toolchain tells them that a read handler is missing its access gate, so the defect is found in the field — on a vehicle, in a hospital — instead of in the build.

QX-PROBE moves that check into the build, on any machine, with no SDK, no board and no licence. It is deliberately narrow: eleven rules, each backed by a page of the official BlackBerry QNX SDP 8.0 documentation, and nothing it cannot justify.
<!-- FIN:WHY -->

_Measured: 1161 characters._

## 7. "How we built it"

<!-- DEBUT:HOW -->
QX-PROBE is one Python 3 file — 671 lines, standard library only (re, sys, dataclasses) — that reads the C source of a resource manager and reports what it can prove. The QNX 8.0 resource-manager protocol is not expressed in a type system, so the analysis is done on the text of the code, with the comments and the string literals blanked before the search: a gate merely quoted inside an error message is not mistaken for a gate.

The hard part was not the detection, it was the silence. A linter for a real-time operating system that reports canonical code by mistake is worse than no linter at all: five of the first rules did exactly that, and they were rewritten. Every rule now cites the official documentation page it comes from, with the sentence it relies on and what it does not do. Every rule has a test that fails on the previous code and passes on the current one — a rule that was simply deleted would prove nothing. And the rule set is checked against BlackBerry's own public resource manager (Apache-2.0), which must stay green: 0 errors, 0 warnings.

The suite is 27 tests — 10 anti-false-positive, 15 detection, 2 output format — and it is a two-sided contract: valid code must produce no actionable finding, broken code must produce the expected one.

The tutorial that teaches the protocol is checked the same way: scripts/verifier-codelab.py replays every command of the codelab in a throw-away copy of the repository and compares the real output with the output printed in the tutorial — 12 blocks replayed, 0 differing.
<!-- FIN:HOW -->

_Measured: 1542 characters._

## 8. "What's next"

<!-- DEBUT:WHATSNEXT -->
Three things, in this order.

1. Measure the QNX 8.0 build. The repository already contains a real build path for the example resource managers (scripts/build_qcc.sh, qcc -Vgcc_ntoaosdebug -Werror, targets x86_64, aarch64 and armv7), but it has never been run against a real qcc: the SDP 8.0 licence was not available where this project was written, so the compilation is honestly labelled NOT MEASURED in the repository and in this submission. With the SDK we will compile the examples for QNX 8.0, run them in a QEMU guest, and add that build to the continuous-integration chain.

2. Take the check to the target. The linter reads the source today; the next step is to run the same eleven rules on the QNX side, where a resource manager can report its own protocol at start-up.

3. Widen the coverage. The resource-manager protocol is the first QNX 8.0 interface covered here; message passing and the network interfaces follow, under the same rule: a rule that cannot be justified by an official QNX 8.0 page is removed rather than kept.
<!-- FIN:WHATSNEXT -->

_Measured: 1039 characters._

## 9. Testing instructions

The rules require it: *"Access must be provided to an Entrant's working Project
for judging and testing by providing a link to a public code repository"* and
*"The Entrant must make the Project available free of charge and without any
restriction, for testing, evaluation and use by the Sponsor, Administrator and
Judges"*. Here is the whole procedure, in **three commands**.

<!-- DEBUT:TESTING -->
QX-PROBE is a host tool: there is nothing to install, nothing to build and
nothing to pay for.

REQUIREMENTS
  Python 3 (the standard library only). No QNX SDK, no QNX board, no QEMU,
  no network access, no licence.

1) GET THE PROJECT
   git clone https://github.com/tgg49099-dotcom/qnx-qx-probe.git
   cd qnx-qx-probe
   Measured: 1.4 s, 2.1 MB.

2) RUN THE TEST SUITE
   bash scripts/run_tests.sh
   Measured: 0.47 s. Expected output:
     Ran 27 tests in 0.119s
     OK
     RESULT: QX-PROBE suite GREEN (RC 0)
   The 27 tests are the two-sided contract: 10 of them prove that valid
   QNX 8.0 code produces no actionable finding, 15 prove that a broken file
   produces the expected finding, 2 check the format of the output.

3) RUN THE TOOL ON A REAL QNX 8.0 RESOURCE MANAGER
   python3 -I qx_probe.py examples/blackberry_eventfd_mgr.c
   Measured: 0.06 s. Expected output (last line):
     RESULT: 5 finding(s), 0 ERROR, 0 WARN
   Exit code 0. The file it analyses is BlackBerry's own published resource
   manager, shipped in the repository under Apache-2.0. The five findings are
   INFO lines that describe the code (three unwired io_funcs slots, two
   macro counts); they do not condemn it and do not change the exit code.

   To see the tool catch a real defect, run it on the sabotaged fixture:
     python3 -I qx_probe.py tests/fixtures/qnx80_resmgr_qx004_no_gate.c
     RESULT: 6 finding(s), 1 ERROR, 0 WARN      (exit code 1)

EXIT CODES
  0 = no actionable finding
  1 = at least one ERROR or one WARN
  2 = malformed call
  INFO findings never change the exit code.

The whole procedure takes less than three seconds on a modern laptop.
<!-- FIN:TESTING -->

_Measured: 1657 characters._

> The three commands are the ones a judge has to type. Everything else in the
> repository — the eleven rules with their official QNX 8.0 source pages
> ([RULES.md](../RULES.md)), the tutorial
> ([docs/CODELAB.md](CODELAB.md)), the shot list of the video
> ([video/SCENARIO.md](../video/SCENARIO.md)) — is there for the judge who
> wants to go further.

## 10. Build and run instructions (QNX 8.0)

The rules require: *"Include build and run instructions specifying the QNX
version, the target (hardware or QEMU), and the toolchain used."*

<!-- DEBUT:BUILD -->
  THE SUBMITTED TOOL (qx_probe.py) - a host tool: nothing to build, and
  nothing to execute on a target.

    QNX version : 8.0 - it analyses QNX 8.0 resource-manager source code
    Target      : none to execute - it reads .c files, it never runs on the
                   target
    Toolchain   : Python 3, standard library only (re, sys, dataclasses)
    Install     : git clone https://github.com/tgg49099-dotcom/qnx-qx-probe.git
                   then python3 -I qx_probe.py your_resmgr.c

  THE C EXAMPLES - a real QNX 8.0 build path:

    bash scripts/build_qcc.sh [x86_64|aarch64|armv7]

    QNX version : 8.0 (QNX SDP 8.0 host tools)
    Target      : x86_64 by default - a QNX 8.0 guest running under QEMU.
                   aarch64 and armv7 are also accepted as arguments.
    Toolchain   : qcc -Vgcc_ntoaosdebug -Werror (the SDP 8.0 compiler)

    This script REQUIRES the QNX SDP 8.0 and a non-commercial QNX Everywhere
    licence (myQNX account). Without qcc it stops with an explicit error message
    and exit code 2, and it never simulates compiler output or produces a fake
    binary.

    NOT MEASURED: we do not hold an SDP 8.0 licence yet, so this build has not
    been executed against a real qcc. The script is prepared and its "no SDK"
    path is verified; the successful compilation is not.

    RUN IT ON THE TARGET: the example mounts /dev/qxprobe-demo; on a QNX 8.0
    guest, read it with cat /dev/qxprobe-demo.
<!-- FIN:BUILD -->

_Measured: 1448 characters._

## 11. Evidence of QNX use

<!-- DEBUT:QXUSE -->
The QNX connection is the product itself, not a mention of QNX in a README.

  - The tool analyses the C source of QNX 8.0 resource managers and knows the
    QNX 8.0 resource-manager protocol: resmgr_attach(), resmgr_context_t(),
    iofunc_func_init(), iofunc_read_verify(), iofunc_write_verify(),
    dispatch_block()/resmgr_block(), dispatch_handler()/resmgr_handler(),
    _RESMGR_NPARTS().
  - Every one of the 11 rules cites the official BlackBerry QNX SDP 8.0
    documentation page it comes from, with the URL and the exact sentence it
    relies on. The 12 pages cited were all reachable on 6 November 2026 and
    all carry "Page updated: June 11, 2026".
  - The reference corpus used to validate the tool is BlackBerry's own public
    Apache-2.0 resource manager (examples/blackberry_eventfd_mgr.c), which the
    linter must report with 0 errors and 0 warnings.
  - The repository contains a real QNX 8.0 build path: scripts/build_qcc.sh
    compiles the example resource managers with qcc -Vgcc_ntoaosdebug -Werror
    for x86_64, aarch64 or armv7.
  - The output of the tool is what a QNX developer needs: the findings name the
    file, the line, the QNX API involved and the official documentation page.

  The rules describe a host-based developer tool as eligible when it offers
  "output or functionality specifically intended to build, analyze, test,
  deploy, debug, or manage software for QNX 8.0". That is what this tool is:
  its output is the QNX 8.0 resource-manager protocol, rule by rule.
<!-- FIN:QXUSE -->

_Measured: 1518 characters._

## 12. Links

<!-- DEBUT:LIENS -->
Public repository (judging and testing):
  https://github.com/tgg49099-dotcom/qnx-qx-probe

Licence (Apache-2.0, visible in the "About" section of the repository page):
  https://github.com/tgg49099-dotcom/qnx-qx-probe/blob/main/LICENSE
Notice and attribution (the BlackBerry example used as the reference corpus):
  https://github.com/tgg49099-dotcom/qnx-qx-probe/blob/main/NOTICE
The eleven rules and their official QNX 8.0 sources:
  https://github.com/tgg49099-dotcom/qnx-qx-probe/blob/main/RULES.md
Codelab / tutorial (30 minutes, no SDK, no board, no licence):
  https://github.com/tgg49099-dotcom/qnx-qx-probe/blob/main/docs/CODELAB.md
Demonstration video (71.44 s, English subtitles burned in, under the
three-minute limit of the rules):
  - YouTube: the rules require the video to be uploaded there and made
    publicly visible. PASTE THE URL OF THE UPLOAD HERE:
    <YOUTUBE_URL_A_COLLER_apres_le_televersement>
  - the same file, already in this repository:
    https://github.com/tgg49099-dotcom/qnx-qx-probe/blob/main/media/qx-demo-v2.mp4
  - direct download:
    https://raw.githubusercontent.com/tgg49099-dotcom/qnx-qx-probe/main/media/qx-demo-v2.mp4
The text of this submission, field by field:
  https://github.com/tgg49099-dotcom/qnx-qx-probe/blob/main/docs/SUBMISSION-EN.md
Official QNX 8.0 documentation:
  https://www.qnx.com/developers/docs/8.0/
Origin of the reference example:
  https://gitlab.com/qnx/projects/shim-demo
<!-- FIN:LIENS -->

_Measured: 1445 characters._

**The video field.** The rules require the demonstration video to be *"uploaded
to and made publicly visible on YouTube"* with *"a link to the video ... provided
on the submission form"*. The file is ready and verified — 1 367 966 bytes,
MP4 / H.264, 1920x1080, 25 fps, **71.44 s** (the limit is three minutes), **no
audio track at all** and every sentence **burned into the picture** as an
English subtitle — it is already in the public repository, downloadable from
the URL above. What remains is to upload it to YouTube as a public video and
paste that YouTube URL in the video field of the form. The video is **in
English**, as the rules require, and every command it shows is a command of
the repository, so the judge can replay them as they are.

**The codelab field.** The rules ask, for the "Best Codelab/Tutorial" bonus,
for *"the URL of a codelab or tutorial authored during the Submission Period
that teaches the reader how to perform a task on or for QNX 8.0"*. The URL to
paste is the one above; it is a file of the public repository, so it is public
by construction. It teaches one task on QNX 8.0 — auditing the dispatch table
of a resource manager — in about thirty minutes, with nothing but Python 3.

## 13. The eleven rules, one sentence each

<!-- DEBUT:REGLES11 -->
QX001 (ERROR) — the file uses the QNX resmgr API but wires no dispatch table (none declared, initialised, filled by iofunc_func_init() or passed to resmgr_attach()), or passes a NULL table to resmgr_attach().
QX002 (ERROR) — iofunc_func_init() is asked to fill more entries than the table holds (more than 34 for the io table, more than 8 for the connect table), so the library writes past the end of the structure.
QX003 (INFO) — a slot of the dispatch table points at a function that is neither defined nor declared in the analysed files; if it is not defined in another translation unit, the link will fail.
QX004 (ERROR) — a read or write handler never calls iofunc_read_verify() or iofunc_write_verify(): the access gate is missing.
QX005 (WARN) — resmgr_attach() mounts a relative path, which QNX resolves against the current working directory.
QX006 (ERROR) — no message loop: neither dispatch_block() nor resmgr_block() is called, so the resource manager never waits for a message.
QX007 (ERROR) — the message loop blocks (dispatch_block()/resmgr_block()) but no handler is called (neither dispatch_handler() nor resmgr_handler()).
QX008 (INFO) — a slot of the io_funcs table is left unwired: the documented POSIX default applies, except for notify, for which QNX 8.0 defines none.
QX009 (ERROR) — a handler returns _RESMGR_NPARTS(k) with k greater than attr.nparts_max, so the answer carries more parts than the IOV array holds.
QX010 (INFO) — the number of entries given to iofunc_func_init() is a macro, not a literal; no conclusion is drawn from it.
QX011 (WARN) — a dispatch table declared as an automatic variable is never initialised, so its function pointers hold indeterminate values.
<!-- FIN:REGLES11 -->

_Measured: 1701 characters._

The official QNX 8.0 page behind each rule, the sentence it relies on and what
it does not do are in [RULES.md](../RULES.md) — one section per rule, with the
URL of the page.

## 14. Five sentences for the repository README

<!-- DEBUT:RESUME5 -->
QX-PROBE is a static checker for the QNX 8.0 resource-manager protocol: it reads your C source and reports the protocol mistakes the compiler cannot see. It has eleven rules, and every one of them cites the official BlackBerry QNX SDP 8.0 documentation page it comes from. It runs on Linux, macOS or Windows with zero dependencies — no QNX SDK, no board, no licence — so it fits in a continuous-integration chain. Five of its first rules had a defect that contradicted the documentation; they were rewritten, and each correction is proved by a test that fails on the previous code. The 27-test suite is a two-sided contract: valid code must produce no actionable finding, broken code must produce the expected one.
<!-- FIN:RESUME5 -->

_Measured: 714 characters._

## 15. The remaining questions of the form

| Question | Answer |
|---|---|
| Category | **Developer Tooling & Host Tools** (one category only). |
| New or existing project? | **New.** The project was created during the submission period (2 November – 15 December 2026). |
| Try it out (URL) | `https://github.com/tgg49099-dotcom/qnx-qx-probe` |
| Demonstration video (URL) | The **YouTube** URL, once uploaded as a public video. The file is already in the repository: `https://raw.githubusercontent.com/tgg49099-dotcom/qnx-qx-probe/main/media/qx-demo-v2.mp4` (71.44 s, MP4 / H.264, 1920x1080, 25 fps, no audio, English subtitles burned in). |
| Codelab / tutorial (URL) | `https://github.com/tgg49099-dotcom/qnx-qx-probe/blob/main/docs/CODELAB.md` |
| Licence | Apache-2.0, the full text in `LICENSE` at the root of the repository, visible in the "About" section of the repository page. |
| Attribution | `examples/blackberry_eventfd_mgr.c` and `examples/sys/eventfd.h` come from BlackBerry Limited's public `shim-demo` repository, under Apache-2.0, *Copyright (c) 2025, BlackBerry Limited*. They are redistributed **without any modification**, with the full licence header kept at the top of each file. The notice is in `NOTICE`. The example is used as the reference corpus: it is resource-manager code published by the vendor itself, and the linter must report it without a false positive. |

## 16. How the answers speak to the four judging criteria

The rules say the submissions are judged on four equally weighted criteria.
This is the mapping, so that nothing is left to chance.

| Criterion | Where it is answered |
|---|---|
| **Technological Implementation** | § 7: a real analyser, 671 lines, no dependency, eleven rules each backed by an official QNX 8.0 page, a two-sided test suite of 27 tests, and a QNX 8.0 build path (`qcc -Vgcc_ntoaosdebug -Werror`) that is labelled NOT MEASURED rather than faked. |
| **Design** | § 5, § 9 and § 12: one command to install, three commands to evaluate, one exit code to plug into CI, a repository where the rules, the tutorial and the submission text are written for the judge. |
| **Potential Impact** | § 6: the access gate that lets a client read what it must not, in the automotive, medical and industrial systems where QNX runs; the check moves from the field to the build, at no cost and without hardware. |
| **Innovation & AI Creativity** | The unusual half of the method: the tool is built so that a rule which cannot be justified by an official QNX 8.0 page is **removed** rather than kept, and the rules known to be imperfect are published as such, limits included. The AI assistance is declared in the README and in the NOTICE, and the only factual sources are the official documentation and BlackBerry's public code. |

## 17. Where every figure comes from

Measured on the public repository on **6 November 2026**.

| Figure | Value | How it was measured |
|---|---|---|
| Test suite | 27 tests, RC 0 (10 anti-false-positive, 15 detection, 2 output format) | `bash scripts/run_tests.sh` |
| BlackBerry's resource manager | 5 findings, 0 ERROR, 0 WARN, exit 0 | `python3 -I qx_probe.py examples/blackberry_eventfd_mgr.c` |
| Minimal example | 5 findings, 0 ERROR, 0 WARN, exit 0 | `python3 -I qx_probe.py examples/qnx80_resmgr_minimal.c` |
| Read-only example | 6 findings, 0 ERROR, 0 WARN, exit 0 | `python3 -I qx_probe.py examples/qnx80_resmgr_readonly.c` |
| Relative-path example | 7 findings, 0 ERROR, 1 WARN (QX005), exit 1 | `python3 -I qx_probe.py examples/qnx80_resmgr_relative_path.c` |
| Official example of the documentation | 6 findings, 0 ERROR, 0 WARN, exit 0 | `python3 -I qx_probe.py examples/qnx80_resmgr_official_example.c` |
| Sabotaged fixture | 6 findings, 1 ERROR (QX004), 0 WARN, exit 1 | `python3 -I qx_probe.py tests/fixtures/qnx80_resmgr_qx004_no_gate.c` |
| Codelab | 12 console blocks replayed, 0 differing, RC 0 | `python3 -I scripts/verifier-codelab.py` |
| Official QNX 8.0 pages cited | 12 distinct pages, all HTTP 200 on 06/11/2026, all marked "Page updated: June 11, 2026" | `curl` on each URL of `RULES.md` |
| The linter | 671 lines, standard library only (`re`, `sys`, `dataclasses`) | `wc -l qx_probe.py`, `grep -n "^import\|^from" qx_probe.py` |
| Video | 1 367 966 bytes, md5 `178e1b58638628a5bc56f11c6fada8e2`, 71.44 s, 1920x1080, H.264, 25 fps, 1786 images, no audio, 19 burned-in subtitles | `md5sum`, `ffprobe` on the file of the repository |
| Timing of the three commands | clone 1.4 s (2.1 MB), test suite 0.47 s, run on one file 0.06 s | `time` on each command |
| QNX 8.0 compilation | **NOT MEASURED** | no SDP 8.0 licence in the environment where the project was written; `scripts/build_qcc.sh` stops with an explicit message and exit code 2 |

### The rules this submission answers, quoted

From the QNX Global Hackathon rules, "Submission Requirements" and "Testing":

> Provide a URL to your public code repository for judging and testing on
> either GitHub, GitLab, or Bitbucket. […] The repository must be public and
> open source by including an open source license file. This license should be
> detectable and visible at the top of the repository page (in the About
> section).

> The repository must show that the project genuinely builds for or runs on
> QNX 8.0, not merely that QNX 8.0 is named in the README.

> Include build and run instructions specifying the QNX version, the target
> (hardware or QEMU), and the toolchain used.

> must be uploaded to and made publicly visible on YouTube and a link to the
> video must be provided on the submission form on the Hackathon Website.

> Evidence of QNX use: […] for host-based developer tools, output or
> functionality specifically intended to build, analyze, test, deploy, debug,
> or manage software for QNX 8.0.

> Testing — Access must be provided to an Entrant's working Project for
> judging and testing by providing a link to a public code repository as
> described above.

> All Submission materials must be in English or, if not in English, the
> Entrant must provide an English translation of the demonstration video, text
> description, and testing instructions as well as all other materials
> submitted.

> Best Codelab/Tutorial — […] the Entrant must provide the URL of a codelab
> or tutorial authored during the Submission Period that teaches the reader
> how to perform a task on or for QNX 8.0.
