# World Cup 2026 Daily Email Update

A GitHub Actions automation that sends you a daily email at 8am with:
- **Yesterday's match results**
- **Today's scheduled fixtures**
- **The latest standings in each group**

No server required — runs entirely on GitHub's free infrastructure.

## How it works

Every morning, a GitHub Actions workflow runs a Python script that:
1. Fetches match data from the [football-data.org](https://www.football-data.org/) free API
2. Formats it into an HTML email
3. Sends it via Gmail SMTP

## Set it up for yourself

### 1. Fork this repository

Click **Fork** at the top right of this page.

### 2. Get a football-data.org API key

Sign up for free at [football-data.org/client/register](https://www.football-data.org/client/register). You'll receive your API key by email.

### 3. Create a Gmail App Password

In your Google account:
- Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
- Give it a name (e.g. `worldcup-github`)
- Click **Create** and copy the 16-character code

> This requires 2-Step Verification to be enabled on your Google account.

### 4. Add GitHub Secrets

In your forked repo: **Settings → Secrets and variables → Actions → New repository secret**

Add these 4 secrets:

| Name | Value |
|---|---|
| `FOOTBALL_API_KEY` | Your key from football-data.org |
| `GMAIL_USER` | Your Gmail address (e.g. `you@gmail.com`) |
| `GMAIL_APP_PASSWORD` | The 16-character app password |
| `RECIPIENT_EMAIL` | The address where you want to receive emails |

### 5. Test it

Go to **Actions → Daily World Cup Update → Run workflow** to trigger it immediately and verify the email arrives.

From then on, it runs automatically every morning at 8am Paris time (CEST).

## Timezone

The cron is set to `0 6 * * *` (6am UTC = 8am CEST). If you're in a different timezone, update the cron expression in `.github/workflows/daily_worldcup.yml` accordingly.

| Timezone | Cron for 8am |
|---|---|
| Paris / Berlin (CEST, summer) | `0 6 * * *` |
| London (BST, summer) | `0 7 * * *` |
| New York (EDT, summer) | `0 12 * * *` |
| Los Angeles (PDT, summer) | `0 15 * * *` |
