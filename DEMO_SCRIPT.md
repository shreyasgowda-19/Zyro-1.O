# PayGuard 360 — 3-Minute Live Demo Script (DEMO_SCRIPT.md)

> **Preparation before taking the stage:**
> 1. Run `python -m pytest tests -v` (verify 80/80 backend tests pass).
> 2. Run `npm run build` in `frontend` (verify clean build).
> 3. Click **Reset Demo** in the banner or run `python -c "import requests; requests.post('http://localhost:8000/demo/reset')"` (< 0.5s).
> 4. Ensure backend is running (`uvicorn app.main:app --port 8000`) and frontend is running (`npm run dev`).

---

### Timeline Overview (3:00 Minutes Total)

| Timestamp | Phase | Role / Persona | Screen / Action | Primary Talking Point |
|---|---|---|---|---|
| **0:00–0:20** | Problem & Vision | Presenter | Home / Dashboard (`rahul_personal`) | IRREVERSIBLE UPI SCAMS & EXPLAINABLE SAFETY |
| **0:20–0:55** | Low-Risk Flow | Customer (`rahul_personal`) | Pay screen (`/pay`) → Groceries payment | IMMEDIATE COMPLETION & 0 FALSE FRICTION |
| **0:55–1:35** | High-Risk WOW Moment | Customer (`rahul_personal`) | Simulator Preset F3 → Payment Result | EXPLAINABLE REASONS & LEDGER-AWARE HOLD |
| **1:35–2:15** | Human Review Workflow | Reviewer (`ananya_reviewer`) | Review Queue (`/review`) → Case Inspector | SEPARATION OF DUTIES & MANDATORY NOTES |
| **2:15–2:45** | Budgeting & Bilingual Trust | Customer (`rahul_personal`) | Dashboard & Learn → Hindi Toggle | RECONCILIATION 4/4 & SCAM CHECKER |
| **2:45–3:00** | Close & Prototype Boundaries | Presenter | Global View | SYNTHETIC BOUNDARIES & PRODUCTION PATHWAY |

---

### Step-by-Step Operator Guide

#### Step 1: Problem & Product Vision (0:00–0:20)
* **Action:** Display Customer Dashboard for Rahul (`rahul_personal`). Point out the persistent demo banner: `DEMO MODE — NO REAL MONEY MOVES`.
* **Presenter:** "Digital payments in India happen in seconds. When someone is pressured by an electricity scam or fake lottery, generic warnings get ignored. PayGuard 360 is a fraud-first financial safety platform: it explains why a payment looks risky, holds the dangerous ones for human review, and shows the impact on your balance before money moves."

#### Step 2: Low-Risk Payment Execution (0:20–0:55)
* **Action:** Click **Pay / Send** in navbar. Select payee `Fresh Mart Groceries`, amount `500` (₹500), note `Weekly groceries`. Click **Assess Risk & Pay**.
* **Result Screen:** Risk score **0 (Low)**. Status: **Completed**. Notice: *"No risk signals found."*
* **Presenter:** "A normal payment to a known merchant during daytime scores Low and completes immediately. Notice there is zero unnecessary friction or false alarms for legitimate daily transactions."

#### Step 3: High-Risk Attack Interception & WOW Moment (0:55–1:35)
* **Action:** Click **Simulator** in top navbar. Click **High Risk (F3: Late-Night Flagged Payee)**. The payment form pre-fills with ₹4,000 to flagged tele-services at 02:30 IST. Click **Assess Risk & Pay**.
* **Result Screen:** Risk score **75 (High)**.
  - Three explainable reasons: Flagged Watchlist (R6: 40 pts), Unusual Amount (R1: 25 pts), Night Window (R3: 10 pts).
  - Score Breakdown Panel: *"Without this signal, your score would be 35 (Low risk)"*.
  - Status: **Payment Paused for Review (Held)**.
* **Return to Dashboard:** Highlight the split balances:
  - **Completed balance:** ₹45,000 (unchanged!)
  - **Held balance:** ₹4,000 (reserved!)
  - **Available balance:** drops to ₹41,000!
* **Presenter:** "This is our key differentiator: the payment is paused, the customer sees the exact contributing factors, and funds are safely reserved in the ledger without moving real money."

#### Step 4: Human-in-the-Loop Review Console (1:35–2:15)
* **Action:** Use the Quick Switcher dropdown in the navbar to switch to **Ananya (Reviewer)**.
* **Screen:** Open Review Queue. Click on the held case.
* **Modal:** Show case details, masked customer reference, masked payee (`••••9941`), risk reasons, and transaction history.
* **Action:** Type note: *"Suspicious tele-services payee. Escalating to supervisor for verified ID check."* Click **Escalate**.
* **Supervisor Action:** Switch account to **Vikram (Supervisor)**. Open escalated case. Review note. Enter supervisor rationale: *"Customer confirmed legitimate utility clearance."* Click **Approve**.
* **Presenter:** "High-risk cases require a human decision with mandatory notes and separation of duties: the reviewer escalated, and only a supervisor could resolve it. Compliance events are permanently logged in the append-only audit trail."

#### Step 5: Budgeting, Reconciliation & Hindi Switch (2:15–2:45)
* **Action:** Switch back to **Rahul (Personal Customer)**.
* **Dashboard:** Show incoming approval notification alert. Highlight the live **Ledger Reconciliation: 4/4 Checks Passed**.
* **Bilingual Switch:** Click the **Language button** in the navbar to switch to **हिंदी**.
* **Result:** All navigation links, alert notifications, and risk reason strings switch seamlessly to Hindi.
* **Learn Page:** Open `/learn`. Show the **Deterministic Scam-Message Checker** with zero retention, and the verified helplines (**1930** and **cybercrime.gov.in**).
* **Presenter:** "Completed payments flow into smart budgeting, while held payments never distort expenses. Our live ledger reconciliation confirms accounting integrity, and bilingual localization ensures financial safety reaches every Indian user."

#### Step 6: Close & Prototype Boundaries (2:45–3:00)
* **Action:** Show the **Reset Demo** button restoring the entire database in 0.28 seconds.
* **Presenter:** "PayGuard 360 proves that explainable risk signals, human oversight, and ledger integrity can make digital payments fundamentally safer. This is a prototype built on synthetic data, ready for evaluation."
