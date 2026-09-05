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
    return "alraed separated report sync is live!", 200

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
        
        # هيكل لتخزين المبيعات والمرتجعات لكل حساب بشكل مستقل
        accounts_data = {acc: {"sales": 0.0, "returns": 0.0} for acc in allowed_accounts}
        
        total_sales = 0.0
        total_returns = 0.0
        processed_count = 0

        for row in raw_bills:
            if row.get("deleted", 0) == 1 or row.get("removed", 0) == 1:
                continue

            b_date = str(row.get("bill_date", ""))
            if not b_date.startswith(today_str):
                continue

            amt = float(row.get("amount_afetr_dis1", 0.0) or 0.0)
            op_type = row.get("operation_type", 1)
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

            if target_key and target_key in accounts_data:
                # التحقق هل هي عملية إرجاع (بناءً على operation_type أو القيمة السالبة)
                if op_type in [2, 12, "return"] or amt < 0:
                    accounts_data[target_key]["returns"] += abs(amt)
                    total_returns += abs(amt)
                else:
                    accounts_data[target_key]["sales"] += abs(amt)
                    total_sales += abs(amt)
                processed_count += 1

        # صياغة التقرير المفصل
        report_lines = [f"📊 تقرير المبيعات والمرتجعات اليومي ({today_str}):\n"]
        for acc_name in allowed_accounts:
            s = accounts_data[acc_name]["sales"]
            r = accounts_data[acc_name]["returns"]
            net = s - r
            report_lines.append(f"• {acc_name}:")
            report_lines.append(f"  - مبيعات: {s:,.2f}")
            report_lines.append(f"  - مرتجعات: {r:,.2f}")
            report_lines.append(f"  - الصافي: {net:,.2f} د.ل\n")
        
        total_net = total_sales - total_returns
        report_lines.append(f"📌 إجمالي المبيعات: {total_sales:,.2f} د.ل")
        report_lines.append(f"📌 إجمالي المرتجعات: {total_returns:,.2f} د.ل")
        report_lines.append(f"📌 الإجمالي الصافي العام: {total_net:,.2f} د.ل")
        
        report_message = "\n".join(report_lines)

        # 3. إرسال التقرير عبر Wasender إلى هاتفك
        headers = {"Authorization": f"Bearer {WASENDER_TOKEN}", "Content-Type": "application/json"}
        payload = {"to": RECIPIENT_PHONE, "text": report_message}
        requests.post(WASENDER_URL, json=payload, headers=headers, timeout=15)

        return jsonify({
            "status": "success",
            "date_filtered": today_str,
            "processed_bills_count": processed_count,
            "accounts_data": accounts_data,
            "total_sales": total_sales,
            "total_returns": total_returns,
            "total_net": total_net
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
