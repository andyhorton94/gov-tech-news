# UK Government & Policy News Scraper

A Python script that scrapes articles from UK government and policy websites, filtering for tech, AI, and consultancy-themed content.

## Prerequisites

### 1. Install Python

**Windows:**
- Download Python from https://www.python.org/downloads/
- During installation, check "Add Python to PATH"
- Verify: Open Command Prompt and run `python --version`

**Mac:**
- Install via Homebrew: `brew install python3`
- Or download from https://www.python.org/downloads/

**Linux:**
- Usually pre-installed. If not: `sudo apt install python3` (Ubuntu/Debian)

### 2. Install Dependencies

Open your terminal/command prompt and run:

```bash
pip install requests beautifulsoup4 rapidfuzz
```

## Usage

### Basic Usage

```bash
python scraper.py
```

### Output Files

The script generates timestamped markdown files:

| File Pattern | Description |
|--------------|-------------|
| `articles_YYYY-MM-DD_HHMM.md` | All articles in Markdown format |
| `filtered_YYYY-MM-DD_HHMM.md` | Filtered articles (tech/AI/consultancy) in Markdown |
| `latest.json` | Stores latest filenames for easy discovery |

**Example:**
- `articles_2026-03-03_0927.md` - All articles from March 3rd, 2026 at 09:27
- `filtered_2026-03-03_0927.md` - Filtered articles from same run

> **Tip:** Use `viewer.html` to easily browse all articles!

## Using the HTML Viewer

Open `viewer.html` in your web browser (double-click or drag into browser).

**How to use:**
1. Run `python scraper.py` to generate article files
2. Open `viewer.html` in your browser
3. Click **"Open File"** button
4. Select a markdown file (e.g., `filtered_2026-03-03_0927.md`)
5. Use **Filtered/All** buttons to toggle between views
6. Click article links to open in new tab

**Features:**
- Clean, modern design (shadcn-inspired)
- Toggle between "All" and "Filtered" views
- Click article links to open in new tab
- Works on desktop and mobile

## Configuration

### Adjusting the Time Window

Change `DAYS_TO_SCRAPE` in `scraper.py`:

```python
DAYS_TO_SCRAPE = 7  # Change to desired number of days
```

### Adjusting Keywords

Edit the `KEYWORDS` dict in `scraper.py`:

```python
KEYWORDS = {
    "tech": ["technology", "tech", "digital", "software", "cyber", "data", "cloud", "ai", "machine learning"],
    "ai": ["ai", "artificial intelligence", "machine learning", "ml", "automation", "generative", "llm", "deep learning", "neural"],
    "consultancy": ["consultancy", "consulting", "advisory", "strategy", "consultant"]
}
```

### Adjusting Fuzzy Match Threshold

Change `FUZZY_THRESHOLD` (default: 70):

```python
FUZZY_THRESHOLD = 70  # 0-100, lower = more lenient matching
```

## Scraped Sources

1. **GOV.UK Blog** - https://www.blog.gov.uk/all-posts/
2. **National Audit Office** - https://www.nao.org.uk/reports/
3. **Institute for Government** - https://www.instituteforgovernment.org.uk/
4. **techUK** - https://www.techuk.org/developing-markets/central-government.html
5. **Policy Exchange** - https://policyexchange.org.uk/publications/

## Adding New Sources

> **Need help?** If you're not comfortable editing the code yourself, you can use AI assistants to help:
> - **Opencode** - I'm here to help! Just tell me the URL and I'll add the source for you.
> - **GitHub Copilot in VS Code** - Start typing a comment like `# scrape new site` and Copilot will suggest code.
> - **ChatGPT/Claude** - Paste the template below and the URL, and ask them to generate the scraper function.

To add a new source, you need to create a new scraping function in `scraper.py`. Here's the template:

```python
def scrape_your_source() -> List[Dict]:
    """Scrape your source name."""
    url = "https://your-source-url.com/articles"
    articles = []
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find article elements - adjust CSS selector for your source
        for item in soup.select(".article-item, article, .post"):
            # Extract date - adjust selector
            date_elem = item.find("time") or item.select_one(".date")
            
            # Extract link - adjust selector  
            link = item.find("a", href=True)
            
            if not link:
                continue
            
            # Parse date
            datetime_val = safe_get_attr(date_elem, "datetime") if date_elem else ""
            if datetime_val:
                try:
                    article_date = datetime.fromisoformat(datetime_val.replace("+00:00", ""))
                except ValueError:
                    article_date = parse_date(date_elem.get_text(strip=True)) if date_elem else None
            else:
                article_date = parse_date(date_elem.get_text(strip=True)) if date_elem else None
            
            # Get title
            title = link.get_text(strip=True)
            
            if title and article_date and is_within_days(article_date):
                href = safe_get_attr(link, "href")
                if href and not href.startswith("http"):
                    href = urljoin(url, href)
                articles.append({
                    "date": article_date.strftime("%Y-%m-%d"),
                    "title": title,
                    "link": href,
                    "source": "Your Source Name"
                })
    except Exception as e:
        print(f"Error scraping Your Source: {e}")
    
    return articles
```

Then add your function call in the `main()` function:

```python
print("Scraping Your Source...")
all_articles.extend(scrape_your_source())
```

### Tips for Finding CSS Selectors

1. Visit the website in your browser
2. Right-click on an article title → Inspect
3. Note the HTML tag and class names (e.g., `article`, `.post-title`)
4. Test selectors using browser DevTools (Ctrl+F in Elements panel)

### Common Selectors

| Element | Selector Examples |
|---------|-------------------|
| Article | `article`, `.article`, `.post-item` |
| Title | `h2`, `h3`, `.title`, `.post-title` |
| Date | `time`, `.date`, `.pub-date` |
| Link | `a[href]`, `.post-link` |

## Troubleshooting

### "pip is not recognized"
Use `python -m pip install` instead of `pip install`

### SSL Certificate Errors
Add this to the top of the script (after imports):
```python
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
```

### No articles found
Some websites may have changed their structure. Check the console output for errors.

## Requirements

- Python 3.7+
- requests
- beautifulsoup4
- rapidfuzz
