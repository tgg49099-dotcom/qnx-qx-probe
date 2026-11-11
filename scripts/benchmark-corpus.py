#!/usr/bin/env python3
"""Runs QX-PROBE on a corpus of REAL QNX resource managers.

The examples of the repository are examples.  This script is the other
thing: it runs the linter on resource managers that were written by other
people — seven of them published by QNX or BlackBerry themselves — and it
prints what it finds, file by file, with the commit it read.

Every file is pinned: the corpus is a list of (repository, commit, path).
The script fetches exactly that commit, so the result does not depend on
what the repository looks like today.

Nothing is written inside the repository: the fetched files live in a
temporary directory (or in the directory given by --cache), and the script
leaves no trace behind.

    python3 -I scripts/benchmark-corpus.py             # the table
    python3 -I scripts/benchmark-corpus.py --json      # the same, as JSON
    python3 -I scripts/benchmark-corpus.py --cache .cache

If the network or git is not available, the line is "NOT CHECKED" and the
script says so: a check that could not run is never counted as a success.

EXIT CODES
----------
    0  every file of the corpus was fetched and analysed
    2  at least one file of the corpus could not be fetched: the run is
       NOT CHECKED, never a partial success

Sources: the corpus is described in docs/BENCHMARK.md, with the date of
the measurement and the manual verification of every finding.
"""

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import qx_probe  # noqa: E402

