"""Generate realistic UAP sighting test data for pipeline testing.

Use this when NUFORC scraping is blocked. Generates structured JSON
that matches the expected UAP sighting schema.
"""

import random
from datetime import datetime, timedelta, timezone

def generate_uap_sightings(count=50):
    """Generate realistic UAP sighting records.
    
    Args:
        count: Number of sightings to generate
        
    Returns:
        dict: Structured payload matching NUFORC scraper output format
    """
    
    # Realistic UAP shapes from NUFORC taxonomy
    shapes = [
        "Light", "Triangle", "Circle", "Sphere", "Disk", "Oval", 
        "Cigar", "Diamond", "Rectangle", "Chevron", "Formation",
        "Fireball", "Flash", "Unknown", "Other"
    ]
    
    # US states and major cities
    locations = [
        ("Phoenix", "AZ"), ("Los Angeles", "CA"), ("San Diego", "CA"),
        ("Denver", "CO"), ("Miami", "FL"), ("Atlanta", "GA"),
        ("Chicago", "IL"), ("Boston", "MA"), ("Detroit", "MI"),
        ("Las Vegas", "NV"), ("New York", "NY"), ("Portland", "OR"),
        ("Philadelphia", "PA"), ("Seattle", "WA"), ("Houston", "TX"),
        ("Austin", "TX"), ("Dallas", "TX"), ("Salt Lake City", "UT")
    ]
    
    durations = [
        "2-3 seconds", "5 seconds", "10 seconds", "30 seconds",
        "1 minute", "2 minutes", "5 minutes", "10 minutes",
        "15 minutes", "30 minutes", "1 hour", "2 hours"
    ]
    
    summaries = [
        "Bright light moving erratically across the sky",
        "Multiple lights in formation, silent, moving rapidly",
        "Large triangular craft with lights on each corner",
        "Disk-shaped object hovering then accelerating instantly",
        "Glowing sphere changing colors, red to blue to white",
        "Cigar-shaped craft with no wings or propulsion visible",
        "Chevron-shaped formation of lights moving in unison",
        "Bright flash followed by rapid departure",
        "Silent craft with rotating lights, low altitude",
        "Multiple spheres performing impossible maneuvers",
        "Large craft blocking out stars as it passed overhead",
        "Pulsating light descending then shooting upward"
    ]
    
    sightings = []
    
    # Generate sightings from the past 30 days
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=30)
    
    for i in range(count):
        # Random date/time in past 30 days
        random_seconds = random.randint(0, int((end_date - start_date).total_seconds()))
        sighting_time = start_date + timedelta(seconds=random_seconds)
        
        city, state = random.choice(locations)
        
        sighting = {
            "date_time": sighting_time.strftime("%m/%d/%Y %H:%M"),
            "city": city,
            "state": state,
            "country": "USA",
            "shape": random.choice(shapes),
            "duration": random.choice(durations),
            "summary": random.choice(summaries),
            "report_link": None
        }
        
        sightings.append(sighting)
    
    # Sort by date descending (most recent first)
    sightings.sort(key=lambda x: datetime.strptime(x["date_time"], "%m/%d/%Y %H:%M"), reverse=True)
    
    payload = {
        "source": "NUFORC_TEST_DATA",
        "source_url": "generated",
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "sighting_count": len(sightings),
        "sightings": sightings,
        "note": "Generated test data for pipeline validation"
    }
    
    return payload


if __name__ == "__main__":
    # Generate 100 test sightings
    import json
    data = generate_uap_sightings(100)
    print(json.dumps(data, indent=2))
