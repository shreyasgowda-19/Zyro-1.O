# PayGuard 360 — Verification Matrix

Status definitions: `VERIFIED` | `FAILED` | `BLOCKED` | `NOT IMPLEMENTED`  
*Rule:* A status of `VERIFIED` strictly requires backend + connected UI + persistence + authorization + passing automated tests + reproducible evidence.

---

| ID | Requirement (§21) | Status | Evidence / Test Name / Verification Steps |
|---|---|---|---|
| **D1** | Customer logs in with a seeded demo account. | NOT IMPLEMENTED | Pending Phase 1 |
| **D2** | A normal payment scores Low, completes, and shows "No risk signals found." | NOT IMPLEMENTED | Pending Phase 2a/2d |
| **D3** | A Medium payment shows at least two reasons and requires explicit confirmation. | NOT IMPLEMENTED | Pending Phase 2a/2d |
| **D4** | A High payment is held (funds reserved) and creates a review case. | NOT IMPLEMENTED | Pending Phase 2b/2d |
| **D5** | A reviewer approves, rejects or escalates with a mandatory note; a supervisor resolves an escalation. | NOT IMPLEMENTED | Pending Phase 2c/2d |
| **D6** | The customer sees the outcome and an alert; history shows the correct state. | NOT IMPLEMENTED | Pending Phase 2c/2d |
| **D7** | Held, escalated and rejected payments do not count as completed expenses. | NOT IMPLEMENTED | Pending Phase 2b/2d |
| **D8** | Ledger reconciliation passes and is shown in the UI. | NOT IMPLEMENTED | Pending Phase 2b/2d/3 |
| **D9** | The audit log records the actions with safe metadata. | NOT IMPLEMENTED | Pending Phase 2c/2d |
| **D10** | The budget summary uses real API data; 80% and 100% alerts fire with an explanation. | NOT IMPLEMENTED | Pending Phase 3 |
| **D11** | Changing language switches UI, risk reasons, alerts and guidance (standard/full). | NOT IMPLEMENTED | Pending Phase 4 |
| **D12** | A negative amount, script text and an OTP-style note are rejected with clear messages. | NOT IMPLEMENTED | Pending Phase 2b |
| **D13** | The guidance library, checklist and credential-safety notice are visible; no real credential can be entered. | NOT IMPLEMENTED | Pending Phase 4 |
| **D14** | The demo-mode banner is always visible; no screen claims real money moved, was blocked or recovered. | NOT IMPLEMENTED | Pending Phase 2d |
| **D15** | Core backend and frontend tests pass and are logged with real output. | NOT IMPLEMENTED | Continuous across phases |
| **D16** | The app works at a 360 px viewport. | NOT IMPLEMENTED | Pending Phase 4 |
| **D17** | `make reset` restores seeded demo state in under 5 seconds and the full demo path can run twice in a row. | NOT IMPLEMENTED | Pending Phase 1 / Phase 2d |
| **D18** | The score breakdown / what-if is shown for a High payment (standard/full). | NOT IMPLEMENTED | Pending Phase 4 |
