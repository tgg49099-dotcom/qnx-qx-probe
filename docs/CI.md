# QX-PROBE in continuous integration

QX-PROBE prints a human-readable report by default. For a CI chain it also
speaks two machine formats, with **the same findings and the same exit code**
(`0` = no ERROR/WARN, `1` = at least one, `2` = bad usage):

```console
$ python3 -I qx_probe.py --format json  src/*.c > qx-probe.json
$ python3 -I qx_probe.py --format sarif src/*.c > qx-probe.sarif
```

Every finding carries the **line of the source file** it is about (the call
to `resmgr_attach()`, the definition of the read handler, the
`iofunc_func_init()` call...), so an editor or a code-review tool can jump
to it.

## SARIF 2.1.0: findings as annotations on the pull request

SARIF is the OASIS standard read by GitHub code scanning, GitLab, Azure
DevOps and the SARIF viewers of VS Code and Visual Studio. The output is
validated in this repository against the official OASIS SARIF 2.1.0 JSON
schema (35 results on `examples/*.c` and the test fixture: valid; the same
document with `"version": "2.0"` is rejected).

A minimal GitHub Actions job, for a repository that contains QNX resource
managers (copy `qx_probe.py` into it, or fetch it at a pinned commit):

```yaml
name: qx-probe
on: [push, pull_request]
permissions:
  contents: read
  security-events: write      # needed to upload SARIF
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: QX-PROBE (QNX 8.0 resource-manager protocol)
        run: python3 -I qx_probe.py --format sarif src/*.c > qx-probe.sarif
        continue-on-error: true   # let the upload run; the annotations show the findings
      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: qx-probe.sarif
          category: qx-probe
```

To make the job fail on an actionable finding instead, drop
`continue-on-error` and keep the exit code as the gate.

This workflow is an example for your project: it is **not run** in this
repository, and it has not been measured on GitHub. What is measured here is
the SARIF document itself (`tests/test_output_formats.py`, and the schema
check above).
