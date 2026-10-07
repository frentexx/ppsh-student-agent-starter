#!/usr/bin/env python3
"""把 Codex 的本機對話紀錄（JSONL）整理成一份可讀的 Markdown，並遮蔽金鑰與密碼。

只讀 Codex 的會話紀錄，只輸出「工作資料夾等於這個專案」的對話。
用法：
  python extract_history.py --project <專案資料夾> [--out <輸出.md>] [--since YYYY-MM-DD]
                            [--sessions-dir <資料夾>]
輸出預設：<專案>/作業成果/對話紀錄.md
結束碼：0 成功；2 找不到會話紀錄（請改由學生貼上對話）。

狀態：Codex 紀錄的欄位依公開資料撰寫，【待實機驗證】；解析失敗時不會亂猜，會回報。
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# ---------- 遮蔽 ----------
REDACTIONS = [
    (re.compile(r"\bsk-[A-Za-z0-9_\-]{12,}"), "[已遮蔽金鑰]"),
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._\-]{12,}"), "Bearer [已遮蔽]"),
    (re.compile(r"(?i)\b(api[_-]?key|token|secret|password|passwd|密碼|金鑰)\b\s*[:：=]\s*\S+"),
     r"\1: [已遮蔽]"),
    # 長且同時含英文與數字的字串（常見的 Token 形態）
    (re.compile(r"\b(?=[A-Za-z0-9_\-]*\d)(?=[A-Za-z0-9_\-]*[A-Za-z])[A-Za-z0-9_\-]{32,}\b"),
     "[已遮蔽長字串]"),
]


def redact(text):
    for pat, rep in REDACTIONS:
        text = pat.sub(rep, text)
    return text


# ---------- 讀檔 ----------
def open_lines(path):
    """支援 .jsonl 與 .jsonl.zst（zst 需要 zstandard 套件，沒有就略過並回報）。"""
    if path.suffix == ".zst":
        try:
            import zstandard  # type: ignore
        except ImportError:
            raise RuntimeError("zst")
        import io
        with open(path, "rb") as fh:
            data = zstandard.ZstdDecompressor().stream_reader(fh).read()
        return io.StringIO(data.decode("utf-8", "replace")).read().splitlines()
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def norm(p):
    return os.path.normcase(os.path.normpath(str(p))).rstrip("\\/")


def text_of(content):
    parts = []
    if isinstance(content, str):
        return content
    for c in content or []:
        if isinstance(c, dict) and isinstance(c.get("text"), str):
            parts.append(c["text"])
    return "\n".join(parts)


SYSTEM_PREFIXES = ("<environment_context>", "<user_instructions>", "# AGENTS.md",
                   "<permissions", "<INSTRUCTIONS>", "<turn_aborted>")


def parse_session(path, project):
    lines = open_lines(path)
    cwd, started, msgs, fallback = None, None, [], []
    for raw in lines:
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            continue
        typ = obj.get("type")
        payload = obj.get("payload") or {}
        if typ == "session_meta":
            cwd = payload.get("cwd") or cwd
            started = payload.get("timestamp") or obj.get("timestamp") or started
        elif typ == "turn_context" and not cwd:
            cwd = payload.get("cwd")
        elif typ == "response_item" and payload.get("type") == "message":
            role = payload.get("role")
            if role in ("user", "assistant"):
                t = text_of(payload.get("content")).strip()
                if t and not t.startswith(SYSTEM_PREFIXES):
                    msgs.append((role, t, obj.get("timestamp")))
        elif typ == "event_msg":
            et = payload.get("type")
            if et == "user_message" and payload.get("message"):
                fallback.append(("user", payload["message"].strip(), obj.get("timestamp")))
            elif et == "agent_message" and payload.get("message"):
                fallback.append(("assistant", payload["message"].strip(), obj.get("timestamp")))
    if not cwd:
        return None
    pn, cn = norm(project), norm(cwd)
    if not (cn == pn or cn.startswith(pn + os.sep)):
        return None
    return {"file": path.name, "started": started, "cwd": cwd, "messages": msgs or fallback}


def find_sessions_dirs(arg):
    if arg:
        return [Path(arg)]
    dirs = []
    home = os.environ.get("CODEX_HOME")
    if home:
        dirs.append(Path(home) / "sessions")
    dirs.append(Path.home() / ".codex" / "sessions")
    return [d for d in dirs if d.is_dir()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--out")
    ap.add_argument("--since")
    ap.add_argument("--sessions-dir")
    ap.add_argument("--max-chars", type=int, default=1500, help="單則訊息最多保留字數")
    a = ap.parse_args()

    project = Path(a.project).resolve()
    out = Path(a.out) if a.out else project / "作業成果" / "對話紀錄.md"
    since = datetime.strptime(a.since, "%Y-%m-%d") if a.since else None

    dirs = find_sessions_dirs(a.sessions_dir)
    if not dirs:
        print("找不到 Codex 會話資料夾（~/.codex/sessions）。請改由學生貼上對話。")
        sys.exit(2)

    files = sorted([p for d in dirs for p in d.rglob("rollout-*.jsonl*")])
    sessions, skipped_zst = [], 0
    for f in files:
        try:
            s = parse_session(f, project)
        except RuntimeError:
            skipped_zst += 1
            continue
        except OSError:
            continue
        if not s or not s["messages"]:
            continue
        if since and s["started"]:
            try:
                if datetime.fromisoformat(s["started"].replace("Z", "+00:00")).replace(
                        tzinfo=None) < since:
                    continue
            except ValueError:
                pass
        sessions.append(s)

    if not sessions:
        hint = f"（有 {skipped_zst} 份壓縮紀錄因缺少 zstandard 套件而略過）" if skipped_zst else ""
        print(f"在這個專案資料夾找不到對話紀錄{hint}。請改由學生貼上對話。")
        sys.exit(2)

    out.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# 對話紀錄（自動整理，已遮蔽金鑰與密碼）", "",
             f"- 專案資料夾：{project}", f"- 對話段數：{len(sessions)}", ""]
    total = 0
    for i, s in enumerate(sessions, 1):
        lines += [f"## 第 {i} 段（{s['started'] or '時間不明'}）", ""]
        for role, t, _ts in s["messages"]:
            t = redact(t)
            if len(t) > a.max_chars:
                t = t[: a.max_chars] + "…（以下省略）"
            who = "學生" if role == "user" else "AI"
            lines += [f"**{who}**：{t}", ""]
            total += 1
    out.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"已輸出 {out}（{len(sessions)} 段、{total} 則訊息）")


if __name__ == "__main__":
    main()
