import os
from flask import Flask, jsonify
from supabase import create_client, Client

app = Flask(__name__)
supabase: Client = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

@app.route("/")
def home():
    return "inspector active", 200

@app.route("/send-report", methods=["POST"])
def inspect_tables():
    try:
        # فحص عينة من جدول bills وعينة من جدول accounts
        bills_sample = supabase.table("bills").select("*").limit(5).execute()
        accounts_sample = supabase.table("accounts").select("*").execute()
        
        return jsonify({
            "accounts": accounts_sample.data,
            "bills_sample": bills_sample.data
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
