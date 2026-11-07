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

## 2. Description — paste exactly this (1 651 characters)

```
QX-PROBE is a dependency-free static checker for QNX 8.0 resource managers: it reads your C source and reports the protocol mistakes the compiler cannot see — a missing access gate, a message loop that never dispatches, a reply that returns more parts than the IOV holds. Each of its eleven rules is backed by an official QNX SDP 8.0 documentation page, cited in the repository.

What this video shows (71.44 s, English, no music, no voice-over):
- the real corpus: a QNX 8.0 resource manager published under Apache-2.0;
- the checker stays green on correct code (0 ERROR, 0 WARN);
- the false positive of an earlier version, acknowledged: a read-only manager mounted outside /dev/ gives 0 ERROR, 0 WARN, and the rule behind it is quoted from the QNX 8.0 documentation;
- the same code with one access gate removed: 1 ERROR, exit code 1;
- the 27-test suite, green;
- zero dependency: the Python standard library only, no QNX SDK, no board.

Every sentence is burned into the picture (English subtitles, one per scene);
the file has no audio track at all.

Repository (Apache-2.0): https://github.com/tgg49099-dotcom/qnx-qx-probe
Codelab (30 minutes, no SDK, no board, no licence): https://github.com/tgg49099-dotcom/qnx-qx-probe/blob/main/docs/CODELAB.md
The video file itself, downloadable: https://raw.githubusercontent.com/tgg49099-dotcom/qnx-qx-probe/main/media/qx-demo-v2.mp4

Category: Developer Tooling & Host Tools.
Written with AI assistance (the tool, its rules and this documentation); every QNX 8.0 claim cites an official documentation page, and the reference corpus is BlackBerry's public Apache-2.0 code (see NOTICE in the repository).
```

## 3. The file to upload

| | |
|---|---|
| File | `media/qx-demo-v2.mp4` (in the public repository) |
| Download | https://raw.githubusercontent.com/tgg49099-dotcom/qnx-qx-probe/main/media/qx-demo-v2.mp4 |
| Local copy | `/work/qnx/depot-public/media/qx-demo-v2.mp4` |
| MD5 | `178e1b58638628a5bc56f11c6fada8e2` |
| Size | 1 367 966 bytes |
| Duration (measured with ffprobe) | **71.44 s** — the limit is 180 s, the target 60–120 s |
| Format | MP4 / H.264 (High, yuv420p), 1920x1080, 25 fps, 1786 frames |
| Audio | **none** — the file has no audio stream at all |
| Language | English, no voice-over |
| Subtitles | burned into the picture (no separate subtitle file) |

Check the MD5 after the download, before the upload:
`md5sum qx-demo-v2.mp4` must print `178e1b58638628a5bc56f11c6fada8e2`.

## 4. The thumbnail

| | |
|---|---|
| File | `media/qx-demo-thumbnail.png` (in the public repository) |
| Download | https://raw.githubusercontent.com/tgg49099-dotcom/qnx-qx-probe/main/media/qx-demo-thumbnail.png |
| Local copy | `/work/qnx/depot-public/media/qx-demo-thumbnail.png` |
| MD5 | `c7e26bd7fa6105fca7594afb4f277775` |
| Size | 240 247 bytes |
| Image | PNG, 1280x720 |

It is frame 1074 of the video (t = 42.96 s): the checker reporting the missing
access gate, with the real command line above it and the burned-in subtitle
below it. Checked on the published file: that frame, scaled down to 1280x720,
matches the published thumbnail on **94.6 %** of its pixels (within 8/255).

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
* **No logo of any company**, no third-party image: the 72 frames taken one
  per second over the 71.44 s were looked at one by one (six contact sheets),
  and the 19 frames that carry the 19 burned-in subtitles were extracted and
  read at full resolution.
