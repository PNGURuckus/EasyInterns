"""
Scrapers module for collecting internship postings from various sources.

This module contains implementations of scrapers for different job boards and platforms.
Each scraper follows the BaseScraper interface and is registered in the scraper registry.
"""

from .base import BaseScraper, ScrapeQuery, RawPosting
from .registry import ScraperRegistry
from .indeed import IndeedScraper
from .job_bank import JobBankScraper
from .ops import OPSScraper
from .bcps import BCPSScraper
from .greenhouse import GreenhouseScraper
from .lever import LeverScraper
from .rss import RSSScraper

# Initialize the scraper registry
scraper_registry = ScraperRegistry()

# Register all scrapers
scraper_registry.register(IndeedScraper)
scraper_registry.register(JobBankScraper)
scraper_registry.register(OPSScraper)
scraper_registry.register(BCPSScraper)
scraper_registry.register(GreenhouseScraper)
scraper_registry.register(LeverScraper)
scraper_registry.register(RSSScraper)

__all__ = [
    'BaseScraper',
    'ScrapeQuery',
    'RawPosting',
    'ScraperRegistry',
    'scraper_registry',
    'IndeedScraper',
    'JobBankScraper',
    'OPSScraper',
    'BCPSScraper',
    'GreenhouseScraper',
    'LeverScraper',
    'RSSScraper'
]
