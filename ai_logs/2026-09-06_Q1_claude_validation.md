# Claude Code session transcript

_Question 1 validation session. Exported from the Claude Code session log; tool calls are summarised by name and description rather than reproduced in full._

## You  _04:14_

I am about to start to validate your work so I would need some assistance in explaining what is done

## Claude  _04:14_

I'll look at what's on your branch and summarize the work.

<details><summary>tools run</summary>

- `Bash: Inspect branches, status, and recent history`
- `Bash: List repo contents and commit stats`
- `Bash: List notebook cells overview`
- `Bash: Dump Question 4 section`
- `Bash: Check summary and AI-use cells`
- `Bash: Check notebook execution state and supporting files`
- `Bash: Show code cell header comments`
- `Bash: Extract key numeric outputs`
- `Bash: Word-count the 500-word summaries`

</details>

## Claude  _04:15_

Here's a walkthrough of what's on `rz_working` so you can validate it.

## State of the repo

Branch is clean and in sync with `origin/rz_working`. The work lives entirely in `DSA_2026_S2_Assignment_template.ipynb` — 130 cells, 53 code cells, all executed in order 1→53 with **no error outputs**, so a top-to-bottom re-run is a fair check.

**Questions 1, 2 and 3 are complete. Question 4 and Question 5 are untouched template.**

## Q1 — Validate and improve the dataset (21 marks)

- **Q1a** runs two independent evaluations. First, a stratified hand-read of 30 classifications (5 from each of the six documented categories), where relevant sentences are pulled from the 20k–90k-character filings rather than printing them whole. Second, a whole-dataset comparison of every directional label against the sign of the abnormal return (2,392 filings).
- The headline finding is that the labels are *accurate but mistimed*: 24/30 labels fairly described the filing, but only 6/30 filings were the announcement that broke the news — the rest are quarterly reports and investor decks restating old results next to a price move driven by earnings. That distinction drives everything downstream.
- A `classify_filing()` helper (announcement vs. not) was built for this and validated at 28/30 against the hand-read sample.
- **Q1b** turns each Q1a failure mode into a scored rule; at `risk_score >= 3` it flags 2,015 of 4,539 classifications (44.4%). The per-category table is the thing to eyeball — undocumented compound categories like `positive/negative` flag at 100%, `no_result` at 13%. The queue is then ranked by analyst value, not just doubt.
- **Q1c** cleans text and structured fields, explicitly lists columns that can't be used because they aren't observable before the reaction, then vectorises with sentence embeddings — and tests the vectorisation rather than assuming it. Worth noting: **that test is reported honestly as a partial failure**. Embeddings reach AUC 0.709 on recovering outcome sign, TF-IDF on the same sentences reaches 0.802. Both are carried forward for different uses.
- **Q1d** summary is 496 words.

## Q2 — Comparable trials (20 marks)

- An eligibility rule restricts clustering to rows with populated design fields — and cell 42 *demonstrates why* by showing that if you skip it and impute, k=2 reproduces the missingness indicator at ARI 0.98. The strongest structure in the naive data is the registry linkage failing.
- Eight clusters over combined text components + structured trial characteristics. Sizes and profiles are in cell 51 (e.g. cluster 2 = 330 registrational oncology trials, median enrolment 518; cluster 6 = 261 cardio/metabolic).
- **The silhouette is ~0.06**, and cell 49 confronts that directly against three null references rather than glossing it.
- **Q2c runs six validation checks**, and check 4 is the one to look at: cluster 5 is identified as *a filing type, not a trial type* (quarterly reports), and is recommended for exclusion from Q4. Check 2 finds cluster membership explains only **0.28%** of CAR variance; check 5 gives bootstrap ARI 0.52; check 6 confirms the three Asclepius readouts land in stable clusters across scenarios.
- **Q2d** is 492 words.

## Q3 — Magnitude prediction (27 marks)

- Three feature groups (trial/outcome, text ×3 representations, company/market context), with all price-derived features time-matched, and price *levels* deliberately excluded — the stored `close` series is split-back-adjusted, which had produced a maximum beta of 26,589 before it was caught.
- Evaluation groups by filing accession so whole announcements are held out; every learned step sits inside the CV pipeline.
- Headline (cell 92): random forest **R² = 0.204**, gradient boosting 0.173, ridge 0.101, against an outcome-group-mean baseline of 0.093. So the modelling roughly doubles what knowing good/bad news gives you free. A walk-forward variant gives 0.16.
- Nine held-back columns are added one at a time to *demonstrate* leakage rather than assert it.
- **Q3c** is the strongest result: performance computed within outcome group shows **negative readouts at R² = 0.31 and Spearman 0.55, positive readouts at 0.04**. Crashes are predictable; rallies are not. The gap is bootstrapped and tested against two confounds.
- **Q3d** is 500 words exactly — at the limit, so re-check with the marker's `word_count()` before submitting.

## What is still outstanding

1. **Q4 (17 marks)** — all five parts of Q4a, plus Q4b and Q4c, are still `_Your answer:_` placeholders with empty code cells. Note that Q2 and Q3 were built to feed this: cluster 5 exclusion and the asymmetry result are the inputs.
2. **Q5 (15 marks)** — video not recorded; `[INSERT YOUTUBE URL HERE]` is still at the bottom of the notebook.
3. **AI-use disclosures for Q1–Q3 are drafts, not submissions.** Each carries an explicit "TO COMPLETE BEFORE SUBMISSION — rewrite in your own words" banner. They currently name the model and list the specific points where its first output was wrong. Read them against your own recollection and cut anything that doesn't match your involvement.
4. **`ai_logs/` holds one file** (`2026-09-02_general_claude_setup.md`). The Q1/Q2/Q3 sessions aren't logged there, and `compile_ai_logs.py` hasn't been run to produce `AI_LOGS.md`.
5. **`DSA_2026_S2_Assignment_template.ipynb.bak`** (9,072 lines) is committed to the repo. Probably worth deleting before submission.

Want me to start on Q4, or would you rather validate Q1–Q3 first?

## You  _04:17_

can you explain to me what cell 7 is doing, the two helper functions

<details><summary>tools run</summary>

- `Bash: Print the helper-functions cell source`
- `Bash: Show the helper cell's outputs`
- `Bash: Find downstream uses and the validation output`

</details>

## Claude  _04:17_

That's the second code cell in Q1 (index 6 zero-based, cell 7 if you're counting from 1). It defines the two text helpers that everything else in Question 1 depends on, then applies them to all 3,794 filings.

## `clean_filing_text(t)`

Takes raw `filing_text` from the database and strips the parts that are identical across every 8-K and say nothing about the trial. Four passes, in order:

1. **Mojibake repair** — the `MOJIBAKE` dict maps the character damage left by whatever extracted the text: smart quotes → straight quotes, en/em dashes and the Unicode minus → hyphen, bullet glyphs (`▪ ● • · Ÿ ☐ ☒`) and the replacement char → space. This runs first because the regexes below have to match against repaired text.
2. **Boilerplate removal** — four compiled regexes, each anchored to a structural landmark rather than a keyword:
   - `RE_COVER` — the SEC cover page, from "Check the appropriate box below" through the `13e-4(c))` terminator, capped at the first 6,000 chars (`count=1` so it only ever fires once).
   - `RE_SAFE` — the forward-looking-statements / safe-harbour block. Note the lookahead: it stops at the *next* structural marker (`Item N`, `EX-`, `Exhibit N`, `SIGNATURE`, `About [Company]`, `Contacts:`, `###`) rather than eating a fixed length, so it doesn't swallow real content when the disclaimer is short.
   - `RE_EXIDX` — the Item 9.01 exhibit index.
   - `RE_TAIL` — everything from the signature page to the end.
3. **Slide-deck hyphens** — `\b([A-Za-z]{2,})\s+-\s+([A-Za-z]{2,})\b` → `\1-\2`. Presentation exports render "well-tolerated" as "well - tolerated"; without this, the token is destroyed for both TF-IDF and the embeddings.
4. **URLs out, whitespace collapsed.**

The `{2,}` guard on the hyphen rule is deliberate — it stops it from joining across things like "A - 1" or a dash used as punctuation between initials.

**Result: 43.7% of all characters removed; median filing 19,186 → 7,986 chars.** That number is your first sanity check — if it re-runs much higher, a regex is over-matching and eating substance.

## `classify_filing(clean_text, raw_text, head=1200, body=6000)`

Returns a tuple: `(document kind, count of backward references)`.

**The kind.** Three headline patterns — `RE_FIN` (quarterly/annual financial results, Item 2.02), `RE_RES` (topline / primary endpoint / pivotal / Phase N results), `RE_DECK` (investor presentation, Item 7.01, Reg FD) — evaluated with a specific precedence:

```
res and not fin              → results announcement   # headline only
fin or RE_FIN in body        → periodic report
RE_DECK in body              → deck / FD update
RE_RES in body               → results announcement
otherwise                    → other
```

Two design choices are load-bearing here, and both are documented in the docstring as fixes to a version that was wrong:

- **A trial-results headline beats a financial one.** A company announcing topline data routinely mentions an upcoming quarter in the same release, which would otherwise misfile it.
- **The headline (first 1,200 chars) is checked before the body (first 6,000).** The failure this fixes was real: guidance language like *"we expect to report top-line results in late fourth quarter 2021"* in the body was reading a genuine Theravance topline announcement as a quarterly report.

**The second return value, `n_prior_refs`,** counts matches of `RE_PRIOR` — "previously announced/reported/disclosed", "as announced", "in [Month] 20XX, the Company announced", "earlier this year". Note it runs on `raw_text`, not the cleaned text, so removed boilerplate can't cost you a match. This is the quantitative handle on the recap problem: a filing restating a result disclosed months ago carries backward references that a genuine first disclosure does not.

## Why this cell matters to the rest of Q1

The whole Q1a finding rests on it. Cell 10 validates the classifier against the 30 hand-read filings — **23/30 exact, 28/30 on the announcement-vs-not split** that actually matters — and the payoff line is right there: *only 6 of the 30 sampled filings are the announcement that carried the news.* `filing_kind` and `n_prior_refs` then feed the disagreement analysis (cells 16–17), the Q1b flagging rules and review-queue ranking (21, 23), the Q2c cluster-5 diagnosis (67), and a Q3a feature (83). `clean_filing_text` also feeds Q1c vectorisation (26).

## Where to push on it, if you're validating

- The seven disagreements in cell 10 are all deck-vs-periodic-report confusions on the *same handful of tickers* (TNXP ×3, TBPH ×2). None of them cross the announcement/not-announcement line, which is why the 28/30 figure is the one quoted — but it's a fair question whether that error is systematic per-filer rather than random.
- **738 filings land in `other`** (out of 3,794). That bucket is unexamined in this cell; if a marker asks what's in it, there isn't an answer here.
- `head=1200` and `body=6000` are unjustified constants. They work, but nothing in the notebook tests sensitivity to them.

## You  _04:26_

So where can I read the filings of each of my samples

<details><summary>tools run</summary>

- `Bash: Print Q1 setup and sampling cells`
- `Bash: Print setup and excerpt cells; check DB files`

</details>

## Claude  _04:26_

Three places, in increasing order of fidelity. Let me check what the database gives you first.

<details><summary>tools run</summary>

- `Bash: Extract DB and list table schemas`
- `Bash: Dump the 30 sampled filings to text files`
- `Bash: Install pandas`
- `Bash: Run the sample dump script`
- `Bash: Quantify over-cleaning across all filings`
- `Bash: Check gitignore and status`

</details>

## Claude  _04:28_

Three routes, and I've set up the most useful one for you.

## 1. Inside the notebook — the excerpts (fastest)

Cell 9 defines `show(i)`, which prints one sampled record's header (label, CAR, document kind, restatement count) plus the top-ranked result sentences. It currently only prints three representative cases — indices 6, 1 and 11. The line to read all thirty is already there, commented out at the bottom:

```python
# for i in range(0, 29): # show all 30 records in the stratified sample, for completeness
#     show(i)
```

Note that's `range(0, 29)` — it stops at 28 and **misses record 29** (VTGN, `no_result`). Should be `range(30)` if you uncomment it.

But `show()` gives you `result_sentences()` output: at most 10 sentences ranked by drug mention + result language. That's what the classification was judged against, not the filing.

## 2. The full text — I've written it out for you

`q1a_sample_filings/` in your working directory (untracked, and safe to delete). Thirty files, one per sampled record, named `NN_outcome_ticker_accession.txt`. Each one has a header block with the LLM's label, its `evidence` and `statistics` fields, the CAR, the document kind, and a blank `YOUR VERDICT` line — then the **cleaned** text, then the **raw** text as stored in `filing_text`. Plus `_index.csv` with the sample table.

The script that made it is at `scratchpad/dump_sample.py`; it copies the two helpers verbatim and redraws the sample with `random_state=40100`, so it reproduces the notebook's sample exactly. Confirmation that it did: the seven accessions in cell 10's disagreement table land at indices 10, 12, 14, 18, 20, 21 and 23, matching the notebook.

The raw text is a programmatic extraction of the 8-K, so it's flat and unformatted — but it's complete. Record 25 (ZVRA) is 209,130 characters.

## 3. The original filing on EDGAR

For the actual document with its formatting, exhibits and press release as filed. The database has no CIK column, so you can't build the Archives URL directly — search the accession number at [efts.sec.gov/LATEST/search-index?q=](https://www.sec.gov/edgar/search/) (EDGAR full-text search) or browse by ticker. Worth doing for two or three, particularly the boundary cases, since the raw text loses tables — and endpoint results are often *in* the tables.

## One thing the dump surfaced that you should look at

Compare the raw and clean character counts in the listing. Several filings lose almost everything:

| Record | Raw | Clean | Kept |
|---|---|---|---|
| 04 LPCN | 15,966 | 305 | 1.9% |
| 21 TCRT | 28,094 | 430 | 1.5% |
| 24 LCTX | 11,577 | 601 | 5.2% |
| 01 PFE | 35,415 | 1,023 | 2.9% |

Across all 3,794 filings: **median retention is 65%, but 531 filings (14%) keep under 5%, and 175 end up with under 500 characters.** That's `RE_SAFE` over-matching — its `.{0,12000}?` lookahead finds no terminator and eats the body. The 43.7% aggregate removal figure quoted in the notebook hides this, because it's a ratio of totals rather than a distribution.

It's worth checking whether those near-empty filings are ones where the label actually mattered. Open `04_positive_LPCN_...txt` and read the raw section against the 305-character clean section — that will tell you in a minute whether real result language was destroyed. If it was, it affects Q1c vectorisation and the Q3a text features, not just this sample.

Want me to trace which of the 30 hand-read records were affected, or check whether the over-cleaned filings are concentrated in any particular outcome category?

## You  _04:28_

Stop hook feedback:
[~/.claude/stop-hook-git-check.sh]: There are untracked files in the repository. Please commit and push these changes to the remote branch.

<details><summary>tools run</summary>

- `Bash: Check dump folder size`

</details>

## Claude  _04:29_

The untracked folder is the 1.5 MB of dumped filing text I just generated — derived data, not source. I'll commit the script that reproduces it and ignore the output, rather than checking 30 copies of text that's already in `ctgov.db` into your submission.

<details><summary>tools run</summary>

- `Bash: Add script to repo and ignore output folder`
- `Bash: Commit the script and gitignore update`
- `Bash: Push to rz_working`

</details>

## Claude  _04:29_

Pushed to `rz_working` (`e2eab79..8221fee`). Working tree is clean.

**What I committed:**
- `dump_q1a_sample_filings.py` — regenerates the 30-filing dump from `ctgov.db` on any machine, with the two text helpers copied verbatim so the sample and cleaning match what Q1 actually ran. Run it from the repo root.
- `.gitignore` — added `q1a_sample_filings/`.

**What I deliberately did not commit:** the 1.5 MB dump itself. It's fully derived from the provided database, so committing it would put 30 copies of filing text into your submission for no benefit. The script regenerates it in a few seconds.

One thing to be aware of: this is an ephemeral remote container, so `q1a_sample_filings/` will not survive the session. Re-run the script wherever you're actually reading the filings. If you'd rather have the files sent to you directly instead, say so and I'll send them.

The over-cleaning finding from my last message still stands and is unaddressed — 531 filings (14%) retain under 5% of their characters after `RE_SAFE` runs. That's the more consequential thing to look at than any of this plumbing.

## You  _04:31_

# for i in range(0, 29): # show all 30 records in the stratified sample, for completeness
#     show(i)

This line does it show the cleaned version or the original filing

## Claude  _04:31_

It shows the **cleaned** version — and not even all of it. Three reductions happen between the filing and what prints:

```
filing_text (raw)  →  clean_filing_text()  →  result_sentences()  →  top k=4
```

The chain in cell 9:

```python
clean_by_acc = filing_txt.set_index("accession")["clean"]   # ← the cleaned column

def show(i, k=4):
    ...
    for s in result_sentences(clean_by_acc.get(r.accession, ""), r.drug_name, k=k):
```

`result_sentences()` then splits that on sentence boundaries, drops anything under 40 or over 600 characters, scores each sentence on drug-name mention + result language, and returns the best ones. `show()` passes `k=4`, so you see **at most four sentences** — even though `result_sentences` defaults to 10.

The only thing in that output computed from the raw text is `n_prior_refs` in the header line.

Let me show you what that actually means for the over-cleaned records.

<details><summary>tools run</summary>

- `Bash: Show what show() prints for over-cleaned records`

</details>

## Claude  _04:32_

That's a real problem, and let me pin down which regex causes it rather than leave my earlier guess standing.

<details><summary>tools run</summary>

- `Bash: Trace which regex removes the bulk of each filing`

</details>

## Claude  _04:32_

I need to correct what I said earlier: I attributed the over-cleaning to `RE_SAFE`. That's wrong for most cases — **the main culprit is `RE_TAIL`**.

<details><summary>tools run</summary>

- `Bash: Attribute character removal to each cleaning rule`
- `Bash: Quantify RE_TAIL impact`

</details>

## Claude  _04:33_

Direct answer to your question: **the cleaned version**, and only the top 4 ranked sentences from it. The raw filing never appears in `show()` output.

That matters more than it sounds, because of what the trace above found.

## `RE_TAIL` is deleting the press release

```python
RE_TAIL = re.compile(r"(SIGNATURES?\s+Pursuant to the requirements of the Securities Exchange Act.*)$", re.S | re.I)
```

It matches the signature block and deletes **everything to the end of the document**. The assumption is that the signature page is the last thing in the filing. In an 8-K text extraction it usually isn't — the exhibits come *after* it. Exhibit 99.1 is where the press release lives, which is where the trial result is stated.

Per-rule attribution across all 3,794 filings:

| Rule | Share of all chars removed | Filings where it removes >50% |
|---|---|---|
| `RE_COVER` | 2.0% | 1 |
| `RE_SAFE` | 13.9% | 151 |
| `RE_EXIDX` | 0.3% | 0 |
| **`RE_TAIL`** | **27.2%** | **1,215** |

`RE_TAIL` fires in 1,458 filings (38%), removing a median of **11,987 characters** each. In 1,215 filings it takes more than half the document; in 105 it takes more than 90%.

So I had the diagnosis wrong last message — `RE_SAFE` is a secondary contributor (151 filings), `RE_TAIL` is the main one.

## What that does to your hand-read

Record 04, LPCN, labelled `positive`, 15,966 raw chars → 305 clean. Here is the entirety of what `show(4)` would have printed:

```
- Item 7.01 Regulation FD Disclosures The Company will be meeting with investors and
  presenting materials regarding the Company at the Ladenburg Thalmann 2016 Healthcare
  Conference to be held on September 27, 2016.
- The Company's materials to be used in the presentations are attached hereto as Exhibit 99.1.
```

Record 21 (TCRT, `inconclusive`) and record 24 (LCTX, `inconclusive`) look the same — a cover note pointing at an exhibit that has been deleted. There is nothing in that output to judge a classification against. The trial data for LPCN 1111 is in the 14,133 characters `RE_TAIL` removed.

This doesn't invalidate the Q1a conclusion — 24/30 labels fair, and only 6/30 being the news-breaking announcement both look robust, since most of the sample survived cleaning intact. But a marker who opens record 04 will ask what was actually read there.

## The fix

Anchor the deletion to the signature block itself rather than to end-of-document — stop at the next `EX-` / `Exhibit 99` marker, the same lookahead style `RE_SAFE` already uses:

```python
RE_TAIL = re.compile(
    r"SIGNATURES?\s+Pursuant to the requirements of the Securities Exchange Act"
    r".{0,3000}?(?=(?:EX-|Exhibit\s?99|Item \d|$))", re.S | re.I)
```

That's a one-line change, but it touches `clean` — which feeds Q1c vectorisation, the Q2 clustering text block and the Q3a text features. Everything downstream would need re-running, and some numbers will move.

Two options: I can patch it and re-run Q1–Q3 to see how much shifts, or leave the code as-is and write the limitation up honestly in Q1c (the notebook already takes that posture with the embeddings-vs-TF-IDF result). Re-running is the better answer if you have time before submission; the write-up is defensible if you don't. Which do you want?

## You  _04:35_

so can you explain to me what is the mistake, I am not sure if I get it

## Claude  _04:35_

Let me show you the actual document instead of describing it. Here's what the LPCN filing looks like from top to bottom.

<details><summary>tools run</summary>

- `Bash: Show document structure around signature block`

</details>

## Claude  _04:35_

Now the mistake should be visible.

## The structure of an 8-K

An 8-K filing has two parts glued together in one text file:

```
chars 0 – 1,750     the 8-K itself: cover page, "Item 7.01", a sentence saying
                    "our materials are attached hereto as Exhibit 99.1"
chars 1,750         SIGNATURES ... /s/ Mahesh V. Patel, President and CEO
chars 1,750 – 15,964   EX-99.1 ... the actual presentation
```

The 8-K body is a **cover note**. It says almost nothing — it just points at an attachment. The substance, the thing that reports the trial result, is Exhibit 99.1, and the exhibit is appended **after** the signature.

## What the rule assumes

```python
RE_TAIL = re.compile(r"(SIGNATURES?\s+Pursuant to the requirements of the Securities Exchange Act.*)$", re.S | re.I)
```

The `.*` with `re.S` means "everything from here on, newlines included", and `$` is end of string. So the rule says:

> *find the signature block, delete it and everything after it.*

That is only correct if the signature is the last thing in the document. The reasoning behind it is sound in principle — a signature page is boilerplate, it's the same in every filing, it tells you nothing about a trial. Worth removing. **But in an 8-K the signature is not at the end. It's in the middle**, sitting between the cover note and the exhibits.

## So what actually happens

The signature block starts at character 1,750 of 15,964. The rule deletes from there to the end — **14,214 characters, 89% of the filing**. What survives is the 1,750-character cover note, which after the other rules run leaves 305 characters: *"the Company will be meeting with investors... materials attached hereto as Exhibit 99.1."*

That's the whole of what `show(4)` had to print. The presentation containing the LPCN 1111 data was deleted.

It's the equivalent of throwing away an email's attachment because you decided the signature at the bottom of the covering message meant the message was over.

## Why it isn't obvious

Three reasons this slipped through:

1. **It fires on 38% of filings, not all of them.** When a company writes the result into the 8-K body itself, the exhibit is redundant and nothing important is lost. Those filings clean correctly. So spot-checking a few would likely have looked fine.
2. **The headline number hides it.** The notebook reports "cleaning removed 43.7% of all characters" — that's total chars removed ÷ total chars, pooled across all filings. A rule that removes 5% from most documents and 89% from 1,215 of them averages out to something that looks reasonable. The distribution is what shows the problem; the notebook never plots it.
3. **No output is empty.** Every filing still produces *some* text, so nothing crashes and nothing looks broken. It just quietly gets less informative.

## Scale

`RE_TAIL` fires in 1,458 of 3,794 filings. It removes over half the document in 1,215 of them and over 90% in 105. Across the whole corpus it accounts for 27.2% of all characters removed — more than the other three rules combined.

## The fix

Stop at the exhibit marker rather than running to end-of-document:

```python
RE_TAIL = re.compile(
    r"SIGNATURES?\s+Pursuant to the requirements of the Securities Exchange Act"
    r".{0,3000}?(?=(?:EX-|Exhibit\s?99|Item \d|$))", re.S | re.I)
```

The `(?=...)` lookahead stops the deletion at `EX-` or `Exhibit 99`, so the signature goes and the attachment stays. `RE_SAFE` already uses exactly this pattern — the bug is that `RE_TAIL` didn't.

Does that make sense now? If so, my earlier question stands: patch it and re-run Q1–Q3 to see what moves, or leave the code and document the limitation in Q1c.

## You  _04:36_

so its saying current our code stops at signature but we want to extend and read the exhibits too

## Claude  _04:36_

Yes — that's right on the effect. Two precisions worth having, because they change what the fix involves.

**1. The exhibit text is already there.** Nothing needs fetching or extending. `filing_text` in the database contains the full document, exhibits included — all 15,964 characters for LPCN. We already have it. The code deletes it. So the fix isn't "go and read more", it's "stop throwing away what we already read."

That matters if you're describing this in the write-up: "the extraction missed the exhibits" would be wrong and a marker could check it. "Our cleaning step discarded them" is what happened.

**2. We still want the signature block gone.** It's genuine boilerplate — a few hundred characters of *"the registrant has duly caused this report to be signed..."*, identical across every filing. Removing it was the right intention.

The bug is only in how far the deletion runs:

```
        cover note          SIGNATURES          Exhibit 99.1 (the press release)
        |-------------------|-------------------|--------------------------------|
now:    keep                 delete ------------------------------------------> end
want:   keep                 delete             keep
```

So: delete the signature block, then stop. Currently it deletes the signature block and everything that follows it to the end of the file, which on a filing where the substance is attached rather than inline means the substance goes with it.

That's what the lookahead `(?=(?:EX-|Exhibit\s?99|Item \d|$))` does — it tells the deletion where to stop, instead of letting `.*$` run to the end. The `$` alternative at the end of that list keeps the current behaviour for filings that genuinely do end at the signature.

Want me to make the change and re-run Q1–Q3 so we can see how much the numbers move?

## You  _04:37_

Okay can you change that and re-run it

## Claude  _04:37_

Let me check what a full re-run actually needs before I touch anything.

<details><summary>tools run</summary>

- `Bash: Check notebook imports and the embedding cell`

</details>

## Claude  _04:37_

Needs `sentence-transformers` plus the MiniLM model (no local `models/` dir, so it has to come from the hub). Let me patch first and validate the regex, then set up the environment.

<details><summary>tools run</summary>

- `Bash: Patch RE_TAIL in the notebook`
- `Bash: Validate new regex against old across corpus`

</details>

## Claude  _04:38_

The fix works — filings retaining under 5% drop from 526 to 7, and the rule still removes the signature block in 1,457 of the 1,458 filings where it fires. Now the environment.

<details><summary>tools run</summary>

- `Bash: Patch the dump script to match`
- `Bash: Install core scientific dependencies`
- `Bash: Test Hugging Face reachability`
- `Bash: Check agent proxy status and policy`
- `Bash: Check dependency install status`

</details>

## Claude  _04:38_

Core deps installed. Hugging Face is blocked by the environment's network policy, so the embedding model can't be fetched — that caps how far I can re-run. Let me run everything up to the embedding step and see what moves.

<details><summary>tools run</summary>

- `Bash: Re-run Q1 cells with the patched regex`
- `Bash: Extract key re-run outputs`
- `Bash: Compare old vs new outputs for remaining Q1 cells`
- `Bash: Compare drug-name-found rate and issue prevalence`
- `Bash: Probe for an allowed source of the embedding model`

</details>

## Claude  _04:40_

No route to the model weights from this environment. Let me confirm the effect on the sample dump, then commit.

<details><summary>tools run</summary>

- `Bash: Regenerate sample dump with fixed cleaning`
- `Bash: Commit and push the fix`

</details>

## Claude  _04:41_

Changed and pushed (`8221fee..f6c72c7`). The re-run is **partial** — I need to be clear about that up front.

## What I could re-run

Everything in Q1 up to the embedding step (cells 2–30). All executed cleanly.

| | Before | After |
|---|---|---|
| Characters removed by cleaning | 43.7% | **17.5%** |
| Median filing after cleaning | 7,986 | **13,905** |
| Filings keeping <5% of their text | 526 | **7** |
| Filings under 500 chars | 174 | **9** |
| `results announcement` | 861 | **1,078** |
| `other` | 738 | **502** |
| Classifier vs hand-read (exact) | 23/30 | 23/30 |
| Classifier vs hand-read (announcement/not) | 28/30 | 28/30 |
| "Only N of 30 carried the news" | 6 | 6 |
| Q1b flagged at `risk_score >= 3` | 2,015 (44.4%) | 2,019 (44.5%) |
| Label-vs-return analysis (cell 15) | — | byte-identical |

**Your Q1a and Q1b conclusions survive intact.** The two claims the write-up rests on — 28/30 on the announcement split, and only 6 of 30 being the news-breaking filing — don't move at all. Cell 15 is unchanged because it uses CAR and labels, not text. That's a good result for you: it means the finding wasn't an artefact of the bug.

The classifier genuinely improves. 217 filings move into `results announcement` and 236 leave `other`, because the recovered exhibit text now contains the results language the classifier was looking for and previously couldn't see.

In the sample dump, record 04 (LPCN) goes from 305 characters to 13,878. Record 21 (TCRT) from 430 to 25,789. Record 24 (LCTX) only reaches 845 — that one is `RE_SAFE`, a separate and much smaller issue (151 filings).

## What I could not re-run, and why

Q1c step 4 onward — the vectorisation, all of Q2, all of Q3.

Cell 31 loads `sentence-transformers/all-MiniLM-L6-v2`. There's no local `models/` directory, so it must come from the Hugging Face hub, and **this environment's network policy blocks huggingface.co** (403 at the proxy on CONNECT). I checked for an allowed alternative — no PyPI package carries those weights and the mirrors are blocked too. Substituting a different encoder would silently change your analysis, so I didn't.

## Where that leaves the notebook

**The stored outputs below Q1c step 4 are now stale.** The source is fixed, but the outputs still come from the old run. I deliberately did not write my partial results into cells 2–30, because a notebook where the first half was executed in one run and the second half in another is worse than one that's uniformly stale — the execution counts would no longer mean anything.

You need to re-run it end to end somewhere the model downloads. Colab works (the `open_database()` function already handles Colab paths), or your own machine. Expect the Q3 cells to take a while.

## What to expect when you do

Q1a/Q1b are safe. The things likely to move:

- **Q1c** — the embeddings-vs-TF-IDF comparison (AUC 0.709 vs 0.802). More text per record; the gap could narrow or widen.
- **Q2** — the clustering runs on the text components, so cluster composition and sizes will shift. Cluster 5 was identified as a filing-type artefact via `filing_kind`, which has now changed for ~450 filings. That diagnosis needs re-checking.
- **Q3** — text features feed the model, so R² and the ablation table will move. The Q3c asymmetry result (crashes predictable, rallies not) rests mostly on outcome and market features, so it should hold.

Any prose citing a number will need updating against the new run. The 43.7% figure in the Q1c commentary is already wrong — that one I can fix now if you want, since I've verified the replacement.

## You  _04:43_

yep can you fix it, so q2 and q3 is fine? can you also fix the code

## Claude  _04:43_

Let me answer the Q2/Q3 question properly first, then find every stale number.

<details><summary>tools run</summary>

- `Bash: Find stale numbers in markdown prose`
- `Bash: Compare document-type disagreement rates old vs new`
- `Bash: Re-run with wide display to read full tables`
- `Bash: Inspect cell 21 hardcoded numbers and cell 27 prose`
- `Bash: Read cells 19 and 24 prose`
- `Bash: Read new Q1b flagging table`
- `Bash: Compute the label-error signal union`
- `Bash: Find percentage claims in the Q1d summary`

