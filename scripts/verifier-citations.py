#!/usr/bin/env python3
"""Re-reads the 14 official QNX 8.0 pages cited by the rules and checks that
the sentence each rule depends on is still on the page.

WHAT THIS SCRIPT IS FOR
-----------------------
Every rule of QX-PROBE is backed by a page of the official BlackBerry QNX SDP
8.0 documentation.  A citation is only worth something if the sentence it
quotes is still there, on the official page, at the moment the reader looks.
This script checks exactly that, and it is meant to be run by a judge:

    python3 -I scripts/verifier-citations.py

RULES OF THE SCRIPT (they are the point)
----------------------------------------
* **No false green.**  A page that could not be fetched is `NOT CHECKED`,
  never `OK`.  A page whose sentence could not be found is `QUOTE NOT FOUND`,
  never `OK`.  The verdict of the run is decided by the pages that were
  actually read.
* **Twelve requests, one per page, one run.**  Exactly one HTTP GET per cited
  page, no retry: a page that fails is reported as NOT CHECKED.
* **One domain only.**  Every URL must start with
  `https://www.qnx.com/developers/docs/8.0/`; the script refuses to read
  anything else.
* **An identifiable User-Agent.**  `QX-PROBE-citation-check/1.0`, so the
  administrator of the QNX site can tell what the traffic is.
* **The quotations are not invented here.**  They are the sentences of
  `RULES.md`; the script also checks that each of them is still written in
  `RULES.md`, and says so for every one of them.

HOW A QUOTATION IS COMPARED
---------------------------
The HTML of the documentation is stripped of its tags, its entities are
decoded, its backquotes are removed and its whitespace is squashed; the same
normalisation is applied to the quotation.  Two consequences, both wanted:

  * the HTML rendering of the code (a space between `(*read)` and `(`, for
    instance) does not make the quotation look absent;
  * a quotation that ends a sentence in `RULES.md` may be a truncation of the
    official sentence: the final full stop is therefore not compared.

The comparison against `RULES.md` ignores the case (a quotation embedded in a
sentence may start with a lower-case letter) and the whitespace; the letters,
the digits and the punctuation must match.

EXIT CODES
----------
    0  every cited page was read and every quotation was found
    1  partially verified: at least one page was read, but one page was NOT
       CHECKED or one quotation was NOT FOUND
    2  nothing could be verified at all: no page could be read (no network)

    3  misuse of the command line

`--self-test` runs the checker on local pages, **without any network access**,
and proves that it reports a missing quotation and a page it could not read.
It is the contre-épreuve of this script: a checker that cannot fail is worse
than no checker.

Run:  python3 -I scripts/verifier-citations.py [--self-test]
"""
from __future__ import annotations

import html
import pathlib
import re
import sys
import urllib.error
import urllib.request

UA = ("QX-PROBE-citation-check/1.0 "
      "(+https://github.com/tgg49099-dotcom/qnx-qx-probe)")
BASE = "https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/"
TIMEOUT = 25

