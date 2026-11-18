# Interview Prep Coach

An interactive Streamlit application that helps you prepare for technical and professional interviews. Provide a job description, configure the generation settings, and use an LLM to create role-focused questions and reference answers.

## Features

- **Role-focused questions** — Generate interview questions from a supplied job description.
- **Configurable practice** — Choose a target role, difficulty, number of questions, model, temperature, and prompt technique.
- **Prompt technique comparison** — Experiment with Zero-Shot, Few-Shot, Chain-of-Thought, Role-Based, and Structured Output prompt variants.
- **Reference answers and follow-ups** — Review suggested answers, tested skills, categories, difficulty, and follow-up questions.
- **Answer feedback** — Type an answer and request AI-generated feedback against the reference answer.
- **Input safeguards** — Apply deterministic validation and an LLM-based security check before generation.
- **Usage visibility** — Display token usage and estimated API cost when available.
- **Export** — Download generated question sets as Markdown, JSON, or plain text.

## Tech stack

- Python 3.11+
- Streamlit
- OpenAI Python SDK
- OpenRouter
- pytest and Ruff (development tools)

## Run locally

### 1. Clone the repository

```bash
git clone https://github.com/DaphineNakandi/interview-prep-coach.git
cd interview-prep-coach
```

### 2. Create and activate a virtual environment

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install the project

```bash
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

### 4. Configure your API key

Copy `.env.example` to `.env` and add your OpenRouter API key:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
DEFAULT_MODEL=openai/gpt-5-mini
DEFAULT_TEMPERATURE=0.7
DEFAULT_MAX_TOKENS=4000
```

Never commit `.env` or share your API key.

### 5. Start the app

```bash
streamlit run app.py
```

Streamlit will print a local URL to open in your browser.

## Run tests

```bash
pytest
```

Run Ruff checks with:

```bash
ruff check .
```

## Project structure

```text
interview-prep-coach/
├── app.py                  # Streamlit interface
├── src/
│   ├── config/             # Application settings
│   ├── llm/                # LLM client and generation services
│   ├── models/             # Question and usage data models
│   ├── prompts/            # Prompt templates and builders
│   ├── rag/                # Role-context retrieval
│   ├── security/           # Input validation and LLM guard
│   └── utils/              # Supporting utilities
├── tests/                  # Automated tests
├── .env.example            # Environment variable template
└── pyproject.toml          # Dependencies and tool configuration
```

## Notes

This project uses an API provider, so generating questions and evaluating answers may incur usage costs depending on the selected model and provider account. The security checks are safeguards, not a guarantee that every malicious input will be detected.

## Author

Daphine Nakandi
