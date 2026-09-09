# agents/news_sentiment.py
import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

NEWS_PROMPT = """Search for recent news about {company_name} ({ticker}) from the last 30 days.

Based on what you find, provide:
1. **Overall Sentiment**: Positive / Negative / Neutral — with a one-sentence rationale
2. **Key News Items**: 3-5 bullet points of the most important recent developments
3. **Catalysts**: Any upcoming events or recent positives that could drive the stock higher
4. **Risks**: Any recent negatives, controversies, or concerns flagged in the news

Be specific — cite actual headlines or events, not generic statements."""

def news_node(state: dict) -> dict:
    ticker = state["ticker"]
    company_name = state.get("company_name", ticker)

    print(f"[news] Searching for news on {company_name} ({ticker})")

    model = state.get("agent_config", {}).get("news_model", "claude-sonnet-4-5")
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


    response = client.messages.create(
        model=model,
        max_tokens=2048,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{
            "role": "user",
            "content": NEWS_PROMPT.format(
                company_name=company_name,
                ticker=ticker
            )
        }]
    )

    

    news_summary = ""
    for block in response.content:
        if block.type == "text":
            news_summary += block.text

    print(f"[news] Done. Summary length: {len(news_summary)} chars")

    return {"news_summary": news_summary}