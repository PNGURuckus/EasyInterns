from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import os

# Simple FastAPI app for testing
app = FastAPI(title="EasyInterns API", description="Internship finder platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HealthResponse(BaseModel):
    status: str
    message: str
    database_connected: bool

class InternshipResponse(BaseModel):
    id: int
    title: str
    company: str
    location: str
    description: str

@app.get("/", response_class=HTMLResponse)
def root():
    """Serve the main web interface"""
    with open("templates/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint"""
    try:
        # Check if database file exists
        db_exists = os.path.exists("easyintern.db")
        
        # Try to connect to database
        if db_exists:
            conn = sqlite3.connect("easyintern.db")
            conn.close()
            db_connected = True
        else:
            db_connected = False
            
        return HealthResponse(
            status="healthy",
            message="API is running successfully",
            database_connected=db_connected
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            message=f"Database connection failed: {str(e)}",
            database_connected=False
        )

@app.get("/internships", response_model=List[InternshipResponse])
def get_internships(limit: int = 20):
    """Get internships with more realistic data"""
    sample_internships = [
        {
            "id": 1,
            "title": "Software Engineering Intern",
            "company": "Shopify",
            "location": "Toronto, ON",
            "description": "Build scalable e-commerce solutions used by millions of merchants worldwide. Work with React, Ruby on Rails, and GraphQL."
        },
        {
            "id": 2,
            "title": "Data Science Intern",
            "company": "RBC",
            "location": "Toronto, ON",
            "description": "Apply machine learning to financial services. Analyze customer data and build predictive models for risk assessment."
        },
        {
            "id": 3,
            "title": "Product Management Intern",
            "company": "Slack",
            "location": "Vancouver, BC",
            "description": "Shape the future of workplace communication. Conduct user research and define product roadmaps for enterprise features."
        },
        {
            "id": 4,
            "title": "UX Design Intern",
            "company": "Hootsuite",
            "location": "Vancouver, BC",
            "description": "Design intuitive social media management experiences. Create wireframes, prototypes, and conduct usability testing."
        },
        {
            "id": 5,
            "title": "Marketing Intern",
            "company": "Wealthsimple",
            "location": "Toronto, ON",
            "description": "Drive growth for Canada's leading fintech. Create content, analyze campaigns, and optimize conversion funnels."
        },
        {
            "id": 6,
            "title": "DevOps Engineering Intern",
            "company": "Lightspeed",
            "location": "Montreal, QC",
            "description": "Build and maintain cloud infrastructure. Work with Kubernetes, AWS, and CI/CD pipelines for retail solutions."
        },
        {
            "id": 7,
            "title": "Business Analyst Intern",
            "company": "TD Bank",
            "location": "Toronto, ON",
            "description": "Analyze business processes and drive digital transformation initiatives in one of Canada's largest banks."
        },
        {
            "id": 8,
            "title": "Mobile Developer Intern",
            "company": "Nuvei",
            "location": "Montreal, QC",
            "description": "Develop payment solutions for iOS and Android. Work with fintech APIs and secure transaction processing."
        },
        {
            "id": 9,
            "title": "Cybersecurity Intern",
            "company": "BlackBerry",
            "location": "Waterloo, ON",
            "description": "Protect enterprise systems from cyber threats. Implement security protocols and conduct vulnerability assessments."
        },
        {
            "id": 10,
            "title": "AI Research Intern",
            "company": "Element AI",
            "location": "Montreal, QC",
            "description": "Research cutting-edge AI applications. Work on natural language processing and computer vision projects."
        },
        {
            "id": 11,
            "title": "Sales Development Intern",
            "company": "Coinsquare",
            "location": "Toronto, ON",
            "description": "Drive growth in cryptocurrency trading platform. Generate leads and support enterprise client acquisition."
        },
        {
            "id": 12,
            "title": "Frontend Developer Intern",
            "company": "Clio",
            "location": "Vancouver, BC",
            "description": "Build legal practice management software. Work with React, TypeScript, and modern web technologies."
        }
    ]
    
    return sample_internships[:limit]

@app.get("/stats")
def get_stats():
    """Get API statistics"""
    return {
        "total_internships": 12,
        "active_scrapers": 0,
        "api_version": "1.0.0",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
