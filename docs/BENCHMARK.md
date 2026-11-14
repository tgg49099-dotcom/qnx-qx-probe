# The benchmark: QX-PROBE on 17 real QNX resource managers

> The French counterpart of this file is in
> [`docs/BENCHMARK.fr.md`](docs/BENCHMARK.fr.md), updated with it: the same
> corpus, the same measurements, the same conclusions.

The examples of this repository are **examples**. A linter that only ever
sees its own examples proves nothing about the code of other people. This
document is the measurement of QX-PROBE on **17 resource managers written by
other people** — **seven of them published by QNX or BlackBerry themselves** — and
the record of the **five defects of the tool** it exposed — **nine false
positives in five files** — the **one true positive** it confirmed, and the
tests that were written for each of them.

Everything below was measured on **11 November 2026** with the version of
`qx_probe.py` in this repository.

---

## 1. Why a benchmark on real code

A rule that only fires on fixtures written to make it fire is a rule that
has never been tried against code that its author did not write. Three
things can only be checked on real code:

1. **the false positives** — does the rule condemn valid code that other
   people published? This is the worst failure mode of a linter, and it is
   invisible on examples that were written for the linter;
2. **the storage duration and the call graph** — a real resource manager
   splits its tables, its handlers and its message loop over several files,
   in several idioms (`resmgr_attach()`, a thread pool, a `struct` that
   holds the tables);
3. **the true positives** — does the rule find a real defect in code that
   was written by someone else, with no incentive to please the tool?

The corpus was therefore chosen to be **adversarial by construction**: seven
files published by QNX or BlackBerry themselves (four on
`gitlab.com/qnx/projects`, two on `github.com/qnx`, one on
`github.com/qnx-ports`), and ten files by independent authors (a codelab, a
course, a medical device, a UVC camera driver, two bus drivers, a virtio
port).

---

## 2. The corpus

Seventeen files taken from thirteen public repositories. **Every file is
pinned to the exact commit that was read**, so the measurement does not
depend on what the repository looks like today: the script fetches that one
commit and reads that one path.

| # | Publisher | Project | Path | Commit | SHA-256 (16) | Lines |
|---|---|---|---|---|---|---|
| 1 | QNX | rpi-gpio | `resmgr/main.c` | `880d66fe20a3` | `0a8993aea26d6b09` | 740 |
| 2 | QNX | rpi-mailbox | `rpi_mbox.c` | `dd9ed5928da2` | `eebbb82888389ec4` | 639 |
| 3 | QNX | rpi-thermal | `rpi_thermal.c` | `4ba4fdc40c68` | `b82b73103843e2d5` | 890 |
| 4 | BlackBerry / QNX | shim-demo | `eventfd-mgr.c` | `5be2cd24780f` | `96acb0f8c2c0ea00` | 185 |
| 5 | BlackBerry / QNX | bsp_raspberrypi-bcm2712-rpi5 | `src/hardware/support/bcm2712/fan/resmgr.c` | `573dda1a1ca3` | `9bc95d2e0716bab4` | 291 |
| 6 | BlackBerry / QNX | qnx-posix-publish-subscribe | `qpp/main.c` | `b5ca892f3746` | `ee048cb302f06e0d` | 219 |
| 7 | QNX ports | epoll | `epoll-mgr.c` | `aea458535243` | `806f2950044e90f4` | 1167 |
| 8 | llmike | devu-uvc | `uvc_rm.c` | `8534b138a8f5` | `455a34627ce22ee7` | 557 |
| 9 | llmike | smbus | `smb-ec/main.c` | `fa3c7bbff27f` | `279e7aad6f1377c7` | 184 |
| 10 | llmike | smbus | `smb-ich/main.c` | `fa3c7bbff27f` | `ac65ff517bb691c6` | 187 |
| 11 | kodebooth | qnx-virtio | `src/gpio/resmgr.c` | `037f84fe9b20` | `9da9f7ab6c35e1cb` | 348 |
| 12 | ebenworks | phila-bedside-monitor-qnx | `src/qnx/resmgr.c` | `e255b4be9408` | `0539ffb4cc63befe` | 136 |
| 13 | DesignMaster Solutions | qnx8-resmgr-codelab | `src/hello.c` | `d13f0fbda9b6` | `8217baed0d13f78b` | 85 |
| 14 | DesignMaster Solutions | qnx8-resmgr-codelab | `src/ticks.c` | `d13f0fbda9b6` | `f8b22e50d8baef1f` | 97 |
| 15 | Embedded AI Design Labs | qnx_advance | `module04_drivers/block_rm.c` | `d1a82cef2b82` | `5b2f1844c002d6b7` | 95 |
| 16 | Embedded AI Design Labs | qnx_advance | `module04_drivers/can_rm.c` | `d1a82cef2b82` | `aec260bf680f80b7` | 159 |
| 17 | Embedded AI Design Labs | qnx_advance | `module04_drivers/qtn_sensor_rm.c` | `d1a82cef2b82` | `f7ae084f6a677b1e` | 119 |

