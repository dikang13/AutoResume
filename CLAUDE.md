# AutoResume - LangChain Resume & Cover Letter Agent

## Project Overview
This is a LangChain-based agent system that intelligently modifies resumes/CVs and generates cover letters by analyzing job descriptions.

## Core Requirements

### Inputs
1. **Resume Draft**: `.tex` file containing LaTeX-formatted resume
2. **Job Description**: `.txt` file containing a URL to the job posting

### Outputs
1. **Modified Resume**: Tailored `.tex` file optimized for the specific job
2. **Cover Letter**: Generated cover letter (`.tex` or `.txt`)

### Key Capabilities
- **Reliable**: Error handling, validation, and consistent output
- **Expressive**: Natural language understanding of job requirements
- **Intelligent Matching**: Highlight relevant experience, reorder sections, adjust emphasis

## Architecture Plan

### Phase 1: Core Components
1. **Job Description Fetcher**
   - Tool to fetch and parse job description from URL
   - Extract key requirements, skills, qualifications
   - Handle different job board formats (LinkedIn, Indeed, company sites)

2. **LaTeX Parser**
   - Parse `.tex` resume structure
   - Identify sections (experience, education, skills, projects)
   - Extract individual entries for modification

3. **Resume Analyzer**
   - Compare resume content against job requirements
   - Identify gaps and matching experiences
   - Suggest which experiences to emphasize

### Phase 2: LangChain Agent Setup
1. **Tools Definition**
   - `fetch_job_description`: Fetch and parse job URL
   - `parse_resume`: Extract structured data from .tex file
   - `analyze_match`: Compare resume vs job requirements
   - `modify_resume_section`: Edit specific resume sections
   - `generate_cover_letter`: Create tailored cover letter
   - `validate_latex`: Ensure .tex file compiles

2. **Agent Configuration**
   - Use ReAct or OpenAI Functions agent
   - Define clear tool descriptions and schemas
   - Implement structured output for consistency

3. **Prompt Engineering**
   - System prompt defining agent role and constraints
   - Few-shot examples for resume modifications
   - Guidelines for tone and style matching

### Phase 3: Resume Modification Strategy
1. **Analysis Phase**
   - Extract job keywords and required skills
   - Identify must-have vs nice-to-have qualifications
   - Determine industry/role specific terminology

2. **Modification Phase**
   - Reorder bullet points to prioritize relevant experience
   - Add/emphasize keywords naturally
   - Adjust skill section to match requirements
   - Maintain LaTeX formatting and structure

3. **Quality Assurance**
   - Verify LaTeX syntax validity
   - Ensure no information loss
   - Check length constraints (typically 1-2 pages)

### Phase 4: Cover Letter Generation
1. **Structure**
   - Opening: Express interest and how you found the position
   - Body: Connect 2-3 key experiences to job requirements
   - Closing: Call to action and enthusiasm

2. **Personalization**
   - Use company name and specific role details
   - Reference specific job requirements
   - Match tone to company culture (from job posting)

## Technical Stack

### Dependencies
```toml
langchain >= 0.1.0
langchain-anthropic  # For Claude integration
beautifulsoup4  # Web scraping job descriptions
requests  # HTTP requests
pydantic >= 2.0  # Data validation
python-dotenv  # Environment management
```

### Optional
- `langsmith` - For debugging and tracing
- `pypdf` or `pylatex` - LaTeX manipulation
- `chromadb` or `faiss` - If adding semantic search for experience matching

## File Structure
```
AutoResume/
├── main.py                 # CLI entry point
├── src/
│   ├── __init__.py
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── resume_agent.py      # Main agent logic
│   │   └── prompts.py           # System prompts and templates
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── job_fetcher.py       # Fetch job descriptions
│   │   ├── latex_parser.py      # Parse/modify .tex files
│   │   ├── resume_analyzer.py   # Match resume to job
│   │   └── cover_letter.py      # Generate cover letters
│   └── utils/
│       ├── __init__.py
│       └── validators.py        # Input validation
├── tests/
├── examples/
│   ├── sample_resume.tex
│   └── sample_job.txt
├── .env.example
└── pyproject.toml
```

## Usage Pattern
```python
from src.agent import ResumeAgent

agent = ResumeAgent()
result = agent.run(
    resume_path="resume.tex",
    job_url_file="job_url.txt"
)

# Outputs:
# - resume_modified.tex
# - cover_letter.tex
```

## Development Phases

### Phase 1: Foundation (MVP)
- [ ] Set up project structure
- [ ] Implement job description fetcher
- [ ] Create basic LaTeX parser
- [ ] Build simple agent with 2-3 core tools

### Phase 2: Intelligence
- [ ] Add sophisticated matching logic
- [ ] Implement resume modification strategies
- [ ] Add cover letter generation
- [ ] Create comprehensive prompts

### Phase 3: Polish
- [ ] Add error handling and validation
- [ ] Implement logging and debugging
- [ ] Create tests
- [ ] Add CLI interface with rich output

### Phase 4: Enhancement
- [ ] Add support for multiple resume formats
- [ ] Implement feedback loop for iterative improvements
- [ ] Add caching for job descriptions
- [ ] Create web interface (optional)

## Key Design Decisions

1. **Agent vs Chain**: Use Agent for flexibility in tool use order
2. **LaTeX Preservation**: Maintain original formatting and structure
3. **No Hallucination**: Only use information present in original resume
4. **Transparency**: Log all modifications made
5. **Validation**: Always validate LaTeX compiles before saving

## Environment Variables
```
ANTHROPIC_API_KEY=your_key_here
MODEL_NAME=claude-sonnet-4-5-20250929
LANGSMITH_API_KEY=optional_for_debugging
```

## Future Enhancements
- Support for multiple resume versions (different roles)
- A/B testing different modification strategies
- Integration with ATS (Applicant Tracking System) optimization
- Resume scoring/feedback system
- Multi-language support
