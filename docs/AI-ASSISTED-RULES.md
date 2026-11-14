# The eleven rules, written with an AI — and how each of them was proved

This file answers one question: **for each of the eleven rules of QX-PROBE,
where does it come from, what did it look like when it was first written, and
what proves it is right today?** Every statement in it can be checked in this
repository, by a judge, without trusting anybody.

It is the companion of [`../RULES.md`](../RULES.md), which lists the rules and
their official QNX 8.0 sources. `RULES.md` is the reference; this file is the
proof.

---

## 0. Who wrote what

| What | Who wrote it | How the facts were re-read | Where it can be checked |
|---|---|---|---|
| The eleven rules, the checker `qx_probe.py`, the 27 tests, this document | an **AI agent** (Claude), working in the repository of the owner, on the instructions of the owner | every quotation, commit name, file name, test name and figure below was re-read **against the files of this repository** — never from memory — and against the **live official pages** | `git log`, `RULES.md`, `tests/test_qx_probe.py`, `scripts/verifier-citations.py` |
| The corrections of the five defective rules found on the examples | the same AI agent, in the commit `9706199` (05/11/2026) | by the **counter-proof** of § 4: the current test suite was run against the *previous* code, and the tests that cover the corrections **failed** | `git show 9706199`, `git show 9706199^:qx_probe.py` |
| The corrections of the two rules the **benchmark on real code** found (QX006, QX007) and of the three false positives of QX011 | the same AI agent, on 11/11/2026, after running the tool on 17 resource managers published by other people | by the same **counter-proof**: the current test suite run against the code of the previous commit (`eeb99e4`) **fails** on 4 assertions, and passes on the current code | `docs/BENCHMARK.md`, `git show eeb99e4:qx_probe.py` |
| The text submitted to the contest, and the decision to submit | the **owner** (Tgg) | the owner pastes the blocks of `docs/SUBMISSION-EN.md`; every block carries its measured character count | `docs/SUBMISSION-EN.md` |
| The QNX 8.0 compilation of the examples, and any run on the target | **nobody — not measured** | there is no QNX SDP 8.0 licence in the environment where the project was written; the build path is prepared and its "no SDK" path is verified, the successful compilation is not | `docs/SUBMISSION-EN.md` § 10, `scripts/build_qcc.sh` |

The AI assistance is declared in [`../NOTICE`](../NOTICE) and in
[`../README.md`](../README.md). **Nothing in this repository was published by
the agent**: the agent wrote code and documents, the owner decides what is
published, what is submitted and what is uploaded.

### The method rule

The rule that governs the whole tool is written in `RULES.md`, at the top:

> Reading convention: **a rule without an official source is a rule that does
> not exist.** When the documentation contradicts a rule, it is the rule that
> gives way — never the canonical QNX code.

and, at the bottom of the correction table:

> The governing principle stays the same: **a rule that cannot be corrected
> with an official source must be deleted** — a rule without a source is worse
> than an absent rule.

An AI agent that invents a rule is exactly the failure this rule forbids. That
is why each of the eleven rules below carries the official page it comes from,
the sentence it depends on, and a test: **a rule that no test cites does not
exist either.**

---

## 1. How to replay everything in this file

```console
$ git clone https://github.com/tgg49099-dotcom/qnx-qx-probe.git && cd qnx-qx-probe
$ bash scripts/run_tests.sh                 # 64 tests, RESULT: QX-PROBE suite GREEN (RC 0)
$ python3 -I scripts/verifier-citations.py  # the 14 official pages, 35 quotations (RC 0)
$ git show bfad852:RULES.md                 # the first draft of the eleven rules
$ git show 9706199 --stat                   # the commit that corrected the five defective rules
$ git show eeb99e4:qx_probe.py > /tmp/old.py  # the code before the corrections of 11/11/2026
```

The counter-proof of § 4 (the tests run against the previous code):

```console
$ cp -r . /tmp/old && cd /tmp/old
$ git show 9706199^:qx_probe.py > qx_probe.py   # the code as it was before the corrections
$ python3 -I tests/test_qx_probe.py             # FAILED (failures=11)
```

`scripts/verifier-citations.py` reads the fourteen official pages and checks that
the sentence each rule depends on is still on the page: it prints `OK`,
`QUOTE NOT FOUND` or `NOT CHECKED`, and **a page it could not read is never
reported as verified**. Its `--self-test` mode proves, without any network
access, that it detects a missing quotation and reports an unreadable page as
`NOT CHECKED`.

