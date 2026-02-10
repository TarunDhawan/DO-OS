#!/usr/bin/env python3
"""DO-OS launch tracker: daily progress, release notes, and screenshot registry."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

ROOT = Path.cwd()
BASE_DIR = ROOT / ".do-os"
PROGRESS_DIR = BASE_DIR / "progress"
RELEASE_NOTES_PATH = BASE_DIR / "release-notes.md"
SCREENSHOTS_PATH = BASE_DIR / "screenshots.md"
MANIFEST_PATH = BASE_DIR / "manifest.json"


def now_iso() -> str:
    return dt.datetime.now().replace(microsecond=0).isoformat()


def ensure_initialized() -> None:
    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)

    if not RELEASE_NOTES_PATH.exists():
        RELEASE_NOTES_PATH.write_text(
            "# Release Notes\n\n"
            "Use this file to store notes for every release candidate and launch update.\n\n",
            encoding="utf-8",
        )

    if not SCREENSHOTS_PATH.exists():
        SCREENSHOTS_PATH.write_text(
            "# Launch Screenshots Registry\n\n"
            "Track all screenshots needed for launch assets and release communication.\n\n"
            "| Date | Feature | Path | Description | Importance |\n"
            "|---|---|---|---|---|\n",
            encoding="utf-8",
        )

    if not MANIFEST_PATH.exists():
        manifest = {
            "created_at": now_iso(),
            "version": "0.1",
            "artifacts": {
                "progress_dir": str(PROGRESS_DIR.relative_to(ROOT)),
                "release_notes": str(RELEASE_NOTES_PATH.relative_to(ROOT)),
                "screenshots": str(SCREENSHOTS_PATH.relative_to(ROOT)),
            },
        }
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def require_initialized() -> None:
    if not BASE_DIR.exists():
        raise SystemExit(
            "DO-OS tracker is not initialized. Run: python tools/do_os_tracker.py init"
        )


def progress_path(date: str) -> Path:
    return PROGRESS_DIR / f"{date}.md"


def cmd_init(_: argparse.Namespace) -> None:
    ensure_initialized()
    print(f"Initialized tracker at {BASE_DIR}")


def cmd_progress_add(args: argparse.Namespace) -> None:
    require_initialized()
    date = args.date or dt.date.today().isoformat()
    file_path = progress_path(date)
    if not file_path.exists():
        file_path.write_text(
            f"# Daily Progress - {date}\n\n"
            "## Wins\n- \n\n"
            "## In Progress\n- \n\n"
            "## Blockers\n- \n\n"
            "## Next Steps\n- \n",
            encoding="utf-8",
        )

    entry = f"- [{now_iso()}] {args.entry.strip()}\n"
    with file_path.open("a", encoding="utf-8") as f:
        f.write("\n## Log\n" if "## Log" not in file_path.read_text(encoding="utf-8") else "")
        f.write(entry)
    print(f"Added progress entry to {file_path}")


def cmd_progress_list(args: argparse.Namespace) -> None:
    require_initialized()
    date = args.date or dt.date.today().isoformat()
    file_path = progress_path(date)
    if not file_path.exists():
        print(f"No progress file found for {date}")
        return
    print(file_path.read_text(encoding="utf-8"))


def cmd_release_add(args: argparse.Namespace) -> None:
    require_initialized()
    section = (
        f"\n## {args.version} - {args.date or dt.date.today().isoformat()}\n"
        f"- Summary: {args.summary}\n"
        f"- Impact: {args.impact}\n"
        f"- Owner: {args.owner}\n"
        f"- Notes: {args.notes}\n"
    )
    with RELEASE_NOTES_PATH.open("a", encoding="utf-8") as f:
        f.write(section)
    print(f"Added release note to {RELEASE_NOTES_PATH}")


def cmd_release_list(_: argparse.Namespace) -> None:
    require_initialized()
    print(RELEASE_NOTES_PATH.read_text(encoding="utf-8"))


def cmd_screenshot_add(args: argparse.Namespace) -> None:
    require_initialized()
    row = (
        f"| {args.date or dt.date.today().isoformat()} | {args.feature} | {args.path} | "
        f"{args.description} | {args.importance} |\n"
    )
    with SCREENSHOTS_PATH.open("a", encoding="utf-8") as f:
        f.write(row)
    print(f"Added screenshot entry to {SCREENSHOTS_PATH}")


def cmd_screenshot_list(_: argparse.Namespace) -> None:
    require_initialized()
    print(SCREENSHOTS_PATH.read_text(encoding="utf-8"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Track daily progress, release notes, and launch screenshots.")
    sub = parser.add_subparsers(dest="command", required=True)

    init_p = sub.add_parser("init", help="Initialize DO-OS tracking files")
    init_p.set_defaults(func=cmd_init)

    progress = sub.add_parser("progress", help="Daily progress operations")
    progress_sub = progress.add_subparsers(dest="subcommand", required=True)

    p_add = progress_sub.add_parser("add", help="Add daily progress entry")
    p_add.add_argument("entry", help="Progress note text")
    p_add.add_argument("--date", help="Date in YYYY-MM-DD")
    p_add.set_defaults(func=cmd_progress_add)

    p_list = progress_sub.add_parser("list", help="Show daily progress file")
    p_list.add_argument("--date", help="Date in YYYY-MM-DD")
    p_list.set_defaults(func=cmd_progress_list)

    release = sub.add_parser("release", help="Release notes operations")
    release_sub = release.add_subparsers(dest="subcommand", required=True)

    r_add = release_sub.add_parser("add", help="Add release note")
    r_add.add_argument("version", help="Release version label")
    r_add.add_argument("summary", help="One-line release summary")
    r_add.add_argument("impact", help="Who/what was impacted")
    r_add.add_argument("owner", help="Owner name")
    r_add.add_argument("notes", help="Additional notes")
    r_add.add_argument("--date", help="Date in YYYY-MM-DD")
    r_add.set_defaults(func=cmd_release_add)

    r_list = release_sub.add_parser("list", help="Show release notes")
    r_list.set_defaults(func=cmd_release_list)

    shot = sub.add_parser("screenshot", help="Screenshot registry operations")
    shot_sub = shot.add_subparsers(dest="subcommand", required=True)

    s_add = shot_sub.add_parser("add", help="Register launch screenshot")
    s_add.add_argument("feature", help="Feature or flow name")
    s_add.add_argument("path", help="Relative screenshot path")
    s_add.add_argument("description", help="What this screenshot shows")
    s_add.add_argument(
        "importance",
        choices=["critical", "high", "medium", "low"],
        help="Launch importance",
    )
    s_add.add_argument("--date", help="Date in YYYY-MM-DD")
    s_add.set_defaults(func=cmd_screenshot_add)

    s_list = shot_sub.add_parser("list", help="Show screenshot registry")
    s_list.set_defaults(func=cmd_screenshot_list)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
