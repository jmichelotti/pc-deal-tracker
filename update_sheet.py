"""CLI wrapper around SheetClient so Claude can call it via Bash.

Usage:
    python update_sheet.py init
    python update_sheet.py read-active
    python update_sheet.py upsert --json '{"URL": "...", "Machine": "...", ...}'
    python update_sheet.py mark-status --url URL --status STATUS [--note NOTE]
    python update_sheet.py archive --url URL --reason REASON

All commands print a JSON result to stdout. Errors go to stderr with exit code 1.
"""

from __future__ import annotations

import argparse
import json
import sys

from sheet_client import SheetClient


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init")
    sub.add_parser("read-active")

    p_upsert = sub.add_parser("upsert")
    p_upsert.add_argument("--json", dest="json_str", required=True,
                          help="JSON object with listing fields")

    p_status = sub.add_parser("mark-status")
    p_status.add_argument("--url", required=True)
    p_status.add_argument("--status", required=True,
                          choices=["ACTIVE", "PRICE CHANGED", "EXPIRED", "SOLD"])
    p_status.add_argument("--note", default=None)

    p_archive = sub.add_parser("archive")
    p_archive.add_argument("--url", required=True)
    p_archive.add_argument("--reason", required=True)

    p_rank = sub.add_parser("rank")
    p_rank.add_argument("--json", dest="json_str", required=True,
                        help='JSON array like [{"url":"...","rank":1},...]')

    sub.add_parser("sort-active")

    args = parser.parse_args()

    try:
        client = SheetClient()

        if args.cmd == "init":
            result = client.init()
        elif args.cmd == "read-active":
            result = client.read_active()
        elif args.cmd == "upsert":
            data = json.loads(args.json_str)
            result = client.upsert(data)
        elif args.cmd == "mark-status":
            result = client.mark_status(args.url, args.status, args.note)
        elif args.cmd == "archive":
            result = client.archive(args.url, args.reason)
        elif args.cmd == "rank":
            rankings = json.loads(args.json_str)
            result = client.rank_bulk(rankings)
        elif args.cmd == "sort-active":
            result = client.sort_active()
        else:
            print(f"Unknown command: {args.cmd}", file=sys.stderr)
            return 1

        print(json.dumps(result, indent=2, default=str))
        return 0
    except Exception as e:
        print(json.dumps({"error": type(e).__name__, "message": str(e)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
