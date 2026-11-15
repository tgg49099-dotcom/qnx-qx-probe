# YouTube upload package — QX-PROBE (QNX Global Hackathon)

The rules require the demonstration video to be *"uploaded to and made publicly
visible on YouTube"* and its link to be given on the DevPost form. This page
holds everything needed to do that: the exact title, the exact description, the
exact file, the thumbnail, the five gestures, and the two places where the link
goes. Nothing else is required, and nothing has to be written from scratch.

## 1. Title — paste exactly this (48 characters)

```
QX-PROBE: a linter for QNX 8.0 resource managers
```

## 2. Description — paste exactly this (1722 characters)

```
QX-PROBE is a dependency-free static checker for QNX 8.0 resource managers: it reads your C source and reports the protocol mistakes the compiler cannot see — a missing access gate, a message loop that never dispatches, a reply that returns more parts than the IOV holds. Each of its eleven rules is backed by an official QNX SDP 8.0 documentation page, cited in the repository.

What this video shows (89.72 s, English, no music, no voice-over):
- the real corpus: a QNX 8.0 resource manager published under Apache-2.0;
- the checker stays green on correct code (0 ERROR, 0 WARN);
- the same code with one access gate removed: 1 ERROR, exit code 1;
- a real program split over several files, read as one program;
- the same findings as SARIF 2.1.0 alerts for GitHub code scanning, each one with a link to its rule;
- the benchmark on 17 real public QNX resource managers: one real missing access gate found;
- the 81-test suite, green;
- zero dependency: the Python standard library only, no QNX SDK, no board.

Every sentence is burned into the picture (English subtitles, one per scene);
the file has no audio track at all.

Repository (Apache-2.0): https://github.com/tgg49099-dotcom/qnx-qx-probe
Codelab (30 minutes, no SDK, no board, no licence): https://github.com/tgg49099-dotcom/qnx-qx-probe/blob/main/docs/CODELAB.md
The video file itself, downloadable: https://raw.githubusercontent.com/tgg49099-dotcom/qnx-qx-probe/main/media/qx-demo-v3.mp4

Category: Developer Tooling & Host Tools.
Written with AI assistance (the tool, its rules and this documentation); every QNX 8.0 claim cites an official documentation page, and the reference corpus is BlackBerry's public Apache-2.0 code (see NOTICE in the repository).
```

## 3. The file to upload

| | |
|---|---|
| File | `media/qx-demo-v3.mp4` (in the public repository) |
| Download | https://raw.githubusercontent.com/tgg49099-dotcom/qnx-qx-probe/main/media/qx-demo-v3.mp4 |
| Local copy | `/work/qnx/depot-public/media/qx-demo-v3.mp4` |
| MD5 | `98ec689d13bed874bf2b144538a43d91` |
| Size | 1 417 251 bytes |
| Duration (measured with ffprobe) | **89.72 s** — the limit is 180 s, the target 60–120 s |
| Format | MP4 / H.264 (High, yuv420p), 1920x1080, 25 fps, 2 243 frames |
| Audio | **none** — the file has no audio stream at all |
| Language | English, no voice-over |
| Subtitles | burned into the picture (no separate subtitle file) |

Check the MD5 after the download, before the upload:
`md5sum qx-demo-v3.mp4` must print `98ec689d13bed874bf2b144538a43d91`.

## 4. The thumbnail

| | |
|---|---|
| File | `media/qx-demo-thumbnail.png` (in the public repository) |
| Download | https://raw.githubusercontent.com/tgg49099-dotcom/qnx-qx-probe/main/media/qx-demo-thumbnail.png |
| Local copy | `/work/qnx/depot-public/media/qx-demo-thumbnail.png` |
| MD5 | `d2d5ddea71f5f9c538f10c1a7b9031b8` |
| Size | 404 633 bytes |
| Image | PNG, 1280x720 |

It is frame 1 750 of the video (t = 70.00 s): the benchmark on the 17 real
public QNX resource managers, with the real missing access gate found in
`rpi_thermal/rpi_thermal.c:465`, the real command line above it and the
burned-in subtitle below it. Checked on the published file: that frame, scaled
down to 1280x720, matches the published thumbnail on **98.3 %** of its pixels
(within 8/255).