# --------------------------------------------------------------------------
# The 14 pages cited by RULES.md, and the sentences the rules depend on.
# Every quotation below is a sentence of the official page (measured on
# 07/11/2026) and is written verbatim in RULES.md: the checker prints a
# "not written verbatim in RULES.md" note for every quotation that is not.
# --------------------------------------------------------------------------
CITATIONS: list[tuple[str, str, tuple[str, ...]]] = [
    ("resmgr_attach", "r/resmgr_attach", (
        "A pointer to the resmgr_connect_funcs_t structure that defines the "
        "POSIX-level connect functions.",
        "A pointer to the resmgr_io_funcs_t structure that defines the "
        "POSIX-level I/O functions.",
        "You usually provide an absolute path; if you provide a path that "
        "doesn't start with a slash, it's considered to be relative to the "
        "current working directory.",
        "The number of components to allocate for the IOV array.",
        "or NULL to use the default attributes",
        "If path is NULL, only the first step will be done, unless "
        "RESMGR_FLAG_ATTACH_LOCAL is set in attr.flags or "
        "_RESMGR_FLAG_FTYPEONLY is set in flags",
    )),
    ("resmgr_io_funcs_t", "r/resmgr_io_funcs_t", (
        "You can initialize this table by calling iofunc_func_init() and then "
        "overriding the defaults with your own functions.",
        "int (*read) (resmgr_context_t *ctp, io_read_t *msg, RESMGR_OCB_T *ocb);",
        "iofunc_read_default()",
        "iofunc_write_default()",
        "iofunc_devctl_default()",
        "iofunc_unblock_default()",
    )),
    ("iofunc_func_init", "i/iofunc_func_init", (
        "The nconnect and nio arguments indicate how many entries this "
        "function should fill. This is in place to support forward "
        "compatibility.",
        "The number of entries in the io table that you want to fill.",
        "The number of entries in the connect table that you want to fill.",
        "Typically, you pass _RESMGR_IO_NFUNCS for this argument.",
        "The iofunc_func_init() function initializes the passed connect and "
        "io structures with the POSIX-layer default functions.",
        "my_io_functions.io_read = my_io_read;",
    )),
    ("resmgr_connect_funcs_t", "r/resmgr_connect_funcs_t", (
        "The resmgr_connect_funcs_t structure is a table of the POSIX-level "
        "connect functions that are used by a resource manager.",
        "You can initialize this table by calling iofunc_func_init() and then "
        "overriding the defaults with your own functions.",
    )),
    ("iofunc_read_verify", "i/iofunc_read_verify", (
        "All read handlers should start with a call to iofunc_read_verify() "
        "and proceed only if it returns EOK.",
        # The four sentences below are the behaviour of the gate itself. They
        # are quoted in docs/BENCHMARK.md (section 5) and written verbatim in
        # RULES.md (rule QX004), so the checker finds them in both.
        "the original open included read access",
        "if an xtype is specified that includes extra data headers, the "
        "extra data is in the receive buffer",
        "the read offset to be used is non-negative",
        "The client didn't open the resource for read access.",
    )),
    ("iofunc_write_verify", "i/iofunc_write_verify", (
        "All write handlers should start with a call to iofunc_write_verify() "
        "and proceed only if it returns EOK.",
    )),
    # Added on 14/11/2026: the POSIX default handlers run the gate
    # themselves, so a handler that delegates to them is gated (rule QX004).
    ("iofunc_read_default", "i/iofunc_read_default", (
        "The iofunc_read_default() function calls iofunc_read_verify() to "
        "verify if this read operation should be permitted.",
    )),
    ("iofunc_write_default", "i/iofunc_write_default", (
        "The iofunc_write_default() function calls iofunc_write_verify() to "
        "verify if this write operation should be permitted.",
    )),
    ("resmgr_block", "r/resmgr_block", (
        "The resmgr_block() function waits for a message (created by a call "
        "to resmgr_context_alloc() ) for context ctp .",
        "This function is a special case of dispatch_block() that you should "
        "use only with a simple resource manager.",
    )),
    ("dispatch_block", "d/dispatch_block", (
        "The dispatch_block() function blocks by calling MsgReceive() while "
        "waiting for an event that's registered using one of the attach "
        "functions, message_attach() , pulse_attach() , resmgr_attach() , or "
        "select_attach() .",
    )),
    ("resmgr_handler", "r/resmgr_handler", (
        "The resmgr_handler() function handles the message received in ctp .",
        "The resmgr_handler() function is a special case of dispatch_handler() .",
    )),
    ("dispatch_handler", "d/dispatch_handler", (
        "The dispatch_handler() function handles events received by "
        "dispatch_block() and does one of the following:",
    )),
    ("resmgr_context_t", "r/resmgr_context_t", (
        "An I/O vector where you can place the data that you're returning to "
        "the client. This defaults to one entry, but can be configured by the "
        "attr.nparts_max parameter",
    )),
    ("_resmgr_nparts", "r/_resmgr_nparts", (
        "The resmgr_attach() function should set attr->nparts_max to be the "
        "maximum value for num .",
    )),
]

# The rules that cite each page (for the readable output).
USERS: dict[str, str] = {
    "resmgr_attach": "QX001, QX005, QX009",
    "resmgr_io_funcs_t": "QX001, QX002, QX003, QX008, QX011",
    "iofunc_func_init": "QX001, QX002, QX010, QX011",
    "resmgr_connect_funcs_t": "QX002",
    "iofunc_read_verify": "QX004",
    "iofunc_write_verify": "QX004",
    "iofunc_read_default": "QX004",
    "iofunc_write_default": "QX004",
    "resmgr_block": "QX006",
    "dispatch_block": "QX006",
    "resmgr_handler": "QX007",
    "dispatch_handler": "QX007",
    "resmgr_context_t": "QX009",
    "_resmgr_nparts": "QX009",
}


# --------------------------------------------------------------------- utils
def squash(text: str) -> str:
    """Strips the HTML, decodes the entities, removes the backquotes and the
    whitespace: what is left is the text itself."""
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html.unescape(text)
    text = text.replace("`", "")
    return re.sub(r"\s+", "", text)


def squash_loose(text: str) -> str:
    """Same, without the case: used to look for a quotation in RULES.md."""
    return squash(text).lower()


