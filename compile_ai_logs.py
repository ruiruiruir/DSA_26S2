#!/usr/bin/env python3
"""
compile_ai_logs.py - Data Science Applications assignment helper.

Run this from your submission folder (the one that contains `ai_logs/`):

    python compile_ai_logs.py 123456        # your member ID

No Python on your machine? Use `Run_AI_Log_Packager.ipynb`, provided with this
script, which does the same thing in Google Colab.

What it does:
  1. Scans `ai_logs/` and every folder inside it for the AI conversations you
     saved.
  2. Writes ONE file - a package named after your member ID - containing every
     one of those files exactly as you saved them, plus a `MANIFEST.md` listing
     what is in it: dates, question tags, sizes, the opening line of each file,
     and a SHA-256 for every one.
  3. Tells you, by name, which files you should look at before you submit:
     anything holding a key-shaped string, and anything that looks like a full
     export of your entire chat history.

READ WHAT IT TELLS YOU, AND ACT ON IT. In particular: a bulk export downloaded
from ChatGPT or Claude.ai contains EVERY conversation you have ever had, and
the archive it arrives in also holds your name and email address. If this
script names one of those, open it. Save the individual conversations you want
to submit as .md files instead.

What it does not do:
  - It does not read your conversations to you, merge them, or rewrite them.
    Every file goes in exactly as you saved it. What a marker reads first is
    the manifest, and then the files you saved.
  - It does not claim to know who typed what. The manifest describes your
    files; it does not describe how you worked.
  - It does tell you when a session file carries the tool's own output - shell
    commands and their results, files the agent read. That is submitted as
    saved, so skim those files.
  - It cannot tell that a conversation holds your employer's confidential
    information. Only you can. Skim before you submit.

It NEVER modifies or deletes your saved conversation files. The only file it
ever writes is the package, and it writes that OUTSIDE `ai_logs/`, so it is
safe to re-run at any time.

You are not asked to write anything up - the script packages what you saved.
You are asked to stand behind it, so read the manifest before you submit it.

No third-party packages required - Python 3.8+ standard library only.
"""

import hashlib
import json
import os
import re
import sys
import traceback
import zipfile
from datetime import datetime
from pathlib import Path

LOG_DIR_NAME = "ai_logs"
PACKAGE_DEFAULT = "AI_LOGS.zip"     # the one file this script will ever write
PACKAGE_PATTERN = "DSA 2026 S2 Assignment %s.zip"
# The brief requires 'DSA 2026 S2 Assignment <member ID>'. This becomes a
# filename, so a separator or a '..' would be a path rather than a name.
MEMBER_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _-]{0,40}$")
DOT_REASON = ("the name starts with a dot, so Windows and this script both "
              "treat it as a system file and it is NOT in the package. Files "
              "arrive this way from macOS, a Mac-built zip or a git folder. "
              "If it is a conversation you saved, rename it without the "
              "leading dot and run this again.")
WALK_REASON = ("this folder could not be opened, so nothing inside it is in "
               "the package (%s). On Windows the usual cause is a path longer "
               "than 260 characters: move your submission folder nearer the "
               "top of the drive, or shorten the folder names, and run this "
               "again.")
# Extensions a student expects to be readable. An undecodable .png is a
# picture; an undecodable .md was meant to be read, and is worth reporting.
TEXTISH = {".md", ".txt", ".log", ".text", ".json", ".jsonl", ".csv"}
# Not an upload limit; the Canvas cap is far higher (~5 GB, unconfirmed).
# This flags "you have probably included something you did not mean to". The
# environment variable is for testing without a 100 MB fixture.
SIZE_WARN = int(os.environ.get("AI_LOGS_SIZE_WARN") or 100 * 1024 * 1024)
NAME_RE = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})(?:_(?P<time>\d{4}))?"
    r"_(?P<qtag>Q[1-5]|multiQ|general)_(?P<topic>.+)$",
    re.IGNORECASE,
)


