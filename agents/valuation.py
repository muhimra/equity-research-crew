# agents/valuation.py
import os
import io
import sys
import anthropic
from dotenv import load_dotenv

load_dotenv()

CODE_GEN_PROMPT = """You are a financial analyst writing Python code to value a stock.

Using the following fundamentals data, write a SHORT Python script that performs a basic DCF valuation.

Fundamentals data:
{fundamentals_json}

Requirements for your code:
- Use `freeCashflow` as the base FCF
- Assume a growth rate of 10% for years 1-5, then 3% terminal growth
- Use a discount rate (WACC) of 9%
- Calculate intrinsic value per share using `marketCap` as a proxy for shares * price
- Print the results clearly with labels
- Handle None values gracefully (use 0 or skip calculation if critical fields are None)
- Keep it under 30 lines
- DO NOT use any imports — no math, no numpy, no pandas. Plain Python arithmetic only.
- The variable `fundamentals_data` is already available as a dict — use it directly.

Return ONLY the Python code, no explanation, no markdown, no backticks."""

INTERPRETATION_PROMPT = """You are a financial analyst. A DCF valuation script produced the following output:

{code_output}

The current market data is:
{fundamentals_summary}

{revision_context}

Write a concise valuation summary (150-200 words) covering:
- What the DCF suggests about current valuation (overvalued/undervalued/fairly valued)
- Key assumptions made and their reasonableness
- Confidence level in this estimate and why
- Any important caveats

Be specific with numbers."""

def valuation_node(state: dict) -> dict:
    ticker = state["ticker"]
    fundamentals_data = state.get("fundamentals_data", {})
    fundamentals_summary = state.get("fundamentals_summary", "")
    revision_count = state.get("revision_count", 0)
    critic_feedback = state.get("critic_feedback", "")

    print(f"[valuation] Running valuation for {ticker} (revision #{revision_count})")

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # Build revision context if this is a retry
    revision_context = ""
    if revision_count > 0 and critic_feedback:
        revision_context = f"""IMPORTANT: A critic reviewed your previous valuation and requested revision.
Critic feedback: {critic_feedback}
Please explicitly address these concerns in your updated analysis."""

    # --- Step 1: Ask Claude to write the valuation code ---
    import json
    print("[valuation] Generating valuation code...")

    code_response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": CODE_GEN_PROMPT.format(
                fundamentals_json=json.dumps(fundamentals_data, indent=2)
            )
        }]
    )

    valuation_code = code_response.content[0].text.strip()

    if valuation_code.startswith("```"):
        lines = valuation_code.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        valuation_code = "\n".join(lines).strip()


    # --- Step 2: Execute the code in a restricted namespace ---
    restricted_globals = {
    "__builtins__": {
        "print": print,
        "round": round,
        "range": range,
        "len": len,
        "sum": sum,
        "abs": abs,
        "min": min,
        "max": max,
        "None": None,
        "True": True,
        "False": False,
        "int": int,
        "float": float,
        "str": str,
        "list": list,
        "dict": dict,
        "enumerate": enumerate,
        "zip": zip,
        "__import__": __import__,  # added
    }
}
    restricted_locals = {"fundamentals_data": fundamentals_data}

    # Capture printed output
    captured_output = io.StringIO()
    sys.stdout = captured_output

    try:
        exec(valuation_code, restricted_globals, restricted_locals)
    except Exception as e:
        sys.stdout = sys.__stdout__
        print(f"[valuation] Code execution error: {e}, falling back to summary only")
        code_output = f"Code execution failed: {e}"
    else:
        sys.stdout = sys.__stdout__

    code_output = captured_output.getvalue()
    print(f"[valuation] Execution output:\n{code_output}")

    # --- Step 3: Ask Claude to interpret the results ---
    print("[valuation] Generating interpretation...")

    interp_response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": INTERPRETATION_PROMPT.format(
                code_output=code_output,
                fundamentals_summary=fundamentals_summary,
                revision_context=revision_context
            )
        }]
    )

    valuation_summary = interp_response.content[0].text.strip()
    print(f"[valuation] Done. Summary length: {len(valuation_summary)} chars")

    return {"valuation": valuation_summary}