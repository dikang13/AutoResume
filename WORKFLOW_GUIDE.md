# Workflow Guide - Organizing Job Applications

## Recommended Directory Structure

Organize your job applications with one directory per application:

```
your_work/
├── cv_baseline.tex                    # Your master resume
│
├── apple_clinical_analyst/            # Application 1
│   ├── job_url_20260207.txt          # Job URL
│   ├── resume_modified.tex           # Generated (output)
│   └── cover_letter.tex              # Generated (output)
│
├── google_swe_ml/                     # Application 2
│   ├── job_url.txt
│   ├── resume_modified.tex
│   └── cover_letter.tex
│
└── meta_research_scientist/           # Application 3
    ├── job_url.txt
    ├── resume_modified.tex
    └── cover_letter.tex
```

---

## Quick Start

### 1. Set Up Your Structure

```bash
# Create your work directory
mkdir ~/job_applications
cd ~/job_applications

# Add your master resume
cp /path/to/your/resume.tex cv_baseline.tex

# Create a directory for each job application
mkdir apple_clinical_analyst
```

### 2. Add Job URL

```bash
# Save the job URL
echo "https://jobs.apple.com/en-us/details/200645576" > apple_clinical_analyst/job_url.txt
```

### 3. Run the Agent

**Simple command - outputs go to the job directory automatically:**

```bash
uv run python /path/to/AutoResume/main.py run \
  -r cv_baseline.tex \
  -j apple_clinical_analyst/job_url.txt \
  --yes
```

**That's it!** The outputs will be saved in `apple_clinical_analyst/`:
- `resume_modified.tex`
- `cover_letter.tex`

---

## Default Output Behavior

**NEW:** Outputs now default to the **job URL file's directory**, not the resume directory.

### Example:

```bash
# Your files
cv_baseline.tex
apple_clinical_analyst/job_url.txt

# Command
uv run python main.py run -r cv_baseline.tex -j apple_clinical_analyst/job_url.txt

# Outputs go to: apple_clinical_analyst/
# NOT to: ./ (where cv_baseline.tex is)
```

This makes it natural to organize by application!

---

## Real-World Example

### Scenario: Applying to 3 Jobs

```bash
cd ~/job_applications

# Set up
mkdir apple_clinical_analyst google_swe meta_researcher

echo "https://jobs.apple.com/..." > apple_clinical_analyst/job_url.txt
echo "https://careers.google.com/..." > google_swe/job_url.txt
echo "https://www.metacareers.com/..." > meta_researcher/job_url.txt

# Run for each (can run in parallel!)
uv run python ~/AutoResume/main.py run -r cv_baseline.tex -j apple_clinical_analyst/job_url.txt --yes &
uv run python ~/AutoResume/main.py run -r cv_baseline.tex -j google_swe/job_url.txt --yes &
uv run python ~/AutoResume/main.py run -r cv_baseline.tex -j meta_researcher/job_url.txt --yes &

wait

# Check results
ls apple_clinical_analyst/
# job_url.txt  resume_modified.tex  cover_letter.tex

ls google_swe/
# job_url.txt  resume_modified.tex  cover_letter.tex

ls meta_researcher/
# job_url.txt  resume_modified.tex  cover_letter.tex
```

---

## Advanced Workflows

### 1. Script to Create New Application

**`new_application.sh`:**
```bash
#!/bin/bash
# Usage: ./new_application.sh "company_position" "job_url"

COMPANY_POSITION=$1
JOB_URL=$2

# Create directory
mkdir -p "$COMPANY_POSITION"

# Save job URL
echo "$JOB_URL" > "$COMPANY_POSITION/job_url.txt"

echo "Created application directory: $COMPANY_POSITION"
echo "Job URL saved: $COMPANY_POSITION/job_url.txt"
echo ""
echo "Run: uv run python main.py run -r cv_baseline.tex -j $COMPANY_POSITION/job_url.txt --yes"
```

