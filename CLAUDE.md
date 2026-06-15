# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A GitHub Actions automation that sends a daily HTML email with World Cup match results, upcoming fixtures, and group standings. The entire logic lives in one Python script; there are no dependencies beyond the standard library.

## Running the script locally

```bash
export FOOTBALL_API_KEY=your_key
export GMAIL_USER=you@gmail.com
export GMAIL_APP_PASSWORD=your_app_password
export RECIPIENT_EMAIL=recipient@example.com
python scripts/send_update.py
```

`RECIPIENT_EMAIL` is optional — defaults to `GMAIL_USER` if unset. No `pip install` needed.

## Architecture

`scripts/send_update.py` is the only executable file. Its flow:

1. **Fetch** — `api_get()` calls `football-data.org/v4` with the `WC` competition code. `fetch_matches()` accepts a date range; `fetch_standings()` hits `/competitions/WC/standings`.
2. **Build HTML** — `build_html(yesterday_str, today_str, yesterday_matches, today_matches, standings)` composes three sections by calling helpers:
   - `build_section()` renders an inline-styled HTML table. For fixtures (`show_time=True`) it groups rows by Paris calendar date via `date_header_row()`. For results (`show_time=False`) no grouping is applied.
   - `build_standings_section()` renders one table per group, filtered to `type=TOTAL` entries. Top-2 positions per group are highlighted with a blue tint (promotion spots).
3. **Send** — `send_email()` delivers via Gmail SMTP SSL on port 465.

All times are normalized to `PARIS = timezone(timedelta(hours=2))` (CEST). Switch to `+1` in winter.

## GitHub Actions

`.github/workflows/daily_worldcup.yml` runs at `0 3 * * *` UTC (5am CEST). GitHub's scheduling lag of 2-3h means delivery typically lands around 5-8am Paris time. It requires four repository secrets: `FOOTBALL_API_KEY`, `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `RECIPIENT_EMAIL`. The workflow can also be triggered manually via `workflow_dispatch`.

## Key design decisions

- **Fixtures window is today + tomorrow** — catches late-night games that start in US timezones but fall on the next Paris calendar day.
- **Results window is yesterday + today** — catches overnight games that finished after midnight Paris time.
- Only `FINISHED` matches appear in the results section; everything else (including `IN_PLAY`) goes in the fixtures section.
- `team_name()` prefers `shortName` over `name` to keep table rows compact.
