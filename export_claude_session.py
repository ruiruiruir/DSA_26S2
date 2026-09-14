"""Convert a local Claude Code session (.jsonl) into a readable markdown log for ai_logs/.

The AI-use guidance asks for logs "as exported", with nothing tidied or deleted,
and says tool output and internal reasoning may be left out. This does exactly
that and nothing more:

  * every prompt you typed, and every reply, is copied verbatim;
  * each tool call is listed by name, but its output is not included;
  * the model's internal reasoning ("thinking") is not included;
  * background-task notifications and automatic app messages are shown as
    quoted markers, so the replies to them still read in context;
  * app-injected context (system reminders, session metadata, the system
    prompt) is dropped. Among other things, that metadata contains your email.

Usage:
    python export_claude_session.py <session-id-or-path> --tag Q1 --topic claudecode_validate_dataset

Sessions live in ~/.claude/projects/<project>/<session-id>.jsonl and are
deleted after 30 days by default, so export them as you go.
"""
import argparse, glob, json, os, re, sys
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Australia/Sydney")
PROJECT_DIR = os.path.expanduser("~/.claude/projects/C--Users-Nebula-PC-code-DSA-26S2")

RE_SYSREM = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)
RE_NOTIF = re.compile(r"<task-notification>.*?</task-notification>", re.S)


def local(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(TZ)


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n\n".join(b.get("text", "") for b in content
                           if isinstance(b, dict) and b.get("type") == "text")
    return ""


def tool_label(block):
    name, inp = block.get("name", "tool"), block.get("input") or {}
    if name in ("Bash", "PowerShell", "Monitor") and inp.get("description"):
        detail = inp["description"]
    elif inp.get("file_path"):
        detail = os.path.basename(str(inp["file_path"]))
    else:
        detail = next((str(inp[k]) for k in ("skill", "query", "task_id", "action", "url",
                                             "pattern", "description") if inp.get(k)), "")
    label = "%s: %s" % (name, detail) if detail else name
    return label.replace("`", "'").replace("\n", " ")[:160]


def notification_line(raw, when):
    ids = re.findall(r"<task-id>(.*?)</task-id>", raw)
    ids = [i for i in ids if not i.startswith("__")]
    status = re.search(r"<status>(.*?)</status>", raw, re.S)
    summary = re.search(r"<summary>(.*?)</summary>", raw, re.S)
    body = summary.group(1).strip() if summary else "task update"
    tail = " [%s]" % status.group(1).strip() if status else ""
    return ("> **Background task notification** _%s_ (%s) — %s%s"
            % (when.strftime("%H:%M"), ", ".join(ids) or "?", " ".join(body.split()), tail))


