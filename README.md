# AI Trading Bot — Requirements (v0.2, Partially Agentic, Canada)

> **Status:** Draft 0.2 · **Owner:** Me · **Environment:** AWS (ca-central-1) · **Trading Mode:** Paper-only (no real capital)

---

## 1) Objectives & Scope

### 1.1 Goals
- G1: Run one or more algorithmic **paper** strategies with minute–daily cadences.
- G2: Provide **backtesting + forward-paper** evaluation with comparable metrics.
- G3: Add a **partially agentic layer** that can: (a) auto‑evaluate strategy variants, (b) recommend parameter changes, (c) trigger safe retrains **behind an approval gate**.
- G4: Ship a **React web app** for PnL, risk, positions, orders, and decision traces.
- G5: Deploy with **low ops** and **strong security** defaults on AWS Canada (ca-central-1).

### 1.2 Non‑Goals
- Live trading with real cash; sub‑second HFT; complex derivatives beyond future scope.

### 1.3 Suggested MVP Focus (asset classes & brokers)
- **Primary asset class (MVP): US equities & ETFs** (broad liquidity, low friction for paper).
- **Primary paper broker (MVP): Alpaca Paper** (simple REST/WS, global paper access, good docs).
- **Secondary (Phase 2): Forex via OANDA Practice** (broad FX pairs, easy paper environment).
- **Optional (Phase 2/3): Interactive Brokers (Paper)** for multi‑asset depth and eventual Canada listings.
- **Rationale:** Canadian equity market data/brokerage adds licensing and symbol‑format complexity up front. Starting with US equities enables faster iteration; add CAD/TSX later via IBKR once core is stable.

---

## 2) Data Residency (Canada) — What and Why
- **Target region:** AWS **ca-central-1 (Canada Central)** as the primary region for compute, storage, and logs.
- **Constraint meaning:** Keep **data at rest** in Canada (S3, RDS/DynamoDB, logs) and prefer **in‑region processing**. **Cross‑border transfers** (e.g., calling US‑hosted data APIs) may still occur for market data retrieval; assess policy needs.
- **This project’s default:** No PII and paper‑only orders. We still:
  - Store strategy artifacts, logs, metrics, and backtests in S3 (ca-central-1) with KMS.
  - Use VPC Endpoints for S3/Secrets; avoid unnecessary egress.
  - Document any external data providers’ regions and data flows.
- **If strict residency is required:** Use only providers offering Canadian endpoints or cache 3rd‑party data into S3 (ca-central-1) before use; block cross‑region writes.

---

## 3) Functional Requirements (FR)

### 3.1 Data & Features
- FR‑D1: Ingest historical OHLCV for US equities/ETFs; handle splits/dividends.
- FR‑D2: Live/pseudo‑live bars for minute & daily cadences (Alpaca/Polygon/Tiingo-compatible interfaces).
- FR‑D3: Feature pipeline with versioning (technical indicators, returns, volatility, regime features).
- FR‑D4: Universe selection (e.g., liquid US top‑N by ADV); monthly rebalance.
- FR‑D5: Corporate action adjustments for backtests and PnL realism.

### 3.2 Strategy & Modeling
- FR‑S1: Strategy interface: `generate_signals(features, state) -> orders`.
- FR‑S2: Support rule‑based + ML (classification/regression) strategies; ensemble optional.
- FR‑S3: Risk overlays: max weight/position, gross/net exposure caps, volatility targeting.
- FR‑S4: Position sizing: fixed fraction, volatility parity, capped‑Kelly.

### 3.3 Backtesting & Simulation
- FR‑B1: Event‑driven backtester with fills, slippage, fees, partials; walk‑forward evaluation.
- FR‑B2: Warm‑up period; reproducibility (seed, commit, data snapshot).
- FR‑B3: Portfolio accounting (cash, equity, realized/unrealized PnL, turnover).

### 3.4 Paper Execution & Broker Integration
- FR‑E1: **Alpaca Paper** adapter (MVP) with orders, positions, account, and market clock.
- FR‑E2: Order types: MKT, LMT, STP/STP‑LMT; TIF mapped per broker.
- FR‑E3: Throttle/retry policy; circuit breaker on repeated rejects/timeouts.
- FR‑E4: Trading calendars and sessions; holiday handling.
- FR‑E5: Extensible broker interface; add OANDA Practice & IBKR Paper in later phases.

