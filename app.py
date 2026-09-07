import os
from flask import Flask, jsonify
from supabase import create_client, Client

app = Flask(__name__)
supabase: Client = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

@app.route("/")
def home():
    return "Inspector running", 200

@app.route("/send-report", methods=["POST"])
def inspect_bills():
    try:
        # جلب آخر 5 فواتير مسجلة لمعرفة تواريخها
        response = supabase.table("bills").select("id, bill_date, amount_afetr_dis1, account_id").order("id", desc=True).limit(5).execute()
        return jsonify({
            "status": "success",
            "recent_bills": response.data
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
