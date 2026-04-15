"""Google Sheets client for the PC Deal Tracker.

Writes deals to a two-tab sheet (Active/Archive), keyed by listing URL.
Auth via service account JSON at the path in sheet-config.json.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials


ACTIVE_COLUMNS = [
    "URL",
    "Claude's Ranking",
    "Status",
    "Machine",
    "Price",
    "All-in",
    "Source",
    "Location",
    "CPU",
    "RAM",
    "Storage",
    "Seller",
    "vs Market",
    "First Found",
    "Last Verified",
    "Notes",
]

ARCHIVE_COLUMNS = ACTIVE_COLUMNS + ["Expired Date", "Expired Reason"]

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

PROJECT_ROOT = Path(__file__).parent
CONFIG_PATH = PROJECT_ROOT / "sheet-config.json"


def _today() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")


def _load_config() -> dict:
    with CONFIG_PATH.open() as f:
        return json.load(f)


class SheetClient:
    def __init__(self):
        cfg = _load_config()
        self.cfg = cfg
        sa_path = PROJECT_ROOT / cfg["service_account_path"]
        creds = Credentials.from_service_account_file(str(sa_path), scopes=SCOPES)
        self.gc = gspread.authorize(creds)
        self.ss = self.gc.open_by_url(cfg["sheet_url"])
        self.active_name = cfg["active_tab"]
        self.archive_name = cfg["archive_tab"]

    def _ws(self, name: str):
        return self.ss.worksheet(name)

    def init(self) -> dict:
        """Write headers, bold + freeze them, and convert data ranges into native
        Google Sheets Tables. Idempotent: safe to run repeatedly."""
        results = {}
        for tab, cols in [
            (self.active_name, ACTIVE_COLUMNS),
            (self.archive_name, ARCHIVE_COLUMNS),
        ]:
            ws = self._ws(tab)
            existing = ws.row_values(1)
            if existing != cols:
                ws.update([cols], "A1", value_input_option="USER_ENTERED")
            self._format_header(ws, len(cols))
            self._ensure_table(ws, tab, len(cols))
            results[tab] = f"{len(cols)} columns ready"
        return results

    def _format_header(self, ws, ncols: int) -> None:
        ws.freeze(rows=1)
        ws.format(
            f"A1:{gspread.utils.rowcol_to_a1(1, ncols)}",
            {
                "textFormat": {"bold": True},
                "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.95},
            },
        )

    def _ensure_table(self, ws, tab_name: str, ncols: int) -> None:
        """Create a native Google Sheets Table covering the header + data range
        if one doesn't exist yet. Errors (including 'already exists') are ignored."""
        try:
            body = {
                "requests": [
                    {
                        "addTable": {
                            "table": {
                                "name": f"{tab_name}Table",
                                "range": {
                                    "sheetId": ws.id,
                                    "startRowIndex": 0,
                                    "endRowIndex": 1000,
                                    "startColumnIndex": 0,
                                    "endColumnIndex": ncols,
                                },
                            }
                        }
                    }
                ]
            }
            self.ss.batch_update(body)
        except Exception:
            # Table already exists, or API doesn't support it on this sheet — fine.
            pass

    def read_active(self) -> list[dict]:
        ws = self._ws(self.active_name)
        rows = ws.get_all_records(expected_headers=ACTIVE_COLUMNS)
        return [r for r in rows if r.get("URL")]

    def _find_row_by_url(self, ws, url: str) -> int | None:
        urls = ws.col_values(1)  # column A = URL
        for idx, val in enumerate(urls[1:], start=2):  # skip header
            if val == url:
                return idx
        return None

    def _next_empty_row(self, ws) -> int:
        """Row number immediately after the last URL-bearing row. gspread's
        append_row appends after ws.row_count, which is wrong when the sheet
        has a Table reserving thousands of empty rows."""
        urls = ws.col_values(1)
        return len(urls) + 1

    def _ensure_capacity(self, ws, row: int) -> None:
        if row > ws.row_count:
            ws.add_rows(row - ws.row_count + 5)

    def upsert(self, data: dict) -> dict:
        """Insert or update a row in Active, keyed on URL.
        `data` keys should match ACTIVE_COLUMNS (missing keys -> blank)."""
        if "URL" not in data or not data["URL"]:
            raise ValueError("upsert requires a URL field")
        ws = self._ws(self.active_name)
        today = _today()
        data.setdefault("Last Verified", today)
        data.setdefault("Status", "ACTIVE")

        row_idx = self._find_row_by_url(ws, data["URL"])
        if row_idx is None:
            data.setdefault("First Found", today)
            row = [str(data.get(c, "")) for c in ACTIVE_COLUMNS]
            target_row = self._next_empty_row(ws)
            self._ensure_capacity(ws, target_row)
            end_a1 = gspread.utils.rowcol_to_a1(target_row, len(ACTIVE_COLUMNS))
            ws.update([row], f"A{target_row}:{end_a1}",
                      value_input_option="USER_ENTERED")
            return {"action": "inserted", "url": data["URL"], "row": target_row}

        existing = ws.row_values(row_idx)
        existing += [""] * (len(ACTIVE_COLUMNS) - len(existing))
        merged = []
        for i, col in enumerate(ACTIVE_COLUMNS):
            if col in data and data[col] != "":
                merged.append(str(data[col]))
            else:
                merged.append(existing[i])
        ws.update(
            [merged],
            f"A{row_idx}:{gspread.utils.rowcol_to_a1(row_idx, len(ACTIVE_COLUMNS))}",
            value_input_option="USER_ENTERED",
        )
        return {"action": "updated", "url": data["URL"], "row": row_idx}

    def mark_status(self, url: str, status: str, note: str | None = None) -> dict:
        ws = self._ws(self.active_name)
        row_idx = self._find_row_by_url(ws, url)
        if row_idx is None:
            return {"action": "not_found", "url": url}
        status_col = ACTIVE_COLUMNS.index("Status") + 1
        verified_col = ACTIVE_COLUMNS.index("Last Verified") + 1
        ws.update_cell(row_idx, status_col, status)
        ws.update_cell(row_idx, verified_col, _today())
        if note:
            notes_col = ACTIVE_COLUMNS.index("Notes") + 1
            existing_note = ws.cell(row_idx, notes_col).value or ""
            new_note = f"{existing_note} | {note}" if existing_note else note
            ws.update_cell(row_idx, notes_col, new_note)
        return {"action": "status_updated", "url": url, "status": status}

    def archive(self, url: str, reason: str) -> dict:
        """Copy a row from Active -> Archive with expired date/reason, delete from Active."""
        active = self._ws(self.active_name)
        archive = self._ws(self.archive_name)
        row_idx = self._find_row_by_url(active, url)
        if row_idx is None:
            return {"action": "not_found", "url": url}
        row = active.row_values(row_idx)
        row += [""] * (len(ACTIVE_COLUMNS) - len(row))
        archive_row = row + [_today(), reason]
        target_row = self._next_empty_row(archive)
        self._ensure_capacity(archive, target_row)
        end_a1 = gspread.utils.rowcol_to_a1(target_row, len(ARCHIVE_COLUMNS))
        archive.update([archive_row], f"A{target_row}:{end_a1}",
                       value_input_option="USER_ENTERED")
        active.delete_rows(row_idx)
        return {"action": "archived", "url": url, "reason": reason}

    def rank_bulk(self, rankings: list[dict]) -> dict:
        """Set Claude's Ranking for many rows at once.
        rankings = [{"url": "...", "rank": 1}, {"url": "...", "rank": 2}, ...]
        Unknown URLs are skipped and reported."""
        ws = self._ws(self.active_name)
        urls = ws.col_values(1)
        url_to_row = {u: i + 1 for i, u in enumerate(urls) if u}  # 1-indexed
        updated = []
        skipped = []
        rank_col = ACTIVE_COLUMNS.index("Claude's Ranking") + 1
        rank_col_a1 = gspread.utils.rowcol_to_a1(1, rank_col)[0:-1]
        batch = []
        for entry in rankings:
            url = entry.get("url")
            rank = entry.get("rank")
            if url not in url_to_row:
                skipped.append(url)
                continue
            row_idx = url_to_row[url]
            batch.append({
                "range": f"{rank_col_a1}{row_idx}",
                "values": [[rank]],
            })
            updated.append({"url": url, "rank": rank, "row": row_idx})
        if batch:
            ws.batch_update(batch, value_input_option="USER_ENTERED")
        return {"action": "ranked", "updated": len(updated), "skipped": skipped}

    def sort_active(self) -> dict:
        """Sort Active rows (below header) by Claude's Ranking ascending.
        Blank ranks sort to the bottom."""
        ws = self._ws(self.active_name)
        rank_col = ACTIVE_COLUMNS.index("Claude's Ranking") + 1
        last_row = self._next_empty_row(ws) - 1
        if last_row <= 1:
            return {"action": "sorted", "rows": 0}
        end_a1 = gspread.utils.rowcol_to_a1(last_row, len(ACTIVE_COLUMNS))
        ws.sort((rank_col, "asc"), range=f"A2:{end_a1}")
        return {"action": "sorted", "rows": last_row - 1}
