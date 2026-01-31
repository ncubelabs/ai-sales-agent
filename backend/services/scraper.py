"""
Web Scraper Service for AI Sales Agent
Extracts company information from URLs for research prompt input.

Usage:
    from services.scraper import scrape_company_info
    
    result = await scrape_company_info("https://example.com")
    # Returns structured data for research prompt
"""

import asyncio
import re
from dataclasses import dataclass, field, asdict
from typing import Optional
from urllib.parse import urlparse, urljoin
import logging

# Third-party imports - handle gracefully if missing
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class ScrapedCompanyData:
    """Structured output from web scraping."""
    url: str
    domain: str
    company_name: Optional[str] = None
    title: Optional[str] = None
    meta_description: Optional[str] = None
    tagline: Optional[str] = None
    about_text: Optional[str] = None
    services: list[str] = field(default_factory=list)
    industries_mentioned: list[str] = field(default_factory=list)
    team_page_exists: bool = False
    careers_page_exists: bool = False
    contact_info: dict = field(default_factory=dict)
    social_links: dict = field(default_factory=dict)
    tech_signals: list[str] = field(default_factory=list)
    raw_text_sample: Optional[str] = None  # First ~1000 chars of main content
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def to_prompt_context(self) -> str:
        """Format data for inclusion in research prompt."""
        lines = [f"URL: {self.url}", f"Domain: {self.domain}"]
        
        if self.company_name:
            lines.append(f"Company Name: {self.company_name}")
        if self.title:
            lines.append(f"Page Title: {self.title}")
        if self.meta_description:
            lines.append(f"Description: {self.meta_description}")
        if self.tagline:
            lines.append(f"Tagline: {self.tagline}")
        if self.about_text:
            lines.append(f"About: {self.about_text[:500]}...")
        if self.services:
            lines.append(f"Services/Products: {', '.join(self.services[:10])}")
        if self.industries_mentioned:
            lines.append(f"Industries: {', '.join(self.industries_mentioned)}")
        if self.team_page_exists:
            lines.append("Has Team Page: Yes (suggests established company)")
        if self.careers_page_exists:
            lines.append("Has Careers Page: Yes (likely hiring/growing)")
        if self.social_links:
            lines.append(f"Social Presence: {', '.join(self.social_links.keys())}")
        if self.tech_signals:
            lines.append(f"Tech Signals: {', '.join(self.tech_signals)}")
        if self.raw_text_sample:
            lines.append(f"Content Sample: {self.raw_text_sample[:500]}")
            
        return "\n".join(lines)


# Common industry keywords for detection
INDUSTRY_KEYWORDS = {
    "healthcare": ["health", "medical", "clinic", "patient", "doctor", "hospital", "care", "therapy", "wellness"],
    "ecommerce": ["shop", "store", "cart", "buy", "product", "shipping", "retail", "commerce"],
    "saas": ["software", "platform", "cloud", "dashboard", "analytics", "api", "integration", "subscription"],
    "fintech": ["finance", "payment", "banking", "invest", "loan", "insurance", "fintech", "money"],
    "manufacturing": ["manufacturing", "factory", "production", "industrial", "supply chain", "assembly"],
    "real_estate": ["property", "real estate", "realty", "homes", "listings", "broker", "mortgage"],
    "education": ["education", "learning", "school", "course", "training", "student", "teach"],
    "professional_services": ["consulting", "agency", "legal", "accounting", "advisory", "firm"],
}

# Tech stack signals
TECH_SIGNALS = {
    "react": "React.js",
    "angular": "Angular",
    "vue": "Vue.js",
    "wordpress": "WordPress",
    "shopify": "Shopify",
    "hubspot": "HubSpot",
    "salesforce": "Salesforce",
    "intercom": "Intercom",
    "zendesk": "Zendesk",
    "stripe": "Stripe",
    "segment": "Segment",
    "google-analytics": "Google Analytics",
    "hotjar": "Hotjar",
    "mixpanel": "Mixpanel",
}


