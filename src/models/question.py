"""Data models for interview questions.

Defines the core data structures used throughout the app:
- Difficulty: enum of easy/medium/hard
- Question: a single interview question with metadata
- QuestionSet: a collection of questions with set-level metadata
"""

from dataclasses import dataclass, field
from enum import StrEnum


class Difficulty(StrEnum):
    """Difficulty level for interview questions.

    Uses StrEnum so the value serializes directly to a string
    (JSON-friendly, Streamlit-friendly).

    Members are uppercase (Python convention), values are lowercase
    (display convention).
    """

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class Question:
    """A single interview question with reference answer and metadata.

    Attributes:
        id: Unique identifier within a QuestionSet.
        question: The question text shown to the user.
        reference_answer: A strong example answer.
        category: Type of question (technical, behavioral, situational).
        difficulty: Difficulty level (easy, medium, hard).
        skills_tested: List of skills this question assesses.
        follow_up: Optional follow-up question for deeper probing.
    """

    id: int
    question: str
    reference_answer: str
    category: str
    difficulty: Difficulty
    skills_tested: list[str] = field(default_factory=list)
    follow_up: str = ""


@dataclass
class QuestionSet:
    """A collection of interview questions with metadata.

    Attributes:
        questions: List of Question objects.
        job_title: The role these questions are for.
        generated_at: ISO timestamp of when the set was generated.
        model_used: The LLM model used to generate the questions.
        prompt_variant: Which system prompt variant generated these.
    """

    questions: list[Question]
    job_title: str
    generated_at: str
    model_used: str
    prompt_variant: str

    @property
    def total_questions(self) -> int:
        """Number of questions in the set.

        Computed from len(questions) so it can never diverge from
        the actual list.

        Returns:
            The number of questions.
        """
        return len(self.questions)
