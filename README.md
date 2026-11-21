# PayGuard 360

> **Fraud-first financial safety platform for India — Hackathon Build Specification**
>
> *PayGuard 360 explains why a payment looks risky, pauses the dangerous ones for a human to review, and shows what it does to your budget, all before you press confirm.*

---

## ⚠️ Prototype & Safety Disclosures

> **DEMO MODE — NO REAL MONEY MOVES.**
>
> PayGuard 360 is an offline-capable, simulated decision-support prototype built using synthetic data.
> - **No real money moves, is blocked, or is recovered.**
> - **Zero Credentials:** PayGuard 360 will **never** ask for, accept, store, or log your PIN, OTP, CVV, or card password.
> - **Advisory Scores:** Risk scores (0–100) are deterministic rule-based advisory heuristics, not probabilities or legal proof of fraud.
> - **Human-in-the-Loop:** High-risk payments are held for human review with mandatory notes and separation of duties.

---

## 🚀 Quick Start (3 Commands)

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ & npm

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000 --reload
```
*API and Swagger Docs run at `http://localhost:8000/docs`.*

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
*Web application runs at `http://localhost:5173`.*

### 4. One-Command Demo Reset (< 0.5s)
```bash
python scripts/reset_demo.py
# or via REST:
curl -X POST http://localhost:8000/demo/reset
```

---

## 👥 Seeded Demo Accounts (Synthetic Test Data)

The login screen provides a **1-Click Demo Account Quick Picker**, and the top navigation bar includes an **Instant Role Switcher**. All demo accounts share the password: `password123`.

| Username | Role | Profile Type | Persona & Use Case | Initial Balance |
|---|---|---|---|---|
| `rahul_personal` | `customer` | `personal` | Salaried individual making daily UPI payments | ₹45,000.00 |
| `priya_personal` | `customer` | `personal` | Freelancer with diverse clients & held payments | ₹82,500.00 |
| `sharma_kirana` | `customer` | `merchant` | Small retail shopkeeper managing business cash flow | ₹1,20,000.00 |
| `ananya_reviewer` | `reviewer` | `internal` | Tier-1 Fraud Operations Reviewer | N/A (Staff) |
| `vikram_supervisor` | `supervisor` | `internal` | Compliance & Escalation Resolution Supervisor | N/A (Staff) |

---

## 🌟 Key Architecture & Differentiators

```
[ Customer Initiates Payment ]
              │
              ▼
    [ Credential Guard ] ────► Rejects PIN, OTP, CVV, Luhn-valid cards, malicious scripts
              │ (Valid)
              ▼
   [ Pure Risk Engine ] ────► Evaluates Rules R1–R10 (0–100 Advisory Score)
              │
      ┌───────┴────────────────────────┐
      ▼                                ▼
[ Low Risk: 0–39 ]            [ High Risk: 70–100 ]
Immediate Completion          Payment Placed in 'Held' Status
Funds Debit Instantly         Funds Reserved in Simulated Ledger
                              (Available Balance Drops, Completed Balance Unchanged)
                                       │
                                       ▼
                         [ Reviewer Console (Tier 1) ]
                         - Masked identities (CUST-xxxx, ••••yyyy)
                         - Mandatory review note (>= 5 chars)
                         - Approve / Reject / Escalate
                                       │ (If Escalated)
                                       ▼
                        [ Supervisor Console (Tier 2) ]
                        - Strict Two-Person Rule: Resolver != Escalator
                        - Final Resolution & Ledger Release
```

### 1. Explainable Pre-Payment Risk Assessment
- Pure deterministic engine evaluates 10 configurable rules (`R1`–`R10`), including amount deviations, velocity bursts, nighttime windows, new payees, collect requests, and watchlist presence.
- Output is structured as `code + params` JSON, translated into English or Hindi at render time.
- **What-If Breakdown:** Displays exactly how much the score would drop if specific risk factors (e.g., watchlist match or time window) were absent.

### 2. Ledger-Aware Simulated Holds
- High-risk payments enter `held` status and reserve funds in the simulated ledger.
- **The Balance Invariant:**
  $$\text{Available Balance} = \text{Baseline Available} - \text{Held Balance}$$
