#!/usr/bin/env python3
"""QX-PROBE — analyseur statique du protocole resource-manager QNX 8.0.

Outil hôte : lit du code C et rapporte des faits structurels sur le protocole
resource-manager (resmgr) de QNX 8.0. Aucune dépendance, aucun SDK QNX.

CHAQUE REGLE EST ADOSSÉE À UNE PAGE OFFICIELLE de la documentation BlackBerry
QNX SDP 8.0 (C Library Reference, pages mises à jour le 11 juin 2026). Les
URL officielles sont citées dans le commentaire de chaque règle et reprises
dans RULES.md.  Regle d'or : ZÉRO faux positif — une règle qui signale à tort
du code QNX 8.0 canonique est pire qu'une règle absente.

Usage:  python3 -I qx_probe.py <file.c> [file.c ...]
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

# Table resmgr_io_funcs_t de QNX 8.0 : ordre de declaration officiel.
# Source : https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_io_funcs_t.html
IO_FUNC_SLOTS = (
    "read", "write", "close_ocb", "stat", "notify", "devctl", "unblock",
    "pathconf", "lseek", "chmod", "chown", "utime", "openfd", "fdinfo",
    "lock", "space", "shutdown", "mmap", "msg", "reserved", "dup",
    "close_dup", "lock_ocb", "unlock_ocb", "sync", "power", "acl",
    "pause", "unpause", "read64", "write64", "notify64", "utime64",
    "check_msg",
)

# Slot 64 bits et son equivalent 32 bits (resmgr_io_funcs_t, QNX 8.0).
IO_FUNC_ALIASES = {"read64": "read", "write64": "write",
                   "notify64": "notify", "utime64": "utime"}

# Valeurs par defaut POSIX documentees pour les slots de io_funcs (colonne
# "Default" de resmgr_io_funcs_t).  None = aucun defaut (le slot n'est pas
# traite si le developpeur ne le cable pas).
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
ASSIGN_RE = re.compile(r"\b(io_funcs|dev_funcs|connect_funcs)\s*\.\s*(\w+)\s*=\s*([A-Za-z_]\w*)")
HANDLER_RE = re.compile(
    r"^\s*(?:static\s+)?int\s+([A-Za-z_]\w*)\s*\(", re.MULTILINE)
FUNC_DEF_RE = re.compile(
    r"^[ \t]*(?:static\s+|extern\s+|inline\s+)*int\s+([A-Za-z_]\w*)\s*\(", re.MULTILINE)

# QX009 : nombre de parties renvoyees au client / taille de l'IOV.
# Sources : resmgr_attach() (attr.nparts_max = "The number of components to
# allocate for the IOV array"), resmgr_context_t() (iov), _RESMGR_NPARTS()
# (Caveats : "The resmgr_attach() function should set attr->nparts_max to be
# the maximum value for num").
NPARTS_MAX_RE = re.compile(r"\bnparts_max\s*=\s*(\d+)\s*;")
NPARTS_RE = re.compile(r"\b_RESMGR_NPARTS\s*\(\s*([A-Za-z_]\w*|\d+)\s*\)")
ASSIGN_INT_RE = re.compile(r"\b([A-Za-z_]\w*)\s*=\s*(\d+)\s*;")


@dataclass
class Finding:
    level: str        # ERROR | WARN | INFO
    code: str
    where: str
    message: str


def strip_comments(src: str) -> str:
    """Remove /* */ and // comments, keeping string literals intact."""
    out = []
    i, n = 0, len(src)
    while i < n:
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            i = n if j < 0 else j + 2
            out.append(" ")
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
        else:
            out.append(src[i])
            i += 1
    return "".join(out)


