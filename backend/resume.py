from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).parent / "data"


def resume_filename() -> Optional[str]:
    """Return the name of the resume .docx in data/, or None if absent."""
    path = next(DATA_DIR.glob("*.docx"), None)
    return path.name if path else None


def load_resume() -> str:
    """Load the candidate's resume text from the first .docx in data/."""
    from docx import Document

    path = next(DATA_DIR.glob("*.docx"), None)
    if not path:
        raise FileNotFoundError("No .docx file found in data/.")

    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs)