- Spending budgets reflect only completed transactions; held payments never distort expense tracking.
- Real-time **Live Reconciliation Panel** runs 4 automated balance invariant checks.

### 3. Human Review with Separation of Duties
- High-risk cases are assigned to a fraud queue with cryptographically masked customer references and payee VPAs.
- Reviewers must supply an explanatory note ($\ge 5$ characters) before approving, rejecting, or escalating.
- **Two-Person Rule:** A supervisor who resolves an escalated case cannot be the reviewer who escalated it.
- Append-only audit log protected by SQLite database triggers.

### 4. Smart Budgeting & Financial Awareness
- Category limits with automated 80% and 100% threshold warnings.
- Savings goals with earmark progress tracking.
- **Deterministic Scam-Message Checker:** Ephemeral heuristic scanner for suspicious payment requests with strict zero data retention.
- **Bilingual Support:** 100% key and parameter parity between English and Hindi (`हिंदी`).

---

## 🧪 Testing & Verification

### Run the Automated 18-Point Definition of Done Check
```bash
python scripts/demo_check.py
```
*Validates all 18 criteria (D1–D18) including health, auth rejection, lifecycle transitions, reviewer notes, IDOR boundaries, credential rejection, ledger reconciliation, and bilingual dictionaries in ~1.2s.*

### Run Backend Unit & Integration Tests (80 Tests)
```bash
cd backend
python -m pytest tests -v
```

### Run Frontend Tests (15 Tests)
```bash
cd frontend
npx vitest run
```

### Frontend Production Build
```bash
cd frontend
npm run build
```

---

## 📊 Point-in-Time Evaluation Results

Evaluated via `scripts/evaluate.py` across 300 holdout transactions (seed 1337) with synthetic fraud scenarios and hard negatives:

| Metric | Measured Value | Standard Required | Status |
|---|:---:|:---:|:---:|
| **Medium+ Risk Detection Recall** | **100.0%** | $\ge 85.0\%$ | **PASS** |
| **Medium+ Risk Precision** | **100.0%** | $\ge 80.0\%$ | **PASS** |
| **High-Risk False Hold Rate on Hard Negatives** | **0.0%** | $\le 5.0\%$ | **PASS** |
| **Average Rule Execution Latency** | **0.18 ms** | $< 50.0\text{ ms}$ | **PASS** |
| **Demo State Reset Time** | **0.28 s** | $< 5.0\text{ s}$ | **PASS** |

*Detailed evaluation methodology and confusion matrix are documented in [`docs/EVALUATION.md`](docs/EVALUATION.md).*

---

## 📚 Documentation Index

- [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) — 3-minute timed live demonstration script and operator cues.
- [`DEMO_READ_ALOUD.md`](DEMO_READ_ALOUD.md) — Exact presenter narration script (§26.2).
- [`JUDGE_DEMO_EVIDENCE.md`](JUDGE_DEMO_EVIDENCE.md) — Concrete inputs, live responses, and test transcripts (§26.5).
- [`docs/JUDGE_QA.md`](docs/JUDGE_QA.md) — In-depth answers to 18 judge questions covering architecture, accuracy, and compliance (§24).
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — Architectural overview, ledger equations, and state machine diagrams.
- [`docs/SECURITY.md`](docs/SECURITY.md) — Threat model (STRIDE), credential protection, zero-retention privacy, and gaming defense.
- [`docs/RULES.md`](docs/RULES.md) — Comprehensive specification of pure risk rules R1–R10.
- [`docs/VERIFICATION_MATRIX.md`](docs/VERIFICATION_MATRIX.md) — Full matrix tracking D1–D18 verification status.
- [`docs/DECISIONS.md`](docs/DECISIONS.md) — Architecture and design decision log (DEC-001 through DEC-009).
- [`docs/IMPLEMENTATION_LOG.md`](docs/IMPLEMENTATION_LOG.md) — Complete log of executed commands, phase gates, and outputs.

---

## ⚖️ License & Hackathon Notice

Developed for demonstration and hackathon evaluation. Built in accordance with Master Prompt v5.