def quote_key(quote: str) -> str:
    """The comparison key of a quotation: no whitespace, no trailing full
    stop (a quotation written inside a sentence may be a truncation)."""
    return squash(quote).rstrip(".")


def page_updated(raw: str) -> str:
    """The date the page carries at the bottom: 'Page updated: <date>'."""
    m = re.search(r"Page updated:\s*(?:<[^>]+>)?\s*([^<]{4,40})", raw)
    return m.group(1).strip() if m else "unknown"


def fetch(url: str) -> tuple[str | None, str]:
    """One GET.  Returns (raw_html, status).  `raw_html` is None when the
    page could not be read: the caller must then report NOT CHECKED."""
    if not url.startswith(BASE):
        raise ValueError(f"refusing to read a URL outside {BASE}: {url}")
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            body = response.read()
            status = str(response.getcode())
    except urllib.error.HTTPError as exc:
        return None, f"HTTP {exc.code}"
    except Exception as exc:                      # noqa: BLE001
        return None, f"{type(exc).__name__}: {exc}"
    charset = "utf-8"
    try:
        raw = body.decode(charset, errors="replace")
    except LookupError:                            # pragma: no cover
        raw = body.decode("utf-8", errors="replace")
    return raw, status


def rules_text(repo: str) -> str:
    """The text of RULES.md, with the Markdown markers removed.

    The block quotes are introduced by a '>' at the beginning of the line and
    the emphasis by '**': both would break the comparison of a sentence that
    is written across several lines.  Nothing else is touched: the letters,
    the digits and the punctuation of the sentences are left as they are.
    """
    path = pathlib.Path(repo) / "RULES.md"
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    lines = []
    for line in raw.splitlines():
        stripped = line.lstrip()
        while stripped.startswith(">"):
            stripped = stripped[1:].lstrip()
        lines.append(stripped)
    return squash("\n".join(lines).replace("**", ""))


# ------------------------------------------------------------------ the check
def check_page(name: str, path: str, quotes: tuple[str, ...],
               repo: str, fetcher=None) -> dict:
    """Reads one page and checks its quotations.  One HTTP request."""
    url = BASE + path + ".html"
    raw, status = (fetcher or fetch)(url)
    result = {"name": name, "url": url, "status": status,
              "updated": "-", "found": 0, "missing": [], "read": raw is not None}
    if raw is None:
        return result
    result["updated"] = page_updated(raw)
    page = squash(raw)
    rules = squash_loose(rules_text(repo))
    for quote in quotes:
        key = quote_key(quote)
        on_page = key in page
        in_rules = bool(rules) and key.lower() in rules
        result["found"] += 1 if on_page else 0
        if not on_page:
            result["missing"].append(quote)
        if not in_rules:
            result.setdefault("not_in_rules", []).append(quote)
    return result


def run(repo: str) -> int:
    print("=" * 78)
    print("QX-PROBE - verification of the 14 official QNX 8.0 citations")
    print("=" * 78)
    print(f"User-Agent : {UA}")
    print(f"one request per page, no retry; {len(CITATIONS)} pages, "
          f"{len(CITATIONS)} requests maximum")
    print()

    results = []
    for name, path, quotes in CITATIONS:
        result = check_page(name, path, quotes, repo)
        results.append(result)
        users = USERS.get(name, "-")
        if not result["read"]:
            print(f"[NOT CHECKED] {name} ({users})")
            print(f"              {result['url']}")
            print(f"              {result['status']} - the page could not be read; "
                  f"it is NOT verified")
            continue
        missing = len(result["missing"])
        verdict = "OK" if missing == 0 else "QUOTE NOT FOUND"
        print(f"[{verdict:13s}] {name} ({users})")
        print(f"              {result['url']}")
        print(f"              HTTP {result['status']} - page updated: "
              f"{result['updated']} - {result['found']}/{len(quotes)} "
              f"quotation(s) found")
        for quote in result["missing"]:
            print(f"              NOT FOUND: {quote}")
        for quote in result.get("not_in_rules", []):
            print(f"              note: this sentence is not written verbatim in "
                  f"RULES.md (the page is cited there; the sentence was measured "
                  f"on the page itself)")
        print()

    read = [r for r in results if r["read"]]
    not_checked = [r for r in results if not r["read"]]
    broken = [r for r in read if r["missing"]]
    total_quotes = sum(len(q) for _, _, q in CITATIONS)
    found_quotes = sum(r["found"] for r in read)

    print("=" * 78)
    print(f"pages read        : {len(read)}/{len(results)}")
    print(f"pages NOT CHECKED : {len(not_checked)}"
          + (f"  ({', '.join(r['name'] for r in not_checked)})" if not_checked else ""))
    print(f"quotations found  : {found_quotes}/{total_quotes}")
    print(f"pages with a missing quotation : {len(broken)}"
          + (f"  ({', '.join(r['name'] for r in broken)})" if broken else ""))
    print("=" * 78)

    if not read:
        print("VERDICT: NOTHING COULD BE VERIFIED - no page could be read "
              "(no network).")
        print("         This is NOT a success: nothing was checked. (RC 2)")
        return 2
    if not_checked or broken:
        print("VERDICT: PARTIALLY VERIFIED - the quotations listed above were "
              "not all confirmed.")
        print("         (RC 1)")
        return 1
    print("VERDICT: ALL CITATIONS VERIFIED - every cited page was read and "
          "every quotation was found.")
    print("         (RC 0)")
    return 0