async def scrape_company_info(url: str, timeout: float = 15.0) -> ScrapedCompanyData:
    """
    Scrape company information from a URL.
    
    Args:
        url: The company website URL
        timeout: Request timeout in seconds
        
    Returns:
        ScrapedCompanyData with extracted information
    """
    # Normalize URL
    if not url.startswith(('http://', 'https://')):
        url = f"https://{url}"
    
    parsed = urlparse(url)
    domain = parsed.netloc.replace('www.', '')
    
    result = ScrapedCompanyData(url=url, domain=domain)
    
    # Check dependencies
    if not HTTPX_AVAILABLE:
        result.error = "httpx not installed. Run: pip install httpx"
        return result
    
    if not BS4_AVAILABLE:
        result.error = "beautifulsoup4 not installed. Run: pip install beautifulsoup4"
        return result
    
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; NCubeResearchBot/1.0)",
                "Accept": "text/html,application/xhtml+xml",
            }
        ) as client:
            # Fetch main page
            response = await client.get(url)
            response.raise_for_status()
            
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract basic info
            result.title = _extract_title(soup)
            result.meta_description = _extract_meta_description(soup)
            result.company_name = _infer_company_name(soup, domain, result.title)
            result.tagline = _extract_tagline(soup)
            result.about_text = _extract_about_text(soup)
            result.services = _extract_services(soup)
            result.contact_info = _extract_contact_info(soup)
            result.social_links = _extract_social_links(soup)
            result.tech_signals = _detect_tech_signals(html)
            result.industries_mentioned = _detect_industries(html)
            result.raw_text_sample = _extract_main_text(soup)[:1000]
            
            # Check for team/careers pages (quick existence check)
            result.team_page_exists = await _page_exists(client, url, ["team", "about-us", "about", "our-team"])
            result.careers_page_exists = await _page_exists(client, url, ["careers", "jobs", "join-us", "work-with-us"])
            
    except httpx.HTTPStatusError as e:
        result.error = f"HTTP error {e.response.status_code}: {str(e)}"
    except httpx.RequestError as e:
        result.error = f"Request failed: {str(e)}"
    except Exception as e:
        result.error = f"Scraping error: {str(e)}"
        logger.exception(f"Unexpected error scraping {url}")
    
    return result


def _extract_title(soup: BeautifulSoup) -> Optional[str]:
    """Extract page title."""
    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.get_text(strip=True)
        # Clean common suffixes
        for sep in [' | ', ' - ', ' – ', ' — ']:
            if sep in title:
                title = title.split(sep)[0].strip()
        return title
    return None


def _extract_meta_description(soup: BeautifulSoup) -> Optional[str]:
    """Extract meta description."""
    meta = soup.find('meta', attrs={'name': 'description'})
    if meta and meta.get('content'):
        return meta['content'].strip()
    
    # Try Open Graph description
    og_desc = soup.find('meta', attrs={'property': 'og:description'})
    if og_desc and og_desc.get('content'):
        return og_desc['content'].strip()
    
    return None


def _infer_company_name(soup: BeautifulSoup, domain: str, title: Optional[str]) -> Optional[str]:
    """Infer company name from various sources."""
    # Try Open Graph site name
    og_site = soup.find('meta', attrs={'property': 'og:site_name'})
    if og_site and og_site.get('content'):
        return og_site['content'].strip()
    
    # Try structured data
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            import json
            data = json.loads(script.string)
            if isinstance(data, dict):
                if data.get('name'):
                    return data['name']
                if data.get('organization', {}).get('name'):
                    return data['organization']['name']
        except:
            pass
    
    # Use title if it looks like a company name
    if title and len(title) < 50:
        return title
    
    # Fall back to cleaned domain
    name = domain.split('.')[0]
    return name.replace('-', ' ').replace('_', ' ').title()


def _extract_tagline(soup: BeautifulSoup) -> Optional[str]:
    """Extract tagline or hero text."""
    # Common tagline locations
    selectors = [
        ('h1', {}),
        ('h2', {}),
        ('.tagline', {}),
        ('.hero-text', {}),
        ('.headline', {}),
        ('p', {'class': re.compile(r'hero|tagline|subtitle|lead', re.I)}),
    ]
    
    for tag, attrs in selectors:
        elem = soup.find(tag, attrs) if attrs else soup.find(tag)
        if elem:
            text = elem.get_text(strip=True)
            if 20 < len(text) < 200:  # Reasonable tagline length
                return text
    
    return None