def convert(path):
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]

    def human_text(r):
        return RE_SYSREM.sub("", text_of((r.get("message") or {}).get("content"))).strip()

    typed = {human_text(r) for r in rows if r.get("type") == "user"
             and (r.get("origin") or {}).get("kind") == "human"}
    # Mid-turn messages are delivered as queued_command attachments; a queue
    # 'remove' is the fallback record if no attachment carried the same text.
    midturn_attached = {(r.get("attachment") or {}).get("prompt", "").strip()
                        for r in rows if (r.get("attachment") or {}).get("type") == "queued_command"
                        and "<task-notification>" not in (r.get("attachment") or {}).get("prompt", "")}

    out, state = [], {"section": None, "day": None, "msg": None, "open_tools": False}
    seen_notifs, seen_midturn = set(), set()

    def close_tools():
        if state["open_tools"]:
            out.append("\n</details>\n")
            state["open_tools"], state["msg"] = False, None

    def day_break(when):
        d = when.date()
        if d != state["day"]:
            close_tools()
            out.append("\n---\n\n### %s\n" % when.strftime("%A %d %B %Y").replace(" 0", " "))
            state["day"] = d

    def header(who, when, note=""):
        day_break(when)
        close_tools()
        out.append("\n## %s  _%s_%s\n" % (who, when.strftime("%H:%M"), note))
        state["section"] = who

    def marker(line, when):
        day_break(when)
        close_tools()
        out.append("\n" + line + "\n")
        state["section"] = "marker"

    for r in rows:
        kind, ts = r.get("type"), r.get("timestamp")
        when = local(ts) if ts else None

        if kind == "user":
            content = (r.get("message") or {}).get("content")
            if isinstance(content, list) and any(b.get("type") == "tool_result" for b in content
                                                 if isinstance(b, dict)):
                continue                                   # tool output: omitted
            origin = (r.get("origin") or {}).get("kind")
            raw = text_of(content)
            if origin == "task-notification" or "<task-notification>" in raw:
                for n in RE_NOTIF.findall(raw):
                    key = tuple(re.findall(r"<task-id>(.*?)</task-id>", n))
                    if key not in seen_notifs:
                        seen_notifs.add(key)
                        marker(notification_line(n, when), when)
                continue
            text = RE_SYSREM.sub("", raw).strip()
            if not text:
                continue
            if r.get("isMeta"):
                if text.startswith("Base directory for this skill"):
                    continue                               # skill instructions: listed as a tool call
                marker('> **Automatic message from the app** _%s_ — "%s"'
                       % (when.strftime("%H:%M"), " ".join(text.split())[:300]), when)
                continue
            header("You", when)
            out.append("\n" + text + "\n")

        elif kind == "attachment":
            a = r.get("attachment") or {}
            if a.get("type") != "queued_command":
                continue                                   # app context: dropped
            prompt = a.get("prompt", "")
            if "<task-notification>" in prompt:
                for n in RE_NOTIF.findall(prompt):
                    key = tuple(re.findall(r"<task-id>(.*?)</task-id>", n))
                    if key not in seen_notifs:
                        seen_notifs.add(key)
                        marker(notification_line(n, when), when)
            else:
                t = RE_SYSREM.sub("", prompt).strip()
                if t and t not in typed and t not in seen_midturn:
                    seen_midturn.add(t)
                    header("You", when, "  (sent while Claude was working)")
                    out.append("\n" + t + "\n")

        elif kind == "queue-operation" and r.get("operation") == "remove":
            t = (r.get("content") or "").strip()
            if (t and "<task-notification>" not in t and t not in typed
                    and t not in midturn_attached and t not in seen_midturn):
                seen_midturn.add(t)
                header("You", when, "  (sent while Claude was working)")
                out.append("\n" + t + "\n")

        elif kind == "assistant":
            msg = r.get("message") or {}
            for b in msg.get("content") or []:
                bt = b.get("type")
                if bt == "text" and b.get("text", "").strip():
                    if state["section"] != "Claude":
                        header("Claude", when)
                    close_tools()
                    out.append("\n" + b["text"].strip() + "\n")
                elif bt == "tool_use":
                    if state["section"] != "Claude":
                        header("Claude", when)
                    if not state["open_tools"] or state["msg"] != msg.get("id"):
                        close_tools()
                        out.append("\n<details><summary>tools run</summary>\n")
                        state["open_tools"], state["msg"] = True, msg.get("id")
                    out.append("\n- `%s`" % tool_label(b))
                # 'thinking' blocks: internal reasoning, omitted
    close_tools()

    stamps = [local(r["timestamp"]) for r in rows if r.get("timestamp")]
    titles = [r.get("customTitle") for r in rows if r.get("type") == "custom-title" and r.get("customTitle")]
    sid = os.path.splitext(os.path.basename(path))[0]
    head = [
        "# Claude Code session transcript\n",
        "*Session:* %s — Claude Code desktop app (Code tab), model Opus 5  " % (titles[-1] if titles else sid),
        "*Session ID:* `%s`  " % sid,
        "*Span:* %s to %s (Sydney time)  " % (min(stamps).strftime("%d %B %Y %H:%M"),
                                             max(stamps).strftime("%d %B %Y %H:%M")),
        "*Converted* on %s from the local session record by `export_claude_session.py`. Every prompt "
        "and every reply is included verbatim and unedited. As the AI-use guidance anticipates, tool "
        "output and the model's internal reasoning are omitted, and each tool call is listed by name. "
        "Background-task notifications and automatic app messages are shown as quoted markers so the "
        "replies to them read in context.*\n" % datetime.now(TZ).strftime("%d %B %Y"),
    ]
    return "\n".join(head) + "".join(out).rstrip() + "\n", min(stamps)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("session", help="session id, or path to a .jsonl")
    ap.add_argument("--tag", required=True, help="Q1-Q4, multiQ or general")
    ap.add_argument("--topic", required=True, help="a couple of words, underscore-separated")
    ap.add_argument("--outdir", default="ai_logs")
    args = ap.parse_args()

    path = args.session if args.session.endswith(".jsonl") else \
        next(iter(glob.glob(os.path.join(PROJECT_DIR, args.session + "*.jsonl"))), None)
    if not path or not os.path.isfile(path):
        sys.exit("session not found: %s" % args.session)

    md, start = convert(path)
    os.makedirs(args.outdir, exist_ok=True)
    out = os.path.join(args.outdir, "%s_%s_%s.md" % (start.strftime("%Y-%m-%d_%H%M"), args.tag, args.topic))
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    print("wrote %s (%d KB)" % (out, os.path.getsize(out) // 1024))


if __name__ == "__main__":
    main()
