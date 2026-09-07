import os
import requests
from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify
from supabase import create_client, Client

app = Flask(__name__)
supabase: Client = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

ACCOUNT_NAMES = {
    1: "زبون نقدي",
    2: "موبي كاش",
    3: "ادفع لي",
    4: "يسر باي",
    5: "بطاقة مصرفية"
}

@app.route("/")
def home():
    return "Alraed Bot is running!", 200

@app.route("/send-report", methods=["POST"])
def send_report():
    try:
        # ضبط التاريخ حسب توقيت ليبيا المحلي (UTC+2)
        libya_tz = timezone(timedelta(hours=2))
        today_date = datetime.now(libya_tz).strftime("%Y-%m-%d")
        
        # جلب فواتير اليوم غير المحذوفة
        response = supabase.table("bills").select("account_id, amount_afetr_dis1").eq("bill_date", today_date).eq("deleted", 0).eq("removed", 0).execute()
        
        bills = response.data
        if not bills:
            report_text = f"📊 *التقرير المالي اليومي* - {today_date}\n\nلا توجد فواتير مسجلة اليوم."
        else:
            totals = {}
            for bill in bills:
                acc_id = bill.get("account_id")
                amount = float(bill.get("amount_afetr_dis1", 0) or 0)
                totals[acc_id] = totals.get(acc_id, 0.0) + amount

            report_lines = [f"📊 *التقرير المالي اليومي* - {today_date}\n"]
            grand_total = 0.0

            for acc_id, total in totals.items():
                name = ACCOUNT_NAMES.get(acc_id, f"حساب رقم {acc_id}")
                report_lines.append(f"▫️ *{name}* : {total:.2f} د.ل")
                grand_total += total

            report_lines.append(f"\n💰 *الإجمالي الكلي* : {grand_total:.2f} د.ل")
            report_text = "\n".join(report_lines)

        return jsonify({
            "status": "success",
            "date_used": today_date,
            "report_text": report_text
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
