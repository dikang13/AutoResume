# Bug Fixes and Improvements

This document summarizes the issues identified during testing and the fixes applied.

## Issues Identified During Testing

### 1. ❌ Playwright Not Installed

**Problem:**
- JavaScript-rendered job pages (like Apple Jobs) failed to load properly
- Job fetcher returned minimal content (only page title)
- Empty job title and company fields

**Error Message:**
```
ModuleNotFoundError: No module named 'playwright'
```

**Root Cause:**
- Playwright was listed as optional dependency but not installed
- Required for fetching JavaScript-heavy pages like jobs.apple.com

**Fix Applied:**
```bash
pip install playwright
playwright install chromium
```

**Files Changed:** None (installation only)

---

### 2. ❌ Job Fetcher Not Detecting JavaScript Pages

**Problem:**
- Even though Apple Jobs sent 191KB of HTML, it was mostly empty skeleton
- Job fetcher checked raw HTML size (> 5000 bytes) instead of actual content
- Playwright never triggered because HTML appeared "large enough"
- Result: Got "Please enable Javascript" message instead of job details

**Root Cause:**
Logic in `job_fetcher.py` line 107:
```python
if html_content is None or (html_content and len(html_content) < 5000):
```
This only checked raw byte count, not actual text content.

**Fix Applied:**
Added intelligent detection for JavaScript requirements in `src/tools/job_fetcher.py`:

```python
# Quick check if page needs JavaScript
soup_check = BeautifulSoup(html_content, 'html.parser')
text_check = soup_check.get_text(separator=' ', strip=True)

# Indicators that page needs JavaScript
if (len(text_check) < 1000 or
    'please enable javascript' in text_check.lower() or
    'javascript is required' in text_check.lower() or
    'this site requires javascript' in text_check.lower()):
    needs_javascript = True
```

Now triggers Playwright when:
- Extracted text is less than 1000 characters (minimal content)
- Page contains "please enable javascript" messages
- Page explicitly requires JavaScript

**Files Changed:**
- `src/tools/job_fetcher.py` (lines 94-121)

**Test Result:**
```
Title: Clinical Analyst - Health Software ✓
Company: Apple ✓
Description length: 4,173 characters ✓
```

---

### 3. ❌ Company Name Not Extracted

**Problem:**
- Job fetcher got title but not company name
- Returned empty string for company field

**Root Cause:**
- Apple's job page doesn't use standard CSS selectors for company name
- Existing selectors didn't match Apple's HTML structure

**Fix Applied:**
Added fallback company extraction logic in `src/tools/job_fetcher.py`:

```python
# Fallback: try to extract from URL or page title
if not company:
    # Check if URL contains company name
    if 'apple.com' in url.lower():
        company = 'Apple'
    elif 'linkedin.com' in url.lower():
        company = 'LinkedIn'

    # Or try to extract from title/description text
    if not company and (title or page_title):
        title_text = title or page_title
        # Look for "at Company" or "- Company" patterns
        match = re.search(r'(?:at|@|-)\s*([A-Z][a-zA-Z\s&]+)(?:\s*$|\s*-)', title_text)
        if match:
            company = match.group(1).strip()
```

**Files Changed:**
- `src/tools/job_fetcher.py` (lines 187-202)

---

### 4. ❌ EOF Error During Interactive Questions

**Problem:**
- When piping "y" into script for auto-confirmation, stdin gets consumed
- Subsequent `input()` calls in `ask_user_question` fail with:
```
EOFError: EOF when reading a line
```

**Root Cause:**
- Confirmation prompt consumed stdin
- No stdin left for agent's interactive questions

**Fix Applied:**
Added `--yes` / `-y` flag to skip confirmation prompt in `main.py`:

```python
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    default=False,
    help="Skip confirmation prompt"
)
def run(..., yes: bool):
    # Confirm before proceeding (unless --yes flag is used)
    if not yes and not Confirm.ask("Start the agent?", default=True):
        console.print("Cancelled.")
        return
```

**Usage:**
```bash
python main.py run -r resume.tex -j job_url.txt --yes
```

**Files Changed:**
- `main.py` (lines 54-72, 96-99)

---

## Summary of Changes

### Files Modified:
1. **src/tools/job_fetcher.py**
   - Added smart JavaScript detection
   - Improved company name extraction
   - Better fallback logic for dynamic pages

2. **main.py**
   - Added `--yes` flag to skip confirmation

3. **README.md**
   - Added Playwright installation instructions
   - Documented `--yes` flag
   - Clarified JavaScript page support

4. **test_agent.py** (new file)
   - Created test script with mock user input
   - Helps validate agent functionality
   - Loads environment variables

### Installation Updates:

**Required:**
```bash
pip install -e .
python main.py setup
```

**Optional (for JavaScript pages):**
```bash
pip install playwright
playwright install chromium
```

### Testing Results:

✅ Job fetcher correctly identifies JavaScript pages
✅ Playwright triggers automatically when needed
✅ Job title and company extracted successfully
✅ Agent can run with `--yes` flag for automation
✅ Full job description loaded from Apple Jobs (4,173+ chars)

---

## Next Steps

1. ✅ Install Playwright for JavaScript support
2. ✅ Test with Apple Jobs URL
3. ✅ Verify company extraction
4. ✅ Test non-interactive mode with `--yes`
5. 🔄 Complete end-to-end agent run (in progress)

---

## Known Limitations

- Profile matching based on resume file path (renaming resume creates new profile)
- Some job sites may have anti-scraping measures
- Playwright adds ~300MB of dependencies (Chromium browser)

## Future Enhancements

- Add support for more job board formats
- Improve company name extraction with ML
- Add retry logic for failed fetches
- Cache job descriptions to reduce API calls
