import uuid
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from app.core.config import settings
from app.ml.feature_engineering import summarize_features
from app.models.company import Company
from app.models.forecast import Forecast
from app.models.recommendation import Recommendation
from app.models.report import Report
from app.services.data_processing_service import get_company_financial_dataframe
from app.services.prediction_service import get_latest_prediction


def generate_report(db: Session, company: Company) -> Report:
    df = get_company_financial_dataframe(db, company.id)
    if df.empty:
        raise ValueError("No processed financial data available for this company yet")

    features = summarize_features(df)
    prediction = get_latest_prediction(db, company.id)
    recommendations = (
        db.query(Recommendation).filter(Recommendation.company_id == company.id).order_by(Recommendation.priority).all()
    )
    forecasts = (
        db.query(Forecast).filter(Forecast.company_id == company.id, Forecast.metric == "revenue").order_by(Forecast.period).limit(6).all()
    )

    reports_dir = Path(settings.REPORTS_DIR) / str(company.id)
    reports_dir.mkdir(parents=True, exist_ok=True)
    file_path = reports_dir / f"report_{uuid.uuid4().hex}.pdf"

    doc = SimpleDocTemplate(str(file_path), pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"AI Business Health Report — {company.name}", styles["Title"]))
    story.append(Paragraph(f"Generated {datetime.utcnow().strftime('%Y-%m-%d')} · {company.industry} · {company.country}", styles["Normal"]))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Executive Summary", styles["Heading2"]))
    health_class = prediction.health_class if prediction else "N/A"
    health_score = float(prediction.health_score) if prediction else 0
    story.append(Paragraph(
        f"{company.name} is currently classified as <b>{health_class}</b> with a Business Health Score of "
        f"<b>{health_score}/100</b>. Latest monthly revenue is {features['revenue']:,.2f} with a profit margin of "
        f"{features['profit_margin_pct']:.1f}% and revenue growth of {features['revenue_growth_pct']:.1f}%.",
        styles["Normal"],
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Financial Summary", styles["Heading2"]))
    fin_table_data = [["Metric", "Value"]] + [
        [k.replace("_", " ").title(), f"{v:,.2f}"] for k, v in features.items()
    ]
    fin_table = Table(fin_table_data, colWidths=[8 * cm, 8 * cm])
    fin_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    story.append(fin_table)
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Health Score Breakdown", styles["Heading2"]))
    breakdown = (prediction.health_score_breakdown or {}).get("points", {}) if prediction else {}
    hs_table_data = [["Component", "Points"]] + [[k.replace("_", " ").title(), v] for k, v in breakdown.items()]
    hs_table = Table(hs_table_data, colWidths=[8 * cm, 8 * cm])
    hs_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(hs_table)
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Risk Analysis", styles["Heading2"]))
    risks = prediction.risks if prediction else []
    if risks:
        for r in risks:
            story.append(Paragraph(f"• <b>{r['type']}</b> ({r['severity']}): {r['description']}", styles["Normal"]))
    else:
        story.append(Paragraph("No significant risks detected.", styles["Normal"]))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Revenue Forecast (Next 6 Months)", styles["Heading2"]))
    if forecasts:
        fc_data = [["Period", "Predicted Revenue"]] + [
            [f.period.strftime("%Y-%m"), f"{float(f.predicted_value):,.2f}"] for f in forecasts
        ]
        fc_table = Table(fc_data, colWidths=[8 * cm, 8 * cm])
        fc_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(fc_table)
    else:
        story.append(Paragraph("No forecast generated yet.", styles["Normal"]))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("AI Recommendations", styles["Heading2"]))
    if recommendations:
        for rec in recommendations:
            story.append(Paragraph(f"• [{rec.priority.upper()}] {rec.text}", styles["Normal"]))
    else:
        story.append(Paragraph("No recommendations generated yet.", styles["Normal"]))

    doc.build(story)

    report = Report(company_id=company.id, file_path=str(file_path), report_type="full")
    db.add(report)
    db.commit()
    db.refresh(report)
    return report
