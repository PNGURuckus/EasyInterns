from typing import Dict, Type, List
from .base import SourceScraper, BaseScraper
from ..config import get_settings

class ScraperRegistry:
    """Registry for managing scrapers"""
    
    def __init__(self):
        self._scrapers: Dict[str, Type[BaseScraper]] = {}
        self._initialize_scrapers()
    
    def _initialize_scrapers(self):
        """Initialize all available scrapers"""
        from .indeed import IndeedScraper
        from .job_bank import JobBankScraper
        from .ops import OPSScraper
        from .bcps import BCPSScraper
        from .greenhouse import GreenhouseScraper
        from .lever import LeverScraper
        from .rss import RSSScraper
        from .talent import TalentScraper
        
        # Register all scrapers
        self.register(IndeedScraper)
        self.register(JobBankScraper)
        self.register(OPSScraper)
        self.register(BCPSScraper)
        self.register(GreenhouseScraper)
        self.register(LeverScraper)
        self.register(RSSScraper)
        self.register(TalentScraper)
    
    def register(self, scraper_class: Type[BaseScraper]):
        """Register a scraper class"""
        scraper_instance = scraper_class()
        self._scrapers[scraper_instance.name] = scraper_class
    
    def get_scraper(self, name: str) -> Type[BaseScraper] | None:
        """Get scraper class by name, or None if missing (test-friendly)."""
        return self._scrapers.get(name)
    
    def list_scrapers(self) -> List[Dict[str, any]]:
        """List all registered scrapers with their info"""
        scrapers = []
        settings = get_settings()
        
        for name, scraper_class in self._scrapers.items():
            scraper = scraper_class()
            
            # Check if scraper is enabled
            enabled = True
            if scraper.requires_feature_flag:
                if name == "linkedin" and not getattr(settings, "enable_linkedin_scraper", False):
                    enabled = False
                elif name == "glassdoor" and not getattr(settings, "enable_glassdoor_scraper", False):
                    enabled = False
            
            scrapers.append({
                "name": scraper.name,
                "description": scraper.description,
                "base_url": scraper.base_url,
                "enabled": enabled,
                "requires_feature_flag": scraper.requires_feature_flag
            })
        
        return scrapers
    
    def get_enabled_scrapers(self) -> List[str]:
        """Get list of enabled scraper names"""
        enabled = []
        settings = get_settings()
        
        for name, scraper_class in self._scrapers.items():
            scraper = scraper_class()
            
            # Check if scraper is enabled
            if scraper.requires_feature_flag:
                if name == "linkedin" and not getattr(settings, "enable_linkedin_scraper", False):
                    continue
                elif name == "glassdoor" and not getattr(settings, "enable_glassdoor_scraper", False):
                    continue
            
            enabled.append(name)
        
        return enabled

    def get_available_scrapers(self) -> Dict[str, BaseScraper]:
        """Return enabled scrapers as a name->instance map (for tests)."""
        available: Dict[str, BaseScraper] = {}
        for name in self.get_enabled_scrapers():
            cls = self._scrapers.get(name)
            if cls:
                available[name] = cls()
        return available

    async def _scrape_source(self, name: str, query) -> List:
        cls = self._scrapers.get(name)
        if not cls:
            return []
        scraper = cls()
        try:
            return await scraper.scrape(query)
        except Exception:
            return []

    async def scrape_all_sources(self, query) -> List:
        """Scrape all enabled sources and combine results."""
        import asyncio
        tasks = [self._scrape_source(name, query) for name in self.get_available_scrapers().keys()]
        if not tasks:
            return []
        results = await asyncio.gather(*tasks, return_exceptions=True)
        postings: List = []
        for r in results:
            if isinstance(r, list):
                postings.extend(r)
        return postings

# Global registry instance
_registry = None

def get_scraper_registry() -> ScraperRegistry:
    """Get the global scraper registry"""
    global _registry
    if _registry is None:
        _registry = ScraperRegistry()
    return _registry