# The corpus: real resource managers, publicly available, each pinned to the
# exact commit that was read.  "version" says what the project itself
# declares; where it declares nothing, the field says so — nothing here is
# guessed.
CORPUS = [
    {
        "publisher": "QNX",
        "project": "rpi-gpio",
        "url": "https://gitlab.com/qnx/projects/rpi-gpio.git",
        "sha": "880d66fe20a3111e32a86eb8339e79bc43abbf36",
        "path": "resmgr/main.c",
        "version": "QNX 8.0 (README: 'Building with QNX 8.0 SDP')",
    },
    {
        "publisher": "QNX",
        "project": "rpi-mailbox",
        "url": "https://gitlab.com/qnx/projects/rpi-mailbox.git",
        "sha": "dd9ed5928da2553f43350136244b38ba3857f95d",
        "path": "rpi_mbox.c",
        "version": "not stated in the repository (QNX's own sample group)",
    },
    {
        "publisher": "QNX",
        "project": "rpi-thermal",
        "url": "https://gitlab.com/qnx/projects/rpi-thermal.git",
        "sha": "4ba4fdc40c683acbbdf4409dc251aed1d52cfe89",
        "path": "rpi_thermal.c",
        "version": "not stated in the repository (QNX's own sample group)",
    },
    {
        "publisher": "BlackBerry / QNX",
        "project": "shim-demo",
        "url": "https://gitlab.com/qnx/projects/shim-demo.git",
        "sha": "5be2cd24780f51a83de24b0036bc875a73ffab2e",
        "path": "eventfd-mgr.c",
        "version": "not stated in the repository (QNX's own sample group)",
    },
    {
        "publisher": "BlackBerry / QNX",
        "project": "bsp_raspberrypi-bcm2712-rpi5",
        "url": "https://github.com/qnx/bsp_raspberrypi-bcm2712-rpi5.git",
        "sha": "573dda1a1ca387551e5413eeb84db5a4721e5ce3",
        "path": "src/hardware/support/bcm2712/fan/resmgr.c",
        "version": "QNX 8.0 (README: 'get a QNX SDP 8.0 license')",
    },
    {
        "publisher": "BlackBerry / QNX",
        "project": "qnx-posix-publish-subscribe",
        "url": "https://github.com/qnx/qnx-posix-publish-subscribe.git",
        "sha": "b5ca892f37464bea4ff88db3fdbbb2cc651da6a8",
        "path": "qpp/main.c",
        "version": "QNX 8.0 (README: 'source ~/qnx800/qnxsdp-env.sh')",
    },
    {
        "publisher": "QNX ports",
        "project": "epoll",
        "url": "https://github.com/qnx-ports/epoll.git",
        "sha": "aea458535243e44627b85b915ccbb658a396e4fb",
        "path": "epoll-mgr.c",
        "version": "not stated in the repository",
    },
    {
        "publisher": "llmike",
        "project": "devu-uvc",
        "url": "https://github.com/llmike/devu-uvc.git",
        "sha": "8534b138a8f55de4ecbb8811cfa71404681de369",
        "path": "uvc_rm.c",
        "version": "not stated in the repository",
    },
    {
        "publisher": "llmike",
        "project": "smbus",
        "url": "https://github.com/llmike/smbus.git",
        "sha": "fa3c7bbff27fd1157bbbb9b6cc69edc0696267d5",
        "path": "smb-ec/main.c",
        "version": "not stated in the repository",
    },
    {
        "publisher": "llmike",
        "project": "smbus",
        "url": "https://github.com/llmike/smbus.git",
        "sha": "fa3c7bbff27fd1157bbbb9b6cc69edc0696267d5",
        "path": "smb-ich/main.c",
        "version": "not stated in the repository",
    },
    {
        "publisher": "kodebooth",
        "project": "qnx-virtio",
        "url": "https://github.com/kodebooth/qnx-virtio.git",
        "sha": "037f84fe9b2075102caabfdc9d69ecd8f5c7b9a5",
        "path": "src/gpio/resmgr.c",
        "version": "not stated in the repository",
    },
    {
        "publisher": "ebenworks",
        "project": "phila-bedside-monitor-qnx",
        "url": "https://github.com/ebenworks-systems/phila-bedside-monitor-qnx.git",
        "sha": "e255b4be9408f4ed7db022996f38ed78007a2f69",
        "path": "src/qnx/resmgr.c",
        "version": "QNX 8.0 (README: 'bedside vital-signs monitor written for QNX 8.0')",
    },
    {
        "publisher": "DesignMaster Solutions",
        "project": "qnx8-resmgr-codelab",
        "url": "https://github.com/DesignMaster-Solutions/qnx8-resmgr-codelab.git",
        "sha": "d13f0fbda9b689feb86777bce689052d914d5eaf",
        "path": "src/hello.c",
        "version": "QNX 8.0 (README: 'your first QNX 8.0 resource manager')",
    },
    {
        "publisher": "DesignMaster Solutions",
        "project": "qnx8-resmgr-codelab",
        "url": "https://github.com/DesignMaster-Solutions/qnx8-resmgr-codelab.git",
        "sha": "d13f0fbda9b689feb86777bce689052d914d5eaf",
        "path": "src/ticks.c",
        "version": "QNX 8.0 (README: 'your first QNX 8.0 resource manager')",
    },
    {
        "publisher": "Embedded AI Design Labs",
        "project": "qnx_advance",
        "url": "https://github.com/Embedded-AI-Design-Labs-Pvt-Ltd/qnx_advance.git",
        "sha": "d1a82cef2b829427abb0efc04d075481b43ba3cf",
        "path": "module04_drivers/block_rm.c",
        "version": "QNX 7.1 or 8.0 (README: 'source ~/qnx710/qnxsdp-env.sh # or qnx800')",
    },
    {
        "publisher": "Embedded AI Design Labs",
        "project": "qnx_advance",
        "url": "https://github.com/Embedded-AI-Design-Labs-Pvt-Ltd/qnx_advance.git",
        "sha": "d1a82cef2b829427abb0efc04d075481b43ba3cf",
        "path": "module04_drivers/can_rm.c",
        "version": "QNX 7.1 or 8.0 (README: 'source ~/qnx710/qnxsdp-env.sh # or qnx800')",
    },
    {
        "publisher": "Embedded AI Design Labs",
        "project": "qnx_advance",
        "url": "https://github.com/Embedded-AI-Design-Labs-Pvt-Ltd/qnx_advance.git",
        "sha": "d1a82cef2b829427abb0efc04d075481b43ba3cf",
        "path": "module04_drivers/qtn_sensor_rm.c",
        "version": "QNX 7.1 or 8.0 (README: 'source ~/qnx710/qnxsdp-env.sh # or qnx800')",
    },
]


