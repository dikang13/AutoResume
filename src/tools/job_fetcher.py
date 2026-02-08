"""Tool for fetching and parsing job descriptions from URLs."""

import json
import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class JobDescription(BaseModel):
    """Structured job description data."""

    url: str = Field(description="The URL of the job posting")
    raw_text: str = Field(description="Raw text content of the job posting")
    title: str = Field(default="", description="Job title if found")
    company: str = Field(default="", description="Company name if found")
    requirements: list[str] = Field(default_factory=list, description="Key requirements extracted")


def _extract_json_ld(soup: BeautifulSoup) -> Optional[Dict]:
    """Extract JSON-LD structured data from the page."""
    json_ld_scripts = soup.find_all('script', type='application/ld+json')

    for script in json_ld_scripts:
        try:
            data = json.loads(script.string)
            # Look for JobPosting schema
            if isinstance(data, dict) and data.get('@type') == 'JobPosting':
                return data
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get('@type') == 'JobPosting':
                        return item
        except (json.JSONDecodeError, AttributeError):
            continue

    return None


def _fetch_with_playwright(url: str) -> tuple[str, str]:
    """
    Fetch page content using Playwright for JavaScript-rendered pages.

    Returns:
        Tuple of (html_content, page_title)
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise ImportError(
            "Playwright is not installed. For JavaScript-rendered pages, install with: "
            "uv pip install playwright && playwright install chromium"
        )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto(url, wait_until='networkidle', timeout=30000)
            # Wait a bit for dynamic content to load
            page.wait_for_timeout(2000)

            content = page.content()
            title = page.title()

            return content, title
        finally:
            browser.close()


def fetch_job_description(url: str, use_browser: bool = False) -> JobDescription:
    """
    Fetch and parse a job description from a URL.

    Supports both static HTML and JavaScript-rendered pages (with Playwright).

    Args:
        url: The URL of the job posting
        use_browser: Force using browser automation (Playwright)

    Returns:
        JobDescription object with parsed content

    Raises:
        Exception: If the URL cannot be fetched
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    html_content = None
    page_title = ""
    needs_javascript = False

    # First try regular HTTP request (faster)
    if not use_browser:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            html_content = response.content

            # Quick check if page needs JavaScript
            soup_check = BeautifulSoup(html_content, 'html.parser')
            text_check = soup_check.get_text(separator=' ', strip=True)

            # Indicators that page needs JavaScript
            if (len(text_check) < 1000 or
                'please enable javascript' in text_check.lower() or
                'javascript is required' in text_check.lower() or
                'this site requires javascript' in text_check.lower()):
                needs_javascript = True

        except requests.RequestException:
            # If regular fetch fails, will try browser below
            pass

    # If content needs JavaScript or use_browser is True, try Playwright
    if html_content is None or needs_javascript or use_browser:
        try:
            html_content, page_title = _fetch_with_playwright(url)
        except ImportError as e:
            if html_content is None or needs_javascript:
                raise Exception(
                    f"Failed to fetch {url}. This page may require JavaScript. "
                    f"Install Playwright with: uv pip install playwright && playwright install chromium"
                )
            # Continue with what we have
        except Exception as e:
            if html_content is None:
                raise Exception(f"Failed to fetch job description from {url}: {str(e)}")

    # Parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # Try to extract JSON-LD structured data first
    json_ld = _extract_json_ld(soup)

    title = ""
    company = ""
    description_text = ""

    if json_ld:
        # Extract from structured data
        title = json_ld.get('title', '')

        hiring_org = json_ld.get('hiringOrganization', {})
        if isinstance(hiring_org, dict):
            company = hiring_org.get('name', '')

        description_text = json_ld.get('description', '')

        # Also get qualifications if available
        qualifications = json_ld.get('qualifications', '')
        if qualifications:
            description_text += f"\n\nQualifications:\n{qualifications}"

    # Fallback to HTML parsing
    if not description_text:
        # Remove script, style, and navigation elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()

        description_text = soup.get_text(separator='\n', strip=True)

    if not title:
        # Try to extract title from common selectors
        title_selectors = [
            'h1',
            '[class*="title"]',
            '[class*="job-title"]',
            '[data-automation*="jobTitle"]',
            '[id*="title"]'
        ]
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                title = element.get_text(strip=True)
                break

        # Also try page title as fallback
        if not title and page_title:
            title = page_title

    if not company:
        # Try to extract company from common selectors
        company_selectors = [
            '[class*="company"]',
            '[class*="employer"]',
            '[data-automation*="company"]',
            '[class*="organization"]'
        ]
        for selector in company_selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                company = element.get_text(strip=True)
                break

        # Fallback: try to extract from URL or page title
        if not company:
            # Check if URL contains company name
            if 'apple.com' in url.lower():
                company = 'Apple'
            elif 'linkedin.com' in url.lower():
                company = 'LinkedIn'
            # Add more as needed

            # Or try to extract from title/description text
            if not company and (title or page_title):
                title_text = title or page_title
                # Look for "at Company" or "- Company" patterns
                match = re.search(r'(?:at|@|-)\s*([A-Z][a-zA-Z\s&]+)(?:\s*$|\s*-)', title_text)
                if match:
                    company = match.group(1).strip()

    # Clean up the text
    description_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', description_text)

    return JobDescription(
        url=url,
        raw_text=description_text,
        title=title,
        company=company
    )


def read_job_url_from_file(file_path: str) -> str:
    """
    Read a job URL from a text file.

    Args:
        file_path: Path to the .txt file containing the job URL

    Returns:
        The job URL as a string
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        url = f.read().strip()

    if not url.startswith(('http://', 'https://')):
        raise ValueError(f"Invalid URL in file: {url}")

    return url
