"""Tool for fetching and parsing job descriptions from URLs."""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Any
from pydantic import BaseModel, Field


class JobDescription(BaseModel):
    """Structured job description data."""

    url: str = Field(description="The URL of the job posting")
    raw_text: str = Field(description="Raw text content of the job posting")
    title: str = Field(default="", description="Job title if found")
    company: str = Field(default="", description="Company name if found")
    requirements: list[str] = Field(default_factory=list, description="Key requirements extracted")


def fetch_job_description(url: str) -> JobDescription:
    """
    Fetch and parse a job description from a URL.

    Args:
        url: The URL of the job posting

    Returns:
        JobDescription object with parsed content

    Raises:
        requests.RequestException: If the URL cannot be fetched
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        raise Exception(f"Failed to fetch job description from {url}: {str(e)}")

    soup = BeautifulSoup(response.content, 'html.parser')

    # Remove script and style elements
    for script in soup(["script", "style", "nav", "footer", "header"]):
        script.decompose()

    # Get text content
    text = soup.get_text(separator='\n', strip=True)

    # Try to extract title and company (basic heuristics)
    title = ""
    company = ""

    # Common selectors for job titles
    title_selectors = ['h1', '[class*="title"]', '[class*="job-title"]']
    for selector in title_selectors:
        element = soup.select_one(selector)
        if element and element.get_text(strip=True):
            title = element.get_text(strip=True)
            break

    # Common selectors for company names
    company_selectors = ['[class*="company"]', '[class*="employer"]']
    for selector in company_selectors:
        element = soup.select_one(selector)
        if element and element.get_text(strip=True):
            company = element.get_text(strip=True)
            break

    return JobDescription(
        url=url,
        raw_text=text,
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