def fetch(entry, cache: pathlib.Path) -> tuple[str | None, str | None]:
    """Returns (source, error). Fetches the pinned commit, nothing else."""
    dest = cache / entry["project"]
    try:
        if not (dest / ".git").is_dir():
            dest.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "init", "-q", str(dest)], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "-C", str(dest), "remote", "add", "origin", entry["url"]],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", str(dest), "fetch", "-q", "--depth", "1",
                        "origin", entry["sha"]], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        blob = subprocess.run(["git", "-C", str(dest), "show", f"{entry['sha']}:{entry['path']}"],
                              check=True, capture_output=True, text=True).stdout
        return blob, None
    except subprocess.CalledProcessError as exc:
        return None, f"git failed ({exc.returncode})"
    except FileNotFoundError:
        return None, "git is not installed"


def analyse_entry(entry, cache):
    src, err = fetch(entry, cache)
    if src is None:
        return {"status": "NOT CHECKED", "reason": err, "findings": 0,
                "error": 0, "warn": 0, "lines": []}
    found = qx_probe.analyse(f"{entry['project']}/{entry['path']}", src)
    n_err = sum(1 for f in found if f.level == "ERROR")
    n_warn = sum(1 for f in found if f.level == "WARN")
    lines = [f"{f.level} {f.code} {f.where}: {f.message}" for f in found
             if f.level in ("ERROR", "WARN")]
    return {"status": "OK", "reason": "", "findings": len(found),
            "error": n_err, "warn": n_warn, "lines": lines,
            "exit_code": 1 if (n_err or n_warn) else 0}


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cache", default=None,
                    help="directory where the repositories are fetched "
                         "(a temporary one by default)")
    ap.add_argument("--json", action="store_true", help="machine readable output")
    ap.add_argument("--only", default=None, help="run only the entries whose "
                                                 "project contains this string")
    args = ap.parse_args(argv[1:])

    tmp = None
    if args.cache:
        cache = pathlib.Path(args.cache).resolve()
        cache.mkdir(parents=True, exist_ok=True)
    else:
        tmp = tempfile.mkdtemp(prefix="qx-bench-")
        cache = pathlib.Path(tmp)

    rows = []
    try:
        for entry in CORPUS:
            if args.only and args.only not in entry["project"]:
                continue
            res = analyse_entry(entry, cache)
            row = dict(entry)
            row.pop("url")
            row["url"] = entry["url"]
            row.update(res)
            rows.append(row)
    finally:
        if tmp and os.path.isdir(tmp):
            shutil.rmtree(tmp, ignore_errors=True)

    if args.json:
        print(json.dumps(rows, indent=2))
        return 0 if all(r["status"] == "OK" for r in rows) else 2

    width = max(len(r["project"]) for r in rows) if rows else 10
    print(f"QX-PROBE on {len(rows)} real QNX resource managers\n")
    for r in rows:
        label = f"{r['project']}/{r['path']}"
        if r["status"] != "OK":
            print(f"{label:<{width + 40}}  NOT CHECKED ({r['reason']})")
            continue
        print(f"{label:<{width + 40}}  {r['findings']:>3} finding(s), "
              f"{r['error']} ERROR, {r['warn']} WARN (exit {r['exit_code']})")
        for line in r["lines"]:
            print(f"    {line}")
    checked = sum(1 for r in rows if r["status"] == "OK")
    errors = sum(r["error"] for r in rows)
    print(f"\n{checked}/{len(rows)} files analysed, {errors} ERROR in total")
    if checked != len(rows):
        # A file that could not be fetched is NOT CHECKED, never a success:
        # the exit code says so, and the caller can tell the two apart.
        print(f"VERDICT: NOT CHECKED - {len(rows) - checked} file(s) of the "
              f"corpus could not be fetched")
        return 2
    print(f"VERDICT: {checked}/{len(rows)} FILES ANALYSED, {errors} ERROR IN TOTAL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
