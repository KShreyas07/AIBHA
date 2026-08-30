# AIBHA

An AI-powered Business Health Analyzer for Small and Medium Businesses (SMEs). Upload financial
and operational data, and get a Business Health Score, ML-based classification, forecasts, risk
detection, industry benchmarking, and GPT-powered recommendations through an interactive dashboard.

## Architecture

```
frontend/   React 18 + Vite + Tailwind (dark SaaS UI) + Chart.js + Axios + React Router
backend/    FastAPI + SQLAlchemy + PostgreSQL, clean-architecture layout:
              app/api/v1     - route handlers
              app/services   - business logic / orchestration
              app/ml         - classification, forecasting, risk detection, health score
              app/models     - SQLAlchemy ORM models
              app/schemas    - Pydantic request/response schemas
              app/utils      - file parsing (CSV/Excel/PDF)
              alembic/       - database migrations
              tests/         - pytest suite
```

Pipeline: **Upload → Clean → Feature Engineering → Classification → Forecasting → Risk Detection
→ Health Score → LLM Recommendations → Dashboard**.

## Quick Start (Docker — recommended)

```bash
cp .env.example .env
# edit .env: set SECRET_KEY, and OPENAI_API_KEY if you want GPT-powered
# recommendations/chat (the app works without it via a rule-based fallback)

docker compose up --build
```

- Frontend: http://localhost:5173
- Backend API docs (Swagger): http://localhost:8000/docs
- Postgres: localhost:5432

The backend container runs `alembic upgrade head` automatically on startup.

## Local Development (without Docker)

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# point DATABASE_URL at a local Postgres instance, e.g.:
# DATABASE_URL=postgresql+psycopg2://bha_user:bha_password@localhost:5432/bha_db

alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

macOS note: XGBoost needs the OpenMP runtime — `brew install libomp` if you see a
`libomp.dylib` load error.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env   # VITE_API_BASE_URL=http://localhost:8000/api
npm run dev
```

Open http://localhost:5173.

### Running Tests

```bash
cd backend
source .venv/bin/activate
pytest
```

## Using the App

1. **Register** an account, then **create a company** (Companies page).
2. **Upload data** — CSV, Excel, or PDF — tagged with a category (income statement, balance
   sheet, cash flow, sales, expenses, inventory, or customer data). Files need a date/period
   column plus any of: `revenue, cogs, operating_expenses, net_profit, cash_balance,
   current_assets, current_liabilities, total_debt, total_equity, inventory_value,
   inventory_sold, customers_count`. Column names are matched against common synonyms
   automatically (see `backend/app/utils/file_parser.py`).
3. On the **Dashboard**, click **Run Full Analysis** to clean the data, engineer features,
   classify business health, detect risks, and generate recommendations.
4. Explore **Analytics** (ratios + industry benchmarking), **Forecast** (6/12-month revenue,
   profit, expense, and cash flow projections), **Recommendations**, and **Reports** (downloadable
   PDF).
5. Use the **chat bubble** (bottom-right) to ask questions about your data in plain English.

## AI Configuration

Recommendations and the chat assistant use the OpenAI API (`OPENAI_API_KEY` /
`OPENAI_MODEL` in `backend/.env`). Without a key, both automatically fall back to a
rule-based engine grounded in the same computed metrics, so the app is fully functional
out of the box.

## Key API Endpoints

All endpoints except `/auth/*` and `/health` require `Authorization: Bearer <token>`.

| Endpoint | Purpose |
|---|---|
| `POST /api/auth/register`, `/login`, `/logout`, `GET /me` | Auth |
| `GET/POST/PUT/DELETE /api/company[/{id}]` | Company CRUD |
| `POST /api/upload`, `GET /api/upload` | Upload + list files |
| `POST /api/analyze/{company_id}` | Re-run cleaning + feature engineering |
| `POST/GET /api/predict/{company_id}` | Health classification + risk detection |
| `POST /api/forecast/{company_id}?metric=&horizon_months=` | Forecasting |
| `GET /api/dashboard/{company_id}`, `/benchmark` | Dashboard + industry benchmarking |
| `POST/GET /api/recommendations/{company_id}` | AI recommendations |
| `POST /api/report/{company_id}`, `GET .../download` | PDF report |
| `POST /api/chat` | Chat assistant |

Full interactive docs at `/docs` (Swagger) once the backend is running.

## Notes on the ML Models

All three models below are validated against real data in `backend/research/` (not
synthetic benchmarks) — see `backend/research/DATASET.md` and
`backend/research/FORECAST_DATASET.md` for full methodology, metrics, and honestly-reported
limitations/caveats.

- **Classification** (Healthy/Warning/Critical): a LightGBM model trained on real company
  outcomes — the Taiwanese Bankruptcy Prediction dataset (UCI ML Repository 572,
  6,819 companies) — selected after comparing RandomForest, XGBoost, LightGBM, and
  CatBoost on that data (test ROC-AUC 0.878, PR-AUC 0.421). Predicted bankruptcy
  probability is mapped to Healthy/Warning/Critical via percentile thresholds
  calibrated against the model's own prediction distribution. See
  `backend/app/ml/classification.py`; retrain with
  `python3 -m app.ml.train_bankruptcy_classifier` (falls back to the original
  synthetic-data classifier if the trained artifact is missing, e.g. on a fresh clone
  before retraining).
- **Forecasting**: auto-selects between ARIMA, Prophet, and linear-regression trend by
  holding out the last few months of a company's own data and picking whichever model
  predicts it best (falls back straight to ARIMA — the strongest performer even on
  short histories — when there's not enough data to hold out a validation slice). This
  was chosen after a rolling-origin backtest against 6 real monthly business-revenue
  series showed ARIMA beating both Prophet and linear regression at every horizon
  tested (12-month MAPE: ARIMA 3.8% vs. Prophet 7.5% vs. Linear 7.7%). See
  `backend/app/ml/forecasting.py`.
- **Risk detection**: rule-based checks (revenue drop, high expenses, cash flow, inventory,
  debt) plus Isolation Forest outlier detection. See `backend/app/ml/risk_detection.py`.
- **Health Score**: weighted 0-100 rubric (Revenue Growth 20, Profit Margin 20, Cash Flow 20,
  Inventory 15, Debt 15, Customer Growth 10) — validated against real bankruptcy outcomes
  (ROC-AUC 0.812 as a risk predictor). See `backend/app/ml/health_score.py`.
