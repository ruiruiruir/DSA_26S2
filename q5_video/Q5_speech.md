# Question 5 — video handover script

**Target length:** 675 words — about **4:40** at a measured 145 words per minute. The limit is 3–5
minutes and markers stop watching at 5:00, so time a practice run: if it comes out **over 4:30**,
drop the two passages marked *[cut if long]*, which bring it to 611 words, about **4:15**. Do not
speed the recording up to fit.

**Rubric warning:** one of the hurdles is *"does not appear to be reading word for word from a
script."* Use this to learn the argument and the numbers, then present from the cue cards at the end
of this file. Say it in your own words on the day; if a sentence comes out differently, that is fine
and is what the marker is looking for.

**Before you record:** everything below must be true of *your* involvement. Where a line describes a
judgement you made, make sure you did make it, and change it if you did not. The account in the
video, the notebook and the AI logs have to tell one story.

---

## The script

**[0:00 — Opening, ~19s]**

Hello. I'm handing over the analysis behind the IR team's estimates of how the market will react to
our three upcoming readouts. A quick summary is it's fit to inform those estimates, but not to produce a
headline number, and it's far stronger on the downside than the upside.

**[0:19 — What I built, ~43s]**

There are four stages for you to review, and I will go through each of the steps that I have done.
Then we can move onto the findings, limitations and validations that I performed on my own work.

I validated the LLM's outcome labels which I took a stratified thirty filings read by hand against the original 8-Ks, then
all directional labels checked against the price move that followed. That gave a screen scoring
all the classifications, which flags forty per cent, mostly for timing rather than a wrong label.

I grouped the historical readouts into eight families, on disease, design, stage and sponsor, to
find comparables. This was a clustering exercise and to check for our firms handouts. 

I modelled the three-day abnormal return from trial, text and company features. It explains twenty
per cent of the variation. The models that were used are random forest, GBM and ridge regression.

Then I applied that to our three readouts, three scenarios each, with a monitoring plan.

**[1:02 — What it supports, ~45s]**

So, three things I have come to conclusion from the analysis.

The ordering is sensible. For all three assets a negative readout is materially worse than a positive one, by
eleven to twenty-seven points of central estimate, and that survives every seed.

The downside for ASC-204 can be relied on. It sits in a cluster of 266 cardiovascular and renal outcome trials, 246 in
the same therapeutic area, with 34 negative readouts behind it. That's the estimate I'd let the
funding decision rest on.

*[cut if long]* And severity ranking can also be relied on. 61 per cent of the announcements in the model's worst decile
fell more than ten per cent. It sorts readouts into "could be severe" and "probably won't be", not
into a number.

**[1:47 — Where it should not be relied on, ~52s]**

Now the limitations. 

ASC-101 has effectively no comparables. The dataset holds seven hereditary angioedema readouts in
total, so my method matched it to vaccine trials on design, having nothing to match on disease. That
number is a Phase 3 base rate wearing a comparable set's clothes.

The upside is close to unmodelled as there is only three per cent of the spread within positive readouts, and
effectively nothing with the features Asclepius can supply. For an upside case, quote the historical
range.

And the dataset supplies no price series for Asclepius which is a gap in the data, but normally is required
for analysis. Volatility is most of what let the model size a bad outcome, so the bands are about 69
points wide, and correctly so.

**[2:39 — How the work was produced, ~47s]**

I used Claude, through Claude Code, heavily and throughout — to write and debug the code, to surface
result sentences from the filings for me to read, and to draft commentary I rewrote. The full
conversations are in the submitted log.

What I didn't delegate was the judgement. I set the constraints: no feature unobservable before the
event, and the announcement drafts excluded entirely, because they were written to express the
assumed outcome. The thirty filings are my reading, not its summary. I made some calls on whether it 
should be mixed positive or negative. Also there were models and parameters which I decided to run 
extra analysis on check if it was tuned properly.

