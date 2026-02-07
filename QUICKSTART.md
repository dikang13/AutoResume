# Quick Start Guide

Get started with AutoResume in 5 minutes.

## 1. Install Dependencies

```bash
pip install -e .
```

## 2. Set Up API Key

```bash
python main.py setup
```

Or create `.env` manually:
```bash
echo "ANTHROPIC_API_KEY=your_key_here" > .env
```

## 3. Prepare Your Files

Create two files:

**your_resume.tex** - Your LaTeX resume

**job_url.txt** - Job URL:
```
https://example.com/jobs/software-engineer
```

## 4. Run the Agent

```bash
python main.py run -r your_resume.tex -j job_url.txt
```

## 5. Interact

The agent will:
1. Fetch the job description
2. Analyze your resume
3. **Ask you questions** about your experience
4. Generate tailored resume + cover letter

## Output Files

- `resume_modified.tex` - Tailored resume
- `cover_letter.tex` - Generated cover letter

Compile with:
```bash
pdflatex resume_modified.tex
```

## Example Session

```
$ python main.py run -r resume.tex -j job_url.txt

AutoResume
Intelligent resume tailoring agent

Configuration:
  Resume: resume.tex
  Job URL file: job_url.txt
  Model: claude-sonnet-4-5-20250929

Start the agent? [Y/n]: y

Starting agent...

🤔 Agent question: The job requires experience with GraphQL APIs.
   Have you worked with GraphQL before?
Your answer: Yes, I built a GraphQL API in my e-commerce project

[Agent continues working...]

✓ Success!

Modified resume: resume_modified.tex
Cover letter: cover_letter.tex
```

## Tips

- Be specific when answering agent questions
- Review the output before using it
- The agent preserves your LaTeX formatting
- It won't fabricate experience - that's why it asks questions!

## Need Help?

- Full documentation: [README.md](README.md)
- Development guide: [CLAUDE.md](CLAUDE.md)
- Report issues: [GitHub Issues](https://github.com/anthropics/claude-code/issues)