def _extract_about_text(soup: BeautifulSoup) -> Optional[str]:
    """Extract about/mission text."""
    # Look for about sections
    about_section = soup.find(id=re.compile(r'about', re.I)) or \
                   soup.find(class_=re.compile(r'about', re.I))
    
    if about_section:
        text = about_section.get_text(separator=' ', strip=True)
        return text[:500] if text else None
    
    return None


def _extract_services(soup: BeautifulSoup) -> list[str]:
    """Extract services/products mentioned."""
    services = []
    
    # Look for service sections
    service_section = soup.find(id=re.compile(r'service|product|solution|feature', re.I)) or \
                     soup.find(class_=re.compile(r'service|product|solution|feature', re.I))
    
    if service_section:
        for item in service_section.find_all(['h3', 'h4', 'li']):
            text = item.get_text(strip=True)
            if 3 < len(text) < 100:
                services.append(text)
    
    # Also check nav menu for service indicators
    nav = soup.find('nav')
    if nav:
        for link in nav.find_all('a'):
            text = link.get_text(strip=True)
            href = link.get('href', '')
            if any(kw in href.lower() for kw in ['service', 'product', 'solution']):
                if 3 < len(text) < 50:
                    services.append(text)
    
    return list(set(services))[:10]


def _extract_contact_info(soup: BeautifulSoup) -> dict:
    """Extract contact information."""
    contact = {}
    
    # Email
    email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', soup.get_text())
    if email_match:
        contact['email'] = email_match.group()
    
    # Phone
    phone_match = re.search(r'[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}', soup.get_text())
    if phone_match:
        contact['phone'] = phone_match.group()
    
    # Address (look for structured data)
    address = soup.find(attrs={'itemprop': 'address'})
    if address:
        contact['address'] = address.get_text(strip=True)
    
    return contact


def _extract_social_links(soup: BeautifulSoup) -> dict:
    """Extract social media links."""
    social = {}
    social_domains = {
        'linkedin.com': 'linkedin',
        'twitter.com': 'twitter',
        'x.com': 'twitter',
        'facebook.com': 'facebook',
        'instagram.com': 'instagram',
        'youtube.com': 'youtube',
        'github.com': 'github',
    }
    
    for link in soup.find_all('a', href=True):
        href = link['href'].lower()
        for domain, name in social_domains.items():
            if domain in href and name not in social:
                social[name] = href
    
    return social


def _detect_tech_signals(html: str) -> list[str]:
    """Detect technology signals from HTML source."""
    signals = []
    html_lower = html.lower()
    
    for keyword, tech_name in TECH_SIGNALS.items():
        if keyword in html_lower:
            signals.append(tech_name)
    
    return signals


def _detect_industries(html: str) -> list[str]:
    """Detect mentioned industries."""
    industries = []
    html_lower = html.lower()
    
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw in html_lower)
        if matches >= 2:  # At least 2 keyword matches
            industries.append(industry)
    
    return industries


def _extract_main_text(soup: BeautifulSoup) -> str:
    """Extract main body text content."""
    # Remove script, style, nav, footer
    for element in soup.find_all(['script', 'style', 'nav', 'footer', 'header']):
        element.decompose()
    
    # Get main content
    main = soup.find('main') or soup.find('article') or soup.find('body')
    if main:
        text = main.get_text(separator=' ', strip=True)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        return text
    
    return ""


async def _page_exists(client: "httpx.AsyncClient", base_url: str, paths: list[str]) -> bool:
    """Check if any of the given paths exist."""
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    
    for path in paths:
        try:
            url = urljoin(base, f"/{path}")
            response = await client.head(url, timeout=5.0)
            if response.status_code == 200:
                return True
        except:
            pass
    
    return False


# Synchronous wrapper for non-async contexts
def scrape_company_info_sync(url: str, timeout: float = 15.0) -> ScrapedCompanyData:
    """Synchronous version of scrape_company_info."""
    return asyncio.run(scrape_company_info(url, timeout))


# Simple test
if __name__ == "__main__":
    import sys
    
    async def test():
        url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
        print(f"Scraping: {url}\n")
        
        result = await scrape_company_info(url)
        
        if result.error:
            print(f"Error: {result.error}")
        else:
            print("=== Scraped Data ===")
            print(result.to_prompt_context())
    
    asyncio.run(test())
