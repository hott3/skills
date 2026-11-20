#!/usr/bin/env python3
"""Parse WebVTT subtitle files into clean, deduplicated transcripts.

Removes inline <c> timestamp tags, HTML entities, and rolling-caption duplicate
lines, then groups utterances into timestamped blocks.
"""

import argparse
import html
import re
import sys

TAG_RE = re.compile(r"<[^>]+>")
TS_RE = re.compile(
    r"^(\d{2}):(\d{2}):(\d{2})\.\d{3}\s+-->\s+(\d{2}):(\d{2}):(\d{2})\.\d{3}"
)


def ts_to_seconds(h: str, m: str, s: str) -> int:
    return int(h) * 3600 + int(m) * 60 + int(s)


def format_ts(sec: int) -> str:
    m, s = divmod(sec, 60)
    return f"{m:02d}:{s:02d}"


def sanitize_cosense(text: str) -> str:
    text = text.replace("[", "（").replace("]", "）")
    text = re.sub(r"(^|\s)#(\S+)", r"\1`#\2`", text)
    return text


def parse_vtt(path: str) -> list[tuple[int, str]]:
    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    cues: list[tuple[int, str]] = []
    cur_start: int | None = None
    cur_lines: list[str] = []

    def flush() -> None:
        nonlocal cur_start, cur_lines
        if cur_start is not None and cur_lines:
            for raw in cur_lines:
                cleaned = html.unescape(TAG_RE.sub("", raw)).strip()
                if not cleaned:
                    continue
                if not cues or cues[-1][1] != cleaned:
                    cues.append((cur_start, cleaned))
        cur_start = None
        cur_lines = []

    for line in lines:
        m = TS_RE.match(line)
        if m:
            flush()
            cur_start = ts_to_seconds(m.group(1), m.group(2), m.group(3))
        elif line.strip() == "":
            flush()
        elif cur_start is not None:
            cur_lines.append(line)

    flush()
    return cues


def group_cues(
    cues: list[tuple[int, str]], interval_sec: int = 60, fmt: str = "markdown"
) -> list[str]:
    if not cues:
        return []
    blocks: list[str] = []
    next_marker = 0
    buf: list[str] = []

    for ts, text in cues:
        if fmt == "cosense":
            text = sanitize_cosense(text)
        if ts >= next_marker:
            if buf:
                blocks.append(" ".join(buf))
                buf = []
            ts_str = format_ts(ts)
            if fmt == "markdown":
                prefix = f"**[{ts_str}]**"
            elif fmt == "cosense":
                prefix = f"({ts_str})"
            else:
                prefix = f"[{ts_str}]"
            buf.append(f"{prefix} {text}")
            next_marker = ((ts // interval_sec) + 1) * interval_sec
        else:
            buf.append(text)
    if buf:
        blocks.append(" ".join(buf))
    return blocks


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Parse WebVTT into clean timestamped transcript blocks."
    )
    parser.add_argument("vtt_file", help="Path to the .vtt file")
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Timestamp grouping interval in seconds (default: 60)",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "cosense", "raw"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    args = parser.parse_args()

    cues = parse_vtt(args.vtt_file)
    blocks = group_cues(cues, interval_sec=args.interval, fmt=args.format)
    for b in blocks:
        print(b)
        if args.format == "markdown":
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
