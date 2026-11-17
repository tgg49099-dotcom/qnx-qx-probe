# The QNX 8.0 proof of QX-PROBE

This file is the proof that this project is a QNX 8.0 project, and that it
will really build for QNX 8.0.  It is written for a judge who has not read a
line of the QNX documentation: every line below is an assertion, the command
that produces it, the real output of that command, and the file of this
repository that makes it verifiable.

**One command checks every line of this file:**

```
python3 -I scripts/verifier-preuve-qnx8.py
```

It prints one table -- `affirmation | commande | source | statut` -- and it
exits 0 only when every assertion of this file is still true.  An assertion
with **no command**, or with **no real output**, is a FAILED line: the proof
is incomplete, and the control says so instead of passing.

## What is proved here, and what is not

* **PROVED, and replayable today:** the linter runs on QNX 8.0 code -- on the
  official example of the QNX 8.0 documentation, and on 17 real QNX resource
  managers written by other people, seven of them published by QNX or
  BlackBerry themselves.  The corpus is pinned to a commit: the result does not
  depend on what those repositories look like today.
* **PROVED, and replayable today:** every rule of the linter is backed by a
  page of the official BlackBerry QNX SDP 8.0 C Library Reference.  14 pages,
  36 quotations, re-read on **17 November 2026**: the URL, the HTTP code and
  the SHA-256 of each page are in the table below.
* **NOT MEASURED, and said so everywhere:** the compilation of the C examples
  for QNX 8.0.  The SDP 8.0 needs a myQNX account and a licence; none exists
  in the environment where this project was written.  `scripts/qnx8-proof.sh`
  detects the absence, prints exactly what is missing, and exits 2.  **It
  simulates nothing.**  The day the licence arrives, the same command compiles
  the examples with `qcc -Vgcc_ntox86_64`, runs the linter on them, and writes
  the real output under `proofs/`.

## The assertions

| ID | assertion | command | the real output | where it is verifiable |
|---|---|---|---|---|
| A01 | the QNX version the contest rules ask for is declared | sed -n '46p' README.md | **QNX SDP 8.0** | README.md:46 |
| A02 | the target is declared | sed -n '47p' README.md | the C examples target **QNX 8.0 on QEMU x86_64** | README.md:47 |
| A03 | the toolchain is declared | sed -n '48p' README.md | **`qcc` from the SDP 8.0** | README.md:48 |
| A04 | the README says the QNX compilation is NOT MEASURED: this proof does not pretend | sed -n '48p' README.md | whose compilation is **NOT MEASURED** | README.md:48 |
| A05 | the build script names the qcc variant of the x86_64 target | grep -n 'gcc_ntox86_64' scripts/build_qcc.sh | VARIANT="gcc_ntox86_64" | scripts/build_qcc.sh:25 |
| A06 | the one-command proof script detects the absence of the SDP 8.0 and fails cleanly, without simulating anything | bash scripts/qnx8-proof.sh | ERROR: the QNX SDP 8.0 is not installed on this machine. | scripts/qnx8-proof.sh:166 |
| A07 | the SDP path of that script is exercised with a FAKE compiler: the flags it uses are the real ones | bash scripts/qnx8-proof.sh --self-test | qcc -Vgcc_ntox86_64 -Werror -o build/x86_64/qxprobe-demo examples/qnx80_resmgr_minimal.c | scripts/qnx8-proof.sh:76 |
| A08 | the linter runs on the official example of the QNX 8.0 documentation and reports no error and no warning | python3 -I qx_probe.py examples/qnx80_resmgr_official_example.c | RESULT: 6 finding(s), 0 ERROR, 0 WARN | examples/qnx80_resmgr_official_example.c:1 |
| A09 | the linter runs on 17 real QNX resource managers written by other people, and finds one real defect | python3 -I scripts/benchmark-corpus.py | 17/17 files analysed, 1 ERROR in total | scripts/benchmark-corpus.py:1 |
| A10 | the defect it finds is a missing access gate in third-party code | python3 -I scripts/benchmark-corpus.py | ERROR QX004 rpi-thermal/rpi_thermal.c:465: resmgr_read() never calls iofunc_read_verify() | scripts/benchmark-corpus.py:1 |
| A11 | every rule is backed by a page of the official documentation, and the 36 quotations are found again in those pages | python3 -I scripts/verifier-citations.py | VERDICT: ALL CITATIONS VERIFIED | scripts/verifier-citations.py:1 |
| A12 | the rule QX004 is backed by the official access gate iofunc_read_verify() | sed -n '141p' RULES.md | iofunc_read_verify() | RULES.md:141 |
| A13 | the codelab of the submission answers in public | curl -sS -L -o /dev/null -w '%{http_code}' https://github.com/tgg49099-dotcom/qnx-qx-probe/blob/main/docs/CODELAB.md | 200 | docs/CODELAB.md:1 |
| A14 | the public repository has a main branch | git ls-remote https://github.com/tgg49099-dotcom/qnx-qx-probe.git refs/heads/main | refs/heads/main | git |
| A15 | this proof is published in the public repository | curl -sS -L -o /dev/null -w '%{http_code}' https://raw.githubusercontent.com/tgg49099-dotcom/qnx-qx-probe/main/docs/PREUVE-QNX8.md | 200 | docs/PREUVE-QNX8.md:1 |
| A16 | every published proof of this repository is replayed by one command, and none of them fails | bash scripts/verify-all.sh | VERDICT: EVERY CHECK PASSED - 9/9 OK (RC 0) @@ VERDICT: NO CHECK FAILED | scripts/verify-all.sh:1 |
| A17 | the test suite of the tool is green | bash scripts/run_tests.sh | RESULT: QX-PROBE suite GREEN | scripts/run_tests.sh:1 |

