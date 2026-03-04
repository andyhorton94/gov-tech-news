#!/usr/bin/env python3
"""
UK Government & Policy News Scraper
Scrapes articles from the last 7 days from various UK government/policy websites.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from urllib.parse import urljoin
from rapidfuzz import fuzz

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

DAYS_TO_SCRAPE = 7

KEYWORDS = {
    "tech": ["technology", "tech", "digital", "software", "cyber", "data", "cloud", "ai", "machine learning", "artificial intelligence", "automation", "generative", "llm", "deep learning", "neural", "ml", "software", "it", "information technology", "computer", "computing", "robotics", "automation", "smart", "innovation", "r&d", "research and development"],
    "farming": ["farming", "farm", "farms", "rural", "agriculture", "agricultural", "countryside", "food", "food security", "rural affairs", "environment", "environmental", "climate", "carbon", "net zero", "sustainability", "sustainable", "wildlife", "nature", "conservation", "fishing", "fisheries", "forestry", "woodland", "crops", "livestock", "cattle", "sheep"],
    "economic": ["economic", "economy", "budget", "fiscal", "tax", "spending", "gdp", "growth", "inflation", "treasury", "finance", "financial", "investment", "bank", "banking", "interest rate", "monetary", "pound", "sterling", "public sector", "government spending", "deficit", "debt", "productivity", "trade", "exports", "imports", "business", "enterprise", "smb", "smes", "startup", "jobs", "employment", "wages", "salary", "living wage", "cost of living", "cost of living crisis", "energy prices", "energy crisis"]
}

FUZZY_THRESHOLD = 70


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse various date formats."""
    date_formats = [
        "%d %B %Y",
        "%d %b %Y",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%B %d, %Y",
    ]
    date_str = str(date_str).strip()
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def make_naive(dt: datetime) -> datetime:
    """Convert timezone-aware datetime to naive for comparison."""
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


def is_within_days(date: datetime, days: int = DAYS_TO_SCRAPE) -> bool:
    """Check if a date is within the last N days."""
    date = make_naive(date)
    now = datetime.now()
    cutoff = now - timedelta(days=days)
    return cutoff <= date <= now


def safe_get_attr(element, attr: str, default: str = "") -> str:
    """Safely get an attribute from a BeautifulSoup element."""
    val = element.get(attr)
    return str(val) if val else default


def get_article_tags(title: str) -> List[str]:
    """Get tags for an article based on keyword matching."""
    title_lower = title.lower()
    tags = []
    for category, keywords in KEYWORDS.items():
        for keyword in keywords:
            score = fuzz.ratio(keyword.lower(), title_lower)
            partial_score = fuzz.partial_ratio(keyword.lower(), title_lower)
            if score >= FUZZY_THRESHOLD or partial_score >= FUZZY_THRESHOLD + 10:
                if category not in tags:
                    tags.append(category)
                break
    return tags


def generate_markdown(articles: List[Dict], title: str) -> str:
    """Generate markdown output from articles list."""
    markdown = f"# {title}\n"
    markdown += f"Articles from the last {DAYS_TO_SCRAPE} days\n\n"
    
    current_date = ""
    for article in articles:
        if article["date"] != current_date:
            current_date = article["date"]
            markdown += f"## {current_date}\n\n"
        markdown += f"- [{article['title']}]({article['link']})  \n"
        markdown += f"  *Source: {article['source']}*"
        if article.get("tags"):
            tags_str = ", ".join(article["tags"])
            markdown += f"\n  *Tags: {tags_str}*"
        markdown += "\n\n"
    
    return markdown


