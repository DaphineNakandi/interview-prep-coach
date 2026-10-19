"""Interview Prep Coach — Streamlit UI.

Single-page app for generating job-specific interview questions.
Settings live in the sidebar; results in the main area.
"""

import json
from datetime import datetime

import streamlit as st

from src.config.settings import load_settings
from src.llm.exceptions import (
    LLMAuthError,
    LLMConnectionError,
    LLMError,
    LLMParseError,
    LLMRateLimitError,
    LLMTruncatedError,
)
from src.llm.service import generate_interview_questions
from src.models.question import Difficulty, QuestionSet
from src.security.exceptions import SecurityError


# --- Helper functions ---


def format_as_markdown(question_set: QuestionSet) -> str:
    """Format a QuestionSet as human-readable Markdown.

    Args:
        question_set: The QuestionSet to format.

    Returns:
        A Markdown string.
    """
    lines = [
        f"# Interview Questions: {question_set.job_title}",
        "",
        f"**Generated:** {question_set.generated_at}  ",
        f"**Model:** {question_set.model_used}  ",
        f"**Prompt variant:** {question_set.prompt_variant}  ",
        f"**Total questions:** {question_set.total_questions}",
        "",
        "---",
        "",
    ]

    for q in question_set.questions:
        lines.append(f"## Question {q.id}: {q.question}")
        lines.append("")
        lines.append(f"**Category:** {q.category}  ")
        lines.append(f"**Difficulty:** {q.difficulty}  ")
        lines.append(f"**Skills tested:** {', '.join(q.skills_tested)}")
        lines.append("")
        lines.append("### Reference Answer")
        lines.append("")
        lines.append(q.reference_answer)
        lines.append("")
        if q.follow_up:
            lines.append(f"### Follow-up: {q.follow_up}")
            lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def format_as_plain_text(question_set: QuestionSet) -> str:
    """Format a QuestionSet as plain text.

    Args:
        question_set: The QuestionSet to format.

    Returns:
        A plain text string.
    """
    lines = [
        f"Interview Questions: {question_set.job_title}",
        "=" * 50,
        "",
        f"Generated: {question_set.generated_at}",
        f"Model: {question_set.model_used}",
        f"Total: {question_set.total_questions}",
        "",
    ]

    for q in question_set.questions:
        lines.append(f"Q{q.id}: {q.question}")
        lines.append(f"    Category: {q.category} | Difficulty: {q.difficulty}")
        lines.append(f"    Skills: {', '.join(q.skills_tested)}")
        lines.append(f"    Answer: {q.reference_answer}")
        if q.follow_up:
            lines.append(f"    Follow-up: {q.follow_up}")
        lines.append("")

    return "\n".join(lines)


def format_as_json(question_set: QuestionSet) -> str:
    """Format a QuestionSet as JSON.

    Args:
        question_set: The QuestionSet to format.

    Returns:
        A JSON string.
    """
    data = {
        "job_title": question_set.job_title,
        "generated_at": question_set.generated_at,
        "model_used": question_set.model_used,
        "prompt_variant": question_set.prompt_variant,
        "total_questions": question_set.total_questions,
        "questions": [
            {
                "id": q.id,
                "question": q.question,
                "reference_answer": q.reference_answer,
                "category": q.category,
                "difficulty": str(q.difficulty),
                "skills_tested": q.skills_tested,
                "follow_up": q.follow_up,
            }
            for q in question_set.questions
        ],
    }
    if question_set.usage:
        data["usage"] = {
            "prompt_tokens": question_set.usage.prompt_tokens,
            "completion_tokens": question_set.usage.completion_tokens,
            "total_tokens": question_set.usage.total_tokens,
            "reasoning_tokens": question_set.usage.reasoning_tokens,
            "cost_usd": question_set.usage.cost_usd,
        }
    return json.dumps(data, indent=2)


def display_question(question, index: int) -> None:
    """Display a single question in an expander.

    Args:
        question: The Question object to display.
        index: The display index (1-based).
    """
    with st.expander(f"Q{index}: {question.question[:80]}..."):
        st.markdown(f"**Category:** {question.category}")
        st.markdown(f"**Difficulty:** {question.difficulty}")
        st.markdown(f"**Skills tested:** {', '.join(question.skills_tested)}")
        st.markdown("---")
        st.markdown("### Reference Answer")
        st.markdown(question.reference_answer)
        if question.follow_up:
            st.markdown("---")
            st.markdown(f"**Follow-up:** {question.follow_up}")


def display_generation(question_set: QuestionSet) -> None:
    """Display a full QuestionSet with usage, download, and questions.

    Args:
        question_set: The QuestionSet to display.
    """
    # Metadata
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Questions", question_set.total_questions)
    col2.metric("Model", question_set.model_used.split("/")[-1])
    col3.metric("Variant", question_set.prompt_variant)
    if question_set.usage:
        col4.metric("Cost", f"${question_set.usage.cost_usd:.4f}")

    if question_set.usage:
        with st.expander("Token usage details"):
            st.markdown(f"- **Prompt tokens:** {question_set.usage.prompt_tokens}")
            st.markdown(f"- **Completion tokens:** {question_set.usage.completion_tokens}")
            st.markdown(f"- **Reasoning tokens:** {question_set.usage.reasoning_tokens}")
            st.markdown(f"- **Total tokens:** {question_set.usage.total_tokens}")
            st.markdown(f"- **Cost:** ${question_set.usage.cost_usd:.6f}")

    st.markdown("---")

    # Questions
    for i, q in enumerate(question_set.questions, start=1):
        display_question(q, i)

    st.markdown("---")

    # Download
    st.subheader("Export")
    col_format, col_download = st.columns([1, 2])
    with col_format:
        export_format = st.radio(
            "Format",
            options=["Markdown", "JSON", "Plain text"],
            horizontal=False,
        )

    formatters = {
        "Markdown": (format_as_markdown, "md", "text/markdown"),
        "JSON": (format_as_json, "json", "application/json"),
        "Plain text": (format_as_plain_text, "txt", "text/plain"),
    }
    formatter, ext, mime = formatters[export_format]
    content = formatter(question_set)

    with col_download:
        st.download_button(
            label=f"Download as .{ext}",
            data=content,
            file_name=f"interview_questions_{question_set.job_title.replace(' ', '_')}.{ext}",
            mime=mime,
            use_container_width=True,
        )