**[3:26 — How I satisfied myself it's sound, ~45s]**

On checking. I ran a leakage audit before fitting anything: with the nine excluded columns put back,
R-squared goes from 0.20 to 0.96. Also tested various hyper parameters rather than just taking AI outputs.

*[cut if long]* I validated against honest nulls — permuted features, bootstrap by filing rather than
by row, and forward chaining, which drops R-squared to 0.17. That's what the pipeline can deliver.

I validated each cell manually and read the code to ensure what was generated by claude made sense,
the commentary had also been reviewed and validated before this handover with you.

**[4:11 — PG1 and close, ~29s]**

Under PG1 I'm responsible for the judgements here regardless of what produced the first draft of
them — which means understanding the model before relying on it, and judging whether its assumptions
suit the purpose. However, for your review purpose the code is stored in GitHUB with commentary and
methodology documents.

If your time is limited, I'd put it on two things: my decision to exclude the announcement drafts,
and whether the ASC-101 estimate should go in front of the board at all, as those are two key results that can change 
if you think the method is meant to be different. Otherwise feel free to call me for any questions when you're reviewing.
Thank you.

---

## Cue cards (present from these, not from the script)

**1. Opening**
- Handover: estimates of market reaction to three readouts
- Verdict: fit to *inform*, not to produce a headline number; strong downside, weak upside

**2. What I built — four stages**
- Validated the labels — 30 filings read by hand, 2,392 directional labels vs the realised move;
  screen over all 4,539 classifications flags 40%, mostly timing not wrong labels
- Grouped 1,975 readouts into 8 families (disease, design, stage, sponsor) → comparables
- Modelled the 3-day abnormal return (trial + text + company) → explains 20%
- Applied it to the three readouts, 3 scenarios each, plus a monitoring plan

**3. What it supports**
- Ordering — negative vs positive, 11–27 pts, survives every seed
- ASC-204 — 266-trial cluster, 246 same area, 34 negative readouts → lean on this one
- Ranking severity — worst decile: 61% fell >10%, 43% fell >25%

**4. Where it should not be relied on**
- ASC-101 — 7 HAE readouts in the whole dataset; matched to vaccines on design, not disease
- Upside — R² ≈ 0.03 within positives, ~0 with available features → quote history instead
- No ASCL price series in the dataset → bands ~69 pts wide, and correctly so

**5. How it was produced**
- Claude / Claude Code, heavily, throughout — code, excerpts, draft commentary. Logs submitted.
- Mine: the constraints (no look-ahead features; drafts excluded as circular), the 30 filings read
- Corrected it: mixed-scenario mapping (ASC-204 → mixed-negative); hard-coded cluster number;
  split the ablation

**6. How I checked it**
- Leakage audit: 0.20 → 0.96 with the excluded columns back in
- My own risk index leaked +0.14 — traced to one signal built from the realised return
- Honest nulls: permuted features, bootstrap by filing, forward chaining 0.20 → 0.17
- Corrected my own Q3d claim on what drives the range width

**7. PG1 and close**
- Responsible for the judgements regardless of what drafted them first
- Two things to review: excluding the drafts; whether ASC-101 goes in front of the board at all

---

## Delivery notes

- Upper-body shot, camera at eye level, look at the lens not the screen.
- Say the numbers slowly — they are the evidence the rubric rewards, and they are the easiest thing
  to lose to a rushed delivery.
- Pause between the seven sections; those pauses are the transitions the video guidance asks for.
- Practise once with a timer, then check against the two *[cut if long]* passages. Dropping both
  takes about 25 seconds out without losing a rubric point: each of the three required topics still
  has its own section and its own evidence.
- The "what I built" section is orientation, not the answer — keep it moving. The reviewer has not
  seen the work, but the marks are in the three sections after it.
- If you run *short* (under 3:30), the safest thing to add back is ASC-370: its cluster average is
  unusable — 15 same-area trials out of 388, and that group under-reports failure — but its nearest
  neighbours are genuine gene-therapy readouts, so read it case by case.