* **Every line of text on screen** comes from the recording script, which
  executes the real commands and prints their real output. The audit of that
  text — the terminal lines plus the 19 burned-in subtitles, rebuilt from the
  recording script with the commands re-executed in the repository, **6 063
  characters** (4 887 for the terminal alone) — counts: "BlackBerry" 4,
  "blackberry" 7 (the
  file name `blackberry_eventfd_mgr.c`), "Apache" 2 and "apache" 1 (the
  licence header and its URL), "Python" 2 and "python3" 5 (the toolchain,
  which the rules require us to name), "POSIX" 7 (in the tool's own output),
  "QNX" 16 (the subject of the contest). **No other company name appears**,
  and "Linux" does not appear at all.
* The word **"BlackBerry"** appears four times, as plain text: in the caption
  *"The corpus: a real QNX 8.0 resource manager, published by BlackBerry"*,
  in two burned-in subtitles, and in the Apache-2.0 header of the corpus
  (*"Copyright (c) 2025, BlackBerry Limited"*). That is the attribution the
  Apache-2.0 licence **requires** us to keep, and the corpus is used with the
  author's permission; the rule only forbids third-party marks *"unless the
  Entrant has permission to use such material"*.
* The **subtitles** are burned into the picture (there is no separate `.srt`
  file and no text stream in the MP4): one short sentence per scene, in
  English, two lines at most, at least 2.5 s on screen, drawn in a band at the
  bottom that never covers a line of code or of output.

## 8. The 19 burned-in subtitles

There is no separate subtitle file: every sentence below is drawn **in the
pixels** of the frames, in a band at the bottom of the picture that never
covers a line of code or of output. One sentence per scene, in English, two
lines at most, at least 3.12 s on screen (the rules ask for 2.5 s).

| # | from (s) | to (s) | duration (s) | subtitle |
|---|---|---|---|---|
| 0 | 0.00–3.12 | 3.12 | A linter for QNX 8.0 resource managers. It runs on the host. |
| 1 | 3.12–6.24 | 3.12 | It reports the protocol mistakes the QNX compiler cannot see. |
| 2 | 6.24–9.36 | 3.12 | Every command of this video is a command of the public repository. |
| 3 | 10.24–14.48 | 4.24 | The Apache-2.0 header of BlackBerry's own resource manager. |
| 4 | 14.48–17.60 | 3.12 | Correct QNX 8.0 code must produce no error and no warning. |
| 5 | 18.36–22.48 | 4.12 | BlackBerry's own resource manager: 0 ERROR, 0 WARN. |
| 6 | 22.48–25.60 | 3.12 | Now the case an earlier version of this tool got wrong. |
| 7 | 26.36–30.56 | 4.20 | A read-only manager mounted outside /dev/: 0 ERROR, 0 WARN. |
| 8 | 30.56–33.68 | 3.12 | QNX 8.0 documentation: the path joins the general pathname space.<br>An earlier version of this tool wrongly flagged that case. |
| 9 | 33.68–36.80 | 3.12 | The rule that the earlier version of the tool misread. |
| 10 | 36.80–39.92 | 3.12 | A real defect must be reported, not hidden. |
| 11 | 40.84–45.08 | 4.24 | One access gate removed: the checker reports 1 ERROR. |
| 12 | 45.08–48.20 | 3.12 | The exit code tells the build system to stop. |
| 13 | 49.00–52.68 | 3.68 | The exit code is 1, so the checker can gate a CI pipeline. |
| 14 | 52.68–55.80 | 3.12 | The suite checks both sides: no false positive, real defects caught. |
| 15 | 56.80–60.60 | 3.80 | 27 tests pass: no false positive, and real defects caught. |
| 16 | 60.60–63.72 | 3.12 | No QNX SDK, no board, no licence: Python 3 is enough. |
| 17 | 64.48–68.32 | 3.84 | Only the Python standard library is imported: no QNX SDK, no board. |
| 18 | 68.32–71.44 | 3.12 | End of the demonstration. The source is in the public repository. |

The whole video is 19 scenes, 1 786 frames, 71.44 s.

The table above is not a transcript written after the fact: every sentence was
**re-rendered independently** from that table and compared with the pixels of
the published file. The text masks match at an IoU of **0.998** (minimum 0.997
over the 19 scenes, mean absolute error 1.77 per channel), while a *wrong*
sentence — the next scene's — scores at most 0.547. The check therefore
separates the right text from a wrong one: it does prove that the picture
carries the sentences published here.

## 9. AI — no clause to declare

**No AI clause found** in the rules. The page
(https://qnx.devpost.com/rules, read on 6 November 2026 and read again on
7 November 2026, HTTP 200 both times, **39 540 characters of text** — HTML
tags stripped, blank lines dropped, the remaining lines joined by newlines;
the same count on the copy of 6 November and on the copy of 7 November)
contains no requirement to declare, disclose or mention
the use of AI. The word "AI", taken as a word of its own, occurs **4 times**
in the whole page, and the 4 occurrences are only **3 different texts**
(the navigation menu is printed twice):

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
