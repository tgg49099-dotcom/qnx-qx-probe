# QX-PROBE — a static checker for the QNX 8.0 resource-manager protocol

QX-PROBE reads C code and reports the **false positives you cannot afford**
in a QNX 8.0 driver: a resource manager that never calls
`iofunc_read_verify()`, a message loop that blocks without dispatching, a
reply that returns more parts than the IOV holds.

It is a **host** tool: it runs on Linux, macOS or Windows, it has **no
dependency** and it asks for **neither a QNX SDK nor a QNX board**. That is
what makes it usable in a continuous-integration chain, or for a jury that
has no hardware.

```console
$ python3 -I qx_probe.py examples/qnx80_resmgr_minimal.c
INFO  QX008  examples/qnx80_resmgr_minimal.c: io_funcs.devctl is not assigned (the POSIX default iofunc_devctl_default() applies unless you override it)
...
RESULT: 5 finding(s), 0 ERROR, 0 WARN
```

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
page (the cited pages were updated on 11 June 2026). The detail, rule by
rule, with the quotation and the URL, is in **[RULES.md](RULES.md)**.

## The eleven rules

| Code | What the linter reports | Level | Official QNX 8.0 source |
|---|---|---|---|
| QX001 | the file uses the resmgr API but wires no dispatch table (or attaches a NULL one) | ERROR | `resmgr_attach()` |
| QX002 | `iofunc_func_init()` is asked to fill more entries than the table holds | ERROR | `iofunc_func_init()` |
| QX003 | a slot points at a function not found in the analysed files | INFO | `resmgr_io_funcs_t()` |
| QX004 | a `read`/`write` handler does not call `iofunc_*_verify()` | ERROR | `iofunc_read_verify()` |
| QX005 | the path mounted by `resmgr_attach()` is **relative** | WARN | `resmgr_attach()` |
| QX006 | no message loop (`dispatch_block()`/`resmgr_block()`) | ERROR | `resmgr_block()` |
| QX007 | the loop blocks but no handler is called | ERROR | `resmgr_handler()` |
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

### What was corrected in this version

Five rules (QX001, QX002, QX003, QX004, QX011) had a known defect that
contradicted the official documentation. They are now corrected, and each
correction is covered by a test that **fails on the previous code** and
**passes on the current one** — a rule that was simply deleted would prove
nothing. The rule-by-rule description is in
**[RULES.md](RULES.md)**, section "What was corrected in this version, and
how it is proved".

## What is in the repository

```
qx_probe.py                          the linter (one file, no dependency)
RULES.md                             each rule + its official QNX 8.0 source
CODELAB.md                           the hands-on tutorial (30 minutes, no SDK needed)
examples/qnx80_resmgr_minimal.c      canonical resource manager (written for this repository)
examples/qnx80_resmgr_readonly.c     read-only, mounted outside /dev/
examples/qnx80_resmgr_relative_path.c  triggers exactly one QX005 warning
examples/qnx80_resmgr_official_example.c  the official example of the QNX 8.0 documentation
examples/blackberry_eventfd_mgr.c    BlackBerry's public resource manager (Apache-2.0)
tests/test_qx_probe.py               27 tests: 10 anti-false-positive, 15 detection, 2 output format
tests/fixtures/qnx80_resmgr_qx004_no_gate.c  the sabotaged file used by the tests and the video
scripts/run_tests.sh                 runs the test suite
scripts/verifier-codelab.py          replays every command of CODELAB.md and checks its output
scripts/build_qcc.sh                 QNX 8.0 build (requires the SDP 8.0)
video/SCENARIO.md                    the video demonstration scenario
media/qx-demo-v1.mp4                 the demonstration video itself (MP4, H.264, 1920x1080, 44.48 s)
docs/README.md                       what the files under docs/ are
docs/README.fr.md                    the French original of this file
docs/RULES.fr.md                     the French original of RULES.md
docs/SCENARIO.fr.md                  the French original of video/SCENARIO.md
```

The three files under `docs/` are the **original French versions**, kept
unmodified so the translation can be checked side by side. The English files
are the ones the contest rules require; the French ones are the reference.
`CODELAB.md` is not a translation but a document written directly in English,
because the contest rules require the submitted material to be in English.

## The hands-on codelab

**[CODELAB.md](CODELAB.md)** — a 30-minute tutorial that teaches a task on
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

## The demonstration video

`media/qx-demo-v1.mp4` — 907 244 bytes, MP4 / H.264, 1920x1080, 25 fps,
44.48 s, no audio track (md5 `3558d267dfebc54c275c2c879787b76b`).

Every command shown in the video is a command of this repository, so the
jury can replay them as they are: the checker passes on BlackBerry's own
public resource manager and on the official example of the QNX 8.0
documentation, it catches the missing access gate in a deliberately broken
fixture, and it returns a non-zero exit code — the CI gate. The shot that
compiles the examples with `qcc` and runs them on a QNX 8.0 guest under QEMU
is **absent**: it needs the QNX SDP 8.0 licence, which we do not have. It
was **removed** from the video rather than replaced with a screen capture,
and **no compiler output was simulated**. The shot list and the honest
reservations about it are in **[video/SCENARIO.md](video/SCENARIO.md)**.

## Licence

QX-PROBE code: Apache-2.0 (see `LICENSE`).
The example `examples/blackberry_eventfd_mgr.c` and the header
`examples/sys/eventfd.h` come from BlackBerry's public `shim-demo`
repository and are under Apache-2.0; the full licence header is kept at the
top of each file and the notice is in `NOTICE`.

AI assistance: this project was written with the assistance of a language
model. The official QNX 8.0 documentation and BlackBerry's public reference
code are the only factual sources cited.
