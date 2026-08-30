#!/usr/bin/env python3
"""Send UAP Lakehouse & Scraper Pipeline Analytics Report via Gmail SMTP."""

import argparse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import smtplib
import sys

DEFAULT_FROM = "whall4.wh@gmail.com"
REPORT_SUBJECT = "🛸 UAP Lakehouse & Scraper Pipeline — Medallion Architecture Analytics Report"

PLAIN_TEXT_BODY = """Hi Mark,

Here is the latest intelligence report from the UAP Multi-Source Lakehouse Ingestion Pipeline (FreeFades2Black/uap-scraper-pipeline) after processing through the 3-tier Databricks Medallion architecture (Bronze ➔ Silver ➔ Gold).

======================================================================
🏆 EXECUTIVE SUMMARY & SCORECARD
======================================================================
• Total Ingested Sightings: 1,005 records
• Active Sources: 3 (Kaggle NUFORC, AARO DoD Declassified, NASA Science Directorate)
• Geographic Reach: 797 unique cities across 58 states/territories
• Geocoding Coordinate Coverage: 99.5%
• Historical Date Range: October 10, 1949 – May 20, 2024
• Pipeline Status: Completed with zero stalls (100% throughput across all 3 tiers)

======================================================================
🗺️ TOP 10 GEOGRAPHIC SIGHTINGS (STATE / REGION)
======================================================================
1. California (CA): 89 sightings (69 cities)
2. New York (NY): 58 sightings (41 cities)
3. Washington (WA): 51 sightings (41 cities)
4. Illinois (IL): 48 sightings (29 cities)
5. Texas (TX): 44 sightings (33 cities)
6. Florida (FL): 41 sightings (31 cities)
7. Ohio (OH): 33 sightings (27 cities)
8. Colorado (CO): 32 sightings (23 cities)
9. Michigan (MI): 28 sightings (27 cities)
10. Arizona (AZ): 27 sightings (20 cities)

======================================================================
🛸 OBJECT MORPHOLOGY & SHAPE BREAKDOWN
======================================================================
• Light / Orb: 28.06% (282 sightings)
• Triangle: 9.95% (100 sightings)
• Disk / Saucer: 7.56% (76 sightings)
• Oval / Egg: 6.87% (69 sightings)
• Sphere / Globe: 6.77% (68 sightings)
• Cigar / Cylinder: 4.48% (45 sightings)
• Formation: 3.38% (34 sightings)
• Chevron: 1.49% (15 sightings)
• Diamond: 1.00% (10 sightings)
• Military / Scientific: 0.10% (1 sighting)
• Other / Unspecified: 30.35% (305 sightings)

======================================================================
⚙️ INFRASTRUCTURE & ARCHITECTURE HIGHLIGHTS
======================================================================
• Medallion Ingestion: Automated Bronze raw landing ➔ Silver normalized Delta ➔ Gold business aggregations.
• Containerization: Multi-stage production Docker container with non-root security context (uapuser:10001).
• Orchestration: Scheduled Kubernetes CronJob (every 6 hours) + FastAPI scraper daemon with Prometheus telemetry.
• Resilience: ThreadPool parallel ingestion with SHA-256 deduplication and synthetic fallback.

Repository: https://github.com/FreeFades2Black/uap-scraper-pipeline

Best regards,
Free
"""

