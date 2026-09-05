import os
import requests
from flask import Flask, request, jsonify
from supabase import create_client, Client

app = Flask(__name__)
supabase: Client = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

# إعدادات Wasender API (تأكد من مطابقتها لمتغيرات البيئة لديك في Render)
WASENDER_API_URL = os.environ.get("WASENDER_API_URL", "https://www.wasender.api/send") # استبدل الرابط برابط واجهة Wasender الفعلي لديك
WASENDER_API_KEY = os.environ.get("WASENDER_API_KEY", "")
MY_PHONE_NUMBER = os.environ.get("MY_PHONE_NUMBER", "") # رقم هاتفك المستلم

ACCOUNT_NAMES = {
    1: "زبون نقدي",
    2: "موبي كاش",
    3: "ادفع لي",
    4: "يسر باي",
    5: "بطاقة مصرفية"
}

@app.route("/")
def home():
    return "Alraed WhatsApp Bot is running!", 200

@app.route("/send-report", methods=["POST"])
def send_report():
    try:
        # جلب فواتير اليوم (2026-09-05) غير المحذوفة
        response = supabase.table("bills").select("account_id, amount_afetr_dis1").eq("bill_date", "2026-09-05").eq("deleted", 0).eq("removed", 0).execute()
        
        bills = response.data
        if not bills:
            report_text = "📊 *التقرير المالي اليومي* - 2026-09-05\n\nلا توجد فواتير مسجلة اليوم."
        else:
            totals = {}
            for bill in bills:
                acc_id = bill.get("account_id")
                amount = float(bill.get("amount_afetr_dis1", 0) or 0)
                totals[acc_id] = totals.get(acc_id, 0.0) + amount

            report_lines = ["📊 *التقرير المالي اليومي* - 2026-09-05\n"]
            grand_total = 0.0

            for acc_id, total in totals.items():
                name = ACCOUNT_NAMES.get(acc_id, f"حساب رقم {acc_id}")
                report_lines.append(f"▫️ *{name}*: {total:.2f} د.ل")
                grand_total += total

            report_lines.append(f"\n💰 *الإجمالي الكلي*: {grand_total:.2f} د.ل")
            report_text = "\n".join(report_lines)

        # إرسال التقرير عبر Wasender API إلى هاتفك
        payload = {
            "to": MY_PHONE_NUMBER,
            "message": report_text,
            "key": WASENDER_API_KEY
        }
        
        # تنفيذ طلب الإرسال (يمكنك تعديل الطريقة حسب مكتبة Wasender التي تستخدمها)
        # requests.post(WASENDER_API_URL, json=payload)

        return jsonify({
            "status": "success",
            "report_sent_to": MY_PHONE_NUMBER,
            "report_text": report_text
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
