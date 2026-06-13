import requests
import smtplib
import os
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, datetime


# ── Email helper ──────────────────────────────────────────────
def send_email(subject, body, html=False):
    sender = os.environ["GMAIL_ADDRESS"]
    password = os.environ["GMAIL_APP_PASSWORD"]
   receivers = [
        os.environ["GMAIL_ADDRESS"],  #njan
        "juaeljw@gmail.com",
        "ganeshgopal3106@gmail.com",
    ]
    msg = MIMEMultipart("alternative")
    msg["From"] = sender
    msg["To"] = ", ".join(receivers)
    msg["Subject"] = subject

    mime_type = "html" if html else "plain"
    msg.attach(MIMEText(body, mime_type))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, receivers, msg.as_string())
    print(f"Email sent: {subject}")


# ── Weather (wttr.in) ─────────────────────────────────────────
def get_weather(city="Thiruvananthapuram"):
    url = f"https://wttr.in/{city}?format=3"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text.strip()
    except Exception as e:
        return f"Weather Unavailable ({e})"


# ── Task 1: OpenWeatherMap alert ──────────────────────────────
def check_weather_alert():
    api_key = os.environ.get("OWM_API_KEY", "")
    if not api_key:
        print("No OWM_API_KEY set, skipping weather alert.")
        return

    city = "Thiruvananthapuram"
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        temp = data["main"]["temp"]
        description = data["weather"][0]["description"].lower()
        feels_like = data["main"]["feels_like"]

        alert_needed = temp > 35 or "rain" in description

        print(f"Weather check — Temp: {temp}°C, Condition: {description}, Alert needed: {alert_needed}")

        if alert_needed:
            reasons = []
            if temp > 35:
                reasons.append(f"Temperature is {temp}°C (feels like {feels_like}°C)")
            if "rain" in description:
                reasons.append(f"Rain predicted: {description}")

            body = f"""⚠️ PULSE WEATHER ALERT — {city}

{chr(10).join(reasons)}

Stay hydrated and carry an umbrella if needed!

— Pulse Bot
"""
            send_email(f"⚠️ Pulse Weather Alert — {city}", body)
        else:
            print(f"No alert needed. Temp: {temp}°C, {description}")

    except Exception as e:
        print(f"Weather alert error: {e}")


