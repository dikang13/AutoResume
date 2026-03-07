"""Orchestrator that coordinates the 3-agent pipeline."""

import os
import re
from typing import Optional, Callable, Dict, Any
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .agents.conversational import ConversationalAgent
from .agents.tailoring import TailoringAgent
from .agents.judge import JudgeAgent, JudgeVerdict

console = Console()


class PipelineConfig:
    """Configuration for the multi-agent pipeline."""

    def __init__(
        self,
        model_name: str = "claude-sonnet-4-5-20250929",
        judge_model: str = "claude-haiku-4-5-20251001",
        verbose: bool = False,
        api_key: Optional[str] = None,
    ):
        self.model_name = model_name
        self.judge_model = judge_model
        self.verbose = verbose
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")


def _make_output_dir(job_url_file: str, handoff: Dict[str, Any]) -> str:
    """Create an output directory based on company and job title."""
    base = Path(job_url_file).parent

    company = handoff.get("company", "unknown").strip()
    title = handoff.get("job_title", "unknown").strip()

    # Sanitize for filesystem
    def sanitize(s: str) -> str:
        s = re.sub(r'[^\w\s-]', '', s)
        return re.sub(r'[\s]+', '_', s).strip('_').lower()

    dirname = f"{sanitize(company)}_{sanitize(title)}"
    if not dirname:
        dirname = "output"

    output_dir = base / dirname
    output_dir.mkdir(parents=True, exist_ok=True)
    return str(output_dir)


def run_pipeline(
    resume_path: str,
    job_url_file: str,
    output_dir: Optional[str] = None,
    config: Optional[PipelineConfig] = None,
    user_input_callback: Optional[Callable[[str], str]] = None,
) -> Dict[str, Any]:
    """
    Run the full 3-agent pipeline.

    Args:
        resume_path: Path to the baseline .tex resume
        job_url_file: Path to the .txt file containing the job URL
        output_dir: Override output directory (default: auto-generated)
        config: Pipeline configuration
        user_input_callback: Function for getting user input

    Returns:
        Dict with all results from all three agents.
    """
    config = config or PipelineConfig()

    results: Dict[str, Any] = {
        "success": False,
        "handoff": None,
        "tailoring": None,
        "verdict": None,
    }

    # --- Agent 1: Conversational ---
    console.print(Panel(
        "[bold]Stage 1/3: Analyzing job & resume, asking clarifying questions...[/bold]",
        border_style="cyan",
    ))

    try:
        conv_agent = ConversationalAgent(
            model_name=config.model_name,
            api_key=config.api_key,
            user_input_callback=user_input_callback,
            verbose=config.verbose,
        )
        handoff = conv_agent.run(resume_path=resume_path, job_url_file=job_url_file)
        results["handoff"] = handoff
    except Exception as e:
        console.print(f"[bold red]Conversational agent failed:[/bold red] {e}")
        results["error"] = f"Conversational agent: {e}"
        return results

    console.print("[green]Handoff complete.[/green]\n")

    # Determine output directory
    if output_dir is None:
        output_dir = _make_output_dir(job_url_file, handoff)
    else:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    # --- Agent 2: Tailoring ---
    console.print(Panel(
        f"[bold]Stage 2/3: Tailoring resume for {handoff.get('job_title', '?')} at {handoff.get('company', '?')}...[/bold]",
        border_style="yellow",
    ))

    try:
        tailor_agent = TailoringAgent(
            model_name=config.model_name,
            api_key=config.api_key,
            verbose=config.verbose,
        )
        tailor_result = tailor_agent.run(
            resume_path=resume_path,
            output_dir=output_dir,
            handoff=handoff,
        )
        results["tailoring"] = tailor_result
    except Exception as e:
        console.print(f"[bold red]Tailoring agent failed:[/bold red] {e}")
        results["error"] = f"Tailoring agent: {e}"
        return results

    if not tailor_result.get("success"):
        console.print("[bold red]Tailoring agent did not save a resume.[/bold red]")
        results["error"] = "Tailoring agent did not produce output"
        return results

    console.print(f"[green]Resume saved to {tailor_result['resume_path']}[/green]\n")

    # --- Agent 3: Judge ---
    console.print(Panel(
        "[bold]Stage 3/3: Evaluating tailored resume (Haiku judge)...[/bold]",
        border_style="magenta",
    ))

    try:
        judge = JudgeAgent(
            model_name=config.judge_model,
            api_key=config.api_key,
        )
        verdict = judge.run(
            tailored_resume_path=tailor_result["resume_path"],
            job_description=handoff.get("job_raw_text", ""),
            gaps=handoff.get("candidate_gaps", []),
        )
        results["verdict"] = verdict
    except Exception as e:
        console.print(f"[bold red]Judge agent failed:[/bold red] {e}")
        results["error"] = f"Judge agent: {e}"
        # Non-fatal: we still have the tailored resume
        results["success"] = True
        return results

    _display_verdict(verdict)

    # Save verdict to file
    verdict_path = str(Path(output_dir) / "judge_feedback.txt")
    _save_verdict(verdict, verdict_path)
    console.print(f"\n[dim]Feedback saved to {verdict_path}[/dim]")

    results["success"] = True
    results["output_dir"] = output_dir
    return results


def _display_verdict(verdict: JudgeVerdict):
    """Display the judge's verdict with Rich formatting."""
    # Score with color coding
    score = verdict.employability_score
    if score >= 8:
        color = "green"
    elif score >= 5:
        color = "yellow"
    else:
        color = "red"

    console.print(Panel(
        f"[bold {color}]Employability Score: {score}/10[/bold {color}]\n\n"
        f"{verdict.score_reasoning}",
        title="Judge Verdict",
        border_style=color,
    ))

    # Weaknesses
    if verdict.weaknesses:
        console.print("\n[bold]Weaknesses:[/bold]")
        for w in verdict.weaknesses:
            console.print(f"  [red]-[/red] {w}")

    # Interview questions
    if verdict.interview_questions:
        console.print("\n[bold]Suggested Interview Prep Questions:[/bold]")
        for i, q in enumerate(verdict.interview_questions, 1):
            console.print(f"  {i}. {q}")


def _save_verdict(verdict: JudgeVerdict, path: str):
    """Save the verdict to a text file."""
    lines = [
        f"EMPLOYABILITY SCORE: {verdict.employability_score}/10",
        f"\nREASONING:\n{verdict.score_reasoning}",
        "\nWEAKNESSES:",
    ]
    for w in verdict.weaknesses:
        lines.append(f"  - {w}")
    lines.append("\nINTERVIEW PREP QUESTIONS:")
    for i, q in enumerate(verdict.interview_questions, 1):
        lines.append(f"  {i}. {q}")

    with open(path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
