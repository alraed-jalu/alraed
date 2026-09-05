import os
import requests
from flask import Flask, jsonify
from supabase import create_client, Client
import traceback
from collections import defaultdict

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
WASENDER_URL = os.environ.get("WASENDER_URL")
WASENDER_TOKEN = os.environ.get("WASENDER_TOKEN")
RECIPIENT_PHONE = os.environ.get("RECIPIENT_PHONE")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route("/")
def home():
    return "alraed is live!", 200

@app.route("/send-report", methods=["POST"])
def send_report():
    try:
        response = supabase.table("bills").select("id, amount_afetr_dis1, operation_type, accounts(name)").eq("deleted", 0).eq("removed", 0).execute()
        data = response.data
        
        if not data:
            return jsonify({"status": "error", "message": "No data found in Supabase"}), 404

        # الحسابات المسموح بظهورها فقط
        allowed_accounts = ["زبون نقدي", "موبي كاش 1", "ادفع لي 2", "يسر باي 3", "بطاقة مصرفية 4"]
        accounts_totals = {acc: 0.0 for acc in allowed_accounts}
        total_net = 0.0

        for row in data:
            amt = float(row.get("amount_afetr_dis1", 0.0) or 0.0)
            op_type = row.get("operation_type", 0)
            
            if op_type == 12:
                val = -abs(amt)
            else:
                val = abs(amt)
                
            acc_info = row.get("accounts")
            acc_name = str(acc_info.get("name", "")).strip() if acc_info else ""
            
            # إذا كان الحساب من ضمن الحسابات المطلوبة فقط، نقوم بتجميعه وإضافته للإجمالي الصافي
            if acc_name in accounts_totals:
                accounts_totals[acc_name] += val
                total_net += val

        report_lines = ["📊 تقرير المبيعات اليومي:\n"]
        for acc_name in allowed_accounts:
            val = accounts_totals[acc_name]
            report_lines.append(f"• {acc_name}: {val:,.2f} د.ل")
        
        report_lines.append(f"\n📌 الإجمالي الصافي: {total_net:,.2f} د.ل")
        report_message = "\n".join(report_lines)

        headers = {
            "Authorization": f"Bearer {WASENDER_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "to": RECIPIENT_PHONE,
            "text": report_message
        }

        res = requests.post(WASENDER_URL, json=payload, headers=headers, timeout=15)
        if res.status_code in [200, 201]:
            return jsonify({"status": "success", "message": "Report sent successfully!"}), 200
        else:
            return jsonify({"status": "error", "details": res.text}), 400

    except Exception as e:
        print("ERROR DETECTED:\n", traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
