"""Agent 1: Conversational agent that analyzes the job and resume, asks clarifying questions."""

import os
import sys
from typing import Optional, Callable, Dict, Any, List
from pathlib import Path

from langchain_anthropic import ChatAnthropic
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field

from ..tools.job_fetcher import fetch_job_description, read_job_url_from_file
from ..tools.latex_parser import read_latex_resume, extract_text_content
from ..memory.user_profiles import UserProfileManager, UserProfile


SYSTEM_PROMPT = """\
You are a career consultant preparing to tailor a resume for a specific job application.

Your job is to:
1. Understand the job requirements by analyzing the job description
2. Understand the candidate's background by reading their resume
3. Check the user profile for notes from previous sessions
4. Identify the most critical gap or ambiguity that needs clarification
5. Ask 0-2 focused clarifying questions (only if truly needed)
6. Save any new information the user shares for future sessions
7. Produce a structured handoff summary for the tailoring agent

RULES:
- NEVER fabricate experience, skills, or qualifications
- If the user profile already has relevant notes, do NOT re-ask those questions
- Ask AT MOST 2 questions total. Prefer 0-1 questions.
- Only ask about critical gaps that would significantly change the tailoring strategy
- STRICTLY ONE question per ask_user call. Never combine multiple questions into one call. \
Bad: "Do you have X experience? Also, what about Y?" \
Good: "Do you have X experience?" (then wait for the answer before asking about Y)

CRITICAL: You MUST call the create_handoff tool as your FINAL action. Do NOT end your turn \
with a text response. Your last action must ALWAYS be a create_handoff tool call. The pipeline \
cannot continue without it.
"""


