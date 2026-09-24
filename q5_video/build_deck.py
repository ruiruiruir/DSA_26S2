"""Build the Question 5 handover deck.

16:9, one slide per section of the speech, with the left ~42% of every slide left empty
as a landing zone for the talking-head video. Speaker notes carry the script for that
section plus its timing cue.

    python3 build_deck.py
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# --- geometry -------------------------------------------------------------
SLIDE_W, SLIDE_H = Inches(13.333), Inches(7.5)

VID_L, VID_T = Inches(0.45), Inches(0.75)
VID_W, VID_H = Inches(5.10), Inches(6.00)   # the reserved video panel

TXT_L = Inches(6.05)
TXT_W = SLIDE_W - TXT_L - Inches(0.6)

# --- palette --------------------------------------------------------------
INK = RGBColor(0x14, 0x1B, 0x2D)   # near-black navy, body text
MUTED = RGBColor(0x5A, 0x64, 0x78)  # secondary text
ACCENT = RGBColor(0x1F, 0x4E, 0x79)  # headings, rules
FLAG = RGBColor(0xA8, 0x32, 0x2D)   # the "do not rely" red
PANEL = RGBColor(0xED, 0xF0, 0xF5)  # video panel fill
PANEL_EDGE = RGBColor(0xC2, 0xCB, 0xD8)
PANEL_LABEL = RGBColor(0x9A, 0xA4, 0xB2)
BG = RGBColor(0xFF, 0xFF, 0xFF)

HEAD_FONT = "Calibri"
BODY_FONT = "Calibri"


def add_slide(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H)
    bg.fill.solid()
    bg.fill.fore_color.rgb = BG
    bg.line.fill.background()
    bg.shadow.inherit = False
    return s


def video_panel(slide, label="VIDEO"):
    """The reserved area. Delete these two shapes before recording if you would
    rather composite the camera over plain white."""
    p = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, VID_L, VID_T, VID_W, VID_H)
    p.adjustments[0] = 0.02
    p.fill.solid()
    p.fill.fore_color.rgb = PANEL
    p.line.color.rgb = PANEL_EDGE
    p.line.width = Pt(1.0)
    p.shadow.inherit = False
    tf = p.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    r = tf.paragraphs[0].add_run()
    r.text = label
    r.font.size = Pt(13)
    r.font.name = BODY_FONT
    r.font.color.rgb = PANEL_LABEL
    r.font.bold = True
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    sub = tf.add_paragraph()
    sub.alignment = PP_ALIGN.CENTER
    sub.space_before = Pt(4)
    sr = sub.add_run()
    sr.text = "place your camera here \u00b7 delete this shape before recording"
    sr.font.size = Pt(9)
    sr.font.name = BODY_FONT
    sr.font.color.rgb = PANEL_LABEL
    return p


def textbox(slide, left, top, width, height):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    return tf


def para(tf, text, size, color=INK, bold=False, space_before=0, space_after=8,
         font=BODY_FONT, first=False, italic=False, line_spacing=1.08):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.space_before = Pt(space_before)
    p.space_after = Pt(space_after)
    p.line_spacing = line_spacing
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    r.font.name = font
    r.font.color.rgb = color
    return p


def rule(slide, top, width=Inches(1.5), color=ACCENT):
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, TXT_L, top, width, Pt(3))
    bar.fill.solid()
    bar.fill.fore_color.rgb = color
    bar.line.fill.background()
    bar.shadow.inherit = False


def content_slide(prs, kicker, heading, blocks, notes, accent=ACCENT,
                  lead_pt=19, body_pt=15, gap_pt=14):
    """blocks: list of (lead, body) — lead is the bolded claim, body the evidence."""
    s = add_slide(prs)
    video_panel(s)

    tf = textbox(s, TXT_L, Inches(0.75), TXT_W, Inches(1.5))
    para(tf, kicker.upper(), 12, MUTED, bold=True, first=True, space_after=6)
    para(tf, heading, 30, accent, bold=True, font=HEAD_FONT, space_after=0,
         line_spacing=1.0)

    rule(s, Inches(2.02), color=accent)

    tf = textbox(s, TXT_L, Inches(2.32), TXT_W, Inches(4.5))
    for i, (lead, body) in enumerate(blocks):
        para(tf, lead, lead_pt, INK, bold=True, first=(i == 0),
             space_before=0 if i == 0 else gap_pt, space_after=3)
        if body:
            para(tf, body, body_pt, MUTED, space_after=0, line_spacing=1.12)

    s.notes_slide.notes_text_frame.text = notes
    return s


def main():
    prs = Presentation()
    prs.slide_width, prs.slide_height = SLIDE_W, SLIDE_H

    # ---- 1. title --------------------------------------------------------
    s = add_slide(prs)
    video_panel(s)
    tf = textbox(s, TXT_L, Inches(1.9), TXT_W, Inches(3.4))
    para(tf, "DSA 2026 S2 — QUESTION 5", 12, MUTED, bold=True, first=True, space_after=10)
    para(tf, "Handover to the\nreviewing actuary", 36, ACCENT, bold=True,
         font=HEAD_FONT, space_after=14, line_spacing=1.0)
    para(tf, "Estimating market reactions to the ASC-101, ASC-204 "
             "and ASC-370 readouts", 17, INK, space_after=18, line_spacing=1.15)
    para(tf, "Member ID: [INSERT]", 14, MUTED, space_after=0)
    s.notes_slide.notes_text_frame.text = (
        "[0:00 — ~19s]\n\n"
        "Hello. I'm handing over the analysis behind the IR team's estimates of how the market "
        "will react to our three upcoming readouts. My position: it's fit to inform those "
        "estimates, but not to produce a headline number, and it's far stronger on the downside "
        "than the upside."
    )

    # ---- 2. what I built -------------------------------------------------
    content_slide(
        prs,
        kicker="what I built",
        heading="Four stages",
        blocks=[
            ("Validated the outcome labels.",
             "30 filings read by hand \u00b7 all 2,392 directional labels checked against the "
             "realised move \u00b7 a screen over all 4,539 classifications flags 40%, mostly "
             "timing rather than wrong labels."),
            ("Grouped 1,975 readouts into eight families.",
             "Disease, design, stage and sponsor \u2014 to find comparables for each readout."),
            ("Modelled the three-day abnormal return.",
             "Trial, text and company features, scored on held-out announcements. Explains 20%."),
            ("Applied it to the three readouts.",
             "Three scenarios each, plus a validation, monitoring and refresh plan."),
        ],
        lead_pt=18, body_pt=14, gap_pt=12,
        notes=(
            "[0:19 \u2014 ~43s]\n\n"
            "Four stages.\n\n"
            "I validated the LLM's outcome labels \u2014 thirty filings read by hand against the "
            "original 8-Ks, then all 2,392 directional labels checked against the price move that "
            "followed. That gave a screen scoring all 4,539 classifications, which flags forty per "
            "cent, mostly for timing rather than a wrong label.\n\n"
            "I grouped 1,975 historical readouts into eight families, on disease, design, stage and "
            "sponsor, to find comparables.\n\n"
            "I modelled the three-day abnormal return from trial, text and company features; it "
            "explains twenty per cent of the variation.\n\n"
            "Then I applied that to our three readouts, three scenarios each, with a monitoring plan."
        ),
    )

    # ---- 3. the verdict --------------------------------------------------
    s = add_slide(prs)
    video_panel(s)
    tf = textbox(s, TXT_L, Inches(0.75), TXT_W, Inches(1.5))
    para(tf, "MY OPINION", 12, MUTED, bold=True, first=True, space_after=6)
    para(tf, "Rely on it to inform —\nnot to produce a number", 30, ACCENT,
         bold=True, font=HEAD_FONT, space_after=0, line_spacing=1.0)
    rule(s, Inches(2.32))
    tf = textbox(s, TXT_L, Inches(2.62), TXT_W, Inches(4.0))
    para(tf, "Strong on the downside.", 21, INK, bold=True, first=True, space_after=4)
    para(tf, "R² = 0.31 within negative readouts", 15, MUTED, space_after=16)
    para(tf, "Weak on the upside.", 21, FLAG, bold=True, space_after=4)
    para(tf, "R² = 0.03 within positive readouts — use history, not the model",
         15, MUTED, space_after=16)
    para(tf, "Not a forecast, a ranking.", 21, INK, bold=True, space_after=4)
    para(tf, "Typical error on a single event is about 21 percentage points",
         15, MUTED, space_after=0)
    s.notes_slide.notes_text_frame.text = (
        "No script of its own — this frame carries the verdict while you move from what you "
        "built into the evidence for it. Land on it as you say 'so, three things I'd stand "
        "behind', then advance."
    )

    # ---- 4. what it supports --------------------------------------------
    content_slide(
        prs,
        kicker="what the analysis supports",
        heading="Three things I'd\nstand behind",
        blocks=[
            ("The ordering is reliable.",
             "Negative vs positive separated by 11–27 points of central estimate, "
             "for all three assets, and it survives every seed."),
            ("ASC-204's downside is well evidenced.",
             "266-trial cardiovascular and renal cluster · 246 in the same therapeutic "
             "area · 34 negative readouts behind the distribution."),
            ("It ranks severity.",
             "Worst-ranked decile: 61% fell more than 10%, 43% more than 25%. "
             "AUC 0.78 for a fall beyond 25%."),
        ],
        notes=(
            "[1:02 — ~45s]\n\n"
            "So, three things I'd stand behind.\n\n"
            "The ordering. For all three assets a negative readout is materially worse than a "
            "positive one, by eleven to twenty-seven points of central estimate, and that "
            "survives every seed.\n\n"
            "The downside for ASC-204. It sits in a cluster of 266 cardiovascular and renal "
            "outcome trials, 246 in the same therapeutic area, with 34 negative readouts behind "
            "it. That's the estimate I'd let the funding decision rest on.\n\n"
            "[CUT IF LONG] And severity ranking: 61 per cent of the announcements in the model's "
            "worst decile fell more than ten per cent. It sorts readouts into 'could be severe' "
            "and 'probably won't be', not into a number."
        ),
    )

    # ---- 5. where it should not be relied on -----------------------------
    content_slide(
        prs,
        kicker="where it should not be relied upon",
        heading="Three limits,\nand they are real",
        blocks=[
            ("ASC-101 has effectively no comparables.",
             "7 hereditary angioedema readouts in the whole dataset. Matched to vaccine "
             "trials on design because disease was unmatchable — a Phase 3 base rate, "
             "and it must be labelled as one."),
            ("The upside is close to unmodelled.",
             "R² ≈ 0.03 within positives, ~0 with the features Asclepius can supply. "
             "Quote the comparable-set range instead."),
            ("The dataset supplies no price series for ASCL.",
             "A gap in the data, not a fact about the company. Volatility did most of the work "
             "in sizing a bad outcome, so bands are ~69 points wide — correctly wide."),
        ],
        notes=(
            "[1:47 — ~52s]\n\n"
            "Now the limits, and they're real.\n\n"
            "ASC-101 has effectively no comparables. The dataset holds seven hereditary "
            "angioedema readouts in total, so my method matched it to vaccine trials on design, "
            "having nothing to match on disease. That number is a Phase 3 base rate wearing a "
            "comparable set's clothes.\n\n"
            "The upside is close to unmodelled — three per cent of the spread within positive "
            "readouts, and effectively nothing with the features Asclepius can supply. For an "
            "upside case, quote the historical range.\n\n"
            "And the dataset supplies no price series for Asclepius — a gap in the data, not a "
            "fact about the company. Volatility is most of what let the model size a bad outcome, "
            "so the bands are about 69 points wide, and correctly so."
        ),
        accent=FLAG,
    )

    # ---- 6. how the work was produced ------------------------------------
    content_slide(
        prs,
        kicker="how the work was produced",
        heading="AI throughout —\njudgement not delegated",
        blocks=[
            ("Claude, via Claude Code, heavily and throughout.",
             "Code written and debugged, result sentences pulled from the filings for me "
             "to read, commentary drafted and then rewritten. Full logs submitted."),
            ("The constraints were mine.",
             "No feature unobservable before the event. Announcement drafts excluded as "
             "circular. The 30 filings read against the 8-Ks are my reading."),
            ("And I corrected it.",
             "It called all three mixed scenarios mixed-positive. ASC-204's misses its "
             "primary endpoint and is rescued by a subgroup — that is mixed-negative."),
        ],
        notes=(
            "[2:39 — ~47s]\n\n"
            "I used Claude, through Claude Code, heavily and throughout — to write and debug the "
            "code, to surface result sentences from the filings for me to read, and to draft "
            "commentary I rewrote. The full conversations are in the submitted log.\n\n"
            "What I didn't delegate was the judgement. I set the constraints: no feature "
            "unobservable before the event, and the announcement drafts excluded entirely, "
            "because they were written to express the assumed outcome. The thirty filings are my "
            "reading, not its summary.\n\n"
            "And I corrected it. It mapped all three mixed scenarios to mixed-positive; I read the "
            "ASC-204 draft, saw a missed primary endpoint rescued by a subgroup, and moved it to "
            "mixed-negative.\n\n"
            "(If asked for more: it hard-coded a cluster by number, which breaks because k-means "
            "relabels on refit; and its first ablation conflated losing the text with losing the "
            "price history, so I had it split the comparison.)"
        ),
    )

    # ---- 7. how I checked it ---------------------------------------------
    content_slide(
        prs,
        kicker="how I satisfied myself it is sound",
        heading="What I examined,\nand what it changed",
        blocks=[
            ("Leakage audit before anything was fitted.",
             "R² 0.20 → 0.96 with the nine excluded columns put back."),
            ("My own quality index was leaking.",
             "+0.14 R², traced to one signal built from the realised return — the leakage "
             "that survives review, because the name gives nothing away."),
            ("Validated against honest nulls.",
             "Permuted features · bootstrap by filing, not by row · forward chaining takes "
             "R² from 0.20 to 0.17 — what the pipeline can deliver."),
            ("I corrected my own earlier claim.",
             "I had told the team the range width was mainly the unknown result. "
             "It is about a quarter."),
        ],
        lead_pt=18, body_pt=14, gap_pt=12,
        notes=(
            "[3:26 — ~45s]\n\n"
            "On checking. I ran a leakage audit before fitting anything: with the nine excluded "
            "columns put back, R-squared goes from 0.20 to 0.96. The one that mattered was my own "
            "data-quality index — worth 0.14, until I traced it to one signal built from the "
            "realised return. That's the leakage that survives review; the name gives nothing "
            "away.\n\n"
            "[CUT IF LONG] I validated against honest nulls — permuted features, bootstrap by "
            "filing rather than by row, and forward chaining, which drops R-squared to 0.17. "
            "That's what the pipeline can deliver.\n\n"
            "And I corrected my own claims: I'd told the team the range width was mainly the "
            "unknown result. It's about a quarter."
        ),
    )

    # ---- 8. PG1 and close -------------------------------------------------
    s = add_slide(prs)
    video_panel(s)
    tf = textbox(s, TXT_L, Inches(0.75), TXT_W, Inches(1.5))
    para(tf, "MY RESPONSIBILITY UNDER PG1", 12, MUTED, bold=True, first=True, space_after=6)
    para(tf, "Mine regardless of\nwhat drafted it first", 30, ACCENT, bold=True,
         font=HEAD_FONT, space_after=0, line_spacing=1.0)
    rule(s, Inches(2.32))
    tf = textbox(s, TXT_L, Inches(2.62), TXT_W, Inches(4.0))
    para(tf, "Understand the model before relying on it. Judge whether its assumptions "
             "and methodology suit the purpose at hand.", 18, INK, first=True,
         space_after=22, line_spacing=1.15)
    para(tf, "IF YOUR TIME IS LIMITED, REVIEW", 12, MUTED, bold=True, space_after=8)
    para(tf, "1.  My decision to exclude the announcement drafts from the estimates.",
         17, INK, space_after=8, line_spacing=1.15)
    para(tf, "2.  Whether the ASC-101 estimate should go in front of the board at all.",
         17, INK, space_after=0, line_spacing=1.15)
    s.notes_slide.notes_text_frame.text = (
        "[4:11 — ~29s]\n\n"
        "Under PG1 I'm responsible for the judgements here regardless of what produced the first "
        "draft of them — which means understanding the model before relying on it, and judging "
        "whether its assumptions suit the purpose.\n\n"
        "If your time is limited, I'd put it on two things: my decision to exclude the "
        "announcement drafts, and whether the ASC-101 estimate should go in front of the board at "
        "all. Thank you.\n\n"
        "END — target 4:40, limit 5:00."
    )

    prs.save("Q5_handover_deck.pptx")
    print("wrote Q5_handover_deck.pptx — %d slides" % len(prs.slides._sldIdLst))


if __name__ == "__main__":
    main()
