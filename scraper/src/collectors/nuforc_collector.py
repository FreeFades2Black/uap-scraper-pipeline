"""NUFORC (National UFO Reporting Center) Collector.

Scrapes sighting data from nuforc.org with enhanced anti-blocking measures,
session reuse, and resilient table parsing.
"""

from datetime import datetime, timezone
import time
from typing import Dict
from bs4 import BeautifulSoup
from .base import BaseCollector


class NUFORCCollector(BaseCollector):
    """Collects UAP data from NUFORC.org."""

    def __init__(self):
        super().__init__("NUFORC", timeout=30)
        self.base_urls = [
            "https://www.nuforc.org/webreports/ndxevent.html",
            "https://nuforc.org/webreports/ndxevent.html",
            "http://www.nuforc.org/webreports/ndxevent.html",
            "https://nuforc.org/webreports/ndxe.html"
        ]

    def collect(self) -> Dict:
        """Scrape NUFORC sighting reports with fallback URLs and anti-blocking."""
        all_sightings = []
        last_error = None
        session = self.get_session()

        for url in self.base_urls:
            try:
                self.logger.info(f"Attempting NUFORC scrape: {url}")
                headers = self.get_headers({"Referer": "https://www.google.com/"})

                response = session.get(
                    url,
                    headers=headers,
                    timeout=self.timeout,
                    allow_redirects=True
                )

                if response.status_code == 403:
                    self.logger.warning(f"403 Forbidden from {url} - backing off")
                    last_error = "403 Forbidden"
                    time.sleep(2)
                    continue

                if response.status_code != 200:
                    self.logger.warning(f"Unexpected status {response.status_code} from {url}")
                    last_error = f"HTTP {response.status_code}"
                    continue

                # Parse HTML table
                soup = BeautifulSoup(response.text, "html.parser")
                table = soup.find("table")

                if not table:
                    # Look for alternative table selectors
                    tables = soup.find_all("table")
                    if tables:
                        table = tables[0]

                if not table:
                    self.logger.warning(f"No table structure found at {url}")
                    continue

                rows = table.find_all("tr")
                self.logger.info(f"Found {len(rows)} table rows at {url}")

                for row in rows[1:]:  # Skip header row
                    cols = row.find_all("td")
                    if len(cols) < 5:
                        continue

                    date_text = cols[0].get_text(strip=True)
                    city_text = cols[1].get_text(strip=True) if len(cols) > 1 else "Unknown"
                    state_text = cols[2].get_text(strip=True) if len(cols) > 2 else "Unknown"
                    country_text = cols[3].get_text(strip=True) if len(cols) > 3 else "USA"
                    shape_text = cols[4].get_text(strip=True) if len(cols) > 4 else "Unknown"
                    duration_text = cols[5].get_text(strip=True) if len(cols) > 5 else "Unknown"
                    summary_text = cols[6].get_text(strip=True) if len(cols) > 6 else ""

                    # Extract link
                    report_link = None
                    link_elem = cols[0].find("a")
                    if link_elem and link_elem.get("href"):
                        href = link_elem["href"]
                        report_link = f"https://www.nuforc.org/webreports/{href}" if not href.startswith("http") else href

                    raw_item = {
                        "date_time": date_text,
                        "city": city_text,
                        "state": state_text,
                        "country": country_text,
                        "shape": shape_text,
                        "duration": duration_text,
                        "summary": summary_text,
                        "report_link": report_link
                    }
                    all_sightings.append(self.normalize_sighting(raw_item))

                if all_sightings:
                    self.logger.info(f"✅ Successfully scraped {len(all_sightings)} records from NUFORC")
                    break

            except Exception as e:
                last_error = str(e)
                self.logger.warning(f"Failed scraping {url}: {e}")
                continue

        return {
            "source": "NUFORC",
            "source_url": self.base_urls[0],
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "sighting_count": len(all_sightings),
            "sightings": all_sightings,
            "error": last_error if len(all_sightings) == 0 else None
        }
