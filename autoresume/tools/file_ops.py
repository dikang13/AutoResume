"""File operations for saving resumes."""

import shutil
from pathlib import Path
from .latex_parser import validate_latex_syntax, write_latex_resume


def save_modified_resume(content: str, output_path: str, source_resume_path: str = None) -> str:
    """
    Validate and save a modified LaTeX resume, copying any .cls files from the source.

    Returns:
        Success or error message.
    """
    if not content or len(content) < 500:
        return f"ERROR: Content too short ({len(content)} chars). Must be the complete LaTeX document."

    is_valid, issues = validate_latex_syntax(content)
    if not is_valid:
        return f"LaTeX validation failed: {', '.join(issues)}"

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    write_latex_resume(output_path, content)

    # Copy .cls files from source directory
    copied = []
    if source_resume_path:
        src_dir = Path(source_resume_path).parent
        out_dir = Path(output_path).parent
        for cls_file in src_dir.glob("*.cls"):
            dest = out_dir / cls_file.name
            shutil.copy(cls_file, dest)
            copied.append(cls_file.name)

    msg = f"Resume saved to {output_path}"
    if copied:
        msg += f" (copied: {', '.join(copied)})"
    return msg
