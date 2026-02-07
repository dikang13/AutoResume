# Getting Started with AutoResume

## Installation Complete!

All dependencies are installed and working. Here's how to use AutoResume:

## Quick Start

### 1. Set up your API key

Run the setup command:
```bash
run.bat setup
```

Or manually create a `.env` file:
```
ANTHROPIC_API_KEY=your_api_key_here
```

### 2. Prepare your files

You need two files:
- **resume.tex** - Your LaTeX resume (can use custom .cls files!)
- **job_url.txt** - A text file with the job URL

Example `job_url.txt`:
```
https://careers.company.com/jobs/senior-engineer
```

### 3. Run the agent

```bash
run.bat run -r resume.tex -j job_url.txt
```

Or with full Python path:
```bash
.venv\Scripts\python.exe main.py run -r resume.tex -j job_url.txt
```

### 4. Interact with the agent

The agent will:
- Fetch and analyze the job description
- Read your resume
- **Ask you questions** when it needs clarification
- Generate modified resume and cover letter

Example interaction:
```
[?] Agent question: The job requires experience with Docker.
    Have you used Docker in your previous roles?
Your answer: Yes, I used Docker for containerizing microservices at my last job
```

### 5. Review the output

The agent creates:
- `resume_modified.tex` - Your tailored resume
- `cover_letter.tex` - Generated cover letter

Compile the PDF:
```bash
pdflatex resume_modified.tex
```

## Commands

### Run the agent
```bash
run.bat run -r <resume.tex> -j <job_url.txt>
```

Options:
- `-o <dir>` - Output directory (default: same as resume)
- `-m <model>` - Model to use (default: claude-sonnet-4-5-20250929)

### Setup
```bash
run.bat setup
```

### Version
```bash
run.bat version
```

## Tips

✓ **Keep your .cls file** in the same directory as your resume
✓ **Be specific** when answering agent questions
✓ **Review the output** before submitting
✓ The agent **never fabricates** experience - it only works with what's in your resume
✓ If validation warnings appear, they're usually safe to ignore (compile will work)

## Troubleshooting

### "ANTHROPIC_API_KEY not found"
Create a `.env` file with your API key or run `run.bat setup`

### "Failed to fetch job description"
- Check the URL is accessible
- Some job boards block automated requests
- Try copying the job description to a local file instead

### LaTeX won't compile
- Ensure your `.cls` file is in the same directory
- Check the original resume compiles first
- Look at the `.log` file for specific errors

## Examples

See the `examples/` folder for:
- `sample_resume.tex` - Example resume structure
- `sample_job_url.txt` - Example URL format

## Full Documentation

- **README.md** - Complete user guide
- **QUICKSTART.md** - 5-minute guide
- **CLAUDE.md** - Architecture and development details

---

**Ready to use!** Run `run.bat setup` to configure your API key and get started.
