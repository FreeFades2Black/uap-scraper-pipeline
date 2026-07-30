"""Cloud Functions entry point for UAP scraper.

This file sits at the root of the deployment package and imports
the actual scraper logic from src.main.
"""

from src.main import cloud_function_entry

# Cloud Functions will call this function when triggered via HTTP
__all__ = ['cloud_function_entry']