#!/usr/bin/env python3
"""Generate a self-contained HTML replay of Claude Code sessions for a project.

Reads the project's JSONL session logs from ~/.claude/projects/<slug>/ and emits
a single HTML file with an embedded, synthetic-paced replay player.

Usage:
    generate_replay.py [--project-dir DIR] [--out FILE] [--title TITLE]
                       [--main-session SESSION_ID]

With no arguments, the log directory is derived from the current working
directory (the same slug rule Claude Code uses: every non-alphanumeric
character of the absolute path becomes "-").
"""
import argparse
import json
import glob
import os
import re
from datetime import datetime

TRUNC = 1800  # max chars of any single content block we embed


def project_slug(path):
    """Claude Code's project-dir slug: non-alphanumeric chars become '-'."""
    return re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(path))


def trunc(s, n=TRUNC):
    if s is None:
        return ""
    s = str(s)
    if len(s) > n:
        return s[:n] + "\n…(truncated, %d more chars)" % (len(s) - n)
    return s


def base(path):
    if not path:
        return ""
    return path.replace("\\", "/").rstrip("/").split("/")[-1]


def tool_summary(name, inp):
    """Return (short_label, detail_string) for a tool_use block."""
    inp = inp or {}
    if name == "Read":
        return "Read", base(inp.get("file_path", ""))
    if name == "Write":
        return "Write", base(inp.get("file_path", ""))
    if name == "Edit":
        return "Edit", base(inp.get("file_path", ""))
    if name == "Bash":
        d = inp.get("description") or inp.get("command") or ""
        return "Bash", trunc(d, 200)
    if name in ("Grep",):
        return "Grep", inp.get("pattern", "")
    if name in ("Glob",):
        return "Glob", inp.get("pattern", "")
    if name == "Skill":
        return "Skill", inp.get("command") or inp.get("skill") or ""
    if name in ("Agent", "Task"):
        return "Agent", inp.get("description") or inp.get("subagent_type") or ""
    if name == "TaskCreate":
        return "TaskCreate", trunc(json.dumps(inp.get("tasks", inp)), 200)
    if name == "TaskUpdate":
        return "TaskUpdate", trunc(json.dumps(inp), 160)
    if name in ("ExitPlanMode", "EnterPlanMode"):
        return name, ""
    if name == "AskUserQuestion":
        qs = inp.get("questions", [])
        q = qs[0].get("question") if qs and isinstance(qs[0], dict) else ""
        return "AskUserQuestion", trunc(q, 200)
    if name == "ToolSearch":
        return "ToolSearch", trunc(inp.get("query", ""), 160)
    if name.startswith("mcp__"):
        short = name.split("__")[-1]
        return "mcp:" + short, trunc(json.dumps(inp), 200)
    return name, trunc(json.dumps(inp), 200)


def tool_full(inp):
    """Pretty-printed full tool input for the click-to-expand detail view.

    The compact `tool_summary` line drops the real command / full paths / edit
    contents; this keeps them (capped) so the expand link can show what actually
    ran."""
    if not inp:
        return ""
    try:
        s = json.dumps(inp, indent=2, ensure_ascii=False)
    except Exception:
        s = str(inp)
    return trunc(s, 3000)


def parse_command(s):
    """If a user message is a slash command, return '/name args' text, else None."""
    if "<command-name>" not in s:
        return None
    name_m = re.search(r"<command-name>(.*?)</command-name>", s, re.S)
    args_m = re.search(r"<command-args>(.*?)</command-args>", s, re.S)
    name = (name_m.group(1).strip() if name_m else "").strip()
    args = (args_m.group(1).strip() if args_m else "")
    if not name:
        return None
    return name + (" " + args if args else "")


# Slash commands that are built-in Claude Code controls, not skills. Used to
# keep the skills view honest: a user-invoked skill arrives as a slash command,
# but so do these, and they should not be counted as skills.
BUILTIN_COMMANDS = {
    "model", "clear", "compact", "config", "cost", "doctor", "help", "init",
    "login", "logout", "mcp", "memory", "permissions", "pr-comments",
    "release-notes", "resume", "review", "status", "bug", "vim", "fast",
    "terminal-setup", "add-dir", "agents", "hooks", "exit", "quit", "context",
    "export", "ide", "allowed-tools", "install-github-app", "privacy-settings",
    "upgrade", "theme", "editor",
}


def skill_from_command(cmd):
    """Return the skill name for a user slash command, or None for builtins."""
    t = (cmd or "").strip()
    if not t:
        return None
    name = t.lstrip("/").split()[0] if t.lstrip("/") else ""
    if not name:
        return None
    base_name = name.split(":")[-1]  # plugin-namespaced skills: 'plugin:skill'
    if name in BUILTIN_COMMANDS or base_name in BUILTIN_COMMANDS:
        return None
    return name


def skill_name(inp):
    """Skill name from a Skill tool_use input block."""
    inp = inp or {}
    return inp.get("skill") or inp.get("command") or "?"


def tally_skill(skills, name, source):
    """Accumulate a skill invocation into the per-session skills map."""
    s = skills.setdefault(name, {"name": name, "count": 0, "user": 0, "model": 0})
    s["count"] += 1
    s[source] += 1


