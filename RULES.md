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
* **Source:** `resmgr_attach()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_attach.html>
* **What the documentation says:** `resmgr_attach()` takes `connect_funcs` and
  `io_funcs`, "a pointer to the `resmgr_connect_funcs_t` structure that defines
  the POSIX-level connect functions"; without those tables, the resource
  manager has nothing to run for the client.
* **Known limit:** detection is lexical (`.slot = handler`). A C99 structure
  initialiser (`resmgr_io_funcs_t f = { .read = my_read };`) or a free variable
  name is not seen. A finer rule is planned but not implemented: a missing
  finding is better than a false positive.

## QX002 — more slots wired than `iofunc_func_init()` fills
* **Level:** ERROR
* **Source:** `iofunc_func_init()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_func_init.html>
* **What the documentation says:** "The `nconnect` and `nio` arguments indicate
  how many entries this function should fill. This is in place to support
  forward compatibility." — `nio` designates a **number of entries to fill**,
  not an array bound.
* **Known limit:** the rule counts the slots that are *wired*, not the slots
  that are *positioned* in the structure. To be re-read (see "Rules to
  re-read").

## QX003 — a slot points at an undefined function
* **Level:** ERROR
* **Source:** `resmgr_io_funcs_t()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_io_funcs_t.html>
* **What the documentation says:** each member of the table is a function
  pointer (`int (*read)(resmgr_context_t *ctp, io_read_t *msg, RESMGR_OCB_T *ocb);`).
  A null pointer, or one to a function that does not exist, is not a resource
  manager.
* **Known limit:** a handler defined in another compilation unit is reported
  by mistake. A more exact form (multi-file resolution) is planned but not
  implemented.

## QX004 — the `iofunc_*_verify()` access gate is missing
* **Level:** ERROR
* **Sources:** `iofunc_read_verify()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_read_verify.html> · `iofunc_write_verify()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_write_verify.html>
* **What the documentation says:** "All read handlers should start with a call
  to `iofunc_read_verify()` and proceed only if it returns EOK."
* **Known limit:** the search is textual; a check delegated to a helper
  function, or the name of the function quoted inside a string, is not
  distinguished.

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
  counterparts.

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

## QX011 — no table is initialised by `iofunc_func_init()`
* **Level:** WARN
* **Source:** `iofunc_func_init()` — <https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_func_init.html>
* **What the documentation says:** it is this function that fills the tables
  with the POSIX default values. Without it, the pointers keep their initial
  value.
* **Known limit:** a static zero initialisation, or a `memset` of the table,
  is a legitimate architectural choice (a resource manager that returns
  ENOSYS); the rule then produces an unjustified warning. A finer form is
  planned but not implemented.

---

## Rules to re-read (known, not corrected in this version)

They are flagged here out of honesty: they are in the code, and the jury must
know.

| Rule | Known problem | The documentation that contradicts it |
|---|---|---|
| QX002 | the number of slots wired is not the number of slots *filled*; the word "overflow" is misleading | `iofunc_func_init()` ("how many entries this function should fill") |
| QX001 | C99 structure initialisers and free variable names are not detected | `resmgr_io_funcs_t()` |
| QX003 | a handler defined in another file is reported by mistake | `resmgr_io_funcs_t()` |
| QX004 | the search is textual (string match, delegated check) | `iofunc_read_verify()` |
| QX011 | a table statically zeroed produces an unjustified warning | `iofunc_func_init()` |

The principle that governs all of them: **a rule that cannot be corrected with
an official source must be deleted** — a rule without a source is worse than an
absent rule.
