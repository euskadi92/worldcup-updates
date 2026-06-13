# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A GitHub Actions automation that sends a daily HTML email with World Cup match results and upcoming fixtures. The entire logic lives in one Python script; there are no dependencies beyond the standard library.

## Running the script locally

```bash
export FOOTBALL_API_KEY=your_key
export GMAIL_USER=you@gmail.com
export GMAIL_APP_PASSWORD=your_app_password
export RECIPIENT_EMAIL=recipient@example.com
python scripts/send_update.py
```

No `pip install` needed — the script uses only Python stdlib (`smtplib`, `urllib`, `json`, `datetime`).

## Architecture

`scripts/send_update.py` is the only executable file. Its flow:

1. **Fetch** — `api_get()` calls `football-data.org/v4` with the `WC` competition code. `fetch_matches()` accepts a date range.
2. **Build HTML** — `build_html()` composes two sections (yesterday's results, today+tomorrow's fixtures) by calling `build_section()`, which renders an inline-styled HTML table. Fixtures are grouped by Paris calendar date via `date_header_row()`.
3. **Send** — `send_email()` delivers via Gmail SMTP SSL on port 465.

All times are normalized to `PARIS = timezone(timedelta(hours=2))` (CEST). Switch to `+1` in winter.

## GitHub Actions

`.github/workflows/daily_worldcup.yml` runs at `0 6 * * *` UTC (8am CEST). It requires four repository secrets: `FOOTBALL_API_KEY`, `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `RECIPIENT_EMAIL`. The workflow can also be triggered manually via `workflow_dispatch`.

## Key design decisions

- **Fixtures window is today + tomorrow** — catches late-night games that start in US timezones but fall on the next Paris calendar day.
- **Results window is yesterday + today** — catches overnight games that finished after midnight Paris time.
- Only `FINISHED` matches appear in the results section; everything else (including `IN_PLAY`) goes in the fixtures section.
