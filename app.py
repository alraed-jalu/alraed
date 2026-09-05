import os
import requests
from flask import Flask, jsonify, request
from supabase import create_client, Client
import traceback
from datetime import datetime, timedelta

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
WASENDER_URL = os.environ.get("WASENDER_URL")
WASENDER_TOKEN = os.environ.get("WASENDER_TOKEN")
RECIPIENT_PHONE = os.environ.get("RECIPIENT_PHONE")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route("/")
def home():
    return "alraed is live with smart matching!", 200

@app.route("/send-report", methods=["POST"])
def send_report_manual():
    try:
        req_data = request.get_json(silent=True) or {}
        period = req_data.get("period", "يومي")
        
        today = datetime.now().date()
        if period == "اسبوعي":
            start_date = today - timedelta(days=7)
            title = "📊 تقرير المبيعات الأسبوعي:"
        elif period == "شهري":
            start_date = today.replace(day=1)
            title = "📊 تقرير المبيعات الشهري:"
        elif period == "سنوي":
            start_date = today.replace(month=1, day=1)
            title = "📊 تقرير المبيعات السنوي:"
        else:
            start_date = today
            title = "📊 تقرير المبيعات اليومي:"

        # 1. جلب الحسابات
        acc_res = supabase.table("accounts").select("account_id, name").execute()
        accounts_map = {}
        if acc_res.data:
            for acc in acc_res.data:
                try:
                    accounts_map[int(acc.get("account_id"))] = str(acc.get("name", "")).strip()
                except:
                    pass

        # 2. جلب الفواتير
        bills_res = supabase.table("bills").select("id, account_id, amount_afetr_dis1, operation_type, bill_date, deleted, removed").execute()
        raw_bills = bills_res.data or []

        allowed_accounts = ["زبون نقدي", "موبي كاش 1", "ادفع لي 2", "يسر باي 3", "بطاقة مصرفية 4"]
        accounts_totals = {acc: 0.0 for acc in allowed_accounts}
        total_net = 0.0

        for row in raw_bills:
            if row.get("deleted", 0) == 1 or row.get("removed", 0) == 1:
                continue

            b_date_str = row.get("bill_date")
            if b_date_str:
                try:
                    b_date = datetime.strptime(str(b_date_str).split("T")[0], "%Y-%m-%d").date()
                    if b_date < start_date:
                        continue
                except:
                    pass

            amt = float(row.get("amount_afetr_dis1", 0.0) or 0.0)
            op_type = row.get("operation_type", 0)
            acc_id = row.get("account_id")
            
            val = -abs(amt) if op_type == 12 else abs(amt)
            acc_name = accounts_map.get(int(acc_id), "") if acc_id else ""
            
            # مطابقة ذكية بالكلمات المفتاحية بغض النظر عن اختلاف التسمية حرفياً
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
                accounts_totals[target_key] += val
                total_net += val

        report_lines = [f"{title}\n"]
        for acc_name in allowed_accounts:
            val = accounts_totals[acc_name]
            report_lines.append(f"• {acc_name}: {val:,.2f} د.ل")
        
        report_lines.append(f"\n📌 الإجمالي الصافي: {total_net:,.2f} د.ل")
        report_message = "\n".join(report_lines)

        # إرسال عبر واتساب
        headers = {"Authorization": f"Bearer {WASENDER_TOKEN}", "Content-Type": "application/json"}
        payload = {"to": RECIPIENT_PHONE, "text": report_message}
        requests.post(WASENDER_URL, json=payload, headers=headers, timeout=15)

        return jsonify({"status": "success", "totals": accounts_totals, "net": total_net}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
