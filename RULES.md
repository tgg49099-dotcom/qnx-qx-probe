# The rules of QX-PROBE and their official QNX 8.0 sources

> The French original of this file is kept unmodified in
> [`docs/RULES.fr.md`](docs/RULES.fr.md).

Every rule of the linter is backed by a page of the official **BlackBerry
QNX SDP 8.0** documentation (QNX OS 8.0 C Library Reference). The pages
cited below are all updated as of **11 June 2026**.

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

## QX004 — the `iofunc_*_verify()` access gate is missing
* **Level:** ERROR
* **Sources:** `iofunc_read_verify()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_read_verify.html> · `iofunc_write_verify()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_write_verify.html>
* **What the documentation says:** "All read handlers should start with a call
  to `iofunc_read_verify()` and proceed only if it returns EOK." — and the same
  for `iofunc_write_verify()`.
* **What the rule checks:** the body of the `read`/`write` handler, with the
  strings and the comments blanked, must contain the gate — directly, or
  through a helper function of the same file (a delegated check is a check).
* **What changed in this version:** the search was purely textual. A check
  delegated to a helper was reported as a missing gate (false positive), and
  the *name* of the gate quoted inside an error message was taken for a
  verification (false negative). Both are fixed: strings and comments are
  blanked before the search, and a delegated call counts.

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
* **Level:** ERROR
* **Sources:** `resmgr_block()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_block.html> · `dispatch_block()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/d/dispatch_block.html>
* **What the documentation says:** `resmgr_block()` "waits for a message" and
  "is a special case of `dispatch_block()`". A resource manager that calls
  neither never waits for a message: it does nothing.
* **Why both APIs are accepted:** the reference example in the QNX 8.0
  documentation uses `resmgr_block()`, not `dispatch_block()`. Requiring one of
  the two would produce a false positive on the reference code.

## QX007 — the loop blocks but no handler is called
* **Level:** ERROR
* **Sources:** `resmgr_handler()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_handler.html> · `dispatch_handler()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/d/dispatch_handler.html>
* **What the documentation says:** `resmgr_handler()` "handles the message
  received in `ctp`" and "is a special case of `dispatch_handler()`". Without
  a call to one of the two, the message stays pending and the client never
  gets an answer.

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

---

## What was corrected in this version, and how it is proved

Five rules had a known defect that contradicted the official documentation
(QX001, QX002, QX003, QX004, QX011). Each of them is now covered by a test
that **fails on the previous code** and **passes on the current code**:

| Rule | Defect corrected | Test that proves it |
|---|---|---|
| QX001 | the official example of the documentation was reported; C99 initialisers were invisible | `test_qx001_exemple_officiel_de_la_documentation`, `test_qx001_initialiseur_de_structure_c99`, `test_qx001_table_nulle_a_l_attach` |
| QX002 | "slots wired" was compared to "entries filled"; the real overflow was never detected | `test_qx002_slots_cables_au_dela_des_entrees_remplies`, `test_qx002_debordement_du_tableau` |
| QX003 | a handler defined in another translation unit was condemned | `test_qx003_handler_dans_une_autre_unite_de_compilation`, `test_qx003_handler_non_defini` |
| QX004 | a delegated check was missed; a gate quoted in a string counted | `test_qx004_porte_deleguee_a_un_helper`, `test_qx004_porte_citee_dans_une_chaine` |
| QX011 | a static (zero-initialised) table was warned about | `test_qx011_table_mise_a_zero_statique`, `test_qx011_table_automatique_non_initialisee` |

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
