"""Test script for the resume agent with mock user input.

Usage:
    # With UV (recommended)
    uv run python test_agent.py

    # With activated environment
    python test_agent.py
"""

import sys
import os
from dotenv import load_dotenv
from src.agent.resume_agent import ResumeAgent, ResumeAgentConfig

# Load environment variables
load_dotenv()

# Mock user input - provide sample answers
mock_responses = [
    "I have experience with Python, R, SQL, and data visualization tools.",
    "I have worked with healthcare data at Boehringer Ingelheim.",
    "I'm interested in health informatics and clinical data analysis.",
    "Yes, I can provide more details if needed.",
    "That sounds good, please proceed."
]

response_index = 0

def mock_user_input(prompt: str) -> str:
    """Mock function to simulate user input."""
    global response_index
    if response_index < len(mock_responses):
        response = mock_responses[response_index]
        response_index += 1
        print(f"{prompt}{response}")
        return response
    else:
        return "Yes, please continue."

# Create agent with mock input
config = ResumeAgentConfig(model_name="claude-sonnet-4-5-20250929")
agent = ResumeAgent(config=config, user_input_callback=mock_user_input)

# Run the agent
print("="*80)
print("TESTING AGENT WITH MOCK USER INPUT")
print("="*80)

try:
    result = agent.run(
        resume_path="examples/cv_baseline.tex",
        job_url_file="examples/job_url_20260207.txt",
        output_dir="examples"
    )

    print("\n" + "="*80)
    print("AGENT COMPLETED!")
    print("="*80)

    if result.get("success"):
        print("\n[SUCCESS] Agent completed successfully!")
        print(f"\nModified resume: {result.get('resume_path')}")
        print(f"Cover letter: {result.get('cover_letter_path')}")
        print(f"\nAgent output:\n{result.get('output')}")
    else:
        print(f"\n[ERROR] Agent failed: {result.get('error')}")

except KeyboardInterrupt:
    print("\n\nTest interrupted by user.")
    sys.exit(0)
except Exception as e:
    print(f"\n[ERROR] Test failed: {str(e)}")
    import traceback
    traceback.print_exc()