HTML_BODY = """<!DOCTYPE html>
<html>
<head>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b; background-color: #f8fafc; margin: 0; padding: 20px; line-height: 1.6; }
  .card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; max-width: 700px; margin: auto; padding: 28px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
  h1 { color: #0f172a; font-size: 22px; border-bottom: 2px solid #3b82f6; padding-bottom: 10px; margin-top: 0; }
  h2 { color: #1e293b; font-size: 16px; margin-top: 24px; border-left: 4px solid #3b82f6; padding-left: 10px; }
  table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 14px; }
  th, td { padding: 8px 12px; border: 1px solid #e2e8f0; text-align: left; }
  th { background-color: #f1f5f9; font-weight: 600; }
  .badge { display: inline-block; padding: 4px 8px; font-size: 12px; font-weight: 600; border-radius: 6px; background-color: #dbeafe; color: #1e40af; }
  .footer { margin-top: 24px; font-size: 13px; color: #64748b; border-top: 1px solid #e2e8f0; padding-top: 14px; }
</style>
</head>
<body>
<div class="card">
  <h1>🛸 UAP Lakehouse & Scraper Pipeline Analytics</h1>
  <p>Hi Mark,</p>
  <p>Here is the latest intelligence report from the <strong>UAP Multi-Source Lakehouse Ingestion Pipeline</strong> (<a href="https://github.com/FreeFades2Black/uap-scraper-pipeline">FreeFades2Black/uap-scraper-pipeline</a>) processed through the 3-tier Databricks Medallion architecture (<strong>Bronze ➔ Silver ➔ Gold</strong>).</p>

  <h2>🏆 Executive Scorecard</h2>
  <table>
    <tr><th>Metric</th><th>Value</th></tr>
    <tr><td>Total Ingested Sightings</td><td><strong>1,005 records</strong></td></tr>
    <tr><td>Active Sources</td><td>3 (Kaggle NUFORC, AARO DoD, NASA Science)</td></tr>
    <tr><td>Geographic Coverage</td><td>797 cities across 58 states/territories</td></tr>
    <tr><td>Coordinate Coverage</td><td><strong>99.5%</strong></td></tr>
    <tr><td>Historical Date Range</td><td>Oct 10, 1949 – May 20, 2024</td></tr>
    <tr><td>Throughput Status</td><td><span class="badge">✅ 100% Zero-Stall</span></td></tr>
  </table>

  <h2>🗺️ Top 10 Sightings by Region</h2>
  <table>
    <tr><th>Rank</th><th>State / Region</th><th>Sightings</th><th>Cities</th></tr>
    <tr><td>1</td><td>California (CA)</td><td>89</td><td>69</td></tr>
    <tr><td>2</td><td>New York (NY)</td><td>58</td><td>41</td></tr>
    <tr><td>3</td><td>Washington (WA)</td><td>51</td><td>41</td></tr>
    <tr><td>4</td><td>Illinois (IL)</td><td>48</td><td>29</td></tr>
    <tr><td>5</td><td>Texas (TX)</td><td>44</td><td>33</td></tr>
    <tr><td>6</td><td>Florida (FL)</td><td>41</td><td>31</td></tr>
    <tr><td>7</td><td>Ohio (OH)</td><td>33</td><td>27</td></tr>
    <tr><td>8</td><td>Colorado (CO)</td><td>32</td><td>23</td></tr>
    <tr><td>9</td><td>Michigan (MI)</td><td>28</td><td>27</td></tr>
    <tr><td>10</td><td>Arizona (AZ)</td><td>27</td><td>20</td></tr>
  </table>

  <h2>🛸 Phenomenon Shape Distribution</h2>
  <table>
    <tr><th>Shape</th><th>Count</th><th>% Share</th></tr>
    <tr><td>Light / Orb</td><td>282</td><td>28.06%</td></tr>
    <tr><td>Triangle</td><td>100</td><td>9.95%</td></tr>
    <tr><td>Disk / Saucer</td><td>76</td><td>7.56%</td></tr>
    <tr><td>Oval / Egg</td><td>69</td><td>6.87%</td></tr>
    <tr><td>Sphere / Globe</td><td>68</td><td>6.77%</td></tr>
    <tr><td>Cigar / Cylinder</td><td>45</td><td>4.48%</td></tr>
    <tr><td>Formation</td><td>34</td><td>3.38%</td></tr>
    <tr><td>Other / Unspecified</td><td>305</td><td>30.35%</td></tr>
  </table>

  <h2>⚙️ Architecture Highlights</h2>
  <ul>
    <li><strong>Databricks Medallion:</strong> Bronze Raw ➔ Silver Normalized ➔ Gold Analytics</li>
    <li><strong>Production Containers:</strong> Multi-stage Docker with non-root security context (<code>uapuser:10001</code>)</li>
    <li><strong>Kubernetes Orchestration:</strong> Scheduled <code>CronJob</code> (every 6h) + FastAPI daemon with Prometheus <code>/metrics</code></li>
    <li><strong>Fault-Tolerance:</strong> ThreadPool parallel scraping with SHA-256 deduplication and synthetic fallback</li>
  </ul>

  <div class="footer">
    <p>Repository: <a href="https://github.com/FreeFades2Black/uap-scraper-pipeline">https://github.com/FreeFades2Black/uap-scraper-pipeline</a></p>
    <p>Best regards,<br><strong>Free</strong></p>
  </div>
</div>
</body>
</html>
"""


def send_email(recipient: str, sender: str, app_password: str):
    """Send MIME multipart email using Gmail SMTP SSL."""
    print(f"Connecting to Gmail SMTP server (smtp.gmail.com:465)...")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = REPORT_SUBJECT
    msg["From"] = f"Free <{sender}>"
    msg["To"] = recipient

    msg.attach(MIMEText(PLAIN_TEXT_BODY, "plain", "utf-8"))
    msg.attach(MIMEText(HTML_BODY, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, app_password)
            server.sendmail(sender, [recipient], msg.as_string())
        print(f"✅ Successfully sent UAP report email to: {recipient}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email via Gmail: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Send UAP analytics report via Gmail")
    parser.add_argument("--to", required=True, help="Recipient email address (Mark Schoier)")
    parser.add_argument("--from-email", default=os.getenv("GMAIL_USER", DEFAULT_FROM), help="Sender Gmail address")
    parser.add_argument("--password", default=os.getenv("GMAIL_APP_PASSWORD"), help="Gmail 16-character App Password")

    args = parser.parse_args()

    if not args.password:
        print("❌ Error: Gmail App Password is required.")
        print("   Generate a 16-character password at: https://myaccount.google.com/apppasswords")
        print("   Pass it via --password '<passkey>' or export GMAIL_APP_PASSWORD='<passkey>'")
        sys.exit(1)

    success = send_email(recipient=args.to, sender=args.from_email, app_password=args.password)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