def scrape_gov_blog() -> List[Dict]:
    """Scrape GOV.UK blog posts."""
    url = "https://www.blog.gov.uk/all-posts/"
    articles = []
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        posts = soup.select("ul.blogs-list li")
        for post in posts:
            time_tag = post.find("time")
            if not time_tag:
                continue
            
            link = post.find("a", class_="govuk-link")
            if not link:
                continue
            
            datetime_val = safe_get_attr(time_tag, "datetime")
            if datetime_val:
                try:
                    article_date = datetime.fromisoformat(datetime_val.replace("+00:00", ""))
                except ValueError:
                    article_date = parse_date(time_tag.get_text(strip=True))
            else:
                article_date = parse_date(time_tag.get_text(strip=True))
            
            if article_date and is_within_days(article_date):
                articles.append({
                    "date": article_date.strftime("%Y-%m-%d"),
                    "title": link.get_text(strip=True),
                    "link": safe_get_attr(link, "href"),
                    "source": "GOV.UK Blog"
                })
    except Exception as e:
        print(f"Error scraping GOV.UK Blog: {e}")
    
    return articles


def scrape_nao_reports() -> List[Dict]:
    """Scrape NAO reports."""
    url = "https://www.nao.org.uk/reports/"
    articles = []
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        cards = soup.select(".card--report, .aggregate-posts__item")
        for card in cards:
            time_tag = card.find("time", class_="card__date")
            if not time_tag:
                continue
            
            link = card.find("a", class_="card__link")
            if not link:
                continue
            
            datetime_val = safe_get_attr(time_tag, "datetime")
            if datetime_val:
                try:
                    article_date = datetime.fromisoformat(datetime_val.replace("+00:00", ""))
                except ValueError:
                    article_date = parse_date(time_tag.get_text(strip=True))
            else:
                article_date = parse_date(time_tag.get_text(strip=True))
            
            if article_date and is_within_days(article_date):
                href = safe_get_attr(link, "href")
                articles.append({
                    "date": article_date.strftime("%Y-%m-%d"),
                    "title": link.get_text(strip=True),
                    "link": urljoin(url, href) if href else "",
                    "source": "National Audit Office"
                })
    except Exception as e:
        print(f"Error scraping NAO: {e}")
    
    return articles


def scrape_ifg() -> List[Dict]:
    """Scrape Institute for Government articles."""
    url = "https://www.instituteforgovernment.org.uk/"
    articles = []
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        for article in soup.select("article, .content-card, .featured__item, .list-item, .teaser"):
            date_elem = article.find("time") or article.select_one(".date, .pub-date, [class*='date']")
            link = article.find("a")
            
            if not date_elem or not link:
                continue
            
            datetime_val = safe_get_attr(date_elem, "datetime")
            if datetime_val:
                try:
                    article_date = datetime.fromisoformat(datetime_val.replace("+00:00", ""))
                except ValueError:
                    article_date = parse_date(date_elem.get_text(strip=True))
            else:
                article_date = parse_date(date_elem.get_text(strip=True))
            
            if article_date and is_within_days(article_date):
                href = safe_get_attr(link, "href")
                if href and not href.startswith("http"):
                    href = urljoin("https://www.instituteforgovernment.org.uk", href)
                articles.append({
                    "date": article_date.strftime("%Y-%m-%d"),
                    "title": link.get_text(strip=True),
                    "link": href,
                    "source": "Institute for Government"
                })
    except Exception as e:
        print(f"Error scraping Institute for Government: {e}")
    
    return articles


def scrape_techuk() -> List[Dict]:
    """Scrape techUK central government section."""
    url = "https://www.techuk.org/developing-markets/central-government.html"
    articles = []
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        for item in soup.select(".slider-item, .banner, .content-item, .resource-item, article"):
            date_elem = item.find("time") or item.select_one(".date, .pub-date")
            title_elem = item.find(["h3", "h4", "a"])
            
            if not title_elem:
                continue
            
            link = title_elem.find("a") if title_elem.name != "a" else title_elem
            if not link:
                continue
            
            datetime_val = safe_get_attr(date_elem, "datetime") if date_elem else ""
            if datetime_val:
                try:
                    article_date = datetime.fromisoformat(datetime_val.replace("+00:00", ""))
                except ValueError:
                    article_date = parse_date(date_elem.get_text(strip=True)) if date_elem else None
            else:
                article_date = parse_date(date_elem.get_text(strip=True)) if date_elem else None
            
            title = link.get_text(strip=True)
            if title and len(title) > 10 and article_date and is_within_days(article_date):
                href = safe_get_attr(link, "href")
                if href and not href.startswith("http"):
                    href = urljoin(url, href)
                articles.append({
                    "date": article_date.strftime("%Y-%m-%d"),
                    "title": title,
                    "link": href,
                    "source": "techUK"
                })
    except Exception as e:
        print(f"Error scraping techUK: {e}")
    
    return articles


