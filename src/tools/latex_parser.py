"""Tool for parsing and modifying LaTeX resume files."""

import re
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ResumeContent(BaseModel):
    """Structured resume content."""

    raw_content: str = Field(description="Full LaTeX content")
    sections: Dict[str, str] = Field(default_factory=dict, description="Extracted sections")
    preamble: str = Field(default="", description="LaTeX preamble")


def read_latex_resume(file_path: str) -> ResumeContent:
    """
    Read and parse a LaTeX resume file.

    Args:
        file_path: Path to the .tex file

    Returns:
        ResumeContent object with parsed structure
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split preamble (before \begin{document}) and body
    doc_start = content.find(r'\begin{document}')
    if doc_start == -1:
        preamble = ""
        body = content
    else:
        preamble = content[:doc_start]
        body = content[doc_start:]

    # Extract sections (simple heuristic - look for \section commands)
    sections = {}
    section_pattern = r'\\section\*?\{([^}]+)\}(.*?)(?=\\section|\Z)'
    matches = re.finditer(section_pattern, body, re.DOTALL)

    for match in matches:
        section_name = match.group(1)
        section_content = match.group(2).strip()
        sections[section_name] = section_content

    return ResumeContent(
        raw_content=content,
        sections=sections,
        preamble=preamble
    )


def write_latex_resume(file_path: str, content: str) -> None:
    """
    Write LaTeX content to a file.

    Args:
        file_path: Path to the output .tex file
        content: LaTeX content to write
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def validate_latex_syntax(content: str) -> tuple[bool, List[str]]:
    """
    Basic validation of LaTeX syntax.

    Args:
        content: LaTeX content to validate

    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []

    # Check for balanced braces
    brace_depth = 0
    for i, char in enumerate(content):
        if char == '{':
            brace_depth += 1
        elif char == '}':
            brace_depth -= 1
        if brace_depth < 0:
            issues.append(f"Unmatched closing brace at position {i}")
            break

    if brace_depth > 0:
        issues.append(f"Unmatched opening braces (depth: {brace_depth})")

    # Check for document environment
    if r'\begin{document}' in content and r'\end{document}' not in content:
        issues.append("Missing \\end{document}")
    elif r'\end{document}' in content and r'\begin{document}' not in content:
        issues.append("Missing \\begin{document}")

    # Check for common LaTeX errors
    if r'\documentclass' not in content:
        issues.append("Missing \\documentclass (might be okay for snippets)")

    return len(issues) == 0, issues


def extract_text_content(latex_content: str) -> str:
    """
    Extract plain text from LaTeX, removing commands and markup.

    Args:
        latex_content: LaTeX content

    Returns:
        Plain text content
    """
    # Remove comments
    text = re.sub(r'%.*$', '', latex_content, flags=re.MULTILINE)

    # Remove common LaTeX commands but keep their content
    text = re.sub(r'\\textbf\{([^}]+)\}', r'\1', text)
    text = re.sub(r'\\textit\{([^}]+)\}', r'\1', text)
    text = re.sub(r'\\emph\{([^}]+)\}', r'\1', text)
    text = re.sub(r'\\href\{[^}]+\}\{([^}]+)\}', r'\1', text)

    # Remove other commands
    text = re.sub(r'\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^}]*\})*', '', text)

    # Clean up whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = text.strip()

    return text
