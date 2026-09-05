import os
from datetime import datetime
import requests
from flask import Flask, jsonify, request
from supabase import create_client, Client

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
WASENDER_URL = os.environ.get("WASENDER_URL")
WASENDER_TOKEN = os.environ.get("WASENDER_TOKEN")
RECIPIENT_PHONE = os.environ.get("RECIPIENT_PHONE")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route("/")
def home():
    return "alraed debug sync is live!", 200

@app.route("/send-report", methods=["POST"])
def send_report_manual():
    try:
        # 1. جلب الحسابات
        acc_res = supabase.table("accounts").select("account_id, name").execute()
        accounts_map = {}
        if acc_res.data:
            for acc in acc_res.data:
                try:
                    accounts_map[int(acc.get("account_id"))] = str(acc.get("name", "")).strip()
                except:
                    pass

        # 2. جلب كافة الفواتير
        bills_res = supabase.table("bills").select("*").execute()
        raw_bills = bills_res.data or []

        today_str = datetime.now().strftime("%Y-%m-%d")
        debug_matched_bills = []

        for row in raw_bills:
            if row.get("deleted", 0) == 1 or row.get("removed", 0) == 1:
                continue

            b_date = str(row.get("bill_date", ""))
            if not b_date.startswith(today_str):
                continue

            acc_id = row.get("account_id")
            acc_name = accounts_map.get(int(acc_id), "Unknown") if acc_id is not None else "Unknown"
            
            debug_matched_bills.append({
                "id": row.get("id"),
                "bill_date": b_date,
                "account_id": acc_id,
                "account_name": acc_name,
                "amount": row.get("amount_afetr_dis1"),
                "operation_type": row.get("operation_type")
            })

        return jsonify({
            "status": "success",
            "today_date": today_str,
            "matched_bills_found": debug_matched_bills
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
