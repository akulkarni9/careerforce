from typing import TypedDict, Union


class ApplicationState(TypedDict, total=False):
    raw_jd: Union[str, dict[str, str]]  # str for text input, dict for image payload
    master_resume: str
    structured_jd: str
    critique: str
    match_score: int
    prep: str
