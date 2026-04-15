# pc-deal-tracker

An automated deal-tracking agent that runs on a schedule to find the best used/refurbished PC deals meeting specific requirements, tracks them over time, and maintains a persistent record of active and expired listings.

## Mission

Find and track the best value used/refurbished computers available for purchase (local Bay Area pickup or shipped to 94122) that meet the hardware requirements below. On each run, check previously found deals to see if they are still active, mark expired ones, and search for new deals. Write all findings to `deals.md`.

## Hardware Requirements

**Must meet ALL of the following:**
- 8+ cores / 16+ threads — no 4-core or 6-core machines
- Proper desktop-class CPU, 35W TDP or higher — no U-series or Y-series laptop chips
- CPU from 2019 or newer — no pre-8th gen Intel, no pre-Ryzen 2000 series AMD
- RAM: Either 32GB already installed, OR the machine supports upgrade to 32GB/64GB and a compatible RAM kit is available for a good total price (machine + RAM kit must still represent strong value)
- Total all-in price must make sense for the spec — benchmark against eBay sold listings and flag steals vs. fair prices
- Form factor does not matter — towers, desktops, mini PCs, laptops all acceptable
- Machine will be ethernet-connected, stationary, used for dev work (Claude Code, Python, FastAPI, Angular, pytest)

**Storage: Not required**
- No internal SSD/HDD requirement
- Do NOT add $70 (or any amount) for a missing or small internal drive — user has multiple 1TB USB drives available and current dev work totals only 2.5–3GB
- If machine has a drive already, treat it as added value but do not penalize machines with small or no drives

**Geographic requirement — either is acceptable:**
- Local pickup within ~1 hour of zip code 94122 (SF Inner Sunset), OR
- Shipped from a reputable seller with 98%+ positive feedback, meaningful transaction history, and a return policy covering dead-on-arrival or not-as-described

## What to Search Each Run

Search the following sources for new listings:
- Craigslist SF Bay Area — "32GB desktop", "32GB workstation", "32GB OptiPlex", "32GB EliteDesk", "32GB ThinkCentre", "32GB tower", "i7-10700 32GB", "i9 32GB", "Ryzen 32GB desktop", "16GB workstation upgrade"
- eBay — both local pickup (94xxx) and shipped listings from reputable sellers; search same terms plus model-specific searches based on what's performing well in the tracker
- Facebook Marketplace SF Bay Area
- Craigslist for RAM kits if a promising machine is found that needs an upgrade — verify compatibility before including in tracker

## How to Run a Session

Each session must follow these steps in order:

### Step 1 — Read the current state
Read `deals.md` in full. Note all active listings, their URLs, prices, and date first found. Note all previously expired listings so you don't re-add them.

### Step 2 — Check existing active listings
For each listing currently marked ACTIVE in `deals.md`:
- Visit the URL using the Playwright MCP
- Determine if the listing is still live, price has changed, or has been removed/sold
- Update the status accordingly: ACTIVE, PRICE CHANGED, EXPIRED, or SOLD
- Note the date of the status change

### Step 3 — Search for new deals
Run the searches listed above. For each promising find:
- Verify RAM spec against manufacturer QuickSpecs or official spec sheet
- Benchmark price against eBay sold comps for the same model/config
- Calculate total all-in cost (machine + shipping if applicable + $70 SSD if no drive included)
- Confirm return policy and seller credibility for shipped listings
- Only add to tracker if it represents genuine value — do not pad with mediocre listings

### Step 4 — Update deals.md
Write the updated file with all changes from this session. See format below.

### Step 4b — Mirror all changes to the Google Sheet
Dual-write phase: every change made to `deals.md` in Step 4 must also be applied to the Google Sheet via `update_sheet.py`. See the **Google Sheet Sync** section below for the schema and CLI reference. `deals.md` remains the source of truth for now — the sheet is being validated in parallel.

### Step 4c — Rank all active deals and sort the sheet
After all upserts/status changes/archives are done, assign a ranking to every currently active listing (1 = best, N = worst), call `rank`, then call `sort-active`. The ranking order must match the order shown in the **Active Listings** section of `deals.md` (the best deal at the top becomes rank 1). See the CLI reference below.

### Step 5 — Print a session summary
After updating the file, print a brief summary to the terminal:
- How many active deals are currently tracked
- Any new deals found this session
- Any deals that expired or were sold since last run
- Any deals where price changed
- The single best current deal and why

## deals.md Format

