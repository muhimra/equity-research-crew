# agents/fundamentals.py
import os
import json
import anthropic
from dotenv import load_dotenv
from data.fetch_fundamentals import get_fundamentals

load_dotenv()

FUNDAMENTALS_PROMPT = """You are a financial analyst. Below is raw financial data for {ticker}.
Analyze it and write a concise ~200 word summary covering:
- Key financial ratios and what they indicate
- Revenue and profit trends
- Any red flags or concerns
- Overall financial health assessment

Raw data:
{fundamentals_json}

Be specific and use the actual numbers. Flag any missing data explicitly."""


def fundamentals_node(state: dict) -> dict:
    ticker = state["ticker"]
    print(f"[fundamentals] Fetching data for {ticker}")

    # Step 1: Get real data
    fundamentals_data = get_fundamentals(ticker)
    company_name = fundamentals_data.get("longName", ticker)

    print(f"[fundamentals] Got data for {company_name}, calling Claude...")

    # Step 2: Call Claude
    model = state.get("agent_config", {}).get("fundamentals_model", "claude-sonnet-4-5")
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    prompt = FUNDAMENTALS_PROMPT.format(
        ticker=ticker,
        fundamentals_json=json.dumps(fundamentals_data, indent=2)
    )

    message = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    fundamentals_summary = message.content[0].text
    print(f"[fundamentals] Done. Summary length: {len(fundamentals_summary)} chars")

    return {
        "fundamentals_data": fundamentals_data,
        "fundamentals_summary": fundamentals_summary,
        "company_name": company_name
    }