# 📈 Equity Research Analyst Crew

A multi-agent AI system that takes a stock ticker and produces a professional investment research memo. Built with LangGraph for orchestration and Claude (Anthropic) as the LLM for every agent.

The defining feature is a **critic/revision loop** — a critic agent reviews intermediate outputs and can route the workflow back for revision before final synthesis, demonstrating real multi-agent orchestration rather than simple prompt chaining.

---

## Architecture

```mermaid
graph TD
    A[User Input: Ticker] --> B[Fundamentals Agent]
    B --> C[News & Sentiment Agent]
    C --> D[Valuation Agent]
    D --> E[Critic Agent]
    E -->|REVISE - max 2x| D
    E -->|APPROVE| F[Synthesis Agent]
    F --> G[Final Investment Memo]