```markdown
# PC Deal Tracker
Last updated: [DATE TIME]
Total runs: [N]

## ⭐ Best Current Deal
[Single best listing with one-line reason why]

## Active Listings

### [MACHINE NAME] — $[PRICE] — [SOURCE]
- **Status:** ACTIVE
- **URL:** [url]
- **First found:** [date]
- **Last verified:** [date]
- **CPU:** [model, cores/threads, TDP]
- **RAM:** [amount, type, installed or upgrade needed]
- **Storage:** [what's included or "none"]
- **GPU:** [if present]
- **Location:** [local pickup location or "ships from X"]
- **Seller:** [name, feedback %, transaction count if eBay]
- **Returns:** [policy]
- **All-in price:** [machine] + [shipping] + [SSD if needed] = [total]
- **vs. market:** [brief benchmark — e.g. "eBay comps at $400-450, this is $380 = slight steal"]
- **Notes:** [anything worth flagging — age of listing, condition, upgrade path, etc.]

---

## Expired / Sold Listings

### [MACHINE NAME] — $[PRICE] — [SOURCE]
- **Status:** SOLD / EXPIRED / PRICE CHANGED (was $X, now $Y)
- **URL:** [url]
- **First found:** [date]
- **Expired:** [date]
- **Notes:** [brief note on why it's no longer viable]

---

## Search History
| Run | Date | New Finds | Expired | Best Deal |
|-----|------|-----------|---------|-----------|
| 1   | [date] | [n] | [n] | [machine name] |
```

## Known Good

The following machines were found in prior research and are no longer being tracked as open deals. Do not re-add these to the tracker:

- **HP Z2 Tower G5** $450 (i7-10700, 32GB, 512GB NVMe, NVIDIA T1000) — it is the baseline for what "good value" looks like going forward but hopefully we can find a better deal
- Intel NUC 10i7FNHN $250 Sunnyvale — only 6C/12T, passed on
- HP EliteDesk 800 G6 i7-10700 $250 San Jose — only 16GB RAM
- Dell Latitude 7400 $300 San Jose — 4C/8T, overpriced
- Dell Inspiron 5379 $200 Danville — 4-month listing, red flag
- HP Omen Ryzen 7 5700G $400 Berkeley — good machine, no longer needed
- HP Elite Mini 600 G9 i7-13700T $400 Petaluma — thermal concerns, no longer needed
- Dell OptiPlex 5090 i7-10700 32GB Antioch — no longer listed

## Dead Sources — Do Not Search

- Weird Stuff Warehouse — permanently closed
- RePC — Seattle only, not Bay Area

## Google Sheet Sync (Dual-Write Phase)

The tracker writes to both `deals.md` AND a Google Sheet. The sheet lives at the URL in `sheet-config.json` and has two tabs: `Active` and `Archive`. Auth uses a service account key at `secrets/sa.json` — never read, log, or commit this file.

### Schema

**Active tab columns** (in order): `URL` (unique key) · `Claude's Ranking` · `Status` · `Machine` · `Price` · `All-in` · `Source` · `Location` · `CPU` · `RAM` · `Storage` · `Seller` · `vs Market` · `First Found` · `Last Verified` · `Notes`

`Claude's Ranking` is an integer 1..N where 1 = best current deal. Every session must rerank ALL currently active listings end-to-end (see Step 4c).

**Archive tab columns**: all of the above, plus `Expired Date` and `Expired Reason` at the end.

Status values: `ACTIVE`, `PRICE CHANGED`, `EXPIRED`, `SOLD`.

### CLI operations

All sheet operations go through `update_sheet.py`. Run from the project root via Bash. Every command prints a JSON result to stdout.

- **Read current active listings** (call this at the start of every run to cross-check against `deals.md`):
  ```
  python update_sheet.py read-active
  ```

- **Insert or update a listing** (keyed on URL — same URL = update, new URL = insert). Fields map to Active columns. Omit `First Found` and `Last Verified` on inserts and the script auto-fills today's date; on updates, omitted fields preserve existing values.
  ```
  python update_sheet.py upsert --json '{"URL":"https://...","Machine":"HP Z2 G5","Price":"$450","All-in":"$450","Source":"eBay","Location":"Ships from CA","CPU":"i7-10700 8C/16T 65W","RAM":"32GB DDR4","Storage":"512GB NVMe","Seller":"name (99.5%)","vs Market":"At market","Notes":"..."}'
  ```

- **Update status on an existing row** (use for PRICE CHANGED; also bumps Last Verified and appends the note to Notes):
  ```
  python update_sheet.py mark-status --url "https://..." --status "PRICE CHANGED" --note "was $450, now $400"
  ```

