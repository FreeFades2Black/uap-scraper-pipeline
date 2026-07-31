"""NUFORC (National UFO Reporting Center) Collector.

Scrapes sighting data from nuforc.org with enhanced anti-blocking measures.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import time
from typing import Dict
from .base import BaseCollector


class NUFORCCollector(BaseCollector):
    """Collects UAP data from NUFORC.org."""
    
    def __init__(self):
        super().__init__("NUFORC")
        self.base_urls = [
            "https://www.nuforc.org/webreports/ndxevent.html",
            "http://www.nuforc.org/webreports/ndxevent.html",
            "https://nuforc.org/webreports/ndxevent.html"
        ]
        self.timeout = 30
    
    def _get_headers(self) -> dict:
        """Generate browser-like headers."""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Referer': 'https://www.nuforc.org/',
            'Cache-Control': 'max-age=0'
        }
    
    def collect(self) -> Dict:
        """Scrape NUFORC sighting reports."""
        
        all_sightings = []
        last_error = None
        
        # Try multiple URLs
        for url in self.base_urls:
            try:
                self.logger.info(f"Attempting: {url}")
                
                response = requests.get(
                    url,
                    headers=self._get_headers(),
                    timeout=self.timeout,
                    allow_redirects=True
                )
                
                if response.status_code == 403:
                    self.logger.warning(f"403 Forbidden from {url}")
                    last_error = "403 Forbidden"
                    time.sleep(3)  # Wait before next attempt
                    continue
                
                response.raise_for_status()
                
                # Parse HTML
                soup = BeautifulSoup(response.text, "html.parser")
                table = soup.find("table")
                
                if not table:
                    self.logger.warning(f"No table found at {url}")
                    continue
                
                rows = table.find_all("tr")
                self.logger.info(f"Found {len(rows)} rows")
                
                # Parse rows
                for row in rows[1:]:  # Skip header
                    cols = row.find_all("td")
                    if len(cols) < 6:
                        continue
                    
                    sighting = {
                        "date_time": cols[0].get_text(strip=True),
                        "city": cols[1].get_text(strip=True),
                        "state": cols[2].get_text(strip=True),
                        "country": cols[3].get_text(strip=True),
                        "shape": cols[4].get_text(strip=True),
                        "duration": cols[5].get_text(strip=True),
                        "summary": cols[6].get_text(strip=True) if len(cols) > 6 else "",
                        "report_link": None
                    }
                    
                    # Extract link if available
                    link = cols[0].find("a")
                    if link and link.get("href"):
                        sighting["report_link"] = f"https://www.nuforc.org{link['href']}"
                    
                    all_sightings.append(sighting)
                
                self.logger.info(f"✅ Successfully scraped {len(all_sightings)} from NUFORC")
                break  # Success! Stop trying other URLs
                
            except Exception as e:
                last_error = str(e)
                self.logger.warning(f"Failed {url}: {e}")
                continue
        
        return {
            "source": "NUFORC",
            "source_url": self.base_urls[0],
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "sighting_count": len(all_sightings),
            "sightings": all_sightings,
            "error": last_error if len(all_sightings) == 0 else None
        }
