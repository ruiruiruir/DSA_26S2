"""Reproduce the Q1a stratified sample and write each filing out in full, so the
30 classifications can be read against the source text outside the notebook."""
import os, re, sqlite3, textwrap
import pandas as pd

OUT = "q1a_sample_filings"
MEMBER_ID = 40100
SIX = ["positive", "negative", "mixed-positive", "mixed-negative", "inconclusive", "no_result"]

conn = sqlite3.connect("ctgov.db")
consensus = pd.read_sql("SELECT * FROM consensus_outcomes", conn)
event_res = pd.read_sql("SELECT * FROM event_study_results", conn)
filing_txt = pd.read_sql("SELECT accession, filing_text FROM filing_text", conn)

# --- helpers copied verbatim from the notebook (Q1 cell 7) ---------------------
MOJIBAKE = {"’": "'", "‘": "'", "“": '"', "”": '"',
            "–": "-", "—": "-", "−": "-", "′": "'",
            "▪": " ", "●": " ", "•": " ", "·": " ",
            "Ÿ": " ", " ": " ", "�": " ",
            "☐": " ", "☒": " "}
RE_COVER = re.compile(r"^.{0,6000}?Check the appropriate box below.*?13e-4\(c\)\)", re.S | re.I)
RE_SAFE = re.compile(
    r"(?:This (?:press release|communication|report|presentation)[^.]{0,200}(?:forward-looking)"
    r"|Forward[- ]Looking Statements?|Safe Harbor Statement|Private Securities Litigation Reform Act)"
    r".{0,12000}?(?=(?:Item \d|EX-|Exhibit \d|SIGNATURE|About [A-Z]|Contacts?:|###|$))", re.S | re.I)
RE_EXIDX = re.compile(r"Item 9\.01[^A-Za-z]{0,20}Financial Statements and Exhibits"
                      r".{0,2000}?(?=(?:SIGNATURE|EX-|Exhibit 99|$))", re.S | re.I)
RE_TAIL = re.compile(r"SIGNATURES?\s+Pursuant to the requirements of the Securities Exchange Act"
                     r".{0,3000}?(?=(?:EX-|Exhibit\s?99|Item \d|$))", re.S | re.I)

def clean_filing_text(t):
    if not isinstance(t, str):
        return ""
    for k, v in MOJIBAKE.items():
        t = t.replace(k, v)
    t = RE_COVER.sub(" ", t, count=1)
    t = RE_SAFE.sub(" ", t)
    t = RE_EXIDX.sub(" ", t)
    t = RE_TAIL.sub(" ", t)
    t = re.sub(r"\b([A-Za-z]{2,})\s+-\s+([A-Za-z]{2,})\b", r"\1-\2", t)
    t = re.sub(r"https?://\S+", " ", t)
    return re.sub(r"\s+", " ", t).strip()

RE_FIN = re.compile(
    r"(Reports?|Announces?)\b[^.]{0,90}\b(First|Second|Third|Fourth)[- ]Quarter"
    r"|(Reports?|Announces?)\b[^.]{0,70}\b(Financial|Fiscal|Full[- ]Year|Annual|Year[- ]End)\b[^.]{0,40}Results"
    r"|Quarterly (Report|Results)|Results of Operations and Financial Condition|Item 2\.02", re.I)
RE_RES = re.compile(
    r"\b(Announce[sd]?|Report(s|ed)?|Present(s|ed)?|Provide[sd]?)\b[^.]{0,150}"
    r"\b(top-?\s?line|primary endpoint|pivotal|Phase\s?[1-4I]|results? (from|of|in|for)|data (from|in|at))\b", re.I)
RE_DECK = re.compile(r"\b(corporate|company|investor|business)\s+(presentation|deck|update|overview)\b"
                     r"|Item 7\.01|Regulation FD Disclosure", re.I)
