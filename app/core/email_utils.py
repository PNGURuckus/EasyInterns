import re
import socket
import dns.resolver
from typing import List, Tuple, Optional, Dict
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup

# Common email patterns
EMAIL_PATTERNS = [
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    r'\b[A-Za-z0-9._%+-]+\s*\[\s*at\s*\]\s*[A-Za-z0-9.-]+\s*\[\s*dot\s*\]\s*[A-Z|a-z]{2,}\b',
    r'\b[A-Za-z0-9._%+-]+\s*@\s*[A-Za-z0-9.-]+\s*\.\s*[A-Z|a-z]{2,}\b'
]

# Common contact page paths
CONTACT_PATHS = [
    '/contact', '/contact-us', '/contacts', '/about/contact',
    '/company/contact', '/careers/contact', '/support/contact',
    '/about', '/team', '/careers', '/jobs', '/about-us'
]

# HR/Recruiting email prefixes
HR_PREFIXES = [
    'hr', 'careers', 'jobs', 'recruiting', 'recruitment', 'talent',
    'people', 'hiring', 'internships', 'students', 'campus'
]

def extract_emails_from_text(text: str) -> List[str]:
    """Extract email addresses from text using regex patterns"""
    emails = set()
    
    for pattern in EMAIL_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            # Clean up obfuscated emails
            email = match.replace('[at]', '@').replace('[dot]', '.').replace(' ', '')
            if is_valid_email_format(email):
                emails.add(email.lower())
    
    return list(emails)

def is_valid_email_format(email: str) -> bool:
    """Check if email has valid format"""
    pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
    return bool(re.match(pattern, email))

def validate_email_mx(email: str) -> bool:
    """Validate email by checking MX record"""
    try:
        domain = email.split('@')[1]
        mx_records = dns.resolver.resolve(domain, 'MX')
        return len(mx_records) > 0
    except:
        return False

def score_email_confidence(email: str, context: Dict[str, str]) -> float:
    """Score email confidence based on various factors"""
    score = 0.5  # Base score
    
    domain = email.split('@')[1].lower()
    local_part = email.split('@')[0].lower()
    
    # Domain factors
    if domain in context.get('company_domain', '').lower():
        score += 0.3  # Same domain as company
    
    # Common business domains get lower score
    free_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com']
    if domain in free_domains:
        score -= 0.2
    
    # HR/recruiting keywords in local part
    for prefix in HR_PREFIXES:
        if prefix in local_part:
            score += 0.2
            break
    
    # Generic addresses get lower score
    generic_locals = ['info', 'contact', 'support', 'admin', 'webmaster', 'noreply']
    if local_part in generic_locals:
        score -= 0.1
    
    # Personal names get higher score if in context
    company_name = context.get('company_name', '').lower()
    if company_name and any(word in local_part for word in company_name.split()):
        score += 0.1
    
    # Source type affects confidence
    source_type = context.get('source_type', 'unknown')
    if source_type == 'posting':
        score += 0.2  # Found in job posting
    elif source_type == 'website':
        score += 0.1  # Found on company website
    
    # MX record validation
    if validate_email_mx(email):
        score += 0.1
    else:
        score -= 0.2
    
    return max(0.0, min(1.0, score))

async def extract_emails_from_url(url: str, max_depth: int = 2) -> List[Tuple[str, float, str]]:
    """Extract emails from a URL and related pages"""
    emails_found = []
    visited_urls = set()
    
    async def crawl_page(page_url: str, depth: int) -> None:
        if depth > max_depth or page_url in visited_urls:
            return
        
        visited_urls.add(page_url)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(page_url)
                if response.status_code != 200:
                    return
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract emails from page text
                page_text = soup.get_text()
                emails = extract_emails_from_text(page_text)
                
                # Get company domain for context
                parsed_url = urlparse(page_url)
                company_domain = parsed_url.netloc
                
                context = {
                    'company_domain': company_domain,
                    'source_type': 'website',
                    'source_url': page_url
                }
                
                for email in emails:
                    confidence = score_email_confidence(email, context)
                    emails_found.append((email, confidence, 'website'))
                
                # If this is the first page, look for contact pages
                if depth == 0:
                    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                    for path in CONTACT_PATHS:
                        contact_url = base_url + path
                        await crawl_page(contact_url, depth + 1)
        
        except Exception:
            pass  # Silently fail for individual pages
    
    await crawl_page(url, 0)
    
    # Remove duplicates and sort by confidence
    unique_emails = {}
    for email, confidence, source in emails_found:
        if email not in unique_emails or confidence > unique_emails[email][0]:
            unique_emails[email] = (confidence, source)
    
    return [(email, conf, src) for email, (conf, src) in unique_emails.items()]

def extract_emails_from_job_posting(posting_text: str, company_name: str = "", apply_url: str = "") -> List[Tuple[str, float, str]]:
    """Extract emails specifically from job posting text"""
    emails = extract_emails_from_text(posting_text)
    
    # Get company domain from apply URL
    company_domain = ""
    if apply_url:
        parsed_url = urlparse(apply_url)
        company_domain = parsed_url.netloc
    
    context = {
        'company_name': company_name,
        'company_domain': company_domain,
        'source_type': 'posting'
    }
    
    results = []
    for email in emails:
        confidence = score_email_confidence(email, context)
        results.append((email, confidence, 'posting'))
    
    return sorted(results, key=lambda x: x[1], reverse=True)

def generate_potential_emails(company_name: str, company_domain: str) -> List[Tuple[str, float, str]]:
    """Generate potential HR emails based on company info"""
    if not company_domain:
        return []
    
    # Clean company name
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', company_name.lower())
    
    potential_emails = []
    
    # Common HR email patterns
    patterns = [
        f"hr@{company_domain}",
        f"careers@{company_domain}",
        f"jobs@{company_domain}",
        f"recruiting@{company_domain}",
        f"internships@{company_domain}",
        f"talent@{company_domain}",
        f"people@{company_domain}",
        f"hiring@{company_domain}"
    ]
    
    for email in patterns:
        # Lower confidence since these are generated
        confidence = 0.3
        if validate_email_mx(email):
            confidence += 0.1
        potential_emails.append((email, confidence, 'generated'))
    
    return potential_emails

async def find_contact_emails(company_name: str, company_url: str, job_posting_text: str = "") -> List[Dict[str, any]]:
    """Main function to find contact emails for a company"""
    all_emails = []
    
    # Extract from job posting if provided
    if job_posting_text:
        posting_emails = extract_emails_from_job_posting(job_posting_text, company_name, company_url)
        all_emails.extend(posting_emails)
    
    # Extract from company website
    if company_url:
        try:
            website_emails = await extract_emails_from_url(company_url)
            all_emails.extend(website_emails)
        except Exception:
            pass  # Continue if website crawling fails
    
    # Generate potential emails
    if company_url:
        parsed_url = urlparse(company_url)
        domain = parsed_url.netloc
        generated_emails = generate_potential_emails(company_name, domain)
        all_emails.extend(generated_emails)
    
    # Deduplicate and format results
    unique_emails = {}
    for email, confidence, source_type in all_emails:
        if email not in unique_emails or confidence > unique_emails[email]['confidence']:
            unique_emails[email] = {
                'email': email,
                'confidence': confidence,
                'source_type': source_type,
                'verified': False
            }
    
    # Sort by confidence and return top results
    results = list(unique_emails.values())
    results.sort(key=lambda x: x['confidence'], reverse=True)
    
    return results[:10]  # Return top 10 emails