### 3.5 Monitoring, Ops & UX
- FR‑O1: **React app**: equity curve, drawdown, Sharpe, exposures, open positions, order log.
- FR‑O2: Decision trace: last N orders with feature snapshot and (if ML) attribution.
- FR‑O3: Alerting: order rejects, stale data, abnormal PnL swings, connectivity loss.
- FR‑O4: Runbooks for common ops; parameter hot‑reload via UI/APIs (within safe bounds).
- FR‑O5: Read‑only viewer vs operator permissions.

### 3.6 Partially Agentic Layer
- FR‑A1: **Research Agent (offline/ops‑assisted):**
  - Proposes parameter grids/variants; launches backtests (Step Functions/ECS Batch).
  - Scores candidates with objective (e.g., Sharpe with drawdown penalty, turnover cap).
  - Produces a **recommendation** (not auto‑deploy) with diffs and expected deltas.
- FR‑A2: **Maintenance Agent:**
  - Watches feature/label drift and data freshness; flags retrain needs.
  - Runs **gated retraining**; pushes model artifact to registry after validation.
- FR‑A3: **Risk Watchdog:**
  - Enforces hard limits (max loss/day, max drawdown since midnight, max reject rate).
  - Can **auto‑de‑risk** (cut target exposure) but **cannot** deploy new models.
- FR‑A4: **Human‑in‑the‑loop approvals** for any strategy/model change in paper.

---

## 4) Non‑Functional Requirements (NFR)
- NFR‑1 Security: IAM least privilege; Secrets Manager; no plaintext keys; KMS‑encrypted S3/RDS/Dynamo.
- NFR‑2 Reliability: 99.5% monthly availability for paper loop; graceful degradation on data outage.
- NFR‑3 Performance: Signal→order under 2s for 1‑minute bars; backtest 10y daily/200 symbols <30 min on on‑demand.
- NFR‑4 Cost: Idle base ≤ **$50/mo** in ca-central-1 (excl. 3rd‑party data fees).
- NFR‑5 Observability: 100% key events logged; traces on critical paths; metrics at 1m granularity.
- NFR‑6 Portability: Identical Docker image runs local/ECS.
- NFR‑7 Compliance: Paper‑only; clear disclaimers; logs retained ≥ 13 months.
- NFR‑8 Residency: All at‑rest data/logs in **ca-central-1** by default.

---

## 5) AWS Architecture (Canada‑first)

**Compute**
- ECS on Fargate (long‑running strategy service), ECS Batch/Step Functions (backtests & agents), Lambda (low‑frequency jobs).

**Data & Storage**
- S3 (raw, processed, results) with KMS; optional Glue/Iceberg; DynamoDB (state/checkpoints); RDS Postgres for reporting (optional if Dynamo‑only suffices).

**Networking & Security**
- VPC with private subnets; VPC Endpoints for S3/Secrets; NAT for vetted egress; Security Groups locked down.

**Observability**
- CloudWatch logs/metrics/alarms, X‑Ray traces; metrics to Grafana/CloudWatch dashboards.

**API & UI**
- API Gateway + Lambda or ECS for control plane; static **React** app on S3 + CloudFront (origin in ca-central-1).

**High‑level Flow**
1) EventBridge triggers data jobs → S3. 2) Feature jobs → S3/Iceberg. 3) Strategy (ECS) consumes features → signals. 4) Broker adapter submits **paper** orders → states in Dynamo/RDS. 5) Metrics/audit → CloudWatch + S3. 6) Backtests/agents via Step Functions/ECS Batch.

---

## 6) React App (MVP)
- Tech: React + Vite, TypeScript, Tailwind, shadcn/ui, Recharts.
- Pages: Dashboard (PnL/equity/drawdown), Orders & Fills, Positions & Exposures, Strategy Runs, Agent Recommendations.
- Controls: Safe parameter sliders (caps), start/stop strategy, approve/reject agent proposals.
- Auth: Cognito (user pools) or AWS IAM Identity Center; role‑based access (viewer/operator).

