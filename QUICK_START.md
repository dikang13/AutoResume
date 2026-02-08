# Quick Start - Simple Workflow

## TL;DR - Fastest Way to Use AutoResume

### 1. Setup (One Time)
```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS/Linux
# or
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# Clone and setup
git clone <repo>
cd AutoResume
uv sync --all-extras
uv run playwright install chromium
uv run python main.py setup  # Enter your API key
```

### 2. Organize Your Applications
```
your_applications/
├── cv_baseline.tex              # Your master resume
└── apple_clinical_analyst/      # One folder per job
    └── job_url.txt             # Just the URL
```

### 3. Run (One Command!)
```bash
uv run python /path/to/AutoResume/main.py run \
  -r cv_baseline.tex \
  -j apple_clinical_analyst/job_url.txt \
  --yes
```

### 4. Get Your Files
```
apple_clinical_analyst/
├── job_url.txt
├── resume_modified.tex    ← Generated!
└── cover_letter.tex       ← Generated!
```

---

## That's It!

The agent:
- ✅ Fetches the job description (even JavaScript pages!)
- ✅ Analyzes your resume
- ✅ Tailors your resume for the job
- ✅ Generates a personalized cover letter
- ✅ Saves everything in the job directory

---

## Example: Real Usage

```bash
# Your structure
mkdir ~/job_apps
cd ~/job_apps
cp ~/Documents/my_resume.tex cv_baseline.tex

# New application
mkdir apple_job
echo "https://jobs.apple.com/en-us/details/200645576" > apple_job/job_url.txt

# Run it
uv run python ~/AutoResume/main.py run -r cv_baseline.tex -j apple_job/job_url.txt --yes

# Done! Check results:
ls apple_job/
# job_url.txt  resume_modified.tex  cover_letter.tex
```

---

## Tips

- **Multiple applications?** Just create more folders!
  ```bash
  mkdir google_swe meta_ml apple_analyst
  echo "https://..." > google_swe/job_url.txt
  echo "https://..." > meta_ml/job_url.txt
  # etc.
  ```

- **Want to answer questions?** Remove `--yes`:
  ```bash
  uv run python main.py run -r cv_baseline.tex -j company/job_url.txt
  # Agent will ask for clarification if needed
  ```

- **Need different output location?** Use `-o`:
  ```bash
  uv run python main.py run -r cv_baseline.tex -j company/job_url.txt -o ~/Desktop/
  ```

---

## Full Documentation

- 📘 [UV_SETUP.md](UV_SETUP.md) - UV installation and usage
- 📂 [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) - Detailed workflow patterns
- 📖 [README.md](README.md) - Complete documentation
- 🐛 [FIXES.md](FIXES.md) - Bug fixes and improvements

---

**You're ready to apply! 🚀**
