# AutoResume

Multi-agent resume tailoring system powered by LangChain and Claude. Three specialized agents analyze job descriptions, tailor your LaTeX resume, and provide interview prep feedback.

## How It Works

```
                         +---------------------+
                         |      INPUTS         |
                         |  resume.tex         |
                         |  job_url.txt        |
                         +----------+----------+
                                    |
                    ================v=================
                    |  Agent 1: CONVERSATIONAL        |
                    |  (Sonnet)                       |
                    |                                 |
                    |  - Fetches job description      |
                    |  - Reads & analyzes resume      |
                    |  - Asks 0-4 clarifying Qs       |
                    |  - Loads/saves user notes       |
                    |  - Produces structured handoff   |
                    ================+=================
                                    |
                              handoff dict
                    (requirements, strengths, gaps,
                     clarification answers, strategy)
                                    |
                    ================v=================
                    |  Agent 2: TAILORING             |
                    |  (Sonnet)                       |
                    |                                 |
                    |  - Modifies .tex content        |
                    |  - Reorders & rewrites bullets  |
                    |  - Mirrors job keywords         |
                    |  - Generates cover letter        |
                    ================+=================
                                    |
                    ================v=================
                    |  Agent 3: JUDGE                 |
                    |  (Haiku - cheapest model)       |
                    |                                 |
                    |  - Scores employability (1-10)  |
                    |  - Identifies weaknesses        |
                    |  - Suggests 3-5 interview Qs    |
                    ================+=================
                                    |
                         +----------v----------+
                         |      OUTPUTS        |
                         |                     |
                         |  <company>_<title>/  |
                         |    resume_tailored.tex
                         |    cover_letter.tex  |
                         |    judge_feedback.txt|
                         +---------------------+
```

**Key design decisions:**
- Only the conversational agent talks to the user; the other two are non-interactive
- User notes persist across sessions (stored in `.user_profiles/`)
- The judge uses Haiku to minimize cost -- it's a one-shot evaluation
- Output goes into an auto-named subfolder next to your job URL file

## Setup

### Prerequisites

- Python 3.9+
- [uv](https://docs.astral.sh/uv/) package manager
- Anthropic API key ([get one here](https://console.anthropic.com/))

### Installation

```bash
git clone <repo-url>
cd AutoResume

# Install dependencies
uv sync

# (Optional) For JavaScript-rendered job pages (Apple, LinkedIn, etc.)
uv sync --all-extras
uv run playwright install chromium
```

### Configure API Key

Option A -- interactive setup:
```bash
uv run autoresume setup
```

Option B -- manual `.env` file:
```bash
echo "ANTHROPIC_API_KEY=your_key_here" > .env
```

## Usage

### Basic

```bash
uv run autoresume run -r path/to/resume.tex -j path/to/job_url.txt
```

The job URL file is a plain text file containing a single URL:
```
https://jobs.apple.com/en-us/details/200012345/clinical-data-analyst
```

### Options

```
-r, --resume PATH        Path to your baseline .tex resume (required)
-j, --job-url PATH       Path to .txt file containing the job URL (required)
-o, --output-dir PATH    Override output directory (default: auto-generated)
-m, --model TEXT         Model for agents 1 & 2 (default: claude-sonnet-4-5-20250929)
    --judge-model TEXT   Model for agent 3 (default: claude-haiku-4-5-20251001)
-v, --verbose            Show agent thinking / tool calls
-y, --yes                Skip confirmation prompt
```

### Example

```bash
uv run autoresume run \
  -r real_user/cv_baseline.tex \
  -j real_user/apple_clinical_analyst/job_url_20260207.txt
```

The agent will:
1. Fetch the job description and analyze requirements
2. Read your resume and identify alignment/gaps
3. Ask you 0-4 clarifying questions (one at a time)
4. Tailor your resume and generate a cover letter
5. Score your employability and suggest interview prep questions

Output lands in `real_user/apple_clinical_analyst/apple_clinical_data_analyst/`.

## Inputs and Outputs

### Inputs

| File | Format | Description |
|------|--------|-------------|
| `resume.tex` | LaTeX | Your baseline resume. Any `.cls` files in the same directory are auto-copied to the output. |
| `job_url.txt` | Plain text | A single line containing the job posting URL. |

### Outputs

All outputs are saved to `<job_url_dir>/<company>_<title>/`:

| File | Description |
|------|-------------|
| `resume_tailored.tex` | Modified resume with reordered bullets, added keywords, and emphasis changes. |
| `cover_letter.tex` | Personalized cover letter connecting your experience to the job. |
| `judge_feedback.txt` | Employability score (1-10), weaknesses, and 3-5 interview prep questions. |

### Persistent State

| Location | Description |
|----------|-------------|
| `.user_profiles/*.json` | Per-user notes remembered across sessions (skills, preferences, past Q&A). |

## Repository Structure

```
AutoResume/
├── autoresume/
│   ├── cli.py                       # Click CLI entry point
│   ├── orchestrator.py              # Pipeline coordinator (Agent 1 -> 2 -> 3)
│   ├── agents/
│   │   ├── conversational.py        # Agent 1: analyze, ask questions, handoff
│   │   ├── tailoring.py             # Agent 2: modify .tex, save output
│   │   └── judge.py                 # Agent 3: score, weaknesses, interview Qs
│   ├── memory/
│   │   └── user_profiles.py         # Persistent per-user notes (JSON)
│   └── tools/
│       ├── job_fetcher.py           # Fetch + parse job descriptions from URLs
│       ├── latex_parser.py          # Read, validate, and write LaTeX files
│       └── file_ops.py              # Save resume / cover letter helpers
├── real_user/                       # Real resume + job URL files
│   ├── cv_baseline.tex
│   └── apple_clinical_analyst/
│       └── job_url_20260207.txt
├── examples/
│   ├── sample_resume.tex
│   └── sample_job_url.txt
├── pyproject.toml
├── CLAUDE.md                        # Development guide and architecture plan
└── README.md
```

## Troubleshooting

**`ANTHROPIC_API_KEY not found`** -- Run `uv run autoresume setup` or create a `.env` file.

**`Failed to fetch job description`** -- The page may require JavaScript. Install Playwright:
```bash
uv sync --all-extras && uv run playwright install chromium
```

**`LaTeX validation failed`** -- Check your original `.tex` file for unmatched braces or missing `\end{document}`.

## License

MIT
