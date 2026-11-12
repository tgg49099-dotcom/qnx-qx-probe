# The rules of QX-PROBE and their official QNX 8.0 sources

> The French counterpart of this file is in
> [`docs/RULES.fr.md`](docs/RULES.fr.md), updated with it: the same eleven
> rules and the same official QNX 8.0 sources.

Every rule of the linter is backed by a page of the official **BlackBerry
QNX SDP 8.0** documentation (QNX OS 8.0 C Library Reference). The 12 pages
cited below were re-read on **12 November 2026**: all 12 answered HTTP 200,
and each one carries the update date QNX put on it (`Page updated:
November 05, 2026`). The date each page carries is printed by
`scripts/verifier-citations.py`, so a judge can read it for himself.

Reading convention: **a rule without an official source is a rule that does
not exist.** When the documentation contradicts a rule, it is the rule that
gives way — never the canonical QNX code.

---

## QX001 — no dispatch table wired
* **Level:** ERROR
* **Sources:** `resmgr_attach()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_attach.html> · `resmgr_io_funcs_t()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_io_funcs_t.html> · `iofunc_func_init()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_func_init.html>
* **What the documentation says:** `resmgr_attach()` takes `connect_funcs` and
  `io_funcs` — "a pointer to the `resmgr_connect_funcs_t` structure that
  defines the POSIX-level connect functions" and "a pointer to the
  `resmgr_io_funcs_t` structure that defines the POSIX-level I/O functions".
  `resmgr_io_funcs_t()` adds: "You can initialize this table by calling
  `iofunc_func_init()` and then overriding the defaults with your own
  functions."
* **What the rule checks:** a file that uses the resmgr API but wires **no**
  dispatch table at all — no `resmgr_io_funcs_t` / `resmgr_connect_funcs_t`
  declared, no C99 initialiser, no table filled by `iofunc_func_init()`, no
  table passed to `resmgr_attach()`. The rule also reports a **NULL table**
  passed to `resmgr_attach()`: the documentation explicitly allows `NULL` for
  the `attr` argument ("or NULL to use the default attributes"), but says
  nothing of the sort for the two dispatch tables — a NULL table means a
  resource manager with no handler at all.
* **What changed in this version:** the rule used to look for a table named
  `io_funcs` and for members named `read`/`write`. The **official example** of
  `iofunc_func_init()` uses another name (`my_io_functions`) and another member
  spelling (`my_io_functions.io_read = my_io_read;`), and a C99 initialiser
  (`resmgr_io_funcs_t f = { .read = my_read };`) wires a table too. All of
  these were reported by mistake. The rule now recognises the four documented
  ways of wiring a table, accepts both member spellings, and has gained the
  NULL-table case.
* **Known limit:** the rule is applied to **every analysed file**, so a file
  that only *defines handlers* is reported although the two dispatch tables
  live in another file — until that is fixed, analyse the file that calls
  `resmgr_attach()`, whose `connect_funcs` and `io_funcs` arguments are the
  two tables the rule is about. A **NULL** table is reported as well: the
  documentation explicitly allows `NULL` only for the `attr` argument ("or
  NULL to use the default attributes") and says nothing about the two
  dispatch tables, so the rule takes the strict reading — a NULL table means
  a resource manager with no handler at all.

## QX002 — `iofunc_func_init()` is asked to fill more entries than the table holds
* **Level:** ERROR
* **Sources:** `iofunc_func_init()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_func_init.html> · `resmgr_io_funcs_t()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_io_funcs_t.html> · `resmgr_connect_funcs_t()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_connect_funcs_t.html>
* **What the documentation says:**
  > `nio` — "The number of entries in the io table that you want to fill.
  > Typically, you pass `_RESMGR_IO_NFUNCS` for this argument."
  >
  > `nconnect` — "The number of entries in the connect table that you want to
  > fill."
  >
  > "The `nconnect` and `nio` arguments indicate how many entries this
  > function should fill. This is in place to support forward compatibility."
  >
  > "The `resmgr_connect_funcs_t` structure is a table of the POSIX-level
  > connect functions that are used by a resource manager."