**Usage:**
```bash
./new_application.sh "apple_clinical_analyst" "https://jobs.apple.com/..."
```

---

### 2. Batch Processing Script

**`apply_all.sh`:**
```bash
#!/bin/bash
# Process all applications in current directory

for dir in */; do
    if [ -f "$dir/job_url.txt" ]; then
        echo "Processing: $dir"
        uv run python ~/AutoResume/main.py run \
          -r cv_baseline.tex \
          -j "$dir/job_url.txt" \
          --yes
        echo "---"
    fi
done
```

**Usage:**
```bash
cd ~/job_applications
./apply_all.sh
```

---

### 3. Add Metadata

Keep notes in each application directory:

```
apple_clinical_analyst/
├── job_url.txt
├── notes.md                # Your notes about the role
├── resume_modified.tex
├── cover_letter.tex
└── status.txt              # Track application status
```

**`notes.md` example:**
```markdown
# Apple - Clinical Analyst

## Key Points
- Focus on EHR experience from Boehringer Ingelheim
- Emphasize medical coding standards (ICD-10, LOINC)
- Mention Python & SQL skills

## Questions Asked in Interview
- (to be filled after interview)

## Timeline
- Applied: 2026-02-08
- Response: pending
```

---

### 4. Override Output Directory (if needed)

If you want to save outputs elsewhere:

```bash
uv run python main.py run \
  -r cv_baseline.tex \
  -j apple_clinical_analyst/job_url.txt \
  -o ~/Desktop/for_printing/
```

---

## Tips

### 1. Naming Convention

Use clear, consistent names:
```
company_position/           # Good
company_position_date/      # Also good
random_name/                # Avoid
```

Examples:
- `apple_clinical_analyst/`
- `google_ml_engineer/`
- `meta_research_scientist_llm/`
- `openai_research_engineer_2026_02_08/`

### 2. Version Control

Consider git for your applications folder:

```bash
cd ~/job_applications
git init
git add cv_baseline.tex
git add apple_clinical_analyst/
git commit -m "Add Apple clinical analyst application"
```

This helps you:
- Track changes to your resume over time
- See what worked for different companies
- Revert if needed

### 3. Backup Your Master Resume

```bash
# Before each application
cp cv_baseline.tex cv_baseline_backup_$(date +%Y%m%d).tex
```

### 4. Compile PDFs

After generating:

```bash
cd apple_clinical_analyst/
pdflatex resume_modified.tex
pdflatex cover_letter.tex

# Clean up aux files
rm *.aux *.log *.out
```

---

## Quick Reference

### Minimal Command (outputs to job directory)
```bash
uv run python main.py run -r cv_baseline.tex -j company/job_url.txt --yes
```

### With Custom Output Directory
```bash
uv run python main.py run -r cv_baseline.tex -j company/job_url.txt -o output/ --yes
```

### With Different Model
```bash
uv run python main.py run -r cv_baseline.tex -j company/job_url.txt -m claude-opus-4-6 --yes
```

### Interactive Mode (for questions)
```bash
uv run python main.py run -r cv_baseline.tex -j company/job_url.txt
# Omit --yes to be prompted for confirmation and answer agent questions
```

---

## Example: Real User Setup

Your actual structure:
```
real_user/
├── cv_baseline.tex                    # Master resume
└── apple_clinical_analyst/
    ├── job_url_20260207.txt          # Job URL
    ├── resume_modified.tex           # Output (generated)
    └── cover_letter.tex              # Output (generated)
```

Your actual command:
```bash
cd real_user/
uv run python ../main.py run \
  -r cv_baseline.tex \
  -j apple_clinical_analyst/job_url_20260207.txt \
  --yes
```

Outputs automatically saved to `apple_clinical_analyst/` directory! 🎉

---

## Summary

✅ **One directory per application**
✅ **Job URL in the application directory**
✅ **Outputs automatically saved to the same directory**
✅ **Master resume stays clean at the top level**
✅ **Easy to organize and track**

This pattern makes managing multiple applications clean and effortless!
