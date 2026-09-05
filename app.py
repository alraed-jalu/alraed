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
    return "alraed is live and ready for webhooks!", 200

def generate_report_text(period_type="يومي"):
    try:
        # تحديد نطاق التاريخ بناءً على الفترة المطلوبة
        today = datetime.now().date()
        
        if period_type == "اسبوعي":
            start_date = today - timedelta(days=7)
            title = "📊 تقرير المبيعات الأسبوعي:"
        elif period_type == "شهري":
            start_date = today.replace(day=1)
            title = "📊 تقرير المبيعات الشهري:"
        elif period_type == "سنوي":
            start_date = today.replace(month=1, day=1)
            title = "📊 تقرير المبيعات السنوي:"
        else: # يومي
            start_date = today
            title = "📊 تقرير المبيعات اليومي:"

        # جلب الفواتير من Supabase وتصفيتها حسب التاريخ
        response = supabase.table("bills").select("id, amount_afetr_dis1, operation_type, bill_date, accounts(name)").eq("deleted", 0).eq("removed", 0).gte("bill_date", str(start_date)).execute()
        data = response.data
        
        if not data:
            return f"عذراً، لا توجد بيانات مبيعات مسجلة للفترة الحالية ({period_type})."

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
            
            if acc_name in accounts_totals:
                accounts_totals[acc_name] += val
                total_net += val

        report_lines = [f"{title}\n"]
        for acc_name in allowed_accounts:
            val = accounts_totals[acc_name]
            report_lines.append(f"• {acc_name}: {val:,.2f} د.ل")
        
        report_lines.append(f"\n📌 الإجمالي الصافي: {total_net:,.2f} د.ل")
        return "\n".join(report_lines)

    except Exception as e:
        return f حدث خطأ أثناء إنشاء التقرير: {str(e)}"

@app.route("/send-report", methods=["POST"])
def send_report_manual():
    # نقطة لطلب التقرير اليدوي (افتراضياً اليومي أو حسب الطلب)
    req_data = request.get_json(silent=True) or {}
    period = req_data.get("period", "يومي")
    
    report_message = generate_report_text(period)

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

@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    try:
        incoming_data = request.get_json(silent=True) or {}
        
        # استخراج نص الرسالة ورقم المرسل من هيكل Wasender webhook
        message_body = ""
        sender = ""
        
        # التعامل مع الاحتمالات المختلفة لهيكل الـ Webhook الوارد من Wasender
        if "body" in incoming_data:
            message_body = str(incoming_data.get("body", "")).lower().strip()
            sender = str(incoming_data.get("from", ""))
        elif "message" in incoming_data:
            msg_obj = incoming_data.get("message", {})
            message_body = str(msg_obj.get("body", "")).lower().strip()
            sender = str(incoming_data.get("sender", ""))

        # تحليل الكلمات المفتاحية لتحديد الفترة المطلوبة
        period = "يومي"
        if "اسبوع" in message_body or "أسبوع" in message_body:
            period = "اسبوعي"
        elif "شهر" in message_body:
            period = "شهري"
        elif "سنة" in message_body or "سنوي" in message_body:
            period = "سنوي"
        elif "يوم" in message_body or "تقرير" in message_body:
            period = "يومي"
        else:
            # إذا كانت رسالة أخرى لا تخص طلب التقرير، نتجاهلها أو نرد بشكل مناسب
            return jsonify({"status": "ignored"}), 200

        # توليد وإرسال التقرير المناسب
        report_message = generate_report_text(period)

        headers = {
            "Authorization": f"Bearer {WASENDER_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "to": RECIPIENT_PHONE if not sender else sender,
            "text": report_message
        }

        requests.post(WASENDER_URL, json=payload, headers=headers, timeout=15)
        return jsonify({"status": "success", "period_selected": period}), 200

    except Exception as e:
        print("WEBHOOK ERROR:\n", traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
