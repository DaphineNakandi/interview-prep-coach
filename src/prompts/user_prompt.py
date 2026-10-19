"""User prompt builder.

Builds the user message from job-specific inputs. Stateless function:
same inputs always produce the same output.
"""

from src.models.question import Difficulty


def build_user_prompt(
    job_description: str,
    difficulty: Difficulty,
    num_questions: int,
    context: str = "",
) -> str:
    """Build the user prompt for interview question generation.

    Args:
        job_description: The job description text to generate questions for.
        difficulty: Difficulty level for the questions.
        num_questions: Number of questions to generate.
        context: Optional context from RAG-lite retrieval. Injected before
            the job description if provided.

    Returns:
        A formatted user prompt ready to send to the LLM.
    """
    parts = [
        f"Generate {num_questions} interview questions at {difficulty} difficulty.",
        "",
    ]

    if context:
        parts.append("Relevant context for this role:")
        parts.append(context)
        parts.append("")

    parts.append("Job description:")
    parts.append(job_description)

    return "\n".join(parts)



