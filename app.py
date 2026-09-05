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
    return "alraed exact match report sync is live!", 200

@app.route("/send-report", methods=["POST"])
def send_report_manual():
    try:
        # 1. جلب الحسابات لتكوين قاموس الربط
        acc_res = supabase.table("accounts").select("account_id, name").execute()
        accounts_map = {}
        if acc_res.data:
            for acc in acc_res.data:
                try:
                    acc_id = int(acc.get("account_id"))
                    acc_name = str(acc.get("name", "")).strip()
                    accounts_map[acc_id] = acc_name
                except:
                    pass

        # 2. جلب الفواتير
        bills_res = supabase.table("bills").select("id, account_id, amount_afetr_dis1, operation_type, deleted, removed, bill_date").execute()
        raw_bills = bills_res.data or []

        today_str = datetime.now().strftime("%Y-%m-%d")

        allowed_accounts = ["زبون نقدي", "موبي كاش 1", "ادفع لي 2", "يسر باي 3", "بطاقة مصرفية 4"]
        accounts_totals = {acc: 0.0 for acc in allowed_accounts}
        total_net = 0.0
        processed_count = 0

        for row in raw_bills:
            if row.get("deleted", 0) == 1 or row.get("removed", 0) == 1:
                continue

            b_date = str(row.get("bill_date", ""))
            if not b_date.startswith(today_str):
                continue

            # قراءة القيمة الحقيقية كما هي مخزنة في الحقل (سواء موجبة أو سالبة تماماً مثل المنظومة)
            amt = float(row.get("amount_afetr_dis1", 0.0) or 0.0)
            
            acc_id = row.get("account_id")
            acc_name = accounts_map.get(int(acc_id), "") if acc_id is not None else ""
            
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
                processed_count += 1

        report_lines = [f"📊 تقرير المبيعات اليومي ({today_str}):\n"]
        for acc_name in allowed_accounts:
            val = accounts_totals[acc_name]
            report_lines.append(f"• {acc_name}: {val:,.2f} د.ل")
        
        report_lines.append(f"\n📌 الإجمالي الصافي: {total_net:,.2f} د.ل")
        report_message = "\n".join(report_lines)

        # 3. إرسال التقرير عبر Wasender
        headers = {"Authorization": f"Bearer {WASENDER_TOKEN}", "Content-Type": "application/json"}
        payload = {"to": RECIPIENT_PHONE, "text": report_message}
        requests.post(WASENDER_URL, json=payload, headers=headers, timeout=15)

        return jsonify({
            "status": "success",
            "processed_bills_count": processed_count,
            "calculated_totals": accounts_totals,
            "total_net": total_net
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
