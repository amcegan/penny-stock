# AI Agents & Automation Documentation

## Overview
This project was developed with the assistance of an AI agent (Antigravity). The development followed a structured process of Planning, Scaffolding, Implementation, and Verification.

## Agent Configuration
The agent operates under strict rules defined in `.agent/rules/coding_standards.md` (conceptually, though file creation was blocked by gitignore in this session, the principles were followed).

### Core Rules
1.  **Modular Architecture**: All business logic is separated into `stock_scanner/` modules.
2.  **Safety**: No arbitrary command execution used for business logic. Browser access restricted.
3.  **Security**: Secrets managed via environment variables.
4.  **Testing**: Unit tests generated for key nodes using `pytest`.

## Prompts & AI Logic
The application uses Generative AI (Gemini 2.0 Flash) for:
1.  **Sentiment Analysis**: Analyzing news headlines to filter out negative news.
    - Prompt Location: `stock_scanner/prompts.py` (SENTIMENT_PROMPT)
2.  **Report Generation**: Creating professional company and CEO reports.
    - Prompt Location: `stock_scanner/prompts.py` (COMPANY_REPORT_PROMPT, CEO_REPORT_PROMPT)

## Workflows
- **Daily Scan**: Automated via GitHub Actions (`.github/workflows/daily_scan.yml`).
- **Tests**: `pytest` allows verification of logic without hitting external APIs (using mocks).

## LangGraph Logic
The application uses a linear graph with conditional logic inside the nodes:
`Screener` -> `Volume Filter` -> `Analyst Filter` -> `News Analysis` -> `Reporting`

- **State**: `GraphState` (TypedDict) tracks candidates through the pipeline.
- **Observability**: configured for LangSmith tracing via `LANGCHAIN_TRACING_V2`.
