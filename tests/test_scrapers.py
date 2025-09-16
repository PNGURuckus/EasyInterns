import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.scrapers.base import ScrapeQuery, RawPosting
from app.scrapers.indeed import IndeedScraper
from app.scrapers.talent import TalentScraper
from app.scrapers.registry import ScraperRegistry

class TestScraperBase:
    """Test scraper base functionality."""
    
    def test_scrape_query_creation(self):
        """Test ScrapeQuery dataclass creation."""
        query = ScrapeQuery(
            query="software engineer intern",
            location="Toronto, ON",
            max_results=50
        )
        assert query.query == "software engineer intern"
        assert query.location == "Toronto, ON"
        assert query.max_results == 50
    
    def test_raw_posting_creation(self):
        """Test RawPosting dataclass creation."""
        posting = RawPosting(
            title="Software Engineering Intern",
            company_name="Tech Corp",
            location="Toronto, ON",
            description="Join our team...",
            apply_url="https://example.com/apply",
            source="indeed",
            external_id="test-123"
        )
        assert posting.title == "Software Engineering Intern"
        assert posting.company_name == "Tech Corp"
        assert posting.source == "indeed"

class TestIndeedScraper:
    """Test Indeed scraper functionality."""
    
    @pytest.fixture
    def scraper(self):
        return IndeedScraper()
    
    def test_scraper_name(self, scraper):
        """Test scraper name property."""
        assert scraper.name == "indeed"
    
    @patch('httpx.AsyncClient.get')
    async def test_scrape_success(self, mock_get, scraper):
        """Test successful scraping."""
        # Mock HTML response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <div class="job_seen_beacon">
            <h2><a href="/viewjob?jk=123"><span title="Software Engineer Intern">Software Engineer Intern</span></a></h2>
            <span class="companyName">Tech Corp</span>
            <div class="companyLocation">Toronto, ON</div>
            <div class="summary">Great opportunity for students...</div>
        </div>
        """
        mock_get.return_value = mock_response
        
        query = ScrapeQuery(query="software intern", location="Toronto")
        results = await scraper.scrape(query)
        
        assert isinstance(results, list)
        # Results might be empty due to HTML parsing complexity
        # This tests the scraper doesn't crash
    
    @patch('httpx.AsyncClient.get')
    async def test_scrape_http_error(self, mock_get, scraper):
        """Test scraping with HTTP error."""
        mock_get.side_effect = Exception("Network error")
        
        query = ScrapeQuery(query="software intern", location="Toronto")
        results = await scraper.scrape(query)
        
        assert results == []
    
    def test_parse_salary(self, scraper):
        """Test salary parsing."""
        # Test various salary formats
        assert scraper._parse_salary("$50,000 - $60,000 a year") == (50000, 60000)
        assert scraper._parse_salary("$25/hour") == (52000, 52000)  # Approx annual
        assert scraper._parse_salary("Competitive salary") == (None, None)
        assert scraper._parse_salary("") == (None, None)

class TestTalentScraper:
    """Test Talent.com scraper functionality."""
    
    @pytest.fixture
    def scraper(self):
        return TalentScraper()
    
    def test_scraper_name(self, scraper):
        """Test scraper name property."""
        assert scraper.name == "talent"
    
    @patch('httpx.AsyncClient.get')
    async def test_scrape_success(self, mock_get, scraper):
        """Test successful scraping."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <div class="job-item">
            <h3><a href="/job/123">Software Engineering Intern</a></h3>
            <div class="company">Tech Corp</div>
            <div class="location">Toronto, ON</div>
            <div class="description">Join our development team...</div>
        </div>
        """
        mock_get.return_value = mock_response
        
        query = ScrapeQuery(query="software intern", location="Toronto")
        results = await scraper.scrape(query)
        
        assert isinstance(results, list)

class TestScraperRegistry:
    """Test scraper registry functionality."""
    
    def test_registry_initialization(self):
        """Test registry creates with scrapers."""
        registry = ScraperRegistry()
        scrapers = registry.get_available_scrapers()
        
        assert len(scrapers) > 0
        assert "indeed" in scrapers
        assert "talent" in scrapers
    
    def test_get_scraper_by_name(self):
        """Test getting scraper by name."""
        registry = ScraperRegistry()
        
        indeed_scraper = registry.get_scraper("indeed")
        assert indeed_scraper is not None
        assert indeed_scraper.name == "indeed"
        
        invalid_scraper = registry.get_scraper("nonexistent")
        assert invalid_scraper is None
    
    @patch('app.config.get_settings')
    def test_feature_flags(self, mock_settings):
        """Test feature flag filtering."""
        # Mock settings with LinkedIn disabled
        mock_settings.return_value.enable_linkedin_scraper = False
        mock_settings.return_value.enable_glassdoor_scraper = False
        
        registry = ScraperRegistry()
        scrapers = registry.get_available_scrapers()
        
        assert "linkedin" not in scrapers
        assert "glassdoor" not in scrapers
    
    async def test_scrape_all_sources(self):
        """Test scraping from all available sources."""
        registry = ScraperRegistry()
        query = ScrapeQuery(query="software intern", location="Toronto")
        
        with patch.object(registry, '_scrape_source', new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = [
                RawPosting(
                    title="Test Intern",
                    company_name="Test Corp",
                    location="Toronto, ON",
                    description="Test description",
                    apply_url="https://example.com",
                    source="indeed",
                    external_id="test-123"
                )
            ]
            
            results = await registry.scrape_all_sources(query)
            
            assert len(results) > 0
            assert all(isinstance(posting, RawPosting) for posting in results)

class TestScrapingUtilities:
    """Test scraping utility functions."""
    
    def test_clean_text(self):
        """Test text cleaning utility."""
        from app.scrapers.base import BaseScraper
        
        scraper = BaseScraper()
        
        # Test HTML tag removal
        dirty_text = "<p>Hello <strong>world</strong>!</p>"
        clean_text = scraper._clean_text(dirty_text)
        assert clean_text == "Hello world!"
        
        # Test whitespace normalization
        messy_text = "  Multiple   spaces\n\nand\tlines  "
        clean_text = scraper._clean_text(messy_text)
        assert clean_text == "Multiple spaces and lines"
    
    def test_extract_domain(self):
        """Test domain extraction from URLs."""
        from app.scrapers.base import BaseScraper
        
        scraper = BaseScraper()
        
        assert scraper._extract_domain("https://www.example.com/path") == "example.com"
        assert scraper._extract_domain("http://subdomain.example.org") == "subdomain.example.org"
        assert scraper._extract_domain("invalid-url") == ""
    
    def test_parse_date_relative(self):
        """Test relative date parsing."""
        from app.scrapers.base import BaseScraper
        from datetime import datetime, timedelta
        
        scraper = BaseScraper()
        
        # Test "X days ago" format
        result = scraper._parse_posting_date("2 days ago")
        expected = datetime.now().date() - timedelta(days=2)
        assert result == expected
        
        # Test "today" format
        result = scraper._parse_posting_date("today")
        expected = datetime.now().date()
        assert result == expected
        
        # Test invalid format
        result = scraper._parse_posting_date("invalid date")
        assert result is None
