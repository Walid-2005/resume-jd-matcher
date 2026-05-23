"""
Fetch job descriptions from LinkedIn and Indeed job listing URLs.

Uses multiple extraction strategies with fallbacks:
1. JSON-LD structured data (most reliable)
2. Open Graph / meta tag descriptions
3. HTML content extraction from known selectors
"""
import json
import re
import html as html_mod
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


# ── Constants ────────────────────────────────────────────────────────────

_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}

_REQUEST_TIMEOUT = 15  # seconds

_SUPPORTED_PLATFORMS = {
    'linkedin': ['linkedin.com'],
    'indeed': ['indeed.com'],
}


# ── Public API ───────────────────────────────────────────────────────────

class JobFetchError(Exception):
    """Raised when a job description cannot be fetched."""
    pass


def fetch_job_description(url: str) -> dict:
    """Fetch a job description from a supported job board URL.

    Returns a dict with:
        title:       str  – job title (or empty string)
        company:     str  – company name (or empty string)
        location:    str  – location (or empty string)
        description: str  – full job description text
        platform:    str  – 'linkedin' | 'indeed' | 'other'
        url:         str  – the original URL
    """
    url = url.strip()
    if not url:
        raise JobFetchError('URL is required')

    # Validate URL
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https'):
        raise JobFetchError('URL must start with http:// or https://')

    platform = _detect_platform(parsed.hostname or '')

    if platform == 'linkedin':
        return _fetch_linkedin(url)
    elif platform == 'indeed':
        return _fetch_indeed(url)
    else:
        raise JobFetchError(
            'Unsupported URL. Please paste a LinkedIn or Indeed job listing URL.'
        )


# ── Platform detection ───────────────────────────────────────────────────

def _detect_platform(hostname: str) -> str:
    hostname = hostname.lower()
    for platform, domains in _SUPPORTED_PLATFORMS.items():
        for domain in domains:
            if hostname == domain or hostname.endswith('.' + domain):
                return platform
    return 'other'


# ── LinkedIn ─────────────────────────────────────────────────────────────

def _fetch_linkedin(url: str) -> dict:
    """Fetch job description from a LinkedIn job URL.

    LinkedIn public job pages contain JSON-LD structured data and
    description content accessible without authentication.
    """
    html = _download_page(url)
    soup = BeautifulSoup(html, 'lxml')

    result = {
        'title': '',
        'company': '',
        'location': '',
        'description': '',
        'platform': 'linkedin',
        'url': url,
    }

    # Strategy 1: JSON-LD structured data
    json_ld = _extract_json_ld(soup, 'JobPosting')
    if json_ld:
        result['title'] = json_ld.get('title', '')
        hiring_org = json_ld.get('hiringOrganization', {})
        if isinstance(hiring_org, dict):
            result['company'] = hiring_org.get('name', '')
        location = json_ld.get('jobLocation', {})
        if isinstance(location, dict):
            address = location.get('address', {})
            if isinstance(address, dict):
                parts = [
                    address.get('addressLocality', ''),
                    address.get('addressRegion', ''),
                    address.get('addressCountry', ''),
                ]
                result['location'] = ', '.join(p for p in parts if p)
            elif isinstance(address, str):
                result['location'] = address
        desc = json_ld.get('description', '')
        if desc:
            result['description'] = _html_to_text(desc)
            return result

    # Strategy 2: LinkedIn-specific selectors
    # Public job pages use these class patterns
    _linkedin_desc_selectors = [
        'div.show-more-less-html__markup',
        'div.description__text',
        'section.description div.core-section-container__content',
        'div[class*="description"]',
        'div.decorated-job-posting__details',
    ]
    for selector in _linkedin_desc_selectors:
        el = soup.select_one(selector)
        if el and len(el.get_text(strip=True)) > 50:
            result['description'] = _element_to_text(el)
            break

    # Title fallback
    if not result['title']:
        for sel in ['h1.top-card-layout__title', 'h1[class*="title"]', 'h1']:
            el = soup.select_one(sel)
            if el:
                result['title'] = el.get_text(strip=True)
                break

    # Company fallback
    if not result['company']:
        for sel in [
            'a.topcard__org-name-link',
            'span.topcard__flavor',
            'a[class*="company"]',
        ]:
            el = soup.select_one(sel)
            if el:
                result['company'] = el.get_text(strip=True)
                break

    # Location fallback
    if not result['location']:
        for sel in [
            'span.topcard__flavor--bullet',
            'span[class*="location"]',
        ]:
            el = soup.select_one(sel)
            if el:
                result['location'] = el.get_text(strip=True)
                break

    # Strategy 3: Meta tag description as last resort
    if not result['description']:
        result['description'] = _extract_meta_description(soup)

    if not result['description']:
        raise JobFetchError(
            'Could not extract job description from this LinkedIn URL. '
            'The listing may be expired, private, or require authentication. '
            'Try copying the description manually.'
        )

    return result


# ── Indeed ───────────────────────────────────────────────────────────────