def scrape_policy_exchange() -> List[Dict]:
    """Scrape Policy Exchange publications."""
    url = "https://policyexchange.org.uk/publications/"
    articles = []
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        for article in soup.select(".elementor-post, .post-item, .publication-item, article"):
            date_elem = article.find("time") or article.select_one(".date, .pub-date")
            link = article.find("a", href=True)
            
            if not link:
                continue
            
            datetime_val = safe_get_attr(date_elem, "datetime") if date_elem else ""
            if datetime_val:
                try:
                    article_date = datetime.fromisoformat(datetime_val.replace("+00:00", ""))
                except ValueError:
                    article_date = parse_date(date_elem.get_text(strip=True)) if date_elem else None
            else:
                article_date = parse_date(date_elem.get_text(strip=True)) if date_elem else None
            
            title = link.get_text(strip=True)
            if title and len(title) > 10:
                if article_date and is_within_days(article_date):
                    href = safe_get_attr(link, "href")
                    if href and not href.startswith("http"):
                        href = urljoin(url, href)
                    articles.append({
                        "date": article_date.strftime("%Y-%m-%d"),
                        "title": title,
                        "link": href,
                        "source": "Policy Exchange"
                    })
    except Exception as e:
        print(f"Error scraping Policy Exchange: {e}")
    
    return articles


def main():
    """Main function to scrape all sources and output results."""
    print("=" * 60)
    print("UK Government & Policy News Scraper")
    print(f"Scraping articles from the last {DAYS_TO_SCRAPE} days")
    print("=" * 60)
    print()
    
    all_articles = []
    
    print("Scraping GOV.UK Blog...")
    all_articles.extend(scrape_gov_blog())
    print(f"  Found {len(all_articles)} articles so far")
    
    print("Scraping National Audit Office...")
    all_articles.extend(scrape_nao_reports())
    print(f"  Found {len(all_articles)} articles so far")
    
    print("Scraping Institute for Government...")
    all_articles.extend(scrape_ifg())
    print(f"  Found {len(all_articles)} articles so far")
    
    print("Scraping techUK...")
    all_articles.extend(scrape_techuk())
    print(f"  Found {len(all_articles)} articles so far")
    
    print("Scraping Policy Exchange...")
    all_articles.extend(scrape_policy_exchange())
    print(f"  Found {len(all_articles)} articles so far")
    
    seen_links = set()
    unique_articles = []
    for article in all_articles:
        link = article["link"]
        if link not in seen_links:
            seen_links.add(link)
            unique_articles.append(article)
    all_articles = unique_articles
    
    all_articles.sort(key=lambda x: x["date"], reverse=True)
    
    for article in all_articles:
        article["tags"] = get_article_tags(article["title"])
    
    print()
    print("=" * 60)
    print(f"Total articles found: {len(all_articles)}")
    
    tagged_count = sum(1 for a in all_articles if a["tags"])
    print(f"Articles with tags: {tagged_count}")
    print("=" * 60)
    print()
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    
    markdown_output = generate_markdown(all_articles, "UK Government & Policy News")
    
    print(markdown_output)
    
    output_md = f"articles_{timestamp}.md"
    with open(output_md, "w", encoding="utf-8") as f:
        f.write(markdown_output)
    print(f"Markdown saved to {output_md}")
    
    import json
    latest_info = {
        "latest_all": output_md,
        "timestamp": timestamp
    }
    with open("latest.json", "w") as f:
        json.dump(latest_info, f)
    print("Latest info saved to latest.json")


if __name__ == "__main__":
    main()
