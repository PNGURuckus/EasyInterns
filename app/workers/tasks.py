import asyncio
from typing import List, Dict, Any
from datetime import datetime
import traceback

from ..scrapers.registry import get_scraper_registry
from ..scrapers.base import RawPosting
from ..repositories import get_repositories, get_session
from ..core.email_utils import find_contact_emails
from ..models import Internship, Company, Source, ContactEmail
from ..api.scrape import update_job_status, get_job_status

async def run_scrape_job(job_id: str, sources_to_scrape: List[str], force: bool = False):
    """Run scraping job for specified sources"""
    
    try:
        # Update job status to running
        update_job_status(job_id, status="running")
        
        registry = get_scraper_registry()
        session = get_session()
        repos = get_repositories(session)
        
        total_new_internships = 0
        total_internships = 0
        
        for i, source_name in enumerate(sources_to_scrape):
            try:
                # Update progress
                update_job_status(job_id, progress={
                    **get_job_status(job_id)["progress"],
                    "current_source": source_name,
                    "completed_sources": i
                })
                
                # Get scraper
                scraper_class = registry.get_scraper(source_name)
                scraper = scraper_class()
                
                # Run scraper
                raw_postings = await scraper.scrape()
                
                # Process and store internships
                new_count = await process_raw_postings(raw_postings, source_name, repos, session)
                
                total_new_internships += new_count
                total_internships += len(raw_postings)
                
                # Update progress
                update_job_status(job_id, progress={
                    **get_job_status(job_id)["progress"],
                    "completed_sources": i + 1,
                    "total_internships": total_internships,
                    "new_internships": total_new_internships
                })
                
            except Exception as e:
                error_msg = f"Error scraping {source_name}: {str(e)}"
                current_progress = get_job_status(job_id)["progress"]
                current_progress["errors"].append(error_msg)
                update_job_status(job_id, progress=current_progress)
                print(f"Scraping error: {error_msg}")
                continue
        
        # Job completed successfully
        result = {
            "total_sources": len(sources_to_scrape),
            "total_internships": total_internships,
            "new_internships": total_new_internships,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        update_job_status(job_id, status="completed", result=result)
        
        # Start background email enrichment
        asyncio.create_task(enrich_contact_emails(job_id, total_new_internships))
        
    except Exception as e:
        error_msg = f"Job failed: {str(e)}\n{traceback.format_exc()}"
        update_job_status(job_id, status="failed", error=error_msg)
        print(f"Job {job_id} failed: {error_msg}")
    
    finally:
        session.close()

async def process_raw_postings(raw_postings: List[RawPosting], source_name: str, repos, session) -> int:
    """Process raw postings and store as internships"""
    
    # Get or create source
    source = session.query(Source).filter(Source.name == source_name).first()
    if not source:
        source = Source(name=source_name, base_url="", enabled=True)
        session.add(source)
        session.commit()
        session.refresh(source)
    
    new_count = 0
    
    for posting in raw_postings:
        try:
            # Check if internship already exists
            existing = session.query(Internship).filter(
                Internship.apply_url == posting.apply_url
            ).first()
            
            if existing:
                continue  # Skip duplicates
            
            # Get or create company
            company_name = posting.company or "Unknown Company"
            company = session.query(Company).filter(Company.name == company_name).first()
            if not company:
                company = Company(
                    name=company_name,
                    domain=extract_domain_from_url(posting.apply_url or ""),
                    description=None
                )
                session.add(company)
                session.commit()
                session.refresh(company)
            
            # Determine field tag and modality
            field_tag = classify_field_tag(posting.title or "", posting.description or "")
            modality = classify_modality(posting.location or "", posting.description or "")
            
            # Create internship
            internship = Internship(
                title=posting.title or "",
                description=posting.description,
                location=posting.location,
                modality=modality,
                field_tag=field_tag,
                apply_url=posting.apply_url or "",
                external_id=posting.external_id,
                salary_min=posting.salary_min,
                salary_max=posting.salary_max,
                posting_date=posting.posted_date,
                deadline=None,
                requirements=posting.requirements,
                benefits=posting.benefits,
                is_government=posting.is_government,
                company_id=company.id,
                source_id=source.id
            )
            
            session.add(internship)
            session.commit()
            session.refresh(internship)
            
            new_count += 1
            
        except Exception as e:
            print(f"Error processing posting: {str(e)}")
            session.rollback()
            continue
    
    return new_count

async def enrich_contact_emails(job_id: str, new_internships_count: int):
    """Background task to enrich internships with contact emails"""
    
    if new_internships_count == 0:
        return
    
    try:
        session = get_session()
        
        # Get recent internships without contact emails
        recent_internships = session.query(Internship).filter(
            Internship.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
        ).limit(50).all()  # Limit to avoid overwhelming email extraction
        
        for internship in recent_internships:
            try:
                if internship.company:
                    company_url = f"https://{internship.company.domain}" if internship.company.domain else ""
                    
                    # Find contact emails
                    emails = await find_contact_emails(
                        company_name=internship.company.name,
                        company_url=company_url,
                        job_posting_text=internship.description or ""
                    )
                    
                    # Store contact emails
                    for email_data in emails[:5]:  # Limit to top 5 emails
                        contact_email = ContactEmail(
                            internship_id=internship.id,
                            email=email_data["email"],
                            confidence=email_data["confidence"],
                            source_type=email_data["source_type"],
                            verified=False
                        )
                        session.add(contact_email)
                    
                    session.commit()
                    
            except Exception as e:
                print(f"Error enriching emails for internship {internship.id}: {str(e)}")
                session.rollback()
                continue
        
    except Exception as e:
        print(f"Email enrichment failed: {str(e)}")
    finally:
        session.close()

def extract_domain_from_url(url: str) -> str:
    """Extract domain from URL"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc.replace("www.", "")
    except:
        return ""

def classify_field_tag(title: str, description: str) -> str:
    """Classify internship field based on title and description"""
    from ..models import FieldTag
    
    text = f"{title} {description}".lower()
    
    # Software Engineering keywords
    if any(keyword in text for keyword in ["software", "developer", "programming", "coding", "engineer", "backend", "frontend", "fullstack"]):
        return FieldTag.SOFTWARE_ENGINEERING
    
    # Data Science keywords
    if any(keyword in text for keyword in ["data", "analytics", "machine learning", "ai", "scientist", "analyst"]):
        return FieldTag.DATA_SCIENCE
    
    # Product Management keywords
    if any(keyword in text for keyword in ["product", "pm", "product manager", "product management"]):
        return FieldTag.PRODUCT_MANAGEMENT
    
    # Design keywords
    if any(keyword in text for keyword in ["design", "ui", "ux", "designer", "creative", "visual"]):
        return FieldTag.DESIGN
    
    # Marketing keywords
    if any(keyword in text for keyword in ["marketing", "digital marketing", "social media", "content", "brand"]):
        return FieldTag.MARKETING
    
    # Sales keywords
    if any(keyword in text for keyword in ["sales", "business development", "account", "revenue"]):
        return FieldTag.SALES
    
    # Finance keywords
    if any(keyword in text for keyword in ["finance", "financial", "accounting", "investment", "banking"]):
        return FieldTag.FINANCE
    
    # Consulting keywords
    if any(keyword in text for keyword in ["consulting", "consultant", "strategy", "advisory"]):
        return FieldTag.CONSULTING
    
    # Research keywords
    if any(keyword in text for keyword in ["research", "researcher", "lab", "academic"]):
        return FieldTag.RESEARCH
    
    # Operations keywords
    if any(keyword in text for keyword in ["operations", "ops", "logistics", "supply chain"]):
        return FieldTag.OPERATIONS
    
    return FieldTag.OTHER

def classify_modality(location: str, description: str) -> str:
    """Classify work modality based on location and description"""
    from ..models import Modality
    
    text = f"{location} {description}".lower()
    
    if any(keyword in text for keyword in ["remote", "work from home", "distributed", "anywhere"]):
        return Modality.REMOTE
    
    if any(keyword in text for keyword in ["hybrid", "flexible", "remote/onsite", "part remote"]):
        return Modality.HYBRID
    
    return Modality.ONSITE

async def score_all_internships():
    """Background task to score all internships for relevance"""
    
    try:
        session = get_session()
        
        # Get internships without scores
        internships = session.query(Internship).filter(
            Internship.relevance_score.is_(None)
        ).limit(1000).all()
        
        for internship in internships:
            try:
                # Calculate relevance score
                score = calculate_relevance_score(internship)
                internship.relevance_score = score
                session.add(internship)
                
            except Exception as e:
                print(f"Error scoring internship {internship.id}: {str(e)}")
                continue
        
        session.commit()
        
    except Exception as e:
        print(f"Scoring failed: {str(e)}")
    finally:
        session.close()

def calculate_relevance_score(internship: Internship) -> float:
    """Calculate relevance score for an internship"""
    
    score = 0.5  # Base score
    
    # Recency bonus (newer posts get higher scores)
    if internship.posting_date:
        days_old = (datetime.utcnow() - internship.posting_date).days
        if days_old <= 7:
            score += 0.2
        elif days_old <= 30:
            score += 0.1
        elif days_old > 90:
            score -= 0.1
    
    # Title quality (intern-specific titles get bonus)
    title_lower = internship.title.lower()
    if any(keyword in title_lower for keyword in ["intern", "internship", "co-op", "summer student"]):
        score += 0.2
    
    # Company size/reputation (placeholder - would need company data)
    if internship.company and internship.company.domain:
        # Well-known domains get bonus
        known_domains = ["google.com", "microsoft.com", "apple.com", "amazon.com", "meta.com"]
        if any(domain in internship.company.domain for domain in known_domains):
            score += 0.3
    
    # Government positions
    if internship.is_government:
        score += 0.1
    
    # Salary information available
    if internship.salary_min or internship.salary_max:
        score += 0.1
    
    # Description quality
    if internship.description and len(internship.description) > 200:
        score += 0.1
    
    return max(0.0, min(1.0, score))
