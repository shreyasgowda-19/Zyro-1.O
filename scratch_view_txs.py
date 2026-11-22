import sqlite3

conn = sqlite3.connect("backend/payguard.db")
cursor = conn.cursor()

txs = cursor.execute("SELECT id, user_id, type, source, amount_paise, category, payee_id, method, status, note, created_at FROM transactions").fetchall()
print(f"Total transactions: {len(txs)}")
for t in txs:
    print(t)

conn.close()
