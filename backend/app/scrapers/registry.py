from typing import Dict, Type, List, Optional
from .base import BaseScraper, ScrapeQuery, RawPosting
import logging

logger = logging.getLogger(__name__)

class ScraperRegistry:
    """Registry for all available scrapers"""
    
    def __init__(self):
        self._scrapers: Dict[str, Type[BaseScraper]] = {}
    
    def register(self, scraper_class: Type[BaseScraper]) -> None:
        """Register a new scraper class"""
        if not issubclass(scraper_class, BaseScraper):
            raise ValueError(f"{scraper_class.__name__} is not a subclass of BaseScraper")
        
        name = scraper_class.__name__.lower().replace('scraper', '')
        self._scrapers[name] = scraper_class
        logger.info(f"Registered scraper: {name}")
    
    def get_scraper(self, name: str) -> Optional[Type[BaseScraper]]:
        """Get a scraper class by name"""
        return self._scrapers.get(name.lower())
    
    def get_available_scrapers(self) -> List[str]:
        """Get a list of all registered scraper names"""
        return list(self._scrapers.keys())
    
    async def scrape_all(
        self, 
        query: ScrapeQuery, 
        scraper_names: Optional[List[str]] = None
    ) -> Dict[str, List[RawPosting]]:
        """
        Run multiple scrapers in parallel
        
        Args:
            query: Search query parameters
            scraper_names: Optional list of scraper names to use. If None, uses all scrapers.
            
        Returns:
            Dictionary mapping scraper names to lists of job postings
        """
        import asyncio
        
        if scraper_names is None:
            scraper_names = self.get_available_scrapers()
        
        # Filter to only requested and available scrapers
        scrapers_to_run = [
            (name, self._scrapers[name])
            for name in scraper_names
            if name in self._scrapers
        ]
        
        # Run scrapers in parallel
        tasks = []
        for name, scraper_class in scrapers_to_run:
            logger.info(f"Starting scraper: {name}")
            scraper = scraper_class()
            tasks.append(scraper.scrape(query))
        
        # Gather results
        results = {}
        completed = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for (name, _), result in zip(scrapers_to_run, completed):
            if isinstance(result, Exception):
                logger.error(f"Scraper {name} failed: {str(result)}")
                results[name] = []
            else:
                results[name] = result
        
        return results

# Create a global registry instance
scraper_registry = ScraperRegistry()

def register_scraper(scraper_class: Type[BaseScraper]) -> Type[BaseScraper]:
    """Class decorator to register a scraper"""
    scraper_registry.register(scraper_class)
    return scraper_class