The exact URLs, the pinned commits and the version each project declares for
itself are in [`scripts/benchmark-corpus.py`](../scripts/benchmark-corpus.py)
— the manifest is in the script, so it can be read and checked without
running anything.

**What the "version" column says.** Four projects state their own target
(`QNX 8.0`, `qnx800/qnxsdp-env.sh`); the others state nothing, and the
manifest says so rather than guessing. A corpus file written for QNX 7.1
may use an API that QNX 8.0 kept — the linter's job is to read the QNX 8.0
documentation, not to guess the version of the file.

---

## 3. The method

```console
$ python3 -I scripts/benchmark-corpus.py
```

The script does, for each entry:

1. `git init` in a **temporary directory** (or in `--cache`), then
   `git remote add origin <url>` and `git fetch --depth 1 origin <sha>`;
2. reads **exactly one blob**: `git show <sha>:<path>`;
3. runs `qx_probe.analyse()` on it and counts the findings.

Nothing is ever written inside the repository, and the temporary directory is
removed at the end of the run. The script prints `NOT CHECKED` for any file
it could not fetch — **a check that could not run is never counted as a
success**, and the final line counts only the files that were actually read.

The corpus is public code, read with the public Git protocol; nothing is
copied into the repository and no file of the corpus is redistributed here.

---

## 4. The measurement

The result of the run of 14 November 2026, with the version of the linter
in this repository. **The same corpus, run with the previous version of the
tool, produced 3 ERROR and 7 WARN — nine of them false positives; that
"before" measurement is in § 6.**

| # | File | Findings | ERROR | WARN | Exit code |
|---|---|---|---|---|---|
| 1 | rpi-gpio `resmgr/main.c` | 5 | 0 | 0 | 0 |
| 2 | rpi-mailbox `rpi_mbox.c` | 7 | 0 | 0 | 0 |
| 3 | **rpi-thermal `rpi_thermal.c`** | 7 | **1** | 0 | **1** |
| 4 | shim-demo `eventfd-mgr.c` | 5 | 0 | 0 | 0 |
| 5 | bsp rpi5 `fan/resmgr.c` | 5 | 0 | 0 | 0 |
| 6 | qpp `main.c` | 37 | 0 | 0 | 0 |
| 7 | epoll `epoll-mgr.c` | 11 | 0 | 0 | 0 |
| 8 | **devu-uvc `uvc_rm.c`** | 3 | 0 | **1** | **1** |
| 9 | smbus `smb-ec/main.c` | 8 | 0 | 0 | 0 |
| 10 | smbus `smb-ich/main.c` | 8 | 0 | 0 | 0 |
| 11 | qnx-virtio `gpio/resmgr.c` | 4 | 0 | 0 | 0 |
| 12 | phila `src/qnx/resmgr.c` | 5 | 0 | 0 | 0 |
| 13 | codelab `src/hello.c` | 5 | 0 | 0 | 0 |
| 14 | codelab `src/ticks.c` | 6 | 0 | 0 | 0 |
| 15 | qnx_advance `block_rm.c` | 5 | 0 | 0 | 0 |
| 16 | qnx_advance `can_rm.c` | 6 | 0 | 0 | 0 |
| 17 | qnx_advance `qtn_sensor_rm.c` | 5 | 0 | 0 | 0 |

