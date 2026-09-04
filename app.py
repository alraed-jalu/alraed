import os
import datetime
import requests
from flask import Flask, request, jsonify
from supabase import create_client, Client

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

WASENDER_URL = "https://wasenderapi.com/api/send-message"
WASENDER_TOKEN = "d0edd417e1b9e2c1a47f8e43cdb98c0be2a0f113a8060f00cb34abd5132c181c"
RECIPIENT_PHONE = "218911143064"

@app.route("/", methods=["GET"])
def home():
    return "Alraed Reports Bot is Running Successfully on Render!"

@app.route("/webhook", methods=["POST"])
def webhook_handler():
    data = request.json
    print("Received webhook data:", data)
    return jsonify({"status": "success", "message": "Webhook received"}), 200

@app.route("/send-report", methods=["POST"])
def trigger_report():
    try:
        today = datetime.date.today().isoformat()
        
        response = supabase.table("Bills").select("Id, AmountAfetrDis1, OperationType, Accounts(Name)").eq("Date", today).execute()
        rows = response.data
        
        accounts_totals = {}
        total_net = 0.0
        
        for row in rows:
            val = float(row.get("AmountAfetrDis1", 0.0) or 0.0)
            op_type = row.get("OperationType")
            
            if op_type == 12:
                val = -abs(val)
            else:
                val = abs(val)
                
            acc_info = row.get("Accounts")
            acc_name = acc_info.get("Name", "غير معروف") if acc_info else "غير معروف"
            
            accounts_totals[acc_name] = accounts_totals.get(acc_name, 0.0) + val
            total_net += val
            
        report_lines = [f"📊 تقرير المبيعات اليومي (Supabase):\n"]
        for acc_name, total_val in accounts_totals.items():
            report_lines.append(f"• {acc_name}: {total_val:,.2f} د.ل")
            
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
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