* **What the rule checks:** the only honest overflow is a count **larger than
  the table**: more than **34** entries for the io table (the
  `resmgr_io_funcs_t` structure declares 34 function members plus `nfuncs`),
  more than **8** entries for the connect table (`resmgr_connect_funcs_t`
  declares 8 function members plus `nfuncs`). In that case the library
  writes past the end of the structure.
* **What changed in this version:** the rule used to compare the number of
  **slots wired** with the number of **entries filled**. That was a false
  positive: the official example fills the defaults and *then* overrides some
  of them ("At this point, the defaults have been filled in. You may now
  override some of the default functions with functions that you have
  written"), so wiring more slots than `nio` is legitimate. Worse, the real
  overflow was never detected. The rule now reports the overflow and nothing
  else.
* **Known limit:** only a **literal** count is checked: a count held in a
  variable is not checked at all (the macro case is reported as `QX010`,
  INFO). The count is compared with the size of the **standard** tables of
  QNX 8.0 — 34 function members for `resmgr_io_funcs_t` and 8 for
  `resmgr_connect_funcs_t` — so a program that passes a structure of its own
  to `iofunc_func_init()` is measured against those sizes.

## QX003 — a slot points at a function not found in the analysed files
* **Level:** INFO (it was ERROR before this version)
* **Source:** `resmgr_io_funcs_t()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_io_funcs_t.html>
* **What the documentation says:** each member of the table is a function
  pointer (`int (*read)(resmgr_context_t *ctp, io_read_t *msg, RESMGR_OCB_T *ocb);`).
  A pointer to a function that does not exist is a link error — but the link
  is resolved by the **linker**, over the whole program.
* **What the rule checks:** the handler assigned to a slot is neither defined
  nor declared in the analysed files. The finding states the exact condition:
  "if it is not defined in another translation unit, the link will fail".
* **What changed in this version:** a single compilation unit **cannot** prove
  that a symbol is missing — a handler defined in another file is perfectly
  legal. The rule therefore no longer condemns the code: it dropped from
  ERROR to INFO, and the CLI now resolves the symbols of **all** the files it
  analyses, so the finding disappears as soon as the handler is defined
  somewhere in the analysed set.
* **Known limit:** the resolution covers **only the files given on the
  command line**: a handler defined in a file that is not analysed is still
  reported — as INFO, which does not condemn the code and does not change the
  exit code. Pass every file of the program to make the finding disappear.

## QX004 — the `iofunc_*_verify()` access gate is missing
* **Level:** ERROR
* **Sources:** `iofunc_read_verify()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_read_verify.html> · `iofunc_write_verify()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_write_verify.html>
* **What the documentation says:** "All read handlers should start with a call
  to `iofunc_read_verify()` and proceed only if it returns EOK." — and the same
  for `iofunc_write_verify()`: "All write handlers should start with a call
  to `iofunc_write_verify()` and proceed only if it returns EOK."

  The page of `iofunc_read_verify()` also states what that gate checks:

  > This function checks at least that:
  > the original open included read access
  > the incoming message is well-formed, including that:
  > if an xtype is specified that includes extra data headers, the extra data is in the
  > receive buffer
  > the read offset to be used is non-negative

  and what it returns when the check fails:

  > EBADF
  > The client didn't open the resource for read access.
* **What the rule checks:** the body of the `read`/`write` handler, with the
  strings and the comments blanked, must contain the gate — directly, or
  through a helper function of the same file (a delegated check is a check).
* **What changed in this version:** the search was purely textual. A check
  delegated to a helper was reported as a missing gate (false positive), and
  the *name* of the gate quoted inside an error message was taken for a
  verification (false negative). Both are fixed: strings and comments are
  blanked before the search, and a delegated call counts.
* **Known limit:** the gate is looked for in the body of the handler, **in
  the file being analysed**: a check delegated to a helper of **another**
  file is still reported as a missing gate, even when that helper is part of
  the analysed set. A helper of the **same** file is accepted, and a gate
  merely quoted inside a string does not count — the strings and the
  comments are blanked before the search.

## QX005 — the path mounted by `resmgr_attach()` is relative
* **Level:** WARN
* **Source:** `resmgr_attach()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_attach.html>
* **What the documentation says:**
  > The `resmgr_attach()` function puts the path into the **general pathname
  > space** and binds requests on this path to the dispatch handle `dpp`. You
  > usually provide an absolute path; if you provide a path that doesn't start
  > with a slash, it's considered to be relative to the current working
  > directory.
* **Why this rule exists (and why it is narrow):** an earlier version of the
  tool required a mount point under `/dev/`. That was **wrong**: QNX's pathname
  space is general, and `/var/run/…`, `/tmp/…`, `/etc/…` are valid mount
  points. Reporting those cases was a false positive on canonical code — the
  worst kind of error for this tool. The current rule only reports the
  documented case that depends on the current working directory: a **relative**
  path.
* **What the rule does not do:** it requires nothing about the prefix
  (`/dev/` or otherwise) and it does not trigger when the path is not a
  literal (variable, macro) — in that case, nothing can be said.

## QX006 — no message loop
* **Level:** WARN
* **Sources:** `resmgr_block()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_block.html> · `dispatch_block()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/d/dispatch_block.html>
* **What the documentation says:** `resmgr_block()` "waits for a message" and
  "is a special case of `dispatch_block()`". A resource manager that calls
  neither never waits for a message: it does nothing.

  The two pages, verbatim:

  > The resmgr_block() function waits for a message (created by a call to
  > resmgr_context_alloc()) for context ctp.
  >
  > This function is a special case of dispatch_block() that you should use
  > only with a simple resource manager.
  >
  > The dispatch_block() function blocks by calling MsgReceive() while waiting
  > for an event that's registered using one of the attach functions,
  > message_attach(), pulse_attach(), resmgr_attach(), or select_attach().
* **Why both APIs are accepted:** the reference example in the QNX 8.0
  documentation uses `resmgr_block()`, not `dispatch_block()`. Requiring one of
  the two would produce a false positive on the reference code.
* **What changed in this version:** the rule used to look for a **call** to
  `dispatch_block()` or `resmgr_block()`. A resource manager that hands the
  loop over to a **thread pool** — `pool_attr.block_func = &resmgr_block;` —
  never calls them: it *references* them. The rule now accepts a call **or a
  reference**.
* **What changed in this version (the level):** the rule was at **ERROR**
  and is now at **WARN**. QX-PROBE analyses **one file at a time**, and the
  loop of a resource manager split over several files lives in another
  translation unit: reporting the absence of a loop at ERROR level on the
  file that holds the handlers is a false positive on a valid architecture.
  The level is now the one a single-file tool can defend, and the message
  says exactly what it means — *in this file* — and where to look
  (`pool_attr.block_func`). The measurement that brought this change is in
  [`docs/BENCHMARK.md`](docs/BENCHMARK.md) §6.
* **Known limit:** the rule cannot see the other files of the project. It
  reports what the analysed file contains, and it says so in the message.

## QX007 — the loop blocks but no handler is called
* **Level:** WARN
* **Sources:** `resmgr_handler()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_handler.html> · `dispatch_handler()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/d/dispatch_handler.html>
* **What the documentation says:** `resmgr_handler()` "handles the message
  received in `ctp`" and "is a special case of `dispatch_handler()`". Without
  a call to one of the two, the message stays pending and the client never
  gets an answer.

  The two pages, verbatim:

  > The resmgr_handler() function handles the message received in ctp.
  >
  > The resmgr_handler() function is a special case of dispatch_handler().
  >
  > The dispatch_handler() function handles events received by dispatch_block()
  > and does one of the following:
* **What changed in this version (the level):** like QX006, this rule was at
  **ERROR** and is now at **WARN**, for the same reason: a handler may live
  in another translation unit, and a single file cannot prove that the
  project handles nothing.
* **Known limit:** the rule cannot see the other files of the project. A file
  that blocks but does not call a handler is a **reminder to check the whole
  project**, not a condemnation of the file.

## QX008 — an `io_funcs` slot is not wired
* **Level:** INFO
* **Source:** `resmgr_io_funcs_t()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_io_funcs_t.html>
* **What the documentation says:** "You can initialize this table by calling
  `iofunc_func_init()` and then overriding the defaults with your own
  functions." Each member has a documented default value in the "Default"
  column of the table: `iofunc_read_default()` for `read`,
  `iofunc_write_default()` for `write`, `iofunc_devctl_default()` for `devctl`,
  `iofunc_unblock_default()` for `unblock`; `notify`, on the other hand, has
  **no** default ("None").
* **Why INFO and not ERROR:** a **read-only** resource manager (no `write`) or
  a write-only one (no `read`) is perfectly valid. Requiring `read` and
  `write` at ERROR level blocked valid resource managers — that was a fatal
  false positive. The 64-bit slots (`read64`, `write64`, `notify64`,
  `utime64`) are taken into account as equivalents of their 32-bit
  counterparts, and the slots wired by a C99 initialiser are counted as wired
  too.

## QX009 — the reply returns more parts than the IOV holds
* **Level:** ERROR
* **Sources:** `resmgr_attach()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_attach.html> · `resmgr_context_t()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_context_t.html> · `_RESMGR_NPARTS()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/_resmgr_nparts.html>
* **What the documentation says:**
  > `resmgr_attach()` — `nparts_max`: "The number of components to allocate
  > for the IOV array."
  >
  > `resmgr_context_t()` — `iov`: "An I/O vector where you can place the data
  > that you're returning to the client. This defaults to one entry, but can be
  > configured by the `attr.nparts_max` parameter."
  >
  > `_RESMGR_NPARTS()` — Caveats: "The `resmgr_attach()` function should set
  > `attr->nparts_max` to be the maximum value for `num`."
* **What the rule checks:** if the file declares `resmgr_attr.nparts_max = N`
  and a handler returns `_RESMGR_NPARTS(k)` with `k > N`, the answer to the
  client would carry more parts than the IOV holds.
* **Proof of no false positive:** `k` is only taken into account when it is
  known unambiguously (a literal, or a single assignment in the handler). In
  case of doubt, the rule says nothing.

## QX010 — the number of slots of `iofunc_func_init()` is a macro
* **Level:** INFO
* **Source:** `iofunc_func_init()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_func_init.html>
* **What the documentation says:** "Typically, you pass
  `_RESMGR_CONNECT_NFUNCS` for this argument" and "Typically, you pass
  `_RESMGR_IO_NFUNCS`". That is the normal case; the linter reports it as
  information and draws no conclusion from it (no false "overflow").

## QX011 — an automatic dispatch table is never initialised
* **Level:** WARN
* **Sources:** `iofunc_func_init()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_func_init.html> · `resmgr_io_funcs_t()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_io_funcs_t.html>
* **What the documentation says:** "The `iofunc_func_init()` function
  initializes the passed connect and io structures with the POSIX-layer
  default functions." A table that is never initialised keeps its
  indeterminate values.
* **What the rule checks:** a dispatch table declared as an **automatic**
  variable (on the stack) and never initialised — by `iofunc_func_init()`, by
  a C99 initialiser or by a `memset` to zero. Its function pointers then hold
  indeterminate values.
* **What changed in this version:** the rule used to report **every** table
  that was not filled by `iofunc_func_init()`, including the static ones. A
  static table is zero-initialised by C — that is a deliberate choice (the
  handlers are NULL and the base layer answers `ENOSYS`), not a bug. The
  false positive is gone; the warning still fires on the case it was written
  for.
* **What changed in this version (the storage duration):** the rule used to
  decide that a table was "automatic" because its declaration did not say
  `static`. A table that is a **member of a structure** has the storage
  duration of the object that holds it, and it is filled through the member
  (`iofunc_func_init(…, &resmgr.io_funcs)`). Both were reported by mistake
  on real resource managers, one of them published by QNX itself. The rule
  now computes the storage duration of the declaration, and recognises an
  initialisation made through a member expression.
* **What changed in this version (every call):** the rule used to read the
  **first** `iofunc_func_init()` call of the file and to ignore the next
  ones. A resource manager may fill two io tables — one per device — and the
  second table was reported as uninitialised. The rule now iterates over
  **every** call. The three defects above were found by running the tool on
  17 real resource managers; the measurement is in
  [`docs/BENCHMARK.md`](docs/BENCHMARK.md) §6.
* **Known limit:** the rule recognises the three initialisations it knows —
  `iofunc_func_init()`, a C99 initialiser and a `memset` to zero. A table
  initialised by **copying another table** (`io_funcs = model;`) is not
  recognised and is warned about, although its pointers are perfectly
  defined.

---

## What was corrected in this version, and how it is proved

Seven rules had a known defect that contradicted the official documentation
(QX001, QX002, QX003, QX004, QX006, QX007, QX011). Each of them is now covered
by a test that **fails on the previous code** and **passes on the current
code**:

| Rule | Defect corrected | Test that proves it |
|---|---|---|
| QX001 | the official example of the documentation was reported; C99 initialisers were invisible | `test_qx001_exemple_officiel_de_la_documentation`, `test_qx001_initialiseur_de_structure_c99`, `test_qx001_table_nulle_a_l_attach` |
| QX002 | "slots wired" was compared to "entries filled"; the real overflow was never detected | `test_qx002_slots_cables_au_dela_des_entrees_remplies`, `test_qx002_debordement_du_tableau` |
| QX003 | a handler defined in another translation unit was condemned | `test_qx003_handler_dans_une_autre_unite_de_compilation`, `test_qx003_handler_non_defini` |
| QX004 | a delegated check was missed; a gate quoted in a string counted | `test_qx004_porte_deleguee_a_un_helper`, `test_qx004_porte_citee_dans_une_chaine` |
| QX006 | a loop delegated to a thread pool (`pool_attr.block_func = &resmgr_block`) was not recognised; a resource manager split over several files was condemned at ERROR level | `test_api_resmgr_block_et_resmgr_handler` (the delegated case is asserted in the same test), `test_qx006_boucle_de_messages_absente` |
| QX007 | the same limit as QX006: the handler may live in another translation unit | `test_api_resmgr_block_et_resmgr_handler`, `test_qx007_dispatch_absent` |
| QX011 | a static (zero-initialised) table was warned about; a table that is a member of a structure was called "automatic"; only the first `iofunc_func_init()` call was read | `test_qx011_table_mise_a_zero_statique` (it also covers the member case and the second call), `test_qx011_table_automatique_non_initialisee` |

The last three rows come from the **benchmark on real code** — 17 resource
managers written by other people, seven of them published by QNX or
BlackBerry themselves. The
corpus, the measurement and the manual verification of every finding are in
[`docs/BENCHMARK.md`](docs/BENCHMARK.md).

Reproduce the proof (host only, no QNX SDK needed):

```console
$ bash scripts/run_tests.sh
```

The suite is the two-sided contract: the valid cases must produce **no**
actionable finding, and the sabotaged cases must produce the expected
finding. A rule that was simply deleted proves nothing.

Every one of the eleven rules is cited by at least one test — a rule that no
test cites is a rule that does not exist. Two rules (QX008, the unwired slot
reported as INFO, and QX010, the macro reported as INFO) had no test of
their own until this version; they have one now.

The governing principle stays the same: **a rule that cannot be corrected with
an official source must be deleted** — a rule without a source is worse than an
absent rule.

---

## The contest rules, quoted — video v2 (06/11/2026)

The six requirements below are quoted **verbatim** from the QNX Global
Hackathon rules page, consulted on **06/11/2026** (HTTP 200, 160 476 bytes
for the saved copy — the live page varies by a few hundred bytes with the
session tokens and the page furniture, the text of the rules does not):
<https://qnx.devpost.com/rules>. For each one: how video v2 answers it.

*Re-read on 07/11/2026:* the page answers HTTP 200 again and its **text** is
**identical** to the copy of 06/11/2026 — 39 540 characters of text in both
copies, measured with the same script (HTML tags stripped, blank lines
dropped, the remaining lines joined by newlines). The only difference in that
text is the participant counter, which is live: 601 on the copy of 06/11,
657 then 658 during the re-read of 07/11; replace it by a placeholder and the
two texts are strictly equal. The six quotations below were checked character
by character against the copy fetched on 07/11/2026: all six are still exact.

*Re-read again on 12/11/2026:* the page answers HTTP 200 once more, and the
**text of the rules is still identical** to the copy of 06/11/2026. The body
of the rules — from the title line to the end of the page — gives the same
**37 665 characters** in the four copies saved on 06/11, 07/11, 11/11 and
12/11, measured with the same method as above (HTML tags stripped, blank lines
dropped, the remaining lines joined by newlines; the 39 540 characters of the
paragraph above count the whole page, navigation included). The participant
counter, which is live and sits above that text, went from 601 on 06/11 to
1 192 on 11/11 and 1 310 on 12/11. The six quotations below were checked again,
character by character, against the copy fetched on 12/11/2026: all six are
still exact.

**1. Duration** — "should be less than three (3) minutes".

*How the video answers it:* it runs **71.44 s** (measured with `ffprobe` on
the file of the repository), well under the three minutes, and over the one
minute asked for internally. No scene is shorter than 3.12 s, so every
burned-in subtitle stays on screen for at least 2.5 s.

**2. The device** — "should include footage that shows the Project functioning
on the device for which it was built".

*How the video answers it:* QX-PROBE is a **host tool**: it reads C source
code, it does not run on a QNX board and does not need one. "The device for
which it was built" is therefore **the host machine** that runs the tool —
which the rules confirm in the definition of the category we ticked: "a
host-based tool (Windows, macOS, or Linux) that builds, tests, analyzes, or
otherwise supports software targeting QNX 8.0". The video shows **the real
tool** running on **the real public files of the repository** — the resource
manager published by BlackBerry, a read-only example, a deliberately broken
fixture — with the real output and the real exit code on screen. Nothing is
mocked, no compiler output is simulated, no documentation page is captured.

*If a judge reads this requirement as "the QNX board":* that reading is
defensible, and the two options it implies both have a cost. (a) Running the
C examples on the target requires the **QNX SDP 8.0** under the non-commercial
**QNX Everywhere** licence (a myQNX account) — free in money, but it has to
be signed up for and waited for; (b) running them in a **QEMU** guest
requires the same kit (the QNX 8.0 image and `mkqnximage` come with the SDP).
Both options go through that same licence, which we do not hold. That is why
the video shows the host tool, and why the pack writes `NOT MEASURED` where
the compilation has not been measured, instead of showing simulated output.

**3. YouTube** — "must be uploaded to and made publicly visible on YouTube and
a link to the video must be provided on the submission form on the Hackathon
Website".

*How the video answers it:* the video is in **English** (the rules require
English for every submitted material) and has **no audio track at all** — no
music, no voice-over. The binary file is already in the public repository.
What remains is **one single action by the owner**: upload it to YouTube as
a public video, then paste that URL into the video field of the form. No
account has been created and no video has been published by the automation.

**4. Trademarks and copyright** — "must not include third party trademarks, or
copyrighted music or other material unless the Entrant has permission to use
such material".

*How the video answers it:* the video has **no audio track**, hence no
copyrighted music. The only third-party code shown is
`examples/blackberry_eventfd_mgr.c`, by BlackBerry Limited, redistributed
**without modification** under **Apache-2.0** with its licence header intact:
that licence **is** the permission to use the material, and `NOTICE` carries
the attribution. The sentences of the QNX 8.0 documentation shown on screen
are quoted with the official page that carries them.

**5. Real behaviour** — "must function as depicted in the video".

*How the video answers it:* every command in the video is a command of the
public repository, typed as it is written, and every output on screen was
produced at recording time. A judge can replay them and get the same
results: 27 tests green, exit code 0 on correct code, exit code 1 on the
broken fixture.

**6. Build and run instructions** — "Include build and run instructions
specifying the QNX version, the target (hardware or QEMU), and the toolchain
used".

*How the video answers it:* the submitted tool is a host tool: there is
**nothing to build and nothing to execute on a target**, it needs neither the
QNX SDK nor a board. The QNX version it analyses is **8.0** and the toolchain
is the **Python 3 standard library**. The same three elements are written in
the `BUILD` and `TESTING` blocks of `docs/SUBMISSION-EN.md`, with the `qcc`
build path of the C examples, explicitly marked `NOT MEASURED`.