# ── Task 2: News scraper (RSS feeds) ─────────────────────────
def get_news_headlines():
    import xml.etree.ElementTree as ET

    sources = [
        {"name": "BBC News", "url": "http://feeds.bbci.co.uk/news/world/rss.xml"},
        {"name": "Reuters", "url": "https://feeds.reuters.com/reuters/topNews"},
        {"name": "The Hindu", "url": "https://www.thehindu.com/news/national/feeder/default.rss"},
    ]

    all_articles = []

    for source in sources:
        try:
            response = requests.get(source["url"], timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            root = ET.fromstring(response.content)
            items = root.findall(".//item")[:3]  # top 3 per source

            for item in items:
                title = item.findtext("title", "No title").strip()
                link = item.findtext("link", "#").strip()
                pub_date = item.findtext("pubDate", "Unknown time").strip()
                all_articles.append({
                    "source": source["name"],
                    "title": title,
                    "link": link,
                    "pub_date": pub_date,
                })
            print(f"Fetched {len(items)} articles from {source['name']}")
        except Exception as e:
            print(f"News error ({source['name']}): {e}")

    return all_articles


def build_news_html(articles):
    today = date.today().strftime("%A, %B %d %Y")
    rows = ""
    current_source = ""

    for a in articles:
        if a["source"] != current_source:
            current_source = a["source"]
            rows += f"""
            <tr>
              <td colspan="2" style="background:#1a1a2e;color:#a29bfe;padding:10px 16px;font-size:11px;
                  text-transform:uppercase;letter-spacing:0.1em;font-weight:700;">
                {current_source}
              </td>
            </tr>"""

        rows += f"""
            <tr>
              <td style="padding:12px 16px;border-bottom:1px solid #2a2a30;vertical-align:top;">
                <a href="{a['link']}" style="color:#e8e8f0;text-decoration:none;font-weight:500;
                    font-size:14px;line-height:1.4;">{a['title']}</a>
                <div style="color:#8888a0;font-size:11px;margin-top:4px;">{a['pub_date']}</div>
              </td>
            </tr>"""

    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#0d0d0f;font-family:'Inter',Arial,sans-serif;">
  <div style="max-width:600px;margin:32px auto;background:#18181c;border:1px solid #2a2a30;
      border-radius:10px;overflow:hidden;">

    <div style="background:#111114;padding:24px 32px;border-bottom:1px solid #2a2a30;">
      <div style="color:#6c63ff;font-size:11px;text-transform:uppercase;letter-spacing:0.12em;
          font-weight:700;margin-bottom:6px;">Pulse — Daily News</div>
      <div style="color:#e8e8f0;font-size:22px;font-weight:800;">{today}</div>
    </div>

    <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
      {rows}
    </table>

    <div style="padding:16px 32px;border-top:1px solid #2a2a30;text-align:center;">
      <span style="color:#8888a0;font-size:11px;">Built by Gavin Satheesh · Pulse Bot</span>
    </div>

  </div>
</body>
</html>"""
    return html


def send_news_email():
    articles = get_news_headlines()
    if not articles:
        print("No articles fetched, skipping news email.")
        return
    html = build_news_html(articles)
    today = date.today().strftime("%A, %B %d %Y")
    send_email(f"Pulse — Morning Headlines | {today}", html, html=True)


# ── Task 3: GitHub repos → projects.json ─────────────────────
def update_projects_json():
    github_token = os.environ.get("GITHUB_TOKEN", "")
    username = "gavinsatheesh"

    headers = {"Accept": "application/vnd.github+json"}
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    url = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=20"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        repos = response.json()

        projects = []
        for repo in repos:
            if repo["fork"]:
                continue  # skip forks
            projects.append({
                "name": repo["name"],
                "description": repo["description"] or "",
                "url": repo["html_url"],
                "language": repo["language"] or "N/A",
                "stars": repo["stargazers_count"],
                "updated": repo["updated_at"][:10],
            })

        with open("projects.json", "w", encoding="utf-8") as f:
            json.dump(projects, f, indent=2)

        print(f"projects.json updated with {len(projects)} repos.")

    except Exception as e:
        print(f"GitHub API error: {e}")


# ── Quote ─────────────────────────────────────────────────────
def get_quote():
    url = "https://zenquotes.io/api/random"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return f'"{data[0]["q"]}" - {data[0]["a"]}'
    except Exception as e:
        return f"Quote Unavailable ({e})"


# ── Daily summary email ───────────────────────────────────────
def build_summary():
    today = date.today().strftime("%A, %B %d %Y")
    weather = get_weather()
    quote = get_quote()

    summary = f"""
==================================
    PULSE — Daily Summary
    {today}
==================================

  WEATHER
  {weather}

  TODAY'S QUOTE
  {quote}

==================================
    Built by Gavin Satheesh
==================================
"""
    return summary


# ── Main ──────────────────────────────────────────────────────
def run():
    print("=== Pulse Bot Starting ===")

    # Daily summary email
    summary = build_summary()
    print(summary)
    with open("daily_summary.txt", "w", encoding="utf-8") as f:
        f.write(summary)
    today = date.today().strftime("%A, %B %d %Y")
    send_email(f"Pulse — Daily Summary | {today}", summary)

    # Task 1: Weather alert
    check_weather_alert()

    # Task 2: News headlines email
    send_news_email()

    # Task 3: Update projects.json
    update_projects_json()

    print("=== Pulse ran successfully! ===")


if __name__ == "__main__":
    run()