def _fetch_indeed(url: str) -> dict:
    """Fetch job description from an Indeed job URL."""
    html = _download_page(url)
    soup = BeautifulSoup(html, 'lxml')

    result = {
        'title': '',
        'company': '',
        'location': '',
        'description': '',
        'platform': 'indeed',
        'url': url,
    }

    # Strategy 1: JSON-LD
    json_ld = _extract_json_ld(soup, 'JobPosting')
    if json_ld:
        result['title'] = json_ld.get('title', '')
        hiring_org = json_ld.get('hiringOrganization', {})
        if isinstance(hiring_org, dict):
            result['company'] = hiring_org.get('name', '')
        location = json_ld.get('jobLocation', {})
        if isinstance(location, dict):
            address = location.get('address', {})
            if isinstance(address, dict):
                parts = [
                    address.get('addressLocality', ''),
                    address.get('addressRegion', ''),
                ]
                result['location'] = ', '.join(p for p in parts if p)
        desc = json_ld.get('description', '')
        if desc:
            result['description'] = _html_to_text(desc)
            return result

    # Strategy 2: Indeed-specific selectors
    _indeed_desc_selectors = [
        'div#jobDescriptionText',
        'div.jobsearch-jobDescriptionText',
        'div[class*="jobDescription"]',
        'div[id*="jobDescription"]',
    ]
    for selector in _indeed_desc_selectors:
        el = soup.select_one(selector)
        if el and len(el.get_text(strip=True)) > 50:
            result['description'] = _element_to_text(el)
            break

    # Title fallback
    if not result['title']:
        for sel in ['h1.jobsearch-JobInfoHeader-title', 'h1[class*="Title"]', 'h1']:
            el = soup.select_one(sel)
            if el:
                result['title'] = el.get_text(strip=True)
                break

    # Company fallback
    if not result['company']:
        for sel in ['div[data-company-name]', 'span[class*="company"]']:
            el = soup.select_one(sel)
            if el:
                result['company'] = el.get_text(strip=True)
                break

    # Strategy 3: Meta description
    if not result['description']:
        result['description'] = _extract_meta_description(soup)

    if not result['description']:
        raise JobFetchError(
            'Could not extract job description from this Indeed URL. '
            'The listing may be expired or require login. '
            'Try copying the description manually.'
        )

    return result


# ── Helpers ──────────────────────────────────────────────────────────────

def _download_page(url: str) -> str:
    """Download a page and return its HTML content."""
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=_REQUEST_TIMEOUT, allow_redirects=True)
        resp.raise_for_status()
        return resp.text
    except requests.exceptions.Timeout:
        raise JobFetchError('Request timed out. Please try again.')
    except requests.exceptions.ConnectionError:
        raise JobFetchError('Could not connect to the website. Check your internet connection.')
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 429:
            raise JobFetchError('Rate limited by the website. Please wait a moment and try again.')
        if e.response is not None and e.response.status_code in (401, 403):
            raise JobFetchError(
                'Access denied. This job listing may require authentication. '
                'Try copying the description manually.'
            )
        raise JobFetchError(f'Failed to fetch the page (HTTP {e.response.status_code if e.response else "?"}).')
    except requests.exceptions.RequestException:
        raise JobFetchError('Failed to fetch the page. Please check the URL and try again.')


def _extract_json_ld(soup: BeautifulSoup, target_type: str) -> dict | None:
    """Extract JSON-LD data of a specific @type from the page."""
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string or '')
            # Handle both single object and array of objects
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict):
                    item_type = item.get('@type', '')
                    if isinstance(item_type, list):
                        if target_type in item_type:
                            return item
                    elif item_type == target_type:
                        return item
                    # Check @graph
                    for graph_item in item.get('@graph', []):
                        if isinstance(graph_item, dict):
                            gt = graph_item.get('@type', '')
                            if gt == target_type or (isinstance(gt, list) and target_type in gt):
                                return graph_item
        except (json.JSONDecodeError, TypeError):
            continue
    return None


def _extract_meta_description(soup: BeautifulSoup) -> str:
    """Extract description from meta tags (og:description or name=description)."""
    for attr, key in [
        ({'property': 'og:description'}, 'content'),
        ({'name': 'description'}, 'content'),
        ({'name': 'twitter:description'}, 'content'),
    ]:
        tag = soup.find('meta', attrs=attr)
        if tag and tag.get(key):
            text = tag[key].strip()
            if len(text) > 50:
                return text
    return ''


def _html_to_text(html_content: str) -> str:
    """Convert an HTML string (e.g. from JSON-LD description) to clean text."""
    soup = BeautifulSoup(html_content, 'lxml')
    return _element_to_text(soup)


def _element_to_text(el) -> str:
    """Convert a BS4 element to readable plain text, preserving list structure."""
    # Replace <br> with newlines
    for br in el.find_all('br'):
        br.replace_with('\n')
    # Replace <li> with bullet points
    for li in el.find_all('li'):
        li.insert(0, '\n- ')
    # Replace block-level tags with newlines
    for tag in el.find_all(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        tag.insert(0, '\n')
        tag.append('\n')

    text = el.get_text()

    # Clean up whitespace
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            lines.append(stripped)

    return '\n'.join(lines)
