"""
Internships API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from sqlmodel import Session, select
from backend.core.database import get_session
from backend.data.models import FieldTag, Modality, Internship, Company, Source, ContactEmail
from backend.data.schemas import (
    InternshipSearchParams,
    InternshipDetailResponse,
    InternshipListResponse
)

router = APIRouter()


@router.get("/internships", response_model=InternshipListResponse)
async def search_internships(
    q: Optional[str] = Query(None, description="Search query"),
    field: Optional[List[FieldTag]] = Query(None, description="Field tags"),
    skills: Optional[List[str]] = Query(None, description="Required skills"),
    country: str = Query("Canada", description="Country"),
    region: Optional[str] = Query(None, description="Province/State"),
    city: Optional[str] = Query(None, description="City"),
    modality: Optional[List[Modality]] = Query(None, description="Work modality"),
    salary_min: Optional[int] = Query(None, description="Minimum salary"),
    posted_within_days: Optional[int] = Query(None, description="Posted within days"),
    source: Optional[List[str]] = Query(None, description="Source names"),
    sort: str = Query("relevance", description="Sort by: relevance, date, salary"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    include_low_confidence: bool = Query(False, description="Include low confidence emails"),
    session: Session = Depends(get_session)
):
    """
    Search internships with filters and facets
    Returns paginated results with facet counts
    """
    # Build query
    query = select(Internship).join(Company).join(Source)
    
    # Apply filters
    if q:
        query = query.where(Internship.title.contains(q) | Internship.description.contains(q))
    if field:
        query = query.where(Internship.field_tag.in_(field))
    if country:
        query = query.where(Internship.country == country)
    if region:
        query = query.where(Internship.region == region)
    if city:
        query = query.where(Internship.city == city)
    if modality:
        query = query.where(Internship.modality.in_(modality))
    if salary_min:
        query = query.where(Internship.salary_min >= salary_min)
    
    # Pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Execute query
    internships = session.exec(query).all()
    
    # If no results, return multiple mock internships for demo
    if not internships:
        mock_internships = [
            {
                "id": 1,
                "title": "Software Engineering Intern",
                "description": "Build scalable e-commerce solutions used by millions of merchants worldwide. Work with React, Ruby on Rails, and GraphQL. You'll collaborate with senior developers on real-world projects that impact millions of users.",
                "field_tag": "software_engineering",
                "city": "Toronto",
                "region": "Ontario",
                "country": "Canada",
                "modality": "hybrid",
                "salary_min": 25000,
                "salary_max": 30000,
                "salary_currency": "CAD",
                "duration_months": 4,
                "apply_url": "https://careers.shopify.com/intern/123",
                "posted_at": "2024-01-15T10:00:00Z",
                "expires_at": "2024-02-15T23:59:59Z",
                "skills_required": ["React", "JavaScript", "Python"],
                "education_level": "bachelor",
                "experience_level": "entry",
                "government_program": False,
                "relevance_score": 0.95,
                "created_at": "2024-01-15T10:00:00Z",
                "company": {
                    "id": 1,
                    "name": "Shopify",
                    "domain": "shopify.com",
                    "logo_url": "https://logo.clearbit.com/shopify.com",
                    "description": "Leading e-commerce platform",
                    "headquarters_city": "Ottawa",
                    "headquarters_region": "Ontario",
                    "headquarters_country": "Canada",
                    "size_category": "large",
                    "industry": "E-commerce"
                },
                "source": {
                    "id": 1,
                    "name": "job_bank_ca",
                    "display_name": "Job Bank Canada",
                    "source_type": "api"
                }
            },
            {
                "id": 2,
                "title": "Data Science Intern",
                "description": "Join our AI/ML team to build recommendation systems and analyze user behavior patterns. Work with Python, TensorFlow, and large datasets to drive business insights.",
                "field_tag": "data_science",
                "city": "Vancouver",
                "region": "British Columbia",
                "country": "Canada",
                "modality": "remote",
                "salary_min": 22000,
                "salary_max": 28000,
                "salary_currency": "CAD",
                "duration_months": 8,
                "apply_url": "https://careers.microsoft.com/intern/456",
                "posted_at": "2024-01-12T14:30:00Z",
                "expires_at": "2024-02-20T23:59:59Z",
                "skills_required": ["Python", "TensorFlow", "SQL", "Pandas"],
                "education_level": "bachelor",
                "experience_level": "entry",
                "government_program": False,
                "relevance_score": 0.88,
                "created_at": "2024-01-12T14:30:00Z",
                "company": {
                    "id": 2,
                    "name": "Microsoft",
                    "domain": "microsoft.com",
                    "logo_url": "https://logo.clearbit.com/microsoft.com",
                    "description": "Global technology leader",
                    "headquarters_city": "Vancouver",
                    "headquarters_region": "British Columbia",
                    "headquarters_country": "Canada",
                    "size_category": "enterprise",
                    "industry": "Technology"
                },
                "source": {
                    "id": 2,
                    "name": "indeed_ca",
                    "display_name": "Indeed Canada",
                    "source_type": "html"
                }
            },
            {
                "id": 3,
                "title": "Product Management Intern",
                "description": "Support product managers in defining roadmaps, conducting user research, and analyzing market trends. Perfect for students interested in tech product strategy.",
                "field_tag": "product_management",
                "city": "Montreal",
                "region": "Quebec",
                "country": "Canada",
                "modality": "hybrid",
                "salary_min": 20000,
                "salary_max": 26000,
                "salary_currency": "CAD",
                "duration_months": 4,
                "apply_url": "https://careers.ubisoft.com/intern/789",
                "posted_at": "2024-01-10T09:15:00Z",
                "expires_at": "2024-02-25T23:59:59Z",
                "skills_required": ["Analytics", "User Research", "Figma"],
                "education_level": "bachelor",
                "experience_level": "entry",
                "government_program": False,
                "relevance_score": 0.82,
                "created_at": "2024-01-10T09:15:00Z",
                "company": {
                    "id": 3,
                    "name": "Ubisoft",
                    "domain": "ubisoft.com",
                    "logo_url": "https://logo.clearbit.com/ubisoft.com",
                    "description": "Leading game developer and publisher",
                    "headquarters_city": "Montreal",
                    "headquarters_region": "Quebec",
                    "headquarters_country": "Canada",
                    "size_category": "large",
                    "industry": "Gaming"
                },
                "source": {
                    "id": 1,
                    "name": "job_bank_ca",
                    "display_name": "Job Bank Canada",
                    "source_type": "api"
                }
            },
            {
                "id": 4,
                "title": "UX/UI Design Intern",
                "description": "Create beautiful and intuitive user interfaces for mobile and web applications. Work closely with designers and developers to bring concepts to life.",
                "field_tag": "design_ux_ui",
                "city": "Calgary",
                "region": "Alberta",
                "country": "Canada",
                "modality": "on_site",
                "salary_min": 18000,
                "salary_max": 24000,
                "salary_currency": "CAD",
                "duration_months": 4,
                "apply_url": "https://careers.benevity.com/intern/101",
                "posted_at": "2024-01-08T16:45:00Z",
                "expires_at": "2024-03-01T23:59:59Z",
                "skills_required": ["Figma", "Adobe Creative Suite", "Prototyping"],
                "education_level": "bachelor",
                "experience_level": "entry",
                "government_program": False,
                "relevance_score": 0.79,
                "created_at": "2024-01-08T16:45:00Z",
                "company": {
                    "id": 4,
                    "name": "Benevity",
                    "domain": "benevity.com",
                    "logo_url": "https://logo.clearbit.com/benevity.com",
                    "description": "Corporate social responsibility platform",
                    "headquarters_city": "Calgary",
                    "headquarters_region": "Alberta",
                    "headquarters_country": "Canada",
                    "size_category": "medium",
                    "industry": "Social Impact"
                },
                "source": {
                    "id": 3,
                    "name": "talent_com",
                    "display_name": "Talent.com",
                    "source_type": "api"
                }
            },
            {
                "id": 5,
                "title": "Marketing Analytics Intern",
                "description": "Analyze marketing campaigns, track user engagement metrics, and create data-driven recommendations to optimize marketing spend and ROI.",
                "field_tag": "marketing",
                "city": "Ottawa",
                "region": "Ontario",
                "country": "Canada",
                "modality": "hybrid",
                "salary_min": 19000,
                "salary_max": 25000,
                "salary_currency": "CAD",
                "duration_months": 6,
                "apply_url": "https://careers.mogo.ca/intern/202",
                "posted_at": "2024-01-05T11:20:00Z",
                "expires_at": "2024-02-28T23:59:59Z",
                "skills_required": ["Google Analytics", "Excel", "SQL", "Tableau"],
                "education_level": "bachelor",
                "experience_level": "entry",
                "government_program": True,
                "relevance_score": 0.75,
                "created_at": "2024-01-05T11:20:00Z",
                "company": {
                    "id": 5,
                    "name": "Mogo",
                    "domain": "mogo.ca",
                    "logo_url": "https://logo.clearbit.com/mogo.ca",
                    "description": "Financial technology company",
                    "headquarters_city": "Ottawa",
                    "headquarters_region": "Ontario",
                    "headquarters_country": "Canada",
                    "size_category": "medium",
                    "industry": "Fintech"
                },
                "source": {
                    "id": 2,
                    "name": "indeed_ca",
                    "display_name": "Indeed Canada",
                    "source_type": "html"
                }
            }
        ]
        
        mock_facets = {
            "fields": [
                {"key": "software_engineering", "count": 150},
                {"key": "data_science", "count": 80},
                {"key": "product_management", "count": 45}
            ],
            "regions": [
                {"key": "Ontario", "count": 200},
                {"key": "British Columbia", "count": 120},
                {"key": "Quebec", "count": 90}
            ],
            "cities": [
                {"key": "Toronto", "count": 180},
                {"key": "Vancouver", "count": 100},
                {"key": "Montreal", "count": 85}
            ],
            "modalities": [
                {"key": "hybrid", "count": 250},
                {"key": "remote", "count": 180},
                {"key": "on_site", "count": 120}
            ],
            "sources": [
                {"key": "job_bank_ca", "count": 300},
                {"key": "indeed_ca", "count": 200},
                {"key": "talent_com", "count": 150}
            ],
            "government_programs": 45
        }
        
        return InternshipListResponse(
            items=mock_internships,
            total=len(mock_internships),
            page=page,
            page_size=page_size,
            total_pages=1,
            facets=mock_facets
        )
    
    # Return actual database results if found
    return InternshipListResponse(
        items=[internship.dict() for internship in internships],
        total=len(internships),
        page=page,
        page_size=page_size,
        total_pages=(len(internships) + page_size - 1) // page_size,
        facets=mock_facets  # TODO: Calculate real facets from database
    )


@router.get("/internships/{internship_id}", response_model=InternshipDetailResponse)
async def get_internship_detail(internship_id: int, session: Session = Depends(get_session)):
    """
    Get detailed internship information including verified contacts
    """
    # Get internship from database
    internship = session.get(Internship, internship_id)
    if not internship:
        # Return mock data for demo based on ID
        mock_internships = {
            1: {
                "id": 1,
                "title": "Software Engineering Intern",
                "description": "Build scalable e-commerce solutions used by millions of merchants worldwide. Work with React, Ruby on Rails, and GraphQL. You'll collaborate with senior developers on real-world projects that impact millions of users. This is a fantastic opportunity to learn from industry experts and contribute to products used by millions of merchants globally.",
                "field_tag": "software_engineering",
                "city": "Toronto",
                "region": "Ontario",
                "country": "Canada",
                "modality": "hybrid",
                "salary_min": 25000,
                "salary_max": 30000,
                "salary_currency": "CAD",
                "duration_months": 4,
                "apply_url": "https://careers.shopify.com/intern/123",
                "posted_at": "2024-01-15T10:00:00Z",
                "expires_at": "2024-02-15T23:59:59Z",
                "skills_required": ["React", "JavaScript", "Python"],
                "education_level": "bachelor",
                "experience_level": "entry",
                "government_program": False,
                "relevance_score": 0.95,
                "created_at": "2024-01-15T10:00:00Z",
                "company": {
                    "id": 1,
                    "name": "Shopify",
                    "domain": "shopify.com",
                    "logo_url": "https://logo.clearbit.com/shopify.com",
                    "description": "Leading e-commerce platform",
                    "headquarters_city": "Ottawa",
                    "headquarters_region": "Ontario",
                    "headquarters_country": "Canada",
                    "size_category": "large",
                    "industry": "E-commerce"
                },
                "source": {
                    "id": 1,
                    "name": "job_bank_ca",
                    "display_name": "Job Bank Canada",
                    "source_type": "api"
                }
            },
            2: {
                "id": 2,
                "title": "Data Science Intern",
                "description": "Join our AI/ML team to build recommendation systems and analyze user behavior patterns. Work with Python, TensorFlow, and large datasets to drive business insights. You'll be mentored by senior data scientists and work on cutting-edge machine learning projects that directly impact product recommendations and user experience.",
                "field_tag": "data_science",
                "city": "Vancouver",
                "region": "British Columbia",
                "country": "Canada",
                "modality": "remote",
                "salary_min": 22000,
                "salary_max": 28000,
                "salary_currency": "CAD",
                "duration_months": 8,
                "apply_url": "https://careers.microsoft.com/intern/456",
                "posted_at": "2024-01-12T14:30:00Z",
                "expires_at": "2024-02-20T23:59:59Z",
                "skills_required": ["Python", "TensorFlow", "SQL", "Pandas"],
                "education_level": "bachelor",
                "experience_level": "entry",
                "government_program": False,
                "relevance_score": 0.88,
                "created_at": "2024-01-12T14:30:00Z",
                "company": {
                    "id": 2,
                    "name": "Microsoft",
                    "domain": "microsoft.com",
                    "logo_url": "https://logo.clearbit.com/microsoft.com",
                    "description": "Global technology leader",
                    "headquarters_city": "Vancouver",
                    "headquarters_region": "British Columbia",
                    "headquarters_country": "Canada",
                    "size_category": "enterprise",
                    "industry": "Technology"
                },
                "source": {
                    "id": 2,
                    "name": "indeed_ca",
                    "display_name": "Indeed Canada",
                    "source_type": "html"
                }
            },
            3: {
                "id": 3,
                "title": "Product Management Intern",
                "description": "Support product managers in defining roadmaps, conducting user research, and analyzing market trends. Perfect for students interested in tech product strategy. You'll work on real product features, conduct user interviews, and help shape the future of our gaming products.",
                "field_tag": "product_management",
                "city": "Montreal",
                "region": "Quebec",
                "country": "Canada",
                "modality": "hybrid",
                "salary_min": 20000,
                "salary_max": 26000,
                "salary_currency": "CAD",
                "duration_months": 4,
                "apply_url": "https://careers.ubisoft.com/intern/789",
                "posted_at": "2024-01-10T09:15:00Z",
                "expires_at": "2024-02-25T23:59:59Z",
                "skills_required": ["Analytics", "User Research", "Figma"],
                "education_level": "bachelor",
                "experience_level": "entry",
                "government_program": False,
                "relevance_score": 0.82,
                "created_at": "2024-01-10T09:15:00Z",
                "company": {
                    "id": 3,
                    "name": "Ubisoft",
                    "domain": "ubisoft.com",
                    "logo_url": "https://logo.clearbit.com/ubisoft.com",
                    "description": "Leading game developer and publisher",
                    "headquarters_city": "Montreal",
                    "headquarters_region": "Quebec",
                    "headquarters_country": "Canada",
                    "size_category": "large",
                    "industry": "Gaming"
                },
                "source": {
                    "id": 1,
                    "name": "job_bank_ca",
                    "display_name": "Job Bank Canada",
                    "source_type": "api"
                }
            },
            4: {
                "id": 4,
                "title": "UX/UI Design Intern",
                "description": "Create beautiful and intuitive user interfaces for mobile and web applications. Work closely with designers and developers to bring concepts to life. You'll participate in the full design process from user research to final implementation, working on products that help companies make a positive social impact.",
                "field_tag": "design_ux_ui",
                "city": "Calgary",
                "region": "Alberta",
                "country": "Canada",
                "modality": "on_site",
                "salary_min": 18000,
                "salary_max": 24000,
                "salary_currency": "CAD",
                "duration_months": 4,
                "apply_url": "https://careers.benevity.com/intern/101",
                "posted_at": "2024-01-08T16:45:00Z",
                "expires_at": "2024-03-01T23:59:59Z",
                "skills_required": ["Figma", "Adobe Creative Suite", "Prototyping"],
                "education_level": "bachelor",
                "experience_level": "entry",
                "government_program": False,
                "relevance_score": 0.79,
                "created_at": "2024-01-08T16:45:00Z",
                "company": {
                    "id": 4,
                    "name": "Benevity",
                    "domain": "benevity.com",
                    "logo_url": "https://logo.clearbit.com/benevity.com",
                    "description": "Corporate social responsibility platform",
                    "headquarters_city": "Calgary",
                    "headquarters_region": "Alberta",
                    "headquarters_country": "Canada",
                    "size_category": "medium",
                    "industry": "Social Impact"
                },
                "source": {
                    "id": 3,
                    "name": "talent_com",
                    "display_name": "Talent.com",
                    "source_type": "api"
                }
            },
            5: {
                "id": 5,
                "title": "Marketing Analytics Intern",
                "description": "Analyze marketing campaigns, track user engagement metrics, and create data-driven recommendations to optimize marketing spend and ROI. You'll work with our growth team to understand user acquisition funnels and help improve conversion rates across all marketing channels.",
                "field_tag": "marketing",
                "city": "Ottawa",
                "region": "Ontario",
                "country": "Canada",
                "modality": "hybrid",
                "salary_min": 19000,
                "salary_max": 25000,
                "salary_currency": "CAD",
                "duration_months": 6,
                "apply_url": "https://careers.mogo.ca/intern/202",
                "posted_at": "2024-01-05T11:20:00Z",
                "expires_at": "2024-02-28T23:59:59Z",
                "skills_required": ["Google Analytics", "Excel", "SQL", "Tableau"],
                "education_level": "bachelor",
                "experience_level": "entry",
                "government_program": True,
                "relevance_score": 0.75,
                "created_at": "2024-01-05T11:20:00Z",
                "company": {
                    "id": 5,
                    "name": "Mogo",
                    "domain": "mogo.ca",
                    "logo_url": "https://logo.clearbit.com/mogo.ca",
                    "description": "Financial technology company",
                    "headquarters_city": "Ottawa",
                    "headquarters_region": "Ontario",
                    "headquarters_country": "Canada",
                    "size_category": "medium",
                    "industry": "Fintech"
                },
                "source": {
                    "id": 2,
                    "name": "indeed_ca",
                    "display_name": "Indeed Canada",
                    "source_type": "html"
                }
            }
        }
        
        if internship_id not in mock_internships:
            raise HTTPException(status_code=404, detail="Internship not found")
        
        mock_internship = mock_internships[internship_id]
        
        # Mock contact emails based on company
        mock_contacts_map = {
            1: [  # Shopify
                {
                    "id": 1,
                    "email": "careers@shopify.com",
                    "confidence_score": 0.9,
                    "confidence_level": "high",
                    "email_type": "careers",
                    "name": "Shopify Careers Team",
                    "title": "Talent Acquisition",
                    "mx_verified": True
                },
                {
                    "id": 2,
                    "email": "internships@shopify.com",
                    "confidence_score": 0.85,
                    "confidence_level": "high",
                    "email_type": "internships",
                    "name": "Sarah Chen",
                    "title": "University Relations Manager",
                    "mx_verified": True
                }
            ],
            2: [  # Microsoft
                {
                    "id": 3,
                    "email": "university@microsoft.com",
                    "confidence_score": 0.88,
                    "confidence_level": "high",
                    "email_type": "university",
                    "name": "Microsoft University Relations",
                    "title": "Campus Recruiting",
                    "mx_verified": True
                },
                {
                    "id": 4,
                    "email": "datascience-interns@microsoft.com",
                    "confidence_score": 0.75,
                    "confidence_level": "medium",
                    "email_type": "team",
                    "name": "Alex Rodriguez",
                    "title": "Senior Data Scientist",
                    "mx_verified": True
                }
            ],
            3: [  # Ubisoft
                {
                    "id": 5,
                    "email": "careers.montreal@ubisoft.com",
                    "confidence_score": 0.82,
                    "confidence_level": "high",
                    "email_type": "careers",
                    "name": "Ubisoft Montreal HR",
                    "title": "Human Resources",
                    "mx_verified": True
                },
                {
                    "id": 6,
                    "email": "product-internships@ubisoft.com",
                    "confidence_score": 0.68,
                    "confidence_level": "medium",
                    "email_type": "team",
                    "name": "Marie Dubois",
                    "title": "Product Manager",
                    "mx_verified": False
                }
            ],
            4: [  # Benevity
                {
                    "id": 7,
                    "email": "talent@benevity.com",
                    "confidence_score": 0.79,
                    "confidence_level": "medium",
                    "email_type": "careers",
                    "name": "Benevity Talent Team",
                    "title": "Talent Acquisition",
                    "mx_verified": True
                },
                {
                    "id": 8,
                    "email": "design-team@benevity.com",
                    "confidence_score": 0.65,
                    "confidence_level": "medium",
                    "email_type": "team",
                    "name": "Jordan Kim",
                    "title": "Design Lead",
                    "mx_verified": True
                }
            ],
            5: [  # Mogo
                {
                    "id": 9,
                    "email": "careers@mogo.ca",
                    "confidence_score": 0.85,
                    "confidence_level": "high",
                    "email_type": "careers",
                    "name": "Mogo Careers",
                    "title": "People & Culture",
                    "mx_verified": True
                },
                {
                    "id": 10,
                    "email": "marketing@mogo.ca",
                    "confidence_score": 0.72,
                    "confidence_level": "medium",
                    "email_type": "team",
                    "name": "Taylor Smith",
                    "title": "Marketing Director",
                    "mx_verified": True
                }
            ]
        }
        
        mock_contacts = mock_contacts_map.get(internship_id, [])
        
        return InternshipDetailResponse(
            internship=mock_internship,
            contact_emails=mock_contacts,
            is_bookmarked=False
        )
    
    # Return actual database result if found
    # TODO: Get actual contact emails from database
    return InternshipDetailResponse(
        internship=internship.dict(),
        contact_emails=[],  # TODO: Query actual contact emails
        is_bookmarked=False  # TODO: Check if user has bookmarked this
    )
