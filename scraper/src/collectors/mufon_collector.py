"""MUFON (Mutual UFO Network) Collector.

Collects publicly accessible reports and structured summary feeds from MUFON.
"""

from datetime import datetime, timezone
from typing import Dict
from bs4 import BeautifulSoup
from .base import BaseCollector


class MUFONCollector(BaseCollector):
    """Collects UAP data from MUFON public records."""

    def __init__(self):
        super().__init__("MUFON", timeout=30)
        self.api_url = "https://mufon.com/mufon-ufo-reports/"
        self.feed_url = "https://mufon.com/feed/"

    def collect(self) -> Dict:
        """Collect public MUFON sighting reports."""
        all_sightings = []
        last_error = None

        session = self.get_session()
        headers = self.get_headers()

        # Try RSS feed first (more structured and reliable)
        try:
            response = session.get(self.feed_url, headers=headers, timeout=self.timeout)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "xml")
                items = soup.find_all("item")
                for item in items[:30]:
                    title = item.find("title").get_text(strip=True) if item.find("title") else "MUFON Report"
                    pub_date = item.find("pubDate").get_text(strip=True) if item.find("pubDate") else str(datetime.now(timezone.utc))
                    link = item.find("link").get_text(strip=True) if item.find("link") else self.api_url
                    desc = item.find("description").get_text(strip=True) if item.find("description") else ""

                    raw_data = {
                        "date_time": pub_date,
                        "city": "Unknown",
                        "state": "Unknown",
                        "country": "USA",
                        "shape": "Aerial Anomaly",
                        "duration": "Unspecified",
                        "summary": f"{title} - {desc}"[:400],
                        "report_link": link
                    }
                    all_sightings.append(self.normalize_sighting(raw_data))

                if all_sightings:
                    self.logger.info(f"✅ Collected {len(all_sightings)} reports from MUFON RSS feed")
        except Exception as e:
            self.logger.warning(f"MUFON RSS feed attempt failed: {e}")
            last_error = str(e)

        # If RSS returned nothing, try main web report index
        if not all_sightings:
            try:
                response = session.get(self.api_url, headers=headers, timeout=self.timeout)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    links = soup.find_all("a", href=lambda h: h and "/ufo-" in h)
                    for l in links[:15]:
                        raw_data = {
                            "date_time": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                            "city": "Unknown",
                            "state": "Unknown",
                            "country": "USA",
                            "shape": "MUFON Case Entry",
                            "duration": "Unknown",
                            "summary": l.get_text(strip=True)[:250],
                            "report_link": l["href"] if l["href"].startswith("http") else f"https://mufon.com{l['href']}"
                        }
                        all_sightings.append(self.normalize_sighting(raw_data))
            except Exception as web_err:
                last_error = str(web_err)
                self.logger.warning(f"MUFON web scrape failed: {web_err}")

        return {
            "source": "MUFON",
            "source_url": self.api_url,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "sighting_count": len(all_sightings),
            "sightings": all_sightings,
            "error": last_error if len(all_sightings) == 0 else None
        }
