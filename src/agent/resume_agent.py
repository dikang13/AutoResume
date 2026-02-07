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
        def save_modified_resume(new_content: str, output_path: str) -> str:
            """
            Save a modified resume after validating LaTeX syntax.

            Args:
                new_content: The modified LaTeX content
                output_path: Path where to save the modified resume

            Returns:
                Success or error message
            """
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

            Args:
                question: The question to ask the user

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

        return [
            fetch_job_from_url,
            read_resume,
            save_modified_resume,
            ask_user_question,
            save_cover_letter
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
            output_dir: Directory for output files (default: same as resume)

        Returns:
            Dictionary with results and output paths
        """
        # Determine output directory
        if output_dir is None:
            output_dir = str(Path(resume_path).parent)

        output_resume = os.path.join(output_dir, "resume_modified.tex")
        output_cover_letter = os.path.join(output_dir, "cover_letter.tex")

        # Read job URL from file
        try:
            job_url = read_job_url_from_file(job_url_file)
        except Exception as e:
            return {"error": f"Failed to read job URL: {str(e)}"}

        # Construct the initial prompt
        initial_prompt = f"""I need help tailoring my resume and creating a cover letter for a job application.

Resume file: {resume_path}
Job URL: {job_url}

Please:
1. Fetch and analyze the job description
2. Read and understand my resume
3. Ask me any clarifying questions about my experience if needed
4. Suggest modifications to tailor the resume for this job
5. Generate a personalized cover letter

Save the modified resume to: {output_resume}
Save the cover letter to: {output_cover_letter}

Remember: Only use information from my actual resume. If you need to know something about my experience, ask me!"""

        try:
            result = self.agent.invoke({"input": initial_prompt})

            return {
                "success": True,
                "output": result["output"],
                "resume_path": output_resume,
                "cover_letter_path": output_cover_letter
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
