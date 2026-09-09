# agents/critic.py
import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

CRITIC_PROMPT = """You are a skeptical senior equity research analyst reviewing a junior analyst's work on {ticker}.

Here are the three sections you are reviewing:

## FUNDAMENTALS SUMMARY:
{fundamentals_summary}

## NEWS & SENTIMENT SUMMARY:
{news_summary}

## VALUATION:
{valuation}

Your job is to critically evaluate this research for:
1. **Unsupported assumptions** — are any claims made without backing from the data?
2. **Internal contradictions** — does the valuation contradict the fundamentals or news?
3. **Missing risks** — are there obvious risks not mentioned (macro, competitive, regulatory)?
4. **Overly optimistic framing** — is bad news being downplayed or good news overstated?
5. **Valuation methodology weaknesses** — are the DCF assumptions reasonable and clearly stated?

Be specific — reference actual numbers and claims from the sections above.
Do NOT give generic feedback like "consider adding more detail." Point to exact issues.

VERDICT RULES — follow these strictly:
- If the valuation shows more than 30% downside, you MUST issue REVISE unless sensitivity analysis is provided
- If any section contains incomplete sentences or cut-off text, you MUST issue REVISE
- If DCF assumptions (WACC, growth rate) are not explicitly stated, you MUST issue REVISE
- If there are internal contradictions between sections, you MUST issue REVISE
- Only APPROVE if ALL of the above pass

End your response with EXACTLY one of these two options on its own line with nothing after it:
APPROVE
REVISE: <your specific reason in one sentence>"""

def critic_node(state: dict) -> dict:
    ticker = state["ticker"]
    fundamentals_summary = state.get("fundamentals_summary", "")
    news_summary = state.get("news_summary", "")
    valuation = state.get("valuation", "")
    revision_count = state.get("revision_count", 0)

    print(f"[critic] Reviewing research for {ticker} (revision #{revision_count})")

    model = state.get("agent_config", {}).get("critic_model", "claude-sonnet-4-5")
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    response = client.messages.create(
        model=model,
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": CRITIC_PROMPT.format(
                ticker=ticker,
                fundamentals_summary=fundamentals_summary,
                news_summary=news_summary,
                valuation=valuation
            )
        }]
    )

    critic_feedback = response.content[0].text.strip()

    if "APPROVE" not in critic_feedback and "REVISE" not in critic_feedback:
        print("[critic] WARNING: No verdict found in response — may be truncated. Defaulting to REVISE.")
        critic_feedback += "\nREVISE: Response truncated, manual review required."


    # Log the verdict clearly
    if "REVISE" in critic_feedback:
        print(f"[critic] Verdict: REVISE requested")
    else:
        print(f"[critic] Verdict: APPROVED")

    print(f"[critic] Full feedback length: {len(critic_feedback)} chars")

    return {
        "critic_feedback": critic_feedback,
        "revision_count": revision_count + 1
    }