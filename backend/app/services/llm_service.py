import json

from openai import OpenAI

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

RECOMMENDATION_SYSTEM_PROMPT = """You are a senior financial advisor for small and medium businesses,
acting as an action planner: prioritize and quantify recommendations, don't just list generic advice.
Given a company's financial metrics, health score, and detected risks, produce 4-6 specific,
actionable recommendations. Each recommendation MUST reference the actual numbers provided
(e.g. "Profit margin fell to 4.2%, below the 8% healthy threshold ...").
Respond ONLY with JSON: a list of objects with keys:
- "category": one of expenses, inventory, customer, cash, marketing, debt, revenue
- "priority": low, medium, or high
- "text": the recommendation, referencing the data
- "based_on": the specific metric(s) driving it
- "confidence": a number from 0 to 1 — how confident you are this action will help, given how
  directly the data supports it (e.g. a metric far outside a healthy range = high confidence)
- "impact_estimate": your best-effort estimate of the annualized dollar impact of taking this
  action, as a plain number (e.g. 4500 or -1200), derived from the provided revenue/expense
  figures — a realistic order-of-magnitude estimate, not a precise forecast. Use a negative
  number only if the action itself costs money before it pays off.
- "difficulty": low, medium, or high — how hard this is to actually implement"""

CHAT_SYSTEM_PROMPT = """You are an AI business analyst assistant embedded in a Business Health
Analyzer dashboard. Answer the user's question about their company using ONLY the financial
context provided below. Be concise, specific, and always cite the relevant numbers. If asked
to predict something, use the forecast data provided; do not invent figures that aren't in
the context."""


def _get_client() -> OpenAI | None:
    if not settings.OPENAI_API_KEY:
        return None
    return OpenAI(api_key=settings.OPENAI_API_KEY)


def is_llm_available() -> bool:
    return bool(settings.OPENAI_API_KEY)


def generate_recommendations_llm(context: dict) -> list[dict] | None:
    client = _get_client()
    if client is None:
        return None

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": RECOMMENDATION_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(context)},
            ],
            response_format={"type": "json_object"},
            temperature=0.4,
        )
        content = response.choices[0].message.content
        parsed = json.loads(content)
        items = parsed if isinstance(parsed, list) else parsed.get("recommendations", [])
        return items
    except Exception:  # noqa: BLE001 - degrade to rule-based recommendations on any API failure
        logger.exception("LLM recommendation generation failed; falling back to rule-based engine")
        return None


def answer_chat_llm(context: dict, question: str) -> str | None:
    client = _get_client()
    if client is None:
        return None

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": CHAT_SYSTEM_PROMPT},
                {"role": "user", "content": f"Business data:\n{json.dumps(context)}\n\nQuestion: {question}"},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content
    except Exception:  # noqa: BLE001
        logger.exception("LLM chat completion failed; falling back to rule-based answer")
        return None
