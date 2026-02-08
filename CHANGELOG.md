# Changelog

## Version 0.2.0 - Enhanced Agent Features

### New Features

#### 1. User Memory/Profile System
- **Persistent Memory**: Agent now remembers your experience, skills, and preferences across sessions
- **Automatic Profile Creation**: Creates a user profile on first use based on your resume file
- **Profile Loading**: Automatically loads your profile when using the same resume
- **Smart Context**: Uses saved information to provide better assistance without asking repeated questions
- **Privacy-Focused**: Profiles stored locally in `.user_profiles/` directory (git-ignored)

**How it works:**
- First time: Creates profile, learns about you during conversation
- Return visits: Loads your profile, references past conversations
- Agent uses `save_user_info` tool to remember important details you share

#### 2. One Question at a Time
- **Natural Conversation**: Agent now asks only ONE clarifying question at a time
- **Better Flow**: Wait for your response before asking the next question
- **Less Overwhelming**: Makes conversations feel more natural and manageable

**Implementation:**
- Updated system prompts to enforce single-question rule
- Tool descriptions emphasize waiting for responses
- Creates a more human-like interaction

#### 3. JavaScript-Rendered Webpage Support
- **Dynamic Pages**: Now works with JavaScript-rendered job postings (Apple, LinkedIn, etc.)
- **JSON-LD Extraction**: Automatically extracts structured data from job pages
- **Playwright Integration**: Optional browser automation for complex pages
- **Smart Fallback**: Tries fast HTTP request first, uses browser if needed

**Supported Sites:**
- Apple Jobs (https://jobs.apple.com/...)
- LinkedIn Jobs
- Sites with JSON-LD structured data
- Any standard HTML job posting

**Installation for JS support:**
```bash
uv pip install playwright
playwright install chromium
```

### Improvements

#### Bug Fixes
- Fixed `save_modified_resume` validation error by adding `get_full_resume_content` tool
- Agent now has access to complete resume content for modifications
- Better error messages when job pages fail to load

#### Enhanced Prompts
- Clearer instructions for tool usage
- Explicit workflow steps in system prompt
- Better guidance for providing full LaTeX content when saving

#### Better Job Fetching
- Tries multiple strategies to extract job information
- Better parsing of company names and job titles
- Improved text extraction from complex pages

### Technical Changes

**New Files:**
- `src/utils/user_profiles.py` - User profile management
- `CHANGELOG.md` - This file

**Modified Files:**
- `src/agent/resume_agent.py` - Added profile management, new tools
- `src/agent/prompts.py` - Updated for new features
- `src/tools/job_fetcher.py` - Complete rewrite with Playwright support
- `pyproject.toml` - Added browser automation as optional dependency
- `.gitignore` - Exclude user profiles directory
- `README.md` - Updated features list

**New Dependencies:**
- `playwright>=1.40.0` (optional, for JS-rendered pages)

### Usage Examples

#### Using User Memory
The agent automatically:
- Saves information you share during conversations
- Loads your profile on next use
- References past conversations

No special commands needed - just use the agent naturally!

#### Working with JavaScript Pages
For Apple Jobs and similar:
```bash
# First time setup (one-time)
uv pip install playwright
playwright install chromium

# Then use normally
run.bat run -r resume.tex -j job_url.txt
```

The agent automatically detects when a page needs JavaScript rendering.

#### One Question at a Time
The agent now naturally asks questions sequentially:
```
Agent: Do you have experience with Docker?
You: Yes, 2 years
Agent: [processes answer]
Agent: What projects did you use Docker in?
You: [answer]
```

### Migration Notes

**Upgrading from v0.1.0:**
1. Pull latest changes
2. No database migration needed - profiles auto-created
3. Optionally install Playwright for JS page support
4. Existing resumes will create new profiles on first use

**Profile Storage:**
- Location: `./.user_profiles/`
- Format: JSON files named after resume
- Not committed to git (privacy)
- Safe to delete anytime (will recreate on next use)

### Known Limitations

- JavaScript page fetching requires Playwright installation
- Profile matching based on resume file path (renaming resume creates new profile)
- Memory persists locally only (not synced across machines)

### Coming Soon

- Profile merging and management CLI commands
- Export/import profiles
- Profile analytics (skills over time, common questions, etc.)
- Web interface for profile management
