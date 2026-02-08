# UV Setup Guide - Reproducible Environment

This project uses [UV](https://docs.astral.sh/uv/) for fast, reproducible Python dependency management.

## Why UV?

- ⚡ **10-100x faster** than pip/pip-tools
- 🔒 **Fully reproducible** with `uv.lock`
- 🎯 **Single tool** for virtual environments, dependencies, and Python versions
- 📦 **Drop-in replacement** for pip, pip-tools, pipx, poetry, and pyenv

---

## Quick Start

### 1. Install UV

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Or with pip:**
```bash
pip install uv
```

### 2. Set Up the Project

```bash
# Clone the repository
git clone <repo-url>
cd AutoResume

# Create virtual environment and install all dependencies
uv sync --all-extras

# This will:
# - Create .venv/ directory
# - Install all dependencies from uv.lock
# - Install dev tools (pytest, black, ruff)
# - Install browser support (playwright)
# - Install the autoresume CLI
```

### 3. Activate the Environment

**Windows:**
```bash
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

Or use `uv run` to run commands without activating:
```bash
uv run python main.py run -r resume.tex -j job.txt
```

---

## Installation Options

### Minimal Installation (No Optional Dependencies)

```bash
uv sync
```

This installs only required dependencies (no dev tools, no browser support).

### With Browser Support (Recommended)

```bash
uv sync --extra browser

# Then install Chromium for Playwright
uv run playwright install chromium
```

### With Dev Tools

```bash
uv sync --group dev
```

### Everything (All Extras + Dev)

```bash
uv sync --all-extras
```

---

## Common Commands

### Running the Application

```bash
# Using uv run (no activation needed)
uv run python main.py run -r resume.tex -j job.txt

# Or activate and run directly
.venv\Scripts\activate  # Windows
python main.py run -r resume.tex -j job.txt
```

### Adding Dependencies

```bash
# Add a new dependency
uv add requests

# Add a dev dependency
uv add --group dev pytest

# Add an optional dependency
uv add --optional browser playwright
```

### Updating Dependencies

```bash
# Update all dependencies
uv lock --upgrade

# Update a specific package
uv lock --upgrade-package langchain

# Sync after updating
uv sync --all-extras
```

### Running Tests

```bash
# Using uv run
uv run pytest

# Or with activated environment
pytest
```

### Code Formatting & Linting

```bash
# Format code
uv run black src/ main.py

# Lint code
uv run ruff check src/ main.py

# Fix linting issues
uv run ruff check --fix src/ main.py
```

---

## Lock File (`uv.lock`)

The `uv.lock` file contains:
- **Exact versions** of all dependencies
- **Checksums** for security
- **Transitive dependencies** fully resolved
- **Cross-platform compatibility** (Windows, macOS, Linux)

### When to Update the Lock File

```bash
# After adding/removing dependencies
uv lock

# After changing version constraints in pyproject.toml
uv lock

# To upgrade dependencies
uv lock --upgrade
```

### Committing the Lock File

✅ **ALWAYS commit `uv.lock` to version control**

This ensures everyone on your team uses the exact same dependency versions.

---

## Project Structure

```
AutoResume/
├── pyproject.toml          # Project metadata and dependencies
├── uv.lock                 # Locked dependency versions (COMMIT THIS!)
├── .venv/                  # Virtual environment (gitignored)
├── .python-version         # Python version (gitignored, local only)
├── src/                    # Source code
│   ├── agent/              # Agent logic
│   ├── tools/              # Tools (job fetcher, LaTeX parser)
│   └── utils/              # Utilities
├── main.py                 # CLI entry point
└── tests/                  # Tests
```

---

## Troubleshooting

### Issue: "uv: command not found"

**Solution:** UV not in PATH. Add to your shell profile:

```bash
# bash/zsh
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Windows: Restart terminal after installation
```

### Issue: "No Python interpreter found"

**Solution:** UV can install Python for you:

```bash
uv python install 3.11
uv python pin 3.11  # Creates .python-version file
```

### Issue: "Playwright browsers not found"

**Solution:** Install Chromium after syncing:

```bash
uv sync --extra browser
uv run playwright install chromium
```

### Issue: Environment out of sync

**Solution:** Remove and recreate:

```bash
rm -rf .venv
uv sync --all-extras
```

---

## Migration from pip/pip-tools

### Old Workflow:
```bash
pip install -r requirements.txt
pip install -e .
```

### New Workflow:
```bash
uv sync
```

That's it! UV handles:
- Virtual environment creation
- Dependency resolution
- Package installation
- Editable installs

---

## Performance Comparison

| Tool | Install Time | Lock Time |
|------|--------------|-----------|
| pip + pip-tools | ~45s | ~30s |
| poetry | ~60s | ~40s |
| **uv** | **~3s** | **~1s** |

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Test
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Run tests
        run: uv run pytest

      - name: Lint
        run: uv run ruff check .
```

---

## Best Practices

1. ✅ **Always commit `uv.lock`** to version control
2. ✅ **Use `uv sync`** after pulling changes
3. ✅ **Use `uv run`** for one-off commands
4. ✅ **Pin Python version** with `.python-version`
5. ✅ **Update regularly** with `uv lock --upgrade`
6. ❌ **Don't edit `uv.lock`** manually
7. ❌ **Don't commit `.venv/`** to version control

---

## Resources

- [UV Documentation](https://docs.astral.sh/uv/)
- [UV GitHub](https://github.com/astral-sh/uv)
- [pyproject.toml Reference](https://packaging.python.org/en/latest/specifications/declaring-project-metadata/)

---

## Summary

```bash
# Setup (once)
uv sync --all-extras
uv run playwright install chromium

# Setup API key
uv run python main.py setup

# Run the agent
uv run python main.py run -r resume.tex -j job.txt --yes

# That's it! 🚀
```

All dependencies are locked in `uv.lock` for complete reproducibility across machines and environments.