</details>

## Claude  _04:45_

Now applying all the verified corrections.

<details><summary>tools run</summary>

- `Bash: Apply all verified number corrections`
- `Bash: Verify word count and that edited cells still run`
- `Bash: Inspect whether RE_SAFE over-deletes`
- `Bash: Quantify residual RE_SAFE over-deletion`
- `Bash: Commit prose corrections and push`

</details>

## Claude  _04:48_

Pushed (`f6c72c7..98aea99`).

## "So Q2 and Q3 is fine?" — no, and I can't tell you they are

I need to be direct about this. **Q2 and Q3 are not verified and not updated.** Their stored outputs and all their commentary still come from the run with the broken cleaning.

They depend on the sentence embeddings, and I can't recompute those here — Hugging Face is blocked by this environment's network policy. So I have no way to check whether their numbers moved. When I said earlier they'd "likely move", that was reasoning, not measurement.

What I can say concretely: `filing_kind` changed for roughly 450 filings, and the Q2c check-4 finding — that cluster 5 is a filing-type artefact, *"only 1.7% of its 120 filings are results announcements"* — is computed directly from `filing_kind`. That specific number is now unreliable. The whole feature space feeding the clustering also changed, since the text block is built from `clean`. Q3's text features likewise.

You must re-run the notebook end to end on Colab or your own machine, then re-check every number in Q2 and Q3 prose against the new outputs. I'd treat that as required before submission, not optional.

## What I fixed

**Code:**
- `RE_TAIL` — committed last turn.
- Cell 9: `range(0, 29)` → `range(30)`. It stopped at record 28 and never showed record 29.

**Prose — every figure re-measured by executing cells 2–30, none estimated:**

| Cell | Was | Now |
|---|---|---|
| 27 | 43.7% of characters removed | **17.5%** |
| 27 | median 19,186 → 7,986 | **→ 13,905** |
| 19 | 60.9% vs 46.0% agreement | **62.9% vs 46.3%** |
| 19 | median abs reaction 13.1% vs 5.1% | **11.4% vs 5.1%** |
| 19, 24, 35 | negative agrees 90% | **91%** |
| 24 | 2,015 flagged (44.4%) | **2,019 (44.5%)** |
| 24 | `no_result` flagged 13.3% | **16.9%** |
| 24 | 2,128 not-an-announcement | **1,946** |
| 35 | 61% / 46%, flags 39%/61%/84–90% | **63% / 46%, 38%/59%/79–88%** |

Q1d is still 496 words. Cells 2–30 re-execute cleanly after the edits.

**One correction that isn't mine:** cell 24 said the label-is-wrong signals "reach 589 records, or 13%". 589 is 455 + 89 + 45 — the sum of S1, S2 and S3. Those signals overlap, so the union is **551 (12%)**. That was wrong before my fix too. I changed it and flagged it in the commit.

## One thing left, your call

`RE_SAFE` has the same shape of problem, much smaller. Under the fixed pipeline it fires on 3,327 filings removing a median 3,355 characters — correct behaviour — but **removes over half the document in 151 filings and over 80% in 15**. Record 24 (LCTX) in your sample is one: it still ends up at 845 characters, because the deck repeats its safe-harbour block and the lookahead finds no terminator.

I did not touch it. Fixing it would shift the Q1 numbers a third time and need another prose pass, and you're about to validate. Say the word if you want it done — otherwise it's a fair limitation to note in Q1c.

## You  _05:33_

Okay can you explain to me what cell 10 is doing

<details><summary>tools run</summary>

- `Bash: Print the validation cell source`

</details>

## Claude  _05:34_

This is the one I've been calling cell 10 — the validation of `classify_filing()` against your hand-reading. (If you meant the `show()` / `result_sentences()` cell instead, say so and I'll do that one.)

## What it does

It scores the automated document-type classifier against your own reading of the same 30 filings.

**`HAND_LABELLED`** is a hardcoded list of 30 strings — your verdict on what kind of document each sampled filing is. Position in the list maps to position in `sample`, so element 0 is record 0, element 1 is record 1, and so on. This is the only place in the notebook where a human judgement is written down as data rather than derived by code.

**`check`** puts the two side by side and computes two different notions of "correct":

```python
check["exact"] = check.filing_kind == check.read_by_hand
check["announcement_correct"] = ((check.filing_kind == "results announcement") ==
                                 (check.read_by_hand == "results announcement"))
```

- `exact` — did the classifier pick the same one of four categories you did?
- `announcement_correct` — did it agree on the *binary* question, is this a results announcement or not?

The second is deliberately weaker, and the comment says why: *"Most of Analysis 2 below turns on the announcement / not-announcement distinction."* Everything downstream — the sign-agreement split, the Q1b `S5_not_an_announcement` signal, the Q2c cluster-5 diagnosis — only ever asks "is this an announcement?" Confusing a deck with a quarterly report costs nothing, because both are *not announcements*. So the binary figure is the one that licenses the downstream use, and the exact figure is context.

Current output: **23 of 30 exact, 28 of 30 on the binary.** All seven exact-disagreements are deck-vs-periodic-report or deck-vs-other confusions; none crosses the announcement line — which is why the binary score is higher, and why the notebook quotes it as the headline.

The final line then reports the finding this whole cell exists to license:

```python
print("Only %d of the 30 sampled filings are the announcement that carried the news."
      % (check.read_by_hand == "results announcement").sum())
```

Note it counts `read_by_hand`, not `filing_kind`. **The claim comes from your reading, not from the classifier** — the classifier's accuracy is established first, and only then is the human count reported. That ordering is what makes the "only 6 of 30" claim defensible, and it's the strongest methodological move in Q1a: it converts an assumption into a measurement.

## What a marker will press on

**1. `HAND_LABELLED` has no provenance in the notebook.** It's 30 bare strings. Nothing records when you read them, what you saw, or why record 4 is a deck rather than a periodic report. If asked "how do we know these are your readings?", the notebook has no answer. The `q1a_sample_filings/` dump I made partly addresses this — it has a `YOUR VERDICT` line per filing, so you can produce a worked record.

**2. It is circular unless the reading came first.** The cell is only evidence if you labelled the 30 before seeing `filing_kind`. Nothing in the notebook establishes that ordering. Be ready to say plainly that you read them first — and if you didn't, that changes what this cell is worth and you shouldn't claim otherwise.

**3. n=30 is small for a 4-class problem.** 23/30 exact has a wide confidence interval, and some categories have very few instances. The binary 28/30 is on firmer ground.

**4. The list is position-coupled to the sample.** It's valid only for `random_state=MEMBER_ID` with the current stratification. Change the seed, the strata, or the sort order, and these 30 strings silently attach to different filings — no error, just a meaningless score. Worth a comment saying so.

**5. It survived the cleaning fix unchanged**, at 23/30 and 28/30. Worth knowing that's not because nothing moved: record 21 (TCRT) shifted from `other` to `periodic report`, so the composition of the disagreements changed while the totals happened not to. That's a coincidence of this sample, not stability you can claim in general.

## You  _05:39_

Sorry can you just explain from Re_result what is happening

## Claude  _05:39_

That's cell 9 — the excerpt extractor. Let me walk it in order.

<details><summary>tools run</summary>

- `Bash: Demonstrate the scoring on a real record`

</details>

## Claude  _05:40_

Here's the cell, top to bottom, with a real record run through it.

## `RE_RESULT`

One alternation of ~20 phrases that mark a sentence as reporting a *result*:

```
primary endpoint | co-primary | secondary endpoint | statistically significant
p = 0.0xx | hazard ratio | odds ratio | response rate | overall survival
progression-free | did not meet | failed to | met its | achieved | topline
discontinu* | futility | terminat* | well-tolerated | adverse events
efficacy | superiority | non-inferior* | interim analysis
```

Deliberately two-sided — `met its` and `achieved` sit next to `did not meet` and `failed to`. It's detecting that a result is being *reported*, not whether the result is good. That matters, because this same helper is later reused to pick the sentences that get embedded for Q1c, and an outcome-biased selector would leak the label into the features.

`p\s?[=<>]\s?0?\.\d+` catches `p=0.009`, `p < .05`, `p> 0.05` — the optional `0?` handles the leading-zero-dropped style journals use.

## `drug_tokens(name)`

Turns a drug name into search tokens:

```python
name = re.sub(r"\(.*?\)", "", str(name))          # drop anything parenthesised
return [t.lower() for t in re.split(r"[^A-Za-z0-9]+", name) if len(t) > 3][:4]
```

Strips parentheticals, splits on non-alphanumerics, drops tokens of 3 characters or fewer, keeps at most 4. The length filter is there to stop fragments like "IL" or "AB" matching everywhere.

## `result_sentences(clean_text, drug, k=10, lo=40, hi=600)`

Four steps.

**Split and filter.** `re.split(r"(?<=[.!?])\s+", …)` — a lookbehind split, so the punctuation stays attached to the sentence. Then keep only sentences between `lo=40` and `hi=600` characters. Short ones are headers and fragments; long ones are usually unsplit tables or legal text.

**Score** each surviving sentence:

```python
hit   = the sentence mentions a drug token
n_res = how many RE_RESULT terms it contains
score = (3 if hit else 0) + min(n_res, 3) + (2 if (hit and n_res) else 0)
```

