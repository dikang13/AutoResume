"""CLI for AutoResume - Multi-agent resume tailoring system."""

import os
import sys
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from dotenv import load_dotenv

from .orchestrator import run_pipeline, PipelineConfig

console = Console()


def user_input_callback(prompt_text: str) -> str:
    """Callback for getting user input during agent execution.

    Uses raw input() instead of Rich Prompt.ask to avoid console lock
    conflicts with LangChain's AgentExecutor output.
    """
    sys.stdout.flush()
    sys.stderr.flush()
    return input(prompt_text)


@click.group()
def cli():
    """AutoResume - Multi-agent resume tailoring system."""
    pass


@cli.command()
@click.option("--resume", "-r", type=click.Path(exists=True), required=True, help="Path to your resume .tex file")
@click.option("--job-url", "-j", type=click.Path(exists=True), required=True, help="Path to .txt file containing job URL")
@click.option("--output-dir", "-o", type=click.Path(), default=None, help="Output directory (default: auto-generated)")
@click.option("--model", "-m", default="claude-sonnet-4-5-20250929", help="Model for conversational & tailoring agents")
@click.option("--judge-model", default="claude-haiku-4-5-20251001", help="Model for the judge agent")
@click.option("--yes", "-y", is_flag=True, default=False, help="Skip confirmation prompt")
@click.option("--verbose", "-v", is_flag=True, default=False, help="Show agent thinking")
def run(
    resume: str,
    job_url: str,
    output_dir: Optional[str],
    model: str,
    judge_model: str,
    yes: bool,
    verbose: bool,
):
    """Run the 3-agent pipeline to tailor your resume."""
    load_dotenv()

    if not os.getenv("ANTHROPIC_API_KEY"):
        console.print("[bold red]Error:[/bold red] ANTHROPIC_API_KEY not found.", style="red")
        console.print("Set it in a .env file or export it in your shell.")
        sys.exit(1)

    console.print(Panel.fit(
        "[bold cyan]AutoResume[/bold cyan]\n"
        "Multi-agent resume tailoring system\n\n"
        "Pipeline: Conversational -> Tailoring -> Judge",
        border_style="cyan",
    ))

    console.print(f"\n[bold]Configuration:[/bold]")
    console.print(f"  Resume:       {resume}")
    console.print(f"  Job URL file: {job_url}")
    console.print(f"  Model:        {model}")
    console.print(f"  Judge model:  {judge_model}")
    console.print()

    if not yes and not Confirm.ask("Start the pipeline?", default=True):
        console.print("Cancelled.")
        return

    console.print()

    try:
        config = PipelineConfig(
            model_name=model,
            judge_model=judge_model,
            verbose=verbose,
        )

        results = run_pipeline(
            resume_path=resume,
            job_url_file=job_url,
            output_dir=output_dir,
            config=config,
            user_input_callback=user_input_callback,
        )

        console.print("\n" + "=" * 70)

        if results.get("success"):
            tailoring = results.get("tailoring", {})
            console.print(Panel.fit(
                "[bold green]Pipeline Complete[/bold green]\n\n"
                f"Resume:     {tailoring.get('resume_path', 'N/A')}\n"
                f"PDF:        {results.get('pdf_path', 'N/A')}\n"
                f"Output Dir: {results.get('output_dir', 'N/A')}",
                border_style="green",
            ))
        else:
            console.print(Panel.fit(
                f"[bold red]Pipeline Failed[/bold red]\n\n{results.get('error', 'Unknown error')}",
                border_style="red",
            ))

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Interrupted by user.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}", style="red")
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
def setup():
    """Interactive setup to configure AutoResume."""
    console.print(Panel.fit("[bold cyan]AutoResume Setup[/bold cyan]", border_style="cyan"))

    console.print("\n[bold]Step 1:[/bold] API Key")
    console.print("You need an Anthropic API key. Get one at: https://console.anthropic.com/\n")

    api_key = Prompt.ask("Enter your Anthropic API key (or press Enter to skip)")

    if api_key:
        from pathlib import Path
        env_path = Path(".env")
        env_content = env_path.read_text() if env_path.exists() else ""

        if "ANTHROPIC_API_KEY" in env_content:
            lines = env_content.split("\n")
            lines = [
                f"ANTHROPIC_API_KEY={api_key}" if line.startswith("ANTHROPIC_API_KEY") else line
                for line in lines
            ]
            env_content = "\n".join(lines)
        else:
            env_content += f"\nANTHROPIC_API_KEY={api_key}\n"

        env_path.write_text(env_content)
        console.print("[green]API key saved to .env[/green]")

    console.print("\n[green]Setup complete![/green]")
    console.print("Run: autoresume run -r your_resume.tex -j job_url.txt")


@cli.command()
def version():
    """Display version information."""
    console.print("[bold cyan]AutoResume[/bold cyan] v0.3.0")
    console.print("Multi-agent system: Conversational -> Tailoring -> Judge")


if __name__ == "__main__":
    cli()