## 5. The five gestures

1. Open **https://studio.youtube.com** and click **Create (+) ▸ Upload videos**.
2. Select the file downloaded in § 3 (or drop it on the page), then paste the
   title of § 1 and the description of § 2 into the two fields.
3. Click **Show more**, then **Custom thumbnail**, and upload the PNG of § 4.
4. In **Visibility**, choose **Public**, then **Save**.
5. Copy the video link (`https://www.youtube.com/watch?v=…`) and paste it in
   the two places of § 6.

Then check it really is public: open the watch URL while logged out (private
window). The page must play the video without asking for an account.

## 6. Where the link goes

1. **The DevPost form** — the field that asks for the demonstration video
   (the rules: *"a link to the video must be provided on the submission form"*).
2. **The repository** — `docs/SUBMISSION-EN.md`, block `LIENS`: replace the
   line

   ```
   <YOUTUBE_URL_A_COLLER_apres_le_televersement>
   ```

   with the YouTube URL. Send me the URL and I will do that commit myself;
   or paste it in and commit, it is one line.

Both links are checked by the verification script: every URL of
`docs/SUBMISSION-EN.md` must answer HTTP 200, the placeholder excepted.

## 7. What the video contains (checked)

* **No audio at all** — `ffprobe -show_streams` lists a single video stream,
  no audio stream; so no music, no voice-over, nothing copyrighted.
* **No logo of any company**, no third-party image: the 90 frames taken one
  per second over the 89.72 s were looked at one by one (three contact sheets
  of 30 frames), and the 18 frames that carry the 18 burned-in subtitles were
  extracted and read at full resolution.
* **Every line of text on screen** comes from the recording script, which
  executes the real commands and prints their real output. The audit of that
  text — the terminal lines plus the 18 burned-in subtitles, rebuilt from the
  recording timeline with the commands **re-executed on a fresh clone of the
  public repository**, **9 072 characters** (7 964 for the terminal alone) —
  counts: "BlackBerry" 3, "blackberry" 7 (the file name
  `blackberry_eventfd_mgr.c`), "Apache" 2 and "apache" 1 (the licence header
  and its URL), "Python" 1 and "python3" 7 (the toolchain, which the rules
  require us to name), "POSIX" 10 (in the tool's own output), "QNX" 10 (the
  subject of the contest). **No other company name appears**, and "Linux" does
  not appear at all.
