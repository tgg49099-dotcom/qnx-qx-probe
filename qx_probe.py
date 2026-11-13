#!/usr/bin/env python3
"""QX-PROBE — static checker for the QNX 8.0 resource-manager protocol.

Host tool: reads C code and reports structural facts about the QNX 8.0
resource-manager (resmgr) protocol. No dependency, no QNX SDK required.

EVERY RULE IS BACKED BY AN OFFICIAL PAGE of the BlackBerry QNX SDP 8.0
documentation (C Library Reference). The official URLs are quoted in the
comment of each rule and collected in RULES.md; scripts/verifier-citations.py
re-reads those pages and prints the update date each one carries.  Golden
rule: ZERO false positives — a rule that misreports canonical QNX 8.0 code
is worse than a missing rule.

Usage:  python3 -I qx_probe.py [--format text|json|sarif] <file.c> [file.c ...]
Exit:   0 = no actionable finding, 1 = at least one ERROR or WARN finding,
        2 = bad usage.  INFO never changes the exit code.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass

# ---------------------------------------------------------------- QNX surface

QNX_HEADERS = ("<sys/resmgr.h>", "<sys/dispatch.h>", "<sys/iofunc.h>",
               "<sys/dispatchnode.h>", "<sys/netmgr.h>")

# QNX 8.0 resmgr_io_funcs_t table: official declaration order.
# Source : https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_io_funcs_t.html
IO_FUNC_SLOTS = (
    "read", "write", "close_ocb", "stat", "notify", "devctl", "unblock",
    "pathconf", "lseek", "chmod", "chown", "utime", "openfd", "fdinfo",
    "lock", "space", "shutdown", "mmap", "msg", "reserved", "dup",
    "close_dup", "lock_ocb", "unlock_ocb", "sync", "power", "acl",
    "pause", "unpause", "read64", "write64", "notify64", "utime64",
    "check_msg",
)

# QNX 8.0 resmgr_connect_funcs_t table: official declaration order.
# Source : https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_connect_funcs_t.html
CONNECT_FUNC_SLOTS = (
    "open", "unlink", "rename", "mknod", "readlink", "link", "unblock", "mount",
)

# 64-bit slot and its 32-bit equivalent (resmgr_io_funcs_t, QNX 8.0).
IO_FUNC_ALIASES = {"read64": "read", "write64": "write",
                   "notify64": "notify", "utime64": "utime"}

# The official iofunc_func_init() example writes the member "io_read" while the
# resmgr_io_funcs_t() structure declares "read": BOTH spellings are accepted, so
# the checker cannot misfire and invent a finding on the documentation's own code.
SLOT_NAMES = (frozenset(IO_FUNC_SLOTS) | frozenset(CONNECT_FUNC_SLOTS) |
              frozenset("io_" + s for s in IO_FUNC_SLOTS))

# Documented POSIX defaults for the io_funcs slots ("Default" column of
# resmgr_io_funcs_t).  None = no default (the slot is not handled unless the
# developer wires it).
IO_FUNC_DEFAULTS = {
    "read": "iofunc_read_default()",
    "write": "iofunc_write_default()",
    "devctl": "iofunc_devctl_default()",
    "unblock": "iofunc_unblock_default()",
    "notify": None,
}

# iofunc_func_init(): connect_nfuncs, connect_funcs, io_nfuncs, io_funcs
NFUNCS_RE = re.compile(
    r"iofunc_func_init\s*\(\s*([^,]+?)\s*,\s*([^,]+?)\s*,\s*([^,]+?)\s*,\s*([^)]+?)\s*\)",
    re.DOTALL)
# Assignment of a table slot: <variable> . <slot> = <handler>.
# The variable name is free: the official iofunc_func_init() example uses
# "my_io_functions", most code uses "io_funcs".
MEMBER_ASSIGN_RE = re.compile(
    r"\b([A-Za-z_]\w*)\s*\.\s*([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)")
# Declaration of a dispatch table (with or without a C99 initialiser).
TABLE_DECL_RE = re.compile(
    r"\b(resmgr_io_funcs_t|resmgr_connect_funcs_t)\s+([A-Za-z_]\w*)\s*(=\s*\{[^}]*\})?")
# Explicit zero initialiser: = {0} or = {NULL}.
ZERO_INIT_RE = re.compile(r"=\s*\{\s*(?:0|NULL)\s*\}")
# memset(&table, 0, ...): the table is explicitly zeroed.
MEMSET_ZERO_RE = re.compile(r"memset\s*\(\s*&\s*([A-Za-z_]\w*)\s*,\s*0\s*,")
# QX009: number of parts returned to the client / size of the IOV.
# Sources: resmgr_attach() (attr.nparts_max = "The number of components to
# allocate for the IOV array"), resmgr_context_t() (iov), _RESMGR_NPARTS()
# (Caveats: "The resmgr_attach() function should set attr->nparts_max to be
# the maximum value for num").
NPARTS_MAX_RE = re.compile(r"\bnparts_max\s*=\s*(\d+)\s*;")
NPARTS_RE = re.compile(r"\b_RESMGR_NPARTS\s*\(\s*([A-Za-z_]\w*|\d+)\s*\)")
ASSIGN_INT_RE = re.compile(r"\b([A-Za-z_]\w*)\s*=\s*(\d+)\s*;")

# Function call (name + "("): used to find the helpers of a handler.
CALL_RE = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
HANDLER_RE = re.compile(
    r"^\s*(?:static\s+)?int\s+([A-Za-z_]\w*)\s*\(", re.MULTILINE)
FUNC_DEF_RE = re.compile(
    r"^[ \t]*(?:static\s+|extern\s+|inline\s+)*int\s+([A-Za-z_]\w*)\s*\(", re.MULTILINE)

# C keywords that are not function calls.
C_KEYWORDS = frozenset((
    "if", "else", "for", "while", "switch", "case", "return", "sizeof",
    "do", "break", "continue", "goto", "defined", "static_cast",
))


@dataclass
class Finding:
    level: str        # ERROR | WARN | INFO
    code: str
    where: str
    message: str
    line: int = 1     # 1-based line in the raw file (used by every output format)

    def loc(self) -> str:
        """`file:line`, the location format of gcc and clang.

        Editors, IDEs (VS Code, Eclipse-based QNX Momentics) and CI log
        viewers turn `file:line:` into a link to the source line.
        """
        return f"{file_of(self.where)}:{max(1, self.line)}"


def strip_comments(src: str) -> str:
    """Remove /* */ and // comments, keeping string literals intact."""
    out = []
    i, n = 0, len(src)
    while i < n:
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            end = n if j < 0 else j + 2
            # keep the line breaks of a block comment: every reported line
            # number must be the line of the RAW file.
            out.append(" " + "\n" * src.count("\n", i, end))
            i = end
        elif src.startswith("//", i):
            j = src.find("\n", i)
            i = n if j < 0 else j
            out.append(" ")
        elif src[i] == '"':
            j = i + 1
            while j < n and src[j] != '"':
                j += 2 if src[j] == "\\" else 1
            out.append(src[i:j + 1])
            i = j + 1
        elif src[i] == "'":
            # character literal: it can contain a brace ('{').
            j = i + 1
            while j < n and src[j] != "'":
                j += 2 if src[j] == "\\" else 1
            out.append(src[i:j + 1])
            i = j + 1
        else:
            out.append(src[i])
            i += 1
    return "".join(out)