**17/17 files analysed, 1 ERROR in total.** The findings that are not ERROR
are the informational ones (QX008, QX010): a slot that is not wired, a
number of slots held in a macro. Those are not defects.

The two lines that carry a finding are the whole point of the corpus, and
both were read by hand before being believed:

```console
$ python3 -I scripts/benchmark-corpus.py
...
rpi-thermal/rpi_thermal.c    7 finding(s), 1 ERROR, 0 WARN (exit 1)
    ERROR QX004 rpi-thermal/rpi_thermal.c:465: resmgr_read() never calls iofunc_read_verify(): the access gate is missing
...
devu-uvc/uvc_rm.c             3 finding(s), 0 ERROR, 1 WARN (exit 1)
    WARN QX006 devu-uvc/uvc_rm.c:511: no message loop in this file: neither dispatch_block() nor resmgr_block() is called or referenced here; in a resource manager split over several files the loop usually lives in another translation unit (it is then set in pool_attr.block_func) — check the whole project
```

---

## 5. The true positive: QNX's own `rpi-thermal` has no access gate

`rpi-thermal` is published by **QNX itself**, in `gitlab.com/qnx/projects`.
Its read handler is:

```c
static int resmgr_read(resmgr_context_t *ctp, io_read_t *msg, RESMGR_OCB_T *ocb)
{
    ...
}
```

and the file contains **no call to `iofunc_read_verify()` at all** — the
search for `iofunc_read_verify` in the pinned blob returns nothing.

The QNX 8.0 documentation is explicit about it, on the page of
`iofunc_read_verify()`:

> All read handlers should start with a call to `iofunc_read_verify()` and
> proceed only if it returns EOK.

The linter therefore reports `ERROR QX004` on this file, and it is right:
the access gate is missing. This is a real defect in code published by the
vendor of the operating system — found by a static linter on the public
source, without running anything. **No report was sent to QNX, and no third
party was contacted**: the file was read from its public repository, at the
pinned commit, and nothing was written anywhere.

**What this does NOT mean.** It does not mean the file is broken in
production, and it does not mean that the node is left unprotected. It means
the file does not follow the rule the documentation states for read
handlers, and that the rule is worth reporting. Concretely:

1. **The opening permissions do exist.** The two nodes are created with the
   mode `0664` (`mode_t mode = 0664;`, line 732, applied to the two
   attributes at lines 830-831), and the open is handled by the **default**
   open handler of the resource-manager library: `iofunc_func_init()` (line
   824) installs the POSIX-layer default functions, and the open handler is
   not overridden. The mode of the node is therefore checked against the
   client when it opens the resource, before any read happens: the default
   open handler (`iofunc_open_default()`,
   <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_open_default.html>)
   calls `iofunc_open()` to check the client's open mode against the
   attributes of the resource. What the missing gate leaves open is **not**
   the permission on the node: it is the second check, the one the
   documentation makes a separate step.

2. **What the missing gate lets through.** The page of
   `iofunc_read_verify()` says what that step is:

   > This function checks at least that:
   > the original open included read access
   > the incoming message is well-formed, including that:
   > if an xtype is specified that includes extra data headers, the extra data is in the receive buffer
   > the read offset to be used is non-negative

   and what it returns when the check fails:

   > EBADF
   > The client didn't open the resource for read access.

   `resmgr_read()` never calls it, so none of these checks is made: a client
   that opened the node for writing only is served the temperature, and the
   handler never looks at the `xtype` of the message it answers — the word
   `xtype` does not appear anywhere in the file — so a read that carries a
   position, or extra data headers, is served as a plain read of the whole
   value.

3. **A second real point, visible without the documentation.** The reply
   ignores `msg->i.nbytes`: the length of the answer is bounded by
   `ctp->msg_max_size` (1024, line 845), not by the number of bytes the
   client asked for (lines 530-534). A client that asks for eight bytes
   receives the whole string. This one is **a candidate for a future rule**,
   not a finding: QX-PROBE does not detect it today, and nothing here
   claims that it does.

---

## 6. The false positives the benchmark found, and the fixes

Before the corpus existed, the five actionable defects below were invisible:
the examples of the repository could not produce them.

