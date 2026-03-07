"""Agent 3: LLM-as-Judge that evaluates the tailored resume using Haiku."""

import os
from typing import Optional, Dict, Any
from pathlib import Path

from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, Field


class JudgeVerdict(BaseModel):
    """Structured output from the judge."""
    employability_score: int = Field(description="Score from 1-10")
    score_reasoning: str = Field(description="Why this score was given")
    weaknesses: list[str] = Field(description="Gaps between candidate and job requirements")
    interview_questions: list[str] = Field(description="3-5 interview questions the candidate should prepare for")


JUDGE_PROMPT = """\
You are a hiring manager evaluating a candidate's resume against a job description.

JOB DESCRIPTION:
{job_description}

TAILORED RESUME (plain text extracted from LaTeX):
{resume_text}

KNOWN GAPS (identified during analysis):
{gaps}

Evaluate this candidate and respond with EXACTLY the following JSON structure:

{{
  "employability_score": <1-10 integer>,
  "score_reasoning": "<2-3 sentences explaining the score>",
  "weaknesses": ["<weakness 1>", "<weakness 2>", ...],
  "interview_questions": ["<question 1>", "<question 2>", "<question 3>", ...]
}}

SCORING GUIDE:
- 9-10: Exceptional match, exceeds most requirements
- 7-8: Strong match, meets most must-have requirements
- 5-6: Moderate match, has relevant transferable skills but notable gaps
- 3-4: Weak match, significant gaps in core requirements
- 1-2: Poor match, fundamentally different background

INTERVIEW QUESTIONS should:
- Target the gaps between the candidate's experience and the job requirements
- Test depth of knowledge in areas where the resume is strong but could be surface-level
- Include at least one behavioral question relevant to the role
- Be specific to this candidate and job (not generic)

Provide 3-5 interview questions.
"""


class JudgeAgent:
    """Evaluates the tailored resume against the job description using Haiku."""

    def __init__(
        self,
        model_name: str = "claude-haiku-4-5-20251001",
        api_key: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be set")

        self.llm = ChatAnthropic(
            model=model_name,
            temperature=0.1,
            anthropic_api_key=self.api_key,
        )

    def run(
        self,
        tailored_resume_path: str,
        job_description: str,
        gaps: list[str],
    ) -> JudgeVerdict:
        """
        Evaluate the tailored resume.

        Args:
            tailored_resume_path: Path to the tailored .tex file
            job_description: Raw job description text
            gaps: Known candidate gaps from the conversational agent

        Returns:
            JudgeVerdict with score, weaknesses, and interview questions.
        """
        from ..tools.latex_parser import read_latex_resume, extract_text_content

        resume = read_latex_resume(tailored_resume_path)
        resume_text = extract_text_content(resume.raw_content)

        gaps_text = "\n".join(f"- {g}" for g in gaps) if gaps else "None identified."

        prompt = JUDGE_PROMPT.format(
            job_description=job_description[:4000],
            resume_text=resume_text[:4000],
            gaps=gaps_text,
        )

        structured_llm = self.llm.with_structured_output(JudgeVerdict)
        verdict = structured_llm.invoke(prompt)

        return verdict
