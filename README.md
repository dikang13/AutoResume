# AutoResume

> Intelligent resume tailoring and cover letter generation using LangChain and Claude

AutoResume is a conversational AI agent that helps you tailor your resume and generate cover letters for specific job applications. It analyzes job descriptions, understands your resume, and makes intelligent modifications while **never fabricating experience or skills**.

## Features

- **Intelligent Job Analysis**: Fetches and analyzes job descriptions from URLs
- **Resume Tailoring**: Modifies your LaTeX resume to emphasize relevant experience
- **Cover Letter Generation**: Creates personalized cover letters based on your resume
- **Conversational Interface**: Asks clarifying questions instead of making assumptions
- **LaTeX Preservation**: Maintains your resume's formatting and structure
- **No Hallucination**: Only works with information explicitly in your resume

## Installation

### Prerequisites

- Python 3.9 or higher
- Anthropic API key ([get one here](https://console.anthropic.com/))

### Setup

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -e .
```

3. Configure your API key:
```bash
python main.py setup
```

Or manually create a `.env` file:
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

## Usage

### Basic Usage

```bash
python main.py run -r path/to/resume.tex -j path/to/job_url.txt
```

Or if installed as a package:
```bash
autoresume run -r resume.tex -j job_url.txt
```

### Command Line Options

- `-r, --resume`: Path to your resume `.tex` file (required)
- `-j, --job-url`: Path to `.txt` file containing the job URL (required)
- `-o, --output-dir`: Output directory for modified files (default: same as resume)
- `-m, --model`: Claude model to use (default: claude-sonnet-4-5-20250929)

### Example Workflow

1. **Prepare your files**:
   - Save your resume as a `.tex` file
   - Create a text file with the job posting URL

2. **Run the agent**:
   ```bash
   python main.py run -r my_resume.tex -j job_url.txt
   ```

3. **Interact with the agent**:
   - The agent will fetch the job description
   - It will analyze your resume
   - **It will ask you questions** if it needs clarification about your experience
   - It will suggest modifications

4. **Review the output**:
   - `resume_modified.tex` - Your tailored resume
   - `cover_letter.tex` - Generated cover letter

## How It Works

### Architecture

AutoResume uses a LangChain agent with specialized tools:

1. **Job Fetcher**: Downloads and parses job descriptions from URLs
2. **LaTeX Parser**: Reads and understands your resume structure
3. **Resume Analyzer**: Compares your resume against job requirements
4. **User Interaction**: Asks clarifying questions when needed
5. **Content Generator**: Modifies resume and generates cover letter

### The Conversational Approach

Unlike traditional resume tools, AutoResume is conversational and asks questions:

```
🤔 Agent question: The job requires experience with Kubernetes.
   Have you worked with container orchestration tools?
Your answer: Yes, I used Docker Compose in my previous role and
             learned Kubernetes basics in a personal project.
```

This ensures that **no false information** is added to your resume.

### Key Principles

1. **Never Fabricate**: Only use information from your actual resume
2. **Ask, Don't Assume**: Clarify uncertainties through conversation
3. **Conservative Changes**: Make targeted modifications, not rewrites
4. **Preserve Structure**: Keep your LaTeX formatting intact
5. **Validate Output**: Ensure the modified resume compiles correctly

## Project Structure

```
AutoResume/
├── main.py                      # CLI entry point
├── src/
│   ├── agent/
│   │   ├── resume_agent.py      # Main agent logic
│   │   └── prompts.py           # System prompts
│   ├── tools/
│   │   ├── job_fetcher.py       # Fetch job descriptions
│   │   └── latex_parser.py      # Parse/modify LaTeX
│   └── utils/
├── examples/
│   ├── sample_resume.tex        # Example resume
│   └── sample_job_url.txt       # Example job URL
├── CLAUDE.md                    # Development guide
└── README.md                    # This file
```

## Examples

See the `examples/` directory for:
- `sample_resume.tex` - A sample LaTeX resume
- `sample_job_url.txt` - Example job URL format

## Configuration

### Environment Variables

Create a `.env` file with:

```env
ANTHROPIC_API_KEY=your_key_here
MODEL_NAME=claude-sonnet-4-5-20250929
```

### Model Selection

- **claude-sonnet-4-5-20250929** (default): Best balance of capability and cost
- **claude-opus-4-6**: Maximum capability for complex resumes
- **claude-haiku-4-5**: Faster and cheaper for simple modifications

## Development

See [CLAUDE.md](CLAUDE.md) for the full development plan and architecture details.

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/ main.py
ruff check src/ main.py
```

## Limitations

- Currently only supports LaTeX (`.tex`) resume files
- Job descriptions must be accessible via public URLs
- Requires an internet connection for API calls
- Does not compile LaTeX (use `pdflatex` or similar to generate PDF)

## Future Enhancements

- [ ] Support for multiple resume formats (Word, PDF, Markdown)
- [ ] ATS (Applicant Tracking System) optimization
- [ ] Resume scoring and feedback
- [ ] Multi-language support
- [ ] Web interface
- [ ] Integration with job boards

## Troubleshooting

### API Key Issues

```
Error: ANTHROPIC_API_KEY not found in environment
```

**Solution**: Run `python main.py setup` or create a `.env` file with your API key

### LaTeX Validation Errors

```
LaTeX validation failed. Issues: Unmatched opening braces
```

**Solution**: Check your original resume file for syntax errors. The agent preserves existing LaTeX structure.

### Job Description Fetch Failures

```
Failed to fetch job description from URL
```

**Solution**: Ensure the URL is accessible and not behind authentication. Some job boards may block automated requests.

## Contributing

Contributions are welcome! Areas for improvement:
- Additional resume format support
- Better LaTeX parsing
- More sophisticated matching algorithms
- Test coverage

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Built with [LangChain](https://www.langchain.com/)
- Powered by [Claude](https://www.anthropic.com/claude) by Anthropic
- CLI built with [Rich](https://rich.readthedocs.io/) and [Click](https://click.palletsprojects.com/)

---

**Note**: This tool is designed to help you present your actual experience effectively. It will not fabricate qualifications or experience. Always review the generated content before submitting applications.
