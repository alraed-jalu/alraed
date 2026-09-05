import os
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
    return "alraed schema sync is live!", 200

@app.route("/send-report", methods=["POST"])
def send_report_manual():
    try:
        # جلب أول 10 صفوف من جدول bills مع كافة أعمدته لمعرفة الحقول الحقيقية
        bills_res = supabase.table("bills").select("*").limit(10).execute()
        raw_bills = bills_res.data or []

        # جلب جدول accounts لمعرفة الحقول والأسماء المخزنة فيه
        acc_res = supabase.table("accounts").select("*").execute()
        raw_accounts = acc_res.data or []

        # إرجاع تفاصيل الهيكلة الحقيقية على الشاشة لنطابقها بدقة
        return jsonify({
            "status": "success",
            "accounts_table_sample": raw_accounts,
            "bills_table_sample": raw_bills
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