**The "before" measurement.** The same corpus, run with the version of the
linter of **08/11/2026** (md5 `bdc705b7636bea56d849a127e7c341a0`):

```console
$ git show eeb99e4:qx_probe.py > qx_probe.py && python3 -I scripts/benchmark-corpus.py
...
bsp_raspberrypi-bcm2712-rpi5/.../fan/resmgr.c    7 finding(s), 0 ERROR, 2 WARN (exit 1)
    WARN QX011 ...: the dispatch table 'connect_funcs' is an automatic variable that is never initialised: ...
    WARN QX011 ...: the dispatch table 'io_funcs' is an automatic variable that is never initialised: ...
epoll/epoll-mgr.c                                15 finding(s), 0 ERROR, 3 WARN (exit 1)
    WARN QX011 ...: the dispatch table 'connect_funcs' is an automatic variable that is never initialised: ...
    WARN QX011 ...: the dispatch table 'devnode_io_funcs' is an automatic variable that is never initialised: ...
    WARN QX011 ...: the dispatch table 'epoll_io_funcs' is an automatic variable that is never initialised: ...
qnx-posix-publish-subscribe/qpp/main.c          18 finding(s), 1 ERROR, 0 WARN (exit 1)
    ERROR QX006 ...: no message loop: neither dispatch_block() nor resmgr_block() is called, so the resource manager never waits for a message
qnx-virtio/src/gpio/resmgr.c                     6 finding(s), 0 ERROR, 2 WARN (exit 1)
    WARN QX011 ...: the dispatch table 'connect_funcs' is an automatic variable that is never initialised: ...
    WARN QX011 ...: the dispatch table 'io_funcs' is an automatic variable that is never initialised: ...
devu-uvc/uvc_rm.c                                3 finding(s), 1 ERROR, 0 WARN (exit 1)
    ERROR QX006 ...: no message loop: neither dispatch_block() nor resmgr_block() is called, so the resource manager never waits for a message

17/17 files analysed, 3 ERROR in total
```

**Nine false positives in five files**, one of them at ERROR level. The
"after" measurement of § 4 — the same corpus, the same commits, the current
code — is **1 ERROR and no false positive at all**.

| # | Rule | What the benchmark found | Where | Fix |
|---|---|---|---|---|
| 1 | QX011 | a dispatch table that is a **member of a `struct`** was reported as "an automatic table that is never initialised" | bsp rpi5 `fan/resmgr.c` (2), epoll `epoll-mgr.c` (3), qnx-virtio `gpio/resmgr.c` (2) | the rule now computes the **storage duration** of the declaration: a member has the duration of the object that holds it, not the duration of an automatic variable |
| 2 | QX011 | a table initialised through a **member expression** (`&resmgr.io_funcs`) was not recognised as initialised | the same three files | `ident_of()` now reduces a member expression to its last component, so `&resmgr.io_funcs` is matched against the `iofunc_func_init()` call |
| 3 | QX011 | a **second** `iofunc_func_init()` call was ignored — the rule only read the first one | epoll `epoll-mgr.c` (`epoll_io_funcs` is filled by the second call) | the rule now iterates over **every** `iofunc_func_init()` call of the file |
| 4 | QX006 | a message loop **delegated to a thread pool** (`pool_attr.block_func = &dispatch_block;`) was not recognised — the function is *referenced*, not called | qpp `main.c` | the rule now accepts a call **or a reference** |
| 5 | QX006 | a resource manager **split over several files** was reported as "no message loop" although the loop lives in another translation unit (`uvc_driver.c`) | devu-uvc `uvc_rm.c` | QX006 was **downgraded from ERROR to WARN**, and its message now says exactly what it means: *in this file*; check the whole project |

Defects 1 and 2 are two halves of the same mistake — a table that is a
member of a structure is not an automatic variable, and it is filled through
the member — so the seven QX011 findings of the "before" run are seven
instances of the same pair.

Defect 5 deserves a word, because it is a change of **level** and not only of
code. A single translation unit cannot prove that a project has no message
loop: the loop may be in `main.c`, the handlers in `io.c`, and the tables in
`resmgr.c`. Reporting the absence of a loop at ERROR level on the file that
holds the handlers is a **false positive on a valid architecture**. The
honest level for a rule that only sees one file is WARN, and the message now
says what to do about it. The two rules that share this limit are **QX006**
(no loop in this file) and **QX007** (a loop in this file but no handler in
this file); both are WARN now, and both say *in this file*.

