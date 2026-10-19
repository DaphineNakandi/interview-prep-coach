"""End-to-end test for Phase 5: client + parser + service."""

from src.config.settings import load_settings
from src.llm.service import generate_interview_questions

settings = load_settings()
print("Configured:", settings.is_configured)

if not settings.is_configured:
    print("ERROR: API key not set")
    exit(1)

print("\nCalling OpenRouter...")
question_set = generate_interview_questions(
    settings=settings,
    job_description=(
        "Senior Python Developer. 5+ years experience. "
        "Strong in algorithms, system design, and mentoring. "
        "Familiar with cloud deployments (AWS/GCP)."
    ),
    job_title="Senior Python Developer",
    difficulty="medium",
    num_questions=3,
    prompt_variant="few_shot",
)

print(f"\nGot {question_set.total_questions} questions")
print(f"Model: {question_set.model_used}")
print(f"Variant: {question_set.prompt_variant}")
print(f"Usage: {question_set.usage}")

print("\n=== First question ===")
q = question_set.questions[0]
print(f"ID: {q.id}")
print(f"Question: {q.question}")
print(f"Category: {q.category}")
print(f"Difficulty: {q.difficulty}")
print(f"Skills: {q.skills_tested}")
print(f"Follow-up: {q.follow_up}")
print(f"\nReference answer:\n{q.reference_answer[:300]}...")