def blank_strings(src: str) -> str:
    """Replaces the CONTENT of string literals with spaces.

    The length of the literal is preserved: offsets stay valid and string
    text can no longer disturb the analysis (parentheses, braces, keywords).
    Character literals are treated the same way: '{' must not corrupt the
    brace counting.
    """
    out = list(src)
    i, n = 0, len(src)
    while i < n:
        if src[i] == '"':
            j = i + 1
            while j < n and src[j] != '"':
                j += 2 if src[j] == "\\" else 1
            for k in range(i + 1, min(j, n)):
                out[k] = " "
            i = min(j + 1, n)
        elif src[i] == "'":
            j = i + 1
            while j < n and src[j] != "'":
                j += 2 if src[j] == "\\" else 1
            for k in range(i + 1, min(j, n)):
                out[k] = " "
            i = min(j + 1, n)
        else:
            i += 1
    return "".join(out)


def split_args(src: str, open_paren: int) -> list[tuple[int, int]]:
    """Splits the arguments of a C call. Returns [(start, end), ...].

    open_paren is the index of the opening '('. The split ignores nested
    commas and commas inside a string literal.
    """
    blanked = blank_strings(src)
    depth = 0
    i = open_paren + 1
    spans: list[tuple[int, int]] = []
    start = i
    while i < len(blanked):
        c = blanked[i]
        if c in "([{":
            depth += 1
        elif c in ")]}":
            if depth == 0:
                break
            depth -= 1
        elif c == "," and depth == 0:
            spans.append((start, i))
            start = i + 1
        i += 1
    spans.append((start, i))
    return [(a, b) for a, b in spans if src[a:b].strip()]