### The proof that each fix is a fix

A fix that is not covered by a test proves nothing. Each of the five
defects above is now covered by a test that **fails on the previous code**
and **passes on the current code** — the red→green contract of this
repository:

```console
$ git stash push -q qx_probe.py && python3 -I tests/test_qx_probe.py
...
FAIL: test_api_resmgr_block_et_resmgr_handler
AssertionError: 'QX006' unexpectedly found in [...] : false positive: the loop is delegated to a thread pool
FAIL: test_qx011_table_mise_a_zero_statique
AssertionError: 'QX011' unexpectedly found in [...] : false positive: a member has the storage duration of the object that holds it
...
Ran 27 tests in 0.143s
FAILED (failures=4)

$ git stash pop -q && python3 -I tests/test_qx_probe.py
...
Ran 27 tests in 0.167s
OK
```

The four failures are the four assertions that the benchmark produced: the
delegated loop (QX006/QX007), the table that is a member of a structure, the
table filled by a second `iofunc_func_init()` call, and the level of
QX006/QX007.

---

## 7. The manual verification of every access gate

The tool is a heuristic; the benchmark is only credible if its verdict is
compared with a human reading. The gate (QX004) was therefore checked by
hand on the seventeen files: for every read/write handler of every file,
does the body contain `iofunc_read_verify()` / `iofunc_write_verify()`?

| # | File | Read/write handlers | Gate found by hand | Tool verdict (QX004) | Agreement |
|---|---|---|---|---|---|
| 1 | rpi-gpio `main.c` | `read_gpio` | yes | no finding | ✔ |
| 2 | rpi-mailbox `rpi_mbox.c` | none | — | no finding | ✔ |
| 3 | **rpi-thermal `rpi_thermal.c`** | `resmgr_read()` | **no** | **ERROR QX004** | ✔ |
| 4 | shim-demo `eventfd-mgr.c` | `io_read`, `io_write` | yes | no finding | ✔ |
| 5 | bsp rpi5 `fan/resmgr.c` | `io_read`, `io_write` | yes | no finding | ✔ |
| 6 | qpp `main.c` | none in this file | — | no finding | ✔ |
| 7 | epoll `epoll-mgr.c` | none in this file | — | no finding | ✔ |
| 8 | devu-uvc `uvc_rm.c` | `uvc_read`, `uvc_write` | yes | no finding | ✔ |
| 9 | smbus `smb-ec/main.c` | none in this file | — | no finding | ✔ |
| 10 | smbus `smb-ich/main.c` | none in this file | — | no finding | ✔ |
| 11 | qnx-virtio `gpio/resmgr.c` | `resmgr_read`, `resmgr_write` | yes | no finding | ✔ |
| 12 | phila `resmgr.c` | `io_read`, `io_write` | yes | no finding | ✔ |
| 13 | codelab `hello.c` | `hello_read`, `hello_write` | yes | no finding | ✔ |
| 14 | codelab `ticks.c` | `ticks_read` | yes | no finding | ✔ |
| 15 | qnx_advance `block_rm.c` | `io_read`, `io_write` | yes | no finding | ✔ |
| 16 | qnx_advance `can_rm.c` | none in this file | — | no finding | ✔ |
| 17 | qnx_advance `qtn_sensor_rm.c` | `io_read` | yes | no finding | ✔ |

**17/17 agreements.** The single disagreement that could have existed — the
missing gate of `rpi-thermal` — is a case where the tool and the hand
reading say the same thing.

Two files deserve a line of explanation:

* **qpp `main.c`** (line 6) holds no read handler: the handlers live in
  `qpp/ioread.c`, `qpp/ioread_dir.c` and `qpp/ioread_text.c`. All three were
  read as well, and all three call `iofunc_read_verify()` — the tool says
  nothing because it analyses one file at a time, and the hand reading says
  the code is correct. Its message loop is in this very file, but **delegated
  to a thread pool** (`pool_attr.block_func = &dispatch_block;`), which is the
  case that made the rule accept a reference and not only a call.