def agent_output_text(content):
    """Pull the final text out of a sub-agent result's content list."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for b in content:
            if isinstance(b, dict):
                if b.get("text"):
                    parts.append(b["text"])
            elif isinstance(b, str):
                parts.append(b)
        return "\n".join(parts)
    return ""


def format_patch(sp):
    """Render a toolUseResult.structuredPatch (list of hunks) as unified diff text."""
    if not isinstance(sp, list):
        return ""
    out = []
    for h in sp:
        if not isinstance(h, dict):
            continue
        out.append("@@ -%s,%s +%s,%s @@" % (
            h.get("oldStart", "?"), h.get("oldLines", "?"),
            h.get("newStart", "?"), h.get("newLines", "?")))
        for ln in (h.get("lines") or []):
            out.append(ln)
    return trunc("\n".join(out), 2600)


def ts_ms(ts):
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp() * 1000
    except Exception:
        return None


def is_real_prompt(text):
    t = (text or "").strip()
    if not t:
        return False
    low = t[:60].lower()
    if t.startswith("<command") or t.startswith("<local-command"):
        return False
    if "command-name" in low or "command-message" in low:
        return False
    if "caveat" in low and "messages below" in t.lower():
        return False
    if t == "[Request interrupted by user]":
        return False
    return True


def extract_session(path):
    sid = base(path)[:-6]  # strip .jsonl
    rows = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue

    # ---- pass 1: back-link maps (results & hooks key off tool_use_id) ----
    tur_by_id = {}    # tool_use_id -> toolUseResult (1:1; verified no multi-result records)
    hooks_by_id = {}  # toolUseID  -> [hook, ...]
    for o in rows:
        m = o.get("message")
        if isinstance(m, dict) and o.get("type") == "user":
            c = m.get("content")
            if isinstance(c, list):
                tid = None
                for b in c:
                    if isinstance(b, dict) and b.get("type") == "tool_result":
                        tid = b.get("tool_use_id")
                tur = o.get("toolUseResult")
                if tid and isinstance(tur, dict):
                    tur_by_id[tid] = tur
        if o.get("type") == "attachment":
            att = o.get("attachment", {})
            if att.get("type") == "hook_success":
                tid = att.get("toolUseID")
                if tid:
                    hooks_by_id.setdefault(tid, []).append({
                        "name": att.get("hookName", ""),
                        "event": att.get("hookEvent", ""),
                        "exit": att.get("exitCode"),
                        "ms": att.get("durationMs"),
                        "out": trunc((att.get("stdout") or "").strip(), 300),
                        "err": trunc((att.get("stderr") or "").strip(), 300),
                    })

    # ---- pass 2: events + accounting ----
    events = []
    custom_title = None
    first_ts = last_ts = None
    n_prompts = n_tools = n_sub = 0
    goal_added = False
    seen_msg_ids = set()  # usage repeats on every line of one API turn
    tokens_out = 0
    peak_ctx = 0
    skills = {}        # name -> {name, count, user, model}
    tool_ev_by_id = {}  # tool_use_id -> tool event (to fold its result in)
    models = {}        # model id -> turn count
    attr_skills = {}   # attributionSkill -> turn count (active-skill context)
    perm_modes = set()
    server_tools = {}  # web_search_requests etc. (absent in this project's data)
    # tokens/model/skill claimed but not yet pinned to a visible event (a turn
    # often opens with an empty thinking line that renders nothing)
    pending_tok = pending_ctx = pending_model = pending_attr = None

    for o in rows:
        t = o.get("type")

        if t == "custom-title":
            custom_title = o.get("customTitle")
            continue
        if t == "permission-mode":
            pm = o.get("permissionMode")
            if pm:
                perm_modes.add(pm)
            continue

        ts = o.get("timestamp")
        if ts:
            if not first_ts:
                first_ts = ts
            last_ts = ts

        if t == "attachment":
            att = o.get("attachment", {})
            atype = att.get("type")
            if atype == "goal_status" and not goal_added and att.get("condition"):
                events.append({"role": "goal", "ts": ts,
                               "text": att["condition"]})  # full, never truncated
                goal_added = True
            elif atype == "plan_mode":
                events.append({"role": "plan", "ts": ts, "text": "Entered plan mode"})
            elif atype == "plan_mode_exit":
                events.append({"role": "plan", "ts": ts, "text": "Exited plan mode"})
            continue

        if o.get("isSidechain"):
            continue  # keep sub-agent chatter out of the main timeline

        if t == "user" and not o.get("isMeta"):
            c = o.get("message", {}).get("content")
            if isinstance(c, str):
                if c.strip() == "[Request interrupted by user]":
                    events.append({"role": "interrupt", "ts": ts,
                                   "text": "Request interrupted by user"})
                else:
                    cmd = parse_command(c)
                    if cmd:
                        ev = {"role": "command", "ts": ts,
                              "text": cmd if len(cmd) <= 2000 else cmd[:2000] + "…"}
                        sk = skill_from_command(cmd)
                        if sk:
                            ev["skill"] = sk
                            ev["skillSource"] = "user"
                            tally_skill(skills, sk, "user")
                        events.append(ev)
                        n_prompts += 1
                    elif is_real_prompt(c):
                        events.append({"role": "user", "ts": ts, "text": c})  # full
                        n_prompts += 1
            elif isinstance(c, list):
                for b in c:
                    if not isinstance(b, dict):
                        continue
                    if b.get("type") == "text" and \
                            (b.get("text") or "").strip() == "[Request interrupted by user]":
                        events.append({"role": "interrupt", "ts": ts,
                                       "text": "Request interrupted by user"})
                    elif b.get("type") == "text" and is_real_prompt(b.get("text")):
                        events.append({"role": "user", "ts": ts,
                                       "text": b["text"]})  # full
                        n_prompts += 1
                    elif b.get("type") == "tool_result":
                        rc = b.get("content")
                        if isinstance(rc, list):
                            rc = "\n".join(x.get("text", "") for x in rc
                                           if isinstance(x, dict))
                        is_err = bool(b.get("is_error"))
                        te = tool_ev_by_id.get(b.get("tool_use_id"))
                        if te is not None:
                            # fold the result into its tool call's accordion
                            te["result"] = trunc(rc, 900)
                            if is_err:
                                te["resultError"] = True
                        else:
                            events.append({"role": "result", "ts": ts,
                                           "text": trunc(rc, 700), "error": is_err})

        elif t == "assistant":
            msg = o.get("message", {})
            c = msg.get("content")
            if not isinstance(c, list):
                continue
            # claim this API turn's token usage once (lines share message id)
            usage = msg.get("usage") or {}
            mid = msg.get("id")
            mdl = msg.get("model")
            ask = o.get("attributionSkill")
            # count models/attribution once per API turn (lines share message id)
            if usage and mid and mid not in seen_msg_ids:
                seen_msg_ids.add(mid)
                tok = usage.get("output_tokens") or 0
                ctx = ((usage.get("input_tokens") or 0)
                       + (usage.get("cache_read_input_tokens") or 0)
                       + (usage.get("cache_creation_input_tokens") or 0))
                tokens_out += tok
                peak_ctx = max(peak_ctx, ctx)
                pending_tok = tok + (pending_tok or 0)
                pending_ctx = ctx
                if mdl:
                    models[mdl] = models.get(mdl, 0) + 1
                if ask:
                    attr_skills[ask] = attr_skills.get(ask, 0) + 1
                stu = usage.get("server_tool_use")
                if isinstance(stu, dict):
                    for k, v in stu.items():
                        if isinstance(v, int) and v > 0:
                            server_tools[k] = server_tools.get(k, 0) + v
            if mdl:
                pending_model = mdl
            if ask:
                pending_attr = ask
            first_event_of_line = len(events)
            for b in c:
                if not isinstance(b, dict):
                    continue
                bt = b.get("type")
                if bt == "thinking":
                    th = b.get("thinking", "")
                    if th.strip():
                        events.append({"role": "thinking", "ts": ts,
                                       "text": trunc(th, 900)})
                elif bt == "text":
                    if b.get("text", "").strip():
                        events.append({"role": "assistant", "ts": ts,
                                       "text": trunc(b["text"], 1600)})
                elif bt in ("tool_use", "server_tool_use"):
                    inp = b.get("input")
                    name = b.get("name", "?")
                    label, detail = tool_summary(name, inp)
                    ev = {"role": "tool", "ts": ts, "tool": label, "detail": detail}
                    full = tool_full(inp)
                    if full:
                        ev["full"] = full
                    tid = b.get("id")
                    tur = tur_by_id.get(tid)
                    if name in ("Agent", "Task") and isinstance(tur, dict):
                        ev["subagent"] = {
                            "type": tur.get("agentType")
                                    or (inp or {}).get("subagent_type") or "agent",
                            "model": tur.get("resolvedModel"),
                            "ms": tur.get("totalDurationMs"),
                            "tokens": tur.get("totalTokens"),
                            "tools": tur.get("totalToolUseCount"),
                            "stats": tur.get("toolStats") or {},
                            "prompt": trunc((inp or {}).get("prompt", ""), 1500),
                            "output": trunc(agent_output_text(tur.get("content")), 4000),
                        }
                        n_sub += 1
                    if name == "Edit" and isinstance(tur, dict) and tur.get("structuredPatch"):
                        ev["diff"] = format_patch(tur["structuredPatch"])
                    if name.startswith("mcp__"):
                        parts = name.split("__")
                        if len(parts) >= 3:
                            ev["mcpServer"] = parts[1]
                    hk = hooks_by_id.get(tid)
                    if hk:
                        ev["hooks"] = hk
                    if name == "Skill":
                        sk = skill_name(inp)
                        ev["skill"] = sk
                        ev["skillSource"] = "model"
                        tally_skill(skills, sk, "model")
                    if tid:
                        tool_ev_by_id[tid] = ev
                    events.append(ev)
                    n_tools += 1
                elif bt == "advisor_tool_result":
                    txt = b.get("content") or b.get("text") or ""
                    if isinstance(txt, list):
                        txt = "\n".join(x.get("text", "") for x in txt
                                        if isinstance(x, dict))
                    events.append({"role": "advisor", "ts": ts,
                                   "text": trunc(txt, 900)})
            if pending_tok is not None and len(events) > first_event_of_line:
                events[first_event_of_line]["tok"] = pending_tok
                events[first_event_of_line]["ctx"] = pending_ctx
                if pending_model:
                    events[first_event_of_line]["model"] = pending_model
                if pending_attr:
                    events[first_event_of_line]["attrSkill"] = pending_attr
                pending_tok = pending_ctx = pending_model = pending_attr = None

    # real elapsed time: wall-clock gap before each event (events inside one
    # turn share a timestamp, so a gap only appears between turns)
    prev_ms = None
    for e in events:
        ms = ts_ms(e.get("ts"))
        if prev_ms is not None and ms is not None and ms - prev_ms >= 1500:
            e["gap"] = int(ms - prev_ms)
        if ms is not None:
            prev_ms = ms

    # title: explicit goal (the objective) wins, else first user prompt,
    # else first assistant line, else customTitle
    title = None
    for e in events:
        if e["role"] == "goal":
            title = e["text"]
            break
    if not title:
        for e in events:
            if e["role"] == "user":
                title = e["text"]
                break
            # a command counts only if it carries arguments (skip bare /model, /clear)
            if e["role"] == "command" and " " in e["text"].strip():
                title = e["text"]
                break
    if not title:
        for e in events:
            if e["role"] == "assistant":
                title = e["text"]
                break
    if not title:
        title = custom_title or sid[:8]
    title = " ".join(title.split())[:90]

    dur = ""
    if first_ts and last_ts:
        try:
            a = datetime.fromisoformat(first_ts.replace("Z", "+00:00"))
            b2 = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
            secs = (b2 - a).total_seconds()
            if secs >= 3600:
                dur = "%.1f h" % (secs / 3600)
            elif secs >= 60:
                dur = "%.0f min" % (secs / 60)
            else:
                dur = "%.0f s" % secs
        except Exception:
            pass

    return {
        "id": sid,
        "title": title,
        "start": first_ts,
        "end": last_ts,
        "duration": dur,
        "nPrompts": n_prompts,
        "nTools": n_tools,
        "nEvents": len(events),
        "tokensOut": tokens_out,
        "peakCtx": peak_ctx,
        "skills": sorted(skills.values(), key=lambda s: (-s["count"], s["name"])),
        "models": [{"name": k, "count": v}
                   for k, v in sorted(models.items(), key=lambda x: -x[1])],
        "attrSkills": [{"name": k, "turns": v}
                       for k, v in sorted(attr_skills.items(), key=lambda x: -x[1])],
        "permModes": sorted(perm_modes),
        "serverTools": server_tools,
        "nSub": n_sub,
        "events": events,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project-dir",
                    help="Claude Code project log dir (default: derived from cwd, "
                         "~/.claude/projects/<slug>/)")
    ap.add_argument("--out", default="session-replay.html",
                    help="output HTML file (default: ./session-replay.html)")
    ap.add_argument("--title",
                    help="project title shown in the header "
                         "(default: basename of cwd)")
    ap.add_argument("--main-session",
                    help="session id to badge as MAIN BUILD (optional)")
    args = ap.parse_args()

    project_dir = args.project_dir or os.path.join(
        os.path.expanduser("~/.claude/projects"), project_slug(os.getcwd()))
    if not os.path.isdir(project_dir):
        raise SystemExit("No session log directory: %s" % project_dir)
    title = args.title or os.path.basename(os.getcwd())

    sessions = []
    for path in glob.glob(os.path.join(project_dir, "*.jsonl")):
        s = extract_session(path)
        if s["nEvents"] == 0:
            continue
        sessions.append(s)

    # strict chronological order by original start timestamp; the main build
    # session keeps a marker badge but is not pinned to the top.
    for s in sessions:
        s["minor"] = s["nEvents"] < 6
        s["main"] = s["id"] == args.main_session
    sessions.sort(key=lambda s: s.get("start") or "")

    data = json.dumps({"sessions": sessions}, ensure_ascii=False)
    data = data.replace("</", "<\\/")  # safe inside <script>

    safe_title = (title.replace("&", "&amp;").replace("<", "&lt;")
                  .replace(">", "&gt;"))
    html_doc = (HTML_TEMPLATE
                .replace("/*__DATA__*/", data)
                .replace("__TITLE__", safe_title))
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html_doc)
    total_ev = sum(s["nEvents"] for s in sessions)
    skill_totals = {}
    for s in sessions:
        for k in s["skills"]:
            t = skill_totals.setdefault(k["name"], 0)
            skill_totals[k["name"]] = t + k["count"]
    print("Wrote %s" % args.out)
    print("Sessions: %d  Total events: %d  Distinct skills: %d"
          % (len(sessions), total_ev, len(skill_totals)))
    for s in sessions[:5]:
        print("  %-10s ev=%-4d prompts=%-2d tools=%-3d %s | %s" % (
            s["id"][:8], s["nEvents"], s["nPrompts"], s["nTools"],
            s["duration"], s["title"][:50]))


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Claude Code Session Replay — __TITLE__</title>
<style>
  :root{
    /* Anthropic page shell (warm ivory / clay) */
    --ivory:#f0eee6; --ivory2:#f7f5ef; --card:#fbfaf7; --line:#e3ded1;
    --ink:#1f1e1c; --ink2:#3b3934; --muted:#6f6b61; --clay:#d97757;
    --clay-ink:#b65a3a; --clay-tint:#f4e3d9; --clay-line:#ecd2c2;
    /* Claude Code terminal pane (sampled from the welcome-screen screenshot) */
    --term:#0c0c0c; --term2:#141414; --term-chrome:#1d1d1d; --term-line:#2a2a2a;
    --t-coral:#cf7559; --t-coral-soft:#d98c6a; --t-green:#69c46a; --t-white:#dad6cc;
    --t-dim:#8a8a8a; --t-blue:#7ba3d0; --t-violet:#b58fc0; --t-red:#e0726b;
    --t-skill:#e8a06a;
    --serif:Georgia,"Iowan Old Style","Times New Roman",serif;
    --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;
    --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  }
  *{box-sizing:border-box}
  html,body{margin:0;height:100%}
  body{background:var(--ivory);color:var(--ink);
    font:14px/1.55 var(--sans);display:flex;flex-direction:column;overflow:hidden}
  header{padding:14px 22px;border-bottom:1px solid var(--line);
    background:var(--ivory2);display:flex;align-items:baseline;gap:14px;flex-wrap:wrap}
  header h1{font-family:var(--serif);font-size:20px;margin:0;font-weight:600;
    letter-spacing:-.01em;color:var(--ink)}
  header h1 span{color:var(--clay)}
  .sub{color:var(--muted);font-size:12px}
  .layout{flex:1;display:flex;min-height:0}
  .sidebar{width:312px;border-right:1px solid var(--line);background:var(--ivory2);
    display:flex;flex-direction:column;min-height:0}
  .tabs{display:flex;border-bottom:1px solid var(--line)}
  .tabs button{flex:1;background:none;border:none;color:var(--muted);padding:11px 6px;
    cursor:pointer;font-size:13px;font-weight:500;border-bottom:2px solid transparent}
  .tabs button:hover{color:var(--ink2)}
  .tabs button.active{color:var(--ink);border-bottom-color:var(--clay)}
  .tabpane{flex:1;overflow-y:auto;padding:10px}
  .tabpane.hidden{display:none}
  .sess{padding:10px 12px;border-radius:10px;cursor:pointer;margin-bottom:7px;
    border:1px solid var(--line);background:var(--card)}
  .sess:hover{border-color:var(--clay-line)}
  .sess.active{border-color:var(--clay);background:var(--clay-tint);
    box-shadow:0 1px 0 rgba(217,119,87,.12)}
  .sess.minor{opacity:.55}
  .sess .t{font-size:12.5px;font-weight:600;color:var(--ink);margin-bottom:5px;line-height:1.4;
    display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
  .sess .m{font-size:11px;color:var(--muted);display:flex;gap:10px;flex-wrap:wrap}
  .badge{display:inline-block;background:var(--clay);color:#fff;font-weight:600;
    font-size:9.5px;letter-spacing:.04em;padding:2px 7px;border-radius:20px;margin-left:6px}
  .main{flex:1;display:flex;min-height:0;padding:18px;background:
    radial-gradient(120% 120% at 100% 0%,#f3ede2 0%,var(--ivory) 55%)}
  /* the dark "Claude Code" window floating on the ivory page */
  .termwin{flex:1;position:relative;display:flex;flex-direction:column;min-height:0;background:var(--term);
    border:1px solid #000;border-radius:13px;overflow:hidden;
    box-shadow:0 24px 60px rgba(60,40,28,.22),0 4px 14px rgba(60,40,28,.14)}
  /* floating jump-to-top/bottom in the terminal corner */
  .scrollnav{position:absolute;right:16px;bottom:16px;z-index:5;display:flex;flex-direction:column;gap:6px}
  .scrollnav button{background:rgba(28,28,28,.92);color:var(--t-white);border:1px solid var(--term-line);
    border-radius:8px;font-family:var(--mono);font-size:11px;padding:5px 9px;cursor:pointer;white-space:nowrap;
    backdrop-filter:blur(2px)}
  .scrollnav button:hover{border-color:var(--clay);color:#fff}
  .titlebar{flex:0 0 auto;height:40px;display:flex;align-items:center;gap:9px;padding:0 15px;
    background:linear-gradient(180deg,#262626,#1c1c1c);border-bottom:1px solid #000;position:relative}
  .dot{width:12px;height:12px;border-radius:50%;box-shadow:inset 0 0 0 .5px rgba(0,0,0,.35)}
  .dot.r{background:#ff5f57}.dot.y{background:#febc2e}.dot.g{background:#28c840}
  .termtitle{position:absolute;left:0;right:0;margin:auto;text-align:center;pointer-events:none;
    color:#9a958c;font:12px/1 var(--mono)}
  .controls{flex:0 0 auto;padding:11px 16px;border-bottom:1px solid var(--term-line);
    background:var(--term2);display:flex;align-items:center;gap:14px;flex-wrap:wrap}
  .btn{background:var(--clay);color:#241007;border:none;border-radius:8px;
    padding:7px 15px;font-size:12.5px;font-weight:600;cursor:pointer;font-family:var(--mono)}
  .btn:hover{background:#e2825f}
  .btn.sec{background:#202020;color:var(--t-white);border:1px solid var(--term-line)}
  .btn.sec:hover{border-color:#3a3a3a;color:#fff}
  .btn:active{transform:translateY(1px)}
  .speed{display:flex;align-items:center;gap:8px;color:var(--t-dim);font-size:12px;font-family:var(--mono)}
  .speed input{width:140px;accent-color:var(--clay)}
  .speedval{color:var(--t-coral-soft);font-weight:600;min-width:34px;text-align:right}
  .progwrap{flex:1;min-width:150px;display:flex;align-items:center;gap:10px}
  .prog{flex:1;height:8px;background:#000;border-radius:6px;cursor:pointer;
    overflow:hidden;border:1px solid var(--term-line)}
  .prog .fill{height:100%;width:0;background:linear-gradient(90deg,var(--clay),var(--t-skill))}
  .count{font-size:11px;color:var(--t-dim);min-width:78px;text-align:right;
    font-family:var(--mono);font-variant-numeric:tabular-nums}
  /* conversation surface — terminal interior */
  .stage{flex:1;overflow-y:auto;padding:22px 26px 120px;background:var(--term);
    color:var(--t-white);font-family:var(--mono);font-size:13px;line-height:1.6}
  .ev{margin:0 0 15px;max-width:none;opacity:0;transform:translateY(8px);
    transition:opacity .35s ease,transform .35s ease}
  .ev.show{opacity:1;transform:none}
  /* brief highlight when jumped to from the prompts list */
  @keyframes evflash{from{box-shadow:0 0 0 2px var(--clay)}to{box-shadow:0 0 0 2px transparent}}
  .ev.flash .bubble,.ev.flash .marker,.ev.flash .tool,.ev.flash .subcard{
    animation:evflash 1.3s ease-out}
  /* console layout: content flush left, role/time gutter on the right */
  .row{display:flex;gap:13px;align-items:flex-start}
  .gut{order:2;flex:0 0 70px;text-align:right;font-size:10px;color:var(--t-dim);
    padding-top:5px;text-transform:lowercase;letter-spacing:.03em;font-family:var(--mono)}
  .body{order:1}
  .body{flex:1;min-width:0}
  .bubble{border-radius:9px;padding:11px 14px;border:1px solid var(--term-line);
    background:#101010;white-space:pre-wrap;word-wrap:break-word;overflow-wrap:anywhere}
  /* user prompt → the green ">" input box from the screenshot */
  .ev-user .bubble{background:#0f0d0c;border:1px solid var(--t-coral);color:var(--t-green)}
  .ev-user .bubble::before{content:"› ";color:var(--t-coral);font-weight:700}
  .ev-user .gut{color:var(--t-green)}
  /* goal → clay "session header" box */
  .ev-goal .bubble{background:#15100d;border:1px solid var(--t-coral);color:var(--t-coral-soft)}
  .ev-goal .gut{color:var(--t-coral-soft)}
  .ev-command .bubble{background:#0d0d0d;border-color:#243024;color:var(--t-green);font-size:12.5px}
  .ev-command .bubble::before{content:"❯ ";color:var(--t-dim)}
  .ev-command .gut{color:var(--t-green)}
  /* Claude response → clay-marked off-white text */
  .ev-assistant .bubble{background:transparent;border:none;border-left:2px solid var(--t-coral);
    border-radius:0;padding:2px 0 2px 15px;color:var(--t-white)}
  .ev-assistant .gut{color:var(--t-coral-soft)}
  .ev-thinking .bubble{background:#0e0e0e;border-color:#262026;color:var(--t-dim);
    font-style:italic;font-size:12.5px}
  .ev-thinking .gut{color:var(--t-violet)}
  .ev-advisor .bubble{background:#14101a;border-color:#3a2f4a;color:#d8c4e0}
  .ev-advisor .gut{color:var(--t-violet)}
  .ev-result .bubble{background:#0a0a0a;border-color:#222;color:var(--t-dim);
    font-size:12px;max-height:240px;overflow:auto}
  .ev-result.err .bubble{border-color:#4a2622;color:var(--t-red)}
  .ev-result .gut{color:var(--t-dim)}
  /* tool call → terminal command line */
  .tool{background:#0e0e0e;border:1px solid var(--term-line);border-left:2px solid var(--t-green);
    border-radius:8px;overflow:hidden}
  .ev-tool .gut{color:var(--t-green)}
  .toolrow{display:flex;align-items:center;gap:10px;padding:8px 12px}
  summary.toolrow{cursor:pointer;list-style:none;user-select:none}
  summary.toolrow::-webkit-details-marker{display:none}
  summary.toolrow:hover{background:#131313}
  details.tool[open]>summary.toolrow{border-bottom:1px solid var(--term-line)}
  .tool .exp{flex:0 0 auto;color:var(--t-blue);font-size:11px;font-family:var(--mono);white-space:nowrap}
  .tool .exp::before{content:'▸';margin-right:3px;color:var(--t-dim)}
  details.tool[open] .exp::before{content:'▾'}
  .toolbody{margin:0;background:#060606;padding:10px 12px;font-family:var(--mono);
    font-size:11.5px;color:var(--t-dim);white-space:pre-wrap;word-wrap:break-word;
    overflow-wrap:anywhere;max-height:340px;overflow:auto}
  .tool .name{flex:0 0 auto;color:var(--t-green);font-weight:600;font-family:var(--mono);
    font-size:12.5px;white-space:nowrap}
  .tool .name::before{content:"$ ";color:var(--t-dim);font-weight:400}
  .tool .detail{flex:1;min-width:0;color:var(--t-dim);font-family:var(--mono);font-size:12px;
    white-space:pre-wrap;overflow:hidden;text-overflow:ellipsis}
  .tokchip{margin-top:5px;text-align:right;font-size:10px;color:#7e7a70;
    font-family:var(--mono);font-variant-numeric:tabular-nums}
  .empty{color:var(--t-dim);text-align:center;margin-top:80px;font-family:var(--mono)}
  /* skill invocations stand out from ordinary tool calls / commands */
  .ev-skill .gut{color:var(--t-skill)}
  .ev-tool.ev-skill .tool{border-left-color:var(--t-skill)}
  .ev-tool.ev-skill .tool .name{color:var(--t-skill)}
  .ev-command.ev-skill .bubble{border-left:3px solid var(--t-skill)}
  .skillbadge{display:inline-flex;align-items:center;gap:4px;background:#1c130c;
    color:var(--t-skill);border:1px solid #4a3320;font-size:10px;padding:1px 7px;
    border-radius:20px;white-space:nowrap;font-family:var(--mono)}
  .ev-tool .skillbadge{flex:0 0 auto}
  .skillbadge.cmd{margin:0 0 5px 0}
  /* sidebar per-session skill tally (light) */
  .sess .skills{margin-top:6px}
  .skl{display:inline-block;background:var(--clay-tint);color:var(--clay-ink);
    border:1px solid var(--clay-line);font-size:10px;padding:1px 7px;border-radius:20px;
    margin:0 4px 4px 0;font-family:var(--mono)}
  /* Skills tab (light) */
  .sksum{margin-bottom:12px}
  .skrow{display:flex;align-items:center;gap:8px;padding:5px 2px}
  .skrow .skl{margin:0}
  .skn{color:var(--ink);font-size:12px;font-weight:600;font-variant-numeric:tabular-nums}
  .sksrc{color:var(--muted);font-size:11px;margin-left:auto;white-space:nowrap}
  .sktl{border-top:1px solid var(--line);padding-top:10px}
  .skitem{display:flex;align-items:center;gap:8px;padding:8px 10px;border-radius:9px;
    cursor:pointer;margin-bottom:6px;background:var(--card);font-size:12px;
    border:1px solid var(--line)}
  .skitem:hover{border-color:var(--clay-line)}
  .skname{flex:1;color:var(--ink);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .sktime{color:var(--muted);font-size:11px;font-family:var(--mono)}
  /* prompt browser (light) */
  #promptPane{display:flex;flex-direction:column;height:100%;min-height:0}
  .plist{flex:1;min-height:0;overflow-y:auto}
  .pnav{flex:0 0 auto;display:flex;align-items:center;gap:8px;padding:8px 2px 10px}
  .pnav .count{flex:1;text-align:center;color:var(--muted)}
  .plist .pitem{padding:9px 11px;border-radius:9px;cursor:pointer;margin-bottom:6px;
    background:var(--card);border:1px solid var(--line);font-size:12px;color:var(--ink2)}
  /* clamp on an inner element so card padding can't leak a partial 3rd line */
  .plist .pitem .ptext{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;
    overflow:hidden;overflow-wrap:anywhere;line-height:1.45}
  .plist .pitem:hover{border-color:var(--clay-line)}
  .plist .pitem.active{border-color:var(--clay);background:var(--clay-tint);color:var(--ink)}
  .pbig{flex:0 0 auto;background:var(--card);border:1px solid var(--line);border-radius:11px;
    padding:15px;margin-bottom:12px;white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px;
    color:var(--ink);min-height:60px;max-height:32vh;overflow:auto}
  .pmetarow{flex:0 0 auto;display:flex;align-items:center;gap:8px;margin-bottom:9px}
  .pmeta{font-size:11px;color:var(--muted)}
  .copybtn{margin-left:auto;background:var(--card);color:var(--muted);
    border:1px solid var(--line);border-radius:7px;font-size:11px;padding:4px 10px;
    cursor:pointer;white-space:nowrap}
  .copybtn:hover{color:var(--clay-ink);border-color:var(--clay)}
  /* per-turn model chip + real-elapsed + attribution */
  .metarow{margin-top:5px;display:flex;gap:7px;justify-content:flex-end;align-items:center;flex-wrap:wrap}
  .modelchip{font-family:var(--mono);font-size:10px;padding:1px 7px;border-radius:20px;
    border:1px solid currentColor;opacity:.9;white-space:nowrap}
  .m-opus{color:var(--t-coral-soft)} .m-sonnet{color:var(--t-blue)}
  .m-haiku{color:var(--t-green)} .m-fable{color:var(--t-violet)} .m-other{color:var(--t-dim)}
  .attrchip{font-family:var(--mono);font-size:10px;color:var(--t-skill);background:#1c130c;
    border:1px solid #4a3320;padding:1px 7px;border-radius:20px;white-space:nowrap}
  .attrchip::before{content:"⚙ "}
  .mcpbadge{flex:0 0 auto;font-family:var(--mono);font-size:10px;color:var(--t-blue);
    border:1px solid #2f4a63;background:#0b1620;padding:1px 7px;border-radius:20px;white-space:nowrap}
  /* real-elapsed divider between turns */
  .gapmark{margin:0;text-align:left;color:#5f5b53;font-family:var(--mono);
    font-size:10px;padding:2px 0 8px}
  .gapmark::before{content:"⏱ "}
  /* interrupt + plan markers */
  .ev-interrupt .body,.ev-plan .body{flex:1}
  .marker{max-width:560px;margin:0;text-align:left;font-family:var(--mono);font-size:11.5px;
    padding:7px 12px;border-radius:8px;border:1px dashed}
  .ev-interrupt .marker{color:var(--t-red);border-color:#4a2622;background:#160e0d}
  .ev-interrupt .marker::before{content:"⛔ "}
  .ev-plan .marker{color:var(--t-coral-soft);border-color:#3a2a20;background:#15100d}
  .ev-plan .marker::before{content:"📋 "}
  /* Edit diff inside tool body */
  .diff .da{color:var(--t-green)} .diff .dd{color:var(--t-red)}
  .diff .dh{color:var(--t-blue)} .diff .dc{color:var(--t-dim)}
  /* tool result, folded into the accordion */
  .resultlbl{padding:7px 12px 3px;border-top:1px solid var(--term-line);font-family:var(--mono);
    font-size:10px;color:var(--t-dim);text-transform:uppercase;letter-spacing:.05em}
  .toolbody.res{color:var(--t-dim)} .toolbody.res.err{color:var(--t-red)}
  .errdot{flex:0 0 auto;width:7px;height:7px;border-radius:50%;background:var(--t-red)}
  /* sub-agent card → opens modal */
  .subcard{background:#0e0e0e;border:1px solid var(--term-line);border-left:2px solid var(--t-skill);
    border-radius:8px;padding:9px 12px;cursor:pointer}
  .subcard:hover{background:#141414;border-color:#3a3a3a}
  .subhead{display:flex;align-items:center;gap:9px;flex-wrap:wrap}
  .subhead .name{color:var(--t-skill);font-weight:600;font-family:var(--mono);font-size:12.5px}
  .subhead .name::before{content:"⛓ "}
  .substats{color:var(--t-dim);font-family:var(--mono);font-size:11px;display:flex;gap:10px;flex-wrap:wrap}
  .subopen{margin-left:auto;color:var(--t-blue);font-size:11px;font-family:var(--mono);white-space:nowrap}
  .subopen::after{content:" ▸"}
  /* hooks (toggled; default hidden) */
  .hookwrap{display:none;margin-top:6px;border:1px solid #2a2620;border-radius:8px;
    background:#0b0a08;overflow:hidden}
  body.show-hooks .hookwrap{display:block}
  .hookrow{padding:6px 11px;border-bottom:1px solid #1c1a16;font-family:var(--mono);font-size:11px;
    color:var(--t-dim);display:flex;gap:9px;align-items:center;flex-wrap:wrap}
  .hookrow:last-child{border-bottom:none}
  .hookrow .hn{color:#c8a06a} .hookrow .ho{color:#5fae5f} .hookrow .he{color:var(--t-red)}
  .hooktoggle{display:flex;align-items:center;gap:6px;color:var(--t-dim);font-size:12px;
    font-family:var(--mono);cursor:pointer;user-select:none}
  .hooktoggle input{accent-color:var(--clay);cursor:pointer}
  /* sidebar model-mix bar + permission chip */
  .mixbar{margin-top:6px;height:5px;border-radius:4px;overflow:hidden;display:flex;background:#efe9dc}
  .mixbar i{display:block;height:100%}
  .seg-opus{background:var(--clay)} .seg-sonnet{background:#7aa2cf}
  .seg-haiku{background:#5db85d} .seg-fable{background:#b58fc0} .seg-other{background:#b9b2a2}
  .permchip{display:inline-block;font-size:9.5px;font-family:var(--mono);color:#7a6a52;
    background:#f1ead9;border:1px solid var(--line);padding:1px 6px;border-radius:20px;margin:5px 4px 0 0}
  /* sub-agent modal — terminal palette */
  .modal-backdrop{position:fixed;inset:0;background:rgba(8,6,4,.62);display:flex;align-items:center;
    justify-content:center;z-index:50;padding:30px}
  .modal-backdrop.hidden{display:none}
  .modal{width:min(860px,100%);max-height:86vh;display:flex;flex-direction:column;background:var(--term);
    border:1px solid var(--term-line);border-radius:13px;overflow:hidden;
    box-shadow:0 30px 80px rgba(0,0,0,.55)}
  .modal .mbar{flex:0 0 auto;display:flex;align-items:center;gap:10px;padding:12px 16px;
    background:linear-gradient(180deg,#262626,#1c1c1c);border-bottom:1px solid #000}
  .modal .mbar .name{color:var(--t-skill);font-family:var(--mono);font-weight:600;font-size:14px}
  .modal .mbar .name::before{content:"⛓ "}
  .modal .mclose{margin-left:auto;background:#202020;color:var(--t-white);border:1px solid var(--term-line);
    border-radius:7px;font-size:13px;padding:4px 11px;cursor:pointer;font-family:var(--mono)}
  .modal .mclose:hover{border-color:#3a3a3a;color:#fff}
  .mbody{overflow-y:auto;padding:16px;color:var(--t-white);font-family:var(--mono);font-size:12.5px}
  .mstats{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:9px;margin-bottom:14px}
  .mstat{background:#111;border:1px solid var(--term-line);border-radius:9px;padding:9px 11px}
  .mstat .k{color:var(--t-dim);font-size:10px;text-transform:uppercase;letter-spacing:.04em}
  .mstat .v{color:var(--t-coral-soft);font-size:15px;font-weight:600;margin-top:2px}
  .msec{margin-top:14px}
  .msec h4{margin:0 0 6px;color:var(--t-skill);font-size:11px;font-weight:600;text-transform:uppercase;
    letter-spacing:.05em;font-family:var(--mono)}
  .msec pre{margin:0;background:#080808;border:1px solid var(--term-line);border-radius:9px;padding:11px;
    white-space:pre-wrap;word-wrap:break-word;overflow-wrap:anywhere;color:var(--t-white);
    max-height:280px;overflow:auto;font-size:12px;line-height:1.55}
  .msec.prompt pre{color:var(--t-dim)}
  /* ============ terminal mode: real Claude Code CLI transcript ============ */
  body.mode-term .gut,body.mode-term .metarow{display:none}
  body.mode-term .ev{max-width:940px}
  body.mode-term .stage{font-size:13px;line-height:1.65}
  /* ● bullet hanging at the left of each line, coloured per role */
  body.mode-term .body{position:relative;padding-left:22px}
  body.mode-term .body::before{content:"●";position:absolute;left:2px;top:0;font-size:9px;
    line-height:1.9;color:#d6d1c6}
  body.mode-term .ev-assistant .body::before{color:#e8e4da}
  body.mode-term .ev-tool .body::before{color:var(--t-green)}
  body.mode-term .ev-tool.ev-skill .body::before{color:var(--t-skill)}
  body.mode-term .ev-thinking .body::before{color:var(--t-dim)}
  body.mode-term .ev-advisor .body::before{color:var(--t-violet)}
  body.mode-term .ev-user .body::before,body.mode-term .ev-goal .body::before,
  body.mode-term .ev-command .body::before{display:none}
  /* flatten the chat boxes into plain transcript text */
  body.mode-term .bubble{background:none;border:none;border-left:none;border-radius:0;padding:0}
  body.mode-term .ev-assistant .bubble{color:#dcd8d0}
  body.mode-term .ev-thinking .bubble{color:var(--t-dim);font-style:italic}
  body.mode-term .ev-result .bubble{background:none;border:none;padding:0}
  /* user / goal / command keep a boxed input look (the CLI prompt box) */
  body.mode-term .ev-user .bubble,body.mode-term .ev-goal .bubble,
  body.mode-term .ev-command .bubble{border:1px solid #343434;border-radius:6px;
    padding:8px 11px;background:#121212}
  body.mode-term .ev-user .bubble{color:var(--t-green)}
  /* tools: flat line + ⎿ result connector, no card chrome */
  body.mode-term .tool{background:none;border:none;border-left:none;border-radius:0}
  body.mode-term .tool .name::before{content:""}
  body.mode-term .toolrow{padding:0;gap:8px}
  body.mode-term summary.toolrow:hover{background:none}
  body.mode-term details.tool[open]>summary.toolrow{border-bottom:none}
  body.mode-term .toolbody{background:#0b0b0b;border-radius:6px;margin-top:6px}
  body.mode-term .resultlbl{border-top:none;padding:6px 0 2px}
  body.mode-term .resultlbl::before{content:"⎿ ";color:var(--t-dim)}
  body.mode-term .subcard{background:none;border:none;border-left:none;padding:0}
  body.mode-term .subhead .name::before{content:"⎿ ";color:var(--t-dim)}
</style>
</head>
<body>
<header>
  <h1>Claude Code Replay · <span>__TITLE__</span></h1>
  <span class="sub" id="hsub"></span>
</header>
<div class="layout">
  <aside class="sidebar">
    <div class="tabs">
      <button id="tabSessions" class="active" onclick="showTab('sessions')">Sessions</button>
      <button id="tabPrompts" onclick="showTab('prompts')">User Prompts</button>
      <button id="tabSkills" onclick="showTab('skills')">Skills</button>
    </div>
    <div id="paneSessions" class="tabpane"></div>
    <div id="paneSkills" class="tabpane hidden"></div>
    <div id="panePrompts" class="tabpane hidden">
      <div id="promptPane">
        <div class="pmetarow">
          <span class="pmeta" id="pmeta"></span>
          <button class="copybtn" id="pcopy" title="Copy this prompt to the clipboard"
                  onclick="copyPrompt()">⧉ Copy</button>
        </div>
        <div class="pbig" id="pbig"></div>
        <div class="pnav">
          <button class="btn sec" onclick="promptStep(-1)">‹ Prev</button>
          <span class="count" id="pcount"></span>
          <button class="btn sec" onclick="promptStep(1)">Next ›</button>
        </div>
        <div class="plist" id="plist"></div>
      </div>
    </div>
  </aside>
  <div class="main">
    <div class="termwin">
      <div class="titlebar">
        <span class="dot r"></span><span class="dot y"></span><span class="dot g"></span>
        <span class="termtitle" id="termtitle">claude — session replay</span>
      </div>
      <div class="controls">
        <button class="btn" id="playBtn" onclick="togglePlay()">▶ Play</button>
        <button class="btn sec" onclick="restart()">↺ Restart</button>
        <button class="btn sec" onclick="revealAll()">⤓ Show all</button>
        <label class="hooktoggle" title="show hook activity on tool calls">
          <input type="checkbox" id="hookToggle" onchange="toggleHooks()"> hooks
        </label>
        <button class="btn sec" id="modeBtn" onclick="toggleMode()"
                title="switch between window and CLI-transcript rendering">▣ terminal</button>
        <div class="speed">
          speed
          <input type="range" id="speed" min="0" max="6" step="1" value="2" oninput="setSpeed()">
          <span class="speedval" id="speedval">2×</span>
        </div>
        <div class="progwrap">
          <div class="prog" id="prog" onclick="seek(event)"><div class="fill" id="fill"></div></div>
          <span class="count" id="count">0 / 0</span>
          <span class="count" id="toks" title="output tokens revealed so far">0 tok</span>
        </div>
      </div>
      <div class="stage" id="stage"></div>
      <div class="scrollnav">
        <button onclick="scrollStage(-1)" title="jump to top">↑ top</button>
        <button onclick="scrollStage(1)" title="jump to bottom">↓ bottom</button>
      </div>
    </div>
  </div>
</div>
<div id="modal" class="modal-backdrop hidden" onclick="modalBackdrop(event)">
  <div class="modal">
    <div class="mbar">
      <span class="name" id="mName">sub-agent</span>
      <button class="mclose" onclick="closeModal()">✕ close</button>
    </div>
    <div class="mbody" id="mBody"></div>
  </div>
</div>
<script>
const DATA = /*__DATA__*/;
const SPEEDS=[0.5,1,2,4,8,16,32];
const BASE={user:1400,goal:1600,command:1000,assistant:900,thinking:700,tool:550,result:500,advisor:1100};
let cur=-1, events=[], idx=0, playing=false, timer=null, speed=2, cumTok=[0];

function esc(s){return (s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
function fmtTok(n){ if(n==null) return ""; if(n<1000) return ""+n;
  if(n<1e6) return (n/1e3).toFixed(1).replace(/\.0$/,"")+"k";
  return (n/1e6).toFixed(2)+"M"; }
function tlabel(ts){ if(!ts) return ""; try{const d=new Date(ts);
  return d.toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});}catch(e){return "";} }
function dlabel(ts){ if(!ts) return ""; try{const d=new Date(ts);
  return d.toLocaleString([], {month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'});
  }catch(e){return "";} }

function renderSessions(){
  const p=document.getElementById('paneSessions'); p.innerHTML='';
  DATA.sessions.forEach((s,i)=>{
    const d=document.createElement('div');
    d.className='sess'+(s.minor?' minor':'')+(i===cur?' active':'');
    d.onclick=()=>loadSession(i);
    const main = s.main ? '<span class="badge">MAIN BUILD</span>' : '';
    const toks = s.tokensOut ? `<span>${fmtTok(s.tokensOut)} tok</span>` : '';
    const skills = (s.skills&&s.skills.length)
      ? `<div class="m skills">`+s.skills.map(k=>
          `<span class="skl">${esc(k.name)}${k.count>1?'×'+k.count:''}</span>`).join('')+`</div>`
      : '';
    const sub = s.nSub ? `<span>${s.nSub} sub-agents</span>` : '';
    const mix = (s.models&&s.models.length) ? mixbarHTML(s.models) : '';
    const perms = (s.permModes&&s.permModes.length)
      ? `<div>`+s.permModes.map(pm=>`<span class="permchip">${esc(pm)}</span>`).join('')+`</div>` : '';
    d.innerHTML=`<div class="t">${esc(s.title)}</div>`+
      `<div class="m"><span>${s.nEvents} events</span>`+
      `<span>${s.nPrompts} prompts</span><span>${s.nTools} tools</span>${sub}${toks}${main}</div>`+
      `<div class="m"><span>${dlabel(s.start)}</span>`+
      (s.duration?`<span>ran ${s.duration}</span>`:'')+`</div>`+mix+perms+skills;
    p.appendChild(d);
  });
}

function loadSession(i){
  cur=i; events=DATA.sessions[i].events; idx=0; pause();
  cumTok=[0];
  for(let k=0;k<events.length;k++) cumTok.push(cumTok[k]+(events[k].tok||0));
  document.getElementById('stage').innerHTML='';
  renderSessions(); updateProgress(); renderPrompts(); renderSkills();
  const s=DATA.sessions[i];
  document.getElementById('termtitle').textContent='claude — '+(s.id||'').slice(0,8);
  const nSkill=(s.skills||[]).reduce((n,k)=>n+k.count,0);
  const mix=(s.models||[]).map(m=>modelShort(m.name)+' '+m.count).join(' / ');
  const srv=Object.entries(s.serverTools||{}).map(([k,v])=>`${k.replace(/_/g,' ')} ${v}`).join(', ');
  document.getElementById('hsub').textContent=
    `${s.nEvents} events · ${s.nPrompts} prompts · ${s.nTools} tool calls`+
    (s.nSub?` · ${s.nSub} sub-agents`:'')+
    (nSkill?` · ${nSkill} skill calls`:'')+
    (s.tokensOut?` · ${fmtTok(s.tokensOut)} tok out`:'')+
    (s.peakCtx?` · peak ctx ${fmtTok(s.peakCtx)}`:'')+
    (mix?` · ${mix}`:'')+
    ((s.permModes&&s.permModes.length)?` · ${s.permModes.join('/')}`:'')+
    (srv?` · ${srv}`:'')+
    (s.duration?` · spanned ${s.duration}`:'')+(s.start?` · ${s.start.slice(0,10)}`:'');
}

function modelClass(m){ if(!m)return 'm-other';
  if(m.indexOf('opus')>=0)return 'm-opus'; if(m.indexOf('sonnet')>=0)return 'm-sonnet';
  if(m.indexOf('haiku')>=0)return 'm-haiku'; if(m.indexOf('fable')>=0)return 'm-fable'; return 'm-other'; }
function modelShort(m){ return m?m.replace('claude-','').replace(/-\d{8}$/,''):''; }
function fmtDur(ms){ if(ms==null)return ''; const s=ms/1000;
  if(s<60)return s.toFixed(s<10?1:0)+'s'; const m=s/60;
  if(m<60)return m.toFixed(m<10?1:0)+'m'; return (m/60).toFixed(1)+'h'; }
function renderDiff(txt){ return esc(txt).split('\n').map(l=>{
  let c='dc'; if(l[0]==='+')c='da'; else if(l[0]==='-')c='dd'; else if(l.slice(0,2)==='@@')c='dh';
  return `<span class="${c}">${l}</span>`; }).join('\n'); }
function mixbarHTML(models){
  const tot=models.reduce((n,m)=>n+m.count,0)||1;
  const tip=models.map(m=>modelShort(m.name)+': '+m.count).join(', ');
  return `<div class="mixbar" title="${esc(tip)}">`+models.map(m=>
    `<i class="seg-${modelClass(m.name).slice(2)}" style="width:${100*m.count/tot}%"></i>`).join('')+`</div>`;
}

function evHTML(e,i){
  const wrap=document.createElement('div');
  wrap.className='ev ev-'+e.role+(e.error?' err':'')+(e.skill?' ev-skill':'');
  const gap = e.gap?`<div class="gapmark">${fmtDur(e.gap)} later</div>`:'';
  if(e.role==='interrupt'||e.role==='plan'){
    wrap.innerHTML=gap+`<div class="marker">${esc(e.text)}</div>`;
    return wrap;
  }
  const gl=e.skill ? 'skill'
    : ({user:'You',goal:'Goal',command:'/cmd',assistant:'Claude',thinking:'thinking',
        tool:'tool',result:'result',advisor:'advisor'}[e.role]||e.role);
  let body;
  if(e.role==='tool' && e.subagent){
    const sa=e.subagent, st=[];
    if(sa.tools!=null)st.push(`${sa.tools} tool calls`);
    if(sa.tokens!=null)st.push(`${fmtTok(sa.tokens)} tok`);
    if(sa.ms!=null)st.push(fmtDur(sa.ms));
    body=`<div class="subcard" onclick="openAgentModal(${i})">`+
      `<div class="subhead"><span class="name">${esc(sa.type)}</span>`+
      `<span class="subopen">open details</span></div>`+
      `<div class="substats">${st.map(x=>`<span>${esc(x)}</span>`).join('')}</div></div>`;
  } else if(e.role==='tool'){
    const sk=e.skill?`<span class="skillbadge" title="invoked by ${e.skillSource}">`+
      `${e.skillSource==='model'?'🤖':'👤'} skill</span>`:'';
    const mcp=e.mcpServer?`<span class="mcpbadge">${esc(e.mcpServer)}</span>`:'';
    const errdot=e.resultError?`<span class="errdot" title="result error"></span>`:'';
    const head=`<span class="name">${esc(e.tool)}</span>`+
      `<span class="detail">${esc(e.detail||'')}</span>${mcp}${sk}${errdot}`;
    let inner='';
    if(e.diff)inner+=`<pre class="toolbody diff">${renderDiff(e.diff)}</pre>`;
    else if(e.full)inner+=`<pre class="toolbody">${esc(e.full)}</pre>`;
    if(e.result!=null)inner+=`<div class="resultlbl">result${e.resultError?' · error':''}</div>`+
      `<pre class="toolbody res${e.resultError?' err':''}">${esc(e.result)}</pre>`;
    if(inner){
      body=`<details class="tool"><summary class="toolrow">${head}`+
           `<span class="exp">details</span></summary>${inner}</details>`;
    } else {
      body=`<div class="tool"><div class="toolrow">${head}</div></div>`;
    }
    if(e.hooks&&e.hooks.length){
      body+=`<div class="hookwrap">`+e.hooks.map(h=>{
        const ex=(h.exit===0||h.exit==null)?`<span class="ho">exit ${h.exit==null?'-':h.exit}</span>`
                 :`<span class="he">exit ${h.exit}</span>`;
        return `<div class="hookrow"><span class="hn">${esc(h.name||h.event||'hook')}</span>${ex}`+
               `${h.ms!=null?`<span>${h.ms}ms</span>`:''}</div>`; }).join('')+`</div>`;
    }
  } else {
    const sk=e.skill?`<div class="skillbadge cmd">👤 skill · ${esc(e.skill)}</div>`:'';
    body=`${sk}<div class="bubble">${esc(e.text)}</div>`;
  }
  const metas=[];
  if(e.tok!=null)metas.push(`<span class="tokchip" style="margin:0">+${fmtTok(e.tok)} out${e.ctx?` · ctx ${fmtTok(e.ctx)}`:''}</span>`);
  if(e.model)metas.push(`<span class="modelchip ${modelClass(e.model)}">${esc(modelShort(e.model))}</span>`);
  if(e.attrSkill)metas.push(`<span class="attrchip">${esc(e.attrSkill)}</span>`);
  const meta = metas.length?`<div class="metarow">${metas.join('')}</div>`:'';
  wrap.innerHTML=gap+`<div class="row"><div class="gut">${gl}<br>${tlabel(e.ts)}</div>`+
                 `<div class="body">${body}${meta}</div></div>`;
  return wrap;
}

function openAgentModal(i){
  const sa=events[i]&&events[i].subagent; if(!sa)return;
  document.getElementById('mName').textContent=sa.type||'sub-agent';
  const st=sa.stats||{};
  const cards=[['agent',sa.type],['model',sa.model?modelShort(sa.model):'inherited'],
    ['duration',sa.ms!=null?fmtDur(sa.ms):'—'],['tokens',sa.tokens!=null?fmtTok(sa.tokens):'—'],
    ['tool calls',sa.tools!=null?sa.tools:'—']];
  let html='<div class="mstats">'+cards.map(c=>
    `<div class="mstat"><div class="k">${c[0]}</div><div class="v">${esc(''+(c[1]==null?'—':c[1]))}</div></div>`).join('')+'</div>';
  const mp={readCount:'reads',bashCount:'bash',editFileCount:'edits',searchCount:'searches',otherToolCount:'other'};
  const bits=[]; for(const k in mp){ if(st[k])bits.push(`${st[k]} ${mp[k]}`); }
  let lines=''; if(st.linesAdded||st.linesRemoved)
    lines=`<span class="da">+${st.linesAdded||0}</span>  <span class="dd">−${st.linesRemoved||0}</span>`;
  if(bits.length||lines)
    html+=`<div class="msec"><h4>tool breakdown</h4><pre class="diff">${esc(bits.join(' · '))}${lines?'\n'+lines:''}</pre></div>`;
  if(sa.prompt)html+=`<div class="msec prompt"><h4>task prompt</h4><pre>${esc(sa.prompt)}</pre></div>`;
  if(sa.output)html+=`<div class="msec"><h4>final output</h4><pre>${esc(sa.output)}</pre></div>`;
  document.getElementById('mBody').innerHTML=html;
  document.getElementById('modal').classList.remove('hidden');
}
function closeModal(){ document.getElementById('modal').classList.add('hidden'); }
function modalBackdrop(ev){ if(ev.target.id==='modal')closeModal(); }
function toggleHooks(){ document.body.classList.toggle('show-hooks',
  document.getElementById('hookToggle').checked); }
function scrollStage(dir){ const s=document.getElementById('stage');
  s.scrollTo({top: dir<0?0:s.scrollHeight, behavior:'smooth'}); }
let termMode=false;
function toggleMode(){ termMode=!termMode;
  document.body.classList.toggle('mode-term',termMode);
  document.getElementById('modeBtn').textContent=termMode?'⊞ window':'▣ terminal';
  document.getElementById('termtitle').textContent=(termMode?'~ claude':'claude')+
    ' — '+((DATA.sessions[cur]||{}).id||'').slice(0,8); }

function delayFor(e){
  let d=BASE[e.role]||700;
  const len=(e.text||e.detail||'').length;
  d += Math.min(len*8, 2200);          // longer content lingers, capped
  return d/speed;
}

function showNext(){
  if(idx>=events.length){ pause(); return; }
  const e=events[idx];
  const node=evHTML(e,idx);
  document.getElementById('stage').appendChild(node);
  requestAnimationFrame(()=>node.classList.add('show'));
  node.scrollIntoView({behavior:'smooth',block:'end'});
  idx++; updateProgress();
  if(playing){ timer=setTimeout(showNext, delayFor(e)); }
}

function togglePlay(){
  if(playing){ pause(); return; }
  if(idx>=events.length){ restart(); }
  playing=true; document.getElementById('playBtn').textContent='❚❚ Pause';
  showNext();
}
function pause(){ playing=false; clearTimeout(timer);
  document.getElementById('playBtn').textContent='▶ Play'; }
function restart(){ pause(); idx=0; document.getElementById('stage').innerHTML='';
  updateProgress(); }
function revealAll(){
  pause();
  const stage=document.getElementById('stage');
  for(;idx<events.length;idx++){
    const n=evHTML(events[idx],idx); n.classList.add('show'); stage.appendChild(n);
  }
  updateProgress();
  stage.scrollTop=stage.scrollHeight;
}
function setSpeed(){ speed=SPEEDS[+document.getElementById('speed').value];
  document.getElementById('speedval').textContent=speed+'×'; }
function updateProgress(){
  const t=events.length||1;
  document.getElementById('fill').style.width=(100*idx/t)+'%';
  document.getElementById('count').textContent=idx+' / '+events.length;
  document.getElementById('toks').textContent=fmtTok(cumTok[idx]||0)+' tok';
}
function seek(ev){
  const r=ev.currentTarget.getBoundingClientRect();
  const frac=(ev.clientX-r.left)/r.width;
  const target=Math.round(frac*events.length);
  pause();
  const stage=document.getElementById('stage'); stage.innerHTML=''; idx=0;
  for(;idx<target && idx<events.length;idx++){
    const n=evHTML(events[idx],idx); n.classList.add('show'); stage.appendChild(n);
  }
  updateProgress(); stage.scrollTop=stage.scrollHeight;
}

/* ---- prompt browser ---- */
let prompts=[], pidx=0;
function renderPrompts(){
  // keep each prompt's index in the full event stream so we can jump to it
  prompts=[];
  events.forEach((e,i)=>{ if(e.role==='user'||e.role==='goal'||e.role==='command')
    prompts.push({role:e.role,text:e.text,ts:e.ts,evIdx:i}); });
  pidx=0;
  const list=document.getElementById('plist'); list.innerHTML='';
  prompts.forEach((e,i)=>{
    const d=document.createElement('div');
    d.className='pitem'; d.onclick=()=>selectPrompt(i);
    const t=document.createElement('div'); t.className='ptext';
    t.textContent=(e.role==='goal'?'🎯 ':e.role==='command'?'⌘ ':'')+e.text;
    d.appendChild(t); list.appendChild(d);
  });
  showPrompt();
}
function selectPrompt(i){ pidx=i; showPrompt(); jumpToEvent(prompts[i].evIdx); }
function jumpToEvent(target){
  if(target==null||target<0)return;
  pause();
  const stage=document.getElementById('stage');
  if(target>=idx){                         // not revealed yet → advance the stream to it
    for(;idx<=target && idx<events.length;idx++){
      const n=evHTML(events[idx],idx); n.classList.add('show'); stage.appendChild(n);
    }
    updateProgress();
  }
  const node=stage.querySelectorAll('.ev')[target];
  if(node){
    node.scrollIntoView({behavior:'smooth',block:'center'});
    node.classList.add('flash'); setTimeout(()=>node.classList.remove('flash'),1300);
  }
}
function showPrompt(){
  if(!prompts.length){
    document.getElementById('pbig').textContent='No user prompts in this session.';
    document.getElementById('pcount').textContent='0 / 0';
    document.getElementById('pmeta').textContent=''; return;
  }
  const e=prompts[pidx];
  document.getElementById('pbig').textContent=e.text;
  document.getElementById('pcount').textContent=(pidx+1)+' / '+prompts.length;
  document.getElementById('pmeta').textContent=
    (e.role==='goal'?'Initial goal':e.role==='command'?'Slash command':'Prompt')+
    (e.ts?' · '+tlabel(e.ts):'');
  [...document.querySelectorAll('#plist .pitem')].forEach((n,i)=>
    n.classList.toggle('active',i===pidx));
}
function promptStep(d){ if(!prompts.length)return;
  pidx=(pidx+d+prompts.length)%prompts.length; showPrompt(); }
function copyPrompt(){
  if(!prompts.length) return;
  const txt=prompts[pidx].text||'';
  const btn=document.getElementById('pcopy');
  const flash=()=>{ btn.textContent='✓ Copied'; setTimeout(()=>{btn.textContent='⧉ Copy';},1200); };
  if(navigator.clipboard&&navigator.clipboard.writeText){
    navigator.clipboard.writeText(txt).then(flash).catch(()=>fallbackCopy(txt,flash));
  } else { fallbackCopy(txt,flash); }
}
function fallbackCopy(txt,cb){
  const ta=document.createElement('textarea');
  ta.value=txt; ta.style.position='fixed'; ta.style.top='-1000px'; ta.style.opacity='0';
  document.body.appendChild(ta); ta.focus(); ta.select();
  try{ document.execCommand('copy'); cb&&cb(); }catch(e){}
  document.body.removeChild(ta);
}

/* ---- skills tab ---- */
function renderSkills(){
  const pane=document.getElementById('paneSkills'); pane.innerHTML='';
  const s=DATA.sessions[cur]||{};
  const items=[];
  events.forEach((e,i)=>{ if(e.skill) items.push({i,name:e.skill,src:e.skillSource,ts:e.ts}); });
  const attr=(s.attrSkills||[]);
  if(!items.length && !attr.length){
    pane.innerHTML='<div class="empty" style="margin-top:30px">No skills used in this session.</div>';
    return;
  }
  let html='';
  if(items.length){
    const agg={};
    items.forEach(it=>{ const a=agg[it.name]||(agg[it.name]={name:it.name,count:0,user:0,model:0});
      a.count++; a[it.src]++; });
    const sum=Object.values(agg).sort((a,b)=>b.count-a.count||a.name.localeCompare(b.name));
    html+='<div class="sksum">';
    sum.forEach(a=>{ html+=`<div class="skrow"><span class="skl">${esc(a.name)}</span>`+
      `<span class="skn">${a.count}×</span>`+
      `<span class="sksrc">${a.user?`👤 ${a.user}`:''}${a.user&&a.model?' · ':''}`+
      `${a.model?`🤖 ${a.model}`:''}</span></div>`; });
    html+='</div><div class="sktl">';
    items.forEach(it=>{ html+=`<div class="skitem" onclick="seekToIndex(${it.i+1})">`+
      `<span>${it.src==='model'?'🤖':'👤'}</span>`+
      `<span class="skname">${esc(it.name)}</span>`+
      `<span class="sktime">${tlabel(it.ts)}</span></div>`; });
    html+='</div>';
  }
  if(attr.length){
    html+=`<div class="sktl" style="margin-top:14px">`+
      `<div class="sksrc" style="margin:0 0 8px">⚙ active skill context · attributed turns</div>`;
    attr.forEach(a=>{ html+=`<div class="skrow"><span class="attrchip">${esc(a.name)}</span>`+
      `<span class="skn">${a.turns}</span><span class="sksrc">turns</span></div>`; });
    html+='</div>';
  }
  pane.innerHTML=html;
}
function seekToIndex(target){
  pause();
  const stage=document.getElementById('stage'); stage.innerHTML=''; idx=0;
  for(;idx<target && idx<events.length;idx++){
    const n=evHTML(events[idx],idx); n.classList.add('show'); stage.appendChild(n);
  }
  updateProgress();
  const last=stage.lastChild; if(last) last.scrollIntoView({block:'center'});
}

function showTab(which){
  const panes={sessions:'paneSessions',prompts:'panePrompts',skills:'paneSkills'};
  const tabs={sessions:'tabSessions',prompts:'tabPrompts',skills:'tabSkills'};
  for(const k in panes){
    document.getElementById(panes[k]).classList.toggle('hidden',k!==which);
    document.getElementById(tabs[k]).classList.toggle('active',k===which);
  }
}

document.addEventListener('keydown',e=>{
  if(e.code==='Escape'){closeModal();return;}
  if(e.target.tagName==='INPUT')return;
  if(e.code==='Space'){e.preventDefault();togglePlay();}
});

let startIdx=DATA.sessions.findIndex(s=>s.main); if(startIdx<0)startIdx=0;
setSpeed(); renderSessions(); loadSession(startIdx);
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
