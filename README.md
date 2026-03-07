# AutoResume

Multi-agent resume tailoring system powered by LangChain and Claude.

```
  resume.tex + url.txt
         |
         v
  +----- CONVERSATIONAL (Sonnet) -----+
  |  Fetches job, reads resume,       |
  |  asks 0-2 clarifying questions,   |
  |  loads/saves user notes           |
  +----------------+------------------+
                   |  handoff
                   v
  +----- TAILORING (Sonnet) ----------+
  |  Modifies .tex: reorders bullets, |
  |  rewrites for relevance,          |
  |  mirrors job keywords             |
  +----------------+------------------+
                   |
                   v
  +----- JUDGE (Haiku) ---------------+
  |  Scores employability (1-10),     |
  |  identifies weaknesses,           |
  |  suggests 3-5 interview Qs        |
  +----------------+------------------+
                   |
                   v
  <company>_<title>/
    resume_tailored.tex
    judge_feedback.txt
```

## Setup

```bash
git clone <repo-url>
cd AutoResume
uv sync
echo "ANTHROPIC_API_KEY=your_key_here" > .env
```

For JavaScript-rendered job pages (Apple, LinkedIn, etc.):
```bash
uv sync --all-extras && uv run playwright install chromium
```

## Usage

```bash
uv run autoresume run -r path/to/resume.tex -j path/to/url.txt
```

The URL file is a plain text file with one line: the job posting URL.

**Options:**
- `-r, --resume` -- path to your baseline `.tex` resume (required)
- `-j, --job-url` -- path to `.txt` file containing the job URL (required)
- `-o, --output-dir` -- override output directory
- `-m, --model` -- model for agents 1 & 2 (default: `claude-sonnet-4-5-20250929`)
- `--judge-model` -- model for agent 3 (default: `claude-haiku-4-5-20251001`)
- `-v, --verbose` -- show agent thinking
- `-y, --yes` -- skip confirmation prompt

**Example:**
```bash
uv run autoresume run \
  -r real_user/cv_baseline.tex \
  -j real_user/edda_research_scientist/url.txt
```

Output lands in `real_user/edda_research_scientist/edda_technology_ai_research_scientist_--_medical_applications/`.

## Repository Structure

```
AutoResume/
├── autoresume/
│   ├── cli.py                  # CLI entry point
│   ├── orchestrator.py         # Pipeline coordinator
│   ├── agents/
│   │   ├── conversational.py   # Agent 1: analyze, ask, handoff
│   │   ├── tailoring.py        # Agent 2: modify .tex
│   │   └── judge.py            # Agent 3: evaluate
│   ├── memory/
│   │   └── user_profiles.py    # Persistent per-user notes
│   └── tools/
│       ├── job_fetcher.py      # Fetch + parse job descriptions
│       ├── latex_parser.py     # Read, validate, write LaTeX
│       └── file_ops.py         # Save resume helpers
├── real_user/                  # Resume + job URL files
├── pyproject.toml
└── CLAUDE.md
```

## License

MIT
