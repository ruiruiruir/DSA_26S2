# Claude Code session transcript

*Session:* Validating Question 2 — Claude Code on the web (remote environment), model Opus 5  
*Session ID:* `77607ed5-2e51-5045-920b-bbab9c1ed057`  
*Span:* 17 September 2026 11:36 to 18 September 2026 16:40 (Sydney time)  
*Converted on 18 September 2026 from the session record by `export_claude_session.py`. Every prompt and every reply is included verbatim and unedited. As the AI-use guidance anticipates, tool output and the model's internal reasoning are omitted, and each tool call is listed by name. Background-task notifications and automatic app messages are shown as quoted markers so the replies to them read in context.*

---

### Thursday 17 September 2026

## You  _11:36_

I am going to validate question 2 right now and need some explanation starting with cell 42 where it explains eligibility rule, what is ARI and silhouette again

## Claude  _11:36_

<details><summary>tools run</summary>

- `Bash: Inspect repo state and files`

</details>

<details><summary>tools run</summary>

- `Bash: List notebook cells with indices`

</details>

<details><summary>tools run</summary>

- `Bash: Dump cells 39-42`

</details>

<details><summary>tools run</summary>

- `Bash: Dump cells 43-52`

</details>

<details><summary>tools run</summary>

- `Bash: Read saved cell dump`

</details>

<details><summary>tools run</summary>

- `Bash: Dump cells 52 and 69-71`

</details>

<details><summary>tools run</summary>

- `Bash: Check Q2b keywords and check 4 cells`

</details>

I read Q2a through Q2c in `DSA_2026_S2_Assignment_template.ipynb`. Explanation first, then something you need to know before you validate.

## Cells 40–42: the eligibility rule and why it's tested

**Cell 40 sets the rule.** Half the feature space Q2 asks for (phase, masking, allocation, intervention model, primary purpose, arms, enrolment, sites) lives in the linked ClinicalTrials.gov study, not in the filing. So a row with no registry linkage has no trial design to cluster on. The rule is stricter than "has an `nct_id`", because a few linked rows still have empty design fields:

```
2482 analysis rows → 2100 with a linked registration → 2076 with design fields populated
```

It then shows the 406 dropped rows are **not** a random subset (mean CAR +0.8% vs −2.2% kept; 34.5% Phase 3 vs 53.1%; median market cap $0.45bn vs $0.69bn), which is the honest way to state the cost of the exclusion.

**Cell 42 is the justification for the rule** — it shows what happens if you skip it. `naive_blocks()` does exactly what a default pipeline does: median-fill the numerics, `fillna("missing")` the categoricals, cluster all 2,482 rows. The result:

| | silhouette | ARI vs "design is missing" |
|---|---|---|
| k=2 | 0.120 | **0.978** |
| k=3 | 0.137 | 0.509 |

The first split the algorithm finds is not a kind of trial — it's whether the registry linkage worked. The cross-tab is nearly perfect separation (cluster 0 = 395 missing / 0 present; cluster 1 = 2,076 present / 11 missing). It happens because imputation gives every missing row *identical* values on every design field, so they form an artificially tight blob. And that artefact scores **0.120**, about 1.8× the 0.068 the real solution gets — the best-separated grouping available in this data is a grouping of the data collection. The last line, `cl = q2[has_design]`, is where the clustering set is fixed for the rest of Q2.

## Silhouette

For each point: `(b − a) / max(a, b)`, where `a` = mean distance to other members of its own cluster, `b` = mean distance to members of the nearest *other* cluster. The score for a solution is the average over all points.

- **+1** = points sit much closer to their own cluster than to any other; **0** = on the boundary; **negative** = on average closer to a neighbouring cluster than to its own (i.e. arguably mislabelled).
- It's an *internal* measure — no ground truth, just geometry in the space you built. So it rewards compact, well-separated blobs and is biased toward whatever your feature scaling emphasises.

Two things in the notebook show why it can't be the arbiter:

1. **Cell 46:** average-linkage Manhattan posts the *best* silhouette (0.106) and best Davies-Bouldin (1.428) while putting 95.3% of trials in one cluster and 1 trial in another. Degenerate, and the measure loves it.
2. **Cell 49:** the chosen solution gets 0.068. Shuffled labels get −0.008; k-means on column-permuted features (all marginals preserved, all joint structure destroyed) gets 0.021. So ~0.02 is what "k-means always returns a partition" buys you for free, and the real structure is weak but genuine. A plain therapeutic-area lookup — no clustering at all — scores 0.075, *higher*. What the clustering adds is combination (splitting within an area on design, stage, sponsor size), not separation, which is why validation moves to Q2b/Q2c.

## ARI (adjusted Rand index)

Agreement between **two partitions** of the same objects. Count pairs of trials: how many are together in both labellings, apart in both, together in one and apart in the other. The Rand index is the share of pairs the two agree on; **adjusted** subtracts the agreement you'd expect from two random labellings with the same cluster sizes and rescales, so:

- **1.0** = identical partitions (up to relabelling — it's invariant to which number a cluster is given, which is exactly why you use it instead of accuracy)
- **0.0** = no better than chance
- **negative** = worse than chance

It's used for two different jobs in Q2:

- **Correspondence to a known partition.** Cell 42's ARI 0.978 against the missingness indicator. Also cell 44 (is the combined solution just the text block or the structured block in disguise?) and cell 49's ARI 0.059 between labels and therapeutic area with area held out.
- **Stability.** Cells 47 and 70 refit k-means on bootstrap resamples and alternative seeds, then ARI the new labels against the fitted ones. Current output: mean 0.680 over 25 resamples (min 0.417, max 0.919), and 0.770–0.877 across five seeds. That says the broad shape is reproducible but exact membership isn't — hence "use membership as a starting point, then check by hand."

## Before you validate: the Q2 prose is describing a different run

Every narrative cell in Q2 disagrees with the outputs stored right above it. The cluster indices have been permuted and the numbers shifted — consistent with the recent Q1c commits changing the `txt_pc*` inputs and the notebook being re-executed without the markdown being revised.

| Cell | Prose says | Output says |
|---|---|---|
| 45 | Manhattan silhouette 0.162, DB 1.49 | 0.106, 1.428 |
| 45 | k=8 gives six clusters ≥100 | seven |
| 50 | 0.059 / shuffled −0.021 / permuted 0.023 | 0.068 / −0.008 / 0.021 |
| 50 | area lookup 0.070; held out 0.050 vs −0.024 | 0.075; 0.062 vs −0.010 |
| 50, 52 | cluster **3** is the residual, negative silhouette, largest at 492 | cluster 3 = 71 trials, silhouette **+0.152**, best reproduction (0.966). The residual is cluster **2** (281 trials, −0.019, worst reproduction 0.660) |
| 52 | sizes 33/71/330/492/376/120/261/393 | 143/142/281/71/319/405/433/282 |
| 55 | oncology = cluster 2, CNS = 4, vaccines = 1, cardio = 6 | oncology = 4, CNS = 6, vaccines = 3, cardio = 7, immune/derm = 1 |
| 71 | bootstrap ARI 0.52, seeds 0.46–0.85, cluster 1 at 96% | 0.680, 0.770–0.877, cluster 1 at 0.912 |

One of these is more than a stale number. **Check 4's finding no longer reproduces.** Cell 68 claims cluster 5 is a filing type, not a trial type — 1.7% results announcements against 19–36% elsewhere, 84.2% Q1b flag rate, SD 9.9%. In the current output, cluster 5 is 405 trials with 29.9% results announcements, and the document-type mix across all eight clusters is uniform (25–40% results announcements, 38–65% periodic reports). No cluster carries that signature now. So the "exclude cluster 5 from Question 4" conclusion — which Q2d and Q4 depend on — currently has nothing behind it.

Want me to rewrite the Q2 narrative cells against the current outputs, re-running the notebook first so you're validating against numbers that are actually reproducible? That would also settle whether the filing-type cluster genuinely disappeared or just moved.

## You  _11:42_

yep can you do that please

## Claude  _11:42_

<details><summary>tools run</summary>

- `Bash: Read setup cell and gitignore`

</details>

<details><summary>tools run</summary>

- `Bash: Read Q1c vectorisation cells`

</details>

<details><summary>tools run</summary>

- `Bash: Check installed packages and model dir`

</details>

<details><summary>tools run</summary>

- `Bash: Check pip and network reachability`

</details>

<details><summary>tools run</summary>

- `Bash: Check agent proxy policy and allowed hosts`

</details>

Full re-execution turns out to be blocked here — let me confirm exactly how far I can get before I touch anything.

<details><summary>tools run</summary>

- `Bash: Check execution counts across code cells`

</details>

<details><summary>tools run</summary>

- `ToolSearch: select:TaskCreate,TaskUpdate`
- `Bash: Extract all Q2 outputs to scratchpad`

</details>

<details><summary>tools run</summary>

- `TaskCreate: Cells 41, 45, 50, 52, 55, 59, 62, 65, 68, 71, 74, 75 in DSA_2026_S2_Assignment_template.ipynb narrate an earlier run. Rewrite each against the outpu`
- `TaskCreate: Cell 68 claims cluster 5 is a filing type (1.7% results announcements). Check cell 67's stored crosstab for any cluster carrying that signature in t`
- `TaskCreate: Q2d summary and Q4 may rely on 'exclude cluster 5' and other cluster indices from the old run. Find and correct or flag them.`

</details>

<details><summary>tools run</summary>

- `Bash: Read cell 51 full output`

</details>

<details><summary>tools run</summary>

- `Bash: Read cells 56-66`

</details>

<details><summary>tools run</summary>

- `Bash: Read cell 67 full output and 68-69`

</details>

<details><summary>tools run</summary>

- `Bash: Read cells 72-77`

</details>

<details><summary>tools run</summary>

- `Bash: Find cluster references in Q3 and Q4`

</details>

<details><summary>tools run</summary>

- `Bash: Read cell 55 in full`

</details>

<details><summary>tools run</summary>

- `Bash: Read cells 43 and 45 in full`

</details>

Now I have everything I need. Writing the replacements:

<details><summary>tools run</summary>

- `Bash: Rewrite Q2a narrative cells 41-50`

</details>

<details><summary>tools run</summary>

- `Bash: Check diff size after rewrite`

</details>

<details><summary>tools run</summary>

- `TaskUpdate`
- `Bash: Rewrite cells 52, 55, 59`

</details>

<details><summary>tools run</summary>

- `Bash: Rewrite cells 62, 65, 68, 71`

</details>

<details><summary>tools run</summary>

- `Bash: Rewrite cells 74 and 75, check Q2d word count`

</details>

<details><summary>tools run</summary>

- `Bash: Trim Q2d under the 500-word cap`

</details>

<details><summary>tools run</summary>

- `Bash: Final Q2d trim`

</details>

<details><summary>tools run</summary>

- `Bash: Update AI-use note for Q2`

</details>

<details><summary>tools run</summary>

- `Bash: Scan rewritten Q2 markdown for leftover old-run figures`

</details>

<details><summary>tools run</summary>

- `Bash: Apply two accuracy corrections`

</details>

<details><summary>tools run</summary>

- `Bash: Verify only markdown changed and structure intact`

</details>

<details><summary>tools run</summary>

- `Bash: Check markdown table column consistency`

</details>

Table is consistent. Committing and pushing:

<details><summary>tools run</summary>

- `TaskUpdate`
- `TaskUpdate`
- `TaskUpdate`

</details>

<details><summary>tools run</summary>

- `Bash: Commit the Q2 rewrite`

</details>

<details><summary>tools run</summary>

- `Bash: Push to rz_working`

</details>

<details><summary>tools run</summary>

- `Bash: Fetch remote and inspect new commits`

</details>

Remote has 21 commits I didn't have — including an end-to-end re-execution. Let me look before doing anything else.

<details><summary>tools run</summary>

- `Bash: Inspect remote notebook structure`

</details>

My rewrite was built on a stale checkout — the branch has moved 21 commits ahead, including a full re-execution and a Q2 reconciliation. Let me preserve my work as a patch and rebase onto reality.

<details><summary>tools run</summary>

- `Bash: Save patch and reset to remote head`

</details>

<details><summary>tools run</summary>

- `Bash: Save patch and keep the commit on a side branch`

</details>

<details><summary>tools run</summary>

- `Bash: Move rz_working to the remote head; the superseded commit is already saved on another branch and as a patch`

</details>

Now on the real head. Validating the current Q2 against its own outputs:

<details><summary>tools run</summary>

- `Bash: Dump current Q2 and read cells 40-46`

</details>

<details><summary>tools run</summary>

- `Bash: Read current cells 42-46`

</details>

<details><summary>tools run</summary>

- `Bash: Read current cells 47-54`

</details>

<details><summary>tools run</summary>

- `Bash: Read current cells 55-64`

</details>

<details><summary>tools run</summary>

- `Bash: Read current cells 65-74`

</details>

<details><summary>tools run</summary>

- `Bash: Read current cells 75-79`

</details>

Current Q2 is in much better shape than what I had. Running a systematic check of every numeric claim against its own outputs:

<details><summary>tools run</summary>

- `Bash: Check Q2d word count and Q4 cluster selection`

</details>

<details><summary>tools run</summary>

- `Bash: Read Q4 prose paragraphs citing Q2 figures`

</details>

<details><summary>tools run</summary>

- `Bash: Read Q4a comparable-set screen output`

</details>

<details><summary>tools run</summary>

- `Bash: Apply Q2 corrections`

</details>

<details><summary>tools run</summary>

- `Bash: Read cell 61 opening exactly`

</details>

<details><summary>tools run</summary>

- `Bash: Correct the check-1 reading of cluster 0`

</details>

<details><summary>tools run</summary>

- `Bash: Align cluster-0 label and fix stale Q4 figures`

</details>

<details><summary>tools run</summary>

- `Bash: Find exact line wrapping in Q4 cells`

</details>

<details><summary>tools run</summary>

- `Bash: Apply remaining corrections with exact line wrapping`

</details>

<details><summary>tools run</summary>

- `Bash: Show cell 125 lines around the check-4 claim`

</details>

<details><summary>tools run</summary>

- `Bash: Apply remaining corrections`

</details>

<details><summary>tools run</summary>

- `Bash: Find exact wrapping of the rare-disease sentence`

</details>

<details><summary>tools run</summary>

- `Bash: Apply remaining corrections and check diff`

</details>

<details><summary>tools run</summary>

- `Bash: Verify integrity and scan for remaining stale figures`

</details>

<details><summary>tools run</summary>

- `Bash: Proofread the corrected paragraphs`

</details>

<details><summary>tools run</summary>

- `Bash: Remove duplicated argument and fix cross-reference`

</details>

<details><summary>tools run</summary>

- `Bash: Final integrity and formatting check`

</details>

Committing and pushing:

<details><summary>tools run</summary>

- `Bash: Commit the validation corrections`

</details>

<details><summary>tools run</summary>

- `Bash: Push and clean up the superseded branch`

</details>

Pushed to `rz_working` as [d964ae7](https://github.com/ruiruiruir/DSA_26S2/commit/d964ae7).

## First, a correction that matters before you validate

My local checkout was **21 commits behind**. Everything I described in my previous message — the stale numbers, the cluster-3-vs-cluster-2 residual mix-up, the cluster-index permutation — had already been fixed on the branch by a full re-execution ("Execute the notebook end to end against the new grain", "Re-run with the sample order restored"). So don't act on the specific figures in that message; they describe a notebook state that no longer exists. The conceptual explanation of ARI and silhouette stands, but the cluster indices I attached to it do not.

What changed under the new run, for the cells you were reading:

| | what I told you | current notebook |
|---|---|---|
| clustering set | 2,076 rows | **1,975** — 101 feature-identical rows collapsed (new cells 43–44 explain the grain) |
| cell 42 naive silhouette / chosen | 0.120 / 0.068 | 0.121 / **0.066** (ARI 0.978 unchanged) |
| the residual cluster | cluster 2 | **cluster 1** (silhouette −0.021, reproduction 61%) |
| where ASC-101/204/370 land | 3 / 7 / 5 | **0 / 5 / 2** |

I also could not re-run it myself: this environment blocks huggingface.co, and `models/all-MiniLM-L6-v2` is gitignored, so Q1c's embedding can't be rebuilt and nothing downstream executes. I validated against the outputs stored in the notebook instead — which is one clean sequential pass, execution counts 2–59, so they're internally consistent and are what a marker sees.

## Your filing-type question, answered

**It genuinely disappeared — it did not move.** No cluster in the current fit carries the signature: results announcements run 24.1%–40.4% across all eight, periodic reports 38%–66%, Q1b flag rate 45.6%–64.9%, and every cluster returns clinical keywords. Q2c check 4 already says this correctly. But **Q4b was still asserting the opposite** — "Q2c check 4 found a cluster that was not a kind of trial but a kind of *document*" — while the Q4a screen three cells earlier prints `Excluded as document-type artefacts: none`. Fixed: the screen is now justified by the earlier fit that produced one, which is the reason it must run on every refit.

## What I found and fixed (10 items)

**Q2a** — Cell 45 claimed the solution is "largely the structured one relabelled" at `w_text` 0.2–0.4; its own table shows only 0.3 is (ARI 0.83), with 0.2 and 0.4 at 0.36 and 0.35 — no closer than 0.5 is. Cell 47 said clusters fall under 100 trials "past k = 10"; the sweep shows the smallest dropping to 31 at **k = 9**, while silhouette keeps climbing to k = 12 and Calinski-Harabasz falls — which actually strengthens the argument.

**Q2b** — `evaluable` was quoted for cluster 2 but isn't in its top ten (replaced with `grade`). The "class prevalence of 3–7%" defence was applied to four clusters, but cluster 1 is at 13.8%.

**Q2c** — Check 1 listed cluster 0 among seven clusters confirmed "without difficulty", citing only its two vaccines; its other two sampled trials are bococizumab (cardiovascular event reduction) and ABP-450 (migraine prevention). All four are *prevention* trials — that's the registry field the feature space keyed on, so cluster 0 is a prevention group that happens to be mostly vaccines. **This is why ASC-101 lands there**, and it's a better story than the one that was written: the assignment is right on purpose and empty on disease. Also: "within reach of the outcome label's 3.8%" for 0.96% of |CAR| (it's four times below), and a flag-rate range that quoted a figure belonging to one of the two clusters the sentence excludes.

**Q4** — The Q4a commentary still quoted the pre-regrain fit throughout: ASC-204's cluster as 282/258/145/41 (now 274/247/142/39), ASC-370's as 405 (388), ASC-101's as 71 (67), 63 rare-disease results across 2,076 rows (61 across 1,975). Q4b's stability figures were the old run's (ARI 0.52, reproducibility 58–96%) rather than 0.70 and 61–98%.

Everything else checks out — I verified every number in Q2a through Q2d against its own output, including all eight rows of the cluster table, the negative-readout counts, the variance shares, the per-cluster silhouettes and reproduction rates, and all three readout assignments. Q2d is 487 words.

One nit I left alone for you to judge: cell 47 says k-means "scores at the top on the internal measures" — average-linkage cosine has a marginally better Davies-Bouldin (3.159 vs 3.189). It's top on Calinski-Harabasz and second on silhouette, so the sentence is roughly right, but "at the top" is doing a little work.

## You  _13:08_

Lets leave it for now, so moving along cell 45 is just showing how many trials per filling, cell 46 explanation is fine too which talks about the weighting between text and structural right

## Claude  _13:08_

Numbering's off by one — worth fixing before you validate, since the new grain section added two cells.

**Cell 43** (markdown) — "One filing, several trials". The argument: an 8-K is filed once but can report several trials, and every row from one filing shares the same filing text, so in Q2b those rows are identical feature vectors carrying different cluster labels. It then rejects the obvious fix (one row per filing) and splits the problem in two.

**Cell 44** (code) — this is the trials-per-filing cell you're thinking of, and it does more than count. 2,076 eligible rows across 1,669 filings; 288 filings carry more than one row. Of those, 217 report genuinely *different* registered trials (different `nct_id`s, 216 differ on at least one design field) and 71 just repeat the same trial under different drug spellings. So it collapses only the 101 rows that are identical in every clustering feature → **1,975 trials**, keeps the 217 genuine multi-trial filings, and handles their dependence by weighting each row 1/(trials in its filing) rather than deleting anything. The counter-factual is printed: one row per filing would have thrown away a further 306 trials, 15.5% of the set, and silently picked an outcome label for 104 filings whose rows disagree on one.

That's also where the 1,975 figure you'll see everywhere downstream comes from — the whole of Q2 runs on 1,975, not 2,076.

**Cell 45** (markdown) — "The feature space". This is the one with the text-versus-structured weighting: 20 text PCs against 35 structured features, each block scaled so the two contribute equal variance, `w_text = 0.5`.

**Cell 46** (code) — builds the `Design` class and prints the sweep table that cell 45's weighting paragraph is describing.

One flag: I rewrote cell 45's weighting paragraph in the commit I just pushed, so re-read it rather than the version you may have looked at. The old text claimed the solution was "largely the structured one relabelled" across `w_text` 0.2–0.4; the table only supports that at 0.3 (ARI 0.83), with 0.2 and 0.4 at 0.36 and 0.35 — no closer to structured than 0.5 is. It now reports that spike as the non-monotonicity it is.

## You  _13:10_

so for cell 47, we chose the method of clustering and ended up with euclidean and we also decide the number of clusters?

## Claude  _13:11_

Yes — cell 47 carries three of the four choices Q2a has to justify (cell 45 did the fourth, the feature space). It's prose over two code cells:

**Algorithm and distance** — evidence in **cell 48**, which fits six combinations on the same matrix: k-means/Euclidean, Ward/Euclidean, average and complete linkage on cosine, average linkage on Manhattan, and a full-covariance Gaussian mixture. k-means/Euclidean wins on the combination of internal scores and a usable size distribution (silhouette 0.066, top Calinski-Harabasz at 70.4, 20.8% in its largest cluster). The load-bearing part is the Manhattan row: best silhouette of the six (0.139) and best Davies-Bouldin (1.50) while putting 1,874 of 1,975 trials in one cluster and one trial alone — a degenerate solution that two of the three internal measures reward, which is the argument for not letting silhouette arbitrate anything later.

Euclidean over cosine is argued separately: after standardisation, magnitude carries real meaning (a 2,500-patient trial genuinely is far from a 45-patient one) and cosine would discard it. Both cosine variants are in the table and both are worse.

**Number of clusters** — evidence in **cell 49**, sweeping k = 3 to 14 and reporting silhouette, Calinski-Harabasz, Davies-Bouldin, smallest cluster, clusters ≥100 trials, clusters ≥30 negative readouts, and bootstrap ARI. The stated conclusion is that internal validation *cannot* choose k here: silhouette only moves between 0.048 and 0.086 with no elbow, and its maximum is at k = 12 where Calinski-Harabasz is near its lowest. So k = 8 is chosen on **use** — enough trials per cluster (100) and enough negative readouts (30) to quote a conditional distribution for Q4 — not on the measures.

Two things worth knowing while you validate:

The decisions are sequential, and each assumes the other. Cell 48 compares algorithms with **k fixed at 8**, before k has been justified; cell 49 then sweeps k using **k-means only**. That's a normal way to do it and it isn't hidden by anything, but the notebook doesn't say it out loud, and it's exactly the kind of thing a marker might poke at. The defence is easy if asked — the k sweep's conclusion is that no k is favoured by the internal measures, so the algorithm comparison isn't sensitive to which k it was run at.

And the "100 trials / 30 negatives" criterion the k choice rests on isn't actually met by k = 8 for either bar in full: seven of eight clusters clear 100 (the eighth has 67), and only four clear 30 negatives. Cell 54 states that honestly and turns it into the quotability rule — clusters 1, 4, 5, 7 can carry a distribution; 0, 2, 3, 6 can only be read. So the criterion functions as a way of ranking k rather than a threshold k = 8 passes.

## You  _20:32_

k-means on the real features, k=8               silhouette +0.066
the same labels, shuffled between rows           silhouette -0.024
k-means on column-permuted features              silhouette +0.020  (sd 0.001 over 5 draws)

Groupings already available without clustering, scored in the same space:
   therapeutic area (8 groups)        silhouette +0.075
   phase (4 groups)                   silhouette +0.048
   area x phase (37 groups)           silhouette +0.046
   LLM outcome group (3 groups)       silhouette -0.042

Same comparison with therapeutic area removed from the feature space:
   k-means (k=8)                      silhouette +0.064
   therapeutic-area lookup            silhouette -0.009
   phase lookup                       silhouette +0.062
   ARI(k-means labels, area)          0.055

Per-cluster mean silhouette:
silhouette
0	0.150
1	-0.021
2	0.045
3	0.098
4	0.092
5	0.056
6	0.071
7	0.107

what do these results mean

## Claude  _20:33_

These four blocks are one argument: *is the clustering finding anything, and is it finding anything you couldn't get for free?* Taken in order —

## Block 1: is there structure at all?

Three numbers on the same scale (silhouette runs −1 to +1; above ~0.5 is strong separation, below ~0.25 is weak):

- **+0.066** — the real solution.
- **−0.024** — the same eight labels shuffled randomly between rows. This keeps the cluster sizes but destroys any link between a label and where the point sits. It's the "labels mean nothing" floor, and as expected it's ~0.
- **+0.020** — the interesting one. Each *column* of the feature matrix is permuted independently, so every feature keeps its exact distribution (same spread of enrolments, same phase mix) but all the relationships between features are destroyed. Then k-means is run on that structureless data. It still returns a partition scoring 0.020, because k-means always carves the space into something.

That third number is the honest null. It says **~0.02 of any silhouette you see is just the algorithm doing its job**, not evidence of anything. So the real signal is roughly 0.066 − 0.020 = 0.046, about two thirds of the headline. The `sd 0.001 over 5 draws` matters here: the null is very stable, so the gap is real rather than noise.

Verdict: there is genuine structure, it clears a properly-constructed null, and it is small in absolute terms.

## Block 2: is it better than something you already had?

This is where it gets uncomfortable, and it's the most important block.

- **therapeutic area, 8 groups: +0.075** — a plain lookup on a registry field, no clustering at all, scores **higher** than the eight-cluster solution it took 55 features to build.
- **phase, 4 groups: +0.048**
- **area × phase, 37 groups: +0.046** — more groups, slightly worse. Silhouette penalises fragmentation.
- **LLM outcome group, 3 groups: −0.042**

That last one looks like a failure and is actually a pass. It says good/bad/inconclusive readouts are *not* geometrically separated in this feature space — the space doesn't encode how a trial went. That's exactly what Q1c claimed about the embedding (topic model, not sentiment model) and exactly what you want for comparables: the grouping should say what a trial **is**, not how it **turned out**. If this number were positive you'd have a leakage problem for Question 4.

The caveat the notebook raises itself: therapeutic area is one of the 35 structured features, so scoring an area lookup inside a space that contains area is rigged in area's favour. Hence block 3.

## Block 3: the comparison run fairly

The whole feature space is rebuilt with the area dummies removed, and everything re-scored in *that* space:

- **k-means: +0.064** — barely moves from 0.066. The clustering wasn't leaning on area to look coherent.
- **area lookup: −0.009** — collapses from +0.075. Confirms the circularity was real and large.
- **phase lookup: +0.062** — a four-group lookup on a single registry field still essentially ties the clustering (within 0.002).
- **ARI(labels, area) = 0.055** — near zero.

That ARI is doing separate work. It asks: with area removed, do the clusters *recover* area anyway from text, design and sponsor? Answer, no — 0.055 is chance-level agreement. Two readings, both true: reassuring, because the clustering isn't just therapeutic area laundered through the text PCs; and sobering, because it means the filing text alone can't recover disease area, which is precisely why area had to be put in as an explicit feature in the first place.

One thing the notebook doesn't say, and worth knowing if you're asked: **phase is still in the area-free feature space**, so the phase lookup enjoys exactly the circularity that area was just stripped of. The 0.062-vs-0.064 tie is therefore harsher on the clustering than a genuinely like-for-like test would be.

## Block 4: are the clusters equally good?

| cluster | silhouette | n | reading |
|---|---|---|---|
| 0 | **+0.150** | 67 | tightest — the prevention/vaccine group |
| 7 | +0.107 | 411 | CNS |
| 3 | +0.098 | 136 | immunology |
| 4 | +0.092 | 291 | registrational oncology |
| 6 | +0.071 | 136 | ophthalmology |
| 5 | +0.056 | 274 | cardio-renal |
| 2 | +0.045 | 388 | open-label single-arm |
| 1 | **−0.021** | 272 | residual |

The size-weighted average of these is the 0.066 at the top.

A negative per-cluster silhouette doesn't mean "wrong" — it means its members are on average closer to a *neighbouring* cluster's centre than to their own. For cluster 1 that is the definition of a leftovers bucket, and it's corroborated twice over: check 1 reads four incoherent titles from it, check 5 gives it the worst reproduction rate (61%). Cluster 2's low-but-positive 0.045 is consistent too — it's defined by *design* (open-label, single-arm, small), and trial size and blinding are continuous, so its boundary is genuinely fuzzy rather than broken.

Note the inversion: the **smallest** cluster is the best separated, and the residual is one of the largest. Size and quality run opposite here, which is why cell 54 sets the quotability rule on negative-readout counts rather than on cluster size.

## What the four blocks license, together

**Yes**: there is real structure, it beats a proper null, and it doesn't encode the outcome.

**No**: silhouette does not justify the clustering over what was already available. On this measure the eight-cluster solution does not beat a one-field lookup, either way you run the comparison.

What clustering adds is **combination**, not separation — it splits *within* a therapeutic area on design, stage and sponsor size, which no single-field lookup can do. Silhouette can't see that, because it only measures geometric compactness. So the justification has to come from somewhere else, which is the entire reason Q2b (keywords) and Q2c's six checks exist. That's the argument cell 52 makes and it's the right one.

If you get asked this in one sentence: *the silhouette shows the structure is real but weak, and shows that internal validation cannot arbitrate between this solution and a free alternative — so the defence rests on the external checks, not on this number.*

## You  _20:45_

Okay cell 55 seems okay its just commentary on the clustering characteristics

## Claude  _20:45_

Careful — numbering again. In the notebook:

**Cell 54** is the commentary on cluster characteristics: the eight-row table (label, size, what defines each) and the size-distribution discussion.

**Cell 55** is the **Q2b section opener** — the method statement for the discriminator model. It explains why TF-IDF with no dimensionality reduction (so every column stays a readable word or bigram), why a random forest is fitted **one-vs-rest per cluster** rather than as a single eight-class model (one importance ranking per cluster is what the question asks for), and that predictive performance isn't being assessed because the forests are being used as a *description* of the clusters, not as classifiers.

So if you're reading the cluster table, you're at 54; 55 is where Q2b starts.

One thing worth not waving through on cell 54: it isn't only commentary. It contains the decision that Q4 runs on — **clusters 1, 4, 5 and 7 can carry a distribution of negative reactions; clusters 0, 2, 3 and 6 can be read but not averaged** — derived from the negative-readout counts (112, 70, 63, 39 versus 24, 21, 20, 14), not from cluster size. And it states the consequence: of the three Asclepius readouts, only ASC-204 lands in a cluster clearing that bar. If a marker asks where you decided what you were allowed to quote to the board, cell 54 is the answer, so it's worth reading as a decision rather than as description.

## You  _21:07_

so cell 56 runs the random forest against the others, what does out of bag accuracy signify again?

## Claude  _21:08_

<details><summary>tools run</summary>

- `Bash: Read the Q2b discriminator code`

</details>

**Out-of-bag accuracy** is a held-out estimate that comes free with a random forest, without a separate test set.

Each tree in the forest is trained on a bootstrap resample of the rows. A bootstrap sample of size *n* drawn with replacement misses about 37% of the rows, and those rows are "out of bag" for that tree. To score a row, you use only the trees that never saw it in training and let them vote. The share of rows the forest gets right that way is `oob_score_`. It's roughly equivalent to cross-validation but costs nothing extra, which is why it's used here — the forests exist to rank keywords, and the OOB number is a cheap sanity check on whether the text separates that cluster at all.

The code confirms it: `RandomForestClassifier(random_state=MEMBER_ID, oob_score=True)`, and the comment notes correctly that `oob_score` changes nothing about how the forest is fitted.

## How to read this particular table

Three columns, and the OOB figure is meaningless without the other two:

- **`always-'not c' baseline`** = 1 − prevalence. Each forest is binary one-vs-rest, and the clusters hold 3.4% to 20.8% of rows, so a model that simply answers "not cluster *c*" for everything already scores 79%–97%. Cluster 3's OOB accuracy of 0.931 against a baseline of 0.931 is a **zero** gain, not a good score.
- **`ceiling`** = the best any text-only model could do. 147 filings have their trials split across different clusters, so those rows are identical TF-IDF vectors carrying different labels — unseparable by construction. Overall that caps accuracy at 0.907; per-cluster it's 0.965–0.992 (computed by giving all of a filing's rows the same answer). So you read OOB against the ceiling, not against 1.0.

Which is why cell 57 reports gain over baseline rather than the raw number: cluster 7 gains +0.101, the four large clusters gain +0.033 to +0.101, and the four smallest gain between 0.000 and +0.012.

## One caveat the notebook doesn't state

The bootstrap draws **rows**, not filings. Rows from the same 8-K have identical TF-IDF vectors, so a row can be out-of-bag for a tree while its identical-text sibling was in-bag — meaning the tree has effectively already seen that exact feature vector with that label. For the 523 rows sitting in multi-trial filings, OOB is therefore optimistically biased.

The notebook handles the other half of this problem carefully (the ceiling, and `sample_weight=filing_weight` so a seven-trial filing doesn't count seven times) and it fixes the equivalent issue in Q2c check 5 by resampling *filings* rather than rows — so the concern is clearly on the author's radar; it just isn't applied to the OOB estimate. It doesn't change any conclusion, since the argument in cell 57 is that these gains are small and the small clusters can't be judged by accuracy anyway, and an optimistic bias only makes that argument safer. But if a marker asks "is your OOB estimate clean here", the honest answer is *not quite, and here's why it doesn't matter*.

Smaller point, worth a glance rather than worry: `oob_score_` is computed as plain unweighted accuracy over OOB predictions, so the filing weights shape the fit but not the reported number.

## You  _21:47_

I am looking at cell 57, why is cluster 3 baseline

## Claude  _21:48_

Mechanically: the baseline is 1 − prevalence, and cluster 3 holds 136 of 1,975 rows, so 1 − 136/1975 = **0.931**. Its OOB accuracy is also 0.931. That means the forest, voting on out-of-bag rows under the default 0.5 majority threshold, essentially **never predicts "cluster 3"** — it answers "not cluster 3" for everything, which is exactly what the trivial baseline does, so the two scores land on the same number.

Three reasons that isn't the indictment it looks like:

**The headroom was 4.7 points, not 6.9.** Cluster 3's ceiling is 0.978 — because filings whose trials straddle clusters are unseparable by text. So the most any text-only model could have gained here was 0.931 → 0.978. "Zero out of a possible 4.7" is a different statement from "zero out of a possible 6.9".

**Accuracy is close to useless at 6.9% prevalence.** A forest can rank cluster-3 rows well — give them genuinely higher probabilities than everything else — and still never push a majority of trees over 0.5, because the class is so rare that the safe vote is always "no". Accuracy only rewards the thresholded decision. AUC or precision/recall would show whatever signal is there; accuracy is built to hide it.

**Gini importance doesn't depend on the prediction succeeding.** The keyword rankings come from how much each term reduced impurity *at the splits during training*, not from the final thresholded vote. So the forest can identify `ulcerative colitis`, `rheumatoid arthritis`, `acr20`, `atopic`, `molluscum contagiosum`, `inadequate response` as the terms that carve cluster 3 out, and still decline to predict it on held-out rows. Those keywords are as clinically specific as any cluster's in the table — this is not a cluster with no vocabulary.

There's also a concrete reason cluster 3's text is hard, and it's sitting in check 1: **reproxalap appears in both cluster 3 and cluster 6** — ALDX's ALLEVIATE trial in allergic conjunctivitis lands in 3, its TRANQUILITY dry-eye trial in 6. Cell 61 rightly presents that as the feature space working (same drug, same sponsor, sorted by what the trial was about). But from a text-only discriminator's point of view those are near-identical documents carrying different labels — precisely what depresses separability between those two clusters. Note cluster 6 has the same n (136) and the same baseline, and gains only +0.012; at this prevalence 0.000 versus 0.012 is not a real difference. Both mean "this metric can't tell".

And cluster 3 is corroborated everywhere else: 99% pure on therapeutic area, 93% reproduction rate under resampling, and four sampled titles that all read as immunology/dermatology (tradipitant in atopic dermatitis, SER-287 in ulcerative colitis, reproxalap, ruxolitinib cream). That's the argument cell 57 makes, and it's sound.

If a marker pushes on it, the clean answer is: *accuracy was the wrong statistic for a 7% class and I should have reported AUC or average precision alongside it — the cluster's validity rests on checks 1, 3 and 5, not on this table.* Adding a `roc_auc` column would be a genuinely small change if you wanted to close that off, though it's not required — the brief explicitly allows not assessing the discriminators' predictive performance.

## You  _21:50_

**What the accuracy table does and does not license.** The ceiling printed above the forests is the
reason this section now reports one. Because a filing's trials all share its text, 147 of the 1,669
filings supply identical feature vectors carrying more than one cluster label, so **no text-only
discriminator can exceed 0.907 accuracy** on this labelling however good it is. Against that ceiling
and against the trivial "call everything not-cluster-*c*" baseline, the forests separate the large
clusters and add little to the small ones:

what does this mean

## Claude  _21:51_

It's saying: **don't read these accuracies against 100%, because 100% was never reachable.**

## Where 0.907 comes from

The clustering works at the **trial** grain — 1,975 trials — but the discriminator reads only the **filing** text, and one 8-K can report several trials. Those trials produce identical TF-IDF vectors. For 147 of the 1,669 filings, the trials in that one filing landed in *different* clusters.

So for those rows the model is handed one input with two different correct answers. No function of the text can return two answers for the same input — it has to pick one and be wrong on the rest. That isn't a modelling weakness; it's arithmetic.

The best conceivable text-only model therefore answers, for each filing, with whichever cluster label is most common among that filing's trials. Sum those best-case correct counts over all filings, divide by 1,975, and you get **0.907**. Roughly 9% of rows are unclassifiable by construction. That's the `_ceiling` line in cell 56, computed *before* any forest is fitted so it can't be tuned after the fact.

The per-cluster ceilings in the table are higher (0.965–0.992) because each forest is binary: in a "cluster *c* vs not *c*" framing, a filing's rows only conflict if they straddle *that particular* boundary, which is rarer than straddling any boundary.

## What it licenses

Every number has to be read between two fences — the baseline below and the ceiling above:

| cluster | baseline | OOB | ceiling | share of available headroom |
|---|---|---|---|---|
| 7 | 0.792 | 0.893 | 0.978 | **54%** |
| 5 | 0.861 | 0.907 | 0.979 | 39% |
| 2 | 0.804 | 0.852 | 0.970 | 29% |
| 4 | 0.853 | 0.886 | 0.965 | 29% |
| 6 | 0.931 | 0.943 | 0.990 | 20% |
| 0 | 0.966 | 0.971 | 0.992 | 19% |
| 1 | 0.862 | 0.872 | 0.974 | 9% |
| 3 | 0.931 | 0.931 | 0.978 | 0% |

(That last column is my arithmetic — (OOB − baseline) / (ceiling − baseline) — not something the notebook prints. It's just a compact way of seeing the same thing the cell says in words.)

Read raw, cluster 7's 0.893 looks worse than cluster 0's 0.971. Read properly, cluster 7 captures over half of everything that was recoverable and cluster 0 captures a fifth of a much smaller allowance. The ranking inverts once you fence the numbers. That's the whole point of the paragraph: **the large clusters are genuinely separable from filing text; the small ones are in a range where the metric can't discriminate either way.**

## Why it's there at all

The ceiling is the **price of the grain decision** made back in cells 43–44. Keeping multi-trial filings as separate trials was the right call — the unit of analysis for this question is the trial, and collapsing would have deleted 306 real trials and silently picked outcome labels for 104 filings. But it guarantees a set of rows that no text model can get right. Printing the ceiling is what stops that cost from being mistaken for a bad model, and it's the kind of thing that earns credit: the constraint is stated, quantified, and measured before the result rather than invoked afterwards as an excuse.

Two small things while you're in there. `0.907` appears twice in that output as unrelated quantities — the overall ceiling, and cluster 5's OOB accuracy — which is pure coincidence but could trip you up if you're asked about it live. And "the reason this section *now* reports one" reads slightly like a note-to-self about a revision; "the reason this section reports one" is cleaner for submission.

## You  _21:52_

always-'not c' baseline what does this mean

## Claude  _21:52_

It's the score you'd get from a model that does nothing.

Each forest is binary — "is this row in cluster *c*, yes or no". The laziest possible classifier answers **"no" every single time**, never predicting the cluster at all. Its accuracy is just the share of rows that genuinely aren't in cluster *c*, i.e. **1 − prevalence**. In the code it's literally `1 - y.mean()`.

So for cluster 0, which holds 67 of 1,975 trials: 1 − 67/1975 = **0.966**. A one-line "model" that says "not cluster 0" to everything scores 96.6% accuracy while identifying precisely zero cluster-0 filings. For cluster 7, which holds 411: 1 − 411/1975 = **0.792**.

That's why the column is printed. Without it, cluster 0's OOB accuracy of 0.971 looks excellent and cluster 7's 0.893 looks mediocre — when in fact cluster 0's forest beat do-nothing by half a point and cluster 7's beat it by ten. The baseline tells you which part of the accuracy is information and which part is just the class being rare.

It also explains why the baseline is different for every row of the table: it's set entirely by cluster size. Small clusters get high baselines and almost no room to show a gain; large clusters get low baselines and more room. Cluster 7 has the most (20.8% prevalence), which is part of why it posts the biggest gain.

So the three columns bracket each forest: **baseline = the floor** (what nothing achieves), **ceiling = the cap** (what a perfect text reader could achieve given the identical-vector problem), and OOB accuracy sits somewhere between them. Only the position between the two fences means anything.

## You  _21:53_

i dont get the 1-prevalence what does this mean

## Claude  _21:53_

Prevalence just means **how common the thing is** — the fraction of rows that *are* in cluster *c*. So 1 − prevalence is the fraction that are *not*.

Worked through for cluster 0:

- 67 trials are in cluster 0
- 1,975 trials in total
- so 1,908 are **not** in cluster 0

Now imagine a "model" that answers **"not cluster 0"** for all 1,975 rows. How often is it right?

- Right on all 1,908 rows that genuinely aren't in cluster 0 ✓
- Wrong on all 67 that are ✗

Accuracy = 1,908 ÷ 1,975 = **0.966**

And that fraction — "rows not in the cluster, divided by all rows" — *is* 1 − prevalence. Prevalence is 67/1975 = 0.034, so 1 − 0.034 = 0.966. Same number, two ways of writing it.

The point is that 96.6% sounds like a good score and is worth nothing, because the model never once said "yes, this is cluster 0". It got its 96.6% purely by the cluster being rare.

The standard analogy: a rare disease affecting 1 person in 100. A doctor who tells every single patient "you don't have it" is correct 99% of the time — and is a useless doctor. 99% is their baseline, not their skill.

So when you see cluster 0's forest scoring 0.971 against a baseline of 0.966, what it actually achieved over doing nothing is half a percentage point. Cluster 7 scored 0.893 against a baseline of 0.792 — ten points of real work, on a cluster that's common enough (411 of 1,975, so 20.8% prevalence, 79.2% baseline) for the metric to have room to show it.

---

### Friday 18 September 2026

## You  _11:29_

in question 2c what is check 1 trying to do

## Claude  _11:29_

<details><summary>tools run</summary>

- `Bash: Re-read check 1's reading after my edit`

</details>

Found a defect I introduced — let me check the code and fix it.

<details><summary>tools run</summary>

- `Bash: Read check 1's sampling code`

</details>

<details><summary>tools run</summary>

- `Bash: Fix the cluster count in check 1`

</details>

<details><summary>tools run</summary>

- `Bash: Commit and push the count fix`

</details>

Fixed and pushed ([68a9248](https://github.com/ruiruiruir/DSA_26S2/commit/68a9248)) — that was my error from the earlier edit, not something you need to chase.

## What check 1 is for

It's the **face-validity test**: print the actual trials in each cluster and ask whether a person who knows what a clinical trial is would agree they belong together. It's the simplest check available and, as cell 59 says, the one most easily skipped.

Three things make it carry more weight than "eyeballing it" usually does:

**It's necessary, not decorative.** Q2a established that internal validation can't justify this solution — silhouette 0.066, beaten by a free therapeutic-area lookup at 0.075, and tied by a phase lookup once area is held out. So the case for the clustering *has* to be made by inspection and by use. Check 1 is the first instalment of that case, and Q2b's keywords plus checks 2–6 are the rest.

**The evidence is genuinely external.** It prints `brief_title` — ClinicalTrials.gov's own description of the study. That field was never in the feature space, which was 20 principal components of *filing* text plus 35 structured registry fields (phase, masking, allocation, model, purpose, area, enrolment, sites, arms, endpoint counts, sponsor). So when the titles agree with the cluster labels, that's corroboration from a source the algorithm never saw, not a restatement of its inputs.

**The sample is random and seeded.** `sub.sample(4, random_state=MEMBER_ID)` — not the first four rows, not hand-picked. That matters for credibility: you can't cherry-pick four coherent trials to flatter a cluster, and anyone re-running it gets the same four.

## What it actually establishes in this run

Four distinct outcomes, not one verdict:

- **Five clusters confirm outright** (3, 4, 5, 6, 7) — the titles read as immunology, registrational oncology, cardio-renal, ophthalmology, CNS.
- **Cluster 0 confirms, but reveals its real organising principle.** Two of its four sampled trials are vaccines and two aren't (bococizumab for cardiovascular event reduction, ABP-450 for migraine prevention) — all four are *prevention* trials. That's not a blemish, it's a discovery: it explains why ASC-101 lands there and why the cluster contains nothing in ASC-101's therapeutic area.
- **Cluster 2 confirms on design rather than disease** — glioblastoma, wet AMD gene therapy, cryptococcal meningitis, cystic fibrosis have nothing clinically in common; all four are open-label and mostly single-arm. That's the finding that sends ASC-370 to nearest-neighbour retrieval instead of the cluster mean in Q4.
- **Cluster 1 fails** — haemorrhoids, gout, hepatitis C and a cystic fibrosis gene therapy. Reading it is what turns "negative silhouette" from an abstraction into a concrete judgement that it's a residual.

Plus the reproxalap observation: the same drug from the same sponsor lands in cluster 3 for allergic conjunctivitis and cluster 6 for dry eye. That's direct evidence the space keys on what the trial is *about* rather than on the company or the molecule — something no summary statistic in Q2 shows.

## Its limit, if you get asked

**Four trials out of 411 is not a sample you can generalise from.** The check can *falsify* coherence — four incoherent titles are enough to condemn cluster 1 — but it can't *establish* it. Four plausible titles from cluster 7 don't prove the other 407 are CNS trials.

That asymmetry is why check 1 is first rather than last, and why five more checks follow. The claim it supports is "nothing here is obviously broken, and one thing obviously is", which is exactly the right amount of weight to put on reading four rows.

## You  _13:40_

Okay so I think for check 2, it is saying that from the direction of the CAR cannot be measured from clustering but the absolute magnitude can be?

## Claude  _13:40_

Right on direction, half-right on magnitude — and the half that's off is the one a marker would press.

**Direction: yes, and emphatically.** Cluster explains **0.18%** of the variance in signed CAR, Kruskal-Wallis H = 8.6, p = 0.28 — not significant. The outcome label explains 9.9% and the company 23.2% on the same rows. Knowing which of eight groups a trial is in tells you essentially nothing about which way the stock moves.

**Magnitude: the difference is real, but "can be measured" overstates it.** On |CAR| the clusters explain **0.96%** with p = 0.013. Two separate facts there, and it's worth not collapsing them:

- **p = 0.013** says the differences between clusters are unlikely to be exactly zero.
- **0.96%** says they're tiny — about 99% of the variation in reaction size has nothing to do with which cluster a trial is in.

With n = 1,975, tiny effects clear significance easily. Significance answers "is there something?"; variance share answers "is it worth anything?" The answers here are yes and barely.

Two further deflations in the same cell:

- **Market-cap decile alone explains 5.7%** — nearly six times more than the clusters. And the clusters correlate with sponsor size by construction (market cap is a feature). So part of that 0.96% *is* company size wearing a trial-type label, which is exactly what check 3 goes on to confirm.
- **Part of the spread is composition, not trial type.** Cluster 2 has the tightest dispersion (17.9%) — but also a 5.4% negative-readout share against 14–27% everywhere else. It looks calm partly because it contains far fewer bad results, which is a fact about what gets disclosed from open-label single-arm studies, not about the trials being safer.

So the accurate version is: **the clusters carry essentially nothing about direction and a little about magnitude, most of which is probably sponsor size.**

## The bit that looks contradictory

You'll notice the cell also reports that negative readouts average −24.7% in cluster 5 and −13.5% in cluster 2 — an 11-point spread that sounds useful, sitting next to "explains 0.18% of the variance". Both are true, and the reconciliation is worth having ready:

Variance explained is about how much of the *scatter* the grouping accounts for. The standard deviations inside those clusters are 18–27% — far wider than the 11-point gap between their means. So the distributions overlap almost completely: the *centres* differ in a way that's genuinely useful for planning a downside, while the grouping still predicts almost nothing about any individual trial.

The cleanest demonstration is the within-outcome test: conditioned on positive readouts, the pooled SD is 21.2% and knowing the cluster narrows it to 21.2%. For negatives, 28.4% becomes 28.5% — very slightly *wider*. That's the sharpest form of the finding, because narrowing the range is precisely what an IR team would want from a comparable set, and it delivers zero.

## What check 2 licenses

Use the clusters to **choose which historical readouts to look at**, never to **narrow the range** of what might happen. Quoting "ASC-204's cluster averaged −24.7% on negative readouts" is fair. Implying the outcome is more certain because you grouped it is not. That's the rule Q2d states and Q4 is built on — and it's why this is described as the single most important output in Question 2 despite being a negative result.

## You  _13:43_

Oh okay I see, then check 3 is just checking the company sizes, if there is any dominant in any cluster but it seems like most are okay?

## Claude  _13:44_

Half of it — check 3 has **two** failure modes, and you've described the one that passes. The second one is present.

**Failure mode 1: is a cluster one company's filings in disguise?** If it were, its reactions would describe that company rather than a trial type. Clean pass, as you say — largest single-sponsor share anywhere is 14.9% (Pfizer in cluster 0), the Herfindahl index runs 0.012 to 0.072 (unconcentrated by any standard), and even the most concentrated cluster has 26 distinct companies in it. Cluster 2 has 135 sponsors across 388 trials with a 3.4% largest share. The two worth remembering are EXEL at 14.1% of cluster 4 and TNXP at 13.9% of cluster 7 — not enough to make either cluster a proxy for its sponsor, but enough to keep in mind when reading those two clusters' reactions.

**Failure mode 2: is a cluster a market-cap bucket in disguise?** This one is real. Median sponsor size runs from **$0.21bn in cluster 6 to $2.36bn in cluster 4** — a factor of eleven — and big-pharma participation from 7.4% of cluster 6 to 37.5% of cluster 3.

The cell's framing of that is the important bit: it's **a feature, not an artefact**. Market cap is deliberately in the feature space, because the brief names sponsor as one of the dimensions of similarity, and sponsor size genuinely conditions how a readout is received. So the problem isn't that size varies across clusters.

The problem is that size is doing **more work than the trial characteristics are**. Check 2 found market-cap decile explains 5.7% of the variation in |CAR| against the clusters' 0.96%. So wherever a cluster appears to predict how big a reaction will be, the honest reading is that it's partly just reporting who the sponsor was. Check 3 is what deflates the one positive result check 2 produced — the two checks are doing a single job across two cells.

**And there's a third thing check 3 does, aimed squarely at Q4.** Asclepius has a $6.0bn market cap:

- Only **cluster 6** has a 90th-percentile sponsor below that ($3.17bn). In the others the upper tail reaches $7.9bn to $205bn, so the comparable sets do contain companies Asclepius's size and larger.
- But the **medians** are $0.21bn to $2.36bn, and the median across the whole clustering set is $0.69bn. The typical comparable is roughly **a tenth** of Asclepius's size.

Combined with the Q1a finding that good news is more fully priced in for large companies, that gives the constraint Q4 inherits: **reactions read off these groups are an upper bound on magnitude, not a central estimate.** If you quote a −24.7% downside from cluster 5 to the board, the accompanying sentence is that it comes from companies much smaller than us and our own move would likely be less violent.

So: "most are okay" is right for the first failure mode and understates the second. The summary a marker would want is *no cluster is a company, but the clusters are partly a company-size grouping, and that limits what the magnitude differences can be attributed to.*

## You  _13:53_

okay so check 4 seems like there is data issues with cluster 2 and cluster 0 has previous language, i think im okay with the analysis. check 5 looks at reproduction rate which is quite straightforward

## Claude  _13:54_

Check 4 summary is right. The one thing to be able to state as the *headline* rather than the footnote: the primary finding is the **negative** one — no cluster is a document type, results-announcement share runs 24.1%–40.4% and the Q1b flag rate 45.6%–64.9% across all eight, both too narrow for any cluster to be explained by document kind. The cluster 2 and cluster 0 signatures are the secondary findings. That ordering matters because Q4a's screen prints `Excluded as document-type artefacts: none`, and a marker may well ask why you kept a screen that found nothing.

On check 5 — "straightforward" is fair, but there are four things in it that aren't obvious:

**It reports two different statistics.** The bootstrap ARI (0.695 mean, 0.529–0.936 over 25 draws) asks whether the *whole partition* survives resampling. The per-cluster reproduction rate (0.614 to 0.984) asks whether *that particular cluster's members* stay together. The second is the actionable one — it's what tells you cluster 0 is small-but-solid (98%) while cluster 1 is large-and-loose (61%).

**It tests two separate sources of instability.** The bootstrap varies *which trials are in the sample*; the five alternative seeds vary *where k-means starts*. Those are different failure modes and most write-ups only do one. Note the honesty about the seed at 0.610 against four in a 0.765–0.786 band — reported rather than averaged away.

**The resampling draws filings, not rows** — and this is the part worth being able to defend. Trials reported in one 8-K share a document and a single market reaction, so drawing rows would treat a seven-trial filing as seven independent observations and inflate the reproducibility. It's the same dependence that `filing_weight` handles in Q2b.

That's also the neat contrast with the OOB caveat from earlier: sklearn's internal bootstrap inside the random forest draws **rows**, so the Q2b OOB accuracies are mildly optimistic, while check 5's bootstrap draws **filings** and isn't. Same problem, handled in one place and not the other. If anyone asks about dependence in your Q2, that's the complete answer.

**The last paragraph isn't about stability at all.** It's the warning that k-means cluster *numbers* are arbitrary across fits — changing the row grain renumbered every cluster in this very notebook — so anything downstream must identify a group by its properties, not its index. That's the justification for how Q4a's document-type screen is written, so it's load-bearing despite sitting at the end of a stability cell.

What the whole check licenses: **broad shape real, exact membership not.** Use cluster membership to pick candidates and then check them by hand — which is precisely why check 6 prefers nearest-neighbour retrieval over the cluster mean for ASC-370.

## You  _14:00_

So it seems like check 6 is checking what the trials from asclepius is similar to and we have issues with asc370 and asc101

## Claude  _14:01_

Right on the second half — but check 6 does two things, and the first one is easy to skim past.

**The invariance test.** Each readout comes with three scenario filings (positive, mixed, negative), and the check assigns each one to a cluster using scalers and centroids fitted on the historical trials only. The assignment has to be the same across all three scenarios:

```
scenario    positive  mixed  negative
ASC-101            0      0         0
ASC-204            5      5         5
ASC-370            2      2         2
```

This could genuinely have failed. The text block is 20 principal components of Q1c's embedding of *result sentences* — so a negative draft filing could easily have pulled a readout into a different cluster than its positive draft. If it had, the comparable set would depend on the outcome you're trying to predict, which is circular and would make the whole thing unusable for Q4. It doesn't happen: the grouping keys on what the trial *is*, not how it went. That's a pass worth claiming.

**On the comparables — the two problems are different in kind, and that's the actual finding.** "ASC-370 and ASC-101 both have issues" flattens the distinction the cell is drawing:

**ASC-370 — the cluster fails, the geometry works.** It lands in cluster 2 (388 trials), of which only 15 share its therapeutic area and 6 its phase, and the cluster under-reports failure (21 negatives, 5.4% negative share). So the cluster *mean* is useless. But its five nearest neighbours — tgAAVCF, NGN-401, SRP-9003, SD-101, ELX-02 — are all gene therapies or rare-disease programmes at the same stage. Q4a quantifies it: **82% of its top-50 neighbours are clinically related.** The remedy is to switch tools — use nearest-neighbour retrieval instead of the cluster — and Q4a does exactly that.

**ASC-101 — both fail, and no method fixes it.** Cluster 0 contains zero trials in its therapeutic area, and retrieval barely helps: **14% of its top-50 neighbours are clinically related**, below Q4a's 30% threshold, so the code falls back to a broad Phase 3 base rate. The one genuine hit is berotralstat at rank 3, an oral HAE prophylactic that moved +10.0%. The cause isn't the clustering — the dataset contains **7 HAE readouts in total** and 61 rare-disease results out of 1,975, sitting in only two clusters. You cannot retrieve comparables that don't exist.

So: **ASC-370 is a tooling problem with a solution; ASC-101 is a data problem with none.** That difference is what drives two different code paths in Q4a and two different sentences to the board.

**The Q4 consequence.** Of the three assets, only ASC-204 lands in a cluster that clears the 30-negative-readout bar (39 negatives). So only one of the three can have a distribution quoted at all — ASC-370 gets read case by case, ASC-101 gets a base rate with an explicit caveat.

And the reason this is called the most direct validation: checks 1–5 test whether the groupings are *good*. Check 6 tests whether they're good **for the job they were built for**. A clustering can pass every generic quality test and still have nothing to say about your three specific assets — which is, for one of them, exactly what happened.

## You  _16:40_

okay can you export this chat to ai_logs for me please

## Claude  _16:40_

<details><summary>tools run</summary>

- `Bash: Inspect ai_logs and the export script`

</details>

<details><summary>tools run</summary>

- `Bash: Read the export script`

</details>

<details><summary>tools run</summary>

- `Bash: Read the rest of the export script`

</details>

The repo has its own exporter — using that rather than inventing a format.

<details><summary>tools run</summary>

- `Bash: Export the session transcript to ai_logs`

</details>