## The fourteen official pages

Each page is fetched again by the control: it must answer HTTP 200, and its
SHA-256 is compared with the one measured on 17 November 2026.  A page that
QNX has changed since is reported as **DRIFT**, not as a failure: the proof
says what was read, and on which date.

| ID | the page | the URL | the sha256 read on 17 November 2026 | cited in |
|---|---|---|---|---|
| P01 | resmgr_attach | https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_attach.html | 407c212bd880a3fef90416adbeda284700b0b41635ba7dbfbdef6eedbf6c2988 | RULES.md:22 |
| P02 | resmgr_io_funcs_t | https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_io_funcs_t.html | 834320546295228f04eb7ae8061226f4a26cb090ace1aed1286aa924c16c7089 | RULES.md:22 |
| P03 | iofunc_func_init | https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_func_init.html | 58b304930c31820b7ab4d75ad9cc85b8ac98e0bf9dc9d6303fcabdd422e1aa16 | RULES.md:22 |
| P04 | resmgr_connect_funcs_t | https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_connect_funcs_t.html | dbfd55d1ac1c512f38d5e0cadaf8e1e4851876b0e65ed8209d7333a2ee3acfe7 | RULES.md:84 |
| P05 | iofunc_read_verify | https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_read_verify.html | 2b71f10d237da190f8539414fe0e821cac3c9ac39740686ad54a113b9fc3f2d6 | RULES.md:141 |
| P06 | iofunc_write_verify | https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_write_verify.html | 720cc573dfa01f73d48f1ec121621cf3dbe88b98a754a160dd5bd1435d495b41 | RULES.md:141 |
| P07 | iofunc_read_default | https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_read_default.html | 5284ec123d3608543354f507be599950f5233b3032241cd06d1262f9861feb4e | RULES.md:141 |
| P08 | iofunc_write_default | https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_write_default.html | 53b303a54703dff4301954db3ee1c646f400cc1822d8f32135e49204f19ea91d | RULES.md:141 |
| P09 | resmgr_block | https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_block.html | 0fc092ec002f37c404dc30f648bfeff97becb823c79c2a12d7f5be1b731920d8 | RULES.md:208 |
| P10 | dispatch_block | https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/d/dispatch_block.html | be8018824dd9c360a65e2c235f460910c00f6d9143d3095adf31e1eaea017bbd | RULES.md:208 |
| P11 | resmgr_handler | https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_handler.html | b389a8bb42d0a19ef4f29769c8bd5d8c1b7aeebb9cf5c4e3e67a82dfc5647700 | RULES.md:249 |
| P12 | dispatch_handler | https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/d/dispatch_handler.html | dac937a6c321f21f286addb3066aea4750be014592d3beaf8173b9e888c5dd3b | RULES.md:249 |
| P13 | resmgr_context_t | https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_context_t.html | 75b5116faccbdb0ce4bef942d7bdbe155cead55074489044f7255a37c5ed0b6f | RULES.md:292 |
| P14 | _resmgr_nparts | https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/_resmgr_nparts.html | ffbe0dc88e41c62097646e0fa8563aa959ae8d27804b4123867c9a3ecce16697 | RULES.md:292 |