---

## 2. The eleven rules, one by one

For each rule: the official page and the sentence it depends on (quoted from
`RULES.md`, word for word), the **first draft** (commit, file and the original
text — the first draft is quoted in French, as it was written, and is *not*
rewritten to look better), and the test that covers it.

### QX001 — no dispatch table wired · **ERROR**

**Official source.** `resmgr_attach()`, `resmgr_io_funcs_t()`,
`iofunc_func_init()` (three pages, listed with their URLs in `RULES.md`).

**The sentence the rule depends on** (verbatim from `RULES.md`):

> "a pointer to the `resmgr_connect_funcs_t` structure that defines the
> POSIX-level connect functions" … "a pointer to the `resmgr_io_funcs_t`
> structure that defines the POSIX-level I/O functions" … "You can initialize
> this table by calling `iofunc_func_init()` and then overriding the defaults
> with your own functions."

**First draft.** Commit `bfad852` (04/11/2026), files `RULES.md` and
`qx_probe.py`. The original limitation it declared, in French:

> « la detection est lexicale (`.slot = handler`). Un initialiseur de structure
> C99 (`resmgr_io_funcs_t f = { .read = my_read };`) ou un nom de variable
> libre n'est pas vu. Une regle plus fine est prevue mais n'est pas
> implementee : mieux vaut un constat manquant qu'un faux positif. »

**The contradiction.** What the documentation says: `iofunc_func_init()` can
initialise the table, and the table can then be overridden member by member —
so a table can be wired in four documented ways (declared, initialised, filled
by `iofunc_func_init()`, or passed to `resmgr_attach()`). What the rule did: it
only recognised `.slot = handler` assignments on a table whose name was one of
`io_funcs`, `dev_funcs`, `connect_funcs` (regex `ASSIGN_RE` of the first
draft). The **official example of the documentation** — `my_io_functions.io_read =
my_io_read;` — was therefore reported as "no dispatch table is assigned". The
first draft said so itself, in its table *"Regles a relire"*:

> « QX001 | les initialiseurs de structure C99 et les noms de variables libres
> ne sont pas detectes | `resmgr_io_funcs_t()` »

**The test that fails on the previous code.**
`test_qx001_exemple_officiel_de_la_documentation` — it runs the checker on
`examples/qnx80_resmgr_official_example.c`, the official example of the
documentation, and requires **no actionable finding**: the first draft reported
one. `test_qx001_initialiseur_de_structure_c99` — a table wired by a C99
initialiser must produce no actionable finding either.
`test_qx001_table_nulle_a_l_attach` — the opposite side: a `NULL` table passed
to `resmgr_attach()` **must** be reported, because the documentation allows
`NULL` only for `attr` ("or NULL to use the default attributes") and says
nothing of the sort about the two dispatch tables.

**The fix.** Commit `9706199` (05/11/2026). The rule now recognises the four
documented ways of wiring a table, accepts both member spellings
(`read` and `io_read`), and reports the `NULL` table. All three tests pass on
the current code.

### QX002 — `iofunc_func_init()` is asked to fill more entries than the table holds · **ERROR**

**Official source.** `iofunc_func_init()`, `resmgr_io_funcs_t()`,
`resmgr_connect_funcs_t()`.

**The sentence the rule depends on:**

> "The number of entries in the io table that you want to fill. Typically, you
> pass `_RESMGR_IO_NFUNCS` for this argument." … "The number of entries in the
> connect table that you want to fill." … "The `nconnect` and `nio` arguments
> indicate how many entries this function should fill. This is in place to
> support forward compatibility."

**First draft.** Commit `bfad852`, `RULES.md` and `qx_probe.py`:

> « `nio` designe un **nombre d'entrees a remplir**, pas une borne de tableau. »
> « Limite connue : la regle compte les slots cables, pas les slots
> *positionnes* dans la structure. Elle est a relire (voir la section "Regles a
> relire" du dossier de travail du projet). »

**The contradiction.** What the documentation says: `nio` and `nconnect` are
the number of entries **to fill**, not the size of the table; the official
example fills the defaults and *then* overrides some of them — in the comment
of that example: "At this point, the defaults have been filled in. You may now
override some of the default functions with functions that you have written".
What the rule did: it
compared the number of **wired slots** with the number of **entries filled**
and reported an "overflow" — a false positive on the official example — and it
never detected the real overflow, a count larger than the table itself. The
first draft declared it:

> « QX002 | le nombre de slots cables n'est pas le nombre de slots *remplis* ;
> le mot "overflow" est trompeur | `iofunc_func_init()` ("how many entries this
> function should fill") »

**The test that fails on the previous code.**
`test_qx002_slots_cables_au_dela_des_entrees_remplies` — wiring more slots
than the number of entries filled is legitimate; the finding `QX002` must
**not** appear. `test_qx002_debordement_du_tableau` — the real overflow must
**appear**: a literal count larger than the table (more than 34 for the io
table, more than 8 for the connect table), because the library then writes
past the end of the structure.

**The fix.** Commit `9706199`. The rule now compares the literal count with
the size of the standard QNX 8.0 tables — `len(IO_FUNC_SLOTS)` = 34 function
members for `resmgr_io_funcs_t` and `len(CONNECT_FUNC_SLOTS)` = 8 for
`resmgr_connect_funcs_t` — and reports nothing else.

### QX003 — a slot points at a function not found in the analysed files · **INFO** (it was **ERROR**)

**Official source.** `resmgr_io_funcs_t()`.

**The sentence the rule depends on:**

> each member of the table is a function pointer
> (`int (*read)(resmgr_context_t *ctp, io_read_t *msg, RESMGR_OCB_T *ocb);`).

**First draft.** Commit `bfad852`:

> « Limite connue : un handler defini dans un autre fichier de compilation est
> signale a tort. Une forme plus exacte (resolution multi-fichiers) est prevue
> mais n'est pas implementee. »

**The contradiction.** What the documentation says: each member is a function
pointer, and the link is resolved by the **linker**, over the whole program.
What the rule did: it searched for the handler in the analysed file only and
condemned it at **ERROR** level — a single compilation unit cannot prove that a
symbol is missing. The first draft declared it:

> « QX003 | un handler defini dans un autre fichier est signale a tort |
> `resmgr_io_funcs_t()` »

**The test that fails on the previous code.**
`test_qx003_handler_dans_une_autre_unite_de_compilation` — a handler defined
in another translation unit must produce **no actionable finding**; the first
draft produced an ERROR. `test_qx003_handler_non_defini` — the opposite side: a
handler that is nowhere to be found must still be reported, and the finding
states the exact condition ("if it is not defined in another translation unit,
the link will fail").

**The fix.** Commit `9706199`. The rule drops from ERROR to INFO, and the CLI
resolves the symbols of **all** the files it analyses: the finding disappears
as soon as the handler is defined somewhere in the analysed set.

### QX004 — the `iofunc_*_verify()` access gate is missing · **ERROR**

**Official source.** `iofunc_read_verify()`, `iofunc_write_verify()`.

**The sentence the rule depends on:**

> "All read handlers should start with a call to `iofunc_read_verify()` and
> proceed only if it returns EOK." — and the same for `iofunc_write_verify()`.

**First draft.** Commit `bfad852`:

> « Limite connue : la recherche est textuelle ; un controle delegue a une
> fonction auxiliaire, ou le nom de la fonction cite dans une chaine de
> caracteres, ne sont pas distingues. »

**The contradiction.** What the documentation says: a read handler *should*
start with the gate call; a delegated check is still a check, and a gate
mentioned inside a string is not a check. What the rule did: it searched the
raw text of the handler body for the name of the function — so a check
delegated to a helper of the same file was reported as a missing gate (a false
positive), and the name of the gate quoted inside an error message was taken
for a verification (a false negative). The first draft declared it:

> « QX004 | la recherche est textuelle (chaine de caracteres, verification
> deleguee) | `iofunc_read_verify()` »

**The test that fails on the previous code.**
`test_qx004_porte_deleguee_a_un_helper` — a gate delegated to a helper of the
same file must produce no `QX004` finding.
`test_qx004_porte_citee_dans_une_chaine` — a gate quoted inside a string
literal must **not** count as a verification.

**The fix.** Commit `9706199`. The strings and the comments are blanked before
the search, and a delegated call counts. `test_qx004_porte_acces_absente` —
the detection side — still requires the finding when no gate is called at all.

### QX005 — the path mounted by `resmgr_attach()` is relative · **WARN**

**Official source.** `resmgr_attach()`.

**The sentence the rule depends on:**

> The `resmgr_attach()` function puts the path into the **general pathname
> space** and binds requests on this path to the dispatch handle `dpp`. You
> usually provide an absolute path; if you provide a path that doesn't start
> with a slash, it's considered to be relative to the current working
> directory.

**First draft.** Commit `bfad852`. The rule already existed in this form in
the first public commit, and it already carried the reason why it is narrow —
in French:

> « une version anterieure de l'outil exigeait un point de montage sous
> `/dev/`. C'etait **faux** : le pathname space de QNX est general, et
> `/var/run/...`, `/tmp/...`, `/etc/...` sont des points de montage valides.
> Signaler ces cas etait un faux positif sur du code canonique — le pire genre
> d'erreur pour cet outil. »

That earlier version is **not** in the public git history: the public history
starts at `bfad852`, with the rule already corrected. The statement is kept
here because it is the reason the rule is narrow.

**The test.** `test_qx005_chemin_relatif` — a relative path produces exactly
one WARN; `scripts/run_tests.sh` checks the same case on the example file
(`examples/qnx80_resmgr_relative_path.c`: 1 WARN, exit code 1). **No
correction was needed for this rule**: the test passes on the first draft and
on the current code.

### QX006 — no message loop · **WARN**

**Official source.** `resmgr_block()`, `dispatch_block()`.

**The sentence the rule depends on:** `resmgr_block()` "waits for a message"
and "is a special case of `dispatch_block()`".

**First draft.** Commit `bfad852`, unchanged since:

> « Pourquoi les deux API sont acceptees : l'exemple de reference de la
> documentation QNX 8.0 utilise `resmgr_block()`, pas `dispatch_block()`.
> Exiger l'un des deux produirait un faux positif sur le code de reference. »

**The test.** `test_qx006_boucle_de_messages_absente` — a file that calls
neither must be reported. It passes on the first draft and on the current code.

**What the benchmark changed (11/11/2026).** The rule was written on examples
and had never met a real resource manager. The corpus of 17 real code files
showed two things: a manager that hands the loop over to a **thread pool**
(`pool_attr.block_func = &resmgr_block;`) never *calls* the blocking function,
it *references* it; and a manager split over several files has its loop in
another translation unit, which a single-file tool cannot see. The first is a
false negative and is fixed (a reference now counts); the second is a false
positive and changed the **level** from ERROR to **WARN**, because a file that
holds the handlers but not the loop is a valid architecture. The message now
says *in this file* and names `pool_attr.block_func`. The measurement is in
[`docs/BENCHMARK.md`](BENCHMARK.md) §6; the proof that the old code fails and
the new code passes is `test_api_resmgr_block_et_resmgr_handler`, which
asserts the delegated case and the level in the same test.

### QX007 — the loop blocks but no handler is called · **WARN**

**Official source.** `resmgr_handler()`, `dispatch_handler()`.

**The sentence the rule depends on:** `resmgr_handler()` "handles the message
received in `ctp`" and "is a special case of `dispatch_handler()`".

**First draft.** Commit `bfad852`, unchanged since:

> « Sans appel a l'un des deux, le message reste en attente et le client ne
> recoit jamais de reponse. »

**The test.** `test_qx007_dispatch_absent`. It passes on the first draft and on
the current code.

**What the benchmark changed (11/11/2026).** Same limit as QX006: the handler
may live in another translation unit, so the level moved from ERROR to **WARN**
and the message says *in this file*. A delegated handler
(`pool_attr.handler_func = (void *)dispatch_handler;`) is also recognised.

### QX008 — an `io_funcs` slot is not wired · **INFO**

**Official source.** `resmgr_io_funcs_t()`.

**The sentence the rule depends on:**

> "You can initialize this table by calling `iofunc_func_init()` and then
> overriding the defaults with your own functions." Each member has a
> documented default value in the "Default" column of the table:
> `iofunc_read_default()` for `read`, `iofunc_write_default()` for `write`,
> `iofunc_devctl_default()` for `devctl`, `iofunc_unblock_default()` for
> `unblock`; `notify`, on the other hand, has **no** default ("None").

**First draft.** Commit `bfad852`. The level was already INFO, and the reason
was already written:

> « Pourquoi INFO et pas ERROR : un gestionnaire en **lecture seule** (pas de
> `write`) ou en **ecriture seule** (pas de `read`) est parfaitement valide.
> Exiger `read` et `write` en ERROR bloquait des gestionnaires valides — c'etait
> un faux positif fatal. »

**The test.** `test_qx008_slot_non_cable_reste_info` — an unwired slot must
stay an **INFO** finding and must not change the exit code. This test did not
exist before commit `9706199`: `RULES.md` says so — "Two rules (QX008 … and
QX010 …) had no test of their own until this version; they have one now." It
passes on the first draft as well: it locks the level, it does not prove a
correction. The same commit made the rule count the slots wired by a C99
initialiser, and report unwired slots **per table** instead of per file.

### QX009 — the reply returns more parts than the IOV holds · **ERROR**

**Official source.** `resmgr_attach()`, `resmgr_context_t()`,
`_RESMGR_NPARTS()`.

**The sentence the rule depends on:**

> `resmgr_attach()` — `nparts_max`: "The number of components to allocate for
> the IOV array." · `resmgr_context_t()` — `iov`: "An I/O vector where you can
> place the data that you're returning to the client. This defaults to one
> entry, but can be configured by the `attr.nparts_max` parameter." ·
> `_RESMGR_NPARTS()` — Caveats: "The `resmgr_attach()` function should set
> `attr->nparts_max` to be the maximum value for `num`."

**First draft.** Commit `bfad852`, unchanged since:

> « Preuve de non-faux-positif : le `k` n'est retenu que s'il est connu sans
> ambiguite (litteral, ou une seule affectation dans le handler). Dans le doute,
> la regle ne dit rien. »

**The tests.** `test_qx009_parts_superieures_a_nparts_max` (the finding must
appear when `k > nparts_max`) and `test_qx009_parts_conformes` (it must not
appear otherwise). Both pass on the first draft and on the current code: this
rule was never defective.

### QX010 — the number of slots of `iofunc_func_init()` is a macro · **INFO**

**Official source.** `iofunc_func_init()`.

**The sentence the rule depends on:** "Typically, you pass
`_RESMGR_CONNECT_NFUNCS` for this argument" and "Typically, you pass
`_RESMGR_IO_NFUNCS`".

**First draft.** Commit `bfad852`:

> « C'est le cas normal ; la sonde le signale comme information, et n'en tire
> aucune conclusion (pas de faux "overflow"). »

**The tests.** `test_qx010_nombre_de_slots_est_une_macro` and
`test_qx010_nombre_de_slots_litteral`. The first was added by commit
`9706199` (the rule had no test of its own before) and passes on the first
draft as well: it locks the behaviour, it does not prove a correction.

### QX011 — an automatic dispatch table is never initialised · **WARN**

**Official source.** `iofunc_func_init()`, `resmgr_io_funcs_t()`.

**The sentence the rule depends on:**

> "The `iofunc_func_init()` function initializes the passed connect and io
> structures with the POSIX-layer default functions."

**First draft.** Commit `bfad852`. The rule was then titled *"aucune table
n'est initialisee par `iofunc_func_init()`"* and declared:

> « Limite connue : une initialisation statique a zero, ou un `memset` de la
> table, est un choix architectural legitime (gestionnaire qui renvoie ENOSYS) ;
> la regle produit alors un avertissement injustifie. Une forme plus fine est
> prevue mais n'est pas implementee. »

**The contradiction.** What the documentation says: `iofunc_func_init()`
initialises the structures with the POSIX defaults — it is one way of
initialising a table among others, not the only one. What the rule did: it
reported **every** table that was not filled by `iofunc_func_init()`, including
the static ones, which C zero-initialises. The first draft declared it:

> « QX011 | une table mise a zero statiquement produit un avertissement
> injustifie | `iofunc_func_init()` »

**The test that fails on the previous code.**
`test_qx011_table_mise_a_zero_statique` — a static table zeroed by C is a
deliberate choice; the finding `QX011` must **not** appear.

**The fix.** Commit `9706199`. The rule now fires only on an **automatic**
table that is never initialised. The other test of the rule,
`test_qx011_table_automatique_non_initialisee`, passes on **both** versions —
by design: it is the case the rule must keep catching, and a rule that stops
catching its own case would prove nothing.

**What the benchmark changed (11/11/2026).** Three more false positives of
the same rule, found on real code — two of them on files published by QNX
itself:

* a table that is a **member of a structure** was called "automatic": it has
  the storage duration of the object that holds it, not that of a stack
  variable;
* a table initialised through a **member expression** (`&resmgr.io_funcs`) was
  not recognised as initialised;
* only the **first** `iofunc_func_init()` call of the file was read, so a
  second table (one per device) was reported as uninitialised.

The rule now computes the storage duration of the declaration, reduces a
member expression to the table it designates, and iterates over **every**
call. The three cases are asserted in `test_qx011_table_mise_a_zero_statique`
(the same test, so that the suite keeps its published size) and the
measurement is in [`docs/BENCHMARK.md`](BENCHMARK.md) §6.

---

## 3. The seven defective rules, in one table

| Rule | What the documentation said | What the rule did | The test that failed on the previous code | Commit |
|---|---|---|---|---|
| QX001 | a table can be wired in four documented ways | only `.slot = handler` on a table named `io_funcs`/`dev_funcs`/`connect_funcs` → the official example was reported | `test_qx001_exemple_officiel_de_la_documentation`, `test_qx001_initialiseur_de_structure_c99` | `9706199` |
| QX002 | `nio`/`nconnect` = entries **to fill** | compared the wired slots with the filled entries → false positive, real overflow never detected | `test_qx002_slots_cables_au_dela_des_entrees_remplies`, `test_qx002_debordement_du_tableau` | `9706199` |
| QX003 | the link is resolved by the linker, over the whole program | condemned a handler defined in another translation unit, at ERROR level | `test_qx003_handler_dans_une_autre_unite_de_compilation`, `test_qx003_handler_non_defini` | `9706199` |
| QX004 | a delegated check is a check; a gate quoted in a string is not | purely textual search: false positive on a delegated check, false negative on a quoted name | `test_qx004_porte_deleguee_a_un_helper`, `test_qx004_porte_citee_dans_une_chaine` | `9706199` |
| QX006 | the loop may be delegated to a thread pool; a project may hold it in another file | looked for a **call** only, and condemned the absence of a loop at ERROR level | `test_api_resmgr_block_et_resmgr_handler` (delegated case) | 11/11/2026 |
| QX007 | the handler may live in another translation unit | condemned the absence of a handler at ERROR level | `test_api_resmgr_block_et_resmgr_handler` (level) | 11/11/2026 |
| QX011 | `iofunc_func_init()` is one way of initialising a table | warned about every table not filled by it, including the static ones (zero-initialised by C), the tables that are members of a structure, and the tables filled by a second call | `test_qx011_table_mise_a_zero_statique` | `9706199` (extended 11/11/2026) |

The commit column says **which version corrected the rule**: the five first
rows were corrected by `9706199` (the examples); the two last rows and the
extension of QX011 were corrected on **11/11/2026**, after the **benchmark on
17 real resource managers** (`docs/BENCHMARK.md`) — the examples of the
repository could not produce them.

---

## 4. The counter-proof, measured

The claim "a test that fails on the previous code and passes on the current
one" is not a promise: it is a measurement, and it can be replayed.

**What was measured, on 07/11/2026** — the *current* test suite
(`tests/test_qx_probe.py`, unchanged since commit `9706199`) was run against
the *previous* code (`git show 9706199^:qx_probe.py`, md5
`44c72bf729913a010632f9e8ad6994f5`), the current code being md5
`bdc705b7636bea56d849a127e7c341a0`:

```
Ran 27 tests in 0.075s
FAILED (failures=11)
```

The **eleven** failures are the ten tests that cover the five corrected rules
(the nine named in the table of § 3, plus
`test_qx001_table_nulle_a_l_attach`), plus `test_summary_line_is_english` (the
first draft printed `RESULTAT: 5 constat(s), 0 ERROR, 0 WARN`; the current code
prints `RESULT: 5 finding(s), 0 ERROR, 0 WARN` — the same commit made the tool
English-only, which the contest rules require).

The other sixteen tests pass on **both** versions — among them the four tests
on the reference examples, BlackBerry's own published resource manager
included, which must stay green. The current code passes the whole suite
(measured on 07/11/2026):

```
Ran 27 tests in 0.129s
OK
RESULT: QX-PROBE suite GREEN (RC 0)
```

(the time varies from one run to another; the three lines that matter are the
number of tests, `OK`, and the exit code)

**What was measured again, on 11/11/2026** — after the benchmark, the *current*
test suite was run against the code of the previous commit (`git show
eeb99e4:qx_probe.py`, md5 `bdc705b7636bea56d849a127e7c341a0`), the code of
that day being md5 `e3c438a67e947240cc6c26d8adf557e9`:

```
Ran 27 tests in 0.224s
FAILED (failures=4)
```

The **four** failures are the four assertions that the benchmark produced: the
delegated loop (QX006/QX007), the table that is a member of a structure, the
table filled by a second `iofunc_func_init()` call, and the level of
QX006/QX007. The other twenty-three tests pass on **both** versions, and the
new code passes the whole suite:

```
Ran 27 tests in 0.167s
OK
```

**What was measured again, on 14/11/2026** — the whole-program test file
(`tests/test_multifile.py`, added with the revision of 14 November 2026) was
run against the code of the previous commit (`git show ef17d75:qx_probe.py`,
md5 `f19865ab9633cdfc2aa5337c89c06a9f`), the code of that day being md5
`9e116ff3d2cd2c0b70e053aae15dc9d5`:

```
Ran 13 tests in 0.626s
FAILED (failures=12)
```

The **twelve** failures are the twelve assertions the revision of 14 November
brings: a handler file alone is not a program without a dispatch table
(QX001), a loop or a gate helper in another file of the same program counts
(QX006, QX007), the root path `""` is not a relative path (QX005), a
block-scope `extern` table is not an automatic table (QX011), an OCB of its
own bound with `resmgr_open_bind()` is an INFO and not an ERROR (QX004), and
the command line reports `--help`, an unknown option and a missing file
without a traceback. The thirteenth test,
`test_iofunc_ocb_without_gate_stays_error`, passes on both versions: it
guards the case the rule must keep catching. The current code passes the
whole file:

```
Ran 13 tests in 0.673s
OK
```

**The code of 12/11/2026** is md5 `b40f0cea4deddb7a253b18053944c5ab`. It
differs from the code of that day by the **header of the file only**: the
update date of the documentation pages was replaced by the sentence that
points at `scripts/verifier-citations.py`, which prints the update date each
cited page carries — QNX republished those pages on 05/11/2026, so a fixed
date in the header would have been false. The eleven rules, their levels,
their messages and their tests are untouched: the same 27 tests pass.

**A test that passes on both versions is not a proof of a correction.** That
is why the table of § 3 names, for each corrected rule, the test that
**failed** on the previous code — and why `test_qx011_table_automatique_non_initialisee`
is described above as a test that passes on both: it guards the case the rule
must keep catching, not a correction.

---

## 5. The limits — what the AI did **not** do

This file is a document about the writing of the rules. It does not widen the
scope of the tool, and it does not close any of the limits the tool already
declares in `RULES.md` (each rule has its own "Known limit" section there).

* **The QNX 8.0 compilation was not performed.** No QNX SDP 8.0 licence was
  available where the project was written. `scripts/build_qcc.sh` is a real
  build path (`qcc -Vgcc_ntox86_64` or `-Vgcc_ntoaarch64le`, `-Werror`, targets
  `x86_64` and `aarch64`); its "no SDK" path is verified and it stops with an explicit
  message and exit code 2 when `qcc` is missing. It never simulates compiler
  output. The successful compilation is **NOT MEASURED**, and it is written as
  such in the submission.
* **Nothing was run on the target.** No QNX board, no QEMU guest, no `qcc`,
  no `mkqnximage`: QX-PROBE is a **host** tool that reads C source, and that
  is what the video shows. The submission says so in the same words.
* **The AI did not decide what is true about QNX.** It read the official
  pages; the sentences are quoted, the pages are cited, and
  `scripts/verifier-citations.py` re-reads them. Where the documentation and a
  rule disagreed, **the rule gave way** — seven times — and each correction is
  now covered by a test that failed before it.
* **The AI did not publish anything.** No account was created, no submission
  was made, no video was uploaded. The owner decides and does.
* **The AI did not write the facts of this file from memory.** Every commit
  name, file name, test name, quotation and figure here was re-read against
  the files of this repository, and the quotations of the official pages were
  re-read against the live pages on **12/11/2026** (`scripts/verifier-citations.py`,
  14 pages read, 35 quotations found, exit code 0).

**What is still open:** the demonstration video has to be uploaded to YouTube
as a public video by the owner, and the submission form has to be filled in
under the owner's DevPost account. Those two actions are outside the reach of
the automation, by the rules of the contest and by the decision of the owner.

---

*QX-PROBE — a static checker for the QNX 8.0 resource-manager protocol.
Apache-2.0. Written with the assistance of a language model; the only factual
sources are the official BlackBerry QNX SDP 8.0 documentation and BlackBerry's
public reference code.*
