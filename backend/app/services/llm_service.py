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

CHAT_SYSTEM_PROMPT = """You are the AI CFO — an on-call financial advisor embedded in this SME's
AIBHA dashboard, speaking to the business owner directly (not a generic analyst summarizing a
report). Answer using ONLY the financial context provided below: metrics, health score, risks,
forecasts, recommendations, cash runway, and goal progress. Be concise, always cite the actual
numbers, and never invent a figure that isn't in the context.

Act like a CFO, not a search engine: when the data supports it, don't just answer the literal
question — say what it means for the business and what to do next (e.g. if asked about cash and
runway is under 3 months, say so plainly and point to the one or two levers that would help most,
drawing on the recommendations and goals context). If a number needed to answer isn't in the
context (e.g. no goals set, no forecast run yet), say so directly and suggest which page would
produce it, rather than guessing. Keep replies short — a few sentences, not a report — this is a
chat widget, not an essay. Use the prior turns of this conversation for continuity: don't
re-introduce yourself or repeat context the user already has if this isn't the first message."""


AGENT_PROMPTS = {
    "cash_flow": """You are a cash-flow specialist agent. You see ONLY the cash position data below
(current cash, burn rate, runway, severity) — nothing else about this business. Respond ONLY with
JSON: {"severity": "low"|"medium"|"high", "summary": "1-2 sentences on the cash position",
"recommendation": "one concrete action"}.""",
    "risk": """You are a risk-assessment specialist agent. You see ONLY the detected risk flags and
health score below — nothing else about this business. Respond ONLY with JSON: {"severity":
"low"|"medium"|"high", "summary": "1-2 sentences on the risk picture", "recommendation": "one
concrete action"}.""",
    "growth": """You are a growth specialist agent. You see ONLY revenue/customer growth rates and
industry percentile below — nothing else about this business. Respond ONLY with JSON: {"severity":
"low"|"medium"|"high", "summary": "1-2 sentences on the growth trajectory", "recommendation": "one
concrete action"}.""",
    "goals": """You are a goals-tracking specialist agent. You see ONLY the company's stated goals
and their progress below — nothing else about this business. Respond ONLY with JSON: {"severity":
"low"|"medium"|"high", "summary": "1-2 sentences on goal progress", "recommendation": "one concrete
action"}.""",
}

ORCHESTRATOR_SYSTEM_PROMPT = """You are the Chief of Staff synthesizing findings from four
specialist agents (Cash Flow, Risk, Growth, Goals) into one executive briefing for the business
owner. You do NOT see the underlying financial data yourself — only each specialist's own summary
and severity rating, given below. Write 3-5 sentences: state the overall verdict, name the single
most urgent issue and which agent flagged it, then give one clear next step. Do not just restate
all four findings — synthesize and prioritize, the way a chief of staff briefs an executive who
doesn't have time to read four separate reports."""


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


def answer_chat_llm(context: dict, question: str, history: list[dict] | None = None) -> str | None:
    client = _get_client()
    if client is None:
        return None

    # Prior turns give the model real multi-turn memory (follow-up questions like "and
    # what about next quarter?" resolve correctly) without re-sending the full context
    # on every turn — only the latest turn carries the fresh data snapshot.
    messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]
    for turn in (history or [])[-10:]:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": f"Business data:\n{json.dumps(context)}\n\nQuestion: {question}"})

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            temperature=0.3,
        )
        return response.choices[0].message.content
    except Exception:  # noqa: BLE001
        logger.exception("LLM chat completion failed; falling back to rule-based answer")
        return None


def run_agent_llm(domain: str, data: dict) -> dict | None:
    """One specialist agent's LLM call — deliberately given only `data`, its own
    bounded slice of context, never the company's full financial picture."""
    client = _get_client()
    if client is None:
        return None

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": AGENT_PROMPTS[domain]},
                {"role": "user", "content": json.dumps(data, default=str)},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        parsed = json.loads(response.choices[0].message.content)
        if not all(k in parsed for k in ("severity", "summary", "recommendation")):
            return None
        return parsed
    except Exception:  # noqa: BLE001 - degrade to this agent's rule-based fallback
        logger.exception("Agent LLM call failed for domain=%s; falling back to rule-based", domain)
        return None


def run_orchestrator_llm(data: dict) -> str | None:
    """The orchestrator's LLM call — sees only the four specialists' own findings
    (summary + severity), never the raw data those specialists analyzed."""
    client = _get_client()
    if client is None:
        return None

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": ORCHESTRATOR_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(data, default=str)},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content
    except Exception:  # noqa: BLE001
        logger.exception("Orchestrator LLM call failed; falling back to rule-based synthesis")
        return None