class ConversationalAgent:
    """Analyzes job + resume, asks clarifying questions, produces handoff for tailoring."""

    def __init__(
        self,
        model_name: str = "claude-sonnet-4-5-20250929",
        temperature: float = 0.3,
        api_key: Optional[str] = None,
        user_input_callback: Optional[Callable[[str], str]] = None,
        verbose: bool = False,
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be set")

        self.llm = ChatAnthropic(
            model=model_name,
            temperature=temperature,
            anthropic_api_key=self.api_key,
        )
        self.user_input_callback = user_input_callback
        self.verbose = verbose
        self.profile_manager = UserProfileManager()
        self.current_profile: Optional[UserProfile] = None
        self.conversation_notes: List[str] = []

        # State populated during run
        self._job_data = None
        self._resume_text = None
        self._handoff: Optional[Dict[str, Any]] = None

    def _create_tools(self):
        agent_ref = self

        @tool
        def fetch_job(url: str) -> str:
            """Fetch and parse a job description from a URL.

            Args:
                url: The URL of the job posting
            """
            try:
                job = fetch_job_description(url)
                agent_ref._job_data = {
                    "title": job.title,
                    "company": job.company,
                    "url": job.url,
                    "raw_text": job.raw_text,
                }
                return (
                    f"Job Title: {job.title}\n"
                    f"Company: {job.company}\n\n"
                    f"Description:\n{job.raw_text[:4000]}"
                )
            except Exception as e:
                return f"Error fetching job: {e}"

        @tool
        def read_resume(file_path: str) -> str:
            """Read and summarize a LaTeX resume file.

            Args:
                file_path: Path to the .tex file
            """
            try:
                resume = read_latex_resume(file_path)
                plain = extract_text_content(resume.raw_content)
                agent_ref._resume_text = plain
                sections = ", ".join(resume.sections.keys()) if resume.sections else "none detected"
                return (
                    f"Sections: {sections}\n\n"
                    f"Content:\n{plain[:3000]}"
                )
            except Exception as e:
                return f"Error reading resume: {e}"

        @tool
        def ask_user(question: str) -> str:
            """Ask the user exactly ONE short clarifying question. Do NOT combine multiple questions.

            Args:
                question: A single question (one sentence, no sub-questions)
            """
            # Reject multi-question calls
            q_marks = question.count("?")
            if q_marks > 1:
                return (
                    "ERROR: You asked multiple questions at once. "
                    "Call ask_user separately for EACH question. "
                    "Pick the single most important question and call ask_user again."
                )

            if agent_ref.user_input_callback:
                sys.stdout.flush()
                sys.stderr.flush()
                print(f"\n[?] {question}", flush=True)
                response = agent_ref.user_input_callback("Your answer: ")
                return response
            return "User input not available."

        @tool
        def save_note(note: str) -> str:
            """Save a note about the user for future sessions.

            Args:
                note: Information to remember (e.g., "Has 3 years of AWS experience")
            """
            agent_ref.conversation_notes.append(note)
            return "Note saved."

        @tool
        def create_handoff(
            job_title: str,
            company: str,
            must_have_requirements: Optional[list[str]] = None,
            nice_to_have_requirements: Optional[list[str]] = None,
            relevant_experiences: Optional[list[str]] = None,
            candidate_strengths: Optional[list[str]] = None,
            candidate_gaps: Optional[list[str]] = None,
            clarification_answers: Optional[list[str]] = None,
            emphasis_strategy: Optional[str] = None,
        ) -> str:
            """Create the structured handoff summary for the tailoring agent.
            Call this after you have gathered all needed information.

            Args:
                job_title: The job title being applied for
                company: The company name
                must_have_requirements: List of must-have requirements from the job description
                nice_to_have_requirements: List of nice-to-have requirements
                relevant_experiences: List of the candidate's most relevant experiences with context
                candidate_strengths: Where the candidate strongly matches the job
                candidate_gaps: Where the candidate is weak or lacks experience
                clarification_answers: Key information from clarifying questions
                emphasis_strategy: How the tailoring agent should approach modifications
            """
            agent_ref._handoff = {
                "job_title": job_title,
                "company": company,
                "must_have_requirements": must_have_requirements or [],
                "nice_to_have_requirements": nice_to_have_requirements or [],
                "relevant_experiences": relevant_experiences or [],
                "candidate_strengths": candidate_strengths or [],
                "candidate_gaps": candidate_gaps or [],
                "clarification_answers": clarification_answers or [],
                "emphasis_strategy": emphasis_strategy or "Emphasize the most relevant experiences for this role.",
            }
            return "Handoff created successfully. The tailoring agent will now take over."

        return [fetch_job, read_resume, ask_user, save_note, create_handoff]

    def run(
        self,
        resume_path: str,
        job_url_file: str,
    ) -> Dict[str, Any]:
        """
        Run the conversational agent.

        Returns:
            Handoff dict for the tailoring agent, plus profile metadata.
        """
        tools = self._create_tools()

        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_tool_calling_agent(self.llm, tools, prompt)
        executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=self.verbose,
            max_iterations=25,
            handle_parsing_errors=True,
        )

        # Read job URL
        job_url = read_job_url_from_file(job_url_file)

        # Load or create user profile
        resume_abs = str(Path(resume_path).resolve())
        self.current_profile = self.profile_manager.find_profile_by_resume(resume_abs)

        profile_info = ""
        if self.current_profile:
            profile_info = "\n\nUSER PROFILE (from previous sessions):\n"
            if self.current_profile.name:
                profile_info += f"Name: {self.current_profile.name}\n"
            if self.current_profile.skills:
                profile_info += f"Known Skills: {', '.join(self.current_profile.skills[:15])}\n"
            if self.current_profile.notes:
                profile_info += f"Notes:\n" + "\n".join(f"  - {n}" for n in self.current_profile.notes[-10:]) + "\n"
            profile_info += "\nUse this information directly. Do NOT re-ask questions already answered.\n"
        else:
            user_id = Path(resume_path).stem
            self.current_profile = self.profile_manager.create_profile(
                user_id=user_id, resume_path=resume_abs
            )
            profile_info = "\n\n(First session with this user - no prior notes)\n"

        initial_prompt = f"""\
I need help tailoring my resume for a job application.{profile_info}

Resume file: {resume_path}
Job URL: {job_url}

Please:
1. Fetch the job description using fetch_job and analyze key requirements
2. Read my resume using read_resume to understand my background
3. Identify gaps between my experience and the job requirements
4. Ask me 0-2 clarifying questions if needed (one at a time, using ask_user)
5. Save any new information I share as notes using save_note
6. YOU MUST call create_handoff as your FINAL action with a structured summary

IMPORTANT: Your very last action must be calling create_handoff. Do not end with a text message."""

        result = executor.invoke({"input": initial_prompt})

        # Persist conversation notes
        if self.current_profile and self.conversation_notes:
            self.profile_manager.update_from_conversation(
                user_id=self.current_profile.user_id,
                notes=self.conversation_notes,
            )

        # If the agent didn't call create_handoff, build a fallback from its text output
        if self._handoff is None:
            output = result.get("output", "")
            if isinstance(output, list):
                output = "\n".join(
                    block.get("text", str(block)) if isinstance(block, dict) else str(block)
                    for block in output
                )

            # Build a minimal handoff from whatever data the agent collected
            self._handoff = {
                "job_title": self._job_data.get("title", "Unknown") if self._job_data else "Unknown",
                "company": self._job_data.get("company", "Unknown") if self._job_data else "Unknown",
                "must_have_requirements": [],
                "nice_to_have_requirements": [],
                "relevant_experiences": [],
                "candidate_strengths": [],
                "candidate_gaps": [],
                "clarification_answers": [],
                "emphasis_strategy": output or "Emphasize the most relevant experiences for this role.",
            }

        # Attach extra context the tailoring agent needs
        self._handoff["job_raw_text"] = self._job_data["raw_text"] if self._job_data else ""
        self._handoff["resume_plain_text"] = self._resume_text or ""
        self._handoff["profile_notes"] = (
            self.current_profile.notes if self.current_profile else []
        )

        return self._handoff
