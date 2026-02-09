"""Main resume agent implementation."""

import os
from typing import Optional, Dict, Any, Callable
from pathlib import Path

from langchain_anthropic import ChatAnthropic
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field
from typing_extensions import Annotated

from ..tools.job_fetcher import fetch_job_description, read_job_url_from_file
from ..tools.latex_parser import (
    read_latex_resume,
    write_latex_resume,
    validate_latex_syntax,
    extract_text_content
)
from ..utils.user_profiles import UserProfileManager, UserProfile
from .prompts import SYSTEM_PROMPT


class ResumeAgentConfig(BaseModel):
    """Configuration for the resume agent."""

    model_name: str = Field(default="claude-sonnet-4-5-20250929")
    temperature: float = Field(default=0.2)
    max_iterations: int = Field(default=25)
    api_key: Optional[str] = Field(default=None)
    verbose: bool = Field(default=False)


class ResumeAgent:
    """
    LangChain agent for resume modification and cover letter generation.

    This agent can:
    - Fetch and analyze job descriptions
    - Parse and modify LaTeX resumes
    - Generate tailored cover letters
    - Ask clarifying questions to avoid hallucination
    """

    def __init__(
        self,
        config: Optional[ResumeAgentConfig] = None,
        user_input_callback: Optional[Callable[[str], str]] = None
    ):
        """
        Initialize the resume agent.

        Args:
            config: Agent configuration
            user_input_callback: Function to get user input (for CLI interaction)
        """
        self.config = config or ResumeAgentConfig()
        self.user_input_callback = user_input_callback

        # Get API key from config or environment
        api_key = self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY must be set in environment or config"
            )

        # Initialize the LLM
        self.llm = ChatAnthropic(
            model=self.config.model_name,
            temperature=self.config.temperature,
            anthropic_api_key=api_key
        )

        # Storage for agent state
        self.job_description = None
        self.resume_content = None
        self.resume_path = None
        self.user_context = {}
        self.full_content_retrieved = False  # Track if agent has called get_full_resume_content

        # User profile management
        self.profile_manager = UserProfileManager()
        self.current_profile: Optional[UserProfile] = None
        self.conversation_notes = []

        # Create tools
        self.tools = self._create_tools()

        # Create agent
        self.agent = self._create_agent()

    def _create_tools(self):
        """Create the tools for the agent."""

        @tool
        def fetch_job_from_url(url: str) -> str:
            """
            Fetch and parse a job description from a URL.

            Args:
                url: The URL of the job posting

            Returns:
                A formatted string containing the job description
            """
            try:
                job = fetch_job_description(url)
                self.job_description = job

                result = f"Job Title: {job.title}\n"
                result += f"Company: {job.company}\n"
                result += f"URL: {job.url}\n\n"
                result += f"Job Description:\n{job.raw_text[:3000]}"  # Truncate if too long

                return result
            except Exception as e:
                return f"Error fetching job description: {str(e)}"

        @tool
        def read_resume(file_path: str) -> str:
            """
            Read and parse a LaTeX resume file.

            Args:
                file_path: Path to the .tex file

            Returns:
                Summary of the resume structure and content
            """
            try:
                resume = read_latex_resume(file_path)
                self.resume_content = resume
                self.resume_path = file_path

                result = "Resume loaded successfully!\n\n"
                result += f"Sections found: {', '.join(resume.sections.keys())}\n\n"

                # Check for .cls files
                cls_files = list(Path(file_path).parent.glob("*.cls"))
                if cls_files:
                    result += f"Note: Found formatting files {[f.name for f in cls_files]} - these will be automatically copied when you save the modified resume.\n\n"

                # Extract plain text for analysis
                plain_text = extract_text_content(resume.raw_content)
                result += f"Content preview:\n{plain_text[:1500]}"

                return result
            except Exception as e:
                return f"Error reading resume: {str(e)}"

        @tool
        def get_full_resume_content() -> str:
            """
            Get the complete LaTeX content of the resume that was previously loaded.
            Use this when you're ready to modify the resume and need the full content.

            Returns:
                The complete LaTeX content of the resume
            """
            if self.resume_content is None:
                return "Error: No resume has been loaded yet. Use read_resume first."

            # Mark that the agent has retrieved the full content
            self.full_content_retrieved = True

            return f"Full resume content:\n\n{self.resume_content.raw_content}"

        @tool
        def save_modified_resume(
            new_content: Annotated[str, Field(
                description="REQUIRED: The COMPLETE modified LaTeX document from \\documentclass to \\end{document}. Must be 1000+ characters containing the entire file, NOT a summary. You MUST call get_full_resume_content() first to get this content, then modify it, then pass the complete modified version here."
            )] = "",
            output_path: str = None
        ) -> str:
            """
            Save a modified resume after validating LaTeX syntax.

            ⚠️⚠️⚠️ CRITICAL REQUIREMENT ⚠️⚠️⚠️

            The new_content parameter MUST contain the COMPLETE modified LaTeX document.
            This means the ENTIRE file - typically 5000+ characters - from start to finish.

            REQUIRED WORKFLOW:

            Step 1: Get original content
                Call: get_full_resume_content()
                Returns: Full LaTeX document (~5000 chars)

            Step 2: Apply modifications mentally
                Keep the ENTIRE document with your changes in memory

            Step 3: Call save_modified_resume with FULL document
                save_modified_resume(new_content="\\\\documentclass{{...}}...\\\\end{{document}}")

            EXAMPLE OF CORRECT USAGE:
            save_modified_resume(new_content="\\\\documentclass{{moderncv}}{{11pt,a4paper}}\\\\usepackage[utf8]{{inputenc}}\\\\name{{Jane}}{{Smith}}\\\\begin{{document}}\\\\makecvtitle\\\\section{{Experience}}\\\\cventry{{2020--2024}}{{Engineer}}{{Company}}{{}}{{}}{{Built ML systems}}\\\\end{{document}}")

            ❌ WRONG (these FAIL):
            save_modified_resume()  # No parameter!
            save_modified_resume(new_content="")  # Empty!
            save_modified_resume(new_content="Modified skills")  # Description not content!

            Args:
                new_content: COMPLETE modified LaTeX (REQUIRED - 1000+ chars)
                output_path: Save location (OPTIONAL - auto-set)

            Returns:
                Success or error message
            """
            # CRITICAL CHECK: Ensure agent has retrieved the full content first
            if not self.full_content_retrieved:
                return """ERROR: You must call get_full_resume_content() FIRST!

                WORKFLOW VIOLATION: You tried to save_modified_resume without first getting the content.

                YOU MUST FOLLOW THIS EXACT SEQUENCE:
                1. Call: get_full_resume_content()
                   This returns the COMPLETE LaTeX (~5000 chars)

                2. Apply your modifications to that content
                   Keep the ENTIRE document with changes in memory

                3. Call: save_modified_resume(new_content="<COMPLETE MODIFIED LATEX>")
                   Pass the FULL modified document as the parameter

                Do NOT skip step 1! You cannot modify content you haven't retrieved."""

            # Use default output path if not provided
            if output_path is None:
                output_path = self.output_resume_path

            # Validation: Check if new_content is actually provided
            if not new_content:
                return """ERROR: You must provide the new_content parameter!

                You called save_modified_resume without the required new_content.

                Steps to fix:
                1. Get the full resume with: get_full_resume_content()
                2. Make your modifications to create the complete document
                3. Call: save_modified_resume(new_content="<FULL LATEX>")

                The new_content should be the COMPLETE LaTeX file, starting with \\\\documentclass and ending with \\\\end{{document}}."""

            # Check if content seems too short to be a full document
            if len(new_content) < 500:
                return f"""ERROR: new_content is too short ({len(new_content)} chars)!

                The new_content must be the COMPLETE modified LaTeX document.
                A full resume is typically 3000-10000 characters.

                You provided: "{new_content[:200]}..."

                This looks like a description or partial content, NOT the full document.

                CORRECT approach:
                1. Call get_full_resume_content() → Returns ~5000 chars
                2. Apply modifications to the ENTIRE document
                3. Pass the COMPLETE modified document (all 5000+ chars) to save_modified_resume

                The parameter should contain the FULL LaTeX from \\\\documentclass to \\\\end{{document}}."""

            try:
                # Validate LaTeX syntax
                is_valid, issues = validate_latex_syntax(new_content)

                if not is_valid:
                    return f"LaTeX validation failed. Issues: {', '.join(issues)}"

                # Save the file
                write_latex_resume(output_path, new_content)

                # Copy .cls files if they exist alongside the original resume
                if self.resume_path:
                    import shutil
                    import glob
                    resume_dir = Path(self.resume_path).parent
                    output_dir = Path(output_path).parent

                    # Copy all .cls files from source to destination
                    cls_files = list(resume_dir.glob("*.cls"))
                    copied_files = []
                    for cls_file in cls_files:
                        dest_cls = output_dir / cls_file.name
                        shutil.copy(cls_file, dest_cls)
                        copied_files.append(cls_file.name)

                    if copied_files:
                        return f"Resume saved successfully to {output_path}\nCopied formatting files: {', '.join(copied_files)}"

                return f"Resume saved successfully to {output_path}"
            except Exception as e:
                return f"Error saving resume: {str(e)}"

        @tool
        def ask_user_question(question: str) -> str:
            """
            Ask the user a clarifying question to get information not in the resume.
            Use this to avoid making up information.

            IMPORTANT: Ask only ONE question at a time. After calling this tool, wait for
            the response before asking additional questions. This creates a natural conversation flow.

            Args:
                question: A single, specific question to ask the user

            Returns:
                The user's response
            """
            if self.user_input_callback:
                print(f"\n[?] Agent question: {question}")
                response = self.user_input_callback("Your answer: ")
                return response
            else:
                return "User input not available in this context."

        @tool
        def save_cover_letter(content: str, output_path: str = None) -> str:
            """
            Save a generated cover letter.

            Args:
                content: The cover letter content (REQUIRED)
                output_path: Path where to save the cover letter (OPTIONAL - defaults to predetermined location)

            Returns:
                Success or error message
            """
            # Use default output path if not provided
            if output_path is None:
                output_path = self.output_cover_letter_path

            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                return f"Cover letter saved successfully to {output_path}"
            except Exception as e:
                return f"Error saving cover letter: {str(e)}"

        @tool
        def save_user_info(
            experiences: Optional[str] = None,
            skills: Optional[str] = None,
            note: Optional[str] = None
        ) -> str:
            """
            Save information learned about the user for future sessions.
            Use this when the user shares details about their experience, skills, or preferences.

            Args:
                experiences: Description of work experience (e.g., "3 years of Python development at XYZ Corp")
                skills: Skills to remember (e.g., "React, Docker, AWS")
                note: General note to remember (e.g., "Prefers concise bullet points")

            Returns:
                Confirmation message
            """
            if self.current_profile is None:
                return "No user profile active. This shouldn't happen."

            # Parse and add information
            if experiences:
                self.conversation_notes.append(f"Experience: {experiences}")

            if skills:
                skill_list = [s.strip() for s in skills.split(",")]
                self.conversation_notes.append(f"Skills: {', '.join(skill_list)}")

            if note:
                self.conversation_notes.append(note)

            return "Information saved to your profile for future sessions."

        # Accumulator for tailored experiences
        self.tailored_experiences = []
        self.tailored_job_info = {"title": "", "company": ""}

        @tool
        def add_tailored_experience(
            title: str,
            company: str,
            bullets: list[str]
        ) -> str:
            """
            Add ONE tailored experience entry. Call this once for EACH relevant experience.

            Args:
                title: Job title for this experience (e.g. "Data Analyst")
                company: Company name (e.g. "Boehringer Ingelheim")
                bullets: List of 2-5 tailored bullet points for this experience

            Returns:
                Confirmation of the added experience
            """
            entry = {
                "title": title,
                "company": company,
                "bullets": bullets
            }
            self.tailored_experiences.append(entry)
            return f"Added experience #{len(self.tailored_experiences)}: {title} at {company} ({len(bullets)} bullets). Call add_tailored_experience again for the next experience, or call finalize_tailored_experiences when done."

        @tool
        def finalize_tailored_experiences(
            target_job_title: str,
            target_company: str,
            key_skills: list[str]
        ) -> str:
            """
            Finalize and save all tailored experiences to a text file.
            Call this AFTER adding all experiences with add_tailored_experience.

            Args:
                target_job_title: The job you're applying for (e.g. "Clinical Data Analyst")
                target_company: Company you're applying to (e.g. "Apple")
                key_skills: List of key skills highlighted across all experiences

            Returns:
                Success or error message
            """
            if not self.tailored_experiences:
                return "ERROR: No experiences added yet! Call add_tailored_experience first for each relevant experience."

            # Build the output text
            lines = []
            lines.append(f"TAILORED EXPERIENCES FOR: {target_job_title} at {target_company}")
            lines.append("=" * 70)
            lines.append("")

            for i, exp in enumerate(self.tailored_experiences, 1):
                lines.append(f"{i}. {exp['title']} | {exp['company']}")
                for bullet in exp['bullets']:
                    lines.append(f"   • {bullet}")
                lines.append("")

            lines.append("-" * 70)
            lines.append("KEY SKILLS HIGHLIGHTED:")
            for skill in key_skills:
                lines.append(f"   • {skill}")

            content = "\n".join(lines)

            # Save to file
            output_path = str(Path(self.output_resume_path).parent / "tailored_experiences.txt")
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return f"Tailored experiences saved to {output_path} ({len(self.tailored_experiences)} experiences, {len(key_skills)} key skills)"
            except Exception as e:
                return f"Error saving: {str(e)}"

        return [
            fetch_job_from_url,
            read_resume,
            get_full_resume_content,
            add_tailored_experience,
            finalize_tailored_experiences,
            save_modified_resume,
            ask_user_question,
            save_cover_letter,
            save_user_info
        ]

    def _create_agent(self) -> AgentExecutor:
        """Create the LangChain agent."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        agent = create_tool_calling_agent(self.llm, self.tools, prompt)

        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=self.config.verbose,
            max_iterations=self.config.max_iterations,
            handle_parsing_errors="Error occurred. When calling save_tailored_experiences, you MUST include content='your full text here' with all the tailored descriptions written out as a string."
        )

    def run(
        self,
        resume_path: str,
        job_url_file: str,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run the agent to modify a resume and generate a cover letter.

        Args:
            resume_path: Path to the .tex resume file
            job_url_file: Path to the .txt file containing job URL
            output_dir: Directory for output files (default: same directory as job URL file)

        Returns:
            Dictionary with results and output paths
        """
        # Determine output directory - defaults to job URL file's directory
        if output_dir is None:
            output_dir = str(Path(job_url_file).parent)

        output_resume = os.path.join(output_dir, "resume_modified.tex")
        output_cover_letter = os.path.join(output_dir, "cover_letter.tex")

        # Store output paths as instance variables for tools to use as defaults
        self.output_resume_path = output_resume
        self.output_cover_letter_path = output_cover_letter

        # Read job URL from file
        try:
            job_url = read_job_url_from_file(job_url_file)
        except Exception as e:
            return {"error": f"Failed to read job URL: {str(e)}"}

        # Load or create user profile
        resume_abs_path = str(Path(resume_path).resolve())
        self.current_profile = self.profile_manager.find_profile_by_resume(resume_abs_path)

        profile_info = ""
        if self.current_profile:
            profile_info = f"\n\nUSER PROFILE (from previous sessions):\n"
            if self.current_profile.name:
                profile_info += f"Name: {self.current_profile.name}\n"
            if self.current_profile.skills:
                profile_info += f"Known Skills: {', '.join(self.current_profile.skills[:10])}\n"
            if self.current_profile.notes:
                profile_info += f"Notes: {'; '.join(self.current_profile.notes[-5:])}\n"
            profile_info += "\n⚠️ IMPORTANT: This profile information is VERIFIED from previous sessions. "
            profile_info += "Use it directly - DO NOT re-ask questions the user already answered. "
            profile_info += "Only ask NEW clarifying questions if you need information NOT in this profile.\n"
        else:
            # Create new profile
            user_id = Path(resume_path).stem
            self.current_profile = self.profile_manager.create_profile(
                user_id=user_id,
                resume_path=resume_abs_path
            )
            profile_info = "\n\n(First time working with this resume - learning about you as we go)\n"

        # Construct the initial prompt
        initial_prompt = f"""I need help tailoring my resume for a specific job application.{profile_info}

Resume file: {resume_path}
Job URL: {job_url}

PRIMARY TASK: Create tailored experience descriptions that highlight my relevant skills and achievements.

Please follow this workflow:

1. Fetch and analyze the job description - identify key requirements and skills
2. Read my resume to understand my background
3. Check the USER PROFILE above - USE that information directly, don't re-ask answered questions
4. Only ask NEW clarifying questions if needed (ONE question at a time)
5. Identify my 3-5 most relevant experiences that match the job requirements
6. For EACH relevant experience, call add_tailored_experience:
   add_tailored_experience(
       title="Job Title",
       company="Company Name",
       bullets=["Tailored bullet 1", "Tailored bullet 2", "Tailored bullet 3"]
   )
   Make bullets catchy for recruiters and professional for hiring managers.
   Use action verbs, quantifiable results, and mirror the job description language.

7. After adding ALL experiences, call finalize_tailored_experiences:
   finalize_tailored_experiences(
       target_job_title="the job title",
       target_company="the company name",
       key_skills=["skill1", "skill2", "skill3"]
   )

Output will be saved to: {str(Path(output_resume).parent / 'tailored_experiences.txt')}

Remember: Only use information from my actual resume. If you need to know something about my experience, ask me!"""

        try:
            result = self.agent.invoke({"input": initial_prompt})

            # Save updated profile with conversation notes
            if self.current_profile and self.conversation_notes:
                self.profile_manager.update_from_conversation(
                    user_id=self.current_profile.user_id,
                    notes=self.conversation_notes
                )

            tailored_experiences_path = str(Path(output_resume).parent / 'tailored_experiences.txt')

            # Normalize output to a plain string (handles content block lists)
            output = result["output"]
            if isinstance(output, list):
                output = "\n".join(
                    block.get("text", str(block)) if isinstance(block, dict) else str(block)
                    for block in output
                )
            elif not isinstance(output, str):
                output = str(output)

            return {
                "success": True,
                "output": output,
                "tailored_experiences_path": tailored_experiences_path,
                "resume_path": output_resume,
                "cover_letter_path": output_cover_letter
            }
        except Exception as e:
            # Still save profile notes even if there was an error
            if self.current_profile and self.conversation_notes:
                self.profile_manager.update_from_conversation(
                    user_id=self.current_profile.user_id,
                    notes=self.conversation_notes
                )

            return {
                "success": False,
                "error": str(e)
            }
