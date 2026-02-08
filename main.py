"""CLI for AutoResume - Interactive resume tailoring agent."""

import os
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm
from dotenv import load_dotenv

from src.agent.resume_agent import ResumeAgent, ResumeAgentConfig

console = Console()


def user_input_callback(prompt_text: str) -> str:
    """Callback for getting user input during agent execution."""
    return Prompt.ask(prompt_text, console=console)


@click.group()
def cli():
    """AutoResume - Intelligent resume tailoring and cover letter generation."""
    pass


@cli.command()
@click.option(
    "--resume",
    "-r",
    type=click.Path(exists=True),
    required=True,
    help="Path to your resume .tex file"
)
@click.option(
    "--job-url",
    "-j",
    type=click.Path(exists=True),
    required=True,
    help="Path to .txt file containing job URL"
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default=None,
    help="Output directory for modified files (default: same as resume)"
)
@click.option(
    "--model",
    "-m",
    default="claude-sonnet-4-5-20250929",
    help="Model to use (default: claude-sonnet-4-5-20250929)"
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    default=False,
    help="Skip confirmation prompt"
)
def run(
    resume: str,
    job_url: str,
    output_dir: Optional[str],
    model: str,
    yes: bool
):
    """
    Run the resume agent to tailor your resume and generate a cover letter.

    Example:
        autoresume run -r resume.tex -j job_url.txt
    """
    # Load environment variables
    load_dotenv()

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        console.print(
            "[bold red]Error:[/bold red] ANTHROPIC_API_KEY not found in environment.",
            style="red"
        )
        console.print("Please set it in a .env file or export it in your shell.")
        sys.exit(1)

    # Display welcome message
    console.print(Panel.fit(
        "[bold cyan]AutoResume[/bold cyan]\n"
        "Intelligent resume tailoring agent",
        border_style="cyan"
    ))

    console.print(f"\n[bold]Configuration:[/bold]")
    console.print(f"  Resume: {resume}")
    console.print(f"  Job URL file: {job_url}")
    console.print(f"  Model: {model}")
    console.print()

    # Confirm before proceeding (unless --yes flag is used)
    if not yes and not Confirm.ask("Start the agent?", default=True):
        console.print("Cancelled.")
        return

    console.print("\n[bold green]Starting agent...[/bold green]\n")

    try:
        # Create agent
        config = ResumeAgentConfig(model_name=model)
        agent = ResumeAgent(
            config=config,
            user_input_callback=user_input_callback
        )

        # Run the agent
        result = agent.run(
            resume_path=resume,
            job_url_file=job_url,
            output_dir=output_dir
        )

        # Display results
        console.print("\n" + "=" * 80 + "\n")

        if result.get("success"):
            console.print(Panel.fit(
                "[bold green][SUCCESS][/bold green]\n\n"
                f"Modified resume: {result['resume_path']}\n"
                f"Cover letter: {result['cover_letter_path']}",
                border_style="green"
            ))

            console.print("\n[bold]Agent Output:[/bold]")
            console.print(Panel(result["output"], border_style="blue"))

        else:
            console.print(Panel.fit(
                f"[bold red][ERROR][/bold red]\n\n{result.get('error', 'Unknown error')}",
                border_style="red"
            ))

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Agent interrupted by user.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}", style="red")
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
def setup():
    """
    Interactive setup to configure AutoResume.
    """
    console.print(Panel.fit(
        "[bold cyan]AutoResume Setup[/bold cyan]",
        border_style="cyan"
    ))

    console.print("\n[bold]Step 1:[/bold] API Key")
    console.print("You need an Anthropic API key to use Claude.")
    console.print("Get one at: https://console.anthropic.com/\n")

    api_key = Prompt.ask("Enter your Anthropic API key (or press Enter to skip)")

    if api_key:
        # Create or update .env file
        env_path = Path(".env")
        env_content = ""

        if env_path.exists():
            env_content = env_path.read_text()

        # Update or add API key
        if "ANTHROPIC_API_KEY" in env_content:
            # Replace existing
            lines = env_content.split("\n")
            lines = [
                f"ANTHROPIC_API_KEY={api_key}" if line.startswith("ANTHROPIC_API_KEY")
                else line
                for line in lines
            ]
            env_content = "\n".join(lines)
        else:
            # Add new
            env_content += f"\nANTHROPIC_API_KEY={api_key}\n"

        env_path.write_text(env_content)
        console.print("[green][OK] API key saved to .env[/green]")

    console.print("\n[bold]Step 2:[/bold] Model Selection")
    console.print("Default model: claude-sonnet-4-5-20250929 (recommended)")
    console.print("This provides the best balance of capability and cost.\n")

    console.print("[green][OK] Setup complete![/green]")
    console.print("\nTry running:")
    console.print("  autoresume run -r your_resume.tex -j job_url.txt")


@cli.command()
def version():
    """Display version information."""
    console.print("[bold cyan]AutoResume[/bold cyan] v0.1.0")
    console.print("Powered by LangChain and Claude")


if __name__ == "__main__":
    cli()
