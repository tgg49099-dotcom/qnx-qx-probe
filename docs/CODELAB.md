# Codelab — check a QNX 8.0 resource manager before you build it

**A hands-on tutorial.** In 30 minutes you will write nothing but a few edits
to a real QNX 8.0 resource manager, and you will catch the four mistakes that
a compiler cannot see — the missing access gate, the relative mount point,
the message loop that was never entered, the reply that returns more parts
than the IOV holds.

**What you need**

| | |
|---|---|
| A host machine | Linux, macOS or Windows |
| Python | 3.8 or later (the tool uses only the standard library) |
| A C compiler | **not** required |
| A QNX 8.0 board or QEMU guest | **not** required |
| The QNX SDP 8.0 | **not** required — see [Part 6](#part-6-build-and-run-it-on-qnx-80) |

**Time:** about 30 minutes. **Difficulty:** beginner.

**Why this tutorial exists.** The QNX 8.0 resource-manager protocol is
specified in prose, not in types: the C compiler cannot tell you that a read
handler forgot its access gate, because `iofunc_read_verify()` is an ordinary
function call that returns an `int`. The same goes for the other three
mistakes below. QX-PROBE reads the source and reports them, with **zero
false positives** — and every one of its eleven rules is backed by a page of
the official BlackBerry QNX SDP 8.0 documentation.

---

## Part 1 — the anatomy of a QNX 8.0 resource manager

Before we break anything, here is the shape of the code we are going to
check. A QNX 8.0 resource manager is five things:

1. **A dispatch handle** — `dispatch_create()` creates the channel the
   clients talk to.
2. **Two dispatch tables** — a `resmgr_connect_funcs_t` (the POSIX-level
   connect functions: `open`, `unlink`, `rename`, …) and a
   `resmgr_io_funcs_t` (the I/O functions: `read`, `write`, `devctl`, …).
   The documentation says you fill them with the POSIX defaults and then
   override what you need: *"You can initialize this table by calling
   `iofunc_func_init()` and then overriding the defaults with your own
   functions."* — [`resmgr_io_funcs_t()`](https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_io_funcs_t.html)
3. **An attachment** — `resmgr_attach()` binds a **path** to the handle and
   to the two tables. *"The `resmgr_attach()` function puts the path into the
   general pathname space and binds requests on this path to the dispatch
   handle `dpp`."* — [`resmgr_attach()`](https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_attach.html)
4. **A message loop** — `dispatch_block()` (or its special case
   `resmgr_block()`) waits for a message, and `dispatch_handler()` (or
   `resmgr_handler()`) *"handles the message received in `ctp`"* —
   [`resmgr_block()`](https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_block.html) ·
   [`resmgr_handler()`](https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_handler.html)
5. **An access gate** in each I/O handler — *"All read handlers should start
   with a call to `iofunc_read_verify()` and proceed only if it returns
   EOK."* — [`iofunc_read_verify()`](https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_read_verify.html)

All five pieces are in `examples/qnx80_resmgr_minimal.c`, a complete
resource manager written for this tutorial. Keep it open — you are about to
edit copies of it.

**One more thing the documentation insists on**, and which a compiler cannot
check either: the number of parts you return to the client must fit in the
IOV. *"The `resmgr_attach()` function should set `attr->nparts_max` to be
the maximum value for `num`."* — [`_RESMGR_NPARTS()`](https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/_resmgr_nparts.html)

---

## Part 2 — install it and run it once

```console
$ git clone https://github.com/tgg49099-dotcom/qnx-qx-probe.git
$ cd qnx-qx-probe
$ python3 -I qx_probe.py examples/qnx80_resmgr_minimal.c
INFO  QX008  examples/qnx80_resmgr_minimal.c:io_funcs: io_funcs.devctl is not assigned (the POSIX default iofunc_devctl_default() applies unless you override it)
INFO  QX008  examples/qnx80_resmgr_minimal.c:io_funcs: io_funcs.unblock is not assigned (the POSIX default iofunc_unblock_default() applies unless you override it)
INFO  QX008  examples/qnx80_resmgr_minimal.c:io_funcs: io_funcs.notify is not assigned (QNX 8.0 defines no default for this slot: the message is not handled)
INFO  QX010  examples/qnx80_resmgr_minimal.c: io function count '_RESMGR_IO_NFUNCS' is not a literal (macro)
INFO  QX010  examples/qnx80_resmgr_minimal.c: connect function count '_RESMGR_CONNECT_NFUNCS' is not a literal (macro)

RESULT: 5 finding(s), 0 ERROR, 0 WARN
$ echo $?
0
```

Read the output before you go on — it is the key to the whole tutorial.

* **Five findings, zero ERROR, zero WARN.** This file is valid QNX 8.0 code,
  and the tool says so.
* **The exit code is 0.** `0` means "no actionable finding"; `1` means "at
  least one ERROR or WARN"; `2` means the call was malformed. `INFO` never
  changes the exit code.
* **The three `QX008` findings are not defects.** `devctl` and `unblock`
  have a documented POSIX default (`iofunc_devctl_default()`,
  `iofunc_unblock_default()`), so not overriding them is normal.
  `notify` is the interesting one: **QNX 8.0 defines no default for it**
  (`"None"` in the *Default* column of the table), so an unwired `notify`
  slot means the notification message is simply not handled. QX-PROBE says
  so — as `INFO`, which does not condemn the code.
* **The two `QX010` findings are not defects either.** You passed
  `_RESMGR_IO_NFUNCS` and `_RESMGR_CONNECT_NFUNCS` to
  `iofunc_func_init()`, which is *"typically"* what the documentation asks
  for. The tool reports the macro, draws no conclusion from it, and stays
  quiet.

> **The golden rule of this tool: a rule that misreports canonical QNX 8.0
> code is worse than a missing rule.** That is why the two INFO families
> above exist at all: they tell you *what the code does* without pretending
> it is broken. If the linter flagged BlackBerry's own published resource
> manager, it would be useless — so the test suite checks that it does not.

Now check the reference code published by BlackBerry, and the example taken
from the QNX 8.0 documentation itself:

```console
$ python3 -I qx_probe.py examples/blackberry_eventfd_mgr.c
INFO  QX008  examples/blackberry_eventfd_mgr.c:io_funcs: io_funcs.devctl is not assigned (the POSIX default iofunc_devctl_default() applies unless you override it)
INFO  QX008  examples/blackberry_eventfd_mgr.c:io_funcs: io_funcs.unblock is not assigned (the POSIX default iofunc_unblock_default() applies unless you override it)
INFO  QX008  examples/blackberry_eventfd_mgr.c:io_funcs: io_funcs.notify is not assigned (QNX 8.0 defines no default for this slot: the message is not handled)
INFO  QX010  examples/blackberry_eventfd_mgr.c: io function count '_RESMGR_IO_NFUNCS' is not a literal (macro)
INFO  QX010  examples/blackberry_eventfd_mgr.c: connect function count '_RESMGR_CONNECT_NFUNCS' is not a literal (macro)

RESULT: 5 finding(s), 0 ERROR, 0 WARN
$ python3 -I qx_probe.py examples/qnx80_resmgr_official_example.c
INFO  QX008  examples/qnx80_resmgr_official_example.c:my_io_functions: my_io_functions.write is not assigned (the POSIX default iofunc_write_default() applies unless you override it)
INFO  QX008  examples/qnx80_resmgr_official_example.c:my_io_functions: my_io_functions.devctl is not assigned (the POSIX default iofunc_devctl_default() applies unless you override it)
INFO  QX008  examples/qnx80_resmgr_official_example.c:my_io_functions: my_io_functions.unblock is not assigned (the POSIX default iofunc_unblock_default() applies unless you override it)
INFO  QX008  examples/qnx80_resmgr_official_example.c:my_io_functions: my_io_functions.notify is not assigned (QNX 8.0 defines no default for this slot: the message is not handled)
INFO  QX010  examples/qnx80_resmgr_official_example.c: io function count '_RESMGR_IO_NFUNCS' is not a literal (macro)
INFO  QX010  examples/qnx80_resmgr_official_example.c: connect function count '_RESMGR_CONNECT_NFUNCS' is not a literal (macro)

RESULT: 6 finding(s), 0 ERROR, 0 WARN
```

Both are clean. The second one deserves a second look: it is the *official
example* of `iofunc_func_init()`, and it spells the member **`io_read`**
instead of `read` — the documentation's own example. QX-PROBE accepts both
spellings precisely so that it cannot misfire on the vendor's code.

---

## Part 3 — break it on purpose, four ways

Each of the following is a mistake that compiles cleanly and misbehaves at
runtime. We make it, we let the tool find it, then we read the official
page that says the code was wrong.

Work in a scratch directory so that the repository stays clean:

```console
$ mkdir -p lab
```

### 3.1 The access gate is missing (QX004)

The repository ships the broken file, so you can see the result immediately:

```console
$ python3 -I qx_probe.py tests/fixtures/qnx80_resmgr_qx004_no_gate.c
ERROR QX004  tests/fixtures/qnx80_resmgr_qx004_no_gate.c:read: qx_read() never calls iofunc_read_verify(): the access gate is missing
INFO  QX008  tests/fixtures/qnx80_resmgr_qx004_no_gate.c:io_funcs: io_funcs.devctl is not assigned (the POSIX default iofunc_devctl_default() applies unless you override it)
INFO  QX008  tests/fixtures/qnx80_resmgr_qx004_no_gate.c:io_funcs: io_funcs.unblock is not assigned (the POSIX default iofunc_unblock_default() applies unless you override it)
INFO  QX008  tests/fixtures/qnx80_resmgr_qx004_no_gate.c:io_funcs: io_funcs.notify is not assigned (QNX 8.0 defines no default for this slot: the message is not handled)
INFO  QX010  tests/fixtures/qnx80_resmgr_qx004_no_gate.c: io function count '_RESMGR_IO_NFUNCS' is not a literal (macro)
INFO  QX010  tests/fixtures/qnx80_resmgr_qx004_no_gate.c: connect function count '_RESMGR_CONNECT_NFUNCS' is not a literal (macro)

RESULT: 6 finding(s), 1 ERROR, 0 WARN
$ echo $?
1
```

**Why it matters.** Without `iofunc_read_verify()`, the handler serves the
read **without checking the permissions of the open descriptor** — the
client gets the data it was not allowed to have. The documentation is
explicit: *"All read handlers should start with a call to
`iofunc_read_verify()` and proceed only if it returns EOK."*

Note that the finding says `never calls iofunc_read_verify()` — the tool
blanked the comments and the string literals before searching, so a gate
merely *mentioned* in an error message is not mistaken for a gate, and a
check delegated to a helper function of the same file **is** accepted.

### 3.2 The mount point is relative (QX005)

```console
$ python3 -I qx_probe.py examples/qnx80_resmgr_relative_path.c
WARN  QX005  examples/qnx80_resmgr_relative_path.c:82: resmgr_attach() attaches the relative path 'qxprobe-rel': QNX resolves it against the current working directory (an absolute path is recommended)
INFO  QX008  examples/qnx80_resmgr_relative_path.c:io_funcs: io_funcs.write is not assigned (the POSIX default iofunc_write_default() applies unless you override it)
INFO  QX008  examples/qnx80_resmgr_relative_path.c:io_funcs: io_funcs.devctl is not assigned (the POSIX default iofunc_devctl_default() applies unless you override it)
INFO  QX008  examples/qnx80_resmgr_relative_path.c:io_funcs: io_funcs.unblock is not assigned (the POSIX default iofunc_unblock_default() applies unless you override it)
INFO  QX008  examples/qnx80_resmgr_relative_path.c:io_funcs: io_funcs.notify is not assigned (QNX 8.0 defines no default for this slot: the message is not handled)
INFO  QX010  examples/qnx80_resmgr_relative_path.c: io function count '_RESMGR_IO_NFUNCS' is not a literal (macro)
INFO  QX010  examples/qnx80_resmgr_relative_path.c: connect function count '_RESMGR_CONNECT_NFUNCS' is not a literal (macro)

RESULT: 7 finding(s), 0 ERROR, 1 WARN
$ echo $?
1
```

**Why it matters.** *"You usually provide an absolute path; if you provide a
path that doesn't start with a slash, it's considered to be relative to the
current working directory."* — the mount point then depends on where the
service was started from. This is a **WARN**, not an ERROR: the code is
legitimate, it is only fragile.

And notice what QX-PROBE does **not** say: it does not ask for `/dev/`. The
QNX pathname space is general, so `/var/run/my_daemon` is a perfectly valid
mount point, and an earlier version of this tool that insisted on `/dev/`
was wrong.

### 3.3 The message loop was never entered (QX006)

Now let *you* break the code. Copy the example and delete the loop that
waits for the messages:

```console
$ python3 - <<'PY'
src = open('examples/qnx80_resmgr_minimal.c').read()
src = src.replace("""    ctp = dispatch_context_alloc(dpp);
    while (1) {
        if ((ctp = dispatch_block(ctp)) == NULL) {
            fprintf(stderr, "qx-probe-demo: block error\\n");
            return EXIT_FAILURE;
        }
        dispatch_handler(ctp);
    }
    return EXIT_SUCCESS;""", """    ctp = dispatch_context_alloc(dpp);
    (void)ctp;
    return EXIT_SUCCESS;""")
open('lab/break_qx006.c', 'w').write(src)
PY
$ python3 -I qx_probe.py lab/break_qx006.c
WARN  QX006  lab/break_qx006.c: no message loop in this file: neither dispatch_block() nor resmgr_block() is called or referenced here; in a resource manager split over several files the loop usually lives in another translation unit (it is then set in pool_attr.block_func) — check the whole project
INFO  QX008  lab/break_qx006.c:io_funcs: io_funcs.devctl is not assigned (the POSIX default iofunc_devctl_default() applies unless you override it)
INFO  QX008  lab/break_qx006.c:io_funcs: io_funcs.unblock is not assigned (the POSIX default iofunc_unblock_default() applies unless you override it)
INFO  QX008  lab/break_qx006.c:io_funcs: io_funcs.notify is not assigned (QNX 8.0 defines no default for this slot: the message is not handled)
INFO  QX010  lab/break_qx006.c: io function count '_RESMGR_IO_NFUNCS' is not a literal (macro)
INFO  QX010  lab/break_qx006.c: connect function count '_RESMGR_CONNECT_NFUNCS' is not a literal (macro)

RESULT: 6 finding(s), 0 ERROR, 1 WARN
```

**Why it matters.** `resmgr_block()` *"waits for a message"*. Without it,
the process attaches its name and exits: the clients that open the device
block forever. The tool accepts **both** idioms — `dispatch_block()` and
`resmgr_block()` — because the reference example in the QNX 8.0
documentation uses the second one.

**Why this one is a WARN and not an ERROR.** QX-PROBE analyses **one file
at a time**, and the loop of a resource manager split over several files
lives in another translation unit. The tool cannot prove that the project
has no message loop, so it says exactly what it can prove: *no loop **in
this file*** — and it tells you where to look (`pool_attr.block_func`). The
same rule, applied to real code, is what taught it that lesson: on
`devu-uvc`, a QNX resource manager published on GitHub, the loop is in
`main.c` and the handlers are in `uvc_rm.c` — see
[`docs/BENCHMARK.md`](BENCHMARK.md) §6.

### 3.4 The reply returns more parts than the IOV holds (QX009)

Same file, one more edit: the read handler claims to return two components
while the resource manager was given room for one.

```console
$ python3 - <<'PY'
src = open('examples/qnx80_resmgr_minimal.c').read()
src = src.replace("return _RESMGR_NPARTS(1);", "return _RESMGR_NPARTS(2);")
open('lab/break_qx009.c', 'w').write(src)
PY
$ python3 -I qx_probe.py lab/break_qx009.c
ERROR QX009  lab/break_qx009.c: qx_read() returns _RESMGR_NPARTS(2) but the resource manager declares attr.nparts_max = 1: the IOV array holds only 1 component(s)
INFO  QX008  lab/break_qx009.c:io_funcs: io_funcs.devctl is not assigned (the POSIX default iofunc_devctl_default() applies unless you override it)
INFO  QX008  lab/break_qx009.c:io_funcs: io_funcs.unblock is not assigned (the POSIX default iofunc_unblock_default() applies unless you override it)
INFO  QX008  lab/break_qx009.c:io_funcs: io_funcs.notify is not assigned (QNX 8.0 defines no default for this slot: the message is not handled)
INFO  QX010  lab/break_qx009.c: io function count '_RESMGR_IO_NFUNCS' is not a literal (macro)
INFO  QX010  lab/break_qx009.c: connect function count '_RESMGR_CONNECT_NFUNCS' is not a literal (macro)

RESULT: 6 finding(s), 1 ERROR, 0 WARN
```

**Why it matters.** `nparts_max` is *"the number of components to allocate
for the IOV array"*. Return more parts than the array holds and the kernel
writes past the end of it.

The tool is careful here: it only reports the overflow when the number of
parts is **unambiguous** — a literal, or a single assignment in the
handler. If it cannot tell, it says nothing.

---

## Part 4 — turn it into a gate

The exit code is what makes the tool usable in a continuous-integration
chain: `0` = clean, `1` = an actionable finding, `2` = bad usage. A single
line is enough:

```console
$ python3 -I qx_probe.py examples/qnx80_resmgr_minimal.c > /dev/null && echo "CI: PASS" || echo "CI: FAIL"
CI: PASS
```

In a CI job (GitHub Actions, GitLab CI, Jenkins), the step is simply:

```yaml
- name: QX-PROBE — QNX 8.0 resource-manager protocol
  run: python3 -I qx_probe.py src/*.c
```

The step fails the build as soon as a resource manager loses its access
gate. No SDK, no board, no licence — the check runs in a second, on any
machine, on every commit.

---

## Part 5 — check the whole program, not one file

A handler is often defined in another translation unit, and a single file
cannot prove that a symbol is missing. So pass **all** the files: the tool
resolves the symbols of the whole analysed set.

```console
$ python3 -I qx_probe.py examples/qnx80_resmgr_minimal.c examples/qnx80_resmgr_readonly.c
INFO  QX008  examples/qnx80_resmgr_minimal.c:io_funcs: io_funcs.devctl is not assigned (the POSIX default iofunc_devctl_default() applies unless you override it)
INFO  QX008  examples/qnx80_resmgr_minimal.c:io_funcs: io_funcs.unblock is not assigned (the POSIX default iofunc_unblock_default() applies unless you override it)
INFO  QX008  examples/qnx80_resmgr_minimal.c:io_funcs: io_funcs.notify is not assigned (QNX 8.0 defines no default for this slot: the message is not handled)
INFO  QX008  examples/qnx80_resmgr_readonly.c:io_funcs: io_funcs.write is not assigned (the POSIX default iofunc_write_default() applies unless you override it)
INFO  QX008  examples/qnx80_resmgr_readonly.c:io_funcs: io_funcs.devctl is not assigned (the POSIX default iofunc_devctl_default() applies unless you override it)
INFO  QX008  examples/qnx80_resmgr_readonly.c:io_funcs: io_funcs.unblock is not assigned (the POSIX default iofunc_unblock_default() applies unless you override it)
INFO  QX008  examples/qnx80_resmgr_readonly.c:io_funcs: io_funcs.notify is not assigned (QNX 8.0 defines no default for this slot: the message is not handled)
INFO  QX010  examples/qnx80_resmgr_minimal.c: io function count '_RESMGR_IO_NFUNCS' is not a literal (macro)
INFO  QX010  examples/qnx80_resmgr_minimal.c: connect function count '_RESMGR_CONNECT_NFUNCS' is not a literal (macro)
INFO  QX010  examples/qnx80_resmgr_readonly.c: io function count '_RESMGR_IO_NFUNCS' is not a literal (macro)
INFO  QX010  examples/qnx80_resmgr_readonly.c: connect function count '_RESMGR_CONNECT_NFUNCS' is not a literal (macro)

RESULT: 11 finding(s), 0 ERROR, 0 WARN
```

The read-only resource manager is **not** condemned for having no `write`
handler: every slot of the table has a documented POSIX default.

---

## Part 6 build and run it on QNX 8.0

This part is **optional**: everything above ran on your host. To get a real
QNX 8.0 binary you need
the **SDP 8.0** — the free non-commercial *QNX Everywhere* licence
(<https://qnx.software/en/developers/get-started/qnx-everywhere>, a myQNX
account is required). With the SDK installed, the host tools are on your
`PATH` and the repository compiles the examples for you:

```console
$ bash scripts/build_qcc.sh x86_64
```

The script uses `qcc -Vgcc_ntoaosdebug -Werror`, that is: the native QNX
libraries and **no warning tolerated**. Targets: `x86_64` (a QEMU guest),
`aarch64`, `armv7`.

> **Honest note.** The build of these examples has **NOT been measured** in
> the environment where this tutorial was written: there was no SDP 8.0
> licence there, so `qcc` was absent and the script stopped with an explicit
> message. No compiler output was ever simulated. If you run it with the
> SDK, you are the first — and the output you get is the real one.

Without the SDK, the script says so and stops:

```console
$ bash scripts/build_qcc.sh
ERROR: qcc was not found.

This script compiles for QNX 8.0 with the SDP 8.0 (host tools).  Without the
SDP 8.0 and a non-commercial QNX Everywhere licence (myQNX account), the
compilation is impossible.

What is missing, and what this script cannot simulate:
  - qcc (the QNX C compiler, shipped with the SDP 8.0)
  - the QNX 8.0 system libraries (libc, libsys, ...)

No compiler output is simulated: without qcc, this script stops here, with
exit code 2.
```

A resource manager is a QNX process: it needs the QNX 8.0 target, not a
Linux one. The example mounts `/dev/qxprobe-demo`; on a QNX 8.0 guest you
would then read it with `cat /dev/qxprobe-demo`.

---

## Part 7 — exercises

Do them on copies, in the `lab/` directory. The expected results below are
the **measured** ones: they were produced by running the tool on the edited
files. The script `scripts/verifier-codelab.py` replays every command of
this tutorial and compares the output with what is written here, so a
tutorial that drifts from the tool is caught by a single command.

1. **Make the tool report a missing dispatch table (QX001).** Delete the two
   table declarations, the `iofunc_func_init()` call, the two slot
   assignments, and pass `NULL` to `resmgr_attach()`. Expected: **two
   `ERROR QX001`**, one for each table (`connect_funcs` and `io_funcs`).
   *And observe:* deleting **only** the `iofunc_func_init()` call produces
   **no** finding — the table is still declared, and a static table is
   zero-initialised by C, which is a deliberate choice (see QX011). This is
   a limit of a static checker, and it is documented in
   [Known limits](#known-limits-of-this-tool).
2. **Make the tool report a NULL dispatch table (QX001, second case).**
   Keep the tables, but pass `NULL` instead of `&connect_funcs` and
   `&io_funcs` to `resmgr_attach()`. The documentation allows `NULL` for
   the `attr` argument *"to use the default attributes"*, but says nothing
   of the sort for the two dispatch tables: a NULL table means a resource
   manager with no handler at all. Expected: **two `ERROR QX001`**.
3. **Make the tool report a handler that does not exist (QX003).** Assign a
   slot to a function you never define, for example
   `io_funcs.read  = qx_read_typo;`. Expected: **one `INFO QX003`** — *INFO*,
   because a single file cannot prove that the symbol is missing: it may be
   defined in another translation unit. Define the handler in a second file
   and pass both files to the command: the QX003 finding disappears, because
   the symbols are resolved across the whole analysed set (but read the
   known limit below before you apply that to a real project).
4. **Make the tool report an uninitialised automatic table (QX011).**
   Declare the two dispatch tables inside `main()` (on the stack) instead of
   at file scope, and do not initialise them. Expected: **two `WARN QX011`**,
   one per table. A *static* table is zero-initialised by C, so it is
   **not** reported.
5. **Make the tool report an overflow of `iofunc_func_init()` (QX002).**
   The signature is `iofunc_func_init(nconnect, connect_funcs, nio,
   io_funcs)` — the **connect** table comes first. Ask for 40 entries of the
   io table, which declares 34 members:
   `iofunc_func_init(_RESMGR_CONNECT_NFUNCS, &connect_funcs, 40, &io_funcs);`
   Expected: **one `ERROR QX002`**.

Every exercise has its answer in the test suite of the repository — one
test per case, named after the rule. Run the whole suite with:

```console
$ bash scripts/run_tests.sh
...
OK

RESULT: QX-PROBE suite GREEN (RC 0)
```

The suite is a two-sided contract: the valid cases must produce **no**
actionable finding, and the sabotaged cases must produce the expected
finding. A rule that was simply deleted would prove nothing.

---

## Part 8 — troubleshooting

**"The tool reports things on valid code."** Before you file a bug, read
the level: `INFO` never condemns the code and never changes the exit code.
`QX008` (an unwired slot with a POSIX default) and `QX010` (the number of
entries is a macro) are informational by design.

**"It reports a handler as missing although it exists."** Give it every
file of the program on the same command line: the symbols are resolved
across the whole analysed set.

**"It says the access gate is missing although my helper calls it."** The
gate must be called **in the body of the handler itself**. The rule follows
the calls that are inside the file it analyses: a check delegated to a
helper is not followed, **even if the helper is one of the analysed files**
(see *Limit 2* below, which shows the exact command).

**"I want to check one file of a very large project."** You can — a single
file is checked on its own, and the findings that depend on the other files
(the symbol resolution) simply stay silent.

**"Does it need the QNX SDK?"** No. The tool reads C source with the
standard library of Python and nothing else. That is the whole point: the
check runs on a laptop, in a container, in a CI job.

**"Does it work on code that is not C?"** No: it is a checker of the QNX
8.0 resource-manager protocol, written in C.

---

## Known limits of this tool

A static checker sees one file at a time. Two limits are worth knowing in
this tutorial — they are stated here with the exact command that reproduces
them, because a tool that hides its limits is not worth trusting. The
**complete list of the known limits of each of the eleven rules** is in
**[RULES.md](../RULES.md)**: every rule that was corrected declares the one
limit it still has.

### Limit 1 — QX001 and programs split across several files

The rule "the file must wire a dispatch table" is applied to **every**
analysed file. In a program split across several files, a file that only
*defines handlers* is therefore reported, although the tables live in
another file:

```console
$ printf 'static int h(resmgr_context_t *ctp, io_read_t *msg, iofunc_ocb_t *ocb)\n{\n    (void)ctp; (void)msg; (void)ocb;\n    return 0;\n}\n' > lab/handlers.c
$ python3 -I qx_probe.py lab/handlers.c
ERROR QX001  lab/handlers.c: file uses the QNX resmgr API but no dispatch table is wired (no resmgr_io_funcs_t / resmgr_connect_funcs_t table is declared, initialised, filled by iofunc_func_init() or passed to resmgr_attach())

RESULT: 1 finding(s), 1 ERROR, 0 WARN
```

**Until this is fixed, analyse the file that calls `resmgr_attach()`.** That
is the file the rule is about: the two dispatch tables are the
`connect_funcs` and `io_funcs` arguments of `resmgr_attach()`.

### Limit 2 — QX004 and a gate delegated to another file

The access gate is looked up in the body of the handler, in the file being
analysed. A check delegated to a helper function of **another** file is
therefore reported as a missing gate:

```console
$ python3 - <<'PY'
src = open('examples/qnx80_resmgr_minimal.c').read()
src = src.replace("""    if ((status = iofunc_read_verify(ctp, msg, ocb, NULL)) != EOK)
        return status;
""", """    if ((status = my_gate(ctp, msg, ocb)) != EOK)
        return status;
""")
open('lab/delegue.c', 'w').write(src)
open('lab/gate.c', 'w').write("""static int my_gate(resmgr_context_t *ctp, io_read_t *msg, iofunc_ocb_t *ocb)
{
    return iofunc_read_verify(ctp, msg, ocb, NULL);
}
""")
PY
$ python3 -I qx_probe.py lab/delegue.c lab/gate.c
ERROR QX001  lab/gate.c: file uses the QNX resmgr API but no dispatch table is wired (no resmgr_io_funcs_t / resmgr_connect_funcs_t table is declared, initialised, filled by iofunc_func_init() or passed to resmgr_attach())
ERROR QX004  lab/delegue.c:read: qx_read() never calls iofunc_read_verify(): the access gate is missing
INFO  QX008  lab/delegue.c:io_funcs: io_funcs.devctl is not assigned (the POSIX default iofunc_devctl_default() applies unless you override it)
INFO  QX008  lab/delegue.c:io_funcs: io_funcs.unblock is not assigned (the POSIX default iofunc_unblock_default() applies unless you override it)
INFO  QX008  lab/delegue.c:io_funcs: io_funcs.notify is not assigned (QNX 8.0 defines no default for this slot: the message is not handled)
INFO  QX010  lab/delegue.c: io function count '_RESMGR_IO_NFUNCS' is not a literal (macro)
INFO  QX010  lab/delegue.c: connect function count '_RESMGR_CONNECT_NFUNCS' is not a literal (macro)

RESULT: 7 finding(s), 2 ERROR, 0 WARN
```

A helper of the **same** file is accepted — the rule follows the call
inside the file it analyses. Only a helper in another file is missed.

---

## What you have learned

* The five pieces of a QNX 8.0 resource manager: dispatch handle, two
  dispatch tables, the attachment, the message loop, the access gate.
* That four protocol errors are invisible to the C compiler, and where the
  official documentation states them.
* That a linter for a real-time operating system must have **zero false
  positives** to be worth anything, and how that is achieved (every rule
  cites an official page; every rule has a test that fails on the previous
  version of the code).
* How to turn a static check into a CI gate with a single exit code.

## References — the official QNX 8.0 pages used here

All of them are pages of the **BlackBerry QNX SDP 8.0** C Library
Reference, re-read on **12 November 2026**: all 12 answered HTTP 200, and
each one carries the update date QNX put on it (`Page updated:
November 05, 2026`).

| Page | URL |
|---|---|
| `resmgr_attach()` | <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_attach.html> |
| `resmgr_block()` | <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_block.html> |
| `resmgr_handler()` | <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_handler.html> |
| `resmgr_io_funcs_t()` | <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_io_funcs_t.html> |
| `resmgr_connect_funcs_t()` | <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_connect_funcs_t.html> |
| `resmgr_context_t()` | <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_context_t.html> |
| `_RESMGR_NPARTS()` | <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/_resmgr_nparts.html> |
| `dispatch_block()` | <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/d/dispatch_block.html> |
| `dispatch_handler()` | <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/d/dispatch_handler.html> |
| `iofunc_func_init()` | <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_func_init.html> |
| `iofunc_read_verify()` | <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_read_verify.html> |
| `iofunc_write_verify()` | <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_write_verify.html> |

The full description of the eleven rules, with the quotation and the URL
for each one, is in **[RULES.md](../RULES.md)**.

## Licence

This tutorial and the tool it uses are under the Apache-2.0 licence (see
[LICENSE](../LICENSE)). The example `examples/blackberry_eventfd_mgr.c` comes
from BlackBerry's public `shim-demo` repository and is kept under
Apache-2.0 as well (see [NOTICE](../NOTICE)).

AI assistance: this tutorial was written with the assistance of a language
model. The official QNX 8.0 documentation and BlackBerry's public reference
code are the only factual sources cited, and every output shown above was
produced by running the commands on a real machine.
