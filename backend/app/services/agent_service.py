"""Multi-agent architecture for the AI Briefing.

Four specialist agents each analyze one bounded domain (cash flow, risk, growth,
goals) using only the data relevant to that domain — never the company's full
financial picture — then an orchestrator agent synthesizes their findings (summary +
severity only, not the underlying numbers) into one executive briefing. This mirrors
the supervisor/specialist pattern used in production multi-agent systems: bounded
context per agent, hierarchical synthesis at the top, and independent specialist
reasoning that in principle (and here, in practice, via a thread pool) can run
concurrently since no agent depends on another's output.

Every agent has an LLM path (app/services/llm_service.py) and a rule-based fallback,
exactly like the rest of the app, so the briefing works with or without an
OPENAI_API_KEY.
"""
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.orm import Session

from app.ml.feature_engineering import summarize_features
from app.models.company import Company
from app.services.benchmark_service import get_benchmark
from app.services.cash_runway_service import get_cash_runway
from app.services.data_processing_service import get_company_financial_dataframe
from app.services.goal_service import list_goals
from app.services.llm_service import run_agent_llm, run_orchestrator_llm
from app.services.prediction_service import get_latest_prediction

SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2}


def _clamp_severity(value) -> str:
    return value if value in SEVERITY_RANK else "medium"


def _ordinal(n: int) -> str:
    suffix = "th" if 11 <= n % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _cash_flow_agent(context: dict) -> dict:
    runway = context["cash_runway"]
    if runway is None:
        return {
            "agent": "Cash Flow Agent", "severity": "low",
            "summary": "Not enough cash-flow history yet to assess runway.",
            "recommendation": "Process a few more months of data to unlock this.",
        }

    domain_data = {
        "current_cash": runway["current_cash"], "avg_monthly_burn": runway["avg_monthly_burn"],
        "runway_months": runway["runway_months"], "severity": runway["severity"],
    }
    llm_result = run_agent_llm("cash_flow", domain_data)
    if llm_result:
        return {"agent": "Cash Flow Agent", **llm_result}

    if runway["severity"] == "critical":
        return {
            "agent": "Cash Flow Agent", "severity": "high",
            "summary": f"Cash runway is critical at {runway['runway_months']} months (burn ${runway['avg_monthly_burn']:.0f}/mo).",
            "recommendation": "Cut discretionary spend immediately and pursue emergency financing or a cash injection.",
        }
    if runway["severity"] == "warning":
        return {
            "agent": "Cash Flow Agent", "severity": "medium",
            "summary": f"Cash runway is {runway['runway_months']} months — worth tightening before it becomes urgent.",
            "recommendation": "Reduce non-essential expenses this quarter to extend runway.",
        }
    return {
        "agent": "Cash Flow Agent", "severity": "low",
        "summary": "Cash position is stable or growing.",
        "recommendation": "No immediate action needed — consider building further reserves.",
    }


def _risk_agent(context: dict) -> dict:
    risks = context["risks"]
    high = [r for r in risks if r["severity"] == "high"]

    domain_data = {"risks": risks, "health_score": context["health_score"], "health_class": context["health_class"]}
    llm_result = run_agent_llm("risk", domain_data)
    if llm_result:
        return {"agent": "Risk Agent", **llm_result}

    if high:
        return {
            "agent": "Risk Agent", "severity": "high",
            "summary": f"{len(high)} high-severity risk(s) detected: " + "; ".join(r["type"] for r in high) + ".",
            "recommendation": f"Address {high[0]['type'].lower()} first — it's the most severe flag right now.",
        }
    if risks:
        return {
            "agent": "Risk Agent", "severity": "medium",
            "summary": f"{len(risks)} moderate risk(s) flagged: " + "; ".join(r["type"] for r in risks) + ".",
            "recommendation": "Monitor these — none are critical yet, but worth tracking monthly.",
        }
    return {"agent": "Risk Agent", "severity": "low", "summary": "No significant risks detected.", "recommendation": "Keep monitoring monthly."}


