# PayGuard 360 — Demo Read-Aloud Lines (Exact Presenter Narration)

> **Purpose:** Natural, easy-to-speak presenter script paired with exact operator cues for a live 3-minute hackathon presentation (§22, §26.2).
> **Presenter Guidance:** Speak conversationally at a steady pace. Keep your eyes on the judges while the operator clicks the UI. Never cite numbers different from the live screen.

---

### Phase 1: Opening & Demo Boundary (0:00 – 0:20)

**[Operator Cue]:** *Display Customer Dashboard for `rahul_personal`. Mouse hovers briefly over top persistent banner: `DEMO MODE — NO REAL MONEY MOVES`.*

**Presenter (Read Aloud):**
> "A payment can look ordinary on the screen even when the request behind it is suspicious. In India, digital payments happen in seconds—and once money leaves an account, recovery is nearly impossible. People need more than a simple confirmation tick: they need to understand warning signs before they proceed.
>
> PayGuard 360 is a fraud-first financial safety platform that analyses simulated payments, explains why a request looks risky, pauses dangerous transactions for human review, and shows the balance impact before anyone presses confirm.
>
> As shown on screen, this is a controlled prototype using synthetic data. No bank, UPI network, or real money is connected. We are demonstrating the pre-payment decision-support workflow, not claiming to block a live payment."

---

### Phase 2: Normal Payment Flow (0:20 – 0:45)

**[Operator Cue]:** *Click **Pay / Send** in navbar. Select payee `Fresh Mart Groceries`, amount `500` (₹500), note `Weekly groceries`. Click **Assess Risk & Pay**.*

**Presenter (Read Aloud):**
> "First, let us look at a routine payment. Rahul is paying 500 rupees for weekly groceries to an established merchant during regular daytime hours.
>
> The system checks the request against configured, deterministic rules. Because no risk signals trigger, this transaction receives an advisory score of Zero—Low Risk—and completes immediately.
>
> Notice that the reasons are completely transparent: the user sees why the transaction cleared smoothly. PayGuard 360 does not introduce artificial friction into legitimate everyday commerce."

---

### Phase 3: High-Risk Attack Interception & Ledger-Aware Hold (0:45 – 1:30)

**[Operator Cue]:** *Click **Simulator** in navbar. Click **Preset F3: High Risk (Late-Night Flagged Payee)**. Form auto-fills ₹4,000 to flagged tele-services at 02:30 IST. Click **Assess Risk & Pay**.*

**Presenter (Read Aloud):**
> "Now, we will trigger a high-risk scenario typical of social engineering scams: a late-night transfer to an unverified tele-services account on a known watchlist.
>
> The engine evaluates the transaction instantly and assigns an advisory score of 75—High Risk. Rather than displaying an opaque warning code, PayGuard 360 explains each contributing signal: 40 points for the flagged watchlist, 25 points for unusual amount deviation, and 10 points for the high-risk nighttime window.
>
> Right below, our 'What would change this score' breakdown shows that removing the watchlist flag alone would drop the score to 35, bringing it into the Low band.
>
> Because this crosses the High-Risk threshold, the payment is held for review. Look at the ledger balances: Rahul's completed spending remains unchanged at 45,000 rupees, while 4,000 rupees is reserved in the held balance. His available balance safely drops to 41,000 rupees. Funds are accounted for without prematurely moving money."

---

### Phase 4: Human-in-the-Loop Review Console (1:30 – 2:10)

**[Operator Cue]:** *Use quick user switcher in navbar: select **Ananya (Reviewer)**. Click **Review** in navbar. Open the top held case. Type note: `"Suspicious tele-services payee. Escalating to supervisor for verified ID check."` Click **Escalate**. Switch user to **Vikram (Supervisor)**. Open escalated case. Type note: `"Customer confirmed legitimate utility clearance."` Click **Approve**.*

**Presenter (Read Aloud):**
> "Here is our human-in-the-loop workflow. Ananya, our fraud reviewer, opens her queue. Notice that customer and payee identities are cryptographically masked to protect privacy while preserving case context.
>
> Reviewers cannot simply press buttons: a descriptive note is mandatory before taking action. Ananya escalates this case for senior verification.
>
> Now Vikram, our supervisor, logs in. PayGuard 360 strictly enforces separation of duties: the person who escalated cannot resolve the escalation. Vikram reviews the risk factors and audit trail, enters his rationale, and approves the payment. Every transition is permanently recorded in an append-only audit log protected by database triggers."

---

### Phase 5: Financial Context, Bilingual Trust & Scam Checker (2:10 – 2:40)

**[Operator Cue]:** *Switch back to **Rahul (Personal Customer)**. View Dashboard with incoming approval alert. Highlight the **Live Ledger Reconciliation: 4/4 Checks Passed**. Click the **Language Toggle** in the navbar to switch to **हिंदी**. Click **Learn** (`/learn`) in navbar. Show scam message checker and official helplines (1930).*

**Presenter (Read Aloud):**
> "Back in Rahul's dashboard, he receives an immediate in-app alert explaining the supervisor's decision.
>
> Notice the live reconciliation panel: all four fundamental ledger checks pass in real time. Held amounts never distort completed expense budgets, and money is never lost in limbo.
>
> Furthermore, financial safety must be inclusive. With one click, the entire platform switches to Hindi—including dynamic alert descriptions and risk reasons.
>
> On our Learn page, users can paste suspicious WhatsApp messages into our deterministic scam checker. It scans for urgent demands and impersonation heuristics with strict zero retention—nothing is ever stored or transmitted to external servers. It also provides one-tap access to India's official 1930 cybercrime helpline."

---

### Phase 6: Conclusion & System Reset (2:40 – 3:00)

**[Operator Cue]:** *Click **Reset Demo** in the banner. Observe instant re-seed toast (< 0.5s).*

**Presenter (Read Aloud):**
> "Our core contribution is combining explainable pre-payment risk signals, human oversight with separation of duties, and ledger-aware holds.
>
> Watch this: with one click, our reset command wipes the database and re-seeds clean demo scenarios in under a second, making testing completely reproducible.
>
> PayGuard 360 is an explainable decision-support prototype. It demonstrates how intelligent safety rails can protect digital payments without compromising user autonomy. Thank you."