def string_literal(text: str) -> str | None:
    """Returns the content of a string literal, or None if it is not one."""
    m = re.fullmatch(r'"((?:[^"\\]|\\.)*)"', text.strip())
    return m.group(1) if m else None


def function_body(src: str, name: str, open_paren: int) -> str | None:
    """Returns the body (braces excluded) of the function `name`, or None."""
    blanked = blank_strings(src)
    depth = 0
    i = open_paren
    while i < len(blanked):
        c = blanked[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                break
        i += 1
    else:
        return None
    j = i + 1
    while j < len(src) and src[j] in " \t\r\n":
        j += 1
    if j >= len(src) or src[j] != "{":
        return None
    depth = 1
    k = j + 1
    while k < len(src):
        c = src[k]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return blank_strings(src[j + 1:k])
        k += 1
    return None


def all_functions(src: str) -> dict[str, str]:
    """Returns {name: body} for every `int` function defined in the file."""
    out: dict[str, str] = {}
    for m in FUNC_DEF_RE.finditer(src):
        name = m.group(1)
        if name in out:
            continue
        body = function_body(src, name, m.end() - 1)
        if body is not None:
            out[name] = body
    return out


def body_of(src: str, name: str) -> str | None:
    """Returns the body of the function `name` (strings blanked), or None."""
    for m in FUNC_DEF_RE.finditer(src):
        if m.group(1) != name:
            continue
        body = function_body(src, name, m.end() - 1)
        if body is not None:
            return body
    return None


def resolve_count(body: str, ident: str) -> int | None:
    """Resolves an integer used as a part count.

    Returns the integer if — and only if — it is known without ambiguity: a
    direct literal, or exactly one `ident = <integer>;` assignment in the body.
    Otherwise None (we say nothing rather than being wrong).
    """
    if ident.isdigit():
        return int(ident)
    found = [int(v) for _n, v in ASSIGN_INT_RE.findall(body) if _n == ident]
    if len(found) == 1:
        return found[0]
    return None


def line_of(src: str, pos: int) -> int:
    return src.count("\n", 0, pos) + 1


def def_line(src: str, name: str) -> int:
    """Line of the definition of the function `name` (1 if not found)."""
    for m in FUNC_DEF_RE.finditer(src):
        if m.group(1) == name and function_body(src, name, m.end() - 1) is not None:
            return line_of(src, m.start(1))
    return 1


def assign_line(src: str, slot: str, handler: str) -> int:
    """Line where `slot` is wired to `handler` (1 if not found)."""
    m = re.search(r"\.\s*" + re.escape(slot) + r"\s*=\s*" + re.escape(handler) + r"\b", src)
    return line_of(src, m.start()) if m else 1


def ident_of(expr: str) -> str | None:
    """Returns the identifier of a simple expression (&x, *x, x), or None.

    A member expression is reduced to its LAST component: the dispatch
    tables of a resource manager are often members of a structure
    (&resmgr->io_funcs, &resmgr.connect_funcs), and the table is then named
    after the member, not after the structure.
    """
    e = expr.strip()
    while e.startswith("&") or e.startswith("*"):
        e = e[1:].strip()
    if "." in e or "->" in e:
        e = re.split(r"->|\.", e)[-1].strip()
    if not re.fullmatch(r"[A-Za-z_]\w*", e):
        return None
    return e


def slot_assignments(src: str) -> list[tuple[str, str, str]]:
    """Returns [(table, slot, handler)] for every wired table slot.

    The slot name must belong to an official QNX 8.0 table
    (resmgr_io_funcs_t / resmgr_connect_funcs_t); the variable name is free,
    as in the official iofunc_func_init() example.
    """
    out = []
    for m in MEMBER_ASSIGN_RE.finditer(src):
        table, slot, handler = m.group(1), m.group(2), m.group(3)
        if slot in SLOT_NAMES:
            out.append((table, slot, handler))
    return out


def designated_assignments(src: str) -> list[tuple[str, str, str]]:
    """Returns [(table, slot, handler)] for the C99 initialisers.

    resmgr_io_funcs_t f = { .read = my_read, .write = my_write };
    wires the table just as legitimately as f.read = my_read.
    """
    out = []
    for m in TABLE_DECL_RE.finditer(src):
        name, init = m.group(2), m.group(3)
        if not init:
            continue
        for d in re.finditer(r"\.\s*([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)", init):
            slot, handler = d.group(1), d.group(2)
            if slot in SLOT_NAMES:
                out.append((name, slot, handler))
    return out


def all_assignments(src: str) -> list[tuple[str, str, str]]:
    """Every slot assignment, whatever its form."""
    return slot_assignments(src) + designated_assignments(src)


def base_slot(slot: str) -> str:
    """Maps a slot back to its official name (io_read -> read)."""
    return slot[3:] if slot.startswith("io_") and slot[3:] in IO_FUNC_SLOTS else slot


def dispatch_tables(src: str) -> dict[str, dict]:
    """Returns {name: infos} for the dispatch tables seen in this file.

    A table is "wired" if it is
      * declared in the file (resmgr_io_funcs_t / resmgr_connect_funcs_t),
      * or one of its slots is assigned,
      * or it is C99-initialised (resmgr_io_funcs_t f = { .read = ... }),
      * or it is filled by iofunc_func_init(),
      * or it is passed to resmgr_attach() / message_attach().

    Sources: resmgr_attach() (io_funcs argument), resmgr_io_funcs_t()
    ("You can initialize this table by calling iofunc_func_init() and then
    overriding the defaults with your own functions").
    """
    tables: dict[str, dict] = {}

    def touch(name: str) -> dict:
        return tables.setdefault(name, {"declared": False, "zero": False,
                                        "auto": False, "used": False, "type": None,
                                        "slots": set()})

    # 1. declarations (with a possible C99 initialiser)
    for m in TABLE_DECL_RE.finditer(src):
        name = m.group(2)
        info = touch(name)
        info["declared"] = True
        info.setdefault("pos", m.start())
        info["type"] = m.group(1)
        init = m.group(3)
        if init and ZERO_INIT_RE.search(init):
            info["zero"] = True
        elif not init:
            # a static-storage declaration is zeroed by C; an automatic
            # declaration (inside a function) is not.  A member of a
            # structure has the storage duration of the object that holds
            # it: it is neither, and the rule must then say nothing.
            info["auto"] = block_kind(src, m.start()) == "function"

    # 2. slot assignments
    for table, slot, _handler in all_assignments(src):
        info = touch(table)
        info["used"] = True
        info["slots"].add(slot)

    # 3. tables filled by iofunc_func_init() — EVERY call: a resource
    # manager may fill two tables in two calls (a second io table for a
    # second device, for instance).
    for m in NFUNCS_RE.finditer(src):
        for expr in (m.group(2), m.group(4)):
            name = ident_of(expr)
            if name:
                touch(name)["used"] = True

    # 4. tables passed to resmgr_attach() / message_attach()
    for call in ("resmgr_attach", "message_attach"):
        for m2 in re.finditer(r"\b" + call + r"\s*\(", src):
            for a, b in split_args(src, m2.end() - 1):
                name = ident_of(src[a:b])
                if name:
                    touch(name)["used"] = True

    # 5. tables explicitly zeroed (memset)
    for name in MEMSET_ZERO_RE.findall(src):
        if name in tables:
            tables[name]["zero"] = True

    return tables


def depth_at(src: str, pos: int) -> int:
    """Brace depth at position `pos` (0 = file level)."""
    blanked = blank_strings(src)
    depth = 0
    for i in range(min(pos, len(blanked))):
        if blanked[i] == "{":
            depth += 1
        elif blanked[i] == "}":
            depth -= 1
    return depth


def block_kind(src: str, pos: int) -> str:
    """Tells where a declaration sits: "struct", "function" or "file".

    A member of a structure or of a union has NO storage duration of its
    own: it has the one of the object that contains it.  Telling a member
    apart from a local variable is therefore necessary before calling a
    dispatch table "automatic" (a member of a static structure is zeroed by
    C, a local variable is not).
    """
    blanked = blank_strings(src)
    stack: list[int] = []
    for i in range(min(pos, len(blanked))):
        if blanked[i] == "{":
            stack.append(i)
        elif blanked[i] == "}" and stack:
            stack.pop()
    if not stack:
        return "file"
    head = src[max(0, stack[-1] - 400):stack[-1]]
    if re.search(r"\b(?:struct|union)\b[^{};]*\{", head):
        return "struct"
    return "function"


def gate_present(body: str, want: str, src: str) -> bool:
    """True if the access gate `want` is called, directly or through a helper.

    The body has its strings blanked: a gate quoted in an error message does
    not count.  A check delegated to a helper of the file counts too (the body
    of the helper is read as well).
    """
    if want in body:
        return True
    for callee in set(CALL_RE.findall(body)):
        if callee in C_KEYWORDS or callee == want:
            continue
        helper = body_of(src, callee)
        if helper is not None and want in helper:
            return True
    return False


def analyse(path: str, raw: str, known_symbols: set[str] | None = None) -> list[Finding]:
    """Analyses one C file.

    `known_symbols`: symbols defined or declared in the OTHER analysed files
    (the CLI accepts several files); without them the checker cannot know that
    a handler is defined in another translation unit.
    """
    f: list[Finding] = []
    src = strip_comments(raw)

    headers = [h for h in QNX_HEADERS if h in src]
    is_resmgr = "resmgr" in src or "dispatch" in src
    if not is_resmgr:
        return f

    assigns = all_assignments(src)
    tables = dispatch_tables(src)

    # C1 — a file that uses the resmgr API must wire a dispatch table.
    # Sources : resmgr_attach() (io_funcs : "A pointer to the resmgr_io_funcs_t
    # structure that defines the POSIX-level I/O functions"), resmgr_io_funcs_t()
    # ("You can initialize this table by calling iofunc_func_init() and then
    # overriding the defaults with your own functions").
    if not tables:
        m0 = re.search(r"\bresmgr_attach\s*\(", src)
        f.append(Finding("ERROR", "QX001", path,
                         "file uses the QNX resmgr API but no dispatch table is wired "
                         "(no resmgr_io_funcs_t / resmgr_connect_funcs_t table is "
                         "declared, initialised, filled by iofunc_func_init() or passed "
                         "to resmgr_attach())", line_of(src, m0.start()) if m0 else 1))
        return f

    # C1 bis — resmgr_attach() with a NULL table.
    # Source: resmgr_attach() — for the "attr" argument the documentation
    # explicitly says "or NULL to use the default attributes"; for
    # "connect_funcs" and "io_funcs" it does NOT: a NULL table means a
    # resource manager with no handler at all.
    for m2 in re.finditer(r"\bresmgr_attach\s*\(", src):
        args = split_args(src, m2.end() - 1)
        if len(args) < 7:
            continue
        for idx, label in ((5, "connect_funcs"), (6, "io_funcs")):
            if src[args[idx][0]:args[idx][1]].strip() == "NULL":
                f.append(Finding("ERROR", "QX001", f"{path}:{line_of(src, m2.start())}",
                                 f"resmgr_attach() attaches the resource manager with a NULL "
                                 f"{label} table: the resource manager has no handler at all",
                                 line_of(src, m2.start())))

    # C2 — iofunc_func_init() must not be asked to fill more entries than the
    # table holds.
    # Sources : iofunc_func_init() (nio : "The number of entries in the io table
    # that you want to fill"), resmgr_io_funcs_t() (the table and its members),
    # resmgr_connect_funcs_t() (same for the connect table).
    init_tables: set[str] = set()
    for m in NFUNCS_RE.finditer(src):
        conn_n, conn_f, io_n, io_f = (x.strip() for x in m.groups())
        for name in (ident_of(conn_f), ident_of(io_f)):
            if name:
                init_tables.add(name)
        for label, n_expr, count in (("io", io_n, len(IO_FUNC_SLOTS)),
                                     ("connect", conn_n, len(CONNECT_FUNC_SLOTS))):
            if not n_expr.isdigit():
                f.append(Finding("INFO", "QX010", path,
                                 f"{label} function count '{n_expr}' is not a literal (macro)",
                                 line_of(src, m.start())))
                continue
            n = int(n_expr)
            if n > count:
                f.append(Finding("ERROR", "QX002", path,
                                 f"iofunc_func_init() is asked to fill {n} entries of the "
                                 f"{label} table, which has {count} function members in QNX 8.0: "
                                 f"the library writes past the end of the structure",
                                 line_of(src, m.start())))

    # C3 — the dispatch tables must be initialised: an automatic table that is
    # never initialised holds indeterminate function pointers.
    # Sources : iofunc_func_init() ("initializes the passed connect and io
    # structures with the POSIX-layer default functions"), resmgr_io_funcs_t().
    for name, info in tables.items():
        if not info["declared"]:
            continue                      # the table lives in another unit
        if name in init_tables:
            continue                      # filled by iofunc_func_init()
        if info["zero"] or not info["auto"]:
            continue                      # static storage: zeroed by C
        f.append(Finding("WARN", "QX011", path,
                         f"the dispatch table '{name}' is an automatic variable that is never "
                         f"initialised: its function pointers hold indeterminate values "
                         f"(iofunc_func_init() or an explicit zero initialiser is expected)",
                         line_of(src, info.get("pos", 0))))

    # C4 — every assigned handler must be a function of the analysed sources.
    # Sources: resmgr_io_funcs_t() (each member is a function pointer).
    # A single file cannot prove that a handler is undefined: the checker
    # therefore no longer CONDENNS it, it reports it (level INFO).
    defined = set(HANDLER_RE.findall(src)) | set(known_symbols or ())
    for table, slot, handler in assigns:
        # A NULL pointer is not a handler that could be missing at link
        # time (x.mount = NULL also hits iofunc_attr_t.mount, which is not
        # a dispatch slot at all): nothing to report.
        if handler == "NULL":
            continue
        if handler not in defined:
            f.append(Finding("INFO", "QX003", f"{path}:{slot}",
                             f"{table}.{slot} = {handler}: this handler is neither defined nor "
                             f"declared in the analysed files; if it is not defined in another "
                             f"translation unit, the link will fail",
                             assign_line(src, slot, handler)))

    # C5 — io_read / io_write must call the iofunc_*_verify() gate.
    # Sources : iofunc_read_verify() ("All read handlers should start with a
    # call to iofunc_read_verify() and proceed only if it returns EOK"),
    # iofunc_write_verify() (same for writes).
    for table, slot, handler in assigns:
        slot = base_slot(slot)
        if slot not in ("read", "write"):
            continue
        body = body_of(src, handler)
        if body is None:
            continue
        want = "iofunc_read_verify" if slot == "read" else "iofunc_write_verify"
        if not gate_present(body, want, src):
            f.append(Finding("ERROR", "QX004", f"{path}:{slot}",
                             f"{handler}() never calls {want}(): the access gate is missing",
                             def_line(src, handler)))

    # C6 — the path attached by resmgr_attach() should be ABSOLUTE.
    # Source: resmgr_attach() — "You usually provide an absolute path; if you
    # provide a path that doesn't start with a slash, it's considered to be
    # relative to the current working directory."
    # The QNX pathname space is GENERAL: a mount point outside /dev/
    # (/var/run, /tmp, /etc, ...) is perfectly valid — no finding.
    # Only finding: a relative path, whose resolution depends on the current
    # working directory (hence on the start-up context of the resmgr).
    # https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_attach.html
    for m2 in re.finditer(r"\bresmgr_attach\s*\(", src):
        args = split_args(src, m2.end() - 1)
        if len(args) < 3:
            continue
        lit = string_literal(src[args[2][0]:args[2][1]])
        if lit is None:
            continue          # non-literal path (variable, macro): nothing to say
        if not lit.startswith("/"):
            f.append(Finding("WARN", "QX005", f"{path}:{line_of(src, m2.start())}",
                             f"resmgr_attach() attaches the relative path '{lit}': "
                             f"QNX resolves it against the current working directory "
                             f"(an absolute path is recommended)",
                             line_of(src, m2.start())))

    # C7 — the message loop: block, then dispatch.
    # Sources: resmgr_block() — "This function is a special case of
    # dispatch_block() that you should use only with a simple resource
    # manager."; resmgr_handler() — "This function is a special case of
    # dispatch_handler()."
    # Both APIs are canonical: demanding one or the other would produce a
    # false positive on the QNX 8.0 reference code.
    # A message loop is often DELEGATED: a thread pool takes the blocking
    # function as a pointer (pool_attr.block_func = &resmgr_block), so a
    # reference to the function counts as a loop, not only a call.
    # What is left is a WARN, not an ERROR: one translation unit cannot
    # prove that the project has no message loop — in a resource manager
    # split over several files, the loop usually lives in the file that
    # creates the dispatch context.
    # https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_block.html
    # https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_handler.html
    code = strip_comments(blank_strings(src))
    has_block = bool(re.search(r"\b(?:dispatch_block|resmgr_block)\b", code))
    has_handler = bool(re.search(r"\b(?:dispatch_handler|resmgr_handler)\b", code))
    m_att = re.search(r"\bresmgr_attach\s*\(", code)
    loop_line = line_of(code, m_att.start()) if m_att else 1
    if not has_block:
        f.append(Finding("WARN", "QX006", path,
                         "no message loop in this file: neither dispatch_block() nor "
                         "resmgr_block() is called or referenced here; in a resource "
                         "manager split over several files the loop usually lives in "
                         "another translation unit (it is then set in "
                         "pool_attr.block_func) — check the whole project", loop_line))
    elif not has_handler:
        f.append(Finding("WARN", "QX007", path,
                         "the message loop blocks (dispatch_block()/resmgr_block()) but no "
                         "handler is called or referenced (neither dispatch_handler() "
                         "nor resmgr_handler()) in this file", loop_line))

    # C8 — report the io_funcs slots left unassigned (informational).
    # Source: resmgr_io_funcs_t — "You can initialize this table by calling
    # iofunc_func_init() and then overriding the defaults with your own
    # functions."  Every unwired slot keeps the documented POSIX default
    # (iofunc_read_default(), iofunc_write_default(), ...) or stays NULL when
    # no default exists.  A read-only resmgr (no write) is therefore VALID:
    # a missing slot is never an ERROR any more.
    # https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_io_funcs_t.html
    io_tables = [name for name, info in tables.items()
                 if info["declared"] and info["type"] == "resmgr_io_funcs_t"]
    for name in io_tables:
        assigned_io = {base_slot(slot) for slot in tables[name]["slots"]}
        covered = {IO_FUNC_ALIASES.get(s, s) for s in assigned_io}
        for slot in ("read", "write", "devctl", "unblock", "notify"):
            if slot in covered:
                continue
            default = IO_FUNC_DEFAULTS.get(slot)
            if default:
                detail = f"the POSIX default {default} applies unless you override it"
            else:
                detail = "QNX 8.0 defines no default for this slot: the message is not handled"
            f.append(Finding("INFO", "QX008", f"{path}:{name}",
                             f"{name}.{slot} is not assigned ({detail})",
                             line_of(src, tables[name].get("pos", 0))))

    # C9 — the number of returned parts cannot exceed the declared IOV.
    # Sources: resmgr_attach() — attr.nparts_max = "The number of components
    # to allocate for the IOV array."; resmgr_context_t() — iov (output) An
    # I/O vector where you can place the data that you're returning to the
    # client. This defaults to one entry, but can be configured by the
    # attr.nparts_max parameter; _RESMGR_NPARTS() — "The resmgr_attach()
    # function should set attr->nparts_max to be the maximum value for num."
    # https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_attach.html
    # https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_context_t.html
    # https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/_resmgr_nparts.html
    m_max = NPARTS_MAX_RE.search(src)
    if m_max and int(m_max.group(1)) >= 1:
        nparts_max = int(m_max.group(1))
        for fname, body in all_functions(src).items():
            for mm in NPARTS_RE.finditer(body):
                n = resolve_count(body, mm.group(1))
                if n is None or n <= nparts_max:
                    continue
                fl = def_line(src, fname)
                mn = re.compile(r"\b_RESMGR_NPARTS\s*\(\s*" + re.escape(mm.group(1)) + r"\s*\)").search(
                    src, sum(len(x) + 1 for x in src.split("\n")[:fl - 1]))
                f.append(Finding("ERROR", "QX009", path,
                                 f"{fname}() returns _RESMGR_NPARTS({n}) but the resource "
                                 f"manager declares attr.nparts_max = {nparts_max}: the IOV "
                                 f"array holds only {nparts_max} component(s)",
                                 line_of(src, mn.start()) if mn else fl))
    return f


TOOL_VERSION = "1.1.0"
RULES_URL = "https://github.com/tgg49099-dotcom/qnx-qx-probe/blob/main/RULES.md"
# SARIF level of each QX-PROBE level (SARIF 2.1.0, §3.27.10 "level").
SARIF_LEVEL = {"ERROR": "error", "WARN": "warning", "INFO": "note"}


def file_of(where: str) -> str:
    """The file part of a `where` (file, file:line or file:slot)."""
    head, sep, tail = where.rpartition(":")
    return head if sep and head and not tail.startswith(("/", "\\")) else where


def to_json(findings: list[Finding]) -> str:
    import json
    return json.dumps({"tool": "qx-probe", "version": TOOL_VERSION,
                       "findings": [{"level": f.level, "code": f.code,
                                     "file": file_of(f.where), "line": f.line,
                                     "where": f.where, "message": f.message}
                                    for f in findings]}, indent=2)


def to_sarif(findings: list[Finding]) -> str:
    """SARIF 2.1.0: the format GitHub code scanning, GitLab and most IDEs read.

    A finding then appears as an annotation on the exact line of a pull
    request, instead of a line in a CI log.
    """
    import json
    codes = sorted({f.code for f in findings})
    rules = [{"id": c, "helpUri": f"{RULES_URL}#{c.lower()}",
              "shortDescription": {"text": c}} for c in codes]
    results = [{"ruleId": f.code, "ruleIndex": codes.index(f.code),
                "level": SARIF_LEVEL[f.level],
                "message": {"text": f.message},
                "locations": [{"physicalLocation": {
                    "artifactLocation": {"uri": file_of(f.where).replace("\\", "/")},
                    "region": {"startLine": max(1, f.line)}}}]}
               for f in findings]
    return json.dumps({
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{"tool": {"driver": {"name": "QX-PROBE", "version": TOOL_VERSION,
                                       "informationUri": "https://github.com/tgg49099-dotcom/qnx-qx-probe",
                                       "rules": rules}},
                  "results": results}]}, indent=2)


