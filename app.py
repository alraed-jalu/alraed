import os
from flask import Flask, jsonify
from supabase import create_client, Client

app = Flask(__name__)
supabase: Client = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

@app.route("/")
def home():
    return "inspector active", 200

@app.route("/send-report", methods=["POST"])
def inspect_all():
    try:
        bills_res = supabase.table("bills").select("id, account_id, amount_afetr_dis1, bill_date, operation_type, deleted, removed").limit(15).execute()
        accounts_res = supabase.table("accounts").select("account_id, name").execute()
        
        return jsonify({
            "accounts_list": accounts_res.data,
            "bills_list": bills_res.data
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
