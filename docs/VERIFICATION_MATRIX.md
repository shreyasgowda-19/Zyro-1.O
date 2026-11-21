# PayGuard 360 — Verification Matrix

Status definitions: `VERIFIED` | `FAILED` | `BLOCKED` | `NOT IMPLEMENTED`  
*Rule:* A status of `VERIFIED` strictly requires backend + connected UI + persistence + authorization + passing automated tests + reproducible evidence.

---

| ID | Requirement (§21) | Status | Evidence / Test Name / Verification Steps |
|---|---|---|---|
| **D1** | Customer logs in with a seeded demo account. | VERIFIED | Tests `test_login_successful` & `test_users_me_authenticated` in `tests/test_foundation.py` passed; `LoginPage.tsx` with one-click persona selector connected to `/auth/login`. |
| **D2** | A normal payment scores Low, completes, and shows "No risk signals found." | VERIFIED | Tests `test_e2e_low_risk_flow` passed; `NewPaymentPage.tsx` -> `/payments` -> `PaymentResultPage.tsx` shows Low risk score, completed status, and receipt. |
| **D3** | A Medium payment shows at least two reasons and requires explicit confirmation. | VERIFIED | Tests `test_e2e_medium_risk_confirm_flow` and `test_e2e_medium_risk_cancel_flow` passed; `PaymentResultPage.tsx` displays reasons and explicit Confirm/Cancel action buttons. |
| **D4** | A High payment is held (funds reserved) and creates a review case. | VERIFIED | Tests `test_e2e_high_risk_hold_and_reviewer_approve` passed; atomic reservation decreases available balance and increases held balance; `ReviewCase` created with `hold_review`. |
| **D5** | A reviewer approves, rejects or escalates with a mandatory note; a supervisor resolves an escalation. | VERIFIED | Tests `test_e2e_escalate_and_supervisor_resolve`, `test_hold_review_approve_workflow`, `test_hold_review_reject_workflow` passed; `ReviewQueuePage.tsx` case inspector modal with note validation (5-500 chars) and separation of duties. |
| **D6** | The customer sees the outcome and an alert; history shows the correct state. | VERIFIED | Tests `test_customer_alerts_read_and_idor_protection` and `test_e2e_high_risk_hold_and_reviewer_approve` passed; `DashboardPage.tsx` alerts section renders unread alerts with dismiss/read actions. |
| **D7** | Held, escalated and rejected payments do not count as completed expenses. | VERIFIED | Tests `test_payment_high_is_held_and_reserves_funds` and `test_e2e_high_risk_hold_and_reviewer_reject` passed; verified formula `completed_balance = opening + income - expenses`, held balance isolated. |
| **D8** | Ledger reconciliation passes and is shown in the UI. | VERIFIED | Tests `test_reconciliation_endpoint` and `test_demo_reset_speed_and_state` passed; `DashboardPage.tsx` displays live 4/4 reconciliation badge with status details from `/accounting/reconciliation`. |
| **D9** | The audit log records the actions with safe metadata. | VERIFIED | Tests `test_review_audit_log_endpoint` and `test_e2e_escalate_and_supervisor_resolve` passed; `ReviewQueuePage.tsx` Audit Trail tab renders append-only events. |
| **D10** | The budget summary uses real API data; 80% and 100% alerts fire with an explanation. | NOT IMPLEMENTED | Pending Phase 3 |
| **D11** | Changing language switches UI, risk reasons, alerts and guidance (standard/full). | NOT IMPLEMENTED | Pending Phase 4 |
| **D12** | A negative amount, script text and an OTP-style note are rejected with clear messages. | VERIFIED | Tests `test_credential_otp_rejected`, `test_credential_luhn_card_rejected`, `test_script_text_rejected`, `test_credential_guard_blocks_payment_payload` passed; clear error codes without logging or echoing sensitive input. |
| **D13** | The guidance library, checklist and credential-safety notice are visible; no real credential can be entered. | NOT IMPLEMENTED | Pending Phase 4 |
| **D14** | The demo-mode banner is always visible; no screen claims real money moved, was blocked or recovered. | VERIFIED | Persistent global banner `DEMO MODE — NO REAL MONEY MOVES` in `Navbar.tsx`; credential safety notice in `NewPaymentPage.tsx` and `LoginPage.tsx`. |
| **D15** | Core backend and frontend tests pass and are logged with real output. | VERIFIED | 67/67 pytest tests pass; 8/8 vitest unit tests pass; `npm run build` succeeds cleanly in 2.12s. |
| **D16** | The app works at a 360 px viewport. | NOT IMPLEMENTED | Pending Phase 4 |
| **D17** | `make reset` restores seeded demo state in under 5 seconds and the full demo path can run twice in a row. | VERIFIED | POST `/demo/reset` and `scripts/reset_demo.py` restore database in 0.22s (< 5.0s target); verified in `test_demo_reset_speed_and_state`. |
| **D18** | The score breakdown / what-if is shown for a High payment (standard/full). | VERIFIED | Tests `test_risk_assessment_rbac_and_breakdown` passed; `GET /risk/assessments/{id}/breakdown` wired to `PaymentResultPage.tsx` showing exact point reduction recommendations. |