* The word **"BlackBerry"** appears three times, as plain text: in the caption
  *"The corpus: BlackBerry's own resource manager, under Apache-2.0"*, in the
  burned-in subtitle *"BlackBerry's own resource manager: 0 ERROR, 0 WARN"*,
  and in the Apache-2.0 header of the corpus (*"Copyright (c) 2025, BlackBerry
  Limited"*). That is the attribution the Apache-2.0 licence **requires** us to
  keep, and the corpus is used with the author's permission; the rule only
  forbids third-party marks *"unless the Entrant has permission to use such
  material"*.
* The **subtitles** are burned into the picture (there is no separate `.srt`
  file and no text stream in the MP4): one short sentence per scene, in
  English, two lines at most, at least 3.20 s on screen (the rules ask for
  2.5 s), drawn in a band at the bottom that never covers a line of code or of
  output.

## 8. The 18 burned-in subtitles

There is no separate subtitle file: every sentence below is drawn **in the
pixels** of the frames, in a band at the bottom of the picture that never
covers a line of code or of output. One sentence per scene, in English, two
lines at most, at least 3.20 s on screen (the rules ask for 2.5 s).

| # | from (s) | to (s) | duration (s) | subtitle |
|---|---|---|---|---|
| 0 | 0.00–4.00 | 4.00 | A linter for QNX 8.0 resource managers. It runs on the host. |
| 1 | 4.00–7.20 | 3.20 | Every command in this video is a command of the public repository. |
| 2 | 7.20–11.32 | 4.12 | The corpus: BlackBerry's own resource manager, under Apache-2.0. |
| 3 | 11.32–16.32 | 5.00 | BlackBerry's own resource manager: 0 ERROR, 0 WARN. |
| 4 | 16.32–19.52 | 3.20 | A real defect must be reported, not hidden. |
| 5 | 19.52–25.68 | 6.16 | One access gate removed: 1 ERROR, and exit code 1 stops the build. |
| 6 | 25.68–31.16 | 5.48 | The rule is the QNX 8.0 documentation's own sentence. |
| 7 | 31.16–34.36 | 3.20 | Real QNX programs are split over several files. |
| 8 | 34.36–39.72 | 5.36 | One file alone: the message loop lives in another file, so a WARN and exit code 1. |
| 9 | 39.72–46.08 | 6.36 | The three files read together, as one program: 0 ERROR, 0 WARN. |
| 10 | 46.08–49.28 | 3.20 | The same findings, as alerts in GitHub code scanning. |
| 11 | 49.28–59.44 | 10.16 | Each alert carries its rule, its level and a link to the rule and its QNX source. |
| 12 | 59.44–62.64 | 3.20 | Then on code the tool was never written for. |
| 13 | 62.64–72.68 | 10.04 | 17 public resource managers, each pinned to a commit: one real missing access gate. |
| 14 | 72.68–75.88 | 3.20 | The suite checks both sides: no false positive, real defects caught. |
| 15 | 75.88–80.64 | 4.76 | 81 tests pass, from a clean clone. |
| 16 | 80.64–85.24 | 4.60 | Only the Python standard library: no QNX SDK, no board, no licence. |
| 17 | 85.24–89.72 | 4.48 | End of the demonstration. The source is in the public repository. |

The whole video is 18 scenes, 2 243 frames, 89.72 s.

The table above is not a transcript written after the fact: every sentence was
**re-rendered independently** from that table and compared with the pixels of
the published file. The text masks match at an IoU of **0.997** (minimum
**0.995** over the 18 scenes, mean absolute error **2.24** per
channel), while a *wrong* sentence — the next scene's — scores at most
**0.554**. The check therefore separates the right text from a wrong
one: it does prove that the picture carries the sentences published here.

**The jury can replay that proof.** It is a script of this repository:

```
$ python3 scripts/audit-sous-titres-pixels.py
```

It needs `ffmpeg` and `pillow` (`pip install pillow`), nothing else — no QNX
SDK, no board, no licence. It reads the table above, reads the second public
copy of the same 18 sentences (`video/SCENARIO.md`), checks that they agree,
extracts the 18 frames from `media/qx-demo-v3.mp4`, re-renders the expected
text and compares the pixels; then it runs the contre-épreuve against the
wrong text and refuses to pass if the two are not clearly separated.

## 9. AI — no clause to declare

**No AI clause found** in the rules. The page
(https://qnx.devpost.com/rules, read on 6 November 2026, read again on
7 November 2026 and read a third time on 12 November 2026, HTTP 200 the
three times, **39 540 characters of text** — HTML
tags stripped, blank lines dropped, the remaining lines joined by newlines;
the same count on the copy of 6 November and on the copy of 7 November. Read
a third time on 12 November 2026, the body of the rules — from its title line
to the end of the page, navigation apart — still gives the same 37 665
characters as on the copies of 6, 7 and 11 November)
contains no requirement to declare, disclose or mention
the use of AI. The word "AI", taken as a word of its own, occurs **4 times**
in the whole page, and the 4 occurrences are only **3 different texts**
(the navigation menu is printed twice) — the same 4 occurrences, in the same
3 texts, on the copy of 12 November 2026:

* the DevPost navigation menu — *"By use case / AI hackathons"* (a link, not
  a rule; printed twice in the page);
* the judging methods, which concern the organisers, not the entrants —
  *"This process may utilize expert panels, peer review, automated AI-driven
  analysis, or any combination thereof to ensure efficient, fair, and objective
  evaluation."* ;
* a judging criterion — *"Innovation & AI Creativity : Is this a creative,
  non-obvious use of QNX and does the team show genuine understanding of the
  problem space they're working in?"*.

The closest rule to the question is the intellectual property clause, which
**allows** assistance: *"An Entrant may contract with a third party for
technical assistance to create the Submission provided the Submission
components are solely the Entrant's work product and the result of the
Entrant's ideas and creativity, and the Entrant owns all rights to them."*

The one-line mention of the AI assistance in the description of § 2 is
therefore **voluntary**: it is there because the `NOTICE` file of the repository
already states it, and the two must not contradict each other.
