import os
import requests
from flask import Flask, jsonify
from supabase import create_client, Client
import traceback

app = Flask(__name__)

# قراءة متغيرات البيئة
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
WASENDER_URL = os.environ.get("WASENDER_URL")
WASENDER_TOKEN = os.environ.get("WASENDER_TOKEN")
RECIPIENT_PHONE = os.environ.get("RECIPIENT_PHONE")

# تهيئة عميل Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route("/")
def home():
    return "alraed is live!", 200

@app.route("/send-report", methods=["POST"])
def send_report():
    try:
        # جلب فواتير أو بيانات اليوم من سوبابيس (تأكد من مطابقة اسم الجدول لديك)
        response = supabase.table("invoices").select("*").execute()
        data = response.data
        
        if not data:
            return jsonify({"status": "error", "message": "No data found in Supabase"}), 404

        accounts_totals = {}
        total_net = 0.0

        for row in data:
            net_val = float(row.get("Net", 0.0))
            acc_info = row.get("Accounts")
            acc_name = acc_info.get("Name", "غير معروف") if acc_info else "غير معروف"
            accounts_totals[acc_name] = accounts_totals.get(acc_name, 0.0) + net_val
            total_net += net_val

        report_lines = ["📊 تقرير المبيعات اليومي (Supabase):\n"]
        for acc_name, total_val in accounts_totals.items():
            report_lines.append(f"• {acc_name}: {total_val:,.2f} د.ل")
        
        report_lines.append(f"\n🏷 الإجمالي الصافي: {total_net:,.2f} د.ل")
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