def main(argv: list[str]) -> int:
    args = argv[1:]
    fmt = "text"
    paths = []
    k = 0
    while k < len(args):
        a = args[k]
        if a.startswith("--format="):
            fmt = a.split("=", 1)[1]
        elif a == "--format" and k + 1 < len(args):
            fmt = args[k + 1]
            k += 1
        else:
            paths.append(a)
        k += 1
    if not paths or fmt not in ("text", "json", "sarif"):
        print(__doc__)
        return 2
    sources = []
    for p in paths:
        with open(p, encoding="utf-8", errors="replace") as fh:
            sources.append((p, fh.read()))
    # The symbols defined in ALL the analysed files: a handler may
    # legitimately be defined in another translation unit.
    known: set[str] = set()
    for _p, raw in sources:
        known |= set(HANDLER_RE.findall(strip_comments(raw)))
    findings: list[Finding] = []
    for p, raw in sources:
        findings += analyse(p, raw, known)

    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    findings.sort(key=lambda x: (order[x.level], x.code, file_of(x.where), x.line))
    n_err = sum(1 for f in findings if f.level == "ERROR")
    n_warn = sum(1 for f in findings if f.level == "WARN")
    if fmt == "json":
        print(to_json(findings))
    elif fmt == "sarif":
        print(to_sarif(findings))
    else:
        for f in findings:
            print(f"{f.level:5} {f.code}  {f.loc()}: {f.message}")
        print(f"\nRESULT: {len(findings)} finding(s), {n_err} ERROR, {n_warn} WARN")
    # An actionable finding (ERROR or WARN) makes the exit code fail: this is
    # what makes the probe usable as a CI gate (in every output format).
    return 1 if (n_err or n_warn) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
