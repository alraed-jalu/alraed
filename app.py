import os
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
    return "alraed schema inspection is live!", 200

@app.route("/send-report", methods=["POST"])
def send_report_manual():
    try:
        # جلب أول فاتورة لعرض كافة الأعمدة والأسماء الموجودة فيها لمعرفة حقل نوع الفاتورة
        bills_res = supabase.table("bills").select("*").limit(3).execute()
        sample_bills = bills_res.data or []

        # جلب الحسابات
        acc_res = supabase.table("accounts").select("account_id, name").execute()
        accounts_map = {}
        if acc_res.data:
            for acc in acc_res.data:
                try:
                    accounts_map[int(acc.get("account_id"))] = str(acc.get("name", "")).strip()
                except:
                    pass

        allowed_accounts = ["زبون نقدي", "موبي كاش 1", "ادفع لي 2", "يسر باي 3", "بطاقة مصرفية 4"]
        accounts_totals = {acc: 0.0 for acc in allowed_accounts}
        total_net = 0.0
        details = []

        for row in sample_bills:
            details.append(row)
            amt = float(row.get("amount_afetr_dis1", 0.0) or 0.0)
            acc_id = row.get("account_id")
            acc_name = accounts_map.get(int(acc_id), "") if acc_id else ""
            
            # مطابقة ذكية
            target_key = None
            acc_lower = acc_name.lower()
            if "نقدي" in acc_lower or "صندوق" in acc_lower:
                target_key = "زبون نقدي"
            elif "موبي" in acc_lower:
                target_key = "موبي كاش 1"
            elif "ادفع" in acc_lower:
                target_key = "ادفع لي 2"
            elif "يسر" in acc_lower:
                target_key = "يسر باي 3"
            elif "بطاقة" in acc_lower or "مصرفية" in acc_lower:
                target_key = "بطاقة مصرفية 4"

            if target_key and target_key in accounts_totals:
                accounts_totals[target_key] += amt
                total_net += amt

        # إرسال تقرير تجريبي بسيط وتخطي الأخطاء
        return jsonify({
            "status": "success",
            "sample_bill_keys": list(sample_bills[0].keys()) if sample_bills else [],
            "sample_rows": sample_bills,
            "calculated_totals": accounts_totals
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