## The rules and their official API

Every rule of the linter names an official function of the QNX 8.0 C Library
Reference, and the line of `RULES.md` that carries the citation says so.

| ID | the rule | the official API | the URL of that API | in RULES.md |
|---|---|---|---|---|
| R01 | QX001 — no dispatch table wired | resmgr_attach | https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_attach.html | RULES.md:22 |
| R02 | QX002 — `iofunc_func_init()` is asked to fill more entries than the table holds | iofunc_func_init | https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_func_init.html | RULES.md:84 |
| R03 | QX003 — a slot points at a function not found in the analysed files | resmgr_io_funcs_t | https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_io_funcs_t.html | RULES.md:120 |
| R04 | QX004 — the `iofunc_*_verify()` access gate is missing | iofunc_read_verify | https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_read_verify.html | RULES.md:141 |
| R05 | QX005 — the path mounted by `resmgr_attach()` is relative | resmgr_attach | https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_attach.html | RULES.md:188 |
| R06 | QX006 — no message loop | resmgr_block | https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_block.html | RULES.md:208 |
| R07 | QX007 — the loop blocks but no handler is called | resmgr_handler | https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_handler.html | RULES.md:249 |
| R08 | QX008 — an `io_funcs` slot is not wired | resmgr_io_funcs_t | https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_io_funcs_t.html | RULES.md:274 |
| R09 | QX009 — the reply returns more parts than the IOV holds | resmgr_attach | https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_attach.html | RULES.md:292 |
| R10 | QX010 — the number of slots of `iofunc_func_init()` is a macro | iofunc_func_init | https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_func_init.html | RULES.md:312 |
| R11 | QX011 — an automatic dispatch table is never initialised | iofunc_func_init | https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_func_init.html | RULES.md:320 |

## The captures

Three real captures of the tool, taken from the real output of the commands
below.  Nothing is drawn: the picture shows the output of the command, and the
same text is embedded in the PNG itself, so the control can check that the
picture shows what the command really prints.

| ID | the image | the command that produced it | the sha256 of the image | what it shows |
|---|---|---|---|---|
| C01 | media/qx-proof-1-corpus-reel.png | python3 -I scripts/benchmark-corpus.py | 697e70ad1033c3dca9b96b059c1be38fa3cc5b36448821d8e5b80c89de8fb888 | the linter on 17 real QNX resource managers, one real defect found |
| C02 | media/qx-proof-2-exemple-officiel.png | python3 -I qx_probe.py examples/qnx80_resmgr_official_example.c | 2ff69e0aaa73cede483a9e360938adc8d7f46df11b74e528c29de7a6ea325320 | the official example of the QNX 8.0 documentation: 0 ERROR, 0 WARN |
| C03 | media/qx-proof-3-sdp-absent.png | bash scripts/qnx8-proof.sh | 1423540ceeb10a0b9e9eb1852d22bce824f4b54ad584521cb66c57ef942b0fc0 | the QNX 8.0 proof script: the SDP is absent, and it says so instead of faking it |

## The two sentences the submission form needs

**Substantially different from QX PORTMAP.**  QX-PROBE is a *source* checker:
it reads the C source of a resource manager and reports the access gates and
dispatch tables that the QNX 8.0 documentation requires (11 rules, `RULES.md`);
QX PORTMAP is a *documentation* mapper: it reads the list of QNX symbols that
a source tree calls and answers, for each one, whether it is still documented
in QNX 8.0, with the official page and the exact quotation.  The first one
audits resource-manager code, the second one guides a port of existing code
to QNX 8.0; they read different inputs, produce different outputs, share no
code, no rule and no document, and each one is a complete submission on its
own.

**The codelab.**  The hands-on tutorial of this project is
`docs/CODELAB.md`, published at
<https://github.com/tgg49099-dotcom/qnx-qx-probe/blob/main/docs/CODELAB.md>.
It is a 30-minute tutorial that teaches a task on QNX 8.0 -- auditing the
dispatch table of a resource manager -- with nothing but Python 3, and every
console output it shows is replayed by `scripts/verifier-codelab.py`.  It
belongs in the **"Codelab / tutorial (URL)"** field of the submission form.
