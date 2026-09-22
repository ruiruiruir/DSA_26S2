# Question 5 — video handover script

**Target length:** 660 words — about **4:30** at a measured 145 words per minute (4:15 if you speak
briskly, 4:50 if you are slow and deliberate). The limit is 3–5 minutes and markers stop watching at
5:00, so time a practice run: if it comes out over **4:40**, drop the two passages marked
*[cut if long]* below, which take it to roughly 4:00. Do not speed the recording up to fit.

**Rubric warning:** one of the hurdles is *"does not appear to be reading word for word from a
script."* Use this to learn the argument and the numbers, then present from the cue cards at the end
of this file. Say it in your own words on the day; if a sentence comes out differently, that is fine
and is what the marker is looking for.

**Before you record:** everything below must be true of *your* involvement. Where a line describes a
judgement you made, make sure you did make it, and change it if you did not. The account in the
video, the notebook and the AI logs have to tell one story.

---

## The script

**[0:00 — Opening, ~28s]**

Hello. I'm handing over the analysis behind the IR team's estimates of how the market will react to
our three upcoming readouts. My position: it's fit to inform those estimates, but not to produce a
headline number, and it's far stronger on the downside than the upside. I'll cover what it supports,
where it shouldn't be relied on, how it was produced, and how I checked it.

**[0:28 — What the analysis supports, ~53s]**

Three things I'd stand behind.

First, the ordering. For all three assets a negative readout is materially worse than a positive one,
by fifteen to twenty-five points of central estimate, and that survives every seed I ran.

Second, the downside for ASC-204. It sits in a cluster of 274 cardiovascular and renal outcome
trials, 247 in the same therapeutic area, with 39 negative readouts behind the distribution. That's
the estimate I'd let the funding decision rest on.

*[cut if long]* Third, ranking severity. Of the announcements the model puts in its worst decile, 60 per cent fell
more than ten per cent and 43 per cent fell more than twenty-five. It sorts readouts into "could be
severe" and "probably won't be". It won't tell you a stock moves fourteen per cent.

**[1:21 — Where it should not be relied on, ~57s]**

Now the limits, and they're real.

ASC-101 has effectively no comparables. The dataset holds seven hereditary angioedema readouts in
total, so my method matched it on design, to vaccine trials, because it couldn't match on disease.
That number is a Phase 3 base rate wearing a comparable set's clothes, and should be presented that
way.

The upside is close to unmodelled. Within positive readouts the model explains about five per cent of
the spread, and effectively nothing once I'm limited to what Asclepius can supply. For an upside
case, quote the historical range, not a model output.

And Asclepius has no price history in this database. Volatility is most of what let the model size a
bad outcome, so the bands are wide — about 68 points. That width is correct, not a gap more modelling
closes.

**[2:17 — How the work was produced, ~52s]**

I used Claude, through Claude Code, heavily and throughout — to write and debug the code, to pull
result sentences out of the filings so I could read them, and to draft commentary I then rewrote. The
full conversations are in the submitted log.

What I didn't delegate was the judgement. I set the constraints: no feature that wasn't observable
before the event, and the illustrative announcement drafts excluded entirely, because they were
written to express the assumed outcome. The thirty filings I read against the original 8-Ks are my
reading, not its summary.

And I corrected it. It mapped all three mixed scenarios to mixed-positive; I read the ASC-204 draft,
saw a missed primary endpoint rescued by a subgroup, and moved it to mixed-negative.

**[3:09 — How I satisfied myself it's sound, ~53s]**

On checking, three things I'd point you at.

I ran a leakage audit before fitting anything. With the nine excluded columns put back, R-squared goes
from 0.21 to 0.96. The one that mattered was my own data-quality index — it lifted R-squared by
0.086, until I traced it to one signal built from the realised return. That's the leakage that
survives review: it looks legitimate, and the name gives nothing away.

*[cut if long]* I validated against honest nulls — permuted features for the clustering, bootstrap by filing rather
than by row, and forward chaining, which drops R-squared from 0.20 to 0.16. That's what the pipeline
can deliver.

And I corrected my own claims: I'd told the team the range width was mainly not knowing the result.
It's about a quarter.

**[4:02 — PG1 and close, ~31s]**

Under PG1 I'm responsible for the judgements here regardless of what produced the first draft of
them — which means understanding the model before relying on it, and judging whether its assumptions
suit the purpose. That's what I've tried to do.

If your time is limited, I'd put it on two things: my decision to exclude the announcement drafts,
and whether the ASC-101 estimate should go in front of the board at all. Thank you.

---

## Cue cards (present from these, not from the script)

**1. Opening**
- Handover: estimates of market reaction to three readouts
- Verdict: fit to *inform*, not to produce a headline number; strong downside, weak upside

**2. What it supports**
- Ordering — negative vs positive, 15–25 pts, survives every seed
- ASC-204 — 274-trial cluster, 247 same area, 39 negative readouts → lean on this one
- Ranking severity — worst decile: 60% fell >10%, 43% fell >25%

**3. Where it should not be relied on**
- ASC-101 — 7 HAE readouts in the whole dataset; matched to vaccines on design, not disease
- Upside — R² ≈ 0.05 within positives, ~0 with available features → quote history instead
- No ASCL price history → bands ~68 pts wide, and correctly so

**4. How it was produced**
- Claude / Claude Code, heavily, throughout — code, excerpts, draft commentary. Logs submitted.
- Mine: the constraints (no look-ahead features; drafts excluded as circular), the 30 filings read
- Corrected it: mixed-scenario mapping (ASC-204 → mixed-negative); hard-coded cluster number;
  split the ablation

**5. How I checked it**
- Leakage audit: 0.21 → 0.96 with the excluded columns back in
- My own risk index leaked +0.086 — traced to one signal built from the realised return
- Honest nulls: permuted features, bootstrap by filing, forward chaining 0.20 → 0.16
- Corrected my own Q3d claim on what drives the range width

**6. PG1 and close**
- Responsible for the judgements regardless of what drafted them first
- Two things to review: excluding the drafts; whether ASC-101 goes in front of the board at all

---

## Delivery notes

- Upper-body shot, camera at eye level, look at the lens not the screen.
- Say the numbers slowly — they are the evidence the rubric rewards, and they are the easiest thing
  to lose to a rushed delivery.
- Pause between the six sections; those pauses are the transitions the video guidance asks for.
- Practise once with a timer, then check against the two *[cut if long]* passages. Dropping both
  takes roughly 30 seconds out without losing a rubric point: each of the three required topics
  still has its own section and its own evidence.
- If you run *short* (under 3:30), the safest thing to add back is ASC-370: its cluster average is
  unusable — 15 same-area trials out of 388, and that group under-reports failure — but its nearest
  neighbours are genuine gene-therapy readouts, so read it case by case.