def blank_strings(src: str) -> str:
    """Remplace le CONTENU des litteraux de chaine par des espaces.

    La longueur de la chaine est preservee : les indices restent valides, et
    le texte des chaines ne peut plus perturber l'analyse (parentheses,
    accolades, mots-cles).
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
        else:
            i += 1
    return "".join(out)


def split_args(src: str, open_paren: int) -> list[tuple[int, int]]:
    """Decoupe les arguments d'un appel C. Renvoie [(debut, fin), ...].

    open_paren est l'index de la '(' d'ouverture.  Le decoupage ignore les
    virgules imbriquees et les virgules situees dans une chaine.
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
    """Renvoie le contenu d'un litteral de chaine, ou None si ce n'en est pas un."""
    m = re.fullmatch(r'"((?:[^"\\]|\\.)*)"', text.strip())
    return m.group(1) if m else None


def function_body(src: str, name: str, open_paren: int) -> str | None:
    """Renvoie le corps (accolades excluses) de la fonction `name`, ou None."""
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
    """Renvoie {nom: corps} pour toutes les fonctions `int` definies dans le fichier."""
    out: dict[str, str] = {}
    for m in FUNC_DEF_RE.finditer(src):
        name = m.group(1)
        if name in out:
            continue
        body = function_body(src, name, m.end() - 1)
        if body is not None:
            out[name] = body
    return out


def resolve_count(body: str, ident: str) -> int | None:
    """Resout un entier utilise comme nombre de parties.

    Renvoie l'entier si — et seulement si — il est connu sans ambiguite :
    litteral direct, ou une seule affectation `ident = <entier>;` dans le corps.
    Dans le cas contraire, None (on ne dit rien plutot que de se tromper).
    """
    if ident.isdigit():
        return int(ident)
    found = [int(v) for _n, v in ASSIGN_INT_RE.findall(body) if _n == ident]
    if len(found) == 1:
        return found[0]
    return None


def line_of(src: str, pos: int) -> int:
    return src.count("\n", 0, pos) + 1


def analyse(path: str, raw: str) -> list[Finding]:
    f: list[Finding] = []
    src = strip_comments(raw)

    headers = [h for h in QNX_HEADERS if h in src]
    is_resmgr = "resmgr" in src or "dispatch" in src
    if not is_resmgr:
        return f

    # C1 — a file that uses the resmgr API must wire a dispatch table.
    assigns = ASSIGN_RE.findall(src)
    if not assigns:
        f.append(Finding("ERROR", "QX001", path,
                         "file uses the QNX resmgr API but no dispatch table is assigned "
                         "(io_funcs.*/dev_funcs.*/connect_funcs.*)"))
        return f

    # C2 — iofunc_func_init() arity must match the number of slots actually used.
    m = NFUNCS_RE.search(src)
    if m:
        conn_n, _conn_f, io_n, _io_f = (x.strip() for x in m.groups())
        used_io = {a[1] for a in assigns if a[0] == "io_funcs"}
        used_conn = {a[1] for a in assigns if a[0] == "connect_funcs"}
        for label, n_expr, used in (("io", io_n, used_io), ("connect", conn_n, used_conn)):
            if not n_expr.isdigit():
                f.append(Finding("INFO", "QX010", path,
                                 f"{label} function count '{n_expr}' is not a literal (macro)"))
                continue
            n = int(n_expr)
            if used and len(used) > n:
                f.append(Finding("ERROR", "QX002", path,
                                 f"{len(used)} {label}_funcs slots assigned but "
                                 f"iofunc_func_init() declares only {n} -> overflow"))
    else:
        f.append(Finding("WARN", "QX011", path,
                         "no iofunc_func_init() call found although dispatch tables are assigned"))

    # C3 — every assigned handler must be a function defined in the file.
    defined = set(HANDLER_RE.findall(src))
    for table, slot, handler in assigns:
        if handler not in defined and not handler.startswith("NULL"):
            f.append(Finding("ERROR", "QX003", f"{path}:{slot}",
                             f"{table}.{slot} = {handler} but no such function is defined here"))

    # C4 — io_read / io_write must call the iofunc_*_verify() gate.
    for table, slot, handler in assigns:
        if not (table in ("io_funcs", "dev_funcs") and slot in ("read", "write")):
            continue
        mh = re.search(r"\bint\s+" + re.escape(handler) + r"\s*\([^)]*\)\s*\{", src)
        if not mh:
            continue
        start = mh.end()
        depth, i = 1, start
        while i < len(src) and depth:
            if src[i] == "{":
                depth += 1
            elif src[i] == "}":
                depth -= 1
            i += 1
        body = src[start:i]
        want = "iofunc_read_verify" if slot == "read" else "iofunc_write_verify"
        if want not in body:
            f.append(Finding("ERROR", "QX004", f"{path}:{slot}",
                             f"{handler}() never calls {want}(): the access gate is missing"))

    # C5 — le chemin monte par resmgr_attach() doit etre ABSOLU.
    # Source : resmgr_attach() — "You usually provide an absolute path; if you
    # provide a path that doesn't start with a slash, it's considered to be
    # relative to the current working directory."
    # Le pathname space de QNX est GENERAL : un point de montage hors /dev/
    # (/var/run, /tmp, /etc, ...) est parfaitement valide — aucune alerte.
    # Seule alerte : un chemin relatif, dont la resolution depend du
    # repertoire courant (donc du contexte de demarrage du resmgr).
    # https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_attach.html
    for m2 in re.finditer(r"\bresmgr_attach\s*\(", src):
        args = split_args(src, m2.end() - 1)
        if len(args) < 3:
            continue
        lit = string_literal(src[args[2][0]:args[2][1]])
        if lit is None:
            continue          # chemin non litteral (variable, macro) : on ne peut rien dire
        if not lit.startswith("/"):
            f.append(Finding("WARN", "QX005", f"{path}:{line_of(src, m2.start())}",
                             f"resmgr_attach() attaches the relative path '{lit}': "
                             f"QNX resolves it against the current working directory "
                             f"(an absolute path is recommended)"))

    # C6 — la boucle de messages : bloquer puis distribuer.
    # Sources : resmgr_block() — "This function is a special case of
    # dispatch_block() that you should use only with a simple resource
    # manager." ; resmgr_handler() — "This function is a special case of
    # dispatch_handler()."
    # Les deux API sont canoniques : exiger l'une ou l'autre produirait un
    # faux positif sur le code de reference de QNX 8.0.
    # https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_block.html
    # https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_handler.html
    has_block = bool(re.search(r"\b(?:dispatch_block|resmgr_block)\s*\(", src))
    has_handler = bool(re.search(r"\b(?:dispatch_handler|resmgr_handler)\s*\(", src))
    if not has_block:
        f.append(Finding("ERROR", "QX006", path,
                         "no message loop: neither dispatch_block() nor resmgr_block() "
                         "is called, so the resource manager never waits for a message"))
    elif not has_handler:
        f.append(Finding("ERROR", "QX007", path,
                         "the message loop blocks (dispatch_block()/resmgr_block()) but no "
                         "handler is called (neither dispatch_handler() nor resmgr_handler())"))

    # C7 — report the io_funcs slots left unassigned (informational).
    # Source : resmgr_io_funcs_t — "You can initialize this table by calling
    # iofunc_func_init() and then overriding the defaults with your own
    # functions."  Chaque slot non cable conserve le defaut POSIX documente
    # (iofunc_read_default(), iofunc_write_default(), ...) ou reste NULL
    # quand aucun defaut n'existe.  Un resmgr en lecture seule (sans write)
    # est donc VALIDE : l'absence d'un slot n'est plus jamais une ERROR.
    # https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_io_funcs_t.html
    assigned_io = {slot for table, slot, _h in assigns if table == "io_funcs"}
    covered = {IO_FUNC_ALIASES.get(s, s) for s in assigned_io}
    for slot in ("read", "write", "devctl", "unblock", "notify"):
        if slot in covered:
            continue
        default = IO_FUNC_DEFAULTS.get(slot)
        if default:
            detail = f"the POSIX default {default} applies unless you override it"
        else:
            detail = "QNX 8.0 defines no default for this slot: the message is not handled"
        f.append(Finding("INFO", "QX008", path,
                         f"io_funcs.{slot} is not assigned ({detail})"))

    # C8 — le nombre de parties renvoyees ne peut pas depasser l'IOV declare.
    # Sources : resmgr_attach() — attr.nparts_max = "The number of components
    # to allocate for the IOV array." ; resmgr_context_t() — "iov (output) An
    # I/O vector where you can place the data that you're returning to the
    # client. This defaults to one entry, but can be configured by the
    # attr.nparts_max parameter" ; _RESMGR_NPARTS() — "The resmgr_attach()
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
                f.append(Finding("ERROR", "QX009", path,
                                 f"{fname}() returns _RESMGR_NPARTS({n}) but the resource "
                                 f"manager declares attr.nparts_max = {nparts_max}: the IOV "
                                 f"array holds only {nparts_max} component(s)"))
    return f


def main(argv: list[str]) -> int:
    paths = argv[1:]
    if not paths:
        print(__doc__)
        return 2
    findings: list[Finding] = []
    for p in paths:
        with open(p, encoding="utf-8", errors="replace") as fh:
            findings += analyse(p, fh.read())

    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    findings.sort(key=lambda x: (order[x.level], x.code, x.where))
    for f in findings:
        print(f"{f.level:5} {f.code}  {f.where}: {f.message}")
    n_err = sum(1 for f in findings if f.level == "ERROR")
    n_warn = sum(1 for f in findings if f.level == "WARN")
    print(f"\nRESULTAT: {len(findings)} constat(s), {n_err} ERROR, {n_warn} WARN")
    # Un constat actionnable (ERROR ou WARN) fait echouer le code de sortie :
    # c'est ce qui rend le probe utilisable comme porte de CI.
    return 1 if (n_err or n_warn) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