# ----------------------------------------------------------- the contre-epreuve
def self_test() -> int:
    """Proves, without any network access, that the checker can fail.

    A checker that always says OK is worse than no checker: this test feeds
    it a page that does not carry the quotation, and a page that cannot be
    read at all, and checks that neither is reported as verified.
    """
    print("=" * 78)
    print("QX-PROBE - self-test of the citation checker (no network access)")
    print("=" * 78)
    failures = 0

    # 1. a page that carries the quotation -> the quotation is found.
    good = ('<html><body><p>All read handlers should start with a call to '
            '<code>iofunc_read_verify()</code> and proceed only if it '
            'returns EOK.</p>'
            '<div>Page updated: <time>June 11, 2026</time></div>'
            '</body></html>')
    key = quote_key("All read handlers should start with a call to "
                    "iofunc_read_verify() and proceed only if it returns EOK.")
    if key in squash(good):
        print("  [OK ] the quotation is found in the page that carries it")
    else:
        print("  [KO ] the quotation was NOT found in the page that carries it")
        failures += 1

    # 2. a page that does NOT carry it -> it must be reported missing.
    bad = '<html><body><p>This page says something else entirely.</p></body></html>'
    if key not in squash(bad):
        print("  [OK ] the quotation is reported missing on a page that does "
              "not carry it")
    else:
        print("  [KO ] the quotation was found on a page that does not carry it")
        failures += 1

    # 3. the comparison ignores the whitespace of the HTML rendering.
    spaced = ('<html><body><code>int (*read) (resmgr_context_t *ctp, '
              'io_read_t *msg, RESMGR_OCB_T *ocb);</code></body></html>')
    member = ("int (*read)(resmgr_context_t *ctp, io_read_t *msg, "
              "RESMGR_OCB_T *ocb);")
    if quote_key(member) in squash(spaced):
        print("  [OK ] the comparison ignores the whitespace of the HTML")
    else:
        print("  [KO ] the comparison does not ignore the whitespace of the HTML")
        failures += 1

    # 4. a page that could not be read is NOT CHECKED, never OK.
    def unreachable(url):
        return None, "URLError: <simulated: no network>"

    result = check_page("iofunc_read_verify", "i/iofunc_read_verify",
                        ("All read handlers should start with a call to "
                         "iofunc_read_verify() and proceed only if it returns "
                         "EOK.",), ".", fetcher=unreachable)
    if not result["read"] and result["found"] == 0:
        print(f"  [OK ] a page that could not be read is NOT CHECKED "
              f"({result['status']}), never OK")
    else:
        print("  [KO ] a page that could not be read was reported as read")
        failures += 1

    # 5. the same page, read: the quotation is found and the page is OK.
    def fake_good(url):
        return good, "200"

    result = check_page("iofunc_read_verify", "i/iofunc_read_verify",
                        ("All read handlers should start with a call to "
                         "iofunc_read_verify() and proceed only if it returns "
                         "EOK.",), ".", fetcher=fake_good)
    if result["read"] and result["found"] == 1 and not result["missing"]:
        print("  [OK ] a page that carries the quotation is reported OK "
              f"(page updated: {result['updated']})")
    else:
        print("  [KO ] a page that carries the quotation was not reported OK")
        failures += 1

    print("=" * 78)
    if failures:
        print(f"SELF-TEST: FAILED ({failures} check(s) failed) (RC 1)")
        return 1
    print("SELF-TEST: GREEN - the checker finds a missing quotation and "
          "reports an unreadable page as NOT CHECKED (RC 0)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    if len(argv) > 1:
        print(f"usage: {argv[0]} [--self-test]", file=sys.stderr)
        return 3
    repo = pathlib.Path(__file__).resolve().parent.parent
    return run(str(repo))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
