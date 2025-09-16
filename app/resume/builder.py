import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright
import tempfile
import os
from datetime import datetime

from ..config import settings

class ResumeBuilder:
    """Resume builder using HTML templates and Playwright for PDF generation"""
    
    def __init__(self):
        self.templates_dir = Path(__file__).parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True
        )
    
    def render_template(self, template_name: str, content: Dict[str, Any]) -> str:
        """Render resume template with content"""
        template_file = f"{template_name}.html"
        
        if not (self.templates_dir / template_file).exists():
            raise ValueError(f"Template {template_name} not found")
        
        template = self.jinja_env.get_template(template_file)
        return template.render(**content)
    
    async def generate_pdf(self, html_content: str, output_path: Optional[str] = None) -> str:
        """Generate PDF from HTML using Playwright"""
        if not output_path:
            # Create temporary file
            temp_dir = Path(tempfile.gettempdir()) / "easyintern_resumes"
            temp_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(temp_dir / f"resume_{timestamp}.pdf")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            # Set content and wait for fonts/styles to load
            await page.set_content(html_content, wait_until="networkidle")
            
            # Generate PDF with print-optimized settings
            await page.pdf(
                path=output_path,
                format="A4",
                print_background=True,
                margin={
                    "top": "0.5in",
                    "right": "0.5in",
                    "bottom": "0.5in",
                    "left": "0.5in"
                }
            )
            
            await browser.close()
        
        return output_path
    
    async def upload_to_storage(self, file_path: str, resume_id: int) -> str:
        """Upload PDF to Supabase Storage and return signed URL"""
        if not settings.supabase_url or not settings.supabase_service_key:
            # For development, return local file path
            return f"file://{file_path}"
        
        try:
            from supabase import create_client
            
            supabase = create_client(settings.supabase_url, settings.supabase_service_key)
            
            # Upload file
            bucket_name = "resumes"
            file_name = f"resume_{resume_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            with open(file_path, "rb") as f:
                response = supabase.storage.from_(bucket_name).upload(
                    path=file_name,
                    file=f,
                    file_options={"content-type": "application/pdf"}
                )
            
            if response.get("error"):
                raise Exception(f"Upload failed: {response['error']}")
            
            # Get signed URL (24 hour expiry)
            signed_url = supabase.storage.from_(bucket_name).create_signed_url(
                path=file_name,
                expires_in=86400  # 24 hours
            )
            
            return signed_url.get("signedURL", f"file://{file_path}")
            
        except Exception as e:
            print(f"Storage upload failed: {e}")
            # Fallback to local file
            return f"file://{file_path}"
    
    def validate_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean resume content"""
        # Ensure required fields exist
        validated = {
            "name": content.get("name", ""),
            "email": content.get("email", ""),
            "phone": content.get("phone", ""),
            "location": content.get("location", ""),
            "linkedin": content.get("linkedin", ""),
            "github": content.get("github", ""),
            "summary": content.get("summary", ""),
            "education": content.get("education", []),
            "experience": content.get("experience", []),
            "projects": content.get("projects", []),
            "skills": content.get("skills", {}),
            "certifications": content.get("certifications", []),
            "activities": content.get("activities", []),
            "awards": content.get("awards", []),
            "languages": content.get("languages", []),
            "volunteer": content.get("volunteer", "")
        }
        
        # Clean up empty sections
        for key, value in list(validated.items()):
            if isinstance(value, list) and not value:
                continue
            elif isinstance(value, dict) and not value:
                continue
            elif isinstance(value, str) and not value.strip():
                validated[key] = None
        
        return validated

# Main function for API usage
async def generate_resume_pdf(content: Dict[str, Any], template: str, resume_id: int) -> str:
    """Generate resume PDF and upload to storage"""
    builder = ResumeBuilder()
    
    # Validate content
    validated_content = builder.validate_content(content)
    
    # Render HTML
    html_content = builder.render_template(template, validated_content)
    
    # Generate PDF
    pdf_path = await builder.generate_pdf(html_content)
    
    # Upload to storage
    pdf_url = await builder.upload_to_storage(pdf_path, resume_id)
    
    # Clean up local file if uploaded successfully
    if pdf_url.startswith("http") and os.path.exists(pdf_path):
        os.remove(pdf_path)
    
    return pdf_url

# Template preview function
async def generate_template_preview(template: str, sample_data: Optional[Dict[str, Any]] = None) -> str:
    """Generate a preview of a template with sample data"""
    builder = ResumeBuilder()
    
    if not sample_data:
        sample_data = {
            "name": "Alex Johnson",
            "email": "alex.johnson@email.com",
            "phone": "(555) 123-4567",
            "location": "San Francisco, CA",
            "linkedin": "linkedin.com/in/alexjohnson",
            "github": "github.com/alexjohnson",
            "summary": "Motivated computer science student with strong programming skills and passion for software development. Seeking internship opportunities to apply technical knowledge and gain hands-on experience in a professional environment.",
            "education": [{
                "degree": "Bachelor of Science in Computer Science",
                "school": "University of California, Berkeley",
                "location": "Berkeley, CA",
                "graduation_date": "Expected May 2025",
                "gpa": "3.7",
                "relevant_coursework": ["Data Structures", "Algorithms", "Software Engineering", "Database Systems"]
            }],
            "experience": [{
                "title": "Software Development Intern",
                "company": "Tech Startup Inc.",
                "location": "San Francisco, CA",
                "start_date": "June 2024",
                "end_date": "August 2024",
                "bullets": [
                    "Developed and maintained web applications using React and Node.js",
                    "Collaborated with cross-functional teams to implement new features",
                    "Improved application performance by 25% through code optimization",
                    "Participated in code reviews and agile development processes"
                ]
            }],
            "projects": [{
                "name": "Task Management App",
                "date": "Spring 2024",
                "description": "Full-stack web application for team task management with real-time updates",
                "technologies": ["React", "Node.js", "MongoDB", "Socket.io"]
            }],
            "skills": {
                "Programming Languages": ["Python", "JavaScript", "Java", "C++"],
                "Web Technologies": ["React", "HTML/CSS", "Node.js", "Express"],
                "Databases": ["MongoDB", "PostgreSQL", "MySQL"],
                "Tools & Platforms": ["Git", "Docker", "AWS", "Linux"]
            },
            "certifications": [{
                "name": "AWS Cloud Practitioner",
                "issuer": "Amazon Web Services",
                "date": "March 2024"
            }],
            "activities": [{
                "title": "President",
                "organization": "Computer Science Club",
                "date": "2023-2024",
                "description": "Led weekly meetings and organized technical workshops for 50+ members"
            }]
        }
    
    validated_content = builder.validate_content(sample_data)
    html_content = builder.render_template(template, validated_content)
    
    # For preview, we might want to return HTML or generate a small PDF
    return html_content