def _growth_agent(context: dict) -> dict:
    metrics = context["metrics"]
    benchmark = context["benchmark"]
    revenue_growth = metrics.get("revenue_growth_pct", 0) or 0

    percentile = None
    if benchmark:
        rg = benchmark["metrics"].get("revenue_growth_pct")
        percentile = rg["percentile"] if rg else None

    domain_data = {
        "revenue_growth_pct": revenue_growth,
        "customer_growth_rate": metrics.get("customer_growth_rate", 0),
        "industry_percentile": percentile,
    }
    llm_result = run_agent_llm("growth", domain_data)
    if llm_result:
        return {"agent": "Growth Agent", **llm_result}

    if revenue_growth < -5:
        severity, recommendation = "high", "Prioritize the revenue/marketing recommendations on your dashboard before anything else."
        summary = f"Revenue is declining {abs(revenue_growth):.1f}% month over month"
    elif revenue_growth < 0:
        severity, recommendation = "medium", "Watch next month closely — one more decline would be a trend, not a blip."
        summary = f"Revenue growth is slightly negative ({revenue_growth:.1f}%)"
    else:
        severity, recommendation = "low", "Keep doing what's working — consider reinvesting in growth."
        summary = f"Revenue is growing {revenue_growth:.1f}% month over month"
    summary += f", putting you in the {_ordinal(round(percentile))} percentile for your industry." if percentile is not None else "."

    return {"agent": "Growth Agent", "severity": severity, "summary": summary, "recommendation": recommendation}


def _goals_agent(context: dict) -> dict:
    goals = context["goals"]
    if not goals:
        return {
            "agent": "Goals Agent", "severity": "low", "summary": "No goals set yet.",
            "recommendation": "Set a target on the Goals page so progress can be tracked automatically.",
        }

    off_track = [g for g in goals if g["on_track"] is False and not g["achieved"]]
    domain_data = {
        "goals": [
            {"label": g["label"], "progress_pct": g["progress_pct"], "on_track": g["on_track"], "achieved": g["achieved"]}
            for g in goals
        ],
    }
    llm_result = run_agent_llm("goals", domain_data)
    if llm_result:
        return {"agent": "Goals Agent", **llm_result}

    if off_track:
        return {
            "agent": "Goals Agent",
            "severity": "high" if len(off_track) == len(goals) else "medium",
            "summary": f"{len(off_track)} of {len(goals)} goal(s) are off track: " + "; ".join(f'"{g["label"]}"' for g in off_track) + ".",
            "recommendation": f'Revisit "{off_track[0]["label"]}" — at the current trajectory it will miss its target date.',
        }
    return {"agent": "Goals Agent", "severity": "low", "summary": f"All {len(goals)} goal(s) are on track or achieved.", "recommendation": "Stay the course."}


AGENTS = [_cash_flow_agent, _risk_agent, _growth_agent, _goals_agent]


def run_briefing(db: Session, company: Company) -> dict:
    df = get_company_financial_dataframe(db, company.id)
    if df.empty:
        raise ValueError("No processed financial data available for this company yet")

    features = summarize_features(df)
    prediction = get_latest_prediction(db, company.id)

    try:
        cash_runway = get_cash_runway(db, company.id)
    except ValueError:
        cash_runway = None
    try:
        benchmark = get_benchmark(db, company)
    except ValueError:
        benchmark = None
    goals = list_goals(db, company.id)

    context = {
        "metrics": features,
        "health_score": float(prediction.health_score) if prediction else None,
        "health_class": prediction.health_class if prediction else None,
        "risks": prediction.risks if prediction else [],
        "cash_runway": cash_runway,
        "benchmark": benchmark,
        "goals": goals,
    }

    # Independent specialists, no shared state or ordering dependency — run them
    # concurrently so the briefing's latency is ~max(agent) rather than sum(agents).
    with ThreadPoolExecutor(max_workers=len(AGENTS)) as executor:
        findings = list(executor.map(lambda fn: fn(context), AGENTS))

    for f in findings:
        f["severity"] = _clamp_severity(f.get("severity"))

    worst_severity = max((f["severity"] for f in findings), key=lambda s: SEVERITY_RANK[s], default="low")
    overall_verdict = {"high": "Urgent", "medium": "Watch", "low": "Healthy"}[worst_severity]

    orchestrator_input = {
        "company": company.name,
        "overall_verdict": overall_verdict,
        "findings": [{"agent": f["agent"], "severity": f["severity"], "summary": f["summary"]} for f in findings],
    }
    executive_summary = run_orchestrator_llm(orchestrator_input)
    if not executive_summary:
        ranked = sorted(findings, key=lambda f: SEVERITY_RANK[f["severity"]], reverse=True)
        top = ranked[0]
        rest = " ".join(f"{f['agent']}: {f['summary']}" for f in ranked[1:])
        executive_summary = (
            f"Overall status: {overall_verdict}. The most pressing issue is from the {top['agent']}: "
            f"{top['summary']} {top['recommendation']} {rest}"
        )

    return {
        "overall_verdict": overall_verdict,
        "executive_summary": executive_summary,
        "findings": findings,
    }