- **Move a row to Archive** (use when a listing is sold, removed, or otherwise no longer viable — row is copied to Archive with `Expired Date` = today and `Expired Reason` = provided reason, then deleted from Active):
  ```
  python update_sheet.py archive --url "https://..." --reason "SOLD — listing removed"
  ```

- **Bulk-set rankings on all active listings** (always pass ranks for every currently active URL, 1..N with no gaps or ties):
  ```
  python update_sheet.py rank --json '[{"url":"https://...","rank":1},{"url":"https://...","rank":2}]'
  ```

- **Sort the Active tab by Claude's Ranking ascending** (call once at the end of the session, after `rank`):
  ```
  python update_sheet.py sort-active
  ```

### When to use which operation

| deals.md change | Sheet operation |
|---|---|
| New deal found and added to Active Listings | `upsert` with all fields |
| Existing active deal re-verified, still live, no change | `mark-status --status ACTIVE` (refreshes Last Verified) |
| Existing active deal's price changed | `mark-status --status "PRICE CHANGED"` + `upsert` with new Price/All-in |
| Active listing moved to Expired/Sold section in deals.md | `archive` with appropriate reason |
| All upserts/archives done for the session | `rank` with the full 1..N ordering, then `sort-active` |

### Error handling

If any `update_sheet.py` call fails, the session does NOT fail — proceed with `deals.md` updates and note the sheet sync failure in the session summary. The service account or network may be down; `deals.md` remains authoritative during dual-write.

### One-time init
Already run. If the Active/Archive tabs ever lose their headers or table formatting, re-run `python update_sheet.py init` — it's idempotent.

## Tooling Notes

- **Default tool for web-based searches is the Playwright MCP.** Use it for Craigslist, eBay, Facebook Marketplace, and any listing verification.
- **Use `browser_evaluate` to extract structured listing data** — do not use snapshots for listing pages, they are too large.
- **Verify listing status by visiting the URL directly** — do not assume a listing is still active from a prior run.
- **Close browser tabs when done** with each search thread.
- **Do not create any files other than deals.md and the Google Sheet updates** — no plan documents, no sub-READMEs, no new code files. Existing files (`sheet_client.py`, `update_sheet.py`, `sheet-config.json`) are the only tooling — do not add more.
- **Do not commit or push to git from inside a tracking session** — the session is automated and unattended. Git commits happen manually via the user's `/ucp` command at end-of-session. Never stage, commit, or push from within a scheduled run.

## Report Writing

- Be honest about thin markets — "found nothing new this run" is a valid and useful result
- Flag dynamic pricing risk on listings that have been active a long time
- Flag any listing that has been sitting more than 2 weeks — may indicate an issue or room to negotiate
- Show the math on all-in prices
- Benchmark every price against eBay sold comps — do not just report the ask

## Tasks

Use `TaskCreate`/`TaskUpdate` for each run. Create a task at the start of the session, mark it in_progress, and mark it completed when deals.md has been written and the summary printed.

Also create a one-time task on the first run:

**Task: Set up Windows Task Scheduler job**
- Create a `.bat` file in this directory called `run-tracker.bat` with the following content:
```bat
@echo off
cd /d "%~dp0"
claude -p "Run a deal tracking session as described in CLAUDE.md" --allowedTools "mcp__playwright__*,WebSearch,WebFetch" >> tracker-log.txt 2>&1
```
- Document in a file called `SCHEDULER-SETUP.md` the exact steps to add this to Windows Task Scheduler:
  - Open Task Scheduler
  - Create Basic Task
  - Name: PC Deal Tracker
  - Trigger: Daily, repeat every 12 hours
  - Action: Start a program → point to `run-tracker.bat`
  - Working directory: this directory
  - Conditions: uncheck "Start only if on AC power" if on a laptop
- Mark this task complete once the .bat file and SCHEDULER-SETUP.md have been created

## What NOT to Do

- Do not re-add machines from the Known Good / Already Purchased list
- Do not pad the tracker with weak listings that don't meet the hardware requirements
- Do not leave browser tabs open between search threads
- Do not cache or re-use listing data from prior runs without re-verifying via URL visit
- Do not create code files, plan documents, or anything other than deals.md (plus the Google Sheet updates via the existing `update_sheet.py`). `run-tracker.bat` and `SCHEDULER-SETUP.md` already exist.
- Do not read, copy, log, or commit `secrets/sa.json` — it's the service account credential for the sheet