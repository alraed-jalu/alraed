import os
from datetime import datetime
from flask import Flask, jsonify, request
from supabase import create_client, Client

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route("/")
def home():
    return "alraed debug raw bills is live!", 200

@app.route("/send-report", methods=["POST"])
def send_report_manual():
    try:
        # جلب الحسابات
        acc_res = supabase.table("accounts").select("account_id, name").execute()
        accounts_map = {}
        if acc_res.data:
            for acc in acc_res.data:
                try:
                    accounts_map[int(acc.get("account_id"))] = str(acc.get("name", "")).strip()
                except:
                    pass

        # جلب كافة الفواتير
        bills_res = supabase.table("bills").select("*").execute()
        raw_bills = bills_res.data or []

        today_str = datetime.now().strftime("%Y-%m-%d")
        
        # تصفية فواتير اليوم وعرض تفاصيلها الخام لكي نراها بوضوح
        today_bills = []
        for row in raw_bills:
            b_date = str(row.get("bill_date", ""))
            if b_date.startswith(today_str):
                acc_id = row.get("account_id")
                acc_name = accounts_map.get(int(acc_id), "غير معروف") if acc_id is not None else "بدون حساب"
                row["account_resolved_name"] = acc_name
                today_bills.append(row)

        return jsonify({
            "status": "success",
            "today_date": today_str,
            "total_today_bills_found": len(today_bills),
            "today_bills_raw_data": today_bills,
            "accounts_mapping": accounts_map
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