---

## 7) Data Model (Essentials)
- Symbols(id, ticker, exchange, asset_class, currency, active_from, active_to)
- Bars(symbol_id, ts, o, h, l, c, v, provider)
- CorporateActions(symbol_id, ts, type, ratio, cash)
- Features(symbol_id, ts, vector_id, values, gen_version)
- Signals(strategy_id, ts, action, confidence, size, meta)
- Orders(id, ts, symbol_id, side, qty, type, tif, limit_price, stop_price, status)
- Fills(order_id, ts, price, qty, fee, slippage)
- Positions(symbol_id, qty, avg_price, unrealized_pnl)
- Runs(run_id, commit, data_snapshot, seed, params, metrics)
- Recommendations(id, created_ts, base_run_id, params_delta, backtest_metrics, status, approver)

---

## 8) Evaluation & Metrics
- Performance: CAGR, vol, Sharpe/Sortino, max DD, Calmar, win%, avg win/loss, turnover, capacity proxy.
- Risk: exposures by sector/asset, VAR (simple), single‑name cap.
- Ops: order reject rate, API error rate, data lag, end‑to‑end latency.
- Stats: time‑series CV; walk‑forward; bootstrap CIs on key metrics.

---

## 9) MLOps (Phase 2 optional)
- Experiment tracking (MLflow or SageMaker Experiments).
- Feature registry (Feast or S3+Glue catalog).
- Model registry (S3 + manifest); drift checks; shadow eval on paper before adopt.

---

## 10) Security & Compliance
- IAM roles per task; secrets in Secrets Manager; rotation ≥90 days.
- KMS encryption for S3/RDS/Dynamo; TLS everywhere.
- Residency guardrails: deny policies for cross‑region S3 buckets except allow‑listed.
- Vendor ToS compliance; log retention ≥13 months.

---

## 11) Testing Strategy
- Unit tests for indicators, fills, slippage, risk limits.
- Integration tests with mocked Alpaca; contract tests per adapter.
- Golden‑file backtests to detect drift; chaos tests (rate limits, network hiccups).

---

## 12) Deployment & IaC
- CI: GitHub Actions → build/scan Docker → ECR.
- IaC: Terraform or AWS CDK; PR‑reviewed; per‑env workspaces.
- Blue/green for strategy service; migrations via Flyway (if RDS).

---

## 13) MVP Slice (90/10)
- Alpaca Paper + US equities/ETFs; daily & 1‑minute bars.
- One rule‑based strategy (momentum or mean‑reversion) + simple risk caps.
- Backtest 10y daily, ~200 symbols.
- ECS Fargate (strategy) + S3 + DynamoDB + Secrets Manager + CloudWatch + EventBridge.
- React app (read‑only + operator approvals) deployed on S3/CloudFront.

---

## 14) Acceptance Criteria (MVP)
- AC‑1: End‑to‑end within 1 interval: data → signal → paper order → fill → PnL visible.
- AC‑2: Reproducible backtest (same commit/seed/data snapshot) within ±0.5% on key metrics.
- AC‑3: Strategy restarts without losing state; secrets never in plaintext.
- AC‑4: Idle monthly cost estimate ≤ $50 (excl. data/vendor fees).
- AC‑5: Agent recommendation appears in UI with diffs & metrics; requires manual approval before activation.

---

## 15) Risks & Mitigations
- Data/vendor lock‑in → abstract providers; add second adapter in Phase 2.
- Overfitting → walk‑forward; turnover/slippage penalties; bootstrap CIs.
- Paper/real gap → realistic slippage/latency models; conservative fills.
- Residency drift → SCPs/IAM guardrails; bucket‑policy denies for out‑of‑region.

---

## 16) Open Questions
- Pick market data vendor for US equities (API & licensing fit with residency posture)?
- Target universe definition (ADV cutoff, min price, exclude leveraged/inverse ETFs)?
- Preference: Terraform vs CDK? Cognito vs Identity Center for auth?
- Timeline for adding FX (OANDA) or IBKR Paper for TSX coverage?

