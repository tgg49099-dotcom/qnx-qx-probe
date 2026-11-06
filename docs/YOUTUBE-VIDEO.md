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

## 2. Description — paste exactly this (1 348 characters)

```
QX-PROBE is a dependency-free static checker for QNX 8.0 resource managers: it reads your C source and reports the protocol mistakes the compiler cannot see — a missing access gate, a message loop that never dispatches, a reply that returns more parts than the IOV holds. Each of its eleven rules is backed by an official QNX SDP 8.0 documentation page, cited in the repository.

What this video shows (44.48 s, English, no music, no voice-over):
- the real corpus: a QNX 8.0 resource manager published under Apache-2.0;
- the checker stays green on correct code (0 ERROR, 0 WARN);
- the same code with one access gate removed: 1 ERROR, exit code 1;
- the 27-test suite, green;
- zero dependency: the Python standard library only, no QNX SDK, no board.

Repository (Apache-2.0): https://github.com/tgg49099-dotcom/qnx-qx-probe
Codelab (30 minutes, no SDK, no board, no licence): https://github.com/tgg49099-dotcom/qnx-qx-probe/blob/main/docs/CODELAB.md
The video file itself, downloadable: https://raw.githubusercontent.com/tgg49099-dotcom/qnx-qx-probe/main/media/qx-demo-v1.mp4

Category: Developer Tooling & Host Tools.
Written with AI assistance (the tool, its rules and this documentation); every QNX 8.0 claim cites an official documentation page, and the reference corpus is BlackBerry's public Apache-2.0 code (see NOTICE in the repository).
```

## 3. The file to upload

| | |
|---|---|
| File | `media/qx-demo-v1.mp4` (in the public repository) |
| Download | https://raw.githubusercontent.com/tgg49099-dotcom/qnx-qx-probe/main/media/qx-demo-v1.mp4 |
| Local copy | `/work/qnx/depot-public/media/qx-demo-v1.mp4` |
| MD5 | `3558d267dfebc54c275c2c879787b76b` |
| Size | 907 244 bytes |
| Duration (measured with ffprobe) | **44.48 s** — the limit is 180 s |
| Format | MP4 / H.264, 1920x1080, 25 fps, 1112 frames |
| Audio | **none** — the file has no audio stream at all |
| Language | English, no voice-over |

Check the MD5 after the download, before the upload:
`md5sum qx-demo-v1.mp4` must print `3558d267dfebc54c275c2c879787b76b`.

## 4. The thumbnail

| | |
|---|---|
| File | `media/qx-demo-thumbnail.png` (in the public repository) |
| Download | https://raw.githubusercontent.com/tgg49099-dotcom/qnx-qx-probe/main/media/qx-demo-thumbnail.png |
| Local copy | `/work/qnx/depot-public/media/qx-demo-thumbnail.png` |
| MD5 | `4b847ad3f61b1f4182e0d14743c15950` |
| Size | 222 648 bytes |
| Image | PNG, 1280x720 |

It is frame 620 of the video (t = 24.8 s): the checker reporting the missing
access gate, with the real command line above it.

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
* **No logo of any company**, no third-party image: the 45 frames taken one
  per second over the 44.48 s were looked at one by one.
* The word **"BlackBerry"** appears three times, as plain text: in the caption
  *"The corpus: a real QNX 8.0 resource manager, published by BlackBerry
  (Apache-2.0)"*, in the Apache-2.0 header of the corpus
  (*"Copyright (c) 2025, BlackBerry Limited"*), and in the file name
  `examples/blackberry_eventfd_mgr.c`. That is the attribution the Apache-2.0
  licence **requires** us to keep, and the corpus is used with the author's
  permission; the rule only forbids third-party marks *"unless the Entrant has
  permission to use such material"*.

## 8. AI — no clause to declare

**No AI clause found** in the rules. The page
(https://qnx.devpost.com/rules, read on 6 November 2026) contains no
requirement to declare, disclose or mention the use of AI. The three
occurrences of "AI" in the whole page are:

* the DevPost navigation menu — *"AI hackathons"* (a link, not a rule);
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
