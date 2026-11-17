# Network measurement of 17 November 2026 — what the QNX servers answer from the machine that built this repository

**Date:** 17 November 2026, 14:29 UTC.
**Host:** the Linux container (Debian 12, x86_64) in which this repository is
built and published.
**Command to replay everything:** `bash scripts/mesurer-reseau-qnx.sh`
(the output of this file was produced by that script, on this host, on this
date).

This file is a **measurement**, not a promise. Every line below is the answer
a command gave on this host on this date. Nothing here is a forecast.

---

## 1. The seven hosts of the measurement request

One line per host: the exact command, then what it answered.

| Host | Exact command | Result |
|---|---|---|
| `www.qnx.com` | `curl -sS -o /dev/null -w '%{http_code}' --max-time 20 https://www.qnx.com/` | **HTTP 301** — answers |
| `download.qnx.com` | `curl -sS -o /dev/null -w '%{http_code}' --max-time 20 https://download.qnx.com/` | **TIMEOUT** — no answer after 20 s, at the TCP level |
| `my.qnx.com` | `curl -sS -o /dev/null -w '%{http_code}' --max-time 20 https://my.qnx.com/` | **NO DNS NAME** — the host does not exist |
| `account.qnx.com` | `curl -sS -o /dev/null -w '%{http_code}' --max-time 20 https://account.qnx.com/` | **NO DNS NAME** — the host does not exist |
| `packages.qnx.com` | `curl -sS -o /dev/null -w '%{http_code}' --max-time 20 https://packages.qnx.com/` | **HTTP 301** — answers, redirects |
| `qnx.qnx.com` | `curl -sS -o /dev/null -w '%{http_code}' --max-time 20 https://qnx.qnx.com/` | **NO DNS NAME** — the host does not exist |
| `update.qnx.com` | `curl -sS -o /dev/null -w '%{http_code}' --max-time 20 https://update.qnx.com/` | **NO DNS NAME** — the host does not exist |

## 2. The same hosts in the public DNS — a dead name is not a blocked connection

The four hosts that answered "no DNS name" were checked against a public
resolver, so that the answer does not depend on the resolver of this
container.

| Host | Exact command | Result |
|---|---|---|
| `www.qnx.com` | `curl -sS --max-time 15 'https://dns.google/resolve?name=www.qnx.com&type=A'` | `A 209.226.137.53` |
| `download.qnx.com` | `curl -sS --max-time 15 'https://dns.google/resolve?name=download.qnx.com&type=A'` | `A 209.226.137.82` |
| `my.qnx.com` | `curl -sS --max-time 15 'https://dns.google/resolve?name=my.qnx.com&type=A'` | **NXDOMAIN** — the name does not exist |
| `account.qnx.com` | `curl -sS --max-time 15 'https://dns.google/resolve?name=account.qnx.com&type=A'` | **NXDOMAIN** — the name does not exist |
| `packages.qnx.com` | `curl -sS --max-time 15 'https://dns.google/resolve?name=packages.qnx.com&type=A'` | `A 72.1.202.85` |
| `qnx.qnx.com` | `curl -sS --max-time 15 'https://dns.google/resolve?name=qnx.qnx.com&type=A'` | **NXDOMAIN** — the name does not exist |
| `update.qnx.com` | `curl -sS --max-time 15 'https://dns.google/resolve?name=update.qnx.com&type=A'` | **NXDOMAIN** — the name does not exist |

**Four of the seven names do not exist in the public DNS.** They cannot be
"blocked": they have no address anywhere. The myQNX service is not reached
through `my.qnx.com`; the official documentation says it is hosted on
`www.qnx.com`.

## 3. The hosts that really serve the QNX services today

