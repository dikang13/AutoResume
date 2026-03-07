"""Agent 2: Tailoring agent that modifies the LaTeX resume based on the handoff."""

import os
from typing import Optional, Dict, Any
from pathlib import Path

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from ..tools.latex_parser import read_latex_resume
from ..tools.file_ops import save_modified_resume


TAILORING_PROMPT = """\
You are an expert resume tailoring specialist. You will be given:
1. The full LaTeX content of a resume
2. A structured analysis of the job and candidate

Your task: return the COMPLETE modified LaTeX document. Output ONLY the LaTeX — no \
commentary, no markdown fences, no explanation. Just the raw LaTeX from \\documentclass \
to \\end{{document}}.

RULES:
- NEVER fabricate experience, skills, or qualifications not in the original resume \
or confirmed in the clarification answers
- Preserve the LaTeX structure and formatting — only modify content
- Be conservative: quality over quantity
- Use action verbs and quantifiable results where possible
- Mirror the job description's language and keywords naturally
- Reorder bullet points to prioritize the most relevant experience first
- You may add keywords to the Skills section if the candidate demonstrably has the skill

===== ANALYSIS =====
{handoff_text}

===== ORIGINAL RESUME LATEX =====
{latex_content}

===== YOUR OUTPUT =====
Return the COMPLETE modified LaTeX document below. Nothing else.
"""


class TailoringAgent:
    """Modifies the LaTeX resume based on the conversational agent's handoff.

    Uses a simple chain (not an agent with tools) to avoid tool-call parameter issues
    with large LaTeX content.
    """

    def __init__(
        self,
        model_name: str = "claude-sonnet-4-5-20250929",
        temperature: float = 0.2,
        api_key: Optional[str] = None,
        verbose: bool = False,
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be set")

        self.llm = ChatAnthropic(
            model=model_name,
            temperature=temperature,
            anthropic_api_key=self.api_key,
            max_tokens=8192,
        )
        self.verbose = verbose

    def run(
        self,
        resume_path: str,
        output_dir: str,
        handoff: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Run the tailoring agent.

        Returns:
            Dict with paths to saved files.
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Read the original resume
        resume = read_latex_resume(resume_path)
        latex_content = resume.raw_content

        # Format the handoff analysis
        handoff_text = self._format_handoff(handoff)

        # --- Step 1: Tailor the resume via a single LLM call ---
        prompt = ChatPromptTemplate.from_template(TAILORING_PROMPT)
        chain = prompt | self.llm | StrOutputParser()

        if self.verbose:
            print("[Tailoring] Generating modified resume...")

        raw_output = chain.invoke({
            "handoff_text": handoff_text,
            "latex_content": latex_content,
        })

        # Strip any markdown fences the model might add
        modified_latex = self._clean_latex_output(raw_output)

        # Save the tailored resume
        resume_out = str(Path(output_dir) / "resume_tailored.tex")
        save_result = save_modified_resume(
            content=modified_latex,
            output_path=resume_out,
            source_resume_path=resume_path,
        )
        resume_saved = not save_result.startswith("ERROR")

        if self.verbose:
            print(f"[Tailoring] {save_result}")

        return {
            "success": resume_saved,
            "output": save_result,
            "resume_path": resume_out if resume_saved else None,
        }

    @staticmethod
    def _clean_latex_output(text: str) -> str:
        """Remove markdown code fences if the model wrapped the LaTeX."""
        text = text.strip()
        if text.startswith("```"):
            # Remove opening fence (```latex or ```)
            first_newline = text.index("\n")
            text = text[first_newline + 1:]
        if text.endswith("```"):
            text = text[:-3].rstrip()
        return text

    @staticmethod
    def _format_handoff(handoff: Dict[str, Any]) -> str:
        lines = []
        lines.append(f"TARGET POSITION: {handoff.get('job_title', 'N/A')} at {handoff.get('company', 'N/A')}")
        lines.append("")

        lines.append("MUST-HAVE REQUIREMENTS:")
        for r in handoff.get("must_have_requirements", []):
            lines.append(f"  - {r}")

        lines.append("\nNICE-TO-HAVE REQUIREMENTS:")
        for r in handoff.get("nice_to_have_requirements", []):
            lines.append(f"  - {r}")

        lines.append("\nCANDIDATE'S RELEVANT EXPERIENCES:")
        for e in handoff.get("relevant_experiences", []):
            lines.append(f"  - {e}")

        lines.append("\nSTRENGTHS (strong match):")
        for s in handoff.get("candidate_strengths", []):
            lines.append(f"  - {s}")

        lines.append("\nGAPS (weak or missing):")
        for g in handoff.get("candidate_gaps", []):
            lines.append(f"  - {g}")

        if handoff.get("clarification_answers"):
            lines.append("\nCLARIFICATION ANSWERS FROM CANDIDATE:")
            for a in handoff["clarification_answers"]:
                lines.append(f"  - {a}")

        if handoff.get("profile_notes"):
            lines.append("\nPROFILE NOTES (from past sessions):")
            for n in handoff["profile_notes"]:
                lines.append(f"  - {n}")

        lines.append(f"\nEMPHASIS STRATEGY:\n{handoff.get('emphasis_strategy', 'N/A')}")

        if handoff.get("job_raw_text"):
            lines.append(f"\nFULL JOB DESCRIPTION (for keyword reference):\n{handoff['job_raw_text'][:3000]}")

        return "\n".join(lines)