So naming the drug is worth 3, result language up to 3 (capped, so a legal paragraph stuffed with jargon can't run away with it), and there's a **2-point interaction bonus** for doing both in the same sentence. That bonus is the real logic of the function: a sentence that names *this* drug *and* states a result is what you want, and it's scored above a sentence that does either alone.

**Select** the top `k` by `(-score, position)` — position breaks ties toward earlier sentences, which in a press release means the headline and lead paragraph.

**Restore reading order.** The selected sentences are re-sorted by original position before returning, so you read them in the order they appear in the filing rather than in score order.

Two fallbacks: if no sentence survives the length filter, return the first 600 characters raw; if nothing scores above zero, return the first `k` sentences unranked.

## `show(i, k=4)`

Prints one sampled record's header — accession, ticker, date, drug, label, consensus type, CAR, document kind, restatement count — then the top 4 sentences. `clean_by_acc` maps accession → cleaned text, so **it reads the cleaned column**, as we established.

## Worked example — record 6

`drug_name` is `'maralixibat (LIVMARLI)'`, label `negative`. The filing splits into 92 sentences, 60 survive the length filter. Top scorers:

| Score | Position | Drug? | Result terms | Sentence |
|---|---|---|---|---|
| 6 | 3 | yes | 1 | "announced topline results of the Phase 2b EMBARK trial evaluating…" |
| 2 | 4 | no | 2 | "The study did not meet its primary endpoint or the key secondary endpoints." |
| 1 | 5 | no | 1 | "LIVMARLI was generally well-tolerated with no new safety findings." |

You can see the machinery working — and you can also see the problem.

## Two weaknesses worth knowing about

**1. `drug_tokens` throws away the brand name.** `re.sub(r"\(.*?\)", "", …)` deletes `(LIVMARLI)`, leaving only `maralixibat`. But filings routinely use the brand name in body text — the third sentence above says "LIVMARLI", and scores `hit=False` because of it. The generic-name-only token list systematically under-scores sentences written in brand-name style. Removing that `re.sub` and keeping both names would be a one-line improvement.

**2. The sentence that carries the actual result ranks second, at score 2.** *"The study did not meet its primary endpoint"* is the finding — it's why this record is labelled `negative`. It scores below a boilerplate announcement sentence because it says "the study" rather than "maralixibat". Pronouns and anaphora are invisible to a bag-of-tokens drug match, and result sentences very often refer back to the subject rather than re-naming it.

At `k=4` this is harmless — all three sentences print, so your hand-reading saw the real result. But Q1c's `embed_records()` calls the same function with **`k=3` and `hi=400`**, and the ranking is exactly what decides which three sentences get embedded. So this ranking quirk propagates into the Q2 and Q3 feature space, where nobody is reading the output to notice.

That's a fair thing to raise yourself in Q1c rather than wait for a marker to find it.

## You  _05:48_

so re_results so phrases that tags sentences?

## Claude  _05:48_

Yes, essentially — with one precision worth having.

It doesn't *label* sentences. It **counts** matches, and the count feeds a score:

```python
n_res = len(RE_RESULT.findall(s))    # how many result phrases in this sentence
```

`findall` returns every match, so a sentence containing "did not meet its primary endpoint" scores 2 hits, not 1. That count then contributes to the ranking, capped at 3:

```python
score = (3 if hit else 0) + min(n_res, 3) + (2 if (hit and n_res) else 0)
```

So it's a **relevance signal, not a tag**. Three consequences:

- It's a matter of degree, not yes/no. A sentence with three result phrases outranks one with a single phrase.
- The cap at 3 stops a dense legal paragraph from dominating on volume alone.
- It's not a filter. A sentence with **zero** result phrases still scores 3 if it names the drug, and can still be returned. Nothing is excluded for failing `RE_RESULT` — it only affects ordering.

The thing being "tagged", if anything, is the *sentence's position in a ranking* — and only the top `k` survive into the output.

Concretely on record 6:

| Sentence | drug? | `RE_RESULT` hits | Score |
|---|---|---|---|
| "announced topline results of the Phase 2b EMBARK trial…" | yes | 1 (`topline`) | 3 + 1 + 2 = **6** |
| "The study did not meet its primary endpoint or the key secondary endpoints." | no | 2 (`did not meet`, `primary endpoint`) | 0 + 2 + 0 = **2** |
| "LIVMARLI was generally well-tolerated…" | no | 1 (`well-tolerated`) | 0 + 1 + 0 = **1** |

Which is also where you can see the ranking flaw I mentioned — the sentence with the *most* result language is the actual finding, but it loses to the announcement sentence because the drug-name bonus (3, plus the 2-point interaction) outweighs everything `RE_RESULT` can contribute.

## You  _05:54_

okay so how did it know for the 6th one document = results announcement

<details><summary>tools run</summary>

- `Bash: Trace the classifier decision for record 6`

</details>

## Claude  _05:55_

Different mechanism entirely — `RE_RESULT` had nothing to do with it. That's cell 9, used only for ranking sentences. `filing_kind` is set back in cell 6 by `classify_filing()`.

Here's the actual trace for record 6 (MIRM, `0001193125-23-297614`):

```
h = clean_text[:1200]           # the "headline window"

RE_FIN.search(h)   → False      # no quarterly/annual results language
RE_RES.search(h)   → True       # matched: 'announced topline results of'
RE_DECK.search(h)  → False
```

Which lands on the very first branch:

```python
if res and not fin:
    kind = "results announcement"
```

`RE_RES` fired because the text contains `announced` … `topline results of`, matching:

```
\b(Announce[sd]?|Report(s|ed)?|Present(s|ed)?|Provide[sd]?)\b[^.]{0,150}
\b(top-?\s?line|primary endpoint|pivotal|Phase\s?[1-4I]|results? (from|of|in|for)|data (from|in|at))\b
```

The `[^.]{0,150}` lets up to 150 non-period characters sit between the verb and the result noun, so "announced topline results of the Phase 2b EMBARK clinical trial" matches as one span. `RE_FIN` found nothing, so the trial-results reading wins outright — no fallback to the body was needed.

## The part worth noticing

Look at what that "headline window" actually contains:

> *"Securities registered pursuant to Section 12(b) of the Act: Title of each class Trading Symbol(s)… Indicate by check mark whether the registrant is an emerging growth company as defined in Rule 405…"*

**It isn't a headline.** It's the first 1,200 characters of cleaned text, and the first several hundred are SEC cover-page residue that `RE_COVER` didn't strip. The real content starts later, and the phrase that decided this classification sits well inside the window rather than at the top of it.

So `head=1200` isn't picking out a headline — it's a guess that the substantive first sentence will fall within 1,200 characters of the start. Here it did, with room to spare. On a filing with a longer cover page or more registered share classes, the same sentence would fall outside the window, `RE_RES` would miss in `h`, and the classification would drop through to the body checks — where a passing mention of a quarter could flip it to `periodic report`.

That's the same failure mode the docstring says was already caught once with Theravance. The headline-first rule fixed the *precedence* problem; it didn't fix the fact that the window boundary is arbitrary. This is exactly the `head=1200` / `body=6000` sensitivity I flagged earlier as untested — record 6 is a concrete illustration of why it's worth a sentence in your write-up.

## You  _06:10_

so does the headline issue impact my project

## Claude  _06:10_

Let me measure it rather than speculate — vary `head` and see how much actually moves.

<details><summary>tools run</summary>

- `Bash: Sensitivity of the classifier to the head window`
- `Bash: Does the Q1a conclusion survive a different head window`

</details>

## Claude  _06:13_

Measured it. Short answer: **yes, but only marginally — none of your conclusions change.**

## Sensitivity of the classifier to `head`

| `head` | results ann. | periodic | deck | other | filings changed vs 1200 | 30-sample: exact / binary |
|---|---|---|---|---|---|---|
| 600 | 1,025 | 1,718 | 549 | 502 | 53 | 24 / 29 |
| 900 | 1,055 | 1,706 | 531 | 502 | 25 | 24 / 29 |
| **1200** | **1,078** | **1,697** | **517** | **502** | — | **23 / 28** |
| 1800 | 1,138 | 1,695 | 459 | 502 | 66 | 24 / 29 |
| 2400 | 1,173 | 1,702 | 417 | 502 | 111 | 25 / 30 |
| 4000 | 1,201 | 1,713 | 378 | 502 | 165 | 24 / 29 |

Between 1.4% and 4.4% of filings move. Two structural things worth seeing: every change crosses the announcement boundary (the "changed" and "announcement-flag changed" counts were identical at every setting), and the movement is almost entirely **deck ↔ results announcement** — `periodic report` and `other` barely budge. A wider window finds result language deeper inside investor decks and reclassifies them as announcements.

## Does the Q1a conclusion survive?

This is the test that matters, since the announcement/periodic gap is what Q1a rests on:

| | announcements | periodic reports | gap |
|---|---|---|---|
| `head=1200` | 62.9% (n=673) | 46.3% (n=741) | **16.6 pts** |
| `head=2400` | 63.3% (n=733) | 46.4% (n=742) | **16.9 pts** |

The finding is essentially invariant. Your claim — labels agree with the market far more often in genuine announcements than in periodic reports — holds at every window I tested. That's a robustness result you can state.

## The awkward bit

**`head=1200` scores worst of the six settings on your own 30-filing validation** (23/28, versus 24/29 or 25/30 everywhere else). At 2400 it's a clean 25/30.

Don't over-read that — with n=30, a one- or two-record difference is noise, and the settings aren't really distinguishable. But it does establish something: **1200 was not tuned.** If it had been, 2400 would have been chosen. That's arguably to your credit, since tuning a threshold on the same 30 records you validate against would be circular — but you should be able to say that deliberately rather than be caught by it.

## So, impact on the project

- **Q1a** — negligible. Conclusion invariant, headline numbers move by ~0.4 points.
- **Q1b** — small. `S5_not_an_announcement` (currently 1,946 records) would shift by a few dozen. Weight-2 signal, won't reorder the queue.
- **Q2c check 4** — the cluster-5 diagnosis is computed from `filing_kind`, and that check is the reason you recommend discarding cluster 5. Its percentages will move slightly. Re-verify after the full re-run.
- **Q3a** — `filing_kind` is one feature among many. Immaterial.

Compare with the `RE_TAIL` bug, which changed the *text itself* for 1,215 filings. This is second-order by comparison.

**My recommendation: leave `head=1200` alone and write it up.** Two or three sentences in Q1c saying you tested 600–4000, that 1.4–4.4% of filings reclassify, that the announcement/periodic gap holds at 16.6–16.9 points throughout, and that you kept the untuned value rather than fit it to the 30-record sample. That converts a soft spot into evidence of robustness testing — which is what the rubric rewards. Changing the value now would invalidate numbers again for no real gain.

Want me to draft that paragraph and add it to Q1c?

## You  _06:19_

yep can you do that please

<details><summary>tools run</summary>

- `Bash: Draft and test the new sensitivity cell`

</details>

## Claude  _06:21_

Cell verified. Inserting it plus the write-up.

<details><summary>tools run</summary>

- `Bash: Insert the sensitivity cell and write-up`
- `Bash: Verify and push the new cell`

</details>

## Claude  _06:22_

Push rejected — the remote has moved. Let me look before doing anything.

<details><summary>tools run</summary>

- `Bash: Inspect divergence with remote`

</details>

## Claude  _06:23_

Two commits landed on the remote touching the same notebook. Let me see what they did before I merge anything.

<details><summary>tools run</summary>

- `Bash: Compare remote notebook against the base`
- `Bash: Diff the changed cell and inspect its output`

</details>

## Claude  _06:23_

The user re-ran cell 9 with the full 30-record loop (using the `range(30)` fix) and pushed the output. That's independent of my new cells — merging rather than clobbering.

<details><summary>tools run</summary>

- `Bash: Start the merge`

</details>

## Claude  _06:23_

Auto-merge on notebook JSON is risky — verifying the result properly before committing.

<details><summary>tools run</summary>

- `Bash: Verify merged notebook integrity`
- `Bash: Commit the verified merge and push`

</details>

## Claude  _06:25_

Done and pushed (`fc064e1..35ae798`).

## What I added

A code cell and a write-up, placed in **Q1a** rather than Q1c — I moved it from what I proposed because `classify_filing()` is defined and validated there, and this directly extends the validation cell above it. In Q1c it would have sat among the cleaning discussion, which is a different mechanism.

The code cell sweeps `head` from 600 to 4,000 and reports three things per setting — how many filings reclassify, how the classifier scores against your 30 hand-read documents, and whether the Analysis 2 gap survives:

```
head  results_ann  periodic  deck  reclassified  exact  binary  ann%   per%   gap
 600         1025      1718   549            53     24      29  63.6   46.3  17.2
 900         1055      1706   531            25     24      29  63.6   46.2  17.4
1200         1078      1697   517             0     23      28  62.9   46.3  16.6
1800         1138      1695   459            66     24      29  63.7   46.1  17.6
2400         1173      1702   417           111     25      30  63.3   46.4  16.9
4000         1201      1713   378           165     24      29  63.0   46.6  16.4
```

The write-up makes three points: the movement is almost entirely decks being read as announcements as the window widens; the 16.4–17.6 point gap holds at every setting, so Analysis 2 doesn't depend on the choice; and `head=1200` is kept **despite** scoring worst on the 30-filing sample, because tuning the window on the same documents used to validate the classifier would make that validation circular. Saying that outright is stronger than quietly adopting 2400.

The new cell has no stored output — it populates on your full re-run.

## One thing you should know about the push

My first push was rejected. You'd pushed two commits meanwhile — cell 9 switched from the three representative records to the full `range(30)` loop and re-run, adding 43,786 characters of output for all 30 filings.

I merged rather than forced, then verified rather than trusting git's auto-merge, since notebook JSON can merge into something that parses but is wrong. Checked: JSON valid, 132 cells, your `range(30)` edit and its output intact, my cells at 12–13, the `RE_TAIL` fix and corrected Q1c figures still present, no duplicated cells, and every Q1 code cell through index 32 executes cleanly.

Worth flagging for the rest of the session: you're editing through the GitHub web UI while I'm editing the same file locally. Same-cell edits from both sides at once would be a genuine conflict that no script can resolve safely. If you're about to work on a cell, tell me and I'll stay off it.

## Still outstanding

- **Full re-run required** — Q2 and Q3 outputs and prose still reflect the pre-fix cleaning, and the new sensitivity cell is unexecuted. Needs a machine where the sentence-transformer model downloads.
- **`RE_SAFE`** — over-deletes in 151 filings, 15 of them by more than 80%. Untouched, your call.
- **Q4 and Q5** — still template.

## You  _06:33_

Why is the 4th record positive? The news doesnt seem positive

<details><summary>tools run</summary>

- `Bash: Inspect record 4 and its recovered text`
- `Bash: Find the actual LPCN 1111 content in the deck`

</details>

## Claude  _06:34_

Good catch — but the label is right, and what you're reading isn't the news. Let me show you why.

<details><summary>tools run</summary>

- `Bash: Show why the real result sentence never reaches the ranking`
- `Bash: Quantify how much text the sentence filter discards`

</details>

## Claude  _06:36_

## The label is correct — you're reading the wrong part of the filing

The deck actually says, verbatim:

> "LPCN 1111: Next generation once-daily oral TRT option — **Positive top-line Phase 2b study results** — Once daily dose identified for the pivotal Phase 3 study"

> "LPCN 1111: Phase 2b Results / Highlights **Met Primary Study Objectives** … Target once-daily Phase 3 dose **met both primary and secondary end points**. Good dose-response relationship was observed"

That is squarely `positive` under the documented definition. And `car_3day` is **+15.3%** — the market agreed. Sign agreement holds on this record.

## So why does the excerpt read like bad news?

What `show(4)` prints is the deck's **risk-factor boilerplate**:

> *"Delays in clinical programs, whether caused by … adverse events…"*
> *"If the Company's product candidates do not meet safety or efficacy endpoints…"*

Two failures stack up to produce that.

**1. The sentence splitter can't parse a slide deck.** Decks have almost no sentence punctuation — they're bullet fragments. Splitting this filing on `[.!?]` yields just 28 chunks: median 182 characters, max **3,852**. Four chunks hold **69% of all the characters**, and they're all over the 600-character limit, so `result_sentences()` discards them before any scoring happens.

The slide containing "Met Primary Study Objectives" **is** chunk 23 — 3,852 characters — dropped by the `hi=600` filter. The winning sentence never enters the competition.

**2. What survives is the only real prose in a deck: the risk factors.** Those are properly punctuated sentences, and they're stuffed with `RE_RESULT` vocabulary — `adverse events`, `safety or efficacy endpoints`, `discontinue`. They win by default. This is exactly what your Q1c commentary predicted about the safe-harbour block being "full of exactly the vocabulary a result classifier would key on" — `RE_SAFE` didn't strip this copy of it, because the deck repeats it after the exhibit marker.

## Partly my doing, and worth being straight about

Before the `RE_TAIL` fix this filing was 305 characters of cover note. The fix genuinely recovered the content — the LPCN 1111 result slides are now in `clean`. But it also recovered the risk-factor section, and the ranking reaches the boilerplate rather than the result. The filing is more informative than it was; the excerpt is more misleading.

## This is bigger than one record

| | filings losing >50% of text | mean share lost |
|---|---|---|
| `hi=600` (Q1a reading) | 638 (17%) | 23% |
| `hi=400` (`embed_records`, Q2/Q3 features) | **1,009 (27%)** | **33%** |

By document type at `hi=400`: decks lose **52%** of their characters, `other` 38%, periodic reports 29%, announcements 28%.

The `hi=400` row is the one that matters. `embed_records()` calls the same function with `k=3, hi=400`, so **for roughly a quarter of filings the Q2 and Q3 text features are built from whatever prose survived — which in decks is disproportionately risk-factor boilerplate.** That's a feature-quality problem, and it plausibly contributes to the Q3b finding that "the wording of the announcement adds nothing once company features are present."

## What I'd do

The minimal fix is to hard-wrap over-long chunks instead of discarding them — split anything above the limit on a secondary boundary (`;`, `·`, or a fixed window) so slide text still competes. That's a few lines in `result_sentences()`.

But it changes the Q1a excerpts, the Q1c embeddings, and everything downstream — a third round of number changes, on top of a re-run you already owe. Your call, and it's a legitimate choice to write it up as a limitation instead: you have the measurements now, and "decks lose 52% of their text to the sentence filter" is a strong thing to be able to state.

For record 4 specifically: nothing to fix. Label correct, market agreed. Just don't rely on `show()` output for deck-type filings — read the raw text in `q1a_sample_filings/04_positive_LPCN_*.txt` instead.

## You  _06:39_

can you explain to me how the six categories were classified

## Claude  _06:39_

That's upstream of your notebook — it's the pipeline that produced `consensus_outcomes`. Let me read the methodology.

<details><summary>tools run</summary>

- `Bash: Read methodology section 5 on outcome classification`
- `Bash: Check consensus_type distribution in the database`

</details>

## Claude  _06:39_

Important framing first: **you didn't build this.** The six categories arrive pre-made in `consensus_outcomes`, produced by the pipeline in §5 of `methodology.md`. Q1a is your evaluation *of* it. Here's how it works.

## Two prompts, run independently on every filing

Every one of the 3,794 filings was classified twice, by two deliberately different prompts:

**B1a — ownership + quote-first**
- Only extract results the filing company owns or sponsors (companies routinely discuss competitors' trials)
- Extract 1–3 verbatim sentences *before* assigning a label
- Classify into the six categories

**B3b — quote-first + statistics required**
- Must return an explicit statistics field (p-value, HR, ORR…)
- **If no statistics found → `inconclusive`**, unless there's an unambiguous endpoint statement

They weren't chosen because both scored well. They were chosen because they **fail differently**: B3b sets a higher evidential bar, so the two part company exactly on borderline filings — and that disagreement becomes a usable reliability signal.

## The six definitions

| Category | Definition |
|---|---|
| `positive` | Primary endpoint met with statistical significance, or unambiguous statement of success |
| `negative` | Primary endpoint missed, stopped for futility, or programme discontinued |
| `mixed-positive` | Some endpoints met, others missed; overall direction favourable |
| `mixed-negative` | Some endpoints met, but overall unfavourable |
| `inconclusive` | Results reported but insufficient to determine direction |
| `no_result` | No trial outcome data at all (earnings report, corporate transaction) |

## How the two labels were reconciled

| B1a | B3b | Consensus | Type |
|---|---|---|---|
| same | same | keep | `agree` |
| positive | mixed-positive | **positive** | `same_direction` |
| negative | mixed-negative | **negative** | `same_direction` |
| any definitive | inconclusive | take the definitive one | `b3b_inconclusive_override` |
| opposite | opposite | flag | `flagged_disagreement` |

I checked the database against the methodology's table — they reconcile exactly:

```
agree                      3085   (1,391 same-result + 1,694 both no_result)
b3b_only                    523
b1a_only                    446
b3b_inconclusive_override   370
same_direction               67
flagged_disagreement         45
b1a_inconclusive_override     3
```

Note `b1a_only` (446) and `b3b_only` (523) — nearly a thousand records where **only one prompt found a result at all**. Those have no second reading behind them, which is what your Q1b `S9_single_prompt` signal picks up.

## How the prompts were selected

Three rounds on a **fixed 10-filing subsample**, varying one design idea per round: round 1 chose the overall strategy (quote-first won), round 2 chose what to return alongside the label, round 3 picked B1a and B3b from six sub-variants.

Two things about that subsample matter, and the methodology is candid about both:

- **It was chosen adversarially, not at random** — 8 of the 10 were filings where two earlier passes had *disagreed*. The intent was to select hard cases.
- **The pair was never re-validated on a random sample.** So the process says little about calibration across the bulk of the corpus, especially the 37% that is `no_result`.

That gap is precisely the opening your Q1a exploits: your stratified sample is the first random look at this pipeline's output.

## Where your Q1a findings attach to specific design decisions

This is the part worth having straight for the video, because each critique traces to a documented choice:

- **Round 3 rejected B1b**, the variant that flagged whether an announcement was *new* rather than a restatement. That is exactly the timing defect you found — roughly half of directional records sit in filings that aren't the disclosure event. The methodology records the choice but not its cost; you measured the cost.
- **Quote-first anchoring** means the label attaches to the most *result-like* sentence, never the most *material* one. Hence Neurogene: labelled `mixed-positive` off favourable efficacy data, while the actual news was a serious adverse event and a halted dose.
- **The `same_direction` rule folds `mixed-positive` into `positive`** — and you showed `mixed-positive` has a mean CAR of **−6.6%**. The rule treats as favourable a category the market marks down.
- **`b3b_inconclusive_override` (370 records)** rests on an assumption the methodology states plainly: that B3b's high inconclusive rate comes from its statistics requirement rather than genuine ambiguity. Your `S10_stats_override` signal flags these.
- **Drug matching between prompts uses substring containment**, which produces the 89 conflicting duplicates and contributes to the 455 records naming a drug that appears nowhere in the filing.

## One thing to be able to say out loud

**The statistics were extracted but never saved.** `consensus_outcomes.statistics` is empty in all 4,539 rows, and `evidence` is populated in only 45. So the quote-first grounding — the entire design principle of both prompts — **cannot be audited from the database at all.** You have to go back to `filing_text` to check any label, which is exactly what your Q1a sample does by hand.

That's the single sharpest observation available about this pipeline, and it's already in your cell 19 table.

## You  _06:43_

so going back to the previous point, do i have to do anything about the excerpts where it seems misleading

## Claude  _06:43_

Let me make this concrete — which of your 30 are actually affected.

<details><summary>tools run</summary>

- `Bash: Identify which sampled records are affected`

</details>

## Claude  _06:44_

Short answer: **one small thing you must do, one you should do, one that's optional.**

## Must do — re-read five records

Five of your 30 lose more than half their text before ranking:

| idx | ticker | label | lost |
|---|---|---|---|
| 4 | LPCN | positive | 69% |
| 6 | MIRM | negative | 61% |
| 17 | LYRA | mixed-negative | 52% |
| 21 | TCRT | inconclusive | 77% |
| 25 | ZVRA | no_result | 57% |

Read those five against the raw text in `q1a_sample_filings/` and confirm your label judgement still holds. It's maybe fifteen minutes. This isn't optional because two specific claims depend on it — "in 24 of our 30 cases the label fairly described the filing", and the `HAND_LABELLED` list feeding your 23/30 and 28/30 validation.

**Record 6 is a useful reassurance**: it loses 61% of its text, yet the surviving excerpt still contains "did not meet its primary endpoint". Losing text doesn't automatically mean losing the news. Record 4 was the unlucky case.

The honest question only you can answer: **did you read the 30 from the filings, or from `show()` output?** If from the filings, nothing is wrong — the excerpts are a convenience layer and their defects don't touch your reading. If from `show()` output, then pre-fix several of those records showed almost nothing (record 4 was 305 characters of cover note), and those judgements need redoing. You now have the raw text either way.

## Should do — write up the measurement

Two or three sentences in Q1c. You have real numbers: the sentence filter discards 23% of characters on average at `hi=600` and **33% at `hi=400`**, which is what `embed_records()` uses; decks lose **52%**; 1,009 filings (27%) lose more than half their text into the Q2/Q3 feature build.

That's worth stating regardless of whether you fix it. A limitation you measured and quantified reads as rigour. The same limitation found by a marker reads as an oversight — and it's findable, because the deck-heavy tickers (TNXP appears six times in your sample) make it visible.

It also gives you a candidate explanation for a Q3 result you already report: "the wording of the announcement adds nothing once company features are present." If a third of the text never reaches the encoder, that finding is partly about the pipeline, not only about the world. Saying so is stronger than leaving it as a clean negative result.

## Optional — the code fix

Hard-wrap over-long chunks instead of discarding them, so slide text competes rather than being dropped. A few lines in `result_sentences()`.

**My recommendation: don't.** It changes the Q1a excerpts, the embeddings, and every Q2/Q3 number, on top of a full re-run you already owe and haven't been able to do yet. You're validating now. The measured limitation is worth nearly as much as the fix and costs you nothing downstream.

If you had a week, I'd say fix it. With submission close, document it.

## What isn't a problem

Record 4's label. `positive` is correct, the deck says "Met Primary Study Objectives", and the market moved +15.3%. Nothing to change there — the excerpt was misleading, the data wasn't.

Want me to draft the Q1c limitation paragraph with these numbers, the way I did for the head-window one?

## You  _06:45_

Wait also I am reading record 8, why is this one negative after the points have been met

<details><summary>tools run</summary>

- `Bash: Inspect record 8`
- `Bash: Verify why the dupilumab sentence appears first`

</details>

## Claude  _06:46_

**The label is right — that "met its primary endpoint" sentence is about a different drug.**

Record 8's `drug_name` is **suptavumab**. The sentence you're reading is about **dupilumab**, which is separately classified in the same filing:

```
drug_name              phase    outcome    consensus_type
dupilumab (Dupixent)   Phase 3  positive   b3b_inconclusive_override
dupilumab (Dupixent)   Phase 3  positive   b3b_inconclusive_override
suptavumab             Phase 3  negative   agree        ← this is record 8
```

The suptavumab sentences are unambiguous:

> "In August 2017, the Company reported that a Phase 3 study evaluating suptavumab **did not meet its primary endpoint** of preventing medically-attended RSV infections in infants."
> "**Further clinical development of suptavumab has been discontinued.**"

Missed primary endpoint plus programme discontinuation — that's the textbook `negative` definition. Both prompts agreed (`consensus_type = agree`).

## Why the wrong drug appears first

Scoring for suptavumab:

| Score | Pos | Drug? | Terms | Sentence |
|---|---|---|---|---|
| 7 | 51 | yes | 2 | "suptavumab did not meet its primary endpoint…" |
| 6 | 52 | yes | 1 | "development of suptavumab has been discontinued" |
| 3 | 50 | yes | 0 | "Suptavumab is an antibody to RSV-F" |
| 2 | 33 | no | 2 | "…dupilumab… met its primary endpoint and key secondary endpoints" |

The dupilumab sentence ranks *last* of the four — it scores 2 against 7. But `result_sentences()` re-sorts the winners back into **reading order** before returning them, and the dupilumab sentence sits at position 33 while the suptavumab ones are at 50–52. So the lowest-scoring sentence prints first.

The ranking worked correctly. The presentation misleads.

## This is worth more than a footnote

Record 8 is a clean illustration of three things your notebook already argues:

**1. Multi-drug filings.** Your Q1c commentary notes ~1,073 records sitting in multi-drug filings. This is one: a positive readout and a discontinued programme in the same 8-K, sharing a single `car_3day` of **+0.39%**. That number is not the market's verdict on suptavumab — it can't be, it's also the verdict on dupilumab. Q3 has to handle that rather than pretend it away, which is exactly what your Q3a step 1 says.

**2. The timing defect.** `filing_kind` is `periodic report`, `n_prior_refs = 1`. This is a November filing restating an August discontinuation. The news was three months old — so a `negative` label sits beside a slightly positive return, and the return is measuring the quarterly report.

**3. A presentation flaw in the excerpt layer** — reading order can put an off-target sentence at the top. Cheap to fix if you ever want to: print the score alongside each sentence in `show()`, so the reader sees which line actually drove the selection.

## For your validation

Both records 4 and 8 came back the same way: **excerpt misleading, label correct.** That's two for two, and it's a good sign — the excerpt layer is where the defects are, not the classifications.

It also strengthens the point from a moment ago: whatever you concluded about individual labels should come from the filings in `q1a_sample_filings/`, not from `show()`. The five records I flagged for re-reading are still worth doing, and I'd now add: whenever a sampled filing names more than one drug, check which drug the sentence is about before judging the label.

## You  _06:48_

Okay now lets look at the hand labelled cell what is it doing

<details><summary>tools run</summary>

- `Bash: Read cell 11 to see how the label judgements are recorded`
- `Bash: Cross-check HAND_LABELLED against the cell 11 prose`

</details>

## Claude  _06:49_

`HAND_LABELLED` is the one place in the notebook where a human judgement is stored as data rather than written as prose.

## What it holds — and what it does not

```python
HAND_LABELLED = [                       # index into `sample`, my reading of the document
    "results announcement", "periodic report", "results announcement", ...
```

Thirty strings, position-matched to `sample`: element 0 is record 0, element 4 is the LPCN deck, element 8 is the REGN quarterly report.

**These are document-type readings only — not outcome readings.** Given the last few questions, that distinction matters. Whether `negative` was the right call on suptavumab is *not* in this list. This list only says "record 8 is a periodic report."

The two hand-readings are recorded in completely different ways:

| Judgement | Where it lives | Auditable? |
|---|---|---|
| What kind of document is this? | `HAND_LABELLED`, as data | Yes — re-scored on every run |
| Is the outcome label fair on the text? | A markdown table in cell 11, as per-category counts | No |

## What the cell computes

```python
check["exact"] = check.filing_kind == check.read_by_hand
check["announcement_correct"] = ((check.filing_kind == "results announcement") ==
                                 (check.read_by_hand == "results announcement"))
```

Two scores: did the classifier pick the same one of four categories (23/30), and did it agree on the binary announcement-or-not question (28/30). The binary one is the one that licenses downstream use, because nothing downstream cares whether a non-announcement is a deck or a quarterly report.

Then the payoff line counts **your** column, not the classifier's:

```python
print("Only %d of the 30 sampled filings are the announcement that carried the news."
      % (check.read_by_hand == "results announcement").sum())
```

That ordering is the point of the whole cell: establish the classifier is trustworthy on the binary split, *then* report the human count. It turns an assumption into a measurement.

## It's internally consistent

I cross-checked the list against the prose in cell 11:

```
periodic report        15        cell 11: "15 are quarterly or annual reports"  ✓
deck / FD update        8        cell 11: "8 are investor decks"                ✓
results announcement    6        cell 11: "Only 6 of the 30"                    ✓
other                   1        cell 11: "1 is a securities purchase agreement" ✓
```

Cell 11's "label fair" column also sums to exactly 24, matching "in 24 of the 30 records the label is a defensible reading". Nothing is inconsistent between the data and the prose.

## The gap worth fixing

**The 24/30 has no per-record backing anywhere.** Cell 11 gives category totals — `mixed-positive (5) → 3 fair`, `inconclusive (5) → 1 fair` — so we know 6 records were judged unfair and which categories they fall in, but not *which records*. Nobody can check them, and you can't re-score them.

That matters right now for two reasons. You're about to re-read five records against the raw text — and if any judgement changes, there is no structured place to record it, and the 24 in the prose would have to be edited by hand. And record 8 showed how easy it is for a multi-drug filing to look mislabelled when it isn't; a per-record list would let you write down *why* you judged each one.

The fix is four lines beside the existing list:

```python
HAND_LABEL_FAIR = [True, True, ...]     # is the outcome label fair on the text?
check["label_fair"] = HAND_LABEL_FAIR
print("Label is a fair reading of the filing:  %d of 30" % sum(HAND_LABEL_FAIR))
```

Then both hand-readings are data, both are re-scored on every run, and the 24/30 becomes auditable in the same way the 28/30 already is. It also makes the cell 11 table generated rather than typed, so the two can't drift apart.

Want me to add that scaffold with the six unfair records left as `None` for you to fill in as you re-read? That would slot in with the five records I flagged earlier.

## You  _06:51_

why is this section even needed

## Claude  _06:51_

Fair question. Let me check what the rubric actually asks for before I answer from opinion.

<details><summary>tools run</summary>

- `Bash: Read the rubric and brief for Q1a`
- `Bash: Extract the rubric text for Q1a`

</details>

## Claude  _06:52_

Checked the rubric. Short answer: **it's not needed to pass — it's needed for the top band, and it's needed for four things downstream to be defensible.**

## What the rubric actually requires for Q1a (7%)

- **Hurdle for a 2:** examine ≥20 classifications against the original filing text and state what you found.
- **Hurdle for a 3:** conduct *both* analyses — accuracy against filing text **and** the label-vs-return comparison.
- **Top differentiator:** *"Identifies systematic patterns **across the whole sample**, with specific evidence from the filings, and separates disagreement over where a category boundary falls from outright misreading of the filing."*

Your stratified sample (cell 8) plus the reading (cell 9) clears both hurdles on its own. Cell 10 isn't doing that work.

## So what is it doing

`classify_filing()` is **your own invention** — it isn't in the database, it isn't in the methodology, you wrote it. And you then apply it to all 3,794 filings to produce the single biggest finding in Q1a: sign agreement 62.9% in announcements versus 46.3% in periodic reports.

That's the "systematic patterns across the whole sample" the top band asks for. It's also a claim about 3,794 filings made with a home-made regex classifier. Cell 10 is the bridge between the 30 you actually read and the 3,794 you're making claims about. Without it, the answer to "how do you know your document classifier works?" is nothing.

Four things break, or become assertions, if you delete it:

1. **Analysis 2's document-type split** — the largest single cause of disagreement you identify.
2. **Q1b's `S5_not_an_announcement`** — weight 2, fires on 1,946 records, and cell 24 calls it *"the largest single contributor by far"* to the 44% flag rate.
3. **Q2c check 4** — the cluster-5-is-a-filing-type diagnosis, and your recommendation to discard that cluster.
4. **A Q3a feature.**

## The honest version

It's a cheap cell doing load-bearing work. Thirty strings and four lines of comparison, and it converts *"I built a classifier and used it on everything"* into *"I built a classifier, checked it against 30 documents I read myself, and it agrees on the distinction that matters 28 times out of 30."*

The specific thing it bought you is documented in the `classify_filing()` docstring: an earlier version read *"we expect to report top-line results in late fourth quarter 2021"* as a quarterly report and misfiled a genuine Theravance announcement. That was caught **by** this validation. Without the cell, that bug ships.

And it's the reason the "only 6 of 30" claim is worth anything. Reported alone it's an anecdote about 30 filings. Reported after establishing the classifier agrees 28/30, it generalises.

## Where I'd push back on it instead

The cell isn't the weak part. The weak part is the asymmetry I mentioned: this hand-reading is stored as auditable data, while the *label-fairness* reading — your 24/30, which is closer to what the rubric's hurdles are actually about — exists only as category totals in a markdown table. If you were going to spend effort anywhere in this section, spend it there, not on removing cell 10.

## You  _06:54_

Okay just to understand what the cell is doing, hand_labelled is what I believe each of the documents are and then it checks against if its correct?

## Claude  _06:54_

Yes, that's it. One precision on the word "correct":

**You are the answer key.** `HAND_LABELLED` is treated as ground truth, and the *classifier* is what gets scored. So the cell measures "does `classify_filing()` agree with me", not "is anyone right". If your reading of a document is wrong, the cell counts that as the code being wrong.

```
HAND_LABELLED[i]        your reading of record i        ← treated as truth
sample.filing_kind[i]   what classify_filing() said     ← being tested
```

It then scores the agreement two ways:

- **`exact`** — same one of four categories? → 23/30
- **`announcement_correct`** — do both agree it is / isn't a results announcement? → 28/30

The binary one is higher because all seven mismatches are deck-vs-periodic-report confusions, and both of those are "not an announcement", so they cancel on the question that actually matters downstream.

And the last line counts **your** column rather than the classifier's — "only 6 of the 30 filings are the announcement that carried the news" is your reading, reported after the classifier has been shown to be trustworthy on that distinction.

Two consequences of you being the answer key, both worth being able to say out loud:

- It's only evidence if you labelled the 30 **before** seeing `filing_kind`. Otherwise it's circular. Nothing in the notebook records that ordering, so you'd need to state it.
- The list is position-coupled to `sample`. Change the seed, the strata, or the sort order and the 30 strings silently attach to different filings — no error, just a meaningless score.

## You  _06:56_

How do I check if these hand labelled are correct

## Claude  _06:56_

The strongest check is one that doesn't depend on either your reading or the classifier. 8-K filings carry structural metadata — Item numbers and the EDGAR document filename — that state what the document is. Let me pull those.

<details><summary>tools run</summary>

- `Bash: Extract Item codes and document filenames for all 30`
- `Bash: Check the two ambiguous records`

</details>

## Claude  _06:58_

Use the filing's own structural metadata — it's objective, and independent of both your reading and the classifier.

## Three signals, in order of reliability

**1. The Item number.** Every 8-K declares which SEC item it's filed under:

| Item | Means | Implies |
|---|---|---|
| **2.02** | Results of Operations and Financial Condition | periodic report (earnings) |
| **7.01** | Regulation FD Disclosure | deck / FD update |
| **8.01** | Other Events | usually a results announcement, sometimes other |
| 9.01 | Financial Statements and Exhibits | present in almost all — ignore |

**2. The lead document filename**, which sits in the first line of `filing_text` — `exel8-kq22018earningsrelea.htm`, `tnxp-8k_03182019.htm`, `ex99-01.htm | CORPORATE PRESENTATION BY THE COMPANY`. Filers name these descriptively.

**3. The exhibit headline.** For filings where the stored text starts at `EX-99.1`, the first line is the press release headline — *"Immunic, Inc. Reports Second Quarter…"*, *"BIOGEN REPORTS FO…"*. That settles it immediately.

## What this found on your 30

I ran it across all of them. **The structural evidence largely backs your reading and indicts the classifier.**

| idx | ticker | you said | code said | Items | verdict |
|---|---|---|---|---|---|
| 10 | TNXP | deck | periodic | **7.01** | **you're right** |
| 14 | TNXP | deck | periodic | **7.01** | **you're right** |
| 21 | TCRT | deck | periodic | 8.01 | **you're right** — text says "will present… at R&D Day" |
| 18 | TNXP | deck | periodic | **2.02 + 7.01** | genuinely both; defensible either way |
| 20 | TBPH | deck | other | exhibit-only | needs your read |
| 23 | NBIX | periodic | results ann. | none | needs your read |
| 12 | TBPH | results ann. | deck | **7.01** | **check this one** |

**Record 12 is the one to look at again.** It opens *"Item 7.01. Regulation FD Disclosure"* — furnished, not filed. Your label says results announcement; the Item code says Reg FD. Companies do furnish topline data under 7.01, so it's arguable, but this is the one where the structure disagrees with you rather than with the code.

Record 23 (Neurocrine, 2003) has no Item numbers at all — the 2003 8-K format predates them. Falls back on reading.

## An important data fact this surfaced

For about a third of your sample, **the stored `filing_text` is the exhibit only, not the 8-K body** — records 0, 3, 5, 7, 9, 15, 17, 22, 28 all begin at `EX-99.1`. That's why they have no Item numbers, and why `RE_COVER` never fires on them. Worth knowing generally: the corpus isn't uniform in what part of the filing it captured.

## What I'd do

Re-check the seven above against `q1a_sample_filings/`, plus the five I flagged earlier for text loss (4, 6, 17, 21, 25) — record 21 is on both lists, so that's eleven filings. For each, the Item number gives you a defensible answer in seconds; only fall back on reading where there isn't one.

If any hand label changes, the 23/30 and 28/30 both move and the cell recomputes them automatically — that's the advantage of `HAND_LABELLED` being data.

Want me to add this as a cell in the notebook? It would sit well right after cell 10: an independent structural cross-check of the hand labels, which is exactly the kind of thing the top rubric band rewards — and it would make your answer to "how do you know your readings are right" a table rather than an assertion.

## You  _07:00_

where does filling_kind come from

## Claude  _07:00_

It's derived in your own code — **not** from the database. Three steps:

**Cell 5** loads only two columns from SQLite:
```python
filing_txt = pd.read_sql("SELECT accession, filing_text FROM filing_text", conn)
```
So at this point `filing_txt` has just `accession` and `filing_text`. There is no `filing_kind` column in the database at all.

**Cell 6** creates it, at the bottom of the helpers cell:
```python
filing_txt["clean"] = filing_txt.filing_text.map(clean_filing_text)
_kinds = [classify_filing(c, r) for c, r in zip(filing_txt.clean, filing_txt.filing_text)]
filing_txt["filing_kind"]  = [k for k, _ in _kinds]
filing_txt["n_prior_refs"] = [n for _, n in _kinds]
```
`classify_filing()` returns a tuple, so this unpacks it into two new columns — one row per filing, 3,794 rows.

**Cell 8** attaches it to the sample:
```python
sample = sample.merge(filing_txt[["accession", "filing_kind", "n_prior_refs"]],
                      on="accession", how="left")
```
Joined on `accession`, so every classification row picks up the document type of the filing it sits in.

## Why that matters

`filing_kind` is **your output, not given data**. The six outcome categories (`positive`, `negative`, …) come from the database and were produced by the LLM pipeline in methodology §5. `filing_kind` was produced by a regex you wrote, in cell 6, from the filing text.

That's the whole reason cell 10 exists, and why the Item-number cross-check is worth doing. Nobody has to validate `outcome` — it's the thing you're evaluating. But `filing_kind` is a tool you built and then used on all 3,794 filings, so it needs evidence behind it.

It's also why the `RE_TAIL` fix moved it: `classify_filing()` reads `clean`, so changing the cleaning changed the classification for ~450 filings.

Downstream it appears in cells 8, 9, 16, 17, 21, 23, 67 (Q2c cluster 5) and 83 (a Q3a feature) — all from this one assignment in cell 6.

## You  _07:04_

is exhibit 99.1 always a result_annoucement

## Claude  _07:04_

No — 99.1 is just a numbering slot, not a content type. Let me show you from your own data.

<details><summary>tools run</summary>

- `Bash: Check what Exhibit 99.1 actually contains across the corpus`

</details>

## Claude  _07:06_

**No.** "Exhibit 99.1" just means "the first additional exhibit attached to this 8-K". It's a numbering slot, not a content type — whatever the company attached lands there.

## In your own corpus

90% of filings (3,424 of 3,794) contain an Exhibit 99.1. What they turn out to be:

| `filing_kind` | filings | share |
|---|---|---|
| periodic report | 1,622 | **47.4%** |
| results announcement | 955 | 27.9% |
| deck / FD update | 443 | 12.9% |
| other | 404 | 11.8% |

The **most common** thing in an Exhibit 99.1 is an earnings release, not a trial result.

Twelve random examples, showing what actually sits behind the marker:

```
Eli Lilly and Company — Lilly Q1 2021 sales and earnings      → earnings
Abeona Therapeutics 2018 R&D Day                              → deck
Femasys Appoints John Canning as Chief Operating Officer      → personnel
Dermata Therapeutics, Inc. Re[ports…]                         → earnings
acumen_corporate-deck — Corporate Presentation November       → deck
Ocuphire Presenting New Data and Updates                      → conference data
Corcept Therapeutics announces…                               → press release
```

An appointment announcement and an R&D-day deck sit in exactly the same exhibit slot as a topline readout.

## In your 30-record sample

Three of the exhibit-only filings make the point on their own:

- record 5, IMUX, `e621857_ex99-1.htm` → *"Immunic, Inc. Reports Second Quarter…"* — **earnings**
- record 15, BIIB, `exhibit991-q42021pressrele.htm` → *"BIOGEN REPORTS FO[URTH QUARTER]…"* — **earnings**
- record 28, TNXP, `ex99-01.htm` → *"CORPORATE PRESENTATION BY THE COMPANY"* — **deck**

## What this means for the check I suggested

I should be precise, because it affects the advice I gave you. The reliable structural signals are:

- **The Item number** — 2.02 / 7.01 / 8.01. This is genuinely diagnostic, because it's the company declaring under which rule they're filing.
- **The exhibit's own headline** — *"Reports Second Quarter"*, *"Corporate Presentation"*, *"Announces Topline Results"*. Diagnostic, because it's a title.

**The exhibit number itself carries no information.** Use 99.1 only to locate where the substance begins — which is exactly what my `RE_TAIL` fix uses it for — never to infer what the substance is.

Related and worth remembering: this is also why the `RE_EXIDX` rule removes the *exhibit index* (the "Exhibit No. / Description" table listing "99.1 Ladenburg Presentation") but not the exhibit itself. The index is boilerplate; the exhibit is the filing.

## You  _07:10_

I cant determine id 20 either

<details><summary>tools run</summary>

- `Bash: Read the start of record 20`

</details>

## Claude  _07:11_

You're right, and the evidence is clear.

<details><summary>tools run</summary>

- `Bash: Confirm why the classifier missed the deck`

</details>

## Claude  _07:12_

It's a deck — your reading is right, the classifier is wrong. Record 20 is **`deck / FD update`**.

## The tells

```
EX-99.1 … EXHIBIT 99.1 THERAVANCE BIOPHARMA®, THERAVANCE®, the Cross/Star logo …
are registered trademarks … © 2025 Theravance Biopharma. All rights reserved.

Theravance Biopharma Ampreloxetine KOL Event   December 8, 2025
Welcome and Opening Remarks   Rick Winningham   Chief Executive Officer
3
Forward Looking Statements   This presentation contains certain "forward-looking" statements…
```

Four independent signals, none of which appear in a press release:

- **A trademark/copyright slide first.** Decks open with a legal title slide; press releases never do.
- **"KOL Event"** — a Key Opinion Leader event, i.e. a live presentation to analysts and clinicians.
- **A speaker attribution and an agenda item** — *"Welcome and Opening Remarks, Rick Winningham, Chief Executive Officer"*. Press releases don't have agendas.
- **A bare `3`** — a slide number, mid-sentence in the extracted text.

Plus the word *presentation* itself in "This presentation contains…".

## Why the code called it `other`

I checked all three patterns against the body — **all three miss**:

```
RE_FIN   → False
RE_RES   → False
RE_DECK  → False        → falls through to "other"
```

`RE_DECK` requires `(corporate|company|investor|business)` immediately before `(presentation|deck|update|overview)`, or an `Item 7.01` / `Regulation FD Disclosure` marker. This filing says **"KOL Event"**, not "corporate presentation" — and because the stored text is the exhibit only, there's no Item 7.01 header to fall back on. The single occurrence of "presentation" is in *"This presentation contains"*, which doesn't match the required adjective.

So it's a vocabulary gap, not a logic error. `RE_DECK` recognises decks that call themselves corporate presentations and misses ones that call themselves a KOL Event, an R&D Day, or an Analyst Day.

## Where that leaves your tally

Your hand label stands, and **this becomes a genuine classifier miss** rather than an ambiguous case. The running score on the seven disagreements: records 10, 14, 21 and now 20 are all cases where you're right and the code is wrong. Record 12 is the one where the Item code (7.01) argues against your label. Records 18 and 23 are still open.

Worth noting for your write-up: four of the seven mismatches are the classifier under-detecting decks, and record 20 shows a specific, nameable cause. That's exactly the "systematic patterns" framing the rubric's top band asks for — better than listing seven one-off disagreements.

If you want, `RE_DECK` could be widened with `KOL Event|R&D Day|Analyst Day|Investor Day|webcast` — but the same caution applies as before: it changes `filing_kind` and everything downstream. Given you have a full re-run pending anyway, this is a cheaper change to fold in than the others, if you want it.

## You  _07:13_

Lets leave it for now

<details><summary>tools run</summary>

- `Bash: Confirm everything is committed and pushed`

</details>

## Claude  _07:13_

Fine. Everything is committed and pushed — working tree clean, `rz_working` in sync at `35ae798`.

## Where things stand

**Done and pushed:**
- `RE_TAIL` fix — the signature block no longer takes the exhibit with it
- Q1 prose updated to the re-measured numbers (17.5% cleaning, 62.9%/46.3%, 2,019 flagged, and the 589→551 union correction)
- `range(0, 29)` → `range(30)` in cell 9
- The `head`/`body` window sensitivity cell and write-up in Q1a
- Merged cleanly with your full 30-record `show()` run

**Open, in rough priority order:**

1. **Full re-run** — Q2 and Q3 outputs and prose still reflect the pre-fix cleaning, and the new sensitivity cell is unexecuted. Needs Colab or your machine. Q2c check 4 (cluster 5) is the specific thing to re-verify, since it reads `filing_kind`.
2. **Re-read 11 filings** — records 4, 6, 17, 21, 25 (heavy text loss) and 10, 12, 14, 18, 20, 23 (classifier disagreements). Records 4, 8 and 20 are already resolved: labels correct, and 20 is a deck as you read it. Record 12 is the one where the Item 7.01 code argues against your label.
3. **Three documented-limitation paragraphs** you have measurements for but haven't written: the sentence-filter loss (33% at `hi=400`, decks 52%), `RE_SAFE` over-deleting in 151 filings, and `RE_DECK` missing "KOL Event"-style decks.
4. **Q4, Q5, the video link, and the AI-use disclosures** — still template or draft.

The scratch files (`q1a_sample_filings/`, `dump_q1a_sample_filings.py`) are committed, so the sample dump survives this session. `ctgov.db` is gitignored and will be gone when the container recycles — it re-extracts from the zip.

Say the word when you want to pick any of it back up.

## You  _07:14_

Okay so the next part of the cell the annoucements what is happening here

<details><summary>tools run</summary>

- `Bash: List current cell indices after the insertion`
- `Bash: Print the document-type / announcements analysis cell`

</details>

## Claude  _07:15_

This is cell 18 — the announcements-vs-everything-else analysis. It's the cell that takes the hypothesis from your 30-filing reading and tests it on all 3,794 filings.

## The hypothesis being tested

The banner comment states it as a falsifiable prediction:

> *"the label describes the trial correctly, but the filing it is attached to is not the day the news reached the market. **If that is right**, disagreement should depend on what kind of document the 8-K is and on how much restatement language it contains."*

That's the right structure — a prediction that could fail, not a description looking for support.

## What it computes

```python
fs = filing_sum.merge(filing_txt[["accession","filing_kind","n_prior_refs"]], on="accession")
fs["expected"] = fs.primary_outcome.map(EXPECTED)      # positive→+1, negative→−1
d = fs.dropna(subset=["expected","car_3day"])
d["agrees"] = np.sign(d.car_3day) == d.expected
```

`EXPECTED` maps each directional label to the sign the market *should* have moved. `agrees` is then a simple boolean: did the price go the way the label implies? Note the `dropna` — `no_result` and `inconclusive` have no direction, so they drop out. This works at **filing** level (`filing_summary`), not record level.

Then three cuts:

**1. By document type** — the headline result:

| | n | sign agreement | median \|CAR\| |
|---|---|---|---|
| results announcement | 673 | **62.9%** | 11.4% |
| deck / FD update | 216 | 53.2% | 6.9% |
| other | 126 | 49.2% | 8.9% |
| periodic report | 741 | **46.3%** | 5.1% |

**2. Document type × label** — the interaction, which is where the strongest number lives:

|  | negative | positive |
|---|---|---|
| results announcement | **0.91** | 0.57 |
| periodic report | 0.53 | 0.44 |

A `negative` label in a genuine announcement agrees with the market 91% of the time. The same label in a quarterly report, 53% — a coin toss.

**3. By restatement count** — an *independent* confirmation:

```
0 backward refs   n=1207   56.6%
1-2               n= 424   49.5%
3-5               n= 105   38.1%
```

## Why the third cut matters most

This is the part worth understanding, because it's what makes the argument hold.

Cuts 1 and 2 use `filing_kind` — your own regex classifier. If that classifier were systematically wrong, the whole finding could be an artefact of it. Cut 3 uses `n_prior_refs`, which comes from a completely different mechanism: counting phrases like "previously announced" in the **raw** text, with no reference to document type at all.

Both point the same way, and cut 3 is monotonic across three of four buckets. Two independent measures of "this filing is a restatement" both predict falling sign agreement. That's much harder to dismiss than either alone — and it's why the finding survived the `RE_TAIL` fix and every `head` window I tested.

## What the numbers actually mean

Median absolute reaction falls from 11.4% in announcements to 5.1% in periodic reports. So it isn't that periodic reports produce *wrong-signed* big moves — they produce **small, noisy moves**, because the trial news is old and the price is reacting to earnings instead. Sign agreement drifts toward 50% for the same reason a coin does.

That's the precise claim your Q1d summary makes: *"the label describes the trial correctly, but the price move beside it reacts to something else, usually earnings."* This cell is where it's established.

## Two caveats worth knowing

- **`n=126` for `other`** is small, and that bucket is heterogeneous by definition — I wouldn't lean on its 49.2%.
- **The `6+` restatement bucket breaks the monotone** (n=20, 50.0%). The prose in cell 21 handles this correctly by quoting the 56.6%→38.1% range and stopping at `3-5`, rather than claiming a clean monotone across all four. Just be ready to say why if asked: n=20.

## You  _07:16_

sorry no this is still in cell 10, it says agreement on annoucement vs not

## Claude  _07:16_

That's the line just below `exact`. Let me show what it does on your actual 30.

<details><summary>tools run</summary>

- `Bash: Build the 2x2 for the binary agreement`

</details>

## Claude  _07:17_

Right, sorry — that's the second score inside cell 10.

```python
check["announcement_correct"] = ((check.filing_kind == "results announcement") ==
                                 (check.read_by_hand == "results announcement"))
```

## What it's doing

It collapses four categories into a **yes/no** on one question — *is this a results announcement?* — for each side, then checks whether the two answers match.

```
(code says announcement?)  ==  (you say announcement?)
        True/False                  True/False
```

Because it's comparing two booleans, it's `True` in **both** matching cases: both said announcement, *or* both said not-an-announcement. So `deck` vs `periodic report` counts as agreement — both are "not an announcement", and the disagreement is invisible to this measure.

## On your 30

```
                     you say announcement
                       False    True
code says   False        23       1
            True          1       5
```

23 + 5 = **28 agree**, hence 28/30.

And here is why it's higher than the 23/30 exact score — five of the seven exact mismatches never cross the boundary:

| idx | ticker | code said | you said | crosses? |
|---|---|---|---|---|
| 10 | TNXP | periodic report | deck | no |
| 14 | TNXP | periodic report | deck | no |
| 18 | TNXP | periodic report | deck | no |
| 20 | TBPH | other | deck | no |
| 21 | TCRT | periodic report | deck | no |
| **12** | TBPH | deck | **results announcement** | **yes** |
| **23** | NBIX | **results announcement** | periodic report | **yes** |

## Why the notebook bothers with two scores

Nothing downstream ever asks "is this a deck or a quarterly report?" Everything asks "is this an announcement?" — the Analysis 2 split, `S5_not_an_announcement` in Q1b, the cluster-5 diagnosis in Q2c. So the binary is the number that licenses those uses, and 28/30 is the honest figure to quote for them. The exact 23/30 is context, and reporting both rather than only the flattering one is the right call.

## The two that cross are exactly the two still unresolved

Records 12 and 23 are the only errors that matter — and they're the same two left open from the Item-number check. Record 12 opens *"Item 7.01. Regulation FD Disclosure"*, which argues for the code's `deck` over your `results announcement`. Record 23 is the 2003 Neurocrine filing with no Item numbers at all.

Note they're in opposite directions — one false negative, one false positive — so if you re-read both and changed only one, the 28/30 would move to 29/30; change both and it's 30/30. That's a small enough number of documents to settle definitively, and it's the highest-value re-reading left in the sample.

## You  _10:12_

so which cell comes down to the conclusion of the stratified sample results

<details><summary>tools run</summary>

- `Bash: List markdown headings across Q1`

</details>

## Claude  _10:13_

**Cell 11 — "What reading the 30 filings showed."** That's the conclusion of Analysis 1.

## The structure of Q1a

```
 7  ### Analysis 1: reading a stratified sample against the filings   ← section heading
 8  code    draw the stratified sample (5 per category, n=30)
 9  code    result_sentences() + show() — read each one
10  code    validate classify_filing() against the hand labels
11  ← CONCLUSION OF ANALYSIS 1
12  code    (new) head/body window sensitivity
13  markdown  what that showed
14  code    the boundary test — two filings, same study
15  markdown  what the boundary test showed

16  ### Analysis 2: label vs. sign of abnormal return              ← the whole-dataset analysis
17–20 code
21  ← CONCLUSION OF ANALYSIS 2

37  ## Q1d  ← conclusion of the whole question, for the IR team
```

## What cell 11 contains

The two-judgement table, one row per category:

| Category | Label fair on the text | Filing is the announcement |
|---|---|---|
| positive (5) | 5 | 2 |
| negative (5) | 5 | 2 |
| mixed-positive (5) | 3 | 2 |
| mixed-negative (5) | 5 | 0 |
| inconclusive (5) | 1 | 0 |
| no_result (5) | 5 | n/a |

Which gives the two headline claims — **24 of 30** labels are a defensible reading, and only **6 of 30** filings are the announcement that carried the news — followed by the three failure modes: (1) the label is right but the filing isn't the event, (2) the label attaches to the wrong news within the filing, (3) the label reproduces the sponsor's adjective instead of assessing evidence.

## One thing worth being clear about

Cell 11 is the conclusion of the *sample*. It is not the conclusion of Q1a. The argument is deliberately two-stage:

- **Cell 11** — 30 filings read by hand generate a hypothesis: the labels are accurate but frequently mis-dated.
- **Cell 21** — that hypothesis is then tested on all 3,794 filings, and confirmed by two independent measures (document type, and restatement-phrase count).

That's why the rubric's top band talks about patterns "across the whole sample" — cell 11 alone would be an anecdote about 30 documents; cell 21 is what makes it a finding. Cell 37 (Q1d) then states it in plain language for the IR team.

If you're walking a marker or the video through Q1a, cell 11 is where you say *"here's what I found by reading"*, and cell 21 is where you say *"and here's it holding across the dataset."*

## You  _10:14_

wait how did this table get made

<details><summary>tools run</summary>

- `Bash: Check whether the cell 11 table is derivable from code`

</details>

## Claude  _10:15_

**It was typed by hand.** Cell 11 is a markdown cell — the table is literal text, not output from any code. Nothing generates it and nothing checks it.

That said, the two columns are in very different positions:

## Column 2 — "Filing is the announcement" — is reproducible

I derived it from `HAND_LABELLED`, grouped by outcome category:

```
                n   is_announcement          cell 11 says
positive        5         2                       2  ✓
negative        5         2                       2  ✓
mixed-positive  5         2                       2  ✓
mixed-negative  5         0                       0  ✓
inconclusive    5         0                       0  ✓
no_result       5         0                     n/a
```

Exact match. So that column is typed, but it's *backed* by data — anyone can regenerate it, and if you change a hand label the table can be checked against the new value.

## Column 1 — "Label fair on the text" — has nothing behind it

`5, 5, 3, 5, 1, 5` → 24. Those six numbers exist **only** as characters in a markdown cell. There is no list, no column, no code. Which means:

- Nobody can tell *which* 6 records were judged unfair — only that 2 were `mixed-positive` and 4 were `inconclusive`.
- It can't be recomputed, so it can't be verified.
- If your re-reading changes a judgement, you edit the number by hand and hope the prose in cells 11, 21 and 37 stays consistent.

This is the asymmetry I flagged a while back, and now it's precise: **the table is half-generated and half-asserted.** The 28/30 in cell 10 is reproducible; the 24/30 in cell 11 is not — and the 24/30 is arguably the number closer to what the rubric's hurdles actually ask about ("examines a sample of ≥20 classifications against the original filing text and states what the examination found").

## Worth knowing about the numbers themselves

The `inconclusive` row says only 1 of 5 labels was fair — the lowest in the table — and the prose explains why: four of the five describe trials that hadn't reported at all, so they overlap `no_result` rather than meaning "unclear result". That's a real finding, and it's the sort of thing a marker may well ask you to point at in the filings. Right now you'd have to find those four records from memory.

## The fix, if you want it

Same shape as `HAND_LABELLED` — a second list beside it:

```python
HAND_LABEL_FAIR = [True, True, ...]      # 30 booleans
```

Then cell 11's table becomes a `groupby` over both columns, generated rather than typed, and the 24/30 recomputes itself whenever a judgement changes. It also gives you somewhere to record the outcome of the eleven re-reads still outstanding.

I offered this earlier and you said to leave it — still happy either way. It's about ten minutes of work and it converts your weakest evidence into your second-strongest.

## You  _10:15_

no sorry as in how did we get these numbers

## Claude  _10:15_

Honest answer: **I can't tell you from the repo, and that's the point.** Let me show you what evidence exists.

<details><summary>tools run</summary>

- `Bash: Check the AI-use disclosure and commit history`
- `Bash: Check AI logs and when the table text was introduced`

</details>

## Claude  _10:16_

Here's what the repository can and cannot tell us.

## What's recorded

The table entered the notebook in commit **`a5fa948 "question 1 by claude"`** — it arrived fully formed, numbers already in place. There is no earlier commit with a partial version, no working file, no per-record list.

The AI-use note in cell 38 describes the division of labour as:

> "Claude … was used across Question 1: to write and debug the cleaning, sampling, flagging and vectorisation code, **to extract result-relevant excerpts from the filings so they could be read**, and **to draft the commentary**."

So the excerpts were machine-produced, and the commentary was machine-drafted. Cell 11 *is* commentary. Whether the six judgements in column 1 came from you reading the 30 filings, or were drafted by the model from the excerpts and then accepted, **is not recorded anywhere in this repository, and I cannot determine it.** I'm not going to guess.

## Two things that follow

**1. The disclosure currently claims something untrue.** Cell 38 ends with *"Full conversation logs are in `ai_logs/`."* `ai_logs/` contains exactly one file — `2026-09-02_general_claude_setup.md`, the setup session. The Question 1 conversation isn't there. As it stands, the notebook points a marker at evidence that doesn't exist, and `compile_ai_logs.py` hasn't been run.

That's fixable but only by you: either recover the transcript into `ai_logs/`, or use `write_manual_note()` from the Setup cell to record honestly that it couldn't be saved. The brief explicitly provides for the second option — a missing log recorded honestly is not a breach; a silent gap is.

**2. Column 2 is verifiable, column 1 isn't.** I confirmed earlier that "Filing is the announcement" (2, 2, 2, 0, 0) reproduces exactly from `HAND_LABELLED`. So that half of the table has an artefact behind it. The "Label fair" column (5, 5, 3, 5, 1, 5 → 24) has none.

## What I'd suggest

You're the only person who knows whether you read those 30 filings. If you did, nothing here is a problem — but the notebook has no record of it, so I'd make one: fill in the `HAND_LABEL_FAIR` list I proposed, working from `q1a_sample_filings/`. That converts a typed number into a reproducible one, and it's the same eleven filings you already need to re-read.

If you haven't read them yet, then read them now and let the numbers land where they land. If the 24 becomes 22 or 26, that's a better answer than 24 with nothing behind it — and the rubric's hurdle is that you *examined* the sample and *stated what you found*, not that you found any particular thing.

Either way, cell 38 needs rewriting in your own words before submission. It says so itself, in bold, at the top.

I'd treat this as the highest-priority item left in Q1 — above the re-run. Want me to add the `HAND_LABEL_FAIR` scaffold so there's somewhere to put the judgements as you work through the filings?

## You  _10:44_

So to examine the 30 fillings, I should read them to see if its positive or not and then check if its been tagged correctly

## Claude  _10:45_

Nearly — two refinements that matter.

## It's not "is it positive", it's "is this label defensible"

You're not judging the news yourself and seeing if you'd have said the same. You're asking: **does the filing's text support the category the pipeline assigned, under the documented definitions?**

| Category | Test |
|---|---|
| `positive` | Primary endpoint met with statistical significance, **or** unambiguous statement of success |
| `negative` | Primary endpoint missed, stopped for futility, or programme discontinued |
| `mixed-positive` | Some endpoints met, others missed; overall favourable |
| `mixed-negative` | Some met, overall unfavourable |
| `inconclusive` | Results reported but insufficient to determine direction |
| `no_result` | No trial outcome data at all |

This distinction is what produced the `mixed-positive` row (3 of 5 fair) and `inconclusive` (1 of 5). Those weren't cases where the news was misread — they're cases where the label doesn't meet its own written definition. Q32 Bio's "encouraging clinical activity" is called `mixed-positive`, but nothing in the filing states an endpoint outcome. That's a fail on definition, not on sentiment.

## Check the right drug first

Record 8 is the cautionary case: the filing says "met its primary endpoint", but that's **dupilumab**, and record 8 is **suptavumab** — which missed and was discontinued. Multi-drug filings are common. Read `drug_name` from the header, then find what the filing says about *that* drug.

## Don't look at the CAR while judging

The dump file header shows `CAR[-1,+1]`. **Ignore it for this judgement.** Analysis 2 tests the label against the market reaction as an independent check — if your reading is influenced by knowing the price fell 68%, that check becomes circular and the whole two-stage argument collapses.

Judge from the filing text alone.

## Two judgements per record

Record them separately, because they answer different questions:

1. **Is the label fair on the text?** → the 24/30, currently unbacked
2. **Is this filing the announcement that carried the news?** → `HAND_LABELLED`, already stored

A record can be "label fair, but not the announcement" — that's the single most common pattern in your sample, and the whole finding of Q1a.

## Practical order

For each of the 30, open `q1a_sample_filings/NN_*.txt`:

1. Header → note `drug_name` and the assigned `outcome`. Skip the CAR line.
2. Search the raw text for the drug name; read what's said about it.
3. Judge against the definition above → fair / not fair.
4. Separately: is this the document that broke the news, or a restatement? (Item 2.02 → periodic; 7.01 → deck; "previously announced" → restatement.)

If a marker asks "how did you examine them", the answer is that procedure plus the file you worked from — which is much stronger than a number in a markdown table.

Say the word and I'll add the `HAND_LABEL_FAIR` list so your judgements land in code rather than prose.

## You  _10:47_

I got the other conversation onto the web version, can  you look and see if theres anything about the analysis for the first part

<details><summary>tools run</summary>

- `Bash: Fetch and check for new commits on the remote`
- `Bash: Inspect the new remote change`

</details>

## Claude  _10:48_

That commit is just Jupyter stamping cell IDs on my two new cells — an artifact of opening the notebook in the web editor. No log file arrived. Let me check whether you mean another session.

<details><summary>tools run</summary>

- `mcp__Claude_Code_Remote__list_sessions`
- `ToolSearch`

</details>

## Claude  _10:48_

Two findings, and neither gets me the conversation.

**The repo change isn't a log.** Commit `4ec2f89` adds exactly two lines — `"id": "afaaebec"` and `"id": "7470b804"` — Jupyter stamping cell IDs onto the two cells I inserted when the notebook was opened in the web editor. `ai_logs/` still contains only `2026-09-02_general_claude_setup.md`.

**I can't read another session's transcript.** I can list your sessions and see their metadata, but there's no tool available to me that returns another session's messages. I checked rather than assuming.

## What I can see

Your account has these sessions on this repo:

| Session | Created | Status |
|---|---|---|
| Work validation explanation | Sep 6 04:13 | this one |
| DSA_26S2 assignment question 3 | Sep 5 13:02 | idle, disconnected |
| DSA_26S2 assignment question 2 | Sep 5 09:54 | idle, disconnected |
| Running 9 tasks on the side | Sep 4 11:34 | idle, connected |
| GitHub repository integration | Sep 1 14:13 | idle |

There's no session titled for Question 1. Q1 landed in commit `a5fa948` on Sep 5 at 00:53, which sits between "Running 9 tasks on the side" (Sep 4) and the Question 2 session (Sep 5 09:54) — so **"Running 9 tasks on the side" is the likely home of the Q1 work**, but that's inference from timestamps, not something I've verified.

## How to get it to me

Either works:

- **Paste** the relevant part of the conversation into this chat.
- **Commit it** — save the transcript as `ai_logs/2026-09-05_Q1_claude.md` and push. That's where it needs to end up anyway for `compile_ai_logs.py`, so this is the version that does double duty.

Then I can read it and tell you specifically whether it shows the 30 filings being read, and by whom.

## Separately — this listing is useful to you

Those session titles and timestamps are themselves a record of your AI use. Whatever we find about the Q1 reading, you have four sessions to export into `ai_logs/` before submission, and cell 38 currently claims they're already there. Exporting them fixes both the disclosure and the question you're asking now.

## You  _10:49_

Okay I will save the logs later, lets work out how to solve the first dot point in question 1a so I can make sure I have verified the tags properly

<details><summary>tools run</summary>

- `Bash: Extract Question 1a from the assignment brief`
- `Bash: Extract the Q1a dot points`

</details>

## Claude  _10:50_

Got the exact wording. Let me be precise about what it asks, because there's a requirement in there that's easy to miss.

## The first dot point, broken into its four requirements

> • Using a random seed equal to your member ID, select a stratified random sample of at least 20 classified outcomes, ensuring the sample includes examples of each of the six documented outcome categories. Examine each sampled classification **against the original 8-K filing text** to assess **whether the classification is accurate** *and* **whether the category boundaries (e.g. between positive and mixed-positive) are applied consistently.**

| # | Requirement | Status |
|---|---|---|
| 1 | Seed = member ID | ✅ `MEMBER_ID = 40100` |
| 2 | Stratified, ≥20, all six categories | ✅ 30, five per category |
| 3 | Each examined **against the original filing text** → is it accurate? | ⚠️ the 24/30, no per-record backing |
| 4 | Are **category boundaries applied consistently** from one filing to the next? | ⚠️ partly — cell 14 tests two filings |

**Requirement 4 is a separate question, not a rephrasing of 3.** It's not "is this label right" but "when two filings present the same situation, does the pipeline draw the positive/mixed-positive line in the same place both times?" The rubric restates it: *"whether the boundaries between adjacent categories were applied the same way from one filing to the next."*

Cell 14 does address it — two filings describing the same study and the same missed endpoint, labelled differently. That's a good demonstration, but it's one pair. Requirement 4 wants the judgement made across the sample.

Also note: **"against the original 8-K filing text"** — the brief says *original*. That's the raw text in `q1a_sample_filings/`, not the cleaned excerpts. Given what we found about decks and the sentence filter, that wording is on your side.

## The method

For each of the 30, record three things as data:

1. **`fair`** — is the assigned outcome defensible on what the filing says about *this drug*, under the documented definition? (Check the drug first — record 8.) Don't look at the CAR.
2. **`boundary`** — does this record sit on an adjacent-category boundary (`positive`/`mixed-positive`, `inconclusive`/`no_result`, `mixed-negative`/`negative`)? If so, is it drawn consistently with the others? → `ok` / `inconsistent` / `n/a`
3. **`note`** — the sentence your judgement rests on. This is what makes it auditable.

Then cell 11's table generates itself from those, instead of being typed.

The `boundary` field is what turns your existing observations into requirement 4 rather than leaving it implicit — you already know `inconclusive` is functioning as a second `no_result` (4 of 5 cases) and that `mixed-positive` follows the sponsor's framing. Those *are* boundary inconsistencies; they're just currently asserted in prose rather than recorded per record.

Let me build the scaffold so your reading lands in code.

<details><summary>tools run</summary>

- `Bash: Build and test the reading-record scaffold`
- `Bash: Verify the table renders with partial fills`

</details>

## Claude  _10:52_

The re-exec resets `READING` — my test was wrong. Testing the table path properly.

<details><summary>tools run</summary>

- `Bash: Test the generated table with three rows filled`
- `Bash: Fix count formatting and re-test`

</details>

## Claude  _10:53_

Works. Inserting it after cell 10, where `HAND_LABELLED` lives.

<details><summary>tools run</summary>

- `Bash: Merge remote cell ids and insert the reading cell`
- `Bash: Verify and push the reading scaffold`

</details>

## Claude  _10:55_

Pushed (`4ec2f89..7abf12d`). Cell 11 is now the reading record; the old typed table moved to cell 12.

## How to work through it

Open `q1a_sample_filings/NN_outcome_ticker_accession.txt` for each record and fill one line:

```python
READING[0] = dict(fair=True,  boundary="ok",
                  note="Sunosi met its primary endpoint in the Phase 3 trial, p<0.001")
```

Run the cell after each batch — it reports progress, generates the category table over what's done, and lists any record you marked unfair with its note. No need to finish all 30 before it's useful.

## What to judge, per record

**`fair`** — does the filing's text about *this drug* satisfy the documented definition of the assigned category? Check the drug name in the header first (record 8's "met its primary endpoint" belongs to dupilumab, not suptavumab). **Don't read the CAR line** — Analysis 2 tests these labels against the market reaction, and that test only means something if your reading didn't use it.

**`boundary`** — this is the requirement that was thinnest, so it's worth being deliberate. Mark `"inconsistent"` when the same situation is labelled differently elsewhere in your sample. You already have two candidates:

- **`inconclusive`** — four of the five are trials that hadn't reported at all. The definition says "results reported but insufficient to determine direction", which is a different thing from "no results yet". Those four are arguably `no_result`, and that's the `inconclusive`/`no_result` boundary being drawn inconsistently.
- **`mixed-positive`** — records 10, 11, 12, 14 are worth comparing directly. If two of them present comparable endpoint outcomes and only one is `mixed-positive`, that's the `positive`/`mixed-positive` boundary the brief names explicitly.

Use `"n/a"` for `no_result` records, which carry no directional claim to place.

**`note`** — quote the sentence. This is what converts "I read them" into evidence a marker can check.

## A suggested order

1. The five with heavy text loss — **4, 6, 17, 21, 25** — read these from the raw section of the file, since the excerpts are unreliable for them.
2. The `inconclusive` block — **20–24** — where the boundary question is sharpest.
3. The `mixed-positive` block — **10–14** — the boundary the brief names.
4. The rest.

Records 4, 8 and 20 we resolved together already: 4 is `fair=True` (deck states "Met Primary Study Objectives"), 8 is `fair=True` (suptavumab missed and was discontinued), and 20's document type is a deck, though its `inconclusive` label still needs your judgement.

Once you're through, cell 12's typed table should be replaced by the generated one, and the 24/30 in cells 12, 22 and 38 updated to whatever you actually find.

## You  _11:06_

so how am i suppose to fill in this reading record

## Claude  _11:06_

Let me walk one record end to end so the loop is concrete.

<details><summary>tools run</summary>

- `Bash: Pull the judgeable text for record 0`

</details>

## Claude  _11:07_

Here's the loop, worked on record 0.

## 1. Open the file

`q1a_sample_filings/00_positive_AXSM_0000950170-22-019151.txt`

Header says: drug = **Sunosi (solriamfetol)**, assigned outcome = **positive**. Skip the CAR line.

## 2. Find what the filing says about that drug

Search the raw section for the drug name. Here the headline does the work:

> *"Axsome Therapeutics Announces Sunosi® (Solriamfetol) **Meets Primary Endpoint** … **Statistically significant** improvement in cognitive function … compared to placebo (**p=0.009, primary endpoint**)"*

## 3. Test against the definition

`positive` = *"Primary endpoint met with statistical significance, or unambiguous statement of success."*

Primary endpoint met ✓, statistically significant ✓, p-value stated ✓. → **`fair=True`**

## 4. Ask the boundary question

Is this near the `positive`/`mixed-positive` line? No — every reported endpoint hit (p=0.009, p=0.002, p=0.004), nothing missed. Nothing to compare. → **`boundary="ok"`**

## 5. Type the line

In cell 11, under the comment block:

```python
READING[0] = dict(fair=True, boundary="ok",
                  note="Meets Primary Endpoint; DSST RBANS p=0.009 vs placebo")
```

Then run the cell.

## The judgement calls will look like this

Not every record is as clean as record 0. The two shapes to watch for:

**A `positive` where nothing was actually tested.** If the filing says "encouraging preliminary data" from a small open-label cohort with no p-value, the definition isn't met — it wants a met endpoint *or* an unambiguous statement of success. That's `fair=False`, and if a comparable filing elsewhere in the sample got `mixed-positive` for the same kind of language, it's also `boundary="inconsistent"`.

**An `inconclusive` where the trial hasn't reported.** The definition is "results reported but insufficient to determine direction." A filing announcing an upcoming readout has no results at all — that's `no_result` territory. Mark `fair=False, boundary="inconsistent"`, because the `inconclusive`/`no_result` line is being drawn in two different places.

## Practical notes

- **Use Ctrl-F on the drug name** rather than reading 20,000 characters. The result sentences cluster around it.
- **Read the headline first.** For press releases it usually settles the question in one line, as above.
- **Quote, don't paraphrase, in `note`.** The quote is the evidence.
- **You can fill them in any order** — run the cell whenever, it summarises what's done and ignores the rest.
- **`fair` is about the label, not the timing.** A correct label on a three-month-old restatement is still `fair=True`. Timing is the separate `HAND_LABELLED` column.

Want me to print the same "drug name + endpoint sentences" extract for the other 29, so you have all of them in one place rather than searching each file? That's the mechanical part, and it doesn't touch the judgement — you'd still be reading the filing's own words and deciding.

## You  _11:09_

can you read all 30 for me

## Claude  _11:09_

I can't fill in the `fair` judgements for you. That column is the assessed work — the rubric hurdle is that *you* examined the filings and stated what you found, and the notebook records it as "my reading of the document". If I produce 30 verdicts and you paste them in, the 24/30 stops being an examination you can stand behind, and cell 38's disclosure becomes harder to write honestly rather than easier.

What I can do is the mechanical half, which your AI-use note already covers ("extract result-relevant excerpts from the filings so they could be read"). Let me pull the evidence for all 30 into one file so you're judging rather than searching.

<details><summary>tools run</summary>

- `Bash: Extract judgeable evidence for all 30 records`
- `Bash: Preview the evidence file`
- `SendUserFile`

</details>

## Claude  _11:10_

`q1a_sample_filings/_evidence_for_reading.txt` — 750 lines, one block per record. Each block gives you:

- the drug and the assigned outcome
- **the documented definition for that category**, inline, so you're not flipping back to the methodology
- the document headline
- every sentence from the **original** filing text that mentions that drug *and* carries result language
- blank `fair` / `boundary` / `note` lines

No CAR values anywhere in it, so the reading stays independent of Analysis 2.

29 of the 30 have at least one drug-and-result sentence. One has none and needs the file read directly — that'll be a `no_result` record where no drug is named.

Record 0 as it appears:

```
READING[0]   0000950170-22-019151   AXSM   2022-10-03
  drug            : Sunosi (solriamfetol)
  assigned outcome: positive
  definition      : primary endpoint met with statistical significance, or unambiguous success
  ...
    - "Axsome Therapeutics Announces Sunosi® Meets Primary Endpoint … Statistically
       significant improvement … (p=0.009, primary endpoint)"
```

Two things to watch while you work through it:

**Safe-harbour sentences leak in.** Record 0's last extracted sentence is forward-looking boilerplate — it matched because it contains "futility analyses" and "interim results". Ignore those; they're the same vocabulary problem your Q1c commentary already describes. The real content is always near the top.

**The first "sentence" is often the whole headline block**, because press-release headlines have no full stops. That's usually the most useful line in the block.

## Where I can help

Once you've formed a view, I'm happy to argue a record with you — the way we did for 4, 8 and 20, where you brought the reading and I checked it against the text and the definitions. That's a different thing from me supplying the verdicts, and it's the part that actually sharpens the answer.

If you do want my read on a specific record, say so and I'll give it — but it needs to go in cell 38 as AI-assisted, not into `HAND_LABELLED` as your own hand-reading.

## You  _11:16_

so how do i fill in the boundary parameter

## Claude  _11:16_

The `boundary` field can't be judged one record at a time — that's what makes it different from `fair`. Let me show you why, using what's already in the notebook.

<details><summary>tools run</summary>

- `Bash: Read the existing boundary test cell`

</details>

## Claude  _11:17_

Cell 15 already shows the shape of the answer, and it's the model to copy.

## The key idea: `boundary` is a comparison, not a verdict

`fair` you can decide from one filing. `boundary` you cannot — "is the line drawn consistently?" only means something relative to *another* record. Cell 15 does exactly this: two Tonix filings, **same study, same missed primary endpoint**, one labelled `mixed-positive` (2016, leads with secondary results), one `mixed-negative` (2019, states the miss first). Nothing about the trial changed. That's a boundary inconsistency, and it took two filings to show it.

So: **evidence for `"inconsistent"` is a pair.** Your `note` should name the counterpart.

```python
READING[11] = dict(fair=True, boundary="inconsistent",
                   note="P201/AtEase primary endpoint missed; labelled mixed-positive here "
                        "but mixed-negative in 0001387131-19-001982 (READING[18]), same study")
READING[18] = dict(fair=True, boundary="inconsistent",
                   note="same study as READING[11], labelled mixed-negative; the difference "
                        "is which result the filing leads with, not the endpoint")
```

Note both can be `fair=True` — each label is defensible on its own filing. The inconsistency is *between* them. That's precisely the distinction the rubric's top band asks for: *"separates disagreement over where a category boundary falls from outright misreading of the filing."*

## Do it as a second pass

Finish `fair` for all 30 first, then go back through in three groups — the adjacent-category pairs your six categories create:

| Pair | Records | The question |
|---|---|---|
| `positive` ↔ `mixed-positive` | 0–4 vs 10–14 | named explicitly in the brief |
| `mixed-negative` ↔ `negative` | 15–19 vs 5–9 | when does "some met, overall unfavourable" become "missed"? |
| `inconclusive` ↔ `no_result` | 20–24 vs 25–29 | you already suspect this one |

For each group, try to state the rule the pipeline appears to be using. Then check all ten records against it:

- **Rule holds for all ten** → every record in the group gets `boundary="ok"`.
- **Two records with the same facts got different labels** → both get `"inconsistent"`, each `note` naming the other.

## Worked example of the reasoning

Take `positive` vs `mixed-positive`. Candidate rule: *"`positive` if every reported endpoint was met; `mixed-positive` if at least one was missed."*

Now test it. Record 0 (Sunosi) — all three endpoints hit, labelled `positive`. Rule holds. Then look at each of records 10–14: did any of them actually have a missed endpoint, or were they downgraded for softer language ("encouraging", "signals") despite nothing being missed? If a `mixed-positive` has no missed endpoint, the rule is broken and that record is `"inconsistent"` against record 0.

## Use `"n/a"` sparingly

Only for the `no_result` records (25–29) — no directional claim, nothing to place on a boundary. Everything else gets `ok` or `inconsistent`.

## What you already have going in

Two observations from your existing prose that are boundary findings waiting to be recorded per record:

- **`inconclusive`** — four of five describe trials that hadn't reported. The definition requires "results reported"; those are `no_result` cases. That's the `inconclusive`/`no_result` line moving.
- **`mixed-positive`/`mixed-negative`** — cell 15's Tonix pair, records 11 and 18.

Verify both against the filings rather than taking them from the prose — but they tell you where to look first.

Want me to print records 0–4 and 10–14 side by side, just their endpoint sentences, so the `positive`/`mixed-positive` comparison is easy to eyeball? Same as the evidence file, reordered for comparison.

## You  _11:36_

is reading[4] and consistent i cant tell

## Claude  _11:36_

Let me pull the full results slide so you can see everything the filing reports.

<details><summary>tools run</summary>

- `Bash: Extract the LPCN Phase 2b results slide in full`

</details>

## Claude  _11:37_

Here's the whole results slide:

> **LPCN 1111: Phase 2b Results / Highlights — Met Primary Study Objectives**
> ▪ Once daily dose identified for the pivotal Phase 3 study
> ▪ Target once-daily Phase 3 dose **met both primary and secondary end points**
> ▪ Good dose-response relationship was observed
> ▪ Well tolerated with no drug-related severe or serious adverse events
> ▪ Results confirm prior Phase 2a study results

Nothing is reported as missed. No endpoint is described as not met, no caveat, no "however". The `mixed-positive` definition requires *"some endpoints met but others missed"* — and there is no missed endpoint here to trigger it. So this record doesn't sit on the `positive`/`mixed-positive` line at all, and there's nothing to compare against record 0.

On that reading it's **`boundary="ok"`** — but read the slide yourself and satisfy yourself, because there are two things a marker could push on.

## The two things that might have made you hesitate

**1. "Target once-daily Phase 3 dose met both endpoints."** The study tested five dose arms (500mg, 750mg, 1000mg in period 1; 1250mg QD and 500mg BID in period 2). The claim is scoped to *one* dose. The others aren't reported as failing — they're just not reported. Is a dose-finding study where one arm succeeded a full `positive`? That's a genuine question, but it's about whether `fair=True`, not about boundary consistency, because nothing is stated as missed.

**2. No p-values anywhere.** Compare record 0, which gives p=0.009, p=0.002, p=0.004. The `positive` definition allows either "statistically significant" **or** "unambiguous statement of success" — and "Met Primary Study Objectives" is about as unambiguous as it gets. So it qualifies under the second limb. But note the two records qualify under *different limbs* of the same definition, which is worth being aware of.

## How to resolve "I can't tell"

`"ok"` is the correct entry when you've looked for a conflicting case and not found one. It doesn't claim the label is beyond question — that's what `fair` is for. It claims you couldn't find another record in the sample treated differently on the same facts.

The test to apply: **can you name a counterpart record?** For the Tonix pair (11 and 18) you can — same study, opposite labels. For record 4, can you point at another sampled filing that says "met primary objectives, nothing missed" and got something other than `positive`? If not, it's `"ok"`.

If you're still uneasy, the honest entry is `"ok"` with a note recording the doubt:

```python
READING[4] = dict(fair=True, boundary="ok",
                  note="'Met Primary Study Objectives'; target Phase 3 dose met both primary "
                       "and secondary endpoints, nothing reported as missed. No p-values given "
                       "— qualifies under the 'unambiguous statement of success' limb rather "
                       "than statistical significance.")
```

That note is worth more than the flag itself. It shows you tested the boundary and says exactly what the evidence was — which is what the rubric's "cites specific evidence from the filings" is asking for.

One more thing: this is a deck, and decks are the format where "nothing missed" is least trustworthy, because a company controls which bullets appear. That's a legitimate observation for your write-up — but it's a limitation of the source, not a boundary inconsistency, so it belongs in the note rather than in the flag.

## You  _11:40_

reading[6] i cant see why its negative

<details><summary>tools run</summary>

- `Bash: Check what record 6 shows in the evidence file`

</details>

## Claude  _11:41_

My extractor dropped the decisive sentence. That's a flaw in the tool I built you, not in the data.

The filing says:

> **"The study did not meet its primary endpoint or the key secondary endpoints."**

It's missing from your evidence file because the sentence says *"The study"* rather than naming the drug, and my filter required a drug token **and** result language. So the one sentence that establishes `negative` was filtered out — leaving only the neutral announcement line and a safety line.

This is the same anaphora problem I flagged in `result_sentences()` earlier, and I reproduced it in my own extractor. Let me fix it.

<details><summary>tools run</summary>

- `Bash: Fix the extractor to keep subject-less result sentences`
- `Bash: Verify record 6 now shows the decisive sentence`
- `SendUserFile`

</details>

## Claude  _11:42_

Record 6 now reads:

```
  RESULT SENTENCES (3):
    - announced topline results of the Phase 2b EMBARK clinical trial evaluating
      LIVMARLI® (maralixibat) oral solution in patients with biliary atresia.
    - [subject not named - confirm it refers to this drug] The study did not meet
      its primary endpoint or the key secondary endpoints.
    - LIVMARLI was generally well-tolerated with no new safety findings.
```

The middle sentence is the one that establishes `negative` — primary endpoint missed. The tag is there because "the study" could in principle refer to a different trial in a multi-drug filing; here the previous sentence names the EMBARK trial evaluating LIVMARLI, so it's the same study. Worth checking that chain each time you see the tag rather than assuming.

**31 sentences were recovered across the 30 records** that the first version dropped. Given record 6's decisive line was one of them, it's worth re-reading any record you already judged from the old file.

## Two things worth taking from this

**Your instinct was right and the tool was wrong.** "I can't see why it's negative" was the correct response to what you were shown — the evidence in front of you genuinely didn't support the label. That's the right reflex for this task: when the label and the visible evidence don't match, the first question is whether you're seeing all the evidence.

**This is a finding about the notebook, not just about my script.** `result_sentences()` has exactly the same defect — a sentence scores 3 points for naming the drug, so *"The study did not meet its primary endpoint"* scores 2 while a bland announcement sentence naming the drug scores 6. In record 6 both happen to survive at `k=4`, so `show()` is fine there. But `embed_records()` uses `k=3` with `hi=400`, and result sentences very often refer back to "the study" rather than re-naming the drug.

You now have a concrete number for that: **31 subject-less result sentences across 30 filings** — roughly one per filing that the drug-name requirement would suppress. That's a measured limitation of the Q1c vectorisation, and it belongs in the same write-up as the sentence-filter loss.

I'd add it to the limitations list rather than fix the code, for the same reason as before — you have a re-run pending and the measurement is worth nearly as much as the fix.

## You  _11:46_

why is reading[11] mixed-positive

<details><summary>tools run</summary>

- `Bash: Show record 11 evidence block`
- `Bash: Find whether the primary endpoint dose missed`

</details>

## Claude  _11:47_

Now the structure is visible, and this is the most interesting record in your sample.

## What the trial actually specified

> **"Primary efficacy endpoint: Difference in CAPS-5 score between TNX-102 SL 2.8 mg and placebo at 12 weeks"**

The primary endpoint is the **2.8 mg** arm at **week 12**. That is the pre-specified test.

## What the filing reports for that arm

> "TNX-102 SL at 2.8 mg daily for 12 weeks: — Reduced PTSD symptoms (CAPS-5) **at weeks 2 and 4** — Reduced hyperarousal at weeks 2, 4 and 8 — **Non-significant intermediate effects at week 12** on PTSD symptoms, global and functional improvement"

**The primary endpoint missed.** Week 12, 2.8 mg — non-significant, stated in the company's own words.

## What the filing leads with instead

> "TNX-102 SL at **5.6 mg** daily for 12 weeks: — Reduced severity of PTSD (CAPS-5, **p=0.031**, Effect Size=0.39) — Reduced key symptoms — Improved global symptoms and function"

The 5.6 mg arm is the **secondary/exploratory** dose, and that's where every headline p-value comes from — p=0.031, p=0.015, p=0.041, all "Placebo v. TNX-102 SL 5.6 mg". Even then, remission rates were **NS, p=0.17**.

## So why `mixed-positive`?

Because the pipeline is quote-first, and the sentences that read most like results are the 5.6 mg ones with the significant p-values. "Some endpoints met, others missed; overall direction favourable" is a defensible reading of the *presentation*. The company built the deck to lead with what worked.

Whether it's defensible against the *trial* is your call, and here's the tension:

- **`negative` is defined as** "primary endpoint missed" — which is exactly what happened.
- **`mixed-positive` requires** "overall direction favourable" — which rests on a non-primary dose arm.

You could reasonably conclude `fair=False` on the grounds that a missed primary endpoint is the definition of `negative`, and that significant results on a secondary dose don't convert it. You could also conclude `fair=True` on the grounds that real endpoints were met and the pipeline was reading what the filing says. Both are arguable — say which you chose and why.

## The boundary judgement, though, is not ambiguous

This is one half of the pair in cell 15. The **same study** appears again as record 18 (`0001387131-19-001982`, 2019), where the filing states the primary endpoint miss up front — and that one is labelled **`mixed-negative`**.

Same trial. Same missed primary endpoint. Two labels. The only difference is which result the company chose to lead with. That is a boundary inconsistency with a named counterpart, which is exactly what the brief's "whether the category boundaries are applied consistently" asks you to find:

```python
READING[11] = dict(fair=???, boundary="inconsistent",
                   note="P201/AtEase primary endpoint (CAPS-5, 2.8 mg, wk 12) non-significant; "
                        "all significant results are the secondary 5.6 mg arm (p=0.031). "
                        "Labelled mixed-positive; same study labelled mixed-negative in "
                        "READING[18] (0001387131-19-001982). Difference is presentation order.")
```

Note that `boundary="inconsistent"` holds **whichever way you decide `fair`** — the inconsistency is between the two records, not within either one.

## One caution

This is a deck reporting a company's own trial, and the dose-arm switch between the primary endpoint and the headline is the kind of thing that's easy to miss when skimming. That's worth a sentence in your write-up: it's a concrete instance of the "label reproduces the sponsor's framing" failure mode your cell 22 already names, and you can now cite the exact endpoint and dose.

## You  _11:48_

sorry i meant reading[10]

<details><summary>tools run</summary>

- `Bash: Show record 10 evidence block`
- `Bash: Look for the trial result in record 10`
- `Bash: Check how the primary endpoint is described in record 10`

</details>

## Claude  _11:49_

There it is. The filing does report a miss — it's just buried in a footnote.

## The decisive line

> **"BESTFIT pre-specified primary endpoint: change in week 12 mean pain score (p=0.172)"**

p=0.172. **The primary endpoint missed.** That sits in the small print under the results table.

## And how the deck frames it

On the body slide:

> "Tonmya demonstrated broad activity and was very well-tolerated in Phase 2b study
>  — Statistically-significant improvements across core fibromyalgia symptoms
>  — **Positive trend in primary endpoint** of change in mean pain intensity"

"Positive trend" is p=0.172. The results table beside it shows only the endpoints that hit — pain 30% responder p=0.033, sleep p<0.001 and p=0.005, PGIC p=0.025, FIQ-R p=0.014 — with the slide headed **"BESTFIT: Tonmya broadly improved fibromyalgia"**.

There's a second sleight worth catching: the table's top row is footnoted *"FDA-accepted primary endpoint in current Phase 3 AFFIRM study"* — that's the primary endpoint of the **next** trial, not this one. The endpoint that actually governed BESTFIT appears only in the footnote, with the failing p-value.

## So `mixed-positive` is defensible on this text

Some endpoints met (sleep, PGIC, FIQ-R, responder analysis — all significant), the primary one missed (p=0.172), and the overall presentation is favourable. That maps onto "some endpoints met but others missed; overall direction favourable" fairly precisely.

Whether you think a missed primary endpoint should be `negative` regardless is the same judgement you face on record 11 — and you should decide it the same way for both, which is itself the consistency question.

## The boundary comparison you now have

Line these three up:

| record | primary endpoint | how the filing describes it | label |
|---|---|---|---|
| 10 (TNXP 2015) | **missed**, p=0.172 | "positive trend"; miss in a footnote | `mixed-positive` |
| 11 (TNXP 2016) | **missed**, 2.8 mg wk 12 NS | leads with the 5.6 mg arm | `mixed-positive` |
| 18 (TNXP 2019) | **missed** (same study as 11) | states the miss up front | `mixed-negative` |

Records 10 and 11 are consistent with each other — both are missed primaries dressed favourably, both `mixed-positive`. Record 18 is the same trial as 11 with the miss stated plainly, and gets `mixed-negative`.

That's a cleaner statement of the finding than cell 15 currently makes: it isn't just that two filings about one study disagree, it's that **across three filings the label tracks where the miss is placed in the document, not whether there was a miss.** All three had a missed primary endpoint; the two that led with the positives got the favourable label.

If your reading agrees, records 10, 11 and 18 all get `boundary="inconsistent"` with notes pointing at each other — and you'd have a three-record pattern rather than a pair, which is stronger evidence for the same claim.

One caution: 10 and 18 are decks and 11 is a results announcement, so document type varies alongside framing. Worth a clause in the note so a marker sees you noticed the confound.

## You  _11:55_

is reading12 mixed becuase there is no specific meeting of end points

<details><summary>tools run</summary>

- `Bash: Inspect record 12 text`

</details>

## Claude  _11:56_

Not vague at all — there are five "primary endpoint" mentions and three "did not". Let me get the actual results.

<details><summary>tools run</summary>

- `Bash: Extract the endpoint results for record 12`

</details>

## Claude  _11:57_

No — the opposite. This filing is unusually specific about endpoints. Your hypothesis doesn't hold here, and the real reason is more interesting.

## What the filing reports

Primary endpoint is stated precisely:

> **"The primary endpoint in the study was mean GCSI score at the end of week 4."**

And the results, by dose:

| Dose | GCSI at week 4 |
|---|---|
| **5 mg** | statistically significant, **nominal p = 0.0327** (GRS nominal p = 0.0159) |
| **15 mg** | "did not demonstrate nominally statistically significant" improvement |
| **30 mg** | same |

Plus:

> "Lack of dose response resulted in a **lack of statistical significance across the three doses when adjusted for multiplicity.** As a result, the statistical comparisons for the 5 mg dose are **not adjusted for multiple comparisons, and all are quoted as nominal.**"

> "Velusetrag Demonstrated **Inverse Dose Response** on GCSI subscale scores"

## So `mixed-positive` maps onto the definition well

"Some endpoints met but others missed; overall direction favourable":

- **Met** — 5 mg on GCSI and GRS, both PRO tools, both patient sub-types, gastric emptying significant at all doses (p < 0.001)
- **Missed** — 15 mg and 30 mg on symptoms; the multiplicity-adjusted analysis across all three doses
- **Overall favourable** — the company's own headline is "Announces **Positive** Top-Line Results"

That's a genuine mixed picture, explicitly reported as such. On the text, `mixed-positive` looks defensible.

## The distinction worth carrying forward

Compare with the three you've just looked at:

| record | what happened | how it's labelled |
|---|---|---|
| 10 (TNXP) | primary missed (p=0.172), miss in a footnote | `mixed-positive` |
| 11 (TNXP) | primary missed, headline is the secondary dose arm | `mixed-positive` |
| **12 (TBPH)** | **primary met at 5 mg, missed at 15/30 mg, stated plainly** | `mixed-positive` |

Records 10 and 11 are *misses dressed as mixed*. Record 12 is **genuinely mixed and honestly reported** — the company states the failed doses, the inverse dose response, and the multiplicity problem in its own press release.

All three get the same label. That is itself a finding: the category can't distinguish "some endpoints genuinely met and others missed" from "primary endpoint missed but presented favourably". If you're arguing boundary inconsistency for 10 and 11, record 12 is your control — the case that shows what `mixed-positive` looks like when applied correctly. Cite it that way and the argument gets much stronger, because you're not just saying "the labels are unreliable", you're showing the same label covering two materially different situations.

## For the nominal-vs-adjusted point

There's a real analytical subtlety here that a marker with a stats background would enjoy: the 5 mg p-values are **nominal only**, because the pre-specified multiplicity adjustment across three doses failed. Strictly, the study did not demonstrate statistical significance on its primary endpoint under its own analysis plan. That's an argument for `fair=False` — the `positive` definition requires "statistical significance", and the `mixed-positive` rests on unadjusted values the company itself flags as nominal.

I'd note that in your `note` field whichever way you land:

```python
READING[12] = dict(fair=???, boundary="ok",
                   note="Primary endpoint GCSI wk4: 5 mg significant (nominal p=0.0327), "
                        "15/30 mg not; multiplicity-adjusted analysis across 3 doses NOT "
                        "significant, so 5 mg quoted as nominal only. Genuine mixed result, "
                        "stated openly — contrast READING[10]/[11] where the primary missed.")
```

One more thing worth noting: this is the record where the Item 7.01 code disagreed with your `results announcement` reading. Having now seen it, the 8-K body says *"issued a press release announcing positive top-line results"* — it's a results announcement furnished under Reg FD. Your reading looks right and the Item code was misleading here.

## You  _12:00_

what about reading[13]

<details><summary>tools run</summary>

- `Bash: Show record 13 evidence block`
- `Bash: Check which drug the negative belongs to in record 13`

</details>

## Claude  _12:01_

This one is the strongest case in the sample for `fair=False`, and it's record 8's problem in reverse.

## Everything the filing says about cabozantinib is positive

> "The findings showed that cabozantinib **improved overall survival (OS) and progression-free survival** compared with placebo irrespective of duration of prior sorafenib treatment or age category."

> "the data demonstrate that cabozantinib provided a **statistically significant and clinically meaningful improvement in OS** versus placebo."

No missed endpoint. No caveat. Nothing "mixed" about it.

## The only negative in the document belongs to a different drug

> "In May, Exelixis' collaborator Genentech informed the company that IMblaze370, the phase 3 pivotal trial evaluating **cobimetinib** in combination with **atezolizumab** … **did not meet its primary endpoint**."

I checked every negative-result sentence in the filing — there is exactly one, and cabozantinib appears in none of them. Cobimetinib is a Genentech-partnered drug, a different molecule in a different indication.

And the classification table for this filing has **only one row**:

```
drug_name                 phase    outcome         consensus_type
cabozantinib (CABOMETYX)  Phase 3  mixed-positive  b3b_only
```

The cobimetinib miss was never classified separately. So the most likely reading is that the pipeline saw a positive cabozantinib result and a missed primary endpoint in the same document, and resolved the two into `mixed-positive` on a single drug.

## Two aggravating details

**`consensus_type = b3b_only`.** B1a — the prompt with the *ownership filter*, designed to exclude third-party trials — didn't return a result for this filing at all. The label rests entirely on B3b, which has no ownership filter. That is precisely the failure mode B1a exists to prevent, and here the one prompt that would have caught it is silent. Your Q1b `S9_single_prompt` signal fires on this record.

**"As previously announced and presented."** CELESTIAL was disclosed months earlier; this is a Q2 earnings 8-K. So the timing defect applies too — the label is attached to a restatement, and the CAR beside it is an earnings reaction.

## What I'd put in the record

```python
READING[13] = dict(fair=False, boundary="ok",
                   note="All cabozantinib statements are positive: 'statistically significant "
                        "and clinically meaningful improvement in OS versus placebo'. The only "
                        "missed endpoint in the filing is IMblaze370 (cobimetinib/atezolizumab, "
                        "Genentech) — a different drug. mixed-positive appears to merge the two. "
                        "consensus_type=b3b_only, so B1a's ownership filter never applied.")
```

`boundary="ok"` because this isn't a boundary being drawn in the wrong place — it's the label attaching to the wrong evidence. That's a different failure, and keeping the two apart is exactly what the rubric's top band rewards.

## Why this record is worth featuring

Your cell 21 already names failure mode (b) — "the label attaches to the wrong news within the same filing" — and cites Neurogene and Sellas. Record 13 is a cleaner example than either, because the two drugs are unambiguously different molecules, the cabozantinib evidence is unambiguously positive, and `b3b_only` explains *mechanically* why the ownership filter didn't save it.

Combined with record 8 (where the reader is misled but the label is right), you have a matched pair: same structural hazard, opposite outcomes. That's a much sharper illustration than either alone.

## You  _12:08_

what about reading[14]

<details><summary>tools run</summary>

- `Bash: Compare record 14 with record 10`

</details>

## Claude  _12:09_

Record 14 is essentially the same document as record 10.

```
READING[10]  0001144204-15-047929  2015-08-11  25,993 chars
READING[14]  0001144204-15-054317  2015-09-10  26,034 chars
text similarity: 0.997
```

Same corporate deck, filed a month apart for a different investor conference. Identical content: BESTFIT mentioned 12 times in both, PTSD 23 times in both, and the same buried footnote in both —

> **"BESTFIT pre-specified primary endpoint: change in week 12 mean pain score (p=0.172)"**

So the analysis is exactly what you worked out for record 10: primary endpoint missed at p=0.172, described on the body slide as a "positive trend", results table showing only the endpoints that hit. `mixed-positive` is defensible on the text, arguable against the trial.

## The interesting part is what having both tells you

**Consistency, at least.** Two near-identical documents got the same label. That's the pipeline behaving deterministically — worth noting, because it means the inconsistency you found between records 11 and 18 is driven by the *documents differing*, not by run-to-run noise. That strengthens your boundary argument rather than weakening it.

**But it also means your sample is less independent than n=30 suggests.** Records 10 and 14 are one document counted twice. Six of your thirty are TNXP, and three of those (10, 14, 28) are corporate decks recycling the same BESTFIT material. When you report "24 of 30", some of those thirty aren't independent observations.

That's worth a sentence in the write-up. It doesn't invalidate anything — the sample was drawn correctly, stratified with your seed, and near-duplicate filings are a real feature of the corpus rather than a sampling error. But a marker who notices two identical decks in a 30-record sample will want to see that you noticed too.

**And it connects to something already in your notebook.** Cell 20 finds 170 records that are "exact repeats" — the `S7_repeated_record` signal. This is a related but distinct phenomenon: not duplicate *rows*, but duplicate *documents* filed under different accession numbers. Both inflate apparent sample size, and only the first is currently flagged.

## Suggested entries

```python
READING[10] = dict(fair=???, boundary="inconsistent",
                   note="BESTFIT pre-specified primary endpoint (wk12 mean pain) p=0.172 — "
                        "missed, disclosed only in a footnote; body slide calls it a 'positive "
                        "trend'. Table shows only endpoints that hit (p=0.033–0.014). "
                        "cf. READING[18], same sponsor, miss stated up front -> mixed-negative.")

READING[14] = dict(fair=???, boundary="inconsistent",
                   note="Near-identical deck to READING[10] (0.997 text similarity, filed one "
                        "month later); same BESTFIT p=0.172 footnote, same label. Consistent "
                        "with [10], but the two are not independent observations.")
```

Whatever you decide for `fair` on record 10, record 14 must get the same value — they're the same document. If you found yourself wanting to answer them differently, that would be a signal to revisit the reasoning on both.

## You  _12:09_

what about reading[15]

<details><summary>tools run</summary>

- `Bash: Show record 15 evidence block`

</details>

## Claude  _12:10_

Only two sentences surfaced, and neither is a trial result. Let me look at what the filing actually says about ADUHELM.

<details><summary>tools run</summary>

- `Bash: Examine the ADUHELM content in record 15`

</details>

## Claude  _12:10_

This one looks like a `no_result` misfiled as a trial outcome.

## What the filing is

Biogen's **Q4 2021 earnings release**. ADUHELM appears 26 times, and every occurrence I sampled is commercial or financial:

- "ADUHELM® revenue was **$1 million**"
- "$164 million in charges associated with inventory and purchase commitments **in excess of forecasted demand**"
- "$155 million related to ADUHELM **commercialisation**"
- "Engaging with **Centers for Medicare and Medicaid Services on ADUHELM reimbursement**"
- a deferred tax valuation allowance on Neurimmune's tax basis in ADUHELM

## What it says about trials

Only two sentences, and neither is a readout:

1. *"The primary endpoint **will be** measured by the Clinical Dementia Rating–Sum of Boxes at 18 months"* — a **future** endpoint for the ENVISION post-marketing study. Nothing reported.
2. *"...plasma samples...showed a statistically significant correlation between plasma p-tau reduction and less cognitive and functional decline"* — a **biomarker correlation** from post-hoc plasma analysis presented at CTAD. That's an exploratory association, not a trial endpoint result.

Note the `phase` field: **"Post-marketing / Phase 4 planned"**. Planned. The trial hasn't run.

## Against the definitions

`mixed-negative` = *"some endpoints met, overall unfavourable."* No endpoint was met — none was tested. No endpoint was missed. There is no trial outcome in this filing at all.

`no_result` = *"Filing does not contain clinical trial outcome data (e.g., **earnings report**, corporate transaction)."* That describes this document exactly.

The commercial news here is genuinely bad — $1m revenue, inventory write-offs, a CMS reimbursement fight. My read is that the pipeline picked up that unfavourable tone and expressed it as `mixed-negative`, but **commercial disappointment is not a trial outcome**, and the category is defined on endpoints.

That points to `fair=False`, though satisfy yourself by scanning the rest of the ADUHELM passages — 26 mentions and I've shown you six.

## Two supporting details

**`consensus_type = b3b_only`** again. B1a returned nothing. The label rests on the single prompt with no ownership filter and no second reading — the same structural weakness as record 13.

**The second row in this filing** is `zuranolone`, labelled `inconclusive`, also `b3b_only`. Worth a glance: if that one is also a not-yet-reported trial, then a single earnings release generated two classifications, neither backed by a readout.

## Suggested entry

```python
READING[15] = dict(fair=False, boundary="inconsistent",
                   note="Q4-2021 earnings release. All ADUHELM content is commercial: $1m "
                        "revenue, $164m inventory charges, CMS reimbursement. The only trial "
                        "references are a future ENVISION endpoint ('will be measured') and a "
                        "post-hoc plasma p-tau correlation. No endpoint met or missed — this "
                        "meets the no_result definition ('earnings report'). Phase field reads "
                        "'Phase 4 planned'. consensus_type=b3b_only.")
```

I'd mark `boundary="inconsistent"` here, because your five `no_result` records (25–29) are also earnings reports and corporate filings — and they were labelled `no_result`. Same kind of document, different category. That's the `no_result` boundary being drawn in two places, and it's a *different* boundary from the `inconclusive`/`no_result` one you're expecting to find at records 20–24.

If that holds up, you have three distinct boundary problems rather than one, which is a stronger answer to the brief's "applied consistently" question than a single example.

## You  _12:13_

what about reading[16]

<details><summary>tools run</summary>

- `Bash: Show record 16 evidence block`

</details>

## Claude  _12:14_

This one is a strong test of the pattern you've been building, and it comes from a different sponsor, which matters.

## What the filing reports

A Q4 2020 earnings release restating the September 2020 SIGNAL topline. The decisive sentence is right there in plain view:

> **"Although the study did not meet the above pre-specified co-primary endpoints,** we believe the results of each of the two cognitive assessments in patients with early manifest disease demonstrated a **strong trend** for beneficial change (OTS, **p=0.028** and PTAP, **p=0.06, 1-sided**)."

And what's offered in place of the co-primaries:

- **exploratory** HD-CAB composite — "believed to indicate highly significant treatment-related benefit (p=0.007)"
- CGIC — "**did not show a statistically significant difference**"
- a **subpopulation** analysis (TFC 11) at p=0.04, one-sided, which the company itself concedes was "**not powered for statistical significance**"

Note that every favourable p-value is one-sided, exploratory, or from a subgroup. The co-primaries missed.

## Why this record matters to your argument

Compare the four you've now examined:

| record | sponsor | primary endpoint | how the filing presents it | label |
|---|---|---|---|---|
| 10/14 | TNXP | missed, p=0.172 | miss in a footnote; "positive trend" | `mixed-positive` |
| 11 | TNXP | missed | leads with the secondary 5.6 mg arm | `mixed-positive` |
| **16** | **VCNX** | **missed (co-primaries)** | **"Although the study did not meet…" stated up front** | **`mixed-negative`** |
| 18 | TNXP | missed (same study as 11) | states the miss first | `mixed-negative` |

Record 16 is the one that breaks the "it's just a Tonix quirk" objection. **Different company, different disease, different year — same rule.** The label tracks *where in the document the miss is stated*, not whether there was one. Filings that state the miss in the leading sentence get the negative-side label; filings that bury it get the positive-side label.

That's a genuine systematic pattern across four filings and two sponsors, which is a considerably stronger claim than the two-filing demonstration in cell 15.

## Is `mixed-negative` fair here?

Arguable both ways, and worth stating which you chose:

- **`fair=True`** — the definition is "some met, overall unfavourable". Some measures did show benefit, and the overall assessment lands unfavourable. The label matches.
- **`fair=False`** — strictly, *no* pre-specified endpoint was met. The co-primaries missed and CGIC missed. Everything positive is exploratory, one-sided, or a subgroup the company admits was underpowered. Under the documented definition that's `negative`, not `mixed-negative`.

I lean toward the second being the stronger reading, but it's your call — and either way `boundary="inconsistent"` holds, because the comparison with records 10 and 11 is what's inconsistent, not this record on its own.

## Suggested entry

```python
READING[16] = dict(fair=???, boundary="inconsistent",
                   note="'Although the study did not meet the above pre-specified co-primary "
                        "endpoints' — stated openly. All favourable results are exploratory "
                        "(HD-CAB p=0.007), one-sided (OTS p=0.028, PTAP p=0.06) or a subgroup "
                        "the company calls underpowered (p=0.04, 1-sided). CGIC not significant. "
                        "Labelled mixed-negative; TNXP filings [10]/[11] with equally missed "
                        "primaries but the miss de-emphasised got mixed-positive. Different "
                        "sponsor, same pattern.")
```

One more thing worth carrying into Q1d: this is also a `periodic report` restating a September 2020 result in March 2021 — so the timing defect stacks on top. The label describes the trial reasonably; the return beside it is a Q4 earnings reaction.

## You  _12:15_

what about reading[17]

<details><summary>tools run</summary>

- `Bash: Show record 17 evidence block`
- `Bash: Check for any met endpoint and compare with record 6`

</details>

## Claude  _12:16_

This is the cleanest boundary finding in your sample so far.

## What record 17 says

> "LYR-210 **did not meet its primary endpoint** of statistically significant improvement compared to sham control in the composite score of the three cardinal symptoms of CRS at 24 weeks."

> CEO: "the **disappointment of not meeting the primary endpoint** in the previously-announced ENLIGHTEN 1 Phase 3 trial"

> "LYR-210 was **generally well tolerated**, with no product-related serious adverse events."

I searched the whole filing for any endpoint described as met. **There are none.** The only non-negative statement is tolerability. On top of that: cost-cutting measures, three leaseholds to sublease, and "substantial doubt regarding our ability to continue as a going concern."

## The comparison that makes this decisive

Put it beside record 6, which you already looked at:

| | record 6 (MIRM) | record 17 (LYRA) |
|---|---|---|
| miss | "The study **did not meet its primary endpoint** or the key secondary endpoints." | "LYR-210 **did not meet its primary endpoint**…" |
| positive | "LIVMARLI was **generally well-tolerated** with no new safety findings." | "LYR-210 was **generally well tolerated**, with no product-related serious adverse events." |
| **label** | **`negative`** | **`mixed-negative`** |

Two filings. Same two ingredients — primary endpoint missed, drug well tolerated. Nothing else met in either. **Different labels.**

That is the `negative` / `mixed-negative` boundary drawn in two different places on materially identical facts, and unlike the Tonix pair you don't even need to argue about presentation order — the sentences are almost word-for-word.

Against the definitions, record 17 fails `mixed-negative` on its own terms: "**some met**, overall unfavourable" requires something to have been met. Nothing was. `negative` — "primary endpoint missed" — is the exact fit.

Note also `consensus_type = agree` here: **both** prompts independently reached `mixed-negative`. So this isn't a single-prompt artefact like records 13 and 15. Both readers drifted the same way, which makes it a property of the prompt design rather than a fluke.

## Suggested entry

```python
READING[17] = dict(fair=False, boundary="inconsistent",
                   note="'LYR-210 did not meet its primary endpoint'; CEO calls it 'the "
                        "disappointment of not meeting the primary endpoint'. No endpoint met "
                        "anywhere in the filing — only 'generally well tolerated'. Company is "
                        "cost-cutting with going-concern doubt. Structurally identical to "
                        "READING[6] (MIRM: primary missed + well tolerated) which is labelled "
                        "negative. consensus_type=agree, so both prompts drifted.")
```

## Where you now stand on the boundary question

You have three distinct, evidenced boundary problems:

1. **`positive` / `mixed-positive`** — records 10, 11, 14 vs 12: the label tracks where the miss sits in the document, not whether there was one.
2. **`negative` / `mixed-negative`** — record 6 vs 17: identical facts, different labels.
3. **`no_result`** — record 15: an earnings release with no readout classified as a trial outcome.

Three different boundaries, each with a named counterpart record and a quotable sentence. That answers the brief's "whether the category boundaries are applied consistently" far more thoroughly than the single Tonix pair in cell 15 — and it's the "systematic patterns across the whole sample" the top rubric band asks for.

Worth noting when you write it up: the drift is not random. In every case the label lands *softer* than the endpoint outcome warrants — misses become mixed, and mixed-negatives become the gentler of the two options. That directional bias is a more useful finding for the IR team than "the labels are noisy", because it tells them which way to correct.

## You  _12:17_

can you do this for the other readings i havent asked just so i can check that i have read them properly

## Claude  _12:18_

I'd rather do it the other way round, and I think it'll serve you better.

If you've read them, send me your calls — even in shorthand (`18: fair, ok` / `22: not fair, inconsistent — trial hasn't reported`) — and I'll check each against the filing text and tell you where I disagree and why. That's a real check on your reading. Me writing 17 fresh analyses for you to compare against isn't a check; it's a second reading that becomes the one you rely on.

There's also a practical reason. We're now 13 records in — 0, 4, 6, 8, 10, 11, 12, 13, 14, 15, 16, 17 and 20 — and on several of those I found things you hadn't flagged (the cobimetinib mix-up in 13, the p=0.172 footnote in 10, the record 6/17 pair). If I do the remaining 17 as well, then every judgement in your sample traces back to this conversation, and cell 38 has to say so. Keeping the rest yours is what makes the 24/30 defensible.

**Remaining: 1, 2, 3, 5, 7, 9, 18, 19, 21, 22, 23, 24, 25, 26, 27, 28, 29.**

Three things that would make short work of them:

- **18** — you already have the context: it's the 2019 Tonix filing, same AtEase study as record 11, and cell 15 already describes it. Should be quick.
- **25–29 (`no_result`)** — these are the easy block. Check there's genuinely no trial outcome, and note whether each is an earnings release or a corporate transaction. Record 15 gives you the comparison that matters.
- **21–24 (`inconclusive`)** — the block where you already suspect the `inconclusive`/`no_result` line is wrong. Your existing prose says four of five describe trials that hadn't reported; verify which four.

Send me any you're unsure about, one at a time, the way you did with 12 and 16 — that worked well, and on both you'd already formed a view I could push against.

## One thing to write down now, while it's fresh

Cell 38 needs to record what actually happened on the 13 we've done: that the excerpts were extracted programmatically, and that for those records the filing text was analysed in conversation with Claude, including the specific findings (cobimetinib vs cabozantinib in 13, the BESTFIT footnote in 10, the 6/17 pair). Note the ones where you changed your mind and the ones where you didn't.

That's a stronger disclosure than the current draft, and it's accurate — which is the standard the AI-use guidance actually sets.

## You  _12:22_

READING[0] = dict(fair=True, boundary="ok",
                  note="Meets Primary Endpoint; DSST RBANS p=0.009 vs placebo")
READING[1] = dict(fair=True,  boundary="ok",           note="OPAL Broaden met its primary efficacy endpoints demonstrating that both tofacitinib 5 mg BID and 10 mg BID were superior to treatment with placebo")
READING[2] = dict(fair=True,  boundary="ok",           note="We are encouraged by the positive results of this Phase II study testing")
READING[3] = dict(fair=True,  boundary="ok",           note="tarcocimab met its primary endpoint and Tarcocimab also met all key secondary endpoints")
READING[4] = dict(fair=True, boundary="ok",             note="'Met Primary Study Objectives'; target Phase 3 dose met both primary and secondary endpoints, nothing reported as missed. No p-values given — qualifies \
                                                               under the 'unambiguous statement of success' limb rather than statistical significance.")
READING[5] = dict(fair=True,  boundary="ok",           note="did not meet its primary endpoint due to a previously unknown interaction with chronic concurrent steroid use")
READING[6] = dict(fair=True,  boundary="ok",           note="The study did not meet its primary endpoint or the key secondary endpoints.")
READING[7] = dict(fair=True,  boundary="ok",           note="Izencitinib in Patients with Ulcerative Colitis · Randomized, double-blind, placebo-controlled study did not meet the primary endpoint")
READING[8] = dict(fair=True,  boundary="ok",           note="suptavumab did not meet its primary endpoint of preventing medically-attended RSV infections in infants")
READING[9] = dict(fair=True,  boundary="ok",           note="fordadistrogene movaparvovec, in ambulatory patients with Duchenne muscular dystrophy (DMD) did not meet its primary endpoint")
READING[10] = dict(fair=True,  boundary="ok",          note="BESTFIT pre-specified primary endpoint: change in week 12 mean pain score (p=0.172) Tonmya demonstrated broad activity and was very well-tolerated in Phase 2b study ")
READING[11] = dict(fair=True, boundary="inconsistent",  note="P201/AtEase primary endpoint missed; labelled mixed-positive here "
                        "but mixed-negative in 0001387131-19-001982 (READING[18]), same study")
READING[12] = dict(fair=True,  boundary="ok",           note="Primary endpoint GCSI wk4: 5 mg significant (nominal p=0.0327), "
                        "15/30 mg not; multiplicity-adjusted analysis across 3 doses NOT "
                        "significant, so 5 mg quoted as nominal only. Genuine mixed result, "
                        "stated openly — contrast READING[10]/[11] where the primary missed.")
READING[13] = dict(fair=False,  boundary="ok",           note="All cabozantinib statements are positive: 'statistically significant "
                        "and clinically meaningful improvement in OS versus placebo'. The only "
                        "missed endpoint in the filing is IMblaze370 (cobimetinib/atezolizumab, "
                        "Genentech) — a different drug. mixed-positive appears to merge the two. "
                        "consensus_type=b3b_only, so B1a's ownership filter never applied.")
READING[14] = dict(fair=True,  boundary="ok",           note="Near-identical deck to READING[10] (0.997 text similarity, filed one "
                        "month later); same BESTFIT p=0.172 footnote, same label. Consistent "
                        "with [10], but the two are not independent observations.")
READING[15] = dict(fair=False,  boundary="inconsistent",           note="Q4-2021 earnings release. All ADUHELM content is commercial: $1m "
                        "revenue, $164m inventory charges, CMS reimbursement. The only trial "
                        "references are a future ENVISION endpoint ('will be measured') and a "
                        "post-hoc plasma p-tau correlation. No endpoint met or missed — this "
                        "meets the no_result definition ('earnings report'). Phase field reads "
                        "'Phase 4 planned'. consensus_type=b3b_only.")
READING[16] = dict(fair=True,  boundary="inconsistent",           note="'Although the study did not meet the above pre-specified co-primary "
                        "endpoints' — stated openly. All favourable results are exploratory "
                        "(HD-CAB p=0.007), one-sided (OTS p=0.028, PTAP p=0.06) or a subgroup "
                        "the company calls underpowered (p=0.04, 1-sided). CGIC not significant. "
                        "Labelled mixed-negative; TNXP filings [10]/[11] with equally missed "
                        "primaries but the miss de-emphasised got mixed-positive. Different "
                        "sponsor, same pattern.")
READING[17] = dict(fair=False,  boundary="ok",           note="'LYR-210 did not meet its primary endpoint'; CEO calls it 'the "
                        "disappointment of not meeting the primary endpoint'. No endpoint met "
                        "anywhere in the filing — only 'generally well tolerated'. Company is "
                        "cost-cutting with going-concern doubt. Structurally identical to "
                        "READING[6] (MIRM: primary missed + well tolerated) which is labelled "
                        "negative. consensus_type=agree, so both prompts drifted.")
READING[18] = dict(fair=True, boundary="inconsistent",
                   note="same study as READING[11], labelled mixed-negative; the difference "
                        "is which result the filing leads with, not the endpoint")
READING[19] = dict(fair=True,  boundary="ok",           note="Did not meet female only study but there could be prospect for males.")
READING[20] = dict(fair=True,  boundary="inconsistent",           note="no results")
READING[21] = dict(fair=True,  boundary="ok",           note="Outcomes were provided but unsure whether positive or negative")
READING[22] = dict(fair=True,  boundary="inconsistent",           note="no results")
READING[23] = dict(fair=True,  boundary="inconsistent",           note="no results")
READING[24] = dict(fair=True,  boundary="inconsistent",           note="no results")
READING[25] = dict(fair=True,  boundary="ok",           note="no results")
READING[26] = dict(fair=True,  boundary="ok",           note="no results")
READING[27] = dict(fair=True,  boundary="ok",           note="no results")
READING[28] = dict(fair=True,  boundary="ok",           note="no results")
READING[29] = dict(fair=True,  boundary="ok",           note="no results")

These are my commentary for every reading can you check if these are in line with what you think

## Claude  _12:22_

This is exactly what I needed. Let me check them against the filings.

<details><summary>tools run</summary>

- `Bash: Verify the records I have not examined`
- `Bash: Verify records 19 and 23 in detail`

</details>

## Claude  _12:24_

Checked all 30 against the filings. Most of it holds up. Five things need attention, and one is systematic.

## 1. The `inconclusive` block contradicts itself — records 20, 22, 24

You wrote `note="no results"` but `fair=True`. Those can't both be right. `inconclusive` is defined as *"results reported but insufficient to determine direction."* If there are no results, the definition isn't met and the label is wrong.

I checked:

- **20 (TBPH Ampreloxetine)** — 0 result-bearing sentences. KOL event deck.
- **24 (LCTX AST-VAC1)** — 0 result-bearing sentences.
- **22 (GUTS Revita)** — has sentences, but they're all forward-looking: *"data update **expected in June 2025**"*, *"REVEAL-1 is **designed to provide** early, real-world insights"*, *"early clinical **signals** reinforce Revita's **potential**"*. Nothing reported.

All three should be `fair=False` — the filings meet the `no_result` definition, not `inconclusive`.

**23 (NBIX indiplon) is the exception, and your note is wrong there in the other direction.** The headline reads *"THE COMPANY ALSO ANNOUNCES **PRELIMINARY RESULTS** OF THE ONE YEAR PHASE III SAFETY STUDY WITH INDIPLON."* There *are* results — preliminary safety data, direction genuinely unclear. That's textbook `inconclusive`. Keep `fair=True`, but change the note from "no results" to the preliminary-safety finding.

**This also contradicts the table already in your notebook**, which says `inconclusive: 1 of 5 fair`. Your new reading says 5 of 5. My check supports something close to the old table — 1 or 2 of 5.

## 2. Record 17's note contradicts its own flag

You wrote `boundary="ok"`, and then in the note: *"Structurally identical to READING[6] … which is labelled negative."* That sentence **is** the boundary inconsistency. Should be `boundary="inconsistent"`.

## 3. Records 17 and 19 have the same structure but different `fair`

- **17 (LYRA)** — primary missed, nothing met, `mixed-negative` → you said `fair=False`
- **19 (CLDX)** — *"the TP10 females-only study did not meet the primary endpoint"*, `mixed-negative` → you said `fair=True`

Your note for 19 is accurate — the filing does say *"given the strong efficacy data in males shown in **this previous study**"* — but that's a **prior** trial, not this readout. So in this filing, as in 17, the primary missed and nothing was met.

Pick a rule and apply it to both. Either cross-study prior evidence counts as "some met" (both `fair=True`), or it doesn't (both `fair=False`). Right now they're judged differently on the same facts, which is the very thing you're criticising the pipeline for.

## 4. Records 10 and 14 marked `ok` while 11 and 18 marked `inconsistent`

10/14 (BESTFIT, primary missed at p=0.172) got `mixed-positive`. Record 16 (VCNX, co-primaries missed) got `mixed-negative`. That's the same cross-filing comparison that justifies your flag on 11/18 — different sponsors, missed primaries, opposite-side labels.

Either 10/14 are also `inconsistent`, or the rule you're using for 11/18 needs stating more narrowly (e.g. "same study, two filings").

## 5. Record 2 — right call, weak evidence quoted

`fair=True` is correct, but your note quotes *"We are encouraged by the positive results"*, which is a characterisation. The filing has the real thing:

> "**met its primary endpoint** of improvement in the median time to alleviation of symptoms … **This result was highly statistically significant.**"

Quote that instead. Also worth a look: the same filing mentions Phase III studies that were **terminated**, with HHS declining to reimburse ~$4m. Doesn't necessarily change `positive` for peramivir, but check whose trials those were.

## Two things I'd add

**Record 23 has three classification rows** — `indiplon`, plus `NBI-42902` twice (one `b1a_only`, one `b3b_only`, slightly different drug strings). That's the substring-matching duplicate problem from the methodology, live in your sample.

**Record 21 (TCRT)** — your note is a fair reading of `inconclusive`, but check *whose* results those p-values are. The deck covers palifosfamide strategy and the IL-12 programme, and the figures (median survival 7.3 vs 9.0 months, p=0.045; PFS HR 0.43) may belong to a comparator regimen rather than Ad-IL12. Same wrong-drug hazard as records 8 and 13.

## What this does to your totals

| category | your reading | table currently in cell 12 |
|---|---|---|
| positive | 5/5 | 5 |
| negative | 5/5 | 5 |
| mixed-positive | 4/5 | 3 |
| mixed-negative | 3/5 | 5 |
| inconclusive | 5/5 | **1** |
| no_result | 5/5 | 5 |
| **total** | **27/30** | **24/30** |

If you make the corrections above, you'll land somewhere around 23–24, close to the existing table but now with per-record evidence behind it. Once you've settled the four points, paste the final `READING` into cell 11 and the generated table replaces the typed one — and the 24/30 in cells 12, 22 and 38 needs updating to whatever you land on.

## You  _12:28_

READING[0] = dict(fair=True, boundary="ok",
                  note="Meets Primary Endpoint; DSST RBANS p=0.009 vs placebo")
READING[1] = dict(fair=True,  boundary="ok",           note="OPAL Broaden met its primary efficacy endpoints demonstrating that both tofacitinib 5 mg BID and 10 mg BID were superior to treatment with placebo")
READING[2] = dict(fair=True,  boundary="ok",           note="met its primary endpoint of improvement in the median time to alleviation of symptoms … This result was highly statistically significant.")
READING[3] = dict(fair=True,  boundary="ok",           note="tarcocimab met its primary endpoint and Tarcocimab also met all key secondary endpoints")
READING[4] = dict(fair=True, boundary="ok",             note="'Met Primary Study Objectives'; target Phase 3 dose met both primary and secondary endpoints, nothing reported as missed. No p-values given — qualifies \
                                                               under the 'unambiguous statement of success' limb rather than statistical significance.")
READING[5] = dict(fair=True,  boundary="ok",           note="did not meet its primary endpoint due to a previously unknown interaction with chronic concurrent steroid use")
READING[6] = dict(fair=True,  boundary="ok",           note="The study did not meet its primary endpoint or the key secondary endpoints.")
READING[7] = dict(fair=True,  boundary="ok",           note="Izencitinib in Patients with Ulcerative Colitis · Randomized, double-blind, placebo-controlled study did not meet the primary endpoint")
READING[8] = dict(fair=True,  boundary="ok",           note="suptavumab did not meet its primary endpoint of preventing medically-attended RSV infections in infants")
READING[9] = dict(fair=True,  boundary="ok",           note="fordadistrogene movaparvovec, in ambulatory patients with Duchenne muscular dystrophy (DMD) did not meet its primary endpoint")
READING[10] = dict(fair=True,  boundary="inconsistent",          note="BESTFIT pre-specified primary endpoint: change in week 12 mean pain score (p=0.172) Tonmya demonstrated broad activity and was very well-tolerated in Phase 2b study ")
READING[11] = dict(fair=True, boundary="inconsistent",  note="P201/AtEase primary endpoint missed; labelled mixed-positive here "
                        "but mixed-negative in 0001387131-19-001982 (READING[18]), same study")
READING[12] = dict(fair=True,  boundary="ok",           note="Primary endpoint GCSI wk4: 5 mg significant (nominal p=0.0327), "
                        "15/30 mg not; multiplicity-adjusted analysis across 3 doses NOT "
                        "significant, so 5 mg quoted as nominal only. Genuine mixed result, "
                        "stated openly — contrast READING[10]/[11] where the primary missed.")
READING[13] = dict(fair=False,  boundary="ok",           note="All cabozantinib statements are positive: 'statistically significant "
                        "and clinically meaningful improvement in OS versus placebo'. The only "
                        "missed endpoint in the filing is IMblaze370 (cobimetinib/atezolizumab, "
                        "Genentech) — a different drug. mixed-positive appears to merge the two. "
                        "consensus_type=b3b_only, so B1a's ownership filter never applied.")
READING[14] = dict(fair=True,  boundary="inconsistent",           note="Near-identical deck to READING[10] (0.997 text similarity, filed one "
                        "month later); same BESTFIT p=0.172 footnote, same label. Consistent "
                        "with [10], but the two are not independent observations.")
READING[15] = dict(fair=False,  boundary="inconsistent",           note="Q4-2021 earnings release. All ADUHELM content is commercial: $1m "
                        "revenue, $164m inventory charges, CMS reimbursement. The only trial "
                        "references are a future ENVISION endpoint ('will be measured') and a "
                        "post-hoc plasma p-tau correlation. No endpoint met or missed — this "
                        "meets the no_result definition ('earnings report'). Phase field reads "
                        "'Phase 4 planned'. consensus_type=b3b_only.")
READING[16] = dict(fair=True,  boundary="inconsistent",           note="'Although the study did not meet the above pre-specified co-primary "
                        "endpoints' — stated openly. All favourable results are exploratory "
                        "(HD-CAB p=0.007), one-sided (OTS p=0.028, PTAP p=0.06) or a subgroup "
                        "the company calls underpowered (p=0.04, 1-sided). CGIC not significant. "
                        "Labelled mixed-negative; TNXP filings [10]/[11] with equally missed "
                        "primaries but the miss de-emphasised got mixed-positive. Different "
                        "sponsor, same pattern.")
READING[17] = dict(fair=False,  boundary="inconsistent",           note="'LYR-210 did not meet its primary endpoint'; CEO calls it 'the "
                        "disappointment of not meeting the primary endpoint'. No endpoint met "
                        "anywhere in the filing — only 'generally well tolerated'. Company is "
                        "cost-cutting with going-concern doubt. Structurally identical to "
                        "READING[6] (MIRM: primary missed + well tolerated) which is labelled "
                        "negative. consensus_type=agree, so both prompts drifted.")
READING[18] = dict(fair=True, boundary="inconsistent",
                   note="same study as READING[11], labelled mixed-negative; the difference "
                        "is which result the filing leads with, not the endpoint")
READING[19] = dict(fair=True,  boundary="ok",           note="Did not meet female only study but there could be prospect for males.")
READING[20] = dict(fair=False,  boundary="inconsistent",           note="no results")
READING[21] = dict(fair=True,  boundary="ok",           note="Outcomes were provided but unsure whether positive or negative")
READING[22] = dict(fair=False,  boundary="inconsistent",           note="no results")
READING[23] = dict(fair=False,  boundary="inconsistent",           note="no results")
READING[24] = dict(fair=False,  boundary="inconsistent",           note="no results")
READING[25] = dict(fair=True,  boundary="ok",           note="no results")
READING[26] = dict(fair=True,  boundary="ok",           note="no results")
READING[27] = dict(fair=True,  boundary="ok",           note="no results")
READING[28] = dict(fair=True,  boundary="ok",           note="no results")
READING[29] = dict(fair=True,  boundary="ok",           note="no results")

does this look more right

## Claude  _12:29_

Better — five of the six are fixed. Let me verify the one I think you flipped the wrong way.

<details><summary>tools run</summary>

- `Bash: Confirm whether record 23 reports results`

</details>

## Claude  _12:30_

Confirmed — record 23 does report results. Flip it back.

```
"THE COMPANY ALSO ANNOUNCES PRELIMINARY RESULTS OF THE ONE YEAR PHASE III
 SAFETY STUDY WITH INDIPLON"

"completion of the Company's one-year safety clinical trial with the immediate
 release formulation of indiplon in adult patients with Chronic Primary Insomnia.
 Based on preliminary observation of data collected this study demonstrate[s]…"

"536 patients were randomized and 211 patients completed one year of dosing
 (target: 100 patients)"
```

Results were reported. It's a **safety** study with no efficacy endpoint, so no direction can be determined — which is `inconclusive` applied *correctly*, not incorrectly.

```python
READING[23] = dict(fair=True, boundary="ok",
                   note="Announces preliminary results of the one-year Phase III safety study "
                        "with indiplon; 536 randomised, 211 completed one year of dosing "
                        "(target 100). Safety study with no efficacy endpoint, so no direction "
                        "determinable — inconclusive correctly applied here, unlike [20]/[22]/[24].")
```

That record is actually valuable to you: it's the **control** for the `inconclusive` category, the one case where the label means what it's defined to mean. Having it strengthens the argument about 20, 22 and 24 rather than weakening it.

## The five other fixes are right

10, 14 and 17 to `inconsistent`; 20, 22, 24 to `fair=False`; record 2's note now quotes the endpoint. All check out.

## One still open: records 17 and 19

Unchanged, and still judged differently on the same structure:

| | primary endpoint | anything met in *this* readout | label | your call |
|---|---|---|---|---|
| 17 LYRA | missed | no — only "well tolerated" | `mixed-negative` | `fair=False` |
| 19 CLDX | missed | no — male efficacy is from *"this previous study"* | `mixed-negative` | `fair=True` |

Pick one rule:

- **Strict** (evidence from this readout only) → 19 becomes `fair=False`, and `boundary="inconsistent"` naming 17 and 6.
- **Lenient** (prior-study evidence counts as "some met") → 17 becomes `fair=True`, and the mismatch with record 6 stays as the boundary flag you've already set.

I'd take the strict reading — the categories describe what a filing reports about a trial's endpoints, and importing a different trial's result is the same move that made record 13 wrong. But it's your call; just apply it to both.

## Where the totals land

With 23 reverted, and 19 left as `fair=True`:

| category | fair | boundary inconsistent |
|---|---|---|
| positive | 5/5 | 0 |
| negative | 5/5 | 0 |
| mixed-positive | 4/5 | 3 (10, 11, 14) |
| mixed-negative | 3/5 | 4 (15, 16, 17, 18) |
| inconclusive | 2/5 | 3 (20, 22, 24) |
| no_result | 5/5 | 0 |
| **total** | **24/30** | **10/30** |

If you take the strict reading on 19, it's **23/30** and 11 boundary flags.

Either way you land within one record of the 24/30 already in the notebook — but now every one of those judgements has a quoted sentence and a named counterpart behind it, and you have a boundary count where before you had a single worked example.

Want me to write the final `READING` into cell 11 and regenerate the table? Settle record 19 first and I'll put the whole thing in at once — then cells 12, 22 and 38 need their numbers updated to match.

## You  _12:31_

lets go with strict on 19, write it into cell 11 and then update the other cells too please

<details><summary>tools run</summary>

- `Bash: Locate every citation of the 24/30 figure`
- `Bash: Build and test the filled reading record`

</details>

## Claude  _12:32_

**23 of 30** fair, **11 of 30** boundary-inconsistent. Writing it in.

<details><summary>tools run</summary>

- `Bash: Write the filled reading into cell 11 and verify`

</details>

## Claude  _12:33_

Now cell 12 — replacing the typed table and the surrounding prose.

<details><summary>tools run</summary>

- `Bash: Read cell 12 before editing`
- `Bash: Rewrite cell 12 table and add the boundary finding`
- `Bash: Find the Q1d claims that need updating`
- `Bash: Update the Q1d summary`

</details>

## Claude  _12:34_

585 words — over the 500 limit. Trimming.

<details><summary>tools run</summary>

- `Bash: Read the full Q1d to trim`
- `Bash: Trim Q1d back under 500 words`
- `Bash: Second trim pass on Q1d`
- `Bash: Final trim to get Q1d under 500`
- `Bash: Get Q1d safely under the limit`

</details>

## Claude  _12:35_

496 words. Now the AI-use disclosure.

<details><summary>tools run</summary>

- `Bash: Update the AI-use disclosure and verify`
- `Bash: Commit and push the completed reading`

</details>

## Claude  _12:37_

Pushed (`7abf12d..e4b3762`). Everything runs and the notebook is valid.

## What went in

**Cell 11** — `READING` filled for all 30, strict rule applied to 19. Output:

| category | fair | boundary inconsistent |
|---|---|---|
| positive | 5/5 | 0 |
| negative | 5/5 | 0 |
| mixed-positive | 4/5 | 3 |
| mixed-negative | 2/5 | 5 |
| inconclusive | 2/5 | 3 |
| no_result | 5/5 | 0 |
| **total** | **23/30** | **11/30** |

**Cell 12** — the typed table is gone; it's now generated by the cell above, with a boundary column added. The failure-mode list gained a fourth mode setting out the three boundaries with their record pairs, and `[12]` and `[23]` named as the controls where the categories *are* applied as documented.

**Cell 38 (Q1d)** — 24→23, the inconclusive claim corrected, and a new paragraph on the framing bias. **496 words.** I had to trim about 90 words to fit; the cuts were compression, not content — the only thing folded away was the standalone "blind spot" heading, since Neurogene is an instance of the same optimism bias and now sits inside that paragraph.

**Cell 39 (AI use)** — records that the 30-record reading is yours from the original text, that the extraction was Claude's, which 13 records were worked through in conversation and what those raised, and where you changed your own first answers (20/22/24 to not-fair, 23 back to fair, 19 to not-fair for consistency). It also carries a **TO DO** that the Q1 session isn't in `ai_logs/` yet.

## Why the boundary result is the stronger half

You went in with one worked example (the Tonix pair in cell 15) and came out with three distinct boundaries, each with named counterpart records and a quotable sentence — and a direction: the label always lands softer than the endpoint outcome warrants. That maps directly onto the rubric's top band, which asks for systematic patterns across the whole sample and for separating boundary disagreement from outright misreading. Your record now does both, and `[12]`/`[23]` as controls are what stop it reading as "the labels are just noisy".

## Left to do

1. **`ai_logs/`** — the Q1 session, plus the Q2 and Q3 sessions. `compile_ai_logs.py` hasn't been run. Cell 39 flags it in bold.
2. **Full re-run** — Q2 and Q3 still reflect the pre-fix cleaning; the new cells 11 and 13 are unexecuted. Q2c check 4 needs re-verifying since it reads `filing_kind`.
3. **Three limitation paragraphs** you have measurements for but haven't written: sentence-filter loss (33% at `hi=400`, decks 52%), `RE_SAFE` over-deleting in 151 filings, `RE_DECK` missing KOL-event decks.
4. **Q4, Q5, video link.**

One thing worth deciding before the re-run: cell 15's two-filing boundary demonstration now overlaps with the fuller account in cell 12. It still earns its place — it's the only side-by-side text comparison — but you may want a line there pointing forward to the three-boundary summary rather than presenting it as the headline finding.

## You  _13:09_

okay lets move on to validating q1a part 2 analysis, starting in cell expected and def sign_table cell

<details><summary>tools run</summary>

- `Bash: Read the Analysis 2 setup cell`
- `Bash: Read the EXPECTED / sign_table cell`
- `Bash: Check for duplicates, zero CARs and silently dropped labels`
- `Bash: Compare as-classified vs deduplicated record level`

</details>

## Claude  _13:13_

Cell 18 is sound. It runs correctly, the numbers reproduce, and the design is right — but there are four things a marker could ask about, and one is a genuine gap in the stated method.

## What the cell does correctly

**`EXPECTED` encodes the label's claim, not the outcome.** `mixed-positive → +1` even though those filings average −6.6%. That's the right way round: the test is whether the market went where the *label* implies, so the −6.6% is a finding rather than a coding error.

**Two levels reported, and the reason is stated.** Record level and filing level, because 1,073 records sit in multi-drug filings sharing one CAR. Reporting both rather than picking one is the right call.

**The statistical tests are the right ones.** Mann-Whitney is non-parametric, which matters because CAR is heavy-tailed and winsorised — a t-test alone would be criticisable. The one-sample t-tests against zero are a reasonable supplement.

**The framing in cell 17 is the strongest part.** It says up front that the check is deliberately weak and that a high disagreement rate is not itself evidence of error, then commits to a falsifiable prediction: disagreement should not depend on document type if the labels are sound. That's what makes cell 21 evidence rather than description.

## Four things to be able to answer

**1. The record level double-counts 108 records.** `sign_table(event_res, "outcome")` doesn't deduplicate, so 108 of the 2,392 are repeated `(accession, drug_name)` pairs. The banner says "as classified", so this looks deliberate — but it's never stated, and cell 8 *does* deduplicate for the sample, so the two treatments differ without explanation.

Good news: it barely matters.

| | as classified | deduplicated |
|---|---|---|
| n | 2,392 | 2,284 |
| overall disagreement | 48.0% | 47.8% |
| positive | 50.7% | 50.5% |
| mixed-positive | 66.0% | 65.7% |
| negative | 29.2% | 28.9% |

One sentence saying "record level is deliberately as-classified; 108 rows are duplicates and dropping them moves the rate by 0.2 points" turns this from an oversight into a robustness check.

**2. 42 composite labels are dropped without mention.** The banner says `no_result` and `inconclusive` are excluded, but `positive/negative` (9), `mixed-positive/mixed-negative` (12), and five other combinations — 42 records — also vanish, because they're not keys in `EXPECTED`. Dropping them is defensible (there's no single expected direction), but the banner should say so, especially since these are the undocumented categories you flag at 100% in Q1b.

**3. Winsorisation caps 50 records in this subset.** 26 sit exactly at −84.2% and 24 at +94.5%. Signs are unaffected, so the disagreement rates are safe — but `mean_car` is computed on censored data, and the −19% / +2.4% figures inherit that. You already note this in cell 21's methodology table; worth a clause here too.

**4. 29 records have |CAR| < 0.1%.** No CAR is exactly zero, so `np.sign()` never returns 0 and the edge case doesn't bite. But for those 29 the "sign" is noise, and they're counted as firm agreements or disagreements.

## Suggested addition

Rather than change the analysis, add a short robustness block to the cell — it answers all four in one place:

```python
# What the record-level table is and is not: it is as-classified, so the 108
# duplicated (accession, drug_name) rows are counted twice, and the 42 records
# carrying undocumented composite labels are dropped with no expected direction.
_d  = rec_d
_dd = _d.drop_duplicates(["accession", "drug_name"])
print("Robustness of the record-level rate:")
print("  as classified   %.1f%% (n=%d)" % (100 * _d.disagrees.mean(), len(_d)))
print("  deduplicated    %.1f%% (n=%d)" % (100 * _dd.disagrees.mean(), len(_dd)))
print("  dropped: %d composite-label records with no single expected direction"
      % (~event_res.outcome.isin(list(EXPECTED) + ["inconclusive", "no_result"])).sum())
print("  %d records sit at the winsorisation bounds; %d have |CAR| < 0.1%%, where the sign is noise"
      % ((_d.car_3day.abs() > 0.84).sum(), (_d.car_3day.abs() < 0.001).sum()))
```

Want me to add that, or move on to the next Analysis 2 cell (19, the disagreement investigation)?

## You  _13:14_

sure add it

<details><summary>tools run</summary>

- `Bash: Draft and test the robustness block`
- `Bash: Insert the robustness block and verify`
- `Bash: Commit and push the robustness block`

</details>

## Claude  _13:17_

Two more commits landed on the remote. Checking them before I merge.

<details><summary>tools run</summary>

- `Bash: Inspect the two new remote commits`

</details>

## Claude  _13:17_

The remote has **130 cells** to my 133 — three of my cells are gone. Let me map exactly what's there before touching anything.

<details><summary>tools run</summary>

- `Bash: Map the remote notebook structure`

</details>

## Claude  _13:18_

Understood — those deletions look deliberate. Let me take the remote as the base and re-apply only my robustness edit.

<details><summary>tools run</summary>

- `Bash: Merge remote and re-apply the robustness block`
- `Bash: Verify the merged notebook runs`
- `Bash: Re-verify stopping before the encoder cell`
- `Bash: Commit the resolved merge and push`

</details>

## Claude  _13:20_

Pushed (`2d61b9a..f45f005`). The robustness block is in, on the version with your restructuring.

## What it now prints

```
Robustness of the record-level disagreement rate
  as classified          48.0%  (n=2392)
  deduplicated           47.8%  (n=2284, 108 repeated records removed)
  composite labels dropped for having no single expected direction: 42 records
  at the winsorisation bounds: 50 records; |CAR| < 0.1% (sign is noise): 29 records

                as classified  deduplicated
positive                0.507         0.505
mixed-positive          0.660         0.657
negative                0.292         0.289
mixed-negative          0.346         0.351
```

The banner also now names the composite labels among the exclusions, since it previously listed only `no_result` and `inconclusive`.

## On the merge

You'd made three edits while I was working, and git's textual auto-merge on notebook JSON would have produced something plausible-looking and wrong. I discarded my local copy, took yours whole, and re-applied the single pending edit by locating the cell by content (`def sign_table`) rather than by index — so the renumbering couldn't put it in the wrong place. Verified afterwards: 130 cells, `READING` and `HAND_LABELLED` intact, everything through index 30 executes.

Renumbering the failure modes so the boundary finding is **(1)** is the right call — it's the strongest thing in Q1a and it was buried at the bottom.

## One thing to confirm

You removed the head/body window sensitivity cell and its commentary. That's your call and the notebook reads more tightly without it — but it was the evidence for two claims that are still load-bearing: that `classify_filing()`'s 1,200-character window isn't an artefact, and that the announcement/periodic gap holds at 16.4–17.6 points across every window from 600 to 4,000.

If a marker asks "why 1,200?", there's now no answer in the notebook. Options: leave it (defensible — the classifier is validated at 28/30 against your hand labels, which is the stronger evidence anyway), or drop one sentence into Q1c saying the window was tested from 600 to 4,000 and the gap held throughout. Happy either way, just flagging it so it's a decision rather than an accident.

## Next

Analysis 2 continues at cells 16, 17 and 18 — the disagreement investigation, the fresh selection of disagreement cases stratified by document type, and the three whole-table checks. Want to work through those next?

## You  _13:22_

Maybe lets drop a sentence into q1c to say the window was tested

<details><summary>tools run</summary>

- `Bash: Locate the Q1c cells`
- `Bash: Add the window-testing sentence to Q1c`
- `Bash: Commit and push the Q1c addition`

</details>

## Claude  _13:22_

Pushed (`f45f005..b95e7ac`). Added as a paragraph in cell 27, just before "What was deliberately left alone".

It opens by saying *why* it's in Q1c rather than Q1a — `classify_filing()` reads the cleaned text, so a cleaning change moves the Q1a document split and the Q1b event-validity signal with it. That makes it a downstream check on the cleaning rather than an orphan paragraph, which is the one thing that could have looked out of place.

It carries the three measurements:

- 600–4,000 characters reclassifies 25–165 of 3,794 filings (0.7%–4.4%), almost all decks read as announcements as the window widens
- sign agreement holds at every setting: 62.9–63.7% vs 46.1–46.6%, a gap of 16.4–17.6 points
- 1,200 kept although 2,400 scores better on your 30 (25/30 and 30/30 vs 23/30 and 28/30), because tuning on the validation documents would be circular

That last clause is the one worth having. It turns "we used an arbitrary number" into a deliberate methodological choice — and pre-empts a marker who notices 2,400 would have scored better.

**One caveat:** these numbers came from the cell you deleted, so they're now prose without a cell that regenerates them. They were measured on the corpus as it stands and I verified them at the time, but if the cleaning changes again — say you fix `RE_SAFE` — they'll go stale silently. Worth re-checking after the full re-run, or keeping a note that they were measured under the current `clean_filing_text()`.

Ready to move on to the Analysis 2 cells — 16 (disagreement investigation), 17 (fresh disagreement selection by document type), 18 (the three whole-table checks) — whenever you are.

## You  _13:25_

so cell 16 is just a quick check on the CAR against the record level and filing level, what is the difference between these two levels

<details><summary>tools run</summary>

- `Bash: Read cell 16`

</details>

## Claude  _13:25_

Cell 16 is the document-type analysis — the record/filing distinction is set up in cell 15. Let me get you concrete numbers for it.

<details><summary>tools run</summary>

- `Bash: Show the record vs filing level difference concretely`

</details>

## Claude  _13:26_

The REGN filing from record 8 shows the whole thing in one example.

## Record level — one row per *classified trial result*

`event_study_results`, 2,615 rows across 1,905 filings.

```
drug_name              outcome    car_3day
dupilumab (Dupixent)   positive    0.00391
dupilumab (Dupixent)   positive    0.00391
suptavumab             negative    0.00391
```

Three rows, **one CAR value repeated three times**. There is only one market reaction to this 8-K — +0.39% — but three classifications hang off it.

## Filing level — one row per *8-K*

`filing_summary`, 1,905 rows, one per filing.

```
n_drugs  outcomes                      primary_outcome  has_mixed_outcomes  car_3day
3        positive, positive, negative  negative         1                   0.00391
```

The three labels collapse to a single `primary_outcome`.

## What each one gets wrong

**Record level over-weights multi-drug filings.** 1,018 of 2,615 records sit in a filing with more than one drug. This REGN filing contributes three observations to the disagreement rate, all sharing one CAR — so a single market event is counted three times. Worse, the same CAR is scored as *agreeing* with `negative` and *disagreeing* with `positive` simultaneously, which is guaranteed by construction, not a finding.

**Filing level throws information away.** Collapsing to `primary_outcome` keeps `negative` and discards both `positive` labels. You go from 2,615 observations to 1,905, and the two dupilumab classifications — real classifications the pipeline made — vanish from the analysis entirely.

The distribution: 1,470 filings have one drug, 294 have two, and the tail runs to eight. Only 79 filings carry genuinely conflicting labels (`has_mixed_outcomes`), so most of the collapsing is harmless — but those 79 are exactly the interesting ones.

## Why the notebook reports both

Neither level is right on its own, so picking one would mean choosing which distortion to accept silently. Reporting both makes the choice visible, and the two agree closely — record level 48.0% overall disagreement, filing level in the same region — which is itself the reassurance that the multi-drug problem isn't driving the result.

## The one thing to watch

`primary_outcome` is derived by the upstream pipeline, not by you, and the methodology doesn't spell out how it picks. In this filing it chose `negative` from `positive, positive, negative` — the minority label. That may be a deliberate "worst outcome wins" rule, or it may be first-in-order. Worth a sentence in your write-up saying you don't know which, since every filing-level number depends on it.

This also connects to Q3a, which states the same problem in modelling terms: 955 records sit in a filing that reported more than one trial result and share one CAR, so the target variable isn't independent across rows. Q1a's two-level reporting is the diagnostic; Q3a is where it has to be handled.

## You  _13:28_

so then cell 17 checks based on document and filing_kind comes straight from the meta data right

## Claude  _13:28_

Careful — that's the one thing to be clear on: **`filing_kind` is not metadata.** Let me confirm which cell you mean first.

<details><summary>tools run</summary>

- `Bash: Read cell 17 and check the database for a document-type column`

</details>

## Claude  _13:29_

**No — `filing_kind` is your own construction, not metadata.** This one matters, because claiming it came from the data would be an error a marker could catch.

## The database has no document-type column

```
filing_text        :: accession, filing_text
filing_summary     :: accession, ticker, event_date, car_3day, n_drugs,
                      outcomes, primary_outcome, has_mixed_outcomes
consensus_outcomes :: accession, ticker, filing_date, drug_name, phase,
                      indication, outcome, consensus_type, evidence,
                      statistics, flagged
event_study_results:: accession, ticker, event_date, drug_name, phase, ...
```

Nothing about document type anywhere. `filing_text` has exactly two columns.

`filing_kind` is created by `classify_filing()` — the regex you wrote, applied to the cleaned text — and attached to `filing_txt` as a new column. The join in cells 16 and 17 is onto that in-memory column, not onto anything from SQLite.

This is why cell 12's validation against `HAND_LABELLED` exists at all. Nobody validates `outcome` — that's the given data you're evaluating. `filing_kind` needs evidence precisely because you built it, and 28/30 on the announcement split is that evidence.

## What cell 17 actually does

It's not the document-type check — that's cell 16. Cell 17 draws a **fresh selection of disagreement cases to read**, and its banner gives two reasons for stratifying by document type rather than by size of move:

1. A disagreement inside a quarterly report and one inside a genuine announcement are candidates for different explanations. Ranking by |CAR| would have surfaced only the second kind.
2. **`car_3day` is winsorised at the 1st and 99th percentiles** — 54 records sit at exactly −84.2% or +94.5%, so "the largest disagreements" returns ties rather than the true extremes.

That second point is the sharper one, and it's a real methodological catch: the obvious approach (sort by |CAR|, read the top 10) is broken by the censoring, and the cell says so and works around it. It's also, per your AI-use note, one of the things that was wrong in a first attempt and got fixed.

Cell 17 is what satisfies the brief's second dot point — *"For a selection of these disagreements, read the underlying 8-K filing to assess whether the disagreement reflects a classification error, market expectations, or other factors."*

## For the write-up

Be precise about provenance in three tiers, because they carry different burdens:

| | source | who validates it |
|---|---|---|
| `outcome`, `car_3day`, `n_drugs` | database, produced upstream | you evaluate it — that's the question |
| `filing_kind`, `n_prior_refs` | **your regex over the filing text** | you must, and you did (28/30) |
| `READING` | your reading of the filings | your own record, now auditable |

If a marker asks "where does document type come from?", the answer is "I derived it and validated it against 30 filings I read by hand" — which is a stronger answer than "it was in the data", and it's the true one.

## You  _13:35_

So what is going on in cell 18

<details><summary>tools run</summary>

- `Bash: Read cell 18 in full`
- `Bash: Run cell 18 and test the drug-token defect`

</details>

## Claude  _13:36_

This is a real finding, and it's a headline number.

## What cell 18 does

Three whole-table checks that the 30-record reading pointed at:

**(a) Duplicate `(filing, drug)` classifications.** Groups by accession and drug name, then classifies each record three ways:

```
unique                         4280
repeated, same label            170
repeated, CONFLICTING labels     89
```

89 records where the *same drug in the same filing* carries two different outcome labels. That's the substring-containment matching the methodology warns about, and it feeds `S1_conflicting_duplicate` at weight 3. You saw an instance in record 23 — three rows for one NBIX filing, `indiplon` plus `NBI-42902` twice.

**(b) Does the classified drug name appear in the filing at all?** Searches the **raw** text, and the docstring explains why — the safe-harbour block lists product names and `clean_filing_text()` deletes it, so checking the cleaned text would report a drug absent when your own cleaning removed the only mention. That's a genuinely careful piece of reasoning.

**(c) Reliability by `consensus_type`.** Sign agreement grouped by provenance — does `b3b_only` behave worse than `agree`? This is what justifies `S9_single_prompt` and `S10_stats_override`.

## The defect in (b)

`drug_present()` calls `drug_tokens()`, which begins:

```python
name = re.sub(r"\(.*?\)", "", str(name))     # deletes the parenthetical
```

So the parenthesised name — usually the brand name or the chemical description — is thrown away before searching. The consequences are worse here than in `result_sentences()`, because some drug names are *almost entirely* parenthetical:

```
ALO-02 (oxycodone/naltrexone ER)              searched for: []   ← nothing
VX-371 (ENaC inhibitor)                       searched for: []
SOF/VEL (sofosbuvir/velpatasvir)              searched for: []
F/TAF (emtricitabine/tenofovir alafenamide)   searched for: []
CHS-0214 (biosimilar etanercept)              searched for: ['0214']
```

After stripping the parenthetical and dropping tokens of ≤3 characters, several drugs have **no search tokens left at all** — and `drug_present()` returns `bool(toks) and ...`, which is `False` when `toks` is empty. So the drug is recorded as "not found in the filing" without any search being performed.

**Measured: of the 455 records reported absent, 199 are found once the parenthetical name is also searched. The corrected count is 256, not 455.**

## Where that number appears

| location | claim |
|---|---|
| cell 18 output | "455 of 2,845 (16.0%)" |
| cell 12 | "two records name drugs whose text does not appear in the filing at all" |
| cell 19 | "455 records (16.0%) name a drug that appears nowhere in the filing" |
| cell 21 (`S2_drug_absent`) | weight **3**, 455 records triggering |
| cell 22 | the 551-record "label is wrong" union |

`S2_drug_absent` is a weight-3 signal — the joint-highest — so roughly 200 records are being pushed toward the review queue on a search that never ran. The flag rate and queue ordering both shift.

## The fix

One line, in `drug_tokens()` or in a variant used by `drug_present()`:

```python
def drug_tokens(name, keep_parenthetical=False):
    inner = re.findall(r"\(([^)]*)\)", str(name)) if keep_parenthetical else []
    name = re.sub(r"\(.*?\)", "", str(name))
    toks = [t.lower() for t in re.split(r"[^A-Za-z0-9]+", name) if len(t) > 3]
    toks += [t.lower() for g in inner for t in re.split(r"[^A-Za-z0-9]+", g) if len(t) > 3]
    return list(dict.fromkeys(toks))[:6]
```

Keep the current behaviour for `result_sentences()` if you like — there, stripping is defensible, since you want sentences about the drug rather than about its formulation. But for "does this name appear anywhere in the filing", searching the full name is clearly right.

Unlike the earlier fixes, **this one doesn't touch `clean` or the embeddings** — it only changes `S2_drug_absent`, so the blast radius is Q1b's flag counts and queue, not Q2 or Q3. That makes it much cheaper to apply than the cleaning changes we deferred.

Want me to make the change and re-run Q1b so you can see how the flag rate and the tier-1 queue move?

## You  _13:42_

sure we can add that but cell 18 is about cap_lo and cap_hi

## Claude  _13:42_

You're right, and we've drifted by one — your cell numbering is one ahead of my zero-based index. Let me pin cells by their content from here rather than by number.

<details><summary>tools run</summary>

- `Bash: Read the cap_lo/cap_hi cell in full`

</details>

## Claude  _13:43_

Right — the `cap_lo`/`cap_hi` cell. Here's what it's doing, then I'll apply the `drug_tokens` fix.

## The problem it solves

The brief asks you to read a selection of disagreements. The obvious way is "sort by |CAR|, take the biggest". Two things break that:

**Winsorisation.** `car_3day` is capped at the 1st and 99th percentiles, so 54 records (2.1%) sit at *exactly* −84.2% or +94.5%. Sorting by |CAR| returns that block of ties first — records whose true value is unknown and unordered. You'd be reading the censoring, not the extremes.

```python
cap_lo, cap_hi = event_res.car_3day.min(), event_res.car_3day.max()
contra = contra[(contra.car_3day > cap_lo) & (contra.car_3day < cap_hi)]
```

Strict inequalities drop every pinned record, so what's left is genuinely measured.

**Selection bias.** Ranking by size alone would return almost entirely genuine announcements, because those are where the big moves are — the very thing cell 16 establishes (median |CAR| 11.4% in announcements vs 5.1% in periodic reports). You'd have read only the cases that support the market-expectations explanation and never seen a mis-dated one.

```python
picks = (contra[contra.filing_kind.isin(["results announcement", "periodic report"])]
         .sort_values("abs_car", ascending=False)
         .groupby("filing_kind").head(4))
```

Four from each document type — the largest *within* each stratum. So you get the biggest announcement disagreements *and* the biggest periodic-report disagreements, which are candidates for different explanations.

That's the design point: the brief asks whether a disagreement is a classification error, a market-expectations effect, or something else. You can only distinguish those if the selection contains all three kinds, and stratifying is what guarantees that.

The cell then prints the top two per stratum with their result sentences, for reading.

## One thing to note

It reuses `result_sentences(clean_by_acc...)` — the cleaned text, `k=4`. So the deck and sentence-filter caveats we found apply to these excerpts too. Worth reading the raw text for any of these you quote in the write-up.

Now the fix.

<details><summary>tools run</summary>

- `Bash: Apply the drug_tokens fix`
- `Bash: Re-run Q1 and check the new absent count and flag rate`
- `Bash: Find hardcoded references to the 455 figure`
- `Bash: Update the hardcoded figures and re-check the flag rate`

</details>

## Claude  _13:45_

Flag rate moved 44.5%→42.4%. Updating the prose that cites it.

<details><summary>tools run</summary>

- `Bash: Get the full updated flagging table`
- `Bash: Update the flagging prose and Q1d`
- `Bash: Find the actual flagging prose cell`
- `Bash: Apply the prose updates and verify`
- `Bash: Locate Q1d and its exact flagging sentence`
- `Bash: Apply all prose updates and verify`
- `Bash: Commit and push the drug-token fix`

</details>

## Claude  _13:49_

Pushed (`b95e7ac..0918566`).

## The fix and what moved

`drug_tokens()` now takes `keep_parenthetical`, defaulting to `False` so sentence ranking is untouched. `drug_present()` opts in, because its question is "does this name appear at all" rather than "which sentences are about this drug".

| | before | after |
|---|---|---|
| drug absent | 455 (16.0%) | **256 (9.0%)** |
| `S2_drug_absent` triggering | 455 | 256 |
| flagged at `risk >= 3` | 2,019 (44.5%) | **1,926 (42.4%)** |
| label-is-wrong union | 551 (12%) | **356 (8%)** |

Per-category flag rates updated too — `negative` 37.5%→33.0%, `positive` 59.0%→55.7%, `mixed-positive` 87.8%→83.9%. Prose updated in the disagreement table, the signal provenance string, the flagging discussion and Q1d. Q1d still 496 words.

**Nothing here touches `clean_filing_text()` or the embeddings**, so this one doesn't add to the Q2/Q3 re-run debt — unlike the cleaning changes we deferred.

## Worth noting for the write-up

The 8% figure is now the honest answer to "how often is the classification actually wrong", as distinct from "how often is this row unusable". It dropped by a third because a weight-3 signal was firing on a search that never ran. That's a good thing to be able to say you caught — it's the difference between a screen that measures the data and one that measures its own bug.

It also makes the Q1a story tighter: the dominant problem is now unambiguously **event validity** (1,946 records, unchanged), not label error. Which is exactly what your Q1d recommendation already says — restrict to genuine announcements.

## Numbering

To stop us drifting again: your cell numbers run one ahead of my zero-based index. From here I'll name cells by content — "the `sign_table` cell", "the flagging discussion" — and give your number when I have it. The `cap_lo`/`cap_hi` cell we just discussed is your 18.

Next in Analysis 2 is the three-checks cell (your 19) — duplicates, drug presence, and reliability by `consensus_type`. We've just been through (b); (a) and (c) are unexamined.

## You  _13:54_

lets look at the three checks cell, what is this doing

<details><summary>tools run</summary>

- `Bash: Run the three-checks cell and show its full output`

</details>

## Claude  _13:55_

Three whole-table checks, each one taking something you noticed in the 30 records and asking how common it is across all 4,539.

## (a) Duplicate `(filing, drug)` classifications

Groups by accession + drug name, then labels each record by what the group looks like:

```python
n_rows, n_distinct = grp.transform("size"), grp.transform("nunique")
dupes[named] = np.where(n_distinct > 1, 2,          # same drug, different labels
                np.where(n_rows > 1, 1, 0))         # same drug, same label
```

```
unique                         4280
repeated, same label            170
repeated, CONFLICTING labels     89
```

The examples are the interesting part — all three are Eli Lilly:

```
ramucirumab            negative                       b3b_inconclusive_override
ramucirumab            positive/negative              flagged_disagreement
Cyramza (ramucirumab)  positive                       b1a_only
Cyramza (ramucirumab)  mixed-negative                 b1a_only
Tanezumab              mixed-positive/mixed-negative  flagged_disagreement
Tanezumab              mixed-negative/mixed-positive  flagged_disagreement
```

Three distinct pathologies in six rows:

- **Row 1–2:** the same drug appears once as `negative` and once as the composite `positive/negative`. The pipeline both resolved and failed to resolve the same conflict.
- **Row 3–4:** `positive` and `mixed-negative` for one drug in one filing, and **both are `b1a_only`** — the same prompt returned two contradictory answers about the same drug. That isn't prompt disagreement; that's one reader disagreeing with itself.
- **Row 5–6:** `mixed-positive/mixed-negative` and `mixed-negative/mixed-positive` — the *same composite*, order reversed, stored as two different labels. Pure string artefact.

That last one is worth a sentence. It means the "undocumented composite categories" you flag at 100% are partly an artefact of ordering, not seven genuinely distinct categories.

## (b) Drug presence — the one we just fixed

**256 of 2,845 (9.0%)**, down from 455 once brand names are searched. Note the concentration:

```
positive        166
negative         30
mixed-positive   29
inconclusive     20
```

**Two thirds of the remaining absences are `positive` labels.** A confident positive classification on a drug whose name never appears in the filing is the most suspicious combination in the table, and it's the largest block.

## (c) Reliability by provenance

```
consensus_type              n     sign_agreement  median_abs_car
agree                    1268           0.550           0.075
b1a_only                  390           0.474           0.051
b3b_only                  346           0.491           0.051
b3b_inconclusive_override 325           0.489           0.051
same_direction             60           0.500           0.068
```

This is the check that justifies `S9_single_prompt`. Records where both prompts agreed reach **55.0%** sign agreement; single-prompt records sit at **47.4%** and **49.1%** — indistinguishable from a coin toss. The `b3b_inconclusive_override` records, where B3b defaulted to `inconclusive` and B1a's call was taken, also sit at 48.9%.

So the provenance field the methodology records does carry real information about reliability, and dual-confirmed records are meaningfully better.

## The confound to be honest about

`median_abs_car` moves with `sign_agreement`: 0.075 for `agree`, 0.051 for the single-prompt types. Larger moves are easier to get the sign right on, and both prompts are likelier to find a result in a filing that reported a big one. So some of the 55% vs 47% gap is that dual-confirmed records sit in more informative filings, not that dual confirmation makes a label better.

The cleanest way to separate them would be to compare within document type, or within a |CAR| band. That's a couple of lines, and it would turn a suggestive gap into a controlled one — which is the kind of thing the rubric's top band rewards.

Want me to add that control, or move on to the Analysis 2 conclusion cell?

## You  _12:07_

okay lets keep validating, i am moving onto q1c cell 27 where raw = filing_txt.filing_text starts with that code

<details><summary>tools run</summary>

- `Bash: Find and read the Q1c raw-text cell`
- `Bash: Run the Q1c inspection cell and probe the regex`

</details>

## Claude  _12:09_

This is the Q1c "look before you clean" cell, and it's the right instinct — the brief explicitly says *"the filing text was extracted programmatically and provided without cleaning, so examine it before deciding what to do with it."* This cell is the examination.

## What it does

**Basic shape** — 3,794 filings, 0 to 318,166 characters, median 19,186. Note the **minimum is 0**: at least one filing has empty text.

**A verbatim sample** — first 600 characters of one filing, showing the cover-page boilerplate as it actually arrives.

**Prevalence probes** — five regexes counting how many filings carry each defect:

```
SEC cover page                   1590   41.9%
Safe-harbour / forward-looking   3389   89.3%
Signature page                   1498   39.5%
Smart quotes / bullet glyphs     3742   98.6%
Slide-deck spaced hyphens        1478   39.0%
```

This is what justifies each rule in `clean_filing_text()`, and it's the right order of operations — measure the problem, then write the rule, rather than writing rules and asserting they were needed.

**Before/after distribution** — mean 27,309 → 22,530, median 19,186 → 13,906.

## Three things worth tightening

**1. The safe-harbour probe undercounts, for the reason the cell itself documents.** It searches `forward-looking statements` with a literal hyphen. But the row below reports that 39% of filings have slide-deck spaced hyphens — and those decks render it `forward - looking statements`, which the probe misses.

```
'forward-looking statements'       3389 filings
allowing spaces around the hyphen  3548 filings   (+159)
```

**159 filings undercounted**, and they're exactly the decks. Ironic given the next probe exists to find that spelling. One-line fix: `r"forward\s*-\s*looking statements"`.

**2. "One filing" is unidentified.** `raw.iloc[0]` happens to be `0000059478-12-000018` (Eli Lilly, Q3 2012 earnings). Worth printing the accession — otherwise a reader can't check the example, and row order isn't guaranteed stable.

**3. `min = 0` isn't followed up.** At least one filing has no text at all. That matters downstream: an empty filing produces empty `clean`, no drug match, and no result sentences. Worth counting how many and noting whether they carry classifications.

## One reading of the before/after table

The 25th percentile falls 12,743 → 8,542 (−33%) while the 75th falls 29,985 → 24,599 (−18%). Short filings lose proportionally more, which is what you'd expect when what's removed is fixed-size boilerplate — cover page and signature block are roughly constant regardless of document length. That's a sanity check the cleaning is behaving sensibly, and it's currently in the output but not commented on.

Also worth noting: `max` barely moves, 318,166 → 317,009. The largest filing is almost entirely substance.

Want me to fix the hyphen probe, print the accession, and add the empty-filing count? All three are contained to this cell and don't touch `clean`, so no downstream effect.

## You  _12:22_

i dont get what the prevalence probles mean

## Claude  _12:22_

"Prevalence probe" was my phrase — the notebook just calls it *"How widespread each issue is"*. Here's what it actually is.

<details><summary>tools run</summary>

- `Bash: Demonstrate what the probes do on a tiny example`

</details>

## Claude  _12:22_

It's a **word search that counts documents.** Nothing more complicated than that.

For each of the five patterns, `raw.str.contains(pattern)` asks every one of the 3,794 filings "do you contain this, yes or no?", and the table reports how many said yes.

```
"cover page"      matches filing [0]  ->  1 of 4  (25%)
"safe harbour"    matches filing [1]  ->  1 of 4  (25%)
"spaced hyphens"  matches filing [2]  ->  1 of 4  (25%)
```

**It counts filings, not occurrences.** A filing saying "forward-looking statements" fifty times counts once, same as one saying it once. So `89.3%` means *"3,389 of the 3,794 filings contain a safe-harbour block somewhere"* — not that 89% of the text is safe-harbour.

## Why the cell does it

Each row is the evidence for one rule in `clean_filing_text()`. That's the whole point — it pairs one-to-one:

| the probe searches for | how many filings | which rule it justifies |
|---|---|---|
| "Check the appropriate box below" | 1,590 (41.9%) | `RE_COVER` |
| "forward-looking statements" | 3,389 (89.3%) | `RE_SAFE` |
| "Pursuant to the requirements of the Securities" | 1,498 (39.5%) | `RE_TAIL` |
| smart quotes, bullets `' ' " " ▪ • ·` | 3,742 (98.6%) | the `MOJIBAKE` dict |
| `well - tolerated` (spaced hyphens) | 1,478 (39.0%) | the slide-deck hyphen rule |

Read down the table and it says: *"here are five things in the raw text, here is how common each one is, and that is why I wrote five cleaning rules."*

The brief asks you to examine the text before deciding what to do with it. This table is that examination, expressed as numbers rather than an assertion. Without it, the cleaning function is five regexes with no stated justification.

## What the numbers tell you

- **98.6% have character damage** — near-universal, so the `MOJIBAKE` repair applies to almost everything.
- **89.3% have a safe-harbour block** — the most widespread structural problem, and the one your commentary says matters most, because it's full of the exact vocabulary a result classifier keys on ("futility analyses", "interim results").
- **~40% each for cover page, signature and spaced hyphens** — these three cluster because they're format-dependent. Roughly two fifths of filings arrive as full 8-K documents with cover and signature; roughly two fifths are slide decks with the spaced hyphens.

That last point is a genuine observation you could make in the write-up: the corpus is roughly two thirds full filings and one third decks, and the cleaning has to handle both.

## The bug I mentioned

The safe-harbour probe searches `forward-looking statements` with a normal hyphen — but decks write `forward - looking statements`, and there are 1,478 decks. So it misses 159 filings and reports 89.3% when the true figure is 93.5%.

The row directly beneath it exists to detect that exact spelling. Worth fixing, since the table is your justification for the cleaning and one of its numbers is understated.

## You  _12:25_

Want me to fix the hyphen probe, print the accession, and add the empty-filing count? yes fix these please and update the table

<details><summary>tools run</summary>

- `Bash: Fix the probe, print the accession, add the empty-filing count`

</details>

## Claude  _12:26_

All three in. Now the prose that cites the old figure.

<details><summary>tools run</summary>

- `Bash: Find prose citing the old safe-harbour figure`
- `Bash: Read the Q1c commentary bullets`
- `Bash: Update the Q1c commentary with the new figures`
- `Bash: Commit and push the Q1c fixes`

</details>

## Claude  _12:27_

Pushed (`0918566..2b774cc`).

## What the cell now prints

```
Filing text, raw: 3794 filings, 0 - 318166 characters (median 19186)
Filings with no text at all: 1; classifications attached to them: 1

First 600 characters of 0000059478-12-000018, verbatim:
...

How widespread each issue is:
                                                filings_affected   pct
SEC cover page ('Check the appropriate box')                1590  41.9
Safe-harbour / forward-looking block                        3548  93.5   ← was 3389 / 89.3
Signature page                                              1498  39.5
Smart quotes / bullet glyphs                                3742  98.6
Slide-deck spaced hyphens ('well - tolerated')              1478  39.0
```

The probe now reads `r"forward\s*-\s*looking statements"`, with a comment saying why the spacing matters and pointing at the deck row two lines below.

## The commentary

Each bullet in "What the text needed" now carries its prevalence figure, and I added the observation that the cover-page, signature and spaced-hyphen counts all cluster near 39–42% because they're format-dependent — roughly two fifths of the corpus is a full 8-K with cover and signature, roughly two fifths is a slide deck. That's the kind of thing that reads as having actually looked at the data rather than just run the numbers.

Plus a short paragraph on the empty filing.

## The empty filing

Exactly **one**, carrying **one classification**. Small enough that it changes nothing, but it's now stated rather than sitting silently behind a `min = 0`. It's also a legitimate small point for Q1b — that record can never be validated by any text-based signal, so it should arguably be excluded rather than reviewed.

Nothing here touched `clean_filing_text()`, so no downstream numbers moved.

Q1c continues with the structured-field cleaning cell, the leakage-column cell, and then the vectorisation — where the embeddings-vs-TF-IDF test lives. That last one is the part still blocked on the model download.

## You  _12:29_

what does cell 29 do q1c step 2

<details><summary>tools run</summary>

- `Bash: Read the Q1c step 2 cell`
- `Bash: Run the Q1c step 2 cell`
- `Bash: Check the phase bucketing and the duplicate resolution`

</details>

## Claude  _12:31_

This cell prepares the modelling table for Q2 and Q3, and it does four things. Two are clean; two involve silent decisions worth knowing about.

## What it does

**(i) Phase, from free text.** 234 distinct raw phase strings collapse into five buckets via `phase_bucket()`. The database's own `phase_clean` gives four categories with 107 in "Other"; this reduces that to 33 unknown.

**(ii) Numeric fields stored as TEXT.** `pd.to_numeric(..., errors="coerce")` on six columns. Roughly 2,200 of 2,615 rows convert — so about 400 rows have no enrolment, arm count or site count.

**(iii) Drop duplicate `(accession, drug_name)` rows.** 2,615 → 2,482.

**(iv) Linkage quality.** `disclosure_lag_days` — days from the linked study's primary completion to the filing. **Mean −109 days, and 748 rows are negative**, meaning the registry says the trial completed *after* the 8-K announced its result. That's a linkage problem, and reporting it is the right call: `lag_quality` shows 1,173 clean, 465 suspect, 400 missing, 275 interim, 169 noisy.

## The two silent decisions

**1. `drop_duplicates(keep="first")` resolves 36 genuine label conflicts by row order.**

Of the 245 rows in repeated groups, 83 rows across **36 groups** have *conflicting* outcome labels. `keep="first"` picks whichever happened to be first, with no rule:

```
IMBRUVICA (ibrutinib)      kept=negative        discarded=['positive']
IMBRUVICA (ibrutinib)      kept=positive        discarded=['negative']
vismodegib (GDC-0449)      kept=inconclusive    discarded=['positive']
Rindopepimut (CDX-110)     kept=mixed-negative  discarded=['positive']
Cabozantinib               kept=positive        discarded=['inconclusive' ×3]
Pregabalin CR              kept=positive        discarded=['positive', 'negative']
```

The two IMBRUVICA rows are the clearest illustration — in one filing the arbitrary winner is `negative`, in another `positive`. These are the same 89 conflicting duplicates you flag at weight 3 in Q1b as evidence the labels are unreliable, and here they're being resolved by nothing at all.

It's only 36 rows of 2,482, so the effect is small. But the cell reports "Dropped 133 exact (filing, drug) duplicates" — and **they aren't all exact**. 83 of those rows disagree about the outcome. The word "exact" is doing work it hasn't earned.

Options: state it ("36 groups conflict; kept the first, affecting 36 of 2,482 rows"), or drop conflicting groups entirely rather than picking arbitrarily. Either is defensible; the current silence isn't.

**2. `phase_bucket()` tests `"4" in s` as a bare substring.**

Every other test uses word boundaries — `\b3\b|iii|pivotal` — but Phase 4 is checked first and with a plain substring search. Consequences visible in the data:

```
Phase 3 (EF-14 pivotal trial)                       -> Phase 4   (the "4" is in "EF-14")
Phase 3 (POD1UM-303 and POD1UM-304)                 -> Phase 4   ("304")
Integrated long-term data (Studies 201, 202, 401)   -> Phase 4   ("401")
Phase 1b (24-week extension)                        -> Phase 4   ("24-week")
Phase 2/3 (Study 045)                               -> Phase 4   ("045")
Phase 3/4 (SUMMIT survival study)                   -> Phase 4   (correct)
```

**Six of the 30 "Phase 4" rows are trial names and week counts containing the digit 4.** Phase 4 is the smallest bucket, so a fifth of it is wrong. `re.search(r"\b4\b|post-approval|post-marketing", s)` would fix it — though note "Phase 3b/4" and "Phase 3B/4" need the `/4` to still match, which `\b4\b` does.

Also worth a look: `Phase 3b` and `Phase IIb` land in **unknown**, because `\b3\b` doesn't match "3b" and `\bii\b` doesn't match "IIb". That's 5 + 2 rows that should bucket cleanly.

## Suggested

Both are contained — `phase_bucket` feeds a Q3a feature, and the duplicate handling affects 36 rows. Neither touches `clean` or the embeddings.

Want me to fix the phase regex and make the duplicate resolution explicit? I'd report the conflicts in the output rather than change the `keep="first"` behaviour, so the analysis stays as-is but the decision becomes visible.

## You  _12:33_

yep lets fix that

<details><summary>tools run</summary>

- `Bash: Fix the phase regex and surface the conflicting duplicates`
- `Bash: Verify the corrected phase buckets`

</details>

## Claude  _12:35_

Almost — "Phase 3 (EF-14 pivotal trial)" still lands in Phase 4. My second alternative was redundant and matched the "4" in "EF-14".

<details><summary>tools run</summary>

- `Bash: Tighten the regex and verify the Phase 4 bucket`

</details>

## Claude  _12:36_

Every Phase 4 entry now genuinely says 4, post-approval or post-marketing.

<details><summary>tools run</summary>

- `Bash: Verify and push the Q1c step 2 fixes`

</details>

## Claude  _12:37_

Pushed (`2b774cc..2887414`).

## Phase bucketing

| bucket | before | after |
|---|---|---|
| Phase 3 | 1,315 | 1,325 |
| Phase 2 | 1,028 | 1,030 |
| Phase 1 | 209 | 211 |
| unknown | 33 | 26 |
| **Phase 4** | **30** | **23** |

Seven of the thirty Phase 4 rows were trial names and durations — "EF-14", "Study 045", "24-week extension", "Studies 201, 202, 401". Every remaining entry genuinely says 4, post-approval or post-marketing.

`\b4\b` still matches "Phase 3b/4" because the slash is a word boundary, but refuses the trailing 4 of "EF-14". Adding the a/b suffixes also rescued "Phase 3b" and "Phase IIb" from `unknown`.

What's left in `unknown` is genuinely unbucketable — `Preclinical`, `NDA`, `BLA (registration)`, `PK/BE study`, `Feasibility Study`. Those aren't phases.

## Duplicate reporting

The output now reads:

```
Dropped 133 duplicate (filing, drug) rows -> 2482 analysis rows
  of the dropped rows, 47 sat in 36 groups whose labels CONFLICT; keep='first' picks
  one by row order, so 36 of the 2482 analysis rows carry an arbitrarily chosen label.
```

plus six examples. Behaviour unchanged — 2,482 rows either way — but the decision is visible. The word "exact" is gone, since 47 of those rows weren't.

The ibrutinib pair is the one I'd quote if asked: one filing keeps `negative`, another keeps `positive`, for the same drug, decided by nothing.

## Where Q1c stands

Remaining in this section: the leakage-column cell (step 3), then vectorisation (steps 4–6) — the embeddings, the dimensionality reduction, and the fitness test. The vectorisation cells are the ones still blocked on the model download, so they can be read but not re-run here.

The leakage cell is worth a look next — it's the one that lists the nine columns held back because they aren't observable at the filing date, and it feeds directly into the Q3b leakage demonstration.

## You  _12:42_

so what is the requirements for these phases

<details><summary>tools run</summary>

- `Bash: Show the bucketing rules in action and what the phases look like`

</details>

## Claude  _12:43_

Two answers, depending on which you meant.

## The rules in the code

Tested top-down, **first match wins**, highest phase first:

| bucket | matches if the string contains |
|---|---|
| **Phase 4** | `4` as a whole word, or `post-approval`, or `post-marketing` |
| **Phase 3** | `3` / `3a` / `3b` as a whole word, or `iii`/`iiia`/`iiib`, or `pivotal` |
| **Phase 2** | `2` / `2a` / `2b`, or `ii`/`iia`/`iib` |
| **Phase 1** | `1` / `1a` / `1b`, or `i`/`ia`/`ib` |
| **unknown** | none of the above |

In practice:

```
Phase III        -> Phase 3      Phase 1/2    -> Phase 2
Phase 2b         -> Phase 2      Phase 2/3    -> Phase 3
Phase IIb        -> Phase 2      Phase 3b/4   -> Phase 4
Pivotal          -> Phase 3      Preclinical  -> unknown
Post-marketing   -> Phase 4      NDA          -> unknown
```

**The ordering encodes a decision worth stating: a combination trial buckets to the higher phase.** "Phase 1/2" becomes Phase 2, "Phase 2/3" becomes Phase 3. That's defensible — a 1/2 trial is being run for its Phase 2 purpose — but it's a choice, and it isn't written down anywhere. `Pivotal → Phase 3` is a second such choice: "pivotal" means registrational, which is normally Phase 3, but the word doesn't say so literally.

## What the phases mean clinically

- **Phase 1** — safety and dose-finding. Small (median enrolment 72 here), often single-arm, no efficacy claim.
- **Phase 2** — first real efficacy signal, dose selection. Median 109.
- **Phase 3** — confirmatory, registrational; the trial an approval rests on. Median 366.
- **Phase 4** — post-approval, run after the drug is already marketed. Median 900.

The enrolment medians in your own table track that ordering cleanly — 72 → 109 → 366 → 900 — which is a decent sanity check that the bucketing is working.

## Why it matters to the assignment

Phase is a proxy for how much is at stake. A Phase 3 miss kills a registration; a Phase 1 result is a step on a long road. It's used in the Q2 clustering feature space and as a Q3a feature.

One thing to notice in the table, though:

```
              rows  med_enrol  med_abs_car
Phase 1        207       72.0      0.061
Phase 2        976      108.5      0.073
Phase 3       1252      366.0      0.059
Phase 4         22      900.0      0.030
```

**Median absolute market reaction does not rise with phase** — Phase 2 (7.3%) actually moves more than Phase 3 (5.9%). That's a real result rather than an error: Phase 3 readouts are more anticipated and more priced in, while Phase 2 carries more surprise. It also fits your Q1a finding that good news is partly expected.

Worth a sentence in Q3 if the model finds phase weak — it isn't that phase doesn't matter, it's that phase and surprise pull in opposite directions.

## You  _12:47_

how do we know what the lag quality is

<details><summary>tools run</summary>

- `Bash: Find how lag_quality is defined in the methodology`

</details>

## Claude  _12:47_

The methodology has **no entry for `lag_quality` or `disclosure_lag_days`** — the grep found nothing. Let me reverse-engineer it from the data.

<details><summary>tools run</summary>

- `Bash: Check the methodology and reverse-engineer lag_quality`
- `Bash: Work out what distinguishes the lag_quality categories`

</details>

## Claude  _12:48_

Two things — where the table comes from, and a correction I owe you.

## Where the table comes from

Straight from the database. In the Q1c step 2 cell:

```python
enriched = pd.read_sql("SELECT * FROM event_study_enriched", conn)
...
display(enriched.lag_quality.value_counts(dropna=False).to_frame("rows"))
```

`lag_quality` and `disclosure_lag_days` are **columns in `event_study_enriched`**, produced by the upstream pipeline. You didn't compute them — the cell just counts the values. Same for `disclosure_lag_days.describe()`.

So unlike `filing_kind` (yours) this is given data, like `outcome`.

## But it isn't documented

I grepped `methodology.md` for both column names: **zero matches.** Section 7 describes the linkage in detail — two-pass candidate search, LLM disambiguation, match rates, confidence levels — and never mentions how lag quality is assigned.

Reverse-engineering it from the data, the categories look like a cross of *lag sign* and *trial status*:

| | trial status | lag range | reading |
|---|---|---|---|
| `clean` (1,235) | COMPLETED 1,151 | −60 to 730 | completed trial, plausible lag |
| `suspect` (483) | COMPLETED 398 | −3,294 to 3,835 | completed, implausible lag |
| `interim` (287) | still recruiting/active | −4,105 to −62 | filing well before completion → genuine interim |
| `noisy` (178) | still active | −38 to 710 | still running, yet filed at or after the recorded completion date |

That's a coherent scheme, but **it's my inference, not documentation.** `clean` and `noisy` overlap almost exactly on lag (−60…730 vs −38…710), so lag alone doesn't separate them — status does.

The 432 nulls are the 412 rows with no linked study, plus 20 with a study whose `primary_completion` is missing.

**For the write-up:** you can report the distribution, but say the field's definition isn't in the methodology and that you inferred what it encodes. That's honest and it's another instance of your Q1a theme — the methodology documents its choices unevenly.

## The correction

Earlier, on `primary_outcome`, I said the methodology doesn't spell out how it picks and suggested writing that you don't know. **That was wrong.** Section 7 defines it:

> `filing_summary` — one row per accession with aggregated outcomes, primary outcome (**using severity hierarchy: negative > mixed-negative > mixed-positive > inconclusive > positive**), and a mixed-outcome flag

That explains the REGN example exactly: `positive, positive, negative` → `negative`, because negative outranks positive. It's a worst-case rule, not first-in-order.

That's better for you than what I said — the filing-level collapse is a documented, defensible rule, and worth stating as such rather than flagging as unknown.

## You  _13:59_

Oh so the clean suspect and interim are from the data

## Claude  _13:59_

Yes — `clean`, `suspect`, `interim` and `noisy` are values sitting in the `lag_quality` column of `event_study_enriched`. The upstream pipeline assigned them. Your cell only runs `value_counts()` on what's already there.

Same for `disclosure_lag_days` — a stored number, not something you computed from `primary_completion` and `event_date`.

## The three tiers of provenance in your notebook

Worth having straight, because they carry different burdens:

| | source | what you must say about it |
|---|---|---|
| `outcome`, `car_3day`, `lag_quality`, `disclosure_lag_days`, `primary_outcome` | database, upstream | given data — you evaluate it |
| `filing_kind`, `n_prior_refs`, `phase_bucket`, `READING` | **your code / your reading** | you must justify and validate it |
| `enrollment_num` etc. | given, but type-converted by you | trivial, no burden |

`lag_quality` is firmly in the first row. If a marker asks "how did you decide which links were suspect?", the answer is "I didn't — the dataset did."

## The catch

The methodology documents the linkage step at length — two-pass search, LLM disambiguation, match rates, confidence levels — but **says nothing about `lag_quality` or `disclosure_lag_days`.** Zero mentions.

So you're reporting a data-quality field whose construction rule isn't published. My reading of the values, which is inference rather than documentation:

- **`clean`** — trial COMPLETED, lag plausible (−60 to 730 days)
- **`suspect`** — trial COMPLETED, lag implausible (−3,294 to 3,835 days)
- **`interim`** — trial still recruiting, filing well before completion → a genuine interim readout
- **`noisy`** — trial still active, yet filed at or after the recorded completion date → contradictory

Note `clean` and `noisy` cover almost the same lag range, so lag alone doesn't separate them — trial status does. That's why it can't just be a binning of `disclosure_lag_days`.

## What I'd write

Something like: *"`lag_quality` is supplied by the dataset and is not defined in the methodology; from the values it appears to combine the sign of the disclosure lag with the trial's registry status. I report the distribution but do not rely on the categories, since their construction cannot be checked."*

That's accurate, and it's a third instance of your Q1a theme — the methodology is thorough about some steps and silent on others. You already make that point about the statistics field being extracted and never saved, and about B1b being tested and rejected without recording what it cost.

## You  _14:00_

so anyways moving onto cell 30 is leakage stuff?

<details><summary>tools run</summary>

- `Bash: Read the leakage cell`
- `Bash: Run the leakage cell and check downstream use of the lag columns`
- `Bash: Check how the lag columns are handled downstream`

</details>

## Claude  _14:02_

Yes — this is the leakage cell, and it's one of the better-constructed parts of Q1c.

## What it does

**Blocks ten columns**, each with a stated reason, in two families:

*Mechanical* — parts of the target itself: `ar_day0` (a component of `car_3day`), `car_3day_raw` (same event pre-winsorisation), `alpha`/`beta` (market-model parameters fitted around this event), `n_evt_days`.

*Temporal* — the more interesting kind. The banner states it exactly: **ClinicalTrials.gov and Drugs@FDA were scraped once, in 2026, so every status field holds today's value, not the value at the filing date.** An 8-K from 2012 whose drug was approved in 2019 carries `fda_approved = 1`.

**Then quantifies the damage** rather than asserting it:

```
overall_status          size    mean CAR
COMPLETED               1484     -0.021
ACTIVE_NOT_RECRUITING    298     +0.012
TERMINATED               141     -0.122   ← −12.2%
RECRUITING               140     -0.001
```

`TERMINATED` averages **−12.2%** against −2.1% for completed. A trial stopped because the drug failed reads TERMINATED forever, so that column is close to reading the answer off the future. Same for FDA approval: −2.7% vs −0.5%.

Showing the leak's size is what makes this convincing. "These columns are leaky" is an assertion; "this one separates the target by 10 points" is evidence.

**Catches a type trap:** `fda_approved` is stored as the strings `'True'`/`'False'`, so `pd.to_numeric` would silently produce all-NaN. Worth knowing about generally.

**Justifies a retention:** `market_cap` is kept, and the test is stated — it varies within ticker for **260 of 317 tickers**, consistent with a point-in-time measure rather than a 2026 snapshot. That's the right way to defend keeping a borderline field.

## The thing I went looking for — and it's handled

`primary_completion` is blocked with the note "drives `disclosure_lag_days`". So the obvious question is whether `disclosure_lag_days` itself leaks through unblocked. It doesn't:

```python
LEAKY["lk_disclosure_lag"] = q3.disclosure_lag_days      # cell 86, held back
"disclosure_lag_days": (["lk_disclosure_lag"],
    "built from a completion date revised after the fact")  # cell 100, tested
```

It's one of the nine columns held back in Q3a and added back one at a time in Q3b purely to measure what it would have bought. Correct handling, and better than blocking — it turns a limitation into a measurement.

## One inconsistency worth a sentence

`lag_quality` is used in **cell 67** (Q2c, sponsor/cluster checks) as `clean_disclosure_lag`:

```python
clean_disclosure_lag=("lag_quality", lambda v: (v == "clean").mean())
```

`lag_quality` is derived from `primary_completion` — the same 2026-snapshot field blocked here and whose numeric child is quarantined for Q3. So the same information is quarantined in Q3 and used freely in Q2.

That's **defensible**, and your own Q1c commentary already gives the reason: Q2 is descriptive and doesn't partition, so leakage doesn't apply the way it does under cross-validation. But the notebook doesn't say it in this cell, and a marker who notices `disclosure_lag` on both sides of the line will want the distinction stated.

One clause in the BLOCKED discussion would close it — something like: *"these are blocked for Question 3, where they would leak across folds; Question 2 is descriptive and does not predict the target, so `lag_quality` is used there as a linkage-quality diagnostic rather than a feature."*

Want me to add that?

## You  _14:04_

so what does cell 32 q1c step 4 do

<details><summary>tools run</summary>

- `Bash: Read the Q1c step 4 vectorisation cell`

</details>

## Claude  _14:04_

This is the vectorisation step — where filing text becomes numbers for Q2 and Q3.

## The core decision

**It doesn't embed the filing.** The banner says why: after cleaning the median filing is still thousands of characters, mostly commercial narrative about other products. Embedding all of that would produce a vector describing *the company*, not *this trial's result* — and two filings with opposite outcomes would look similar, which is exactly the failure your Q1c commentary predicts from the safe-harbour block.

So each record is reduced first, then embedded:

```
clean text  →  result_sentences(k=3, hi=400)  →  3 sentences  →  encoder  →  3 vectors  →  mean  →  1 vector
```

## The mechanics

**`SentenceTransformer(MODEL_DIR if os.path.isdir(MODEL_DIR) else MODEL_HUB)`** — local copy if present, hub otherwise. Sensible for a notebook a marker has to run. This is also the line that blocks me: there's no `models/` directory here and Hugging Face is blocked, which is why everything from this cell down can't be re-executed in this session.

**`embed_records()`** — three things worth noticing:

1. **It flattens then re-splits.** All sentences from all records go into one list, encoded in one call with `batch_size=128`, then sliced back per record by position. That's a real speed decision — one batched call instead of ~2,500.
2. **Double normalisation.** `normalize_embeddings=True` gives unit vectors, then after averaging it re-normalises: `E / np.linalg.norm(E, axis=1, keepdims=True)`. Necessary — the mean of unit vectors isn't a unit vector — and it means downstream distances are cosine-equivalent, which matters for the Q2 clustering.
3. **Records reuse `result_sentences()`**, the same helper the Q1a hand-reading used, so the features and your reading rest on the same selection logic.

**384 dimensions** out (MiniLM-L6-v2), reduced later in step 6.

## The parameters, and what we already know about them

`k=3, hi=400` — tighter than the `k=10, hi=600` default, and tighter than the `k=4` used for reading. These are the two numbers our earlier measurements bear on directly:

- **`hi=400` discards 33% of characters on average, and 52% for decks.** 1,009 filings (27%) lose more than half their text before a single sentence is scored, because slide decks have no sentence punctuation and split into chunks far above 400 characters.
- **`k=3` with the drug-name bonus** means the three winning sentences skew toward sentences naming the drug. We measured **31 subject-less result sentences across 30 filings** — "The study did not meet its primary endpoint" — that the drug-token requirement pushes down the ranking.

So for a meaningful minority of records, the vector is built from whatever prose survived, which in decks is disproportionately risk-factor boilerplate. That's the limitation to write up, and it's a candidate explanation for the Q3b finding that the text adds little once company features are present.

## What I can't verify

This cell has `execution_count: 18` and stored output from the pre-`RE_TAIL`-fix run. Since `clean` changed, **the embeddings currently stored are stale** — they were built from text that was missing the exhibits for 1,215 filings. Everything downstream in Q2 and Q3 inherits that.

That's the single biggest reason the full re-run still matters.

The next cell is the one that actually calls this three times to compare sentence counts — that's where the `k` choice gets tested rather than assumed.

## You  _04:51_

what does question 1c step 5 do, is it just testing with different k folds to see AUC

<details><summary>tools run</summary>

- `Bash: Read the Q1c step 5 cell and its stored output`

</details>

## Claude  _04:52_

Two things to correct, and one of them is yours improving.

<details><summary>tools run</summary>

- `Bash: Compare the AUC output before and after the cleaning fix`

</details>

## Claude  _04:52_

## First, the correction: `k` is not folds

`k` is **how many sentences go into each record's vector**. The folds are fixed at `cv=5` throughout — they never vary.

```python
for k in [1, 3, 10]:
    E = embed_records(enriched, k=k)      # 1, 3 or 10 sentences per record
    cross_val_score(..., cv=5, ...)       # always 5 folds
```

So the sweep is over the *representation*, not the evaluation.

## What the cell actually tests

It asks: **can this vectorisation recover something about the filing that we know independently?** The probe is whether a logistic regression on the vectors can tell `positive` from `negative` — 2,031 records, 18% negative.

The banner is explicit that this is a **diagnostic on the features, not a model for Q3** — Q3 predicts signed CAR, not the label. The point is only that a representation which can't recover "good news vs bad news" isn't carrying the information Q2 and Q3 need.

Three comparisons in one table:

| | what varies |
|---|---|
| `sentences_embedded` 1 / 3 / 10 | how much text per record |
| `AUC_384_dims` vs `AUC_50_components` | full embedding vs PCA to 50 |
| TF-IDF row | a bag-of-words baseline on the *same three sentences* |

That last one is the most valuable design choice — same input text, different representation, so the comparison isolates the encoder rather than confounding it with sentence selection.

## Second: you've re-run this, and the fix helped

The stored output has changed since I last read it, so the numbers I quoted earlier in this session are superseded:

| | before `RE_TAIL` fix | now |
|---|---|---|
| k=1, 384 dims | 0.665 | **0.696** |
| k=3, 384 dims | 0.709 | **0.751** |
| k=10, 384 dims | 0.697 | 0.728 |
| k=3, 50 components | 0.659 | **0.728** |
| **TF-IDF** | 0.802 | **0.888** |

Every figure improved, and the PCA row improved most (0.659 → 0.728), which makes sense — recovering the exhibits gave the components real signal to work with instead of boilerplate variance. **That's clean evidence the cleaning fix was worth making**, and it's worth saying so in Q1c: the same diagnostic before and after, same folds, same subset.

## What the results say

**k=3 is the right choice, and it's tested.** 1 sentence underperforms (0.696), 10 is worse than 3 (0.728 vs 0.751) — more sentences dilute the signal with surrounding narrative. A genuine interior optimum, which is a much better justification than picking 3 by feel.

**TF-IDF beats the embeddings decisively: 0.888 vs 0.751.** That gap has *widened* since the fix (0.086 → 0.137 points). On this task a bag of words is substantially better than a sentence encoder — plausibly because the discriminating evidence is specific tokens ("did not meet", "p=0.009", "discontinued") rather than semantics, and MiniLM is trained on general prose, not trial readouts.

**The brief required embeddings** ("your vectorisation should include word or sentence embeddings with dimensionality reduction applied"), so keeping them isn't optional. But the honest conclusion — which your commentary already reaches — is to keep both representations rather than choose, because the embeddings satisfy the requirement and TF-IDF carries more signal.

**PCA to 50 costs little**: 0.751 → 0.728 at k=3, down from a 5-point loss before the fix. Cheap compression now.

Worth updating the Q1c commentary to the new figures — it still cites the old 0.709/0.802 pair. Want me to check and fix those?

## You  _04:55_

what is tf-idf

## Claude  _04:55_

It's the oldest way of turning text into numbers, and on your data it's beating the neural encoder — so worth understanding properly.

<details><summary>tools run</summary>

- `Bash: Demonstrate TF-IDF on three short documents`

</details>

## Claude  _04:55_

## The idea

**TF-IDF = Term Frequency × Inverse Document Frequency.** It turns each document into one number per word, and the number answers: *"is this word distinctive of this document?"*

Two ingredients multiplied together:

- **TF** — how often the word appears in *this* document. Appears a lot → higher.
- **IDF** — how rare the word is across *all* documents. Appears in few documents → higher.

So a word scores high only if it's frequent here **and** rare elsewhere. That's the whole trick.

Look at what happened to `the` in the demo: it appears in all three documents, so IDF = 1.00 and its weight stays at 0.22–0.24 everywhere — it carries no information, and the maths discovers that by itself. Meanwhile `not` appears in one document of three, IDF = 1.69, and gets weight 0.41 in the document that has it and 0 elsewhere.

Each row of that table is the document's vector. In your notebook the vocabulary is up to **20,000 columns** (`max_features=20000`) instead of ten, with most entries zero — a sparse vector.

## Your settings

```python
TfidfVectorizer(min_df=5, max_features=20000, stop_words="english", ngram_range=(1,2))
```

- `min_df=5` — ignore words appearing in fewer than 5 documents (drops typos and one-off drug codes)
- `stop_words="english"` — drop "the", "of", "and" outright
- **`ngram_range=(1,2)`** — count word *pairs* as well as single words. This one matters a lot here: it means `"did not"`, `"not meet"`, `"primary endpoint"` are features in their own right, not just the separate words.

## Why it beats the embeddings on your data

**TF-IDF has no idea what words mean.** To it, `"failed to achieve"` and `"did not meet"` are completely unrelated features — no shared representation, no notion of synonyms. That's normally its weakness, and it's exactly what sentence embeddings exist to fix.

But your discriminating evidence *is* specific tokens. `"did not meet"`, `"p=0.009"`, `"discontinued"`, `"futility"` — these are near-formulaic in trial announcements. Companies use the same phrases. TF-IDF keeps them exactly; MiniLM compresses them into 384 general-purpose semantic dimensions and blurs the distinction between "met" and "did not meet", which in general English are very similar sentences about endpoints.

Hence 0.888 versus 0.751.

## Where it appears in your notebook

Twice, doing different jobs:

- **Here in Q1c**, as the baseline that tests whether the embeddings are worth anything.
- **In Q2b**, as the *discriminator* — and there the reason is different. The banner says "no dimensionality reduction, so individual terms stay identifiable", then fits a random forest to see which terms distinguish clusters. You can read a TF-IDF feature's name ("pneumococcal", "quarterly"); you cannot read embedding dimension 137. That interpretability is why Q2b uses TF-IDF and Q2a uses the embeddings.

That contrast is a good thing to be able to state: the two representations are kept because they fail differently and because one is legible and the other isn't.

## You  _04:57_

yep update the q1c commentary with the new AUC figures

<details><summary>tools run</summary>

- `Bash: Find the Q1c commentary citing AUC figures`
- `Bash: Check whether disclosure_lag_days is a feature or held back`

</details>

## Claude  _04:58_

Confirmed: `disclosure_lag_days` appears **only** in `LEAKY` — it's held back, not retained. The commentary says the opposite. Fixing both.

<details><summary>tools run</summary>

- `Bash: Update the Q1c commentary with the new AUC figures`
- `Bash: Commit and push the Q1c commentary update`

</details>

## Claude  _04:58_

Pushed (`2887414..6b45d0b`).

## What changed in the commentary

Three qualitative claims now carry their numbers:

- **k=3 is an interior optimum** — 0.751 against 0.696 at k=1 and 0.728 at k=10. Worth stating as an optimum rather than just "more is not better", because it shows the value was tested in both directions.
- **Reduction costs about two points** — 0.751 → 0.728.
- **The TF-IDF gap is fourteen points** — 0.888 vs 0.751, and I added the clause that it's on *identical input text*, so the comparison isolates the representation rather than confounding it with sentence selection. That's the methodological point that makes the comparison worth anything.

Plus a new paragraph recording the before/after: 0.709 / 0.659 / 0.802 pre-fix. The reduced embedding improving most (0.659 → 0.728) is the sharpest detail — before the fix, the first 50 components were largely describing boilerplate variance. That's direct evidence the `RE_TAIL` fix mattered, measured on the same folds and the same subset.

## The correction

The commentary said `disclosure_lag_days` "is retained but with care". It isn't retained — it appears only in `LEAKY` in Q3a, so it's never a feature. Now stated correctly: held back with the other eight candidates, added in Q3b only to measure what it would have bought. And the `lag_quality`-in-Q2c distinction is now explicit rather than left for a marker to query.

## One figure I couldn't verify

"Retaining about 63% of embedding variance" — that needs the embeddings, so I left it as-is. Worth confirming on your next local run, since the PCA variance will have shifted along with everything else.

## Where Q1c stands

The remaining cell is step 6 — dimensionality reduction, and the Q2-vs-Q3 distinction in how it's fitted. The commentary already covers that argument well (PCA fitted once for descriptive clustering, refitted per-fold inside the Q3 pipeline), so it's mostly a matter of checking the code matches what the prose claims — which is exactly the kind of mismatch we just found with `disclosure_lag_days`.

## You  _11:19_

So I have moved onto question 2, the commentary in cell 42 saying ARI are those numbers correct

<details><summary>tools run</summary>

- `Bash: Read the Q2 ARI cells`
- `Bash: Check the stored ARI output and the chosen solution's silhouette`
- `Bash: Compare the ARI output before and after the re-run`

</details>

## Claude  _11:20_

## Are the numbers right?

**ARI 0.98 — correct.** Stored output says 0.978 both before and after your re-run. Unchanged.

**Silhouette 0.119 — now 0.120.** The original run gave 0.119; your re-run after the `RE_TAIL` fix gives 0.120. One digit, but it's a quoted figure that no longer matches the cell above it.

**"Roughly twice" — fair.** The chosen k=8 solution scores 0.068, so 0.120 / 0.068 = 1.76×. "Roughly twice" is honest.

Want me to change 0.119 → 0.120? It's cosmetic but it's the kind of thing a careful marker cross-checks.

## What the commentary is saying

Here's the argument, in plain terms.

**The setup.** Half the features Q2 asks for — enrolment, masking, allocation, phase, sites — come from the linked ClinicalTrials.gov study. But the linkage failed for some rows: 395 of 2,482 have no linked study, so those fields are blank.

**The ordinary thing to do** with blank fields is impute them — fill each with the column median. That's what `naive_blocks()` does, and it's what most people would do without thinking about it.

**The trap.** Imputation fills every missing row with *the same values* — the median, by definition. So those 395 rows become **identical to each other** on every design field. They're not similar trials; they're rows that were filled in from the same recipe.

A clustering algorithm looks for tight groups. 395 rows sitting on exactly the same point is the tightest group in the data by a mile. So that's what it finds first:

```
design fields missing  False  True
cluster 0                  0    395     ← every unlinked row, and nothing else
cluster 1               2076     11
```

**ARI 0.978** measures how closely the clustering matches "did the registry linkage work?" — 1.0 would be exact. At 0.978 the first split the algorithm finds is essentially *that question*, not any question about trials.

**The sting is in the silhouette.** That artefact scores **0.120**, while the real eight-cluster solution scores **0.068**. The fake grouping looks *twice as good* on the standard quality metric. If you chose k and features by maximising silhouette — the textbook move — you would choose the artefact.

Hence the commentary's closing line: *"the best-separated grouping available is a grouping of the data collection, not of the trials."*

## Why keeping this cell is the right call

It would have been easier to apply the eligibility rule quietly and move on. Instead the notebook *demonstrates the failure it avoided* — which does three things:

1. Justifies dropping 395 rows, rather than leaving it looking like convenient sample-trimming.
2. Pre-empts "why didn't you just impute?"
3. Makes the low silhouette of the real solution (0.068) defensible, because you've shown that a higher silhouette here would be a worse answer.

That last point matters a lot for Q2 — 0.068 looks weak in isolation, and this cell is part of why it isn't the embarrassment it appears to be. The other part is cell 49, which scores the real solution against shuffled labels and column-permuted features.

## You  _11:27_

I can just change it myself

## Claude  _11:27_

Sure — it's in the markdown cell above the naive-clustering code, the sentence beginning "The silhouette for that solution (0.119)". Change it to 0.120.

I'll leave the file alone so we don't collide. Just note I have uncommitted work? No — my last change is pushed, so `origin/rz_working` is at `6b45d0b` and you're clear to edit.

Ready when you want to look at the next Q2 cell — the feature space (your cell 44) or the algorithm comparison (46) are the next substantive ones.

## You  _12:47_

can you export this conversation to the ai_logs folder

<details><summary>tools run</summary>

- `Bash: Check the ai_logs format and whether the compile script exists`

</details>

## Claude  _12:47_

Let me check whether the session transcript is on disk — that would give a genuine export rather than my recollection.

<details><summary>tools run</summary>

- `Bash: Look for the session transcript on disk`

</details>

## Claude  _12:47_

The transcript is there — 4.3 MB of JSONL. Let me inspect its structure and convert it to the same format as your existing log.

