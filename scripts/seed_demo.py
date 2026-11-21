import os
import sys
import random
import json
from datetime import datetime, timezone, timedelta

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, backend_dir)

from app.database import SessionLocal, engine, create_append_only_triggers
from app.models.entities import (
    User, Account, Payee, Transaction, RiskAssessment, RiskReason,
    ReviewCase, ReviewCaseAction, AuditLog, Budget, SavingsGoal, Alert, GuidanceItem
)
from app.security.auth import hash_password, mask_payee_identifier, mask_customer_reference

def seed_database():
    random.seed(42)
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(User).count() > 0:
            print("Database already contains data. Skipping or re-seeding.")
            return

        print("Seeding demo accounts...")
        # 1. Create Users
        users_data = [
            # Personal Customers
            {"username": "rahul_personal", "role": "customer", "profile_type": "personal"},
            {"username": "priya_personal", "role": "customer", "profile_type": "personal"},
            # Business Customers
            {"username": "sharma_kirana", "role": "customer", "profile_type": "business"},
            {"username": "techcraft_solutions", "role": "customer", "profile_type": "business"},
            # Reviewer & Supervisor
            {"username": "ananya_reviewer", "role": "reviewer", "profile_type": None},
            {"username": "vikram_supervisor", "role": "supervisor", "profile_type": None},
        ]

        created_users = {}
        for u in users_data:
            user = User(
                username=u["username"],
                password_hash=hash_password("password123"),
                role=u["role"],
                profile_type=u["profile_type"],
                is_active=True
            )
            db.add(user)
            db.flush()
            created_users[u["username"]] = user

        # 2. Create Accounts (Opening Balances in paise)
        # rahul: ₹50,000 (5,000,000 paise)
        # priya: ₹75,000 (7,500,000 paise)
        # sharma_kirana: ₹2,00,000 (20,000,000 paise)
        # techcraft: ₹5,00,000 (50,000,000 paise)
        accounts_data = [
            (created_users["rahul_personal"].id, 5000000),
            (created_users["priya_personal"].id, 7500000),
            (created_users["sharma_kirana"].id, 20000000),
            (created_users["techcraft_solutions"].id, 50000000),
        ]
        for user_id, opening in accounts_data:
            db.add(Account(user_id=user_id, opening_balance_paise=opening))

        # 3. Create Payees
        rahul_id = created_users["rahul_personal"].id
        kirana_id = created_users["sharma_kirana"].id

        payees = [
            # Rahul's payees
            Payee(owner_user_id=rahul_id, display_name="Airtel Broadband", masked_identifier="••••8891", trust_status="known"),
            Payee(owner_user_id=rahul_id, display_name="Landlord Ramesh", masked_identifier="••••4412", trust_status="known"),
            Payee(owner_user_id=rahul_id, display_name="Fresh Mart Groceries", masked_identifier="••••1029", trust_status="known"),
            Payee(owner_user_id=rahul_id, display_name="Suspicious Tele-Services", masked_identifier="••••9941", trust_status="flagged"),
            Payee(owner_user_id=rahul_id, display_name="Apex Electrics", masked_identifier="••••3320", trust_status="new"),

            # Sharma Kirana's payees
            Payee(owner_user_id=kirana_id, display_name="Metro Cash & Carry", masked_identifier="••••5501", trust_status="known"),
            Payee(owner_user_id=kirana_id, display_name="Amul Wholesale Distributor", masked_identifier="••••2219", trust_status="known"),
            Payee(owner_user_id=kirana_id, display_name="Quick Logistics Co", masked_identifier="••••7732", trust_status="known"),
            Payee(owner_user_id=kirana_id, display_name="Shady Equipment Vendor", masked_identifier="••••6610", trust_status="flagged"),
        ]
        db.add_all(payees)
        db.flush()

        # 4. Generate 90 days of transaction history for rahul_personal
        now = datetime.now(timezone.utc)
        categories = ["Food & Dining", "Utilities", "Housing", "Groceries", "Shopping", "Entertainment"]
        
        # Monthly income transactions
        for months_ago in range(3, -1, -1):
            salary_date = now - timedelta(days=months_ago * 30 + 2)
            db.add(Transaction(
                user_id=rahul_id,
                type="income",
                source="manual",
                amount_paise=6500000,  # ₹65,000
                category="Salary",
                payee_id=None,
                method="netbanking",
                status="completed",
                note="Monthly Salary Credit",
                synthetic_device_tag="D1",
                synthetic_city_tag="Bengaluru",
                created_at=salary_date
            ))

        # 25 Completed Expenses over past 60 days
        for i in range(25):
            days_ago = random.randint(3, 60)
            tx_time = (now - timedelta(days=days_ago, hours=random.randint(10, 20))).replace(minute=random.randint(0, 59))
            amt_rupees = random.choice([250, 450, 800, 1200, 1500, 2200, 3100, 4500])
            db.add(Transaction(
                user_id=rahul_id,
                type="expense",
                source="payment",
                amount_paise=amt_rupees * 100,
                category=random.choice(categories),
                payee_id=payees[0].id if i % 2 == 0 else payees[2].id,
                method="upi",
                status="completed",
                note=f"Payment for supplies #{i+1}",
                synthetic_device_tag="D1",
                synthetic_city_tag="Bengaluru",
                created_at=tx_time
            ))

        db.flush()

        # 5. Create Pre-Created Review Cases for Reviewer Queue (P0 demo requirement)
        # Case 1: Held payment by Priya (High Risk)
        priya_id = created_users["priya_personal"].id
        flagged_payee_priya = Payee(
            owner_user_id=priya_id,
            display_name="Dubious Investment Scheme",
            masked_identifier="••••9191",
            trust_status="flagged"
        )
        db.add(flagged_payee_priya)
        db.flush()

        held_tx_1 = Transaction(
            user_id=priya_id,
            type="expense",
            source="payment",
            amount_paise=4500000,  # ₹45,000 (Drains balance + flagged payee + late night)
            category="Investment",
            payee_id=flagged_payee_priya.id,
            method="upi",
            status="held",
            note="Quick guaranteed return investment",
            synthetic_device_tag="D3",
            synthetic_city_tag="Mumbai",
            created_at=now - timedelta(hours=3, minutes=15)
        )
        db.add(held_tx_1)
        db.flush()

        # Risk assessment for held_tx_1 (Score: 70 - High)
        assessment_1 = RiskAssessment(
            transaction_id=held_tx_1.id,
            score=70,
            band="high",
            rules_version="1.0.0",
            features_json=json.dumps({"sample_size": 12, "velocity_count": 1}),
            created_at=held_tx_1.created_at
        )
        db.add(assessment_1)
        db.flush()

        db.add_all([
            RiskReason(assessment_id=assessment_1.id, rule_code="R6", points=40, params_json=json.dumps({"payee_masked": "••••9191"})),
            RiskReason(assessment_id=assessment_1.id, rule_code="R9", points=15, params_json=json.dumps({"amount_paise": 4500000, "available_paise": 5000000, "share_pct": 90})),
            RiskReason(assessment_id=assessment_1.id, rule_code="R8", points=15, params_json=json.dumps({"phrase_ids": ["guaranteed"]}))
        ])

        case_1 = ReviewCase(
            transaction_id=held_tx_1.id,
            case_type="hold_review",
            status="open",
            version=1,
            created_at=held_tx_1.created_at,
            updated_at=held_tx_1.created_at
        )
        db.add(case_1)

        # Case 2: Escalated Case (For Supervisor Resolution Demo)
        sharma_id = created_users["sharma_kirana"].id
        escalated_tx = Transaction(
            user_id=sharma_id,
            type="expense",
            source="payment",
            amount_paise=9800000,  # ₹98,000
            category="Inventory",
            payee_id=payees[8].id,
            method="upi",
            status="escalated",
            note="Bulk urgent stock clearance",
            synthetic_device_tag="D9",
            synthetic_city_tag="Delhi",
            created_at=now - timedelta(hours=6)
        )
        db.add(escalated_tx)
        db.flush()

        assessment_2 = RiskAssessment(
            transaction_id=escalated_tx.id,
            score=80,
            band="high",
            rules_version="1.0.0",
            features_json=json.dumps({"sample_size": 20}),
            created_at=escalated_tx.created_at
        )
        db.add(assessment_2)
        db.flush()

        db.add_all([
            RiskReason(assessment_id=assessment_2.id, rule_code="R6", points=40, params_json=json.dumps({"payee_masked": "••••6610"})),
            RiskReason(assessment_id=assessment_2.id, rule_code="R1", points=25, params_json=json.dumps({"amount_paise": 9800000, "avg_paise": 2000000, "sample_size": 20, "multiple_x10": 49})),
            RiskReason(assessment_id=assessment_2.id, rule_code="R8", points=15, params_json=json.dumps({"phrase_ids": ["urgent"]}))
        ])

        case_2 = ReviewCase(
            transaction_id=escalated_tx.id,
            case_type="hold_review",
            status="escalated",
            version=2,
            assigned_reviewer_id=created_users["ananya_reviewer"].id,
            created_at=escalated_tx.created_at,
            updated_at=now - timedelta(hours=1)
        )
        db.add(case_2)
        db.flush()

        # Initial action by Reviewer that escalated the case
        action_escalate = ReviewCaseAction(
            case_id=case_2.id,
            actor_id=created_users["ananya_reviewer"].id,
            action="escalate",
            note="Unusually high value supplier transaction to flagged entity; requires supervisor authorization.",
            created_at=now - timedelta(hours=1)
        )
        db.add(action_escalate)

        # 6. Create Monthly Budgets for Rahul (Current Month)
        current_period = now.strftime("%Y-%m")
        db.add_all([
            Budget(user_id=rahul_id, category=None, amount_paise=4000000, period=current_period),  # Overall: ₹40,000
            Budget(user_id=rahul_id, category="Food & Dining", amount_paise=1000000, period=current_period),  # ₹10,000
            Budget(user_id=rahul_id, category="Groceries", amount_paise=1200000, period=current_period),  # ₹12,000
            Budget(user_id=rahul_id, category="Utilities", amount_paise=800000, period=current_period),  # ₹8,000
        ])

        # 7. Create Savings Goals
        db.add_all([
            SavingsGoal(user_id=rahul_id, title="Emergency Fund", target_paise=15000000, current_paise=8000000, target_date="2026-12-31"),
            SavingsGoal(user_id=rahul_id, title="Laptop Replacement", target_paise=8000000, current_paise=3500000, target_date="2026-09-30"),
        ])

        # 8. Create In-App Alerts
        db.add_all([
            Alert(
                user_id=rahul_id,
                type="fraud",
                title_code="alert.fraud.held_notice",
                params_json=json.dumps({"amount_paise": 4500000, "status": "held"}),
                related_transaction_id=None,
                dedupe_key=f"fraud_held_welcome_{rahul_id}",
                created_at=now - timedelta(days=1)
            ),
            Alert(
                user_id=rahul_id,
                type="budget",
                title_code="alert.budget.approaching_limit",
                params_json=json.dumps({"category": "Food & Dining", "pct": 82, "budget_paise": 1000000}),
                related_transaction_id=None,
                dedupe_key=f"budget_80_{current_period}_Food_Dining",
                created_at=now - timedelta(hours=12)
            ),
        ])

        # 9. Create Static Verified Guidance Items (§14)
        guidance_items = [
            GuidanceItem(
                topic="helpline",
                language="en",
                title="National Cyber Crime Helpline (1930)",
                body="If you have fallen victim to financial fraud, immediately call 1930 or file a report at cybercrime.gov.in. Notify your bank within 24 hours to block unauthorized accounts.",
                source_label="Ministry of Home Affairs, Government of India",
                source_url="https://cybercrime.gov.in",
                last_verified="2026-01-15"
            ),
            GuidanceItem(
                topic="helpline",
                language="hi",
                title="राष्ट्रीय साइबर अपराध हेल्पलाइन (1930)",
                body="यदि आप वित्तीय धोखाधड़ी के शिकार हुए हैं, तो तुरंत 1930 पर कॉल करें या cybercrime.gov.in पर रिपोर्ट दर्ज करें। अनधिकृत खातों को ब्लॉक करने के लिए 24 घंटे के भीतर अपने बैंक को सूचित करें।",
                source_label="गृह मंत्रालय, भारत सरकार",
                source_url="https://cybercrime.gov.in",
                last_verified="2026-01-15"
            ),
            GuidanceItem(
                topic="sanchar_saathi",
                language="en",
                title="Report Suspicious Calls & WhatsApp Messages",
                body="Report fraud calls, unsolicited payment links, and fake KYC requests via the government's Chakshu portal on Sanchar Saathi.",
                source_label="Department of Telecommunications (DoT)",
                source_url="https://sancharsaathi.gov.in",
                last_verified="2026-02-01"
            ),
            GuidanceItem(
                topic="sanchar_saathi",
                language="hi",
                title="संदिग्ध कॉल और संदेशों की रिपोर्ट करें (संचार साथी)",
                body="संचार साथी पर चक्षु पोर्टल के माध्यम से धोखाधड़ी कॉल, अज्ञात भुगतान लिंक और फर्जी केवाईसी अनुरोधों की रिपोर्ट करें।",
                source_label="दूरसंचार विभाग (DoT)",
                source_url="https://sancharsaathi.gov.in",
                last_verified="2026-02-01"
            ),
            GuidanceItem(
                topic="qr_code_scams",
                language="en",
                title="QR Code & Collect-Request Scams",
                body="Remember: Scanning a QR code or entering your PIN is ONLY for SENDING money, NEVER for receiving money. Any request to approve a collect request to get a refund or lottery prize is a scam.",
                source_label="Reserve Bank of India (RBI) Financial Education",
                source_url="https://rbi.org.in",
                last_verified="2026-01-10"
            ),
            GuidanceItem(
                topic="qr_code_scams",
                language="hi",
                title="क्यूआर कोड और कलेक्ट-अनुरोध धोखाधड़ी",
                body="याद रखें: क्यूआर कोड स्कैन करना या अपना पिन दर्ज करना केवल पैसे भेजने के लिए होता है, पैसे प्राप्त करने के लिए कभी नहीं। रिफंड या लॉटरी पाने के लिए कलेक्ट रिक्वेस्ट को स्वीकृत करने का कोई भी अनुरोध धोखाधड़ी है।",
                source_label="भारतीय रिज़र्व बैंक (RBI) वित्तीय शिक्षा",
                source_url="https://rbi.org.in",
                last_verified="2026-01-10"
            ),
        ]
        db.add_all(guidance_items)

        # 10. Audit Log Initial Entries
        audit_entry = AuditLog(
            actor_id=created_users["ananya_reviewer"].id,
            entity_type="ReviewCase",
            entity_id=case_2.id,
            action="case_escalated",
            safe_metadata_json=json.dumps({"action": "escalate", "status": "escalated"}),
            created_at=now - timedelta(hours=1)
        )
        db.add(audit_entry)

        db.commit()
        print("Demo database seeded successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
