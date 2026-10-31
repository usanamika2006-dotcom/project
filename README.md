# Memzo Subscription Management

A Flask and SQLite subscription management app for the Brightloop Software business scenario, with public product discovery and separate Admin, Staff, and Customer experiences.

## Setup

1. Create and activate a Python virtual environment.
2. Install dependencies with `python -m pip install -r requirements.txt`.
3. Set a persistent, random `SECRET_KEY` before launch. Create the first Admin at `/setup`, or set `ADMIN_EMAIL` and `ADMIN_PASSWORD` and run `python -m flask --app app create-admin`.
4. Run `python app.py` and open the local address printed by Flask.

SQLite database tables are initialized automatically on first run in `instance/brightloop.db`. The database file is kept locally and is not committed. For password-reset email delivery, configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, and optionally `MAIL_FROM`; reset tokens expire after one hour and can only be used once.

Run `python -m flask --app app process-renewals` regularly (for example, once per day from a scheduler) to close expired auto-close subscriptions and create deduplicated renewal reminders for customers.

## Prototype notes

Checkout uses simulated payment outcomes only; no real payment gateway is connected. Use the first-run setup page to create the initial administrator, then create staff accounts through Admin. Public registration creates customer accounts only.