# --- Talking to the student --------------------------------------------------
# Output must not raise. A traceback after the package is written costs no
# data, but the student reads it as a failed run.
#
# It only arises where stdout is not a console (redirected, an IDE pane, a
# notebook) and a filename carries a character outside the ANSI code page.
# backslashreplace, not replace, so two names differing only outside that page
# stay distinguishable.


def _safe_streams():
    """Give stdout and stderr an error handler that cannot raise."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="backslashreplace")
        except (AttributeError, ValueError, OSError):
            pass        # not a stream we can reconfigure; say() is the backstop


def say(text="", stream=None):
    """print() that cannot raise on a character the stream cannot encode.

    The backstop for a stdout _safe_streams() could not reconfigure. It must
    still print the filename: a warning that does not name its file cannot be
    acted on.
    """
    stream = sys.stdout if stream is None else stream
    try:
        stream.write(text + "\n")
        return
    except UnicodeEncodeError:
        pass
    encoding = getattr(stream, "encoding", None) or "ascii"
    try:
        stream.write(text.encode(encoding, "backslashreplace")
                     .decode(encoding, "replace") + "\n")
    except Exception:
        pass            # a report that cannot be printed must not end the run


def die(message):
    """Exit with a message, via say() so the message itself cannot raise.

    sys.exit(str) would write through the stream's own error handler, which an
    exit message naming a file or carrying a localised OS error can defeat.
    """
    say(message, stream=sys.stderr)
    sys.exit(1)


def find_log_dir() -> Path:
    """Look for ai_logs/ in the current directory, or accept being run inside it."""
    here = Path.cwd()
    if (here / LOG_DIR_NAME).is_dir():
        return here / LOG_DIR_NAME
    if here.name == LOG_DIR_NAME:
        return here
    die(
        f"Could not find an '{LOG_DIR_NAME}' folder here ({here}).\n"
        f"Run this script from your submission folder, or create the folder first."
    )


class UnreadableText(Exception):
    """A file whose bytes are not usable as text. Carries the reason."""


def read_text(path: Path) -> str:
    """Read a file as text, or refuse it and say why.

    The byte order mark is checked before any decode: Notepad's "Unicode"
    option writes UTF-16, which a permissive fallback turns into
    NUL-interleaved mojibake. Text still carrying NUL after decoding is
    refused rather than published.
    """
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        # Plain utf-8 would leave U+FEFF at the head of the text, where it
        # reaches the opening line the manifest quotes.
        text = raw.decode("utf-8-sig")
    elif raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        try:
            text = raw.decode("utf-16")
        except UnicodeDecodeError:
            raise UnreadableText(
                "it begins with a UTF-16 byte order mark, but the rest of "
                "the file is not valid UTF-16 (it may have been cut short)")
    else:
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            # Windows "ANSI" saves. cp1252 rather than latin-1: latin-1
            # cannot fail, so it decodes curly quotes into invisible C1
            # controls and publishes the result silently. cp1252 leaves five
            # byte values undefined, so an unreadable file is named instead.
            #
            # Known gap: where the machine's code page is cp932 or cp936 this
            # is the wrong fallback, and such a file is refused only if its
            # bytes happen to hit one of those five values. The fix is to try
            # locale.getpreferredencoding() first; it needs a non-English
            # Windows machine to test on. Design spec, section 9.
            try:
                text = raw.decode("cp1252")
            except UnicodeDecodeError as exc:
                raise UnreadableText(
                    "it is not valid UTF-8, and not valid Windows ANSI "
                    "either (%s). A save made in another language's code "
                    "page looks like this" % exc)
    if "\x00" in text:
        raise UnreadableText(
            "it is not a text file - it decodes to binary data")
    return text


# --- Scanning for things that should not be submitted ------------------------
# The package carries every file as saved, tool output included, so this is
# all that stands between a credential and a submission. It never edits and
# never excludes: it names the file, and the student decides.

SECRET_PATTERNS = (
    ("an API key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}")),
    ("a GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}")),
    ("an AWS access key id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("a Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}")),
    ("a Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("a private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    # The likeliest shape here, the assignment being a database task.
    # Requires user:password@, so `sqlite:///ctgov.db` and ordinary https://
    # links do not fire.
    ("a database connection string with a password",
     re.compile(r"\b[a-z][a-z0-9+.-]{0,30}://[^\s/:@]+:[^\s/@]+@")),
    # Needs a token-shaped run after the word, so "the bearer of the risk"
    # stays prose.
    ("an authorisation token",
     re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/-]{20,}={0,2}")),
    # Three constraints, each load-bearing.
    #
    # The value needs a digit and 8+ characters. The digit clears every false
    # positive across the prose fixtures; a higher floor only loses real
    # secrets (password: a1b2c3d4e5).
    #
    # No leading \b, so AWS_SECRET_ACCESS_KEY= matches - '_' is a word
    # character, so there is no boundary before SECRET. The optional suffix
    # must begin with '_' or '-', which keeps 'tokenizer: gpt2-medium' prose;
    # this subject teaches an NLP chapter.
    #
    # Do not add a prefix group. It reaches nothing new, and an unanchored
    # repeated group rescans from every position: 11.9s per 880 KB against
    # 0.02s for the others. See
    # test_the_scan_is_linear_and_fast_on_a_large_file.
    ("a password or key written out in the text",
     re.compile(r"(?i)(?:api[_-]?key|secret|password|passwd|token)"
                r"(?:[_-][A-Za-z0-9_-]*)?"
                r"[\"'\]]*\s*[:=]\s*"
                r"[\"']?(?=[A-Za-z0-9_\-+/=.]*[0-9])"
                r"[A-Za-z0-9_\-+/=.]{8,}")),
)


def scan_secrets(text):
    """Names of the SECRET_PATTERNS this text matches, in declaration order.

    A floor, not a guarantee. It cannot catch an employer's client list pasted
    into a prompt, and the manifest says so rather than implying the file has
    been cleared.
    """
    return [name for name, pattern in SECRET_PATTERNS if pattern.search(text)]


# A whole-history export holds every conversation the student has ever had,
# plus their name and email in user.json. This detects; it must never grow
# into a reader. See tests/evidence/2026-09-14-web-export-defect.md.
EXPORT_MEMBERS = {"conversations.json", "user.json"}


def detect_bulk_export(path, text):
    """Name the vendor whose whole-history export this file is, or None."""
    if path.suffix.lower() != ".json":
        return None
    try:
        doc = json.loads(text)
    except (ValueError, RecursionError):
        return None
    if not isinstance(doc, list) or not doc:
        return None
    first = doc[0]
    if not isinstance(first, dict):
        return None
    if "mapping" in first and "current_node" in first:
        return "ChatGPT"
    if "chat_messages" in first:
        return "Claude.ai"
    return None


def zip_holds_export(path):
    """True if this .zip is a vendor export archive."""
    if path.suffix.lower() != ".zip":
        return False
    try:
        with zipfile.ZipFile(str(path)) as archive:
            names = set(Path(n).name for n in archive.namelist())
    except (zipfile.BadZipFile, OSError, ValueError):
        return False
    return bool(names & EXPORT_MEMBERS)


# --- Digests, and writing the package ----------------------------------------
# The package digest is built from sorted (path, file-digest) pairs, not from
# the zip's bytes, so it is reproducible despite the timestamps zip records.


def file_digest(path):
    """SHA-256 of a file's bytes, streamed so a large session file is fine."""
    digest = hashlib.sha256()
    with open(str(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def package_digest(entries):
    """One value identifying the whole package's contents.

    `entries` is a list of (relative_path, sha256), sorted so the result does
    not depend on walk order. The NUL and newline separators are required:
    without them ('ab', 'cc...') and ('a', 'bcc...') hash alike, and a
    rename goes unnoticed.
    """
    digest = hashlib.sha256()
    for rel, member in sorted(entries):
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(member.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def member_id_name(member_id):
    """The package filename, given the optional member ID argument."""
    if member_id is None:
        return PACKAGE_DEFAULT
    ident = member_id.strip()
    if not MEMBER_ID_RE.match(ident):
        die("'%s' does not look like a member ID. Use letters, digits, spaces, "
            "hyphens and underscores only - it becomes the name of the file "
            "you submit.\n"
            "Run it with no argument to get %s instead, and rename the file "
            "yourself." % (member_id, PACKAGE_DEFAULT))
    return PACKAGE_PATTERN % ident


def write_package(target, log_dir, files, manifest_text):
    """Write the package: the manifest, then every file, byte-for-byte.

    Nothing here decodes a member. A file this script could not read as text
    still goes in as saved: unreadable to the script is not grounds for
    leaving a conversation out of the record.

    `target` must not resolve inside `log_dir`, or the next run would find the
    package in ai_logs/ and pack it into itself.
    """
    try:
        Path(target).resolve().relative_to(Path(log_dir).resolve())
    except ValueError:
        pass                    # outside log_dir, which is what we require
    else:
        raise ValueError(
            "the package must not be written inside %s - it would be "
            "packaged into itself on the next run" % log_dir)
    with zipfile.ZipFile(str(target), "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("MANIFEST.md", manifest_text)
        for path in files:
            arcname = (Path(LOG_DIR_NAME) /
                       path.relative_to(log_dir)).as_posix()
            archive.write(str(path), arcname)


# --- Command-line agent sessions (.jsonl) ------------------------------------
# One yes/no question: does this file carry the tool's own output, so the
# student knows to skim it?
#
# Keep it a yes/no. A count means parsing records, and a count that comes out
# wrong reads as an all-clear in a section headed "check before you submit".
# Nothing here attributes text to anyone - see
# tests/fixtures/real/claude_code_mixed_authorship.README.md.

TOOL_OUTPUT_MARKERS = re.compile(
    r'"(?:tool_use|tool_result|toolUseResult|function_call'
    r'|function_call_output|server_tool_use)"'
    r'|<bash-(?:input|stdout|stderr)>'
    r'|<system-reminder>|<ide_selection>|<user-prompt-submit-hook>'
    r'|<local-command-stdout>')


def holds_tool_output(text):
    """True if this session file carries the tool's own output."""
    return bool(TOOL_OUTPUT_MARKERS.search(text))


# --- The manifest ------------------------------------------------------------
# One row per file, the checks worth acting on, then a digest per member. It
# describes the package and nothing else. Anything not established is a dash,
# and the table says so: a dash read as a zero is a conclusion about the
# student that the evidence does not support.


def parse_name(path: Path, display: str):
    """Return (when, qtag, topic, warning_or_None) from a filename.

    `display` is the path relative to `ai_logs/`, so a file in a subfolder is
    not confused with a same-named file at the top level.

    `when` is a datetime, midnight where no time was given so date-only names
    sort before same-day timed ones, or None if the name does not match.
    """
    m = NAME_RE.match(path.stem)
    if m:
        try:
            when = datetime.strptime(m.group("date"), "%Y-%m-%d")
            if m.group("time"):
                when = datetime.strptime(
                    f"{m.group('date')} {m.group('time')}", "%Y-%m-%d %H%M"
                )
        except ValueError:
            return None, "?", path.stem, (
                f"'{display}': date/time part is not valid "
                f"(expected YYYY-MM-DD, optionally _HHMM)."
            )
        topic = m.group("topic").replace("_", " ").replace("-", " ").strip()
        return when, m.group("qtag"), topic, None
    return (
        None,
        "?",
        path.stem.replace("_", " "),
        f"'{display}': doesn't match the naming pattern "
        f"YYYY-MM-DD_Qtag_topic (e.g. 2026-08-03_Q1_chatgpt_tfidf.md; "
        f"an optional time is allowed: 2026-08-03_1430_Q1_...). "
        f"Included anyway, listed last.",
    )


ROLE_ONLY = re.compile(r"^#{0,6}\s*\**(user|assistant|system)\**:?$",
                       re.IGNORECASE)


def preview(text, width=90):
    """First non-empty, non-heading line of the file, trimmed for the table.

    The text is quoted as found. Stripping markdown escapes here would also
    strip a backslash the student typed, and this line is theirs, not ours.
    """
    for line in text.splitlines():
        stripped = line.strip()
        if ROLE_ONLY.match(stripped):
            continue                    # a role label in a converted session
        s = stripped.lstrip("#>*- ").strip()
        if s:
            return (s[: width - 1] + "\u2026") if len(s) > width else s
    return "(empty file)"


def _human_size(count):
    # Rounded on purpose: the row only needs to show that a file is 4 KB
    # rather than 0. Exact bytes belong with the digests.
    if count < 1024:
        return "under 1 KB"
    if count < 1024 * 1024:
        return "%.0f KB" % (count / 1024.0)
    return "%.1f MB" % (count / (1024.0 * 1024.0))


SCRIPT_VERSION = "4.0.0"

BULK_NOTE = ("this looks like a full %s export. It contains EVERY "
             "conversation you have ever had, not just the ones about this "
             "assignment, and the archive it came in also carries a "
             "user.json holding your name and email address. Open it and "
             "check, or save the individual conversations you want to submit "
             "as .md files instead.")


class Entry(object):
    """One file in the package, as the manifest describes it."""

    def __init__(self, rel, size, digest):
        self.rel = rel                  # path inside the package
        self.size = size
        self.digest = digest
        self.when = None                # datetime from the filename, or None
        self.qtag = "?"
        self.first_line = ""            # from preview(); every readable file
        self.unreadable = ""            # why it could not be read as text
        self.secrets = []               # scan_secrets() names
        self.bulk = None                # vendor name, or None
        self.machine = False            # carries the tool's own output
        self.textish = False


def _cell(value):
    """A table cell that never breaks the table and never invents content."""
    if value is None or value == "":
        return "\u2014"
    return str(value).replace("|", "\\|").replace("\n", " ")


def build_manifest(entries, skipped, pruned, package_name):
    """The MANIFEST.md text."""
    total = sum(e.size for e in entries)
    out = []
    out.append("# AI conversation log package")
    out.append("")
    out.append("*Generated by `compile_ai_logs.py` v%s on %s.*"
               % (SCRIPT_VERSION, datetime.now().strftime("%Y-%m-%d %H:%M")))
    out.append("")
    out.append("- **Package:** `%s`" % package_name)
    out.append("- **Files:** %d, %s in total" % (len(entries), _human_size(total)))
    out.append("")
    out.append("Every file the student saved in `ai_logs/` is here byte for "
               "byte. Nothing has been merged, shortened or rewritten.")
    out.append("")
    out.append("Only system files are left out, and each one is named below "
               "as not included. Everything else named below is in the "
               "package; it is listed because it is worth a look, not because "
               "it is missing.")
    out.append("")

    out.append("## Files")
    out.append("")
    out.append("| File | Date | Q | Size | First line |")
    out.append("|---|---|---|---:|---|")
    for e in sorted(entries, key=lambda x: (x.when is None, x.when, x.rel)):
        out.append("| `%s` | %s | %s | %s | %s |" % (
            e.rel,
            _cell(e.when.strftime("%Y-%m-%d") if e.when else None),
            _cell(e.qtag if e.qtag != "?" else None),
            _human_size(e.size),
            _cell(e.first_line),
        ))
    out.append("")
    out.append("*A dash means \"not established\", never \"none\". \"First "
               "line\" is the opening line of a file that could be read as "
               "text, quoted as found; it says nothing about who wrote it. "
               "Nothing in this table describes how the student worked - a "
               "saved conversation does not reliably show that, so it is not "
               "claimed here.*")
    out.append("")

    out.append("## Check before you submit")
    out.append("")
    out.append("This package was written from the files as they stood. "
               "Changing one of them afterwards does not change what is in "
               "here: fix it in `%s` and run this again."
               % LOG_DIR_NAME)
    out.append("")
    notes = []
    for e in entries:
        if e.bulk:
            notes.append("- **`%s`** \u2014 %s" % (e.rel, BULK_NOTE % e.bulk))
    for e in entries:
        if e.secrets:
            notes.append("- **`%s`** \u2014 contains %s. Open it and check."
                         % (e.rel, ", ".join(e.secrets)))
    for e in entries:
        if e.machine:
            notes.append("- `%s` \u2014 holds tool output: shell commands and "
                         "their results, files the agent read, context the "
                         "harness inserted. All of it is submitted as saved, "
                         "so read it before you send it." % e.rel)
    for e in entries:
        if e.unreadable and e.textish:
            notes.append("- `%s` \u2014 could not be read as text (%s). It is in "
                         "the package byte for byte anyway, but if you meant "
                         "it to be readable, save it again as .md or .txt."
                         % (e.rel, e.unreadable))
    for e in entries:
        if e.when is None:
            notes.append("- `%s` \u2014 the name does not follow "
                         "YYYY-MM-DD_Qtag_topic, so it has no date or question "
                         "in the table above. It is in the package anyway."
                         % e.rel)
    for rel, reason in skipped:
        notes.append("- `%s/%s` \u2014 %s" % (LOG_DIR_NAME, rel, reason))
    for rel, count in pruned:
        notes.append("- `%s/%s/` \u2014 a system folder, so its %d file(s) are not "
                     "in the package." % (LOG_DIR_NAME, rel, count))
    if notes:
        out.extend(notes)
    else:
        # An all-clear must not cover files that were never decoded, and so
        # never scanned. Unreadable text-shaped files are already in `notes`;
        # what reaches here is the expected binary, named with the limit of
        # the check stated.
        unread = [e for e in entries if e.unreadable]
        if unread:
            out.append("Nothing to check in the files that could be read. "
                       "%d file(s) are not text - %s - so they are in the "
                       "package exactly as saved but were never scanned. "
                       "Check those yourself."
                       % (len(unread),
                          ", ".join("`%s`" % e.rel for e in unread)))
        else:
            out.append("Nothing to check. Every file was read, none carries a "
                       "key-shaped string, and all names follow the pattern.")
    out.append("")
    out.append("*This check is a floor, not a guarantee. It looks for "
               "key-shaped text and for whole-history exports. It cannot tell "
               "that a conversation contains an employer's confidential "
               "information \u2014 only the student can.*")
    out.append("")

    out.append("## Integrity")
    out.append("")
    out.append("SHA-256 of every file in this package. Recompute them to "
               "confirm the contents: a file edited after packaging will not "
               "match.")
    out.append("")
    out.append("```")
    for e in sorted(entries, key=lambda x: x.rel):
        out.append("%s  %s" % (e.digest, e.rel))
    out.append("")
    out.append("Package digest: %s"
               % package_digest([(e.rel, e.digest) for e in entries]))
    out.append("```")
    out.append("")
    return "\n".join(out)


# --- Finding what the student saved ------------------------------------------
# Subfolders are expected. Everything found is either packaged or reported by
# name: a folder skipped in silence costs the student the hurdle.

# `__MACOSX` is in the list because Finder writes it into every zip it makes,
# and its resource-fork stubs carry the same names as the real logs.
PRUNE_DIRS = {".git", "__pycache__", ".ipynb_checkpoints", "node_modules",
              ".venv", "venv", ".idea", ".vscode", "__MACOSX"}


def discover(log_dir):
    """Walk log_dir recursively.

    Returns (files, skipped, pruned):
      files   - sorted Paths to go into the package
      skipped - (name, reason) for each file left out, so the manifest can
                name it; a file dropped in silence costs the student the
                hurdle
      pruned  - (directory, file_count) for each system folder not descended
    """
    files, skipped, pruned = [], [], []

    def note_walk_error(err):
        # os.walk's default onerror=None discards the error and stops
        # descending silently, so an unopenable path would leave no trace in
        # either the skipped or the pruned list.
        target = getattr(err, "filename", None) or str(log_dir)
        try:
            shown = Path(target).relative_to(log_dir).as_posix()
        except ValueError:
            shown = str(target)
        why = getattr(err, "strerror", None) or err
        skipped.append((shown, WALK_REASON % why))

    for dirpath, dirnames, filenames in os.walk(str(log_dir),
                                                onerror=note_walk_error):
        here = Path(dirpath)
        keep = []
        for d in sorted(dirnames):
            if d in PRUNE_DIRS or d.startswith("."):
                count = sum(len(fs) for _, _, fs in os.walk(str(here / d)))
                pruned.append(((here / d).relative_to(log_dir).as_posix(), count))
            else:
                keep.append(d)
        dirnames[:] = keep
        for name in sorted(filenames):
            path = here / name
            rel = path.relative_to(log_dir).as_posix()
            if name.startswith("."):
                skipped.append((rel, DOT_REASON))
                continue
            # No extension filter: the package carries everything the
            # student saved, so the only exclusions are the artefacts above.
            files.append(path)
    files.sort(key=lambda p: str(p).lower())
    return files, skipped, pruned


# --- Running it --------------------------------------------------------------
# An incomplete package fails the hurdle however well the student worked, so
# every run reports what it found, what it left out, and what it cannot vouch
# for. It refuses to write an empty package.


UNEXPECTED_MESSAGE = (
    "Something went wrong that this script did not expect, and it has "
    "stopped.\nThe lines above are for whoever helps you fix it - send them "
    "with your question.\n"
    "\nNothing in ai_logs/ has been changed or deleted: this script only ever "
    "writes\none file, the zip package (%s by default), and that is what may "
    "be missing or half-written." % PACKAGE_DEFAULT)


def run() -> None:
    """main(), plus a plain-English account of any failure it did not expect."""
    _safe_streams()
    try:
        main()
    except KeyboardInterrupt:
        die("Stopped before finishing.")
    except Exception:
        try:
            traceback.print_exc()
        except Exception:
            pass
        die(UNEXPECTED_MESSAGE)


USAGE = ("Usage:  python compile_ai_logs.py <your member ID>\n"
         "        python compile_ai_logs.py \"12 34 56\"   (quote an ID "
         "containing spaces)\n"
         "        python compile_ai_logs.py               (writes %s, "
         "for you to rename)\n"
         "\nRun it from your submission folder - the one that contains "
         "'%s'. No Python? Use Run_AI_Log_Packager.ipynb in Google Colab."
         % (PACKAGE_DEFAULT, LOG_DIR_NAME))


def member_id_from_argv(argv):
    """The member ID from the command line, or None. Refuses anything else.

    A member ID may contain spaces, so an unquoted one arrives as several
    arguments. Taking the first and ignoring the rest produced a package named
    for one word of it, written without complaint, when the brief requires the
    exact name.
    """
    args = argv[1:]
    if not args:
        return None
    if args[0].startswith("-") or args[0] == "/?":
        say(USAGE)
        sys.exit(0)
    if len(args) > 1:
        die("Too many arguments: %s\n"
            "A member ID containing spaces has to be quoted, or the shell "
            "splits it up and only the first word is used:\n"
            "    python compile_ai_logs.py \"%s\"\n\n%s"
            % (" ".join(repr(a) for a in args), " ".join(args), USAGE))
    return args[0]


def main() -> None:
    _safe_streams()
    member_id = member_id_from_argv(sys.argv)
    package_name = member_id_name(member_id)
    log_dir = find_log_dir()
    target = log_dir.parent / package_name

    files, skipped, pruned = discover(log_dir)
    if not files:
        # A student looking at a folder with files in it will not act on
        # "there are no conversations here". Say what was found and why it did
        # not count, covering both skipped files and pruned folders.
        found = ""
        if skipped or pruned:
            lines = ["  %s/%s - %s" % (LOG_DIR_NAME, rel, reason)
                     for rel, reason in skipped]
            lines += ["  %s/%s/ - a system folder, so its %d file(s) were not "
                      "looked at." % (LOG_DIR_NAME, rel, count)
                      for rel, count in pruned]
            found = ("\nWhat is in there was not counted:\n"
                     + "\n".join(lines) + "\n")
        die("There are no conversations in '%s' to package.%s\n"
            "Save each AI conversation as a .md or .txt file in that folder, "
            "then run this again.\n"
            "Nothing has been read, written or changed."
            % (log_dir, found))

    entries = []
    for path in files:
        rel = (Path(LOG_DIR_NAME) / path.relative_to(log_dir)).as_posix()
        # Both calls open the file, and both raise on one the student cannot
        # read right now: open elsewhere, locked by a sync client, or an
        # undownloaded cloud placeholder. Skipping it is not an option - a
        # dropped conversation is one the marker never sees - so stop, name
        # the file, and say what to do about it.
        try:
            entry = Entry(rel, path.stat().st_size, file_digest(path))
        except OSError as exc:
            die("Could not read '%s' (%s).\n"
                "If it is open in another program, close it. If it lives in "
                "OneDrive, Dropbox or Google Drive, make it available offline "
                "so the file is really on this machine, then run this again.\n"
                "Nothing has been written, and nothing in '%s' has been "
                "changed." % (rel, exc.strerror or exc, log_dir))
        entry.when, entry.qtag, _topic, _warn = parse_name(
            path, str(path.relative_to(log_dir)))
        entry.textish = path.suffix.lower() in TEXTISH
        if zip_holds_export(path):
            entry.bulk = "ChatGPT or Claude.ai"
        try:
            text = read_text(path)
        except (UnreadableText, OSError) as exc:
            entry.unreadable = str(exc)
            entries.append(entry)
            continue
        # A JSON or JSONL file's first line is syntax, not conversation, so
        # quoting it as an opening line would tell the reader nothing.
        if path.suffix.lower() not in (".json", ".jsonl"):
            entry.first_line = preview(text)
        entry.secrets = scan_secrets(text)
        entry.bulk = entry.bulk or detect_bulk_export(path, text)
        # Gated on .jsonl: a Claude Code `/export` writes .md, which has no
        # session records to find.
        if path.suffix.lower() == ".jsonl":
            entry.machine = holds_tool_output(text)
        entries.append(entry)

    manifest = build_manifest(entries, skipped, pruned, package_name)
    try:
        write_package(target, log_dir, files, manifest)
    except OSError as exc:
        die("Could not write '%s' (%s).\n"
            "If it is open in another program, close it and run this again.\n"
            "Nothing in '%s' has been changed." % (target, exc, log_dir))

    say("Packaged %d file(s) from %s" % (len(files), log_dir))
    say("  -> %s" % target.name)
    say()

    flagged = [e for e in entries
               if e.bulk or e.secrets or (e.unreadable and e.textish) or e.machine]
    if flagged:
        say("Check these before you submit:")
        for e in flagged:
            if e.bulk:
                say("  %s - a full %s export: it holds EVERY conversation you "
                    "have ever had, and your name and email." % (e.rel, e.bulk))
            if e.secrets:
                say("  %s - contains %s." % (e.rel, ", ".join(e.secrets)))
            if e.machine:
                # The package carries these records, so name the file
                # holding them.
                say("  %s - holds tool output: shell commands and their "
                    "results, files the agent read. Skim it." % e.rel)
            if e.unreadable and e.textish:
                say("  %s - could not be read as text; packaged anyway."
                    % e.rel)
        say()

    size = target.stat().st_size
    if size > SIZE_WARN:
        biggest = sorted(entries, key=lambda e: e.size, reverse=True)[:5]
        say("This package is %s, which is larger than expected. The biggest "
            "files are:" % _human_size(size))
        for e in biggest:
            say("  %s (%s)" % (e.rel, _human_size(e.size)))
        say()

    if member_id is None:
        say("The assignment brief asks you to name your files "
            "'DSA 2026 S2 Assignment <member ID>'. Either rename %s yourself, "
            "or run: python compile_ai_logs.py <your member ID>"
            % package_name)
        say()

    say("Read MANIFEST.md inside the package before you submit it. "
        "Skim your logs for API keys or confidential work data.")
    # The package was written before any of the advice above was printed, so
    # a student who acts on it has a package that no longer matches ai_logs/.
    # Acting on the warning and submitting anyway is the failure this last
    # line exists to prevent, so it is the last thing they read.
    say()
    say("%s has already been written from the files as they are now. "
        "If you change anything in %s, run this again so the package "
        "matches." % (target.name, LOG_DIR_NAME))


if __name__ == "__main__":
    run()