RE_PRIOR = re.compile(
    r"\b(previously (announced|reported|disclosed)|as (previously )?announced"
    r"|in (January|February|March|April|May|June|July|August|September|October|November|December)"
    r" 20\d\d,? (the Company |we |[A-Z][a-z]+ )?(announced|reported)|earlier this year)\b", re.I)

def classify_filing(clean_text, raw_text, head=1200, body=6000):
    h, b = clean_text[:head], clean_text[:body]
    fin, res = bool(RE_FIN.search(h)), bool(RE_RES.search(h))
    if res and not fin:
        kind = "results announcement"
    elif fin or RE_FIN.search(b):
        kind = "periodic report"
    elif RE_DECK.search(b):
        kind = "deck / FD update"
    elif RE_RES.search(b):
        kind = "results announcement"
    else:
        kind = "other"
    return kind, len(RE_PRIOR.findall(raw_text))

filing_txt["clean"] = filing_txt.filing_text.map(clean_filing_text)
_k = [classify_filing(c, r) for c, r in zip(filing_txt.clean, filing_txt.filing_text)]
filing_txt["filing_kind"] = [k for k, _ in _k]
filing_txt["n_prior_refs"] = [n for _, n in _k]

# --- the sample, drawn exactly as the notebook draws it ------------------------
car_by_row = event_res.drop_duplicates(["accession", "drug_name"])[["accession", "drug_name", "car_3day"]]
cons_car = consensus.merge(car_by_row, on=["accession", "drug_name"], how="left")
sample = pd.concat([cons_car[cons_car.outcome == o].sample(n=5, random_state=MEMBER_ID)
                    for o in SIX]).reset_index(drop=True)
sample = sample.merge(filing_txt[["accession", "filing_kind", "n_prior_refs"]], on="accession", how="left")

raw_by_acc = filing_txt.set_index("accession")["filing_text"]
clean_by_acc = filing_txt.set_index("accession")["clean"]

os.makedirs(OUT, exist_ok=True)
for i, r in sample.iterrows():
    car = "n/a" if pd.isna(r.car_3day) else "%+.2f%%" % (100 * r.car_3day)
    fn = "%02d_%s_%s_%s.txt" % (i, r.outcome.replace("/", "-"), r.ticker, r.accession)
    with open(os.path.join(OUT, fn), "w", encoding="utf-8") as f:
        f.write("SAMPLE INDEX      : %d\n" % i)
        f.write("ACCESSION         : %s\n" % r.accession)
        f.write("TICKER / DATE     : %s  %s\n" % (r.ticker, r.filing_date))
        f.write("DRUG / PHASE      : %s  |  %s\n" % (r.drug_name, r.phase))
        f.write("INDICATION        : %s\n" % r.indication)
        f.write("LLM LABEL         : %s   (consensus_type=%s)\n" % (r.outcome, r.consensus_type))
        f.write("CAR[-1,+1]        : %s\n" % car)
        f.write("DOCUMENT KIND     : %s   restatement phrases=%d\n" % (r.filing_kind, r.n_prior_refs))
        f.write("LLM EVIDENCE      : %s\n" % (r.evidence or "(blank)"))
        f.write("LLM STATISTICS    : %s\n" % (r.statistics or "(blank)"))
        f.write("\nYOUR VERDICT      : ____________________  (label fair? document kind right?)\n")
        f.write("\n" + "=" * 100 + "\nCLEANED TEXT (what the notebook analyses)\n" + "=" * 100 + "\n\n")
        f.write(textwrap.fill(clean_by_acc.get(r.accession, ""), 100))
        f.write("\n\n" + "=" * 100 + "\nRAW TEXT (exactly as stored in filing_text)\n" + "=" * 100 + "\n\n")
        f.write(str(raw_by_acc.get(r.accession, "")))
    print("%-58s  %6d raw / %6d clean chars" % (fn, len(str(raw_by_acc.get(r.accession, ""))),
                                                len(clean_by_acc.get(r.accession, ""))))

sample.to_csv(os.path.join(OUT, "_index.csv"), index=False)
print("\nWrote %d filings + _index.csv to %s/" % (len(sample), OUT))
