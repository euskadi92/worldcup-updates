import os
import smtplib
import json
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.request import urlopen, Request
from urllib.error import URLError

API_KEY = os.environ["FOOTBALL_API_KEY"]
GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
RECIPIENT = os.environ.get("RECIPIENT_EMAIL", GMAIL_USER)

API_BASE = "https://api.football-data.org/v4"
# FIFA World Cup 2026 competition code
COMPETITION = "WC"

PARIS = timezone(timedelta(hours=2))  # CEST — adjust to +1 in winter (CET)


def api_get(path):
    req = Request(f"{API_BASE}{path}", headers={"X-Auth-Token": API_KEY})
    with urlopen(req) as resp:
        return json.loads(resp.read())


def fetch_matches(date_from, date_to=None):
    if date_to is None:
        date_to = date_from
    data = api_get(f"/competitions/{COMPETITION}/matches?dateFrom={date_from}&dateTo={date_to}")
    return data.get("matches", [])


def format_score(match):
    score = match.get("score", {})
    ft = score.get("fullTime", {})
    home = ft.get("home")
    away = ft.get("away")
    if home is None or away is None:
        return "- : -"
    return f"{home} : {away}"


def status_label(status):
    return {
        "FINISHED": "Final",
        "IN_PLAY": "Live",
        "PAUSED": "HT",
        "TIMED": "Scheduled",
        "SCHEDULED": "Scheduled",
        "POSTPONED": "Postponed",
        "CANCELLED": "Cancelled",
    }.get(status, status)


def team_name(team):
    return team.get("shortName") or team["name"]


DAYS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def date_label(d):
    return f"{DAYS_EN[d.weekday()]} {d.strftime('%d/%m')}"


def match_row(match, show_time=False):
    home = team_name(match["homeTeam"])
    away = team_name(match["awayTeam"])
    cell = "padding:6px 8px;white-space:nowrap;"

    if show_time:
        utc_time = datetime.fromisoformat(match["utcDate"].replace("Z", "+00:00"))
        middle = utc_time.astimezone(PARIS).strftime("%H:%M")
    else:
        middle = format_score(match)

    return f"""
        <tr>
          <td style="{cell}text-align:right;font-weight:600;">{home}</td>
          <td style="{cell}text-align:center;font-size:17px;font-weight:700;color:#1a1a2e;padding-left:12px;padding-right:12px;">{middle}</td>
          <td style="{cell}text-align:left;font-weight:600;">{away}</td>
        </tr>"""


def date_header_row(label):
    return f"""
        <tr>
          <td colspan="3" style="padding:12px 8px 4px;font-size:13px;font-weight:700;color:#e63946;text-transform:uppercase;letter-spacing:.05em;">{label}</td>
        </tr>"""


def build_section(title, matches, show_time=False):
    if not matches:
        return f"""
        <h2 style="color:#1a1a2e;border-bottom:2px solid #e63946;padding-bottom:6px;">{title}</h2>
        <p style="color:#888;">No matches.</p>"""

    if show_time:
        # Group by Paris calendar date
        from collections import OrderedDict
        groups = OrderedDict()
        for m in matches:
            utc_time = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00"))
            d = utc_time.astimezone(PARIS).date()
            groups.setdefault(d, []).append(m)

        rows = ""
        for d, group_matches in groups.items():
            rows += date_header_row(date_label(d))
            rows += "".join(match_row(m, show_time=True) for m in group_matches)
    else:
        rows = "".join(match_row(m, show_time=False) for m in matches)

    return f"""
    <h2 style="color:#1a1a2e;border-bottom:2px solid #e63946;padding-bottom:6px;">{title}</h2>
    <table style="width:100%;border-collapse:collapse;font-family:sans-serif;font-size:15px;">
      <tbody>{rows}</tbody>
    </table>"""


def build_html(yesterday_str, today_str, yesterday_matches, today_matches):
    yesterday_section = build_section(
        f"Results — {yesterday_str}", yesterday_matches, show_time=False
    )
    today_section = build_section(
        "Today's fixtures (Paris time)", today_matches, show_time=True
    )

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:sans-serif;max-width:640px;margin:auto;padding:24px;color:#1a1a2e;">
  <h1 style="background:#1a1a2e;color:#fff;padding:16px 20px;border-radius:8px;margin:0 0 24px;">
    ⚽ World Cup 2026 Daily Update
  </h1>
  {yesterday_section}
  <br>
  {today_section}
  <p style="font-size:12px;color:#aaa;margin-top:32px;">
    Data via football-data.org &nbsp;·&nbsp; Delivered by GitHub Actions
  </p>
</body>
</html>"""


def send_email(subject, html_body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = RECIPIENT
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, RECIPIENT, msg.as_string())


def main():
    now_paris = datetime.now(PARIS)
    today = now_paris.date()
    yesterday = today - timedelta(days=1)

    today_str = today.isoformat()
    yesterday_str = yesterday.isoformat()

    print(f"Fetching matches for {yesterday_str}–{today_str} (results) and {today_str} (fixtures)...")

    try:
        # Fetch yesterday + today to catch late US/Canada games that finished overnight Paris time
        all_recent = fetch_matches(yesterday_str, today_str)
        yesterday_matches = [m for m in all_recent if m.get("status") == "FINISHED"]
    except URLError as e:
        print(f"Warning: could not fetch results: {e}")
        yesterday_matches = []

    tomorrow = today + timedelta(days=1)
    tomorrow_str = tomorrow.isoformat()

    try:
        # Fetch today + tomorrow to catch games starting late at night Paris time (US timezones)
        upcoming = fetch_matches(today_str, tomorrow_str)
        today_matches = [
            m for m in upcoming
            if m.get("status") != "FINISHED"
            and datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00")).astimezone(PARIS).date() <= tomorrow
        ]
    except URLError as e:
        print(f"Warning: could not fetch today's matches: {e}")
        today_matches = []

    print(f"Found {len(yesterday_matches)} result(s) and {len(today_matches)} fixture(s).")

    html = build_html(yesterday_str, today_str, yesterday_matches, today_matches)
    subject = f"⚽ World Cup — {yesterday_str} results & {today_str} fixtures"

    send_email(subject, html)
    print("Email sent successfully.")


if __name__ == "__main__":
    main()
