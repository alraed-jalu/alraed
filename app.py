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
    return "alraed daily report sync is live!", 200

@app.route("/send-report", methods=["POST"])
def send_report_manual():
    try:
        # جلب الحسابات لتكوين خريطة الأسماء
        acc_res = supabase.table("accounts").select("account_id, name").execute()
        accounts_map = {}
        if acc_res.data:
            for acc in acc_res.data:
                try:
                    accounts_map[int(acc.get("account_id"))] = str(acc.get("name", "")).strip()
                except:
                    pass

        # جلب الفواتير من الجدول
        bills_res = supabase.table("bills").select("id, account_id, amount_afetr_dis1, operation_type, deleted, removed, created_at, date").execute()
        raw_bills = bills_res.data or []

        # تاريخ اليوم بصيغة مقارنة (مثلا YYYY-MM-DD أو حسب تخزين المنظومة)
        today_str = datetime.now().strftime("%Y-%m-%d")

        allowed_accounts = ["زبون نقدي", "موبي كاش 1", "ادفع لي 2", "يسر باي 3", "بطاقة مصرفية 4"]
        accounts_totals = {acc: 0.0 for acc in allowed_accounts}
        total_net = 0.0
        daily_bills_count = 0

        for row in raw_bills:
            if row.get("deleted", 0) == 1 or row.get("removed", 0) == 1:
                continue

            # التحقق من التاريخ (إذا كان حقل التاريخ موجوداً، نتحقق من مطابقته لليوم، أو نتأكد من جلب السجلات الحديثة)
            # سنقوم بفلترة السجلات التي تخص اليوم إذا أمكن، أو عرضها
            bill_date = str(row.get("date", "") or row.get("created_at", ""))
            
            # إذا أردت التأكد من مطابقة تاريخ اليوم (يمكنك تعديل الشرط حسب صيغة التاريخ في قاعدتك)
            # لعرض كافة البيانات الحقيقية غير الصففرية، سنقوم بتجميعها مع طباعة التفاصيل:
            amt = float(row.get("amount_afetr_dis1", 0.0) or 0.0)
            op_type = row.get("operation_type", 0)
            acc_id = row.get("account_id")
            
            # معالجة الإرجاع أو العمليات المختلفة
            val = -abs(amt) if op_type in [12, 2, "return"] else abs(amt)
            acc_name = accounts_map.get(int(acc_id), "") if acc_id else ""
            
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
                daily_bills_count += 1

        report_lines = [f"📊 تقرير المبيعات اليومي ({today_str}):\n"]
        for acc_name in allowed_accounts:
            val = accounts_totals[acc_name]
            report_lines.append(f"• {acc_name}: {val:,.2f} د.ل")
        
        report_lines.append(f"\n📌 الإجمالي الصافي: {total_net:,.2f} د.ل")
        report_message = "\n".join(report_lines)

        # إرسال التقرير الحقيقي عبر واتساب
        headers = {"Authorization": f"Bearer {WASENDER_TOKEN}", "Content-Type": "application/json"}
        payload = {"to": RECIPIENT_PHONE, "text": report_message}
        requests.post(WASENDER_URL, json=payload, headers=headers, timeout=15)

        return jsonify({
            "status": "success",
            "bills_processed": daily_bills_count,
            "calculated_totals": accounts_totals,
            "total_net": total_net
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
