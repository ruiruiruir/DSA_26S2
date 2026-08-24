# Clinical Trials, FDA Approvals, and Market Disclosure: A Linked Database

## Overview

This project constructs a research database linking clinical trial registrations, FDA drug approval decisions, and corporate disclosure filings (SEC 8-Ks) for publicly traded pharmaceutical companies. The goal is to enable analysis of the information flow from clinical trial completion through regulatory approval to capital market disclosure.

## Contents

| | Section |
|---|---|
| | [Overview](#overview) |
| **Acquisition** | [1. ClinicalTrials.gov](#1-clinicaltrialsgov-step-1) · [2. Drugs@FDA](#2-drugsfda-step-2) · [3. Sponsor–Ticker Mapping](#3-sponsorticker-mapping-step-3) · [4. SEC EDGAR 8-K Filing Search](#4-sec-edgar-8-k-filing-search-step-4) |
| **Processing** | [5. Outcome Classification](#5-8-k-clinical-trial-outcome-classification-step-5) · [6. Event Study](#6-event-study--market-reaction-to-trial-announcements-step-6) · [7. Study–Event Linkage](#7-studyevent-linkage-step-7) · [8. Market Capitalisation](#8-market-capitalisation-step-8) |
| **The shipped data** | [Student Database](#student-database) · [Table inventory](#table-inventory) · [Field provenance](#field-provenance) |
| **Reference** | [Summary Statistics](#summary-statistics) · [Analytical Use Cases](#analytical-use-cases) · [Technical Notes](#technical-notes) · [Reproducibility](#reproducibility) |

Steps 1–4 acquire data; steps 5–8 derive from it. A field's provenance is the step that produced it.

## Data Sources

### 1. ClinicalTrials.gov (Step 1)

**Source:** ClinicalTrials.gov API v2 (`/v2/studies` endpoint, paginated JSON)

**Coverage:** 580,678 registered clinical studies (full database as of April 2026)

**Method:**
- Downloaded via paginated API requests (1,000 studies/page, ~581 pages, ~13 min)
- Each study's nested JSON was flattened into a single row with 66 columns
- Loaded into SQLite (`ctgov.db`, ~3 GB) with batched inserts (5,000 per batch) and indexed on `nct_id`, `overall_status`, `study_type`, `phases`, and `lead_sponsor`

**Key fields extracted (66 total):**
- **Identification:** `nct_id`, `org_study_id`, `org_name`, `org_class`, `brief_title`, `official_title`, `acronym`
- **Status & dates:** `overall_status`, `start_date`, `completion_date`, `primary_completion`, `first_posted`, `last_update_posted`, `results_first_posted`, `status_verified_date`
- **Design:** `study_type`, `phases`, `allocation`, `intervention_model`, `primary_purpose`, `masking`, `observational_model`, `time_perspective`, `enrollment`, `enrollment_type`
- **Sponsor:** `lead_sponsor`, `lead_sponsor_class`, `n_collaborators`, `collaborators`, `responsible_party_type`
- **Clinical:** `conditions`, `keywords`, `intervention_names`, `intervention_types`, `n_interventions`, `n_arm_groups`
- **Eligibility:** `eligibility_criteria`, `sex`, `min_age`, `max_age`, `healthy_volunteers`, `std_ages`, `sampling_method`
- **Outcomes:** `n_primary_outcomes`, `n_secondary_outcomes`, `primary_outcome_1`
- **Geography:** `countries`, `n_locations`
- **Regulatory:** `is_fda_regulated_drug`, `is_fda_regulated_device`, `has_dmc`, `has_expanded_access`, `ipd_sharing`
- **Other:** `brief_summary`, `detailed_description`, `overall_official`, `n_references`, `n_mesh_conditions`, `n_mesh_interventions`

**Database profile:**
- 76.3% interventional studies, 23.3% observational
- 54.6% completed, 11.2% recruiting, 15.7% unknown status
- 22.2% industry-sponsored (128,837 studies)
- Median enrollment: 69 participants
- 32.9% of studies include US sites
- Top sponsors: GlaxoSmithKline (3,588), NCI (3,536), AstraZeneca (3,412), Pfizer (3,253)

### 2. Drugs@FDA (Step 2)

**Source:** openFDA API (`/drug/drugsfda.json` endpoint)

**Note:** The FDA's direct bulk download (`fda.gov/media/89850/download`) is blocked for automated server-based requests by Akamai's CDN abuse-detection layer. The openFDA API provides equivalent data programmatically and was used instead.

**Coverage:** 27,275 FDA drug applications, 47,501 products, 173,332 submissions

**Method:**
- Downloaded all drug applications via openFDA API (100 per page, paginated with `skip`)
- openFDA imposes a `skip` limit of 25,000; two-pass approach used to maximise coverage (27,275 of 29,006 total applications retrieved, 94.0%)
- For each application, extracted: brand names, generic names (active ingredients), submission dates, and approval status
- Built a normalised drug name lookup index (brand + generic names, with common formulation suffixes stripped)
- Matched each trial's `intervention_names` field against the lookup, trying exact normalised match first, then individual-word matching for multi-word names

**Matching results:**
- 135,099 trials matched to an FDA drug application (23.3% of all studies)
- 133,363 trials matched to a drug with confirmed FDA approval
- Matching is conservative: only drugs with >=3-character normalised names are indexed to avoid false positives

**Fields added to `studies` table:**
- `fda_approved` — "True"/"False" flag
- `fda_approval_date` — date of first FDA approval (from earliest submission with status "AP")
- `fda_application_number` — NDA/BLA/ANDA reference
- `fda_brand_name`, `fda_generic_name` — matched FDA drug names

**Limitations:**
- Name-based matching can produce false positives (e.g., common drugs like dexamethasone match many trials not specifically studying that drug)
- 6.0% of FDA applications (1,731 of 29,006) were not retrievable due to the openFDA skip limit
- Generic/biosimilar applications (ANDAs) are included but may not be relevant for novel drug research questions

#### Step 2b — Improved FDA matching for event study drugs

The initial programmatic FDA matching in Step 2 was inconsistent at the drug name level — the same drug (e.g., KEYTRUDA/pembrolizumab) could show `fda_approved = True` in some events and `None` in others, affecting 68 drugs across 163 events. This was caused by inconsistent drug name formats (brand vs generic, combo products, biosimilar suffixes, development codes).

To fix this, a two-stage matching pipeline was applied to all 1,495 unique drug names in the event study dataset:

1. **Programmatic matching (772 drugs):** Direct string matching against FDA generic and brand names, with handling for biosimilar suffixes (e.g., galcanezumab → GALCANEZUMAB-GNLM), parenthetical names (e.g., "baricitinib (Olumiant)"), combo products, and development code detection.

2. **LLM-assisted matching (723 drugs):** Remaining drug names were classified in batches of 50 using an LLM with pharmaceutical knowledge. The LLM determined FDA approval status, identified the matching generic name(s), and assigned a confidence level. For combo products (e.g., "KEYTRUDA + Lenvima"), each component was evaluated independently — the drug was marked as FDA-approved if any component had approval.

**Results:**
- 661 drugs classified as FDA-approved, 805 as not approved, 29 as unknown (vaccines, medical devices)
- Confidence: 1,411 HIGH, 72 MEDIUM, 7 LOW, 5 NONE
- Zero drugs with inconsistent `fda_approved` flags across events (previously 68)

**Derived features (`event_fda_features` table):** For each event, the following features were computed from the matched FDA application records:
- `fda_application_type` — NDA (novel drug), BLA (biologic), or ANDA (generic)
- `fda_n_prior_approvals` — number of FDA approval submissions before the event date
- `fda_years_since_approval` — years from first FDA approval to event date
- `fda_marketing_status` — current marketing status (Prescription, Discontinued, etc.)
- `fda_n_dosage_forms` — number of distinct dosage forms
- `company_n_fda_approved` — total FDA-approved products for the company (by ticker)
- `company_n_nda_bla` — total novel drug + biologic approvals for the company

⚠ **`fda_approved` is as at the database build date, not as at the event date.** A drug approved in
2018 shows `fda_approved = True` on a 2012 event, so using the flag as a predictive feature is
look-ahead leakage. The same applies to `overall_status` in `studies`. The two time-relative FDA
features — `fda_n_prior_approvals` and `fda_years_since_approval` — are computed against the event date
and do not carry this problem.

Note also that `fda_approved` is stored differently depending on where you read it: an integer `0`/`1`
in `event_fda_features`, and the strings `'True'`/`'False'` in `event_study_enriched` and `studies`.

These features are available in the `event_fda_features` table, one row per event. The table inventory under *Student Database* records how it joins to `event_study_enriched`. Company-level features were computed by matching `sponsor_tickers` to `fda_applications.sponsor_name` and are available for 1,024 of 2,482 events.

### 3. Sponsor–Ticker Mapping (Step 3)

**Purpose:** Identify which industry-sponsored trials are run by publicly traded companies, enabling linkage to SEC filings.

**Method:**
1. Extracted 15,557 unique industry sponsors from the `lead_sponsor` field (128,837 total trials)
2. Built a three-tier matching system:
   - **Curated list (Tier 1):** ~120 manually verified mappings for major pharma/biotech companies and their subsidiaries, including acquired companies mapped to acquirers (e.g., Celgene → BMY, Allergan → ABBV)
   - **SEC EDGAR ticker file (Tier 2):** Downloaded the SEC's `company_tickers.json` (15,020 entries), matched on exact and normalised company names
   - **Fuzzy matching (Tier 3):** Partial string containment for remaining sponsors
3. Each match assigned a confidence level: high, medium, or low

**Results:**
| Confidence | Sponsors | Trials |
|-----------|----------|--------|
| High | 489 | 42,040 |
| Medium | 429 | 12,663 |
| Low | 290 | 2,191 |
| Unmatched | 14,349 | 71,943 |

- 1,208 sponsors matched to public tickers covering 56,894 trials (44% of industry-sponsored trials)
- Top matched: Pfizer (PFE, 3,253), GlaxoSmithKline (GSK, 3,588), AstraZeneca (AZN, 3,412), Novartis (NVS)
- Top unmatched: Jiangsu HengRui (561 trials), Organon (505), Eisai (362) — mostly non-US companies

**Output:** `sponsor_tickers` table (15,557 rows) with fields: `lead_sponsor`, `ticker`, `company_name`, `cik`, `match_method`, `match_confidence`, `n_trials`

### 4. SEC EDGAR 8-K Filing Search (Step 4)

**Sources:**
1. SEC EDGAR Submissions API (`data.sec.gov/submissions/CIK{cik}.json`) — for filing metadata
2. SEC EDGAR Full-Text Search System (EFTS) (`efts.sec.gov/LATEST/search-index`) — for content-based search

**Two-phase approach:**

**Phase A — Filing metadata download:**
- Queried the EDGAR submissions API for 638 companies with high/medium confidence ticker matches. This is fewer than the 918 sponsors in Step 3 because many sponsors — subsidiaries, renamed and acquired entities — map to the same listed company and therefore the same ticker
- Downloaded metadata for all 8-K and 8-K/A filings (form type, filing date, accession number, primary document)
- Result: 43,065 8-K filings from 347 companies

**Phase B — Full-text content search:**
- Searched EFTS for 8-K filings containing clinical trial result language
- Search terms used:
  - `"topline results"`
  - `"primary endpoint"`
  - `"met its primary endpoint"`
  - `"did not meet" endpoint`
  - `"pivotal trial" results`
  - `"Phase 3" results endpoint`
  - `"Phase 2" results endpoint`
- Each EFTS hit includes the filing's CIK, accession number, and filing date
- Filtered to hits matching our company CIKs
- Result: 3,794 trial-result 8-K filings from 408 companies (2001–2026). The company count exceeds Phase A's 347 because the full-text search was post-filtered against all 638 queried CIKs rather than against Phase A's downloaded set

**Filing-to-trial matching:**
- For each industry trial with a `primary_completion` date, found the earliest 8-K from the same sponsor (by ticker) filed within 365 days after completion
- Used binary search on sorted filing lists for efficient matching
- Result: **8,205 trials** matched to a trial-result 8-K filing

**Fields added to `studies` table:**
- `sec_8k_filing_date` — date of the closest post-completion 8-K containing trial result language
- `sec_8k_accession` — EDGAR accession number

**Limitations:**
- EFTS returns at most 10,000 hits per query and does not support CIK-level filtering in the query itself; post-filtering was applied
- The filing-to-trial match is approximate: a company may file multiple 8-Ks for different trials, and the closest-date heuristic may not always pair them correctly
- Only the first matching 8-K within 365 days is captured; companies may issue multiple disclosures for the same trial
- EFTS hit counts were capped at ~2,000 per query due to pagination and rate limiting

### 5. 8-K Clinical Trial Outcome Classification (Step 5)

**Purpose:** Extract and classify clinical trial outcomes from the text of 8-K filings identified in Step 4, producing structured records suitable for event study analysis.

**Sample:** All 3,794 trial-result 8-K filings, processed across 8 extraction rounds (200 + 200 + 200 + 50 + 100 + 50 + 250 + 2,744). Filing texts were cached locally from EDGAR.

**Method — Dual-prompt consensus extraction:**

Rather than relying on a single LLM prompt, we developed a dual-prompt consensus approach to improve classification reliability. Two complementary prompts were applied independently to every filing:

**Prompt B1a (Ownership + Quote-first):**
- Only extract results the filing company owns, sponsors, or has material interest in (filters out third-party trial mentions)
- Extract 1–3 key sentences verbatim before classifying outcome
- Classify into: positive, negative, mixed-positive, mixed-negative, inconclusive, or no_result

**Prompt B3b (Quote-first + Statistics required):**
- Extract 1–3 key sentences verbatim before classifying
- Require explicit statistics field (p-values, HR, ORR, etc.)
- If no statistics reported, classify as "inconclusive" unless there is an unambiguous endpoint statement
- Designed to diverge from B1a on borderline cases, creating useful signal for consensus flagging

**Prompt selection process:**

The two prompts were arrived at through three rounds of testing on a fixed 10-filing subsample, with each
round varying one design idea at a time and keeping the earlier filings so that variants could be compared
on the same cases.

*The test subsample was chosen adversarially, not at random.* An earlier classification pass and a
validation pass had already been run over a larger set, and the ten filings retained for prompt testing
were weighted towards cases where those two passes had **disagreed** — eight of the ten, spanning
disagreements in both directions (filings called `no_result` by one pass and given a definitive outcome by
the other; a filing called `mixed-positive` by one and `negative` by the other; filings where one pass
found a single result and the other found three or four). The remaining two were cases where both passes
agreed, retained as controls. The intent was to select on hard cases rather than on average ones.

| Round | Variants tested | Design idea being varied |
|---|---|---|
| 1 | A, B, C | Overall extraction strategy. C required the model to work through an explicit drugs-found / results-found checklist and summarise it before classifying. A and B differed in framing, B taking the quote-first approach of grounding each classification in text drawn from the filing. B performed best. |
| 2 | B1, B2, B3 | What the model must return alongside the label, and what it must screen out. B1 introduced the ownership filter and a free-text justification; B2 added a self-reported confidence level with a reason; B3 introduced a dedicated verbatim key-sentence field, making the quote-first requirement explicit in the output rather than implicit in the framing. B1 and B3 were carried forward as complementary. |
| 3 | B1a, B1b, B1c and B3a, B3b, B3c | Three sub-variants of each. On the B1 side: **B1a** added quote-first extraction to the ownership filter; B1b instead added a flag for whether the announcement was new rather than a restatement of previously disclosed results; B1c required the primary endpoint and whether it was met to be extracted as separate fields. On the B3 side: B3a held the quote-first design unchanged; **B3b** added a mandatory statistics field; B3c added self-reported confidence instead. **B1a and B3b** were selected as the final pair on precision and on how usefully they diverged. |

**Why this pair:** the two prompts were retained because they fail differently rather than because both
scored well. B1a's ownership filter addresses a specific error mode of these filings — companies routinely
discuss trials they do not own, including competitors' — while its quote-first requirement forces a label to
be anchored to text that actually appears in the filing. B3b sets a deliberately higher evidential bar: it
must return a statistics field, and defaults to `inconclusive` where it cannot find one. Because that bar is
higher, the two prompts part company on precisely the borderline filings where a single prompt would give a
confident answer with nothing to check it against, which is what makes their disagreement usable as a
reliability signal rather than just noise.

The statistics requirement was a hard one: B3b had to return the field on every record, and where a filing
gave no formal test result it recorded what it could find in prose instead — for example *"60% fewer
additional intravitreal aflibercept injections in combination arm vs monotherapy; specific p-values not
reported"*. B1a was not asked for statistics and did not return them. This is the mechanism behind the
`b3b_inconclusive_override` consensus type: where B3b could find nothing to put in the field, it defaulted to
`inconclusive`, and B1a's definitive call was taken instead.

**The extracted statistics were not kept.** The requirement shaped the classifications — that is what the
override type above records — but the values themselves were never written to the student database.
`consensus_outcomes.statistics` exists and is empty in all 4,539 rows. If you need statistical results,
they have to be extracted from `filing_text` directly.

*Limitation of this process:* tuning on ten deliberately difficult filings selects for prompts that resolve
hard cases, and says little about calibration across the bulk of the corpus — in particular the 37% of
records that are `no_result`, which the subsample represents through disagreement cases rather than
straightforward ones. The prompt pair was not re-validated on a random sample after selection.

**Execution:**
- ~760 extraction agents total across 8 rounds (~380 per prompt)
- Each agent processed 10 filings from a pre-built batch manifest
- Agents launched in waves of 2–4 to manage API rate limits
- Batch 8 (2,744 filings) used 275 manifests per prompt, with automated chaining and rate-limit recovery
- Output: flat JSON arrays with per-trial records including accession, ticker, filing date, drug name, phase, indication, key sentences, outcome, and evidence

**Consensus rules:**
Results from the two prompts were matched by accession number and drug name, then resolved:

| B1a outcome | B3b outcome | Consensus | Type |
|-------------|-------------|-----------|------|
| Same | Same | Keep | Agree |
| positive | mixed-positive | positive | Same direction |
| negative | mixed-negative | negative | Same direction |
| Any definitive | inconclusive | Take definitive | B3b stats override |
| Opposite direction | Opposite direction | Flag for review | Real disagreement |

**Results (3,794 filings — full coverage):**

| Metric | Count |
|--------|-------|
| Consensus results | 4,494 |
| Flagged disagreements | 45 (1.0%) |
| Total records (incl. flagged) | 4,539 |

*Consensus type breakdown:*

| Type | Count | Description |
|------|-------|-------------|
| Exact agreement | 1,391 | Both prompts found same drug, same outcome |
| Both no_result | 1,694 | Both agreed filing had no trial results |
| B3b inconclusive override | 370 | B3b said inconclusive (no stats), B1a had definitive call |
| Same direction | 67 | e.g., positive vs mixed-positive |
| B1a only | 446 | B1a found a result B3b missed |
| B3b only | 523 | B3b found a result B1a missed |
| B1a inconclusive override | 3 | B1a said inconclusive, B3b had definitive call |
| Real disagreement | 45 | Opposite classifications, flagged for review |
| **Total** | **4,539** | |

The first two rows are both stored as `consensus_type = 'agree'` in the database; they are split here
because "both prompts agreed there was no result" is a different kind of agreement from "both prompts
read the same result the same way".

*Final outcome distribution:*

| Outcome | Count |
|---------|-------|
| Positive | 1,898 |
| No result | 1,694 |
| Negative | 403 |
| Inconclusive | 209 |
| Mixed-positive | 205 |
| Mixed-negative | 85 |

**Outcome definitions:**
- **positive** — Primary endpoint met with statistical significance, or unambiguous statement of success
- **negative** — Primary endpoint missed, trial stopped for futility, or program discontinued
- **mixed-positive** — Some endpoints met but others missed; overall direction favourable
- **mixed-negative** — Some endpoints met but overall unfavourable
- **inconclusive** — Results reported but insufficient to determine direction (e.g., interim analysis, no statistics)
- **no_result** — Filing does not contain clinical trial outcome data (e.g., earnings report, corporate transaction)

**Limitations:**
- Drug name matching between prompts uses substring containment, which can cross-match different indications of the same drug
- Single-prompt-only results (~850 records) have lower confidence than dual-confirmed results
- The "inconclusive" override rule assumes B3b's higher inconclusive rate is driven by its statistics requirement rather than genuine ambiguity
- 10 tickers (warrants, delisted equities) had no downloadable price data, reducing event study coverage slightly

**Output files:**
- `8k_parsed/consensus_results.json` — 4,494 classified trial results
- `8k_parsed/consensus_disagreements.json` — 45 flagged disagreements for manual review
- `8k_parsed/b1a_results_*.json`, `b1a_batch{2-8}_results_*.json` — Raw B1a prompt outputs (~380 files)
- `8k_parsed/b3b_results_*.json`, `b3b_batch{2-8}_results_*.json` — Raw B3b prompt outputs (~380 files)
- `8k_parsed/run_consensus.py` — Consensus comparison script

### 6. Event Study — Market Reaction to Trial Announcements (Step 6)

**Purpose:** Measure abnormal stock returns around 8-K filings that disclose clinical trial results, testing whether the market differentiates between positive, negative, and inconclusive outcomes.

**Method — Market model event study:**
- **Estimation window:** [-130, -11] trading days (120 days) before filing date
- **Event window:** [-1, +1] trading days (3-day CAR)
- **Market benchmark:** S&P 500 (SPY)
- **Model:** OLS market model: R_i = α + β·R_m + ε, estimated over the estimation window
- **Abnormal returns:** AR_t = R_it - (α̂ + β̂·R_mt), summed over the event window to produce CAR[-1,+1]
- **Winsorisation:** 1st/99th percentile to limit impact of illiquid penny stocks. This was applied to the CAR itself, after cumulating, not to the daily returns beforehand. The untreated values are retained in `car_3day_raw` (whose minimum is −827.02), so any range or percentile quoted from `car_3day` is capped at the tails by construction
- **Minimum data:** 60 trading days in estimation window required; events with insufficient price data excluded

**Stock prices:** Downloaded via yfinance for 401 company tickers plus SPY, XBI (SPDR S&P Biotech ETF), and IBB (iShares Biotechnology ETF). The market model uses SPY alone, following the single-factor convention; XBI and IBB were downloaded but not used as benchmarks. For a sample that is entirely biotech and pharma, a sector factor would absorb variance that the single-factor residual currently treats as abnormal — adding one is a reasonable extension. 10 tickers (warrants, delisted equities) had no downloadable data. Total: 1,223,564 daily closing prices and volumes stored in `stock_prices` table.

**Results (2,615 events):**

| Outcome Group | n | Mean CAR | Median CAR | t-stat | p-value |
|---|---|---|---|---|---|
| Positive | 1,944 | +1.60% | -0.52% | +3.49 | 0.0005 |
| Negative | 448 | -17.45% | -4.92% | -12.92 | <0.0001 |
| Inconclusive | 181 | +0.29% | -0.63% | +0.28 | 0.78 |

*By detailed outcome:*

| Outcome | n | Mean CAR | t-stat | p-value |
|---|---|---|---|---|
| positive | 1,756 | +2.44% | +5.23 | <0.0001 |
| negative | 370 | -18.79% | -12.56 | <0.0001 |
| mixed-positive | 188 | -6.30% | -3.69 | 0.0003 |
| mixed-negative | 78 | -11.06% | -3.63 | 0.0005 |
| inconclusive | 181 | +0.29% | +0.28 | 0.78 |

The three outcome groups above sum to 2,573, not 2,615. The remaining **42 events carry a null
`outcome_group`**: these are the rows where the two prompts disagreed outright, which the pipeline
flagged rather than resolved (`consensus_type = 'flagged_disagreement'`). Their granular `outcome`
column retains the compound value, such as `positive/negative`, so the disagreement is recoverable.

**Key findings:**
- Strong asymmetry: negative results produce ~7× larger absolute CARs than positive results
- **The positive group has a positive mean but a negative median** (+1.60% against −0.52%): 1,014 of
  the 1,944 positive-outcome events, 52.2%, were followed by a negative three-day abnormal return.
  This is the "sell the news" pattern — the market had already priced the expected success — and it
  means `car_3day` is heavily skewed within both groups, which matters for anything modelled on it
- Mixed outcomes carry negative CARs regardless of direction suffix — markets punish ambiguity
- Inconclusive results show no significant market reaction (near-zero CAR, p=0.78)
- Phase 2 and Phase 3 results drive the effect; Phase 1 results show no significant reaction
- 230 events dropped due to insufficient price history (delisted tickers, very recent IPOs)
- Filings classified `no_result` never enter the event study at all: with no reported trial outcome there is no event to measure a reaction to. They are roughly 37% of all classifications, which is why the event study covers 2,615 records against 4,539 classified

**Output:** `event_study_results` table in ctgov.db (2,615 rows), `event_study_summary.csv`

### 7. Study–Event Linkage (Step 7)

**Purpose:** Link each 8-K clinical trial outcome event (from `event_study_results`) to its specific ClinicalTrials.gov registration in `studies`, enabling enrichment of market reaction data with trial design features (enrollment, masking, allocation, endpoints, etc.).

**Challenge:** The existing linkage between 8-K filings and trials (Step 4) uses date-proximity matching at the sponsor level. Step 7 performs precise drug-level matching: given an event like "solanezumab Phase 3 in Alzheimer's disease disclosed by Lilly on 2012-10-24", find the exact NCT registration. This is non-trivial because:
- ClinicalTrials.gov often registers drugs under internal code names (e.g., LY2062430 instead of solanezumab)
- Multi-drug filings require matching each drug separately
- Trials may be sponsored by subsidiaries, partners, or acquired entities

**Method — Two-pass candidate search + LLM disambiguation:**

**Pass 1 — Candidate generation (`build_linkage_candidates.py`):**
- Tokenised drug names from 2,482 unique (accession, drug_name) pairs, splitting on parentheses and combination separators (+, /, "and")
- Built an inverted index mapping intervention name tokens to NCT IDs across all 521,891 studies with interventions
- Two-tier candidate search: same-sponsor first (via `sponsor_tickers` mapping), then cross-sponsor fallback (all industry studies)
- Capped at 50 candidates per event, ranked by number of matching tokens
- Extracted ~500-character 8-K filing excerpts around drug name mentions for agent context

*Pass 1 candidate stats:*

| Search method | Events | Pct |
|---|---|---|
| Same-sponsor match | 2,019 | 81.3% |
| Cross-sponsor match | 330 | 13.3% |
| No candidates | 133 | 5.4% |

**Pass 1 — LLM agent disambiguation:**
- Split 2,482 events into 249 manifests of ~10 events each
- Each manifest processed by an LLM agent given: event metadata (drug name, phase, indication, ticker, filing date), 8-K excerpt, and candidate study details (NCT ID, title, conditions, phase, interventions, primary completion date, enrollment, status, sponsor)
- Agents returned: best-matching NCT ID (or "no_match"), confidence level (high/medium/low), and free-text reasoning
- Pass 1 result: 1,944 matched (78.3%), 538 no_match

**Pass 2 — Expanded search for no-match events (`linkage_pass2.py`):**

Analysis of pass 1 no-match cases revealed a systematic gap: ClinicalTrials.gov frequently registers drugs under internal code names rather than the generic/brand names used in 8-K filings. For example, solanezumab is registered as "LY2062430" in intervention fields, so token matching on "solanezumab" fails.

Pass 2 addressed this with two improvements:
1. **Title-based search** — Added `brief_title` and `official_title` to the search index (299,412 unique tokens). Titles almost always contain the drug's commercial/generic name even when intervention fields use code names.
2. **Agent-suggested NCT injection** — Pass 1 agents often identified the correct NCT ID in their reasoning text (from training knowledge) despite returning "no_match" because it wasn't in their candidate list. These NCT IDs were extracted, validated against the database, and injected as candidates for pass 2.

Pass 1 candidates (already rejected) were excluded to focus agents on genuinely new options. 333 of the 538 no-match events yielded new candidates; 34 manifests were processed by agents.

*Pass 2 result:* 156 additional matches recovered (6.3pp improvement).

**Final linkage results:**

| Match method | Events | Pct |
|---|---|---|
| Same-sponsor (pass 1) | 1,703 | 68.6% |
| Cross-sponsor (pass 1) | 241 | 9.7% |
| Title search (pass 2) | 156 | 6.3% |
| No match | 382 | 15.4% |

| Confidence | Events | Pct |
|---|---|---|
| High | 2,056 | 82.8% |
| Medium | 362 | 14.6% |
| Low | 64 | 2.6% |

**Bias assessment:** The 382 unmatched events show no material outcome bias (67.7% positive vs 67.0% matched), confirming the matched sample is representative. Unmatched events skew slightly toward pre-2007 filings (before mandatory ClinicalTrials.gov registration), very recent filings (not yet indexed), and small biotechs with unregistered trials.

**Table construction (`build_linkage_tables.py`):**
- `study_event_link` — Primary linkage table: (accession, drug_name) → nct_id, with match method, confidence, candidate count, and agent reasoning. Note that `match_confidence` is recorded for every *attempted* match, including those that failed: 382 rows here (and 412 in `event_study_enriched`) carry a confidence value with a null `nct_id`, so filtering on `match_confidence IS NOT NULL` does not give you the linked set — filter on `nct_id` instead
- `event_study_enriched` — Denormalised analytical table joining `event_study_results` → `study_event_link` → `studies`. Contains all event study columns (CAR, alpha, beta) plus 30 trial design columns (enrollment, masking, allocation, endpoints, conditions, etc.). Keyed by (accession, drug_name, indication); note that a small number of (accession, drug_name) pairs appear more than once where the same drug reported results for multiple indications in the same filing
- `filing_text` — Raw 8-K filing text for all 3,794 trial-result filings, loaded from cached .txt files
- `filing_summary` — One row per accession with aggregated outcomes, primary outcome (using severity hierarchy: negative > mixed-negative > mixed-positive > inconclusive > positive), and a mixed-outcome flag

**Limitations:**
- Token-based candidate search cannot resolve code-name → generic-name mappings without title search. Pass 2 addresses most cases but some remain.
- Subsidiary and partner sponsors (e.g., Loxo Oncology for Lilly drugs, Boehringer Ingelheim for co-developed drugs) are not captured by `sponsor_tickers`, limiting same-sponsor matching.
- ~5% of events classified as trial results upstream are actually patent rulings, regulatory updates, or commercial milestones — these correctly receive no_match.
- Agent-mentioned NCT IDs are validated against the database but not independently verified for factual accuracy.

**Output:** `study_event_link` (2,482 rows), `event_study_enriched` (2,615 rows), `filing_text` (3,794 rows), `filing_summary` (1,905 rows) in ctgov.db

### 8. Market Capitalisation (Step 8)

**Method:** Market capitalisation is computed as shares outstanding × unadjusted close price on or immediately before the event date. Shares outstanding were extracted from SEC 10-K and 10-Q cover pages using an LLM agent pipeline (1,529 ticker-date pairs). Close prices from yfinance were corrected to remove dividend adjustments and account for stock splits occurring after the event date.

**Coverage:** 2,526 of 2,615 events (96.6%). The 89 null events lack either a matching SEC filing, price data (delisted tickers), or have been set to null where incomplete split history would produce unreliable values.

**Output:** `market_cap` column added to `event_study_enriched` table.

## Student Database

The student database (`ctgov.db`) contains 12 tables described in the data dictionary (`data_dictionary.xlsx`) provided with the assignment. Ten are a curated subset of the full pipeline database, which contains additional intermediate tables (FDA application records, sponsor–ticker mappings, raw 8-K filing metadata, etc.) not included in the student distribution. The remaining two (`asclepius_readouts`, `asclepius_scenario_filings`) are fictional data built for Question 4a and are not derived from the pipeline at all — see the fourth provenance category below. Two tables are narrowed for the student distribution. `studies` holds 1,160 rows and 77 columns, covering only the trials linked to events in this dataset — the 77 being the 66 extracted in Step 1, plus the 5 FDA fields from Step 2, the 2 SEC fields from Step 4, and four MeSH columns carried over from the ClinicalTrials.gov browse module (`mesh_conditions`, `mesh_condition_ids`, `condition_ancestors` and `mesh_interventions`; the *counts* `n_mesh_conditions` and `n_mesh_interventions` are among the 66). `stock_prices` holds 486,378 rows of price data windowed around event dates rather than the full download.

### Table inventory

| Table | Rows | Grain and key | Produced by | Provenance |
|---|---|---|---|---|
| `studies` | 1,160 | One registered trial; unique on `nct_id` | Step 1, with the FDA fields added in Step 2 and the SEC fields in Step 4 | Registry-reported |
| `fda_drug_match` | 1,495 | One drug name as written in the filings; unique on `drug_name` | Step 2b | LLM-extracted for 723 names, computed string match for 772 |
| `event_fda_features` | 2,482 | One event; unique on `(accession, drug_name)` | Step 2b | Computed, on LLM-assisted drug matches |
| `filing_text` | 3,794 | One 8-K; unique on `accession` | Downloaded in Step 4, loaded in Step 7 | Registry-reported (EDGAR text, verbatim) |
| `consensus_outcomes` | 4,539 | One extracted result claim; `(accession, drug_name, indication)` is a near-key, 4,532 distinct | Step 5 | LLM-extracted |
| `stock_prices` | 486,378 | One ticker-day; unique on `(ticker, date)`; 320 tickers | Step 6 | Computed (downloaded prices) |
| `event_study_results` | 2,615 | One event; `(accession, drug_name, indication)` is a near-key, 2,610 distinct | Step 6 | Computed, on LLM-extracted event keys |
| `study_event_link` | 2,482 | One event; unique on `(accession, drug_name)`; `nct_id` is null on 382 rows | Step 7 | LLM-extracted |
| `event_study_enriched` | 2,615 | One event; same near-key, 2,610 distinct; 112 `(accession, drug_name)` pairs carry more than one row | Step 7, with `market_cap` added in Step 8 | Mixed: LLM-extracted, registry-reported and computed fields in the same row |
| `filing_summary` | 1,905 | One filing that yielded at least one outcome; unique on `accession` | Step 7 | Computed from LLM-extracted outcomes |
| `asclepius_readouts` | 3 | One fictional pending readout; unique on `readout_id` | Authored for Question 4a | Authored-fictional |
| `asclepius_scenario_filings` | 9 | One fictional filing; unique on `accession`, and on `(readout_id, scenario)` | Authored for Question 4a | Authored-fictional |

`event_fda_features` joins to `event_study_enriched` on `(accession, drug_name)` without fanning out,
because it is itself unique on that pair. The repetition is on the other side: `event_study_enriched`
also varies by indication, so a drug that reported two indications in the one filing takes the same FDA
feature row twice. De-duplicate before counting events off the joined result.

Treat the event-table triple as a near-key rather than a key. A handful of triples repeat, in both
`consensus_outcomes` and the two event tables, so anything that assumes uniqueness needs checking first.
The linkage tables also reference two NCT registrations that were not carried into the trial table
(NCT06049915 and NCT06726604): those events have a non-null `nct_id` with every trial-design column
null, so a non-null `nct_id` tells you the linkage succeeded, not that design fields are present.

*Computed* is not the same as *reliable*. `event_study_results`, `event_fda_features` and
`filing_summary` are arithmetic, but the arithmetic runs on event keys and drug matches produced by a
language model, so they inherit the error modes of Steps 5 and 2b rather than escaping them. Price
coverage runs from 2000-01-03 to 2026-05-08 and is windowed around event dates, not continuous per
ticker. One row in `filing_text` has an empty text field and should be dropped by anything that
tokenises the corpus rather than counted as a filing with no trial language.

### Field provenance

Fields in the student database come from four different kinds of source, and the analytical tables mix them in the same row. Which source a field came from determines what it can be relied on for.

- **LLM-extracted from the 8-K filing text** (Step 5): `outcome`, `consensus_type`, `drug_name`, `indication`, `phase`, `evidence`, `statistics`, `flagged`. These describe *what the company announced*, as read out of the filing by a language model.
- **Reported by the sponsor to ClinicalTrials.gov** (Step 1), reaching the analytical tables through the Step 7 linkage: the trial-design fields — `enrollment`, `masking`, `allocation`, `intervention_model`, `eligibility_criteria`, `primary_outcome_1`, `conditions`, `phases`, dates, and the remaining `studies` columns. These describe *how the trial was designed and registered*.
- **Computed from market and regulatory data**: `car_3day`, `alpha`, `beta` and the other event-study fields from daily prices (Step 6); `market_cap` from SEC cover-page share counts and prices (Step 8); the `event_fda_features` columns from matched Drugs@FDA application records (Step 2b).
- **Authored for the Question 4a scenario** (fictional): every field in `asclepius_readouts` and `asclepius_scenario_filings`. These mirror the shape of the historical tables above so the same analysis code runs against them, but describe no real trial, filing or market activity — nothing in them is evidence about any real drug or company.

Note in particular that `phase` in the event tables is the LLM's reading of the filing, while `phases` in `studies` is the sponsor's registered value; they are independent and do not always agree. Where a field exists in both forms, the difference between them is itself information.

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total clinical studies | 580,678 |
| Industry-sponsored studies | 128,837 |
| Studies matched to FDA drug | 135,099 |
| Studies with FDA-approved drug | 133,363 |
| Studies matched to trial-result 8-K | 8,205 |
| Fully linked (trial + FDA + 8-K) | ~5,000* |
| Event–study linkage (drug-level) | 2,100 of 2,482 (84.6%) |
| Unique filings with outcomes | 1,905 |
| **Rows in `event_study_enriched`** | **2,615** |

*Approximate count of studies with all three linkages.

`event_study_enriched` has 2,615 rows against 2,482 linked (accession, drug_name) pairs because a small number of pairs reported results for more than one indication in the same filing, and the table is keyed by (accession, drug_name, indication). This is the table most analysis is built on.

## Analytical Use Cases

This linked dataset enables research questions such as:
- **Information timing:** How quickly after trial completion do companies file 8-Ks disclosing results? What is the distribution of the lag?
- **Selective disclosure:** Are positive results (FDA-approved drugs) disclosed faster than negative results (unapproved)?
- **Market efficiency:** Does the gap between ClinicalTrials.gov status updates and 8-K filings create a window for informed trading?
- **Regulatory prediction:** What trial characteristics (phase, enrollment, design, sponsor size) predict FDA approval?
- **Disclosure compliance:** Do companies systematically delay disclosure of negative trial outcomes?
- **Geographic patterns:** Do trials conducted in different countries show different disclosure timing?

## Technical Notes

- All data is stored in a single SQLite database (`ctgov.db`) for portability
- Python 3.13 was used for all ETL operations. The acquisition steps need only `requests` and `tqdm`; the event study (Step 6) additionally uses `yfinance`, `pandas` and `numpy`, and Steps 2b, 5, 7 and 8 call an LLM API
- No API keys were required for the data sources — ClinicalTrials.gov, openFDA, SEC EDGAR and Yahoo Finance are all freely accessible. The LLM steps (2b, 5, 7 and 8) do require API credentials
- Drug name matching uses normalisation (lowercasing, stripping formulation/dosage suffixes) and falls back to individual-word matching
- The EDGAR EFTS search is rate-limited to ~8 requests/second; 0.12–0.15s delays were inserted between requests
- Price data is retrieved through `yfinance`, which scrapes Yahoo Finance. Its terms are not the same as the public-domain and public-record sources above; the price data here is distributed for teaching use only
- The acquisition and table-construction scripts cache their work: re-running skips already-completed steps. Note that this is caching rather than idempotence in the strict sense — the LLM steps are non-deterministic, so a genuine re-run would not reproduce the same labels. **The shipped labels are the canonical artefact, not a regenerable one**

## Reproducibility

The pipeline was built using 10 Python scripts covering API download, matching, and table construction, with a total build time of approximately 40 minutes (dominated by API download rates). LLM agent disambiguation (Steps 5 and 7) required additional time for API calls. The build scripts are not included in the student distribution — this document describes the methodology so that students can evaluate the data quality and understand the provenance of each table.
