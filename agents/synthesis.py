# agents/synthesis.py
import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

SYNTHESIS_PROMPT = """You are a senior equity research analyst writing a final investment memo.

You have the following research sections prepared by your team:

## COMPANY: {ticker} — {company_name}

## FUNDAMENTALS SUMMARY:
{fundamentals_summary}

## NEWS & SENTIMENT:
{news_summary}

## VALUATION:
{valuation}

## CRITIC / RISK REVIEW:
{critic_feedback}

Write a professional one-page investment memo with exactly these sections:

# {company_name} ({ticker}) — Investment Research Memo

## Company Overview
2-3 sentences on what the company does, sector, and market position.

## Fundamentals
Key financial metrics and what they mean. Reference specific numbers.

## News & Sentiment
Recent developments, overall sentiment, and key catalysts or headwinds.

## Valuation
DCF findings, what the market is pricing in, and confidence level.

## Risks
Explicitly address every concern raised in the critic review. Do not soften or omit them.

## Recommendation
Buy / Hold / Sell with a one paragraph rationale that reconciles the valuation gap,
fundamentals quality, and risks. Be direct — do not hedge excessively.

---
*This memo is for educational purposes only and is not investment advice.*"""

def synthesis_node(state: dict) -> dict:
    ticker = state["ticker"]
    company_name = state.get("company_name", ticker)

    print(f"[synthesis] Writing final memo for {company_name} ({ticker})")

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": SYNTHESIS_PROMPT.format(
                ticker=ticker,
                company_name=company_name,
                fundamentals_summary=state.get("fundamentals_summary", ""),
                news_summary=state.get("news_summary", ""),
                valuation=state.get("valuation", ""),
                critic_feedback=state.get("critic_feedback", "")
            )
        }]
    )

    final_memo = response.content[0].text.strip()
    print(f"[synthesis] Done. Memo length: {len(final_memo)} chars")

    return {"final_memo": final_memo}