| Host | Exact command | Result | What it is |
|---|---|---|---|
| `www.qnx.com/account/login.html` | `curl -sS -o /dev/null -w '%{http_code}' --max-time 20 https://www.qnx.com/account/login.html` | **HTTP 200** | the myQNX login page |
| `licensing.qnx.com` | `curl -sS -o /dev/null -w '%{http_code}' --max-time 20 https://licensing.qnx.com/` | **HTTP 301** → `www.qnx.com/licensing` | the licensing pages |
| `support7.qnx.com` | `curl -sS -o /dev/null -w '%{http_code}' --max-time 20 https://support7.qnx.com/` | **HTTP 403** | the host that serves the download links |
| `fusion.qnx.com` | `curl -sS -o /dev/null -w '%{http_code}' --max-time 20 https://fusion.qnx.com/` | **HTTP 404** | answers; the official technote asks IT teams to whitelist it |
| `packages.qnx.com` | `curl -sSI -L --max-time 30 https://packages.qnx.com/` | **301** → `blackberry.qnx.com/en` → **301** → `qnx.software/en` → **200** | a marketing redirect today, not a package server |
| `myqnx.com` | `curl -sS -o /dev/null -w '%{http_code}' --max-time 20 https://myqnx.com/` | `curl` exit 60: the TLS certificate does not cover that name | a redirect host |

## 4. `download.qnx.com`: the timeout is at the TCP level

The name resolves (public DNS, and the resolver of this container), and the
connection never starts.

| Test | Exact command | Result |
|---|---|---|
| HTTPS, 20 s | `curl -sS -o /dev/null -w '%{http_code}' --max-time 20 https://download.qnx.com/` | `curl: (28) Connection timed out after 20001 milliseconds` |
| HTTPS, 45 s | `curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 45 https://download.qnx.com/` | `curl: (28) Failed to connect to download.qnx.com port 443 after 45001 ms` |
| raw socket, 25 s | `python3 -c "import socket; socket.create_connection(('209.226.137.82',443),timeout=25)"` | `TimeoutError: timed out` after 25 s |

## 5. What this means for the installation of the SDP 8.0

* **What works from here:** the authentication path. The official technote
  *"About These Technotes"* says the QNX Software Center talks to the
  **myQNX server** and to the **QNX licence server**, both hosted on
  `www.qnx.com`. `www.qnx.com` answers (HTTP 301), and the login page
  answers HTTP 200. So the step that needs credentials can be reached.
* **What does not work from here:** `download.qnx.com` times out at the TCP
  level, after 20 s, after 45 s, and with a raw socket after 25 s.
* **What is NOT proven, and is not claimed:** that `download.qnx.com` is the
  server that would carry the SDP packages. The same official technote says
  the packages come from *"content management server(s)"* whose name is only
  known at runtime, and that the QNX Software Center log names the server
  that failed. The honest statement is therefore: **the host named
  `download.qnx.com` is unreachable from this machine, and whether it is the
  one that matters cannot be known before the client runs.**
* **What to do the day the account exists:** run `scripts/install-sdp8.sh`.
  It measures the network before it installs, and the log of the QNX
  Software Center (`~/.qnx/swupdate/.metadata/.log`) names the server that
  failed, if one does.

## 6. The download of the client itself needs an account

| Question | Measured answer |
|---|---|
| Exact name of the Linux client | `qnx-setup-2.0.4-202501021438-linux.run` (QNX Software Center 2.0.4, build 202501021438, 99.85 MB, 64-bit Linux host) |
| Official page | `https://www.qnx.com/download/group.html?programid=29178` (read 17 November 2026) |
| Direct link | `https://www.qnx.com/download/download/79441/qnx-setup-2.0.4-202501021438-linux.run` |
| Can it be fetched without an account? | **No.** The link answers `302` → `support7.qnx.com` → `302` → `www.qnx.com/account/authenticate.html?id=79441` → `301` → `www.qnx.com/account/login.html` → **200** (the login page) |
| Space needed | the SDP installed is about 4-5 GB; **62 830 MB were free** on this host (`df -Pm /work` → 62 830) |

## 7. Sources, all read on 17 November 2026

