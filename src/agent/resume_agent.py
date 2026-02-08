"""Main resume agent implementation."""

import os
from typing import Optional, Dict, Any, Callable
from pathlib import Path

from langchain_anthropic import ChatAnthropic
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field

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
    max_iterations: int = Field(default=15)
    api_key: Optional[str] = Field(default=None)


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

            return f"Full resume content:\n\n{self.resume_content.raw_content}"

        @tool
        def save_modified_resume(new_content: str = None, output_path: str = None) -> str:
            """
            Save a modified resume after validating LaTeX syntax.

            ⚠️ CRITICAL: This tool requires BOTH parameters - you CANNOT call it without them!

            STEP-BY-STEP WORKFLOW (YOU MUST FOLLOW THIS):
            1. Call get_full_resume_content() to get the original LaTeX
            2. In your response, mentally construct the full modified version
            3. Call THIS tool with BOTH parameters:
               save_modified_resume(
                   new_content="\\\\documentclass{{resume}}...[FULL DOCUMENT]...\\\\end{{document}}",
                   output_path="path/to/save/resume_modified.tex"
               )

            ❌ WRONG - DO NOT DO THIS:
            - save_modified_resume()  # Missing both parameters!
            - save_modified_resume(output_path="...")  # Missing new_content!
            - save_modified_resume(new_content="...")  # Missing output_path!

            ✅ CORRECT - DO THIS:
            save_modified_resume(
                new_content="\\\\documentclass{{resume}}\\\\n...\\\\n\\\\end{{document}}",
                output_path="resume_modified.tex"
            )

            The new_content MUST be the ENTIRE LaTeX file (thousands of characters),
            not just a summary or description!

            Args:
                new_content: The COMPLETE modified LaTeX content - from \\\\documentclass to \\\\end{{document}} (REQUIRED - DO NOT SKIP THIS!)
                output_path: Full path where to save the file (REQUIRED - DO NOT SKIP THIS!)

            Returns:
                Success or error message
            """
            # Validation: Check if parameters are actually provided
            if not new_content or not output_path:
                return """ERROR: You must provide BOTH parameters!

                You called save_modified_resume incorrectly. You MUST provide:
                1. new_content: The ENTIRE modified LaTeX document (full file content)
                2. output_path: Where to save it

                Steps to fix:
                1. Get the full resume with: get_full_resume_content()
                2. Make your modifications to create the complete document
                3. Call: save_modified_resume(new_content="<FULL LATEX>", output_path="resume_modified.tex")

                The new_content should be the COMPLETE LaTeX file, starting with \\\\documentclass and ending with \\\\end{{document}}."""

            try:
                # Validate LaTeX syntax
                is_valid, issues = validate_latex_syntax(new_content)

                if not is_valid:
                    return f"LaTeX validation failed. Issues: {', '.join(issues)}"

                # Save the file
                write_latex_resume(output_path, new_content)

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
        def save_cover_letter(content: str, output_path: str) -> str:
            """
            Save a generated cover letter.

            Args:
                content: The cover letter content
                output_path: Path where to save the cover letter

            Returns:
                Success or error message
            """
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

        return [
            fetch_job_from_url,
            read_resume,
            get_full_resume_content,
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
            verbose=True,
            max_iterations=self.config.max_iterations,
            handle_parsing_errors=True
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
            profile_info += "\nUse this information as context but always verify with the user if unsure.\n"
        else:
            # Create new profile
            user_id = Path(resume_path).stem
            self.current_profile = self.profile_manager.create_profile(
                user_id=user_id,
                resume_path=resume_abs_path
            )
            profile_info = "\n\n(First time working with this resume - learning about you as we go)\n"

        # Construct the initial prompt
        initial_prompt = f"""I need help tailoring my resume and creating a cover letter for a job application.{profile_info}

Resume file: {resume_path}
Job URL: {job_url}

Please follow this workflow:
1. Fetch and analyze the job description
2. Read and understand my resume structure
3. Ask me any clarifying questions about my experience if needed (ONE question at a time)
4. Use get_full_resume_content to get the complete LaTeX document
5. Based on the job requirements and my answers, mentally plan the modifications
6. Construct the complete modified LaTeX document with your changes
7. Save the modified resume:

   ⚠️ CRITICAL - READ THIS CAREFULLY:
   You MUST call save_modified_resume with BOTH parameters filled in.
   DO NOT call it with missing parameters or it will fail!

   Required parameters:
   - new_content: The ENTIRE modified LaTeX document (full file, ~5000+ characters)
   - output_path: {output_resume}

   The new_content is NOT a summary - it's the COMPLETE LaTeX file from
   \\documentclass{{resume}} all the way to \\end{{document}}.

8. Generate and save a personalized cover letter to: {output_cover_letter}

⚠️ COMMON MISTAKE - DO NOT DO THIS:
❌ save_modified_resume()  # Missing BOTH parameters!
❌ save_modified_resume(output_path="{output_resume}")  # Missing new_content!

✅ CORRECT WAY:
✅ save_modified_resume(
       new_content="\\documentclass{{resume}}...5000 chars...\\end{{document}}",
       output_path="{output_resume}"
   )

Remember: Only use information from my actual resume. If you need to know something about my experience, ask me!"""

        try:
            result = self.agent.invoke({"input": initial_prompt})

            # Save updated profile with conversation notes
            if self.current_profile and self.conversation_notes:
                self.profile_manager.update_from_conversation(
                    user_id=self.current_profile.user_id,
                    notes=self.conversation_notes
                )

            return {
                "success": True,
                "output": result["output"],
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
