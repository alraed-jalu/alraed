import os
import requests
from flask import Flask, jsonify, request
from supabase import create_client, Client

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route("/")
def home():
    return "alraed inspect is live!", 200

@app.route("/send-report", methods=["POST"])
def send_report_manual():
    try:
        # جلب البيانات من جدول bills مباشرة
        response = supabase.table("bills").select("*").limit(5).execute()
        return jsonify({
            "status": "success",
            "data": response.data
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