* Command line of the QNX Software Center:
  <https://www.qnx.com/developers/docs/qsc/com.qnx.doc.qsc.user_guide/topic/commandline_qsc.html>
* Technote "About These Technotes" (the server processes of the QNX
  Software Center):
  <http://www.qnx.com/developers/docs/qsc/technotes/topic/about.html>
* Technote "Cannot connect to the server":
  <https://www.qnx.com/developers/docs/qsc/com.qnx.doc.qsc.technotes/topic/connect_to_server.html>
* Public procedure "Install QNX SDP 8.0 on WSL":
  <https://github.com/Maetis/qnx-sdp-projects/blob/main/docs/wsl-install.md>
* Download folder of the QNX Software Center:
  <https://www.qnx.com/download/group.html?programid=29178>
* Free non-commercial licence (QNX Everywhere):
  <https://www.qnx.com/products/everywhere/>

## 8. Third measurement of the same day — 16:37 UTC, no change

The measurement was replayed a third time on **17 November 2026 at 16:37 UTC**
(the two first ones were at 14:41 and 14:53 UTC), with the same command and
from the same host:

```
bash scripts/mesurer-reseau-qnx.sh
```

| Host | Expected (14:29 UTC) | Obtained (16:37 UTC) | |
|---|---|---|---|
| `www.qnx.com` | HTTP 301 | HTTP 301 | unchanged |
| `download.qnx.com` | TIMEOUT | TIMEOUT (TCP, 20 s) | unchanged |
| `my.qnx.com` | NO DNS NAME | NO DNS NAME | unchanged |
| `account.qnx.com` | NO DNS NAME | NO DNS NAME | unchanged |
| `packages.qnx.com` | HTTP 301 | HTTP 301 | unchanged |
| `qnx.qnx.com` | NO DNS NAME | NO DNS NAME | unchanged |
| `update.qnx.com` | NO DNS NAME | NO DNS NAME | unchanged |

The four extra hosts were measured again as well: `licensing.qnx.com` → 301,
`support7.qnx.com` → 403, `fusion.qnx.com` → 404, `myqnx.com` → TLS
certificate error (curl exit 60). The public GitHub API answered HTTP 200.

**Nothing moved between 14:29 and 16:37 UTC.** The only thing that changed on
this host today is the login page itself, which was read again at 17:38 UTC
(28 680 bytes, the form fields `userlogin`, `password` and the hidden
`returnaddress`): the account that the download needs is still the only thing
that is missing.

## 9. Fourth measurement of the same day — 22:25 UTC, no change

The measurement was replayed a fourth time on **17 November 2026 at 22:25 UTC**
(the three first ones were at 14:41, 14:53 and 16:37 UTC), with the same
command and from the same host:

```
bash scripts/mesurer-reseau-qnx.sh
```

| Host | Expected (16:37 UTC) | Obtained (22:25 UTC) | |
|---|---|---|---|
| `www.qnx.com` | HTTP 301 | HTTP 301 | unchanged |
| `download.qnx.com` | TIMEOUT | TIMEOUT (TCP, 20 s) | unchanged |
| `my.qnx.com` | NO DNS NAME | NO DNS NAME | unchanged |
| `account.qnx.com` | NO DNS NAME | NO DNS NAME | unchanged |
| `packages.qnx.com` | HTTP 301 | HTTP 301 | unchanged |
| `qnx.qnx.com` | NO DNS NAME | NO DNS NAME | unchanged |
| `update.qnx.com` | NO DNS NAME | NO DNS NAME | unchanged |

The four extra hosts were measured again as well: `licensing.qnx.com` → 301,
`support7.qnx.com` → 403, `fusion.qnx.com` → 404, `myqnx.com` → TLS
certificate error (curl exit 60). The public GitHub API answered HTTP 200.

**Nothing moved between 14:29 and 22:25 UTC.** The state of the network is
therefore stable across four measurements of the same day, and it is still
the myQNX account that is missing, not the network.