# --- Page config ---
st.set_page_config(
    page_title="Interview Prep Coach",

    layout="wide",
)


# --- Settings ---
@st.cache_resource
def get_settings():
    """Load and cache settings."""
    return load_settings()


settings = get_settings()


# --- Session state ---
if "generations" not in st.session_state:
    st.session_state.generations = []  # list of (label, QuestionSet)


# --- Header ---
st.title("Interview Prep Coach")
st.markdown(
    "Generate tailored interview questions with reference answers. "
    "Paste a job description, pick your settings, and start practicing."
)


# --- Sidebar: Settings ---
with st.sidebar:
    st.header("⚙️ Settings")

    job_title = st.text_input(
        "Job title",
        value="Senior Python Developer",
        help="Short title for the role.",
    )

    difficulty = st.selectbox(
        "Difficulty",
        options=[d.value for d in Difficulty],
        index=1,
        help="How hard should the questions be?",
    )

    num_questions = st.slider(
        "Number of questions",
        min_value=1,
        max_value=10,
        value=5,
    )

    with st.expander("Advanced settings"):
        prompt_variant = st.selectbox(
            "Prompt technique",
            options=[
                "zero_shot",
                "few_shot",
                "chain_of_thought",
                "role_based",
                "structured_output",
            ],
            index=1,
        )

        model = st.selectbox(
            "Model",
            options=[
                "openai/gpt-5-mini",
                "openai/gpt-5-nano",
                "openai/gpt-5",
            ],
            index=0,
        )

        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
        )

        max_tokens = st.slider(
            "Max tokens",
            min_value=1000,
            max_value=8000,
            value=4000,
            step=500,
        )

        enable_rag = st.checkbox("Enable RAG-lite", value=True)
        enable_llm_guard = st.checkbox(
            "Enable LLM security guard",
            value=True,
            help="Screen input with a second LLM. Slower but safer.",
        )


# --- Main area: Input ---
st.header("Job Description")

job_description = st.text_area(
    "Paste the job description here",
    height=250,
    placeholder="Senior Python Developer with 5+ years experience...",
)

generate_button = st.button(
    "Generate Questions",
    type="primary",
    use_container_width=True,
)


# --- Handle generation ---
if generate_button:
    if not settings.is_configured:
        st.error(
            "API key not configured. "
            "Add OPENROUTER_API_KEY to your .env file."
        )
    elif not job_description.strip():
        st.warning("Please paste a job description first.")
    else:
        with st.spinner("Generating questions..."):
            try:
                question_set = generate_interview_questions(
                    settings=settings,
                    job_description=job_description,
                    job_title=job_title,
                    difficulty=difficulty,
                    num_questions=num_questions,
                    prompt_variant=prompt_variant,
                    model=model,
                    enable_rag=enable_rag,
                    enable_llm_guard=enable_llm_guard,
                )

                label = (
                    f"{job_title} "
                    f"({difficulty}, {prompt_variant}, "
                    f"{datetime.now().strftime('%H:%M:%S')})"
                )
                st.session_state.generations.append((label, question_set))
                st.session_state.generations = st.session_state.generations[-3:]

                st.success(
                    f"Generated {question_set.total_questions} questions!"
                )

            except SecurityError as e:
                st.error(f"Security check failed: {e}")
                st.info("Try rephrasing your job description.")
            except LLMAuthError as e:
                st.error(f"Authentication failed: {e}")
                st.info("Check your OPENROUTER_API_KEY in .env.")
            except LLMRateLimitError as e:
                st.error(f"Rate limited: {e}")
                st.info("Wait a moment and try again.")
            except LLMConnectionError as e:
                st.error(f"Connection error: {e}")
                st.info("Check your internet connection.")
            except LLMTruncatedError as e:
                st.error(f"Response truncated: {e}")
                st.info("Increase max tokens in advanced settings.")
            except LLMParseError as e:
                st.error(f" Could not parse LLM response: {e}")
                with st.expander("Raw response (for debugging)"):
                    st.code(e.raw_response)
            except LLMError as e:
                st.error(f"LLM error: {e}")
            except Exception as e:
                st.error(f"Unexpected error: {type(e).__name__}: {e}")


# --- Display results ---
if st.session_state.generations:
    st.header("📋 Results")

    if len(st.session_state.generations) == 1:
        _, question_set = st.session_state.generations[0]
        display_generation(question_set)
    else:
        tab_labels = [label for label, _ in st.session_state.generations]
        tabs = st.tabs(tab_labels)
        for tab, (_, question_set) in zip(tabs, st.session_state.generations):
            with tab:
                display_generation(question_set)