# Question 5 — video handover

Three files:

| File | What it is |
|---|---|
| `Q5_speech.md` | The script (675 words, ~4:40), cue cards to present from, and delivery notes |
| `Q5_handover_deck.pptx` | 8 slides, 16:9, with a reserved panel for your video on every slide |
| `build_deck.py` | Regenerates the deck — edit the text here rather than in PowerPoint if you want the change kept |

## The video panel

Every slide leaves the left-hand block empty for you:

- **position** 0.45 in from the left, 0.75 in from the top
- **size** 5.10 in wide × 6.00 in tall, on a 13.333 × 7.5 in (16:9) slide
- that is 38% of the slide width and 80% of its height — deliberately taller than a 16:9 webcam
  frame, so a cropped upper-body shot fills it rather than sitting in a letterbox

The grey rounded rectangle is only a guide. **Delete it on every slide before you record** (select it,
press Delete — it is the only shape on the left half), or leave it if you prefer your camera to sit
inside a visible frame.

How to get the camera there depends on your tool:

- **PowerPoint (Microsoft 365)** — Insert → Cameo, then drag and crop the camera shape onto the panel.
  Record with Slide Show → Record.
- **OBS / Zoom / Teams recording** — share the deck in Presenter view or full screen, then position
  the webcam source over the panel and crop it to 5.10 : 6.00 (roughly 0.85 : 1).
- **Neither** — record yourself full-frame against the deck on a second screen. The rubric asks for a
  full or upper-body shot to camera; it does not require slides at all, so the deck is support, not a
  requirement.

The speaker notes on each slide hold that section's script and its timing cue, so Presenter view
gives you the cue cards without you reading from a second screen.

## Timing

675 words, about 4:40 at a measured pace. The hurdle is 3–5 minutes and markers stop at 5:00. Time a
practice run; if it lands over 4:30, drop the two passages marked *[cut if long]*, which takes it to
about 4:15. Do not speed the recording up — the video guidance rules that out explicitly.

The deck runs title → what I built → the verdict → what it supports → where it should not be relied
on → how it was produced → how it was checked → PG1. The second slide is orientation for a reviewer
who has not seen the work; it is about 43 seconds and it is the first thing to shorten if you are
long, since the marks sit in the three sections after it.

## Two rubric hurdles worth re-reading before you record

1. **"Does not appear to be reading word for word from a script."** Learn the argument and the
   numbers from `Q5_speech.md`, then present from the cue cards at the end of it.
2. **"The video, the notebook and AI logs submitted tell one consistent story."** The script says you
   used Claude heavily throughout and that the judgement calls were yours. That matches the notebook's
   AI-use cells and the transcripts in `ai_logs/` — but only once the items below are done.

## Still outstanding in the notebook

These are placeholders in `DSA_2026_S2_Assignment_template.ipynb`, not things this folder fixes:

- **Member ID and date** at the top — both still `[INSERT]`.
- **AI-use cells for Q1, Q2 and Q3** still carry the `TO COMPLETE BEFORE SUBMISSION` banner telling
  you to rewrite the notes in your own words. Q4's is already written in your voice.
- **The Q1 session log** is flagged as not yet exported to `ai_logs/`. If it cannot be recovered,
  record that honestly with `write_manual_note()` rather than leaving a silent gap.
- **`compile_ai_logs.py`** has to be run to produce `ai_logs/AI_LOGS.md`, which is the file you
  submit.
- **The Q5 AI-use cell** is a one-line disclosure and is still blank. Something like — *check it
  against what you actually did before using it* — "Claude Code was used to draft the video script and
  build the presentation slides from the assignment brief, the rubric and my executed notebook; the
  opinion, the judgements described and the delivery are my own."
- **The video link cell** at the bottom of the notebook — paste the unlisted YouTube URL there. The
  brief requires it as a hyperlink at the foot of the notebook, and an unlisted link is required, not
  a private one.
- **File naming** — `DSA 2026 S2 Assignment <member ID>` for the recording, per the brief.