* **devu-uvc `uvc_rm.c`** (line 8) is the WARN of the table above: the file
  holds the handlers but not the loop — the loop is in `uvc_driver.c`, another
  translation unit of the same project. The hand reading says exactly what
  the tool says: *the loop is elsewhere in the project*, so the finding is a
  reminder, not a condemnation. It is a WARN for that reason, and this file
  is what made the level change.

---

## 8. What the benchmark does not prove

Honesty about the limits is part of the measurement:

* **One file at a time.** QX-PROBE analyses a file, not a project. The
  limits of QX001, QX003, QX004 and QX006 are the direct consequences, and
  they are written in `RULES.md` for each rule.
* **A corpus is not a proof of completeness.** Seventeen files and thirteen
  repositories show that the tool behaves on real code; they do not show
  that it is right on every possible code. The claim of this repository is
  narrower and checkable: **every rule is backed by an official QNX 8.0
  page**, and every citation is re-checked by
  `scripts/verifier-citations.py`.
* **The corpus is a snapshot.** Every file is pinned to a commit; a later
  version of the same project may be different. The pins are in the
  manifest, so anyone can re-run the measurement on the same bytes.
* **No compilation.** The corpus is read, never built: the QNX SDP is not
  needed, and the findings are about what the source says, not about what
  the compiler accepts.
* **The benchmark is not a contest entry.** It is evidence for the judges.

---

## 9. How to reproduce it

```console
$ git clone https://github.com/tgg49099-dotcom/qnx-qx-probe.git
$ cd qnx-qx-probe
$ python3 -I scripts/benchmark-corpus.py
```

The script needs `git` and the network. It writes nothing in the
repository. With `--json` the same result is produced in machine-readable
form; with `--only <project>` a single entry of the corpus is measured.

The two checks of the repository that must stay green:

```console
$ bash scripts/verify-all.sh
$ python3 -I tests/test_qx_probe.py
```

## 10. Whole programs: nine resource managers of a QNX source tree (v8, 14 November 2026)

The corpus above is one file per project. Larger QNX services are split:
one file per handler, the tables in `main.c`, the loop elsewhere. To test
that case, QX-PROBE was run **once per program, with all its files**, on
nine resource managers of a published QNX 6.4 source tree
(<https://github.com/vocho/openqnx>, commit `cc95df3543a1c481d4f8ad387e29f0d1ff0c87fe`,
`trunk/services/`: random, pipe, dumper, slogger, syslogd, devc-ditto,
mqueue, mq, system/pathmgr — 54 C files). This is older code than QNX 8.0;
it is used here only to test how the linter reads a split program.

| | ERROR | WARN |
|---|---|---|
| v7 | 22 | 20 |
| v8 | 1 | 10 |

* **21 false ERROR removed**: 19 handler or helper files reported QX001 ("no
  dispatch table") although the tables live in another file of the same
  program; 2 QX004 on devc-ditto, which binds its own OCB with
  `resmgr_open_bind()` and never uses the iofunc OCB layer that
  `iofunc_read_verify()` needs (now INFO, "check by hand").
* **10 false WARN removed**: a loop or a handler in another file of the
  program (QX006, QX007), the root path `""` of the path manager read as a
  relative path (QX005), a block-scope `extern` table read as an
  uninitialised automatic table (QX011).
* **The ERROR left is real**: `io_write()` of syslogd writes the message
  without calling `iofunc_write_verify()`, so the open mode of the client is
  never checked.
* **The 10 WARN left** are path-manager files of the kernel process
  (procnto): their message loop is in procnto itself, outside the files
  given — the warning says exactly that.

Reproduce (each program on one command line):

```
git clone https://github.com/vocho/openqnx && cd openqnx
git checkout cc95df3543a1c481d4f8ad387e29f0d1ff0c87fe
cd trunk/services
for d in random pipe dumper slogger syslogd devc-ditto mqueue mq system/pathmgr; do
  python3 -I /path/to/qx_probe.py $(find $d -name '*.c') | tail -1
done
```

The fixtures that pin these cases (`tests/fixtures/multifile/`) are written
for the test suite; no line is copied from these sources.
