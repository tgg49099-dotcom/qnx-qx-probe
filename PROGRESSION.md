# PROGRESSION — QX-PROBE

The map of this repository, and the dated log of its progress.
The French version is [`PROGRESSION-FR.md`](PROGRESSION-FR.md); it follows
the same sections, cycle by cycle.

One line per part: what it is, its state, and the command that proves it.
State = `done` (published and proved) / `partial` (done but incomplete) /
`planned` (not done) / `waiting` (cannot be done until an external piece
arrives).

---

## 1. The tool

| Part | What it does | State | The command that proves it |
|---|---|---|---|
| `qx_probe.py` | The linter: reads a C source and reports the mistakes of the QNX 8.0 resource-manager protocol | done | `python3 -I qx_probe.py examples/blackberry_eventfd_mgr.c` |
| The eleven rules (`RULES.md`) | Each rule with the official QNX 8.0 page it comes from | done | `python3 -I scripts/verifier-citations.py` (36 quotations, 14 pages re-read) |
| The five examples (`examples/`) | Real resource managers, including BlackBerry's own | done | `python3 -I scripts/benchmark-corpus.py` (17 real files, 7 published by QNX or BlackBerry) |
| The test suite (`tests/`) | 97 tests over 22 classes: the two-sided contract, plus the day-of-licence path | done | `bash scripts/run_tests.sh` |
| The codelab (`docs/CODELAB.md`) | 30 minutes, Python 3 only | done | `python3 -I scripts/verifier-codelab.py` |
| The proof of QNX 8.0 (`scripts/qnx8-proof.sh`) | Builds the examples with `qcc`, reads the ELF header, runs them on a target | waiting | exits 2 while the SDP is absent — that is the counter-proof, not a failure |
| The installation of the SDP (`scripts/install-sdp8.sh`) | Installs the SDP 8.0 with the official QNX Software Center commands, then calls the proof | done | `bash scripts/install-sdp8.sh --check` (the pre-flight), and it exits 3 with the list of the missing pieces when the secrets are not in the environment |
| The network measurement (`scripts/mesurer-reseau-qnx.sh`) | One line per QNX host: the exact command and what it answered | done | `bash scripts/mesurer-reseau-qnx.sh` |
| The published video (`media/qx-demo-v3.mp4`) | 89.72 s, 18 scenes, every figure re-measured | done | `python3 -I scripts/audit-sous-titres-pixels.py` (the subtitles ARE the pixels) |
| The submission text (`docs/SUBMISSION-EN.md`) | Field by field, everything to paste into DevPost | done | `python3 -I scripts/verifier-soumission-devpost.py` |
| The continuous integration | A GitHub Actions workflow that replays the proofs | waiting | the token of the owner has no `workflow` scope |

## 2. The figures that are published, and where they come from

| Figure | Where it is published | The command that measures it |
|---|---|---|
| 97 tests, 22 classes | `README.md`, `docs/SUBMISSION-EN.md` | `bash scripts/run_tests.sh` |
| 89 files in the published tree | `docs/SUBMISSION-EN.md` | `git ls-files \| wc -l` |
| 17 real resource managers analysed | `docs/BENCHMARK.md` | `python3 -I scripts/benchmark-corpus.py` |
| 36 quotations of 14 official pages | `RULES.md` | `python3 -I scripts/verifier-citations.py` |
| 89.72 s of video | `docs/YOUTUBE-VIDEO.md` | `ffprobe` |

Every control has its counter-proof: a figure that is deliberately falsified
in a copy of the published documents must be reported as stale.  The
counter-proof runs at every normal run, so a control cannot silently lose
its teeth.

## 3. Progress of this cycle — 17 November 2026, 15:21 (the installation of the SDP 8.0, measured)

- **The question of the cycle**: make the *real* installation of the QNX SDP
  8.0 executable in the container that builds this repository, and prove by
  measurement exactly what is still missing.  The answer is now written in
  code and in a dated file, not in a sentence.
- **`scripts/install-sdp8.sh` is new** (and published).  It uses the
  official QNX Software Center commands, each one with its source in the
  header: the extraction of the client, `-addLicenseKey`, `-mirrorBaseline
  qnx800`, `-installBaseline com.qnx.qnx800`, then
  `source qnxsdp-env.sh`, `qcc -V` and `scripts/qnx8-proof.sh`, whose exit
  code it propagates.  The licence key and the myQNX password are read from
  the environment and from nowhere else: they are never in this repository,
  never in a log of the script, and never in a report.
- **It fails the way it must.**  Run without the three environment
  variables, it prints the three missing variables and the missing
  installer, and exits 3 without touching anything.  A script that cannot
  fail proves nothing.
- **The network is measured, not assumed** (`docs/MESURE-RESEAU-20261117.md`,
  replayed by `scripts/mesurer-reseau-qnx.sh`): `www.qnx.com` answers
  (HTTP 301), and the official technote says the myQNX server and the QNX
  licence server are both hosted there; `download.qnx.com` **times out at
  the TCP level** from this machine (20 s, 45 s, and a raw socket after
  25 s); and four of the seven names of the measurement request —
  `my.qnx.com`, `account.qnx.com`, `qnx.qnx.com`, `update.qnx.com` —
  **do not exist in the public DNS** (NXDOMAIN from a public resolver), so
  they cannot answer: they are not blocked, they have no address.
- **The client itself cannot be downloaded without an account**: the
  official link answers 302 and lands on `www.qnx.com/account/login.html`.
  The exact file is `qnx-setup-2.0.4-202501021438-linux.run` (99.85 MB).
- **What is still missing, exactly**: (1) the file
  `qnx-setup-2.0.4-202501021438-linux.run`, (2) the three environment
  variables `MYQNX_USER`, `MYQNX_PASSWORD`, `QNX_LICENSE_KEY`, (3) a
  network that can reach the content management server(s) that carry the
  packages — the official technote says their name is only known at
  runtime, and the log of the QNX Software Center
  (`~/.qnx/swupdate/.metadata/.log`) names the one that fails.
- **Nothing is simulated.**  `qcc -V` still answers 127 (the compiler is
  absent) and `scripts/qnx8-proof.sh` still exits 2 ("SDP absent"): the
  published documents keep saying **NOT MEASURED**, and that is the truth.

## 4. The earlier cycles (summary)

| Cycle | What it did |
|---|---|
| 197 | The path of the judge: a PEP 668-safe installation, a stale "51-test" found and fixed |
| 198 | The tool that applies the URL of the video, and the watch that detects it |
| 199-200 | The proof of QNX 8.0 written, published and proved from the outside; a factual error about QX PORTMAP corrected |
| 201 (this one) | The installation of the SDP 8.0 made executable and measured; the network measured host by host |
