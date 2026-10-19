# Interview Prep Coach

A Streamlit web app that generates job-specific interview questions with 
reference answers, powered by OpenRouter and Large Language Models.

## Features

- **Tailored Generation:** Paste any job description and get questions specifically tailored to that role.
- **Configurable:** Adjust difficulty, number of questions, model, prompt technique, and temperature.
- **5 Prompt Techniques:** Compare Zero-Shot, Few-Shot, Chain-of-Thought, Role-Based, and Structured Output.
- **RAG-lite Context:** Uses a keyword-based retriever to inject role-specific context into the prompt.
- **Two-Layer Security:** 
  1. Deterministic input validation (length, injection patterns).
  2. LLM-based guard that screens inputs for malicious intent.
- **Cost Transparency:** Displays exact token usage and cost per generation.
- **Export:** Download generated questions as Markdown, JSON, or Plain Text.

## Architecture

The app is built with a strict separation of concerns:

- `src/models/`: Data models (Question, QuestionSet, Usage, Difficulty).
- `src/config/`: Settings loading and validation.
- `src/prompts/`: System and user prompt builders.
- `src/llm/`: OpenRouter API client, exceptions, and service orchestration.
- `src/security/`: Input validator and LLM-based guard.
- `src/rag/`: Knowledge base and keyword retriever.
- `src/utils/`: JSON parsing utilities.
- `app.py`: Streamlit UI.

## Installation

1. **Clone the repo:**
   ```bash
   git clone <your-repo-url>
   cd interview-prep-